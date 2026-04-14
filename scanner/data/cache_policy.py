from __future__ import annotations

import os
from datetime import datetime

from scanner.config import load_config
from scanner.data.bar_clock import most_recent_closed_bar_close_time_utc_ms, timeframe_to_duration_ms
from scanner.storage import get_ohlcv_cache_meta, init_db, ohlcv_bar_exists


def _get_connection_and_cfg():
    cfg = load_config()
    db_path = os.getenv("SCANNER_DB_PATH", "data/independence_release.sqlite")
    return init_db(db_path), cfg


def _validate_symbol(symbol: str) -> str:
    if symbol is None:
        raise TypeError("symbol must not be None")
    if not isinstance(symbol, str):
        raise TypeError(f"symbol must be str, got {type(symbol).__name__}")
    if symbol != symbol.strip():
        raise ValueError(f"symbol invalid value {symbol!r}: must not contain leading/trailing whitespace")
    normalized = symbol.upper()
    if not normalized:
        raise ValueError(f"symbol invalid value {symbol!r}: must be non-empty")
    return normalized


def _validate_timeframe(timeframe: str) -> str:
    if timeframe not in {"1d", "4h"}:
        raise ValueError(f"timeframe invalid value {timeframe!r}: must be one of ('1d', '4h')")
    return timeframe


def get_cache_status(symbol: str, timeframe: str, now: int | datetime) -> str:
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    cutoff = most_recent_closed_bar_close_time_utc_ms(timeframe, now)

    conn, _ = _get_connection_and_cfg()
    try:
        meta = get_ohlcv_cache_meta(conn, symbol, timeframe)
        if meta is None:
            return "missing"
        if meta.cached_close_time_utc_ms is None:
            return "broken"
        if meta.last_fetch_status != "ok":
            return "broken"
        if not ohlcv_bar_exists(conn, symbol, timeframe, meta.cached_close_time_utc_ms):
            return "broken"
        if int(meta.cached_close_time_utc_ms) == int(cutoff):
            return "fresh"
        if int(meta.cached_close_time_utc_ms) < int(cutoff):
            return "stale"
        return "broken"
    finally:
        conn.close()


def bars_missing_since_cached(symbol: str, timeframe: str, now: int | datetime) -> int | None:
    symbol = _validate_symbol(symbol)
    timeframe = _validate_timeframe(timeframe)
    status = get_cache_status(symbol, timeframe, now)
    if status == "fresh":
        return 0
    if status in {"missing", "broken"}:
        return None

    cutoff = most_recent_closed_bar_close_time_utc_ms(timeframe, now)
    conn, _ = _get_connection_and_cfg()
    try:
        meta = get_ohlcv_cache_meta(conn, symbol, timeframe)
        if meta is None or meta.cached_close_time_utc_ms is None:
            return None
        step = timeframe_to_duration_ms(timeframe)
        return int(max(0, (int(cutoff) - int(meta.cached_close_time_utc_ms)) // step))
    finally:
        conn.close()


def get_fetch_decision(symbol: str, timeframe: str, now: int | datetime) -> str:
    status = get_cache_status(symbol, timeframe, now)
    if status == "fresh":
        return "skip"
    if status in {"missing", "broken"}:
        return "fetch_full"

    conn, cfg = _get_connection_and_cfg()
    conn.close()
    threshold = int(cfg.independence_ohlcv_fetch["incremental_max_bars"])
    missing = bars_missing_since_cached(symbol, timeframe, now)
    if missing is None:
        return "fetch_full"
    return "fetch_incremental" if missing < threshold else "fetch_full"
