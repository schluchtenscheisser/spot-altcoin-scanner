"""Pre-1 Binance OHLCV history fetch orchestration."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Any, Protocol

import pandas as pd

from scanner.data.bar_clock import timeframe_to_duration_ms, most_recent_closed_bar_close_time_utc_ms

from .binance_client import BinanceSpotClient
from .history_fetch_config import HistoryFetchConfig, SOURCE
from .manifests import build_history_manifest, build_symbol_completeness, build_universe_manifest, iso_now, write_json
from .parquet_store import WriteResult, normalize_rows, write_partitioned_ohlcv, load_symbol_timeframe
from .symbol_intersection import UniverseResolution, load_mexc_universe, resolve_universe


class HistoryClient(Protocol):
    def get_spot_usdt_symbols(self) -> list[str]: ...
    def get_klines(self, symbol: str, interval: str, *, start_time_ms: int | None = None, end_time_ms: int | None = None, limit: int = 1000) -> list[list[Any]]: ...


@dataclass
class FetchOutcome:
    history_manifest: dict[str, Any]
    universe_manifest: dict[str, Any]
    symbol_completeness: dict[str, Any]
    rows: pd.DataFrame


@dataclass
class FetchAccumulator:
    rows: list[dict[str, Any]] = field(default_factory=list)
    data_quality_issues: list[dict[str, Any]] = field(default_factory=list)
    fetch_errors: dict[str, str] = field(default_factory=dict)


def _ms(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def _start_ms(config: HistoryFetchConfig) -> int:
    return _ms(datetime.combine(config.fetch_start_date, datetime.min.time(), tzinfo=timezone.utc))


def _end_ms(config: HistoryFetchConfig) -> int:
    # Binance endTime is inclusive; request through the end of the requested UTC calendar date.
    return _ms(datetime.combine(config.effective_fetch_end_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)) - 1


def _coerce_float(value: Any, *, column: str, symbol: str, timeframe: str, open_time_ms: int) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"invalid numeric {column} for {symbol} {timeframe} at {open_time_ms}: {value!r}")
    if not math.isfinite(numeric):
        raise ValueError(f"non-finite numeric {column} for {symbol} {timeframe} at {open_time_ms}: {value!r}")
    return numeric


def _row_from_kline(raw: list[Any], *, symbol: str, timeframe: str, fetch_run_id: str, fetched_at_utc: str, runtime_utc: datetime, end_time_ms: int) -> dict[str, Any] | None:
    duration_ms = timeframe_to_duration_ms(timeframe)
    open_time_ms = int(raw[0])
    close_time_ms = int(raw[6]) if len(raw) > 6 else open_time_ms + duration_ms - 1
    latest_closed_boundary = most_recent_closed_bar_close_time_utc_ms(timeframe, runtime_utc)
    if close_time_ms > latest_closed_boundary or close_time_ms > end_time_ms:
        return None
    open_time = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc)
    close_time = datetime.fromtimestamp((open_time_ms + duration_ms) / 1000, tz=timezone.utc)
    return {
        "source": SOURCE,
        "symbol": symbol,
        "timeframe": timeframe,
        "open_time_utc": open_time.isoformat().replace("+00:00", "Z"),
        "close_time_utc": close_time.isoformat().replace("+00:00", "Z"),
        "open": _coerce_float(raw[1], column="open", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms),
        "high": _coerce_float(raw[2], column="high", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms),
        "low": _coerce_float(raw[3], column="low", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms),
        "close": _coerce_float(raw[4], column="close", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms),
        "volume": _coerce_float(raw[5], column="volume", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms),
        "quote_volume": _coerce_float(raw[7], column="quote_volume", symbol=symbol, timeframe=timeframe, open_time_ms=open_time_ms) if len(raw) > 7 and raw[7] is not None else None,
        "trade_count": int(raw[8]) if len(raw) > 8 and raw[8] is not None else None,
        "is_closed": True,
        "fetch_run_id": fetch_run_id,
        "fetched_at_utc": fetched_at_utc,
    }


def fetch_klines_paginated(client: HistoryClient, *, symbol: str, timeframe: str, config: HistoryFetchConfig, fetch_run_id: str, fetched_at_utc: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    start_ms = _start_ms(config)
    end_ms = _end_ms(config)
    duration_ms = timeframe_to_duration_ms(timeframe)
    rows: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    cursor = start_ms
    while cursor <= end_ms:
        batch = client.get_klines(symbol, timeframe, start_time_ms=cursor, end_time_ms=end_ms, limit=1000)
        if not batch:
            break
        advanced = False
        for raw in batch:
            try:
                row = _row_from_kline(raw, symbol=symbol, timeframe=timeframe, fetch_run_id=fetch_run_id, fetched_at_utc=fetched_at_utc, runtime_utc=config.runtime_utc, end_time_ms=end_ms)
            except ValueError as exc:
                issues.append({"symbol": symbol, "timeframe": timeframe, "issue": str(exc)})
                continue
            open_time_ms = int(raw[0])
            if row is not None:
                rows.append(row)
            if open_time_ms >= cursor:
                cursor = open_time_ms + duration_ms
                advanced = True
        if len(batch) < 1000 or not advanced:
            break
    return rows, issues


def _resolve(client: HistoryClient, config: HistoryFetchConfig, mexc_symbols: list[str] | None) -> UniverseResolution:
    binance_symbols = client.get_spot_usdt_symbols()
    if config.universe_mode == "fixed_current_mexc_binance_intersection" and mexc_symbols is None and config.mexc_universe_path is not None:
        mexc_symbols = load_mexc_universe(config.mexc_universe_path)
    return resolve_universe(universe_mode=config.universe_mode, binance_symbols=binance_symbols, mexc_symbols=mexc_symbols)


def run_history_fetch(
    config: HistoryFetchConfig,
    *,
    client: HistoryClient | None = None,
    mexc_symbols: list[str] | None = None,
    fetch_run_id: str | None = None,
    dry_run: bool = False,
) -> FetchOutcome:
    effective_client = client or BinanceSpotClient()
    run_id = fetch_run_id or f"pre1-{uuid4().hex}"
    created_at = iso_now()
    resolution = _resolve(effective_client, config, mexc_symbols)
    accumulator = FetchAccumulator()

    if dry_run:
        write_result = WriteResult()
        rows_df = pd.DataFrame()
    else:
        for symbol in resolution.included_symbols:
            for timeframe in config.timeframes:
                try:
                    rows, issues = fetch_klines_paginated(
                        effective_client,
                        symbol=symbol,
                        timeframe=timeframe,
                        config=config,
                        fetch_run_id=run_id,
                        fetched_at_utc=created_at,
                    )
                    accumulator.rows.extend(rows)
                    accumulator.data_quality_issues.extend(issues)
                except Exception as exc:  # client/network errors are represented in universe manifest
                    accumulator.fetch_errors[symbol] = str(exc)
                    break
        rows_df = normalize_rows(pd.DataFrame(accumulator.rows)) if accumulator.rows else pd.DataFrame()
        write_result = write_partitioned_ohlcv(
            rows_df,
            output_root=config.output_root,
            effective_fetch_end_date=config.effective_fetch_end_date,
            force_repair=config.force_repair,
        )

    daily_counts = {symbol: 0 for symbol in resolution.included_symbols}
    if not rows_df.empty:
        current_counts = rows_df[rows_df["timeframe"] == "1d"].groupby("symbol").size().to_dict()
        daily_counts.update({str(symbol): int(count) for symbol, count in current_counts.items()})
    for symbol in resolution.included_symbols:
        stored_daily = load_symbol_timeframe(config.output_root, symbol, "1d") if not dry_run else pd.DataFrame()
        if not stored_daily.empty:
            daily_counts[symbol] = max(daily_counts.get(symbol, 0), int(len(stored_daily)))

    history_manifest = build_history_manifest(
        config=config,
        fetch_run_id=run_id,
        created_at_utc=created_at,
        symbols=resolution.included_symbols,
        rows=rows_df,
        write_result=write_result,
        data_quality_issues=accumulator.data_quality_issues,
    )
    symbol_completeness = build_symbol_completeness(
        fetch_run_id=run_id,
        created_at_utc=created_at,
        rows=rows_df,
        symbols=resolution.included_symbols,
        timeframes=config.timeframes,
        partition_completeness=write_result.partition_completeness,
    )
    universe_manifest = build_universe_manifest(
        fetch_run_id=run_id,
        created_at_utc=created_at,
        resolution=resolution,
        daily_counts=daily_counts,
        fetch_errors=accumulator.fetch_errors,
        min_history_days=config.min_history_days,
    )

    if not dry_run:
        write_json(config.manifest_root / "history_manifest.json", history_manifest)
        write_json(config.manifest_root / "universe_manifest.json", universe_manifest)
        write_json(config.manifest_root / "symbol_completeness.json", symbol_completeness)
    return FetchOutcome(history_manifest, universe_manifest, symbol_completeness, rows_df)
