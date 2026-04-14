from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import requests

from scanner.clients.mexc_client import MEXCClient
from scanner.config import load_config
from scanner.data.bar_clock import (
    is_close_time_on_grid,
    most_recent_closed_bar_close_time_utc_ms,
    timeframe_to_duration_ms,
)
from scanner.data.cache_policy import get_fetch_decision, _validate_symbol, _validate_timeframe
from scanner.storage import (
    OhlcvBarRecord,
    get_ohlcv_cache_meta,
    init_db,
    upsert_ohlcv_cache_meta,
    write_ohlcv_bars_conflict_strict,
)


@dataclass(frozen=True)
class Bar:
    open_time_utc_ms: int
    close_time_utc_ms: int
    open: float
    high: float
    low: float
    close: float
    base_volume: float
    quote_volume: float


@dataclass(frozen=True)
class FetchResult:
    symbol: str
    timeframe: str
    requested_at_utc_ms: int
    canonical_close_cutoff_utc_ms: int
    bars: list[Bar]
    partial_bars_dropped: int
    invalid_bars_rejected: int
    duplicate_bars_deduplicated: int
    misaligned_bars_rejected: int
    last_fetch_status: str
    last_error_code: str | None


@dataclass(frozen=True)
class PersistResult:
    symbol: str
    timeframe: str
    rows_inserted: int
    rows_noop_identical: int
    cached_close_time_utc_ms: int | None
    last_fetch_status: str
    last_error_code: str | None


def _get_connection_and_cfg():
    cfg = load_config()
    db_path = os.getenv("SCANNER_DB_PATH", "data/independence_release.sqlite")
    return init_db(db_path), cfg


def _utc_now_ms() -> int:
    return int(datetime.now(tz=timezone.utc).timestamp() * 1000)


def _iso_now() -> str:
    return datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _validate_now(now: int | datetime) -> int:
    if now is None:
        raise TypeError("now must not be None")
    if isinstance(now, datetime):
        if now.tzinfo is None:
            raise TypeError("now must be timezone-aware")
        return int(now.astimezone(timezone.utc).timestamp() * 1000)
    if isinstance(now, bool) or not isinstance(now, (int, float)):
        raise TypeError("now must be epoch milliseconds numeric or timezone-aware datetime")
    num = float(now)
    if not math.isfinite(num):
        raise ValueError(f"now invalid value {now!r}: must be finite")
    return int(num)


def _resolve_lookback(tf: str, lookback_bars: int | None, cfg: Any) -> int:
    c = cfg.independence_ohlcv_fetch
    min_key = "min_lookback_bars_1d" if tf == "1d" else "min_lookback_bars_4h"
    def_key = "lookback_bars_1d" if tf == "1d" else "lookback_bars_4h"
    minimum = int(c[min_key])
    maximum = 1000
    if lookback_bars is None:
        return int(c[def_key])
    if isinstance(lookback_bars, bool) or not isinstance(lookback_bars, int) or lookback_bars <= 0:
        raise ValueError(f"lookback_bars invalid value {lookback_bars!r}")
    if lookback_bars < minimum or lookback_bars > maximum:
        raise ValueError(f"lookback_bars invalid value {lookback_bars!r}")
    return lookback_bars


