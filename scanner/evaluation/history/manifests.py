"""Manifest builders/writers for Pre-1 history fetch outputs."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .history_fetch_config import SCHEMA_VERSION, HistoryFetchConfig
from .parquet_store import WriteResult
from .symbol_intersection import ExcludedSymbol, UniverseResolution, empty_excluded_counts


def iso_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return value.as_posix()
    return value


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_safe) + "\n", encoding="utf-8")


def build_symbol_completeness(
    *,
    fetch_run_id: str,
    created_at_utc: str,
    rows: pd.DataFrame,
    symbols: list[str],
    timeframes: tuple[str, ...],
    missing_ranges: dict[str, list[dict[str, str]]] | None = None,
    partition_completeness: list[dict[str, object]] | None = None,
) -> dict[str, Any]:
    counts: dict[str, int] = {}
    latest: dict[str, str | None] = {}
    first: dict[str, str | None] = {}
    for symbol in symbols:
        for timeframe in timeframes:
            key = f"{symbol}|{timeframe}"
            subset = rows[(rows["symbol"] == symbol) & (rows["timeframe"] == timeframe)] if not rows.empty else rows
            counts[key] = int(len(subset))
            if len(subset):
                ordered = subset.sort_values("close_time_utc")
                first[key] = str(ordered.iloc[0]["close_time_utc"])
                latest[key] = str(ordered.iloc[-1]["close_time_utc"])
            else:
                first[key] = None
                latest[key] = None
    return {
        "manifest_type": "symbol_completeness",
        "schema_version": SCHEMA_VERSION,
        "fetch_run_id": fetch_run_id,
        "created_at_utc": created_at_utc,
        "bar_counts_by_symbol_timeframe": dict(sorted(counts.items())),
        "latest_close_time_by_symbol_timeframe": dict(sorted(latest.items())),
        "first_close_time_by_symbol_timeframe": dict(sorted(first.items())),
        "missing_ranges_by_symbol_timeframe": dict(sorted((missing_ranges or {}).items())),
        "partition_completeness": partition_completeness or [],
    }


def build_universe_manifest(
    *,
    fetch_run_id: str,
    created_at_utc: str,
    resolution: UniverseResolution,
    daily_counts: dict[str, int],
    fetch_errors: dict[str, str] | None,
    min_history_days: int,
) -> dict[str, Any]:
    excluded: list[ExcludedSymbol] = list(resolution.excluded_symbols)
    signal_evaluable: list[str] = []
    errors = fetch_errors or {}
    for symbol in resolution.included_symbols:
        if symbol in errors:
            excluded.append(ExcludedSymbol(symbol, symbol, "fetch_error", errors[symbol]))
        elif daily_counts.get(symbol, 0) == 0:
            excluded.append(ExcludedSymbol(symbol, symbol, "no_binance_history", "no daily Binance OHLCV bars were fetched"))
        elif daily_counts.get(symbol, 0) < min_history_days:
            excluded.append(
                ExcludedSymbol(symbol, symbol, "insufficient_history", f"daily bars {daily_counts.get(symbol, 0)} < min_history_days {min_history_days}")
            )
        else:
            signal_evaluable.append(symbol)
    sorted_excluded = sorted(excluded, key=lambda item: (item.reason, item.source_symbol, item.normalized_symbol or ""))
    counts = empty_excluded_counts()
    for item in sorted_excluded:
        counts[item.reason] += 1
    return {
        "manifest_type": "universe_manifest",
        "schema_version": SCHEMA_VERSION,
        "fetch_run_id": fetch_run_id,
        "created_at_utc": created_at_utc,
        "universe_mode": resolution.universe_mode,
        "source_mexc_symbol_count": resolution.source_mexc_symbol_count,
        "binance_usdt_symbol_count": resolution.binance_usdt_symbol_count,
        "included_replay_symbol_count": len(resolution.included_symbols),
        "signal_evaluable_symbol_count": len(signal_evaluable),
        "excluded_counts": counts,
        "included_symbols": sorted(resolution.included_symbols),
        "signal_evaluable_symbols": sorted(signal_evaluable),
        "excluded_symbols": [item.to_dict() for item in sorted_excluded],
    }


def build_history_manifest(
    *,
    config: HistoryFetchConfig,
    fetch_run_id: str,
    created_at_utc: str,
    symbols: list[str],
    rows: pd.DataFrame,
    write_result: WriteResult,
    data_quality_issues: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    bar_counts = {timeframe: 0 for timeframe in config.timeframes}
    if not rows.empty:
        for timeframe, count in rows.groupby("timeframe").size().items():
            bar_counts[str(timeframe)] = int(count)
    symbols_with_any = int(rows["symbol"].nunique()) if not rows.empty else 0
    return {
        "manifest_type": "history_manifest",
        "schema_version": SCHEMA_VERSION,
        "fetch_run_id": fetch_run_id,
        "created_at_utc": created_at_utc,
        "runtime_utc": config.runtime_utc.replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source": config.source,
        "timeframes": list(config.timeframes),
        "fetch_start_date": config.fetch_start_date.isoformat(),
        "fetch_end_date_requested": config.fetch_end_date_requested,
        "effective_fetch_end_date": config.effective_fetch_end_date.isoformat(),
        "evaluation_start_date": config.evaluation_start_date.isoformat(),
        "evaluation_end_date": config.evaluation_end_date.isoformat(),
        "evaluation_dates_operational_in_pre1": False,
        "warm_up_1d_bars": config.warm_up_1d_bars,
        "warm_up_4h_bars": config.warm_up_4h_bars,
        "warm_up_coverage": config.warm_up_coverage,
        "min_history_days": config.min_history_days,
        "closed_bar_only": True,
        "output_root": config.output_root.as_posix(),
        "partitioning": "timeframe/symbol/year/month",
        "force_repair": config.force_repair,
        "symbols_total": len(symbols),
        "symbols_with_any_history": symbols_with_any,
        "bar_counts_by_timeframe": dict(sorted(bar_counts.items())),
        "symbol_completeness_path": (config.manifest_root / "symbol_completeness.json").as_posix(),
        "partitions_written": write_result.written,
        "partitions_skipped_existing": write_result.skipped_existing,
        "partitions_repaired": write_result.repaired,
        "partitions_completed_from_partial": write_result.completed_partial,
        "partitions_incomplete_for_effective_fetch_window": write_result.incomplete,
        "partition_completeness": write_result.partition_completeness,
        "data_quality_issues": data_quality_issues or [],
        "incremental_update_summary": {
            "existing_partitions_detected": write_result.existing_partitions_detected,
            "new_partitions_written": write_result.new_partitions_written,
            "existing_closed_partitions_rewritten": write_result.existing_closed_partitions_rewritten,
            "existing_partial_partitions_completed": write_result.existing_partial_partitions_completed,
        },
    }