def fetch_closed_bars(symbol: str, timeframe: str, now: int | datetime, lookback_bars: int | None = None) -> FetchResult:
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    now_ms = _validate_now(now)
    cutoff = most_recent_closed_bar_close_time_utc_ms(timeframe, now_ms)

    conn, cfg = _get_connection_and_cfg()
    conn.close()
    lookback = _resolve_lookback(timeframe, lookback_bars, cfg)
    duration = timeframe_to_duration_ms(timeframe)
    start_time = cutoff - ((lookback + 1) * duration)

    client = MEXCClient(timeout=int(cfg.independence_ohlcv_fetch["per_call_timeout_s"]), max_retries=int(cfg.independence_ohlcv_fetch["max_retries"]))

    try:
        raw = client.get_klines(symbol=symbol, interval=timeframe, limit=min(1000, lookback + 5), use_cache=False)
    except requests.RequestException:
        return FetchResult(symbol, timeframe, _utc_now_ms(), cutoff, [], 0, 0, 0, 0, "error_transport", "transport")

    dedup: dict[int, Bar] = {}
    partial = invalid = duplicates = misaligned = 0

    for item in raw:
        if not isinstance(item, list) or len(item) < 8:
            invalid += 1
            continue
        try:
            open_time = int(item[0])
            expected_close = open_time + duration
            if item[6] is None:
                close_time = expected_close
            else:
                exchange_close = int(item[6])
                if abs(exchange_close - expected_close) <= 1:
                    close_time = expected_close
                else:
                    invalid += 1
                    continue
            values = [float(item[1]), float(item[2]), float(item[3]), float(item[4]), float(item[5]), float(item[7])]
        except Exception:
            invalid += 1
            continue
        if any((not math.isfinite(v)) for v in values):
            invalid += 1
            continue
        if close_time > cutoff:
            partial += 1
            continue
        if close_time <= start_time:
            continue
        if not is_close_time_on_grid(timeframe, close_time):
            misaligned += 1
            continue

        bar = Bar(open_time, close_time, values[0], values[1], values[2], values[3], values[4], values[5])
        if close_time in dedup:
            duplicates += 1
        dedup[close_time] = bar

    bars = [dedup[k] for k in sorted(dedup.keys()) if start_time < k <= cutoff]
    if bars:
        status = "ok"
        err = None
    elif invalid > 0:
        status = "error_invalid"
        err = "invalid_bars"
    else:
        status = "empty"
        err = None

    return FetchResult(symbol, timeframe, _utc_now_ms(), cutoff, bars, partial, invalid, duplicates, misaligned, status, err)


def persist_fetch(symbol: str, timeframe: str, fetch_result: FetchResult, now: int | datetime) -> PersistResult:
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    _validate_now(now)

    conn, _cfg = _get_connection_and_cfg()
    try:
        with conn:
            meta = get_ohlcv_cache_meta(conn, symbol, timeframe)
            inserted = noop = 0
            if fetch_result.last_fetch_status == "ok":
                records = [
                    OhlcvBarRecord(symbol, timeframe, b.open_time_utc_ms, b.close_time_utc_ms, b.open, b.high, b.low, b.close, b.base_volume, b.quote_volume)
                    for b in fetch_result.bars
                ]
                inserted, noop = write_ohlcv_bars_conflict_strict(conn, symbol, timeframe, records)

            cached_close = meta.cached_close_time_utc_ms if meta else None
            if fetch_result.last_fetch_status == "ok" and inserted > 0 and fetch_result.bars:
                cached_close = fetch_result.bars[-1].close_time_utc_ms

            upsert_ohlcv_cache_meta(
                conn,
                symbol=symbol,
                timeframe=timeframe,
                cached_close_time_utc_ms=cached_close,
                last_fetch_at_utc=_iso_now(),
                last_fetch_status=fetch_result.last_fetch_status,
                last_error_code=fetch_result.last_error_code,
            )

            return PersistResult(symbol, timeframe, inserted, noop, cached_close, fetch_result.last_fetch_status, fetch_result.last_error_code)
    finally:
        conn.close()


def fetch_and_persist(symbol: str, timeframe: str, now: int | datetime, lookback_bars: int | None = None) -> PersistResult:
    decision = get_fetch_decision(symbol, timeframe, now)
    if decision == "skip":
        conn, _ = _get_connection_and_cfg()
        try:
            meta = get_ohlcv_cache_meta(conn, _validate_symbol(symbol), _validate_timeframe(timeframe))
            cached = meta.cached_close_time_utc_ms if meta else None
            return PersistResult(_validate_symbol(symbol), _validate_timeframe(timeframe), 0, 0, cached, "ok", None)
        finally:
            conn.close()

    fetched = fetch_closed_bars(symbol, timeframe, now, lookback_bars)
    return persist_fetch(symbol, timeframe, fetched, now)
