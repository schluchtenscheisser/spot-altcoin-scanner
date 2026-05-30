from __future__ import annotations

import argparse
import hashlib
import json
import math
import shutil
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

ANALYSIS_ID = "BACKTEST-3A_EXIT_PATH_METRICS_4H"
DEFAULT_INPUT_EVENTS_PATH = Path(
    "evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet"
)
DEFAULT_SCENARIO_ID = "hsq_replay_2025_05_to_2026_05_v1"
DEFAULT_REPLAY_ID = "2026-05-24T21-27-31Z"
DEFAULT_OUTPUT_DIR = Path(
    "evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/exit_path_metrics_4h"
)
DEFAULT_HISTORY_ROOT = Path("snapshots/history/ohlcv")
PRIMARY_SEGMENT_PAIRS = (
    ("early_candidates", "base_reclaim"),
    ("confirmed_candidates", "ema_reclaim"),
    ("early_candidates", "early_reversal_break"),
)
PRIMARY_SEGMENTS = tuple(f"{bucket}__{entry}" for bucket, entry in PRIMARY_SEGMENT_PAIRS)
REQUIRED_OUTPUT_FILES = (
    "exit_path_metrics_4h.parquet",
    "exit_path_metrics_4h.csv",
    "exit_path_metrics_4h_summary.json",
    "exit_path_metrics_4h_report.md",
    "exit_path_returns_by_bar.parquet",
    "exit_path_returns_by_bar.csv",
)
EVENT_OUTPUT_COLUMNS = [
    "event_id",
    "symbol",
    "segment_key",
    "decision_bucket",
    "entry_pattern",
    "signal_timestamp",
    "reference_price",
    "reference_price_source",
    "reference_price_status",
    "reference_price_reason",
    "path_bar_1_timestamp",
    "path_bar_1_open",
    "path_bar_1_high",
    "path_bar_1_low",
    "path_bar_1_close",
    "available_path_bars",
    "required_path_bars",
    "path_coverage_ratio",
    "path_coverage_status",
    "path_metric_reason",
    "mfe_pct",
    "mae_pct",
    "mfe_bar_index_4h",
    "mae_bar_index_4h",
    "time_to_mfe_hours",
    "time_to_mae_hours",
    "atr_4h_available",
    "atr_4h_value",
    "atr_4h_period",
    "atr_4h_source",
]
BAR_OUTPUT_COLUMNS = [
    "event_id",
    "symbol",
    "segment_key",
    "decision_bucket",
    "entry_pattern",
    "signal_timestamp",
    "bar_index_4h",
    "bar_timestamp",
    "open_4h",
    "high_4h",
    "low_4h",
    "close_4h",
    "return_open_pct",
    "return_high_pct",
    "return_low_pct",
    "return_close_pct",
    "reference_price",
    "reference_price_source",
    "reference_price_status",
]


@dataclass(frozen=True)
class Backtest3AConfig:
    input_events_path: Path = DEFAULT_INPUT_EVENTS_PATH
    scenario_id: str = DEFAULT_SCENARIO_ID
    replay_id: str = DEFAULT_REPLAY_ID
    bar_timeframe: str = "4h"
    path_bars: int = 42
    primary_only: bool = True
    output_dir: Path = DEFAULT_OUTPUT_DIR
    strict_preflight: bool = True
    overwrite: bool = False
    history_root: Path = DEFAULT_HISTORY_ROOT
    atr_4h_period: int = 14


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate BACKTEST-3A 4h exit path metrics.")
    parser.add_argument("--input-events-path", type=Path, default=DEFAULT_INPUT_EVENTS_PATH)
    parser.add_argument("--scenario-id", default=DEFAULT_SCENARIO_ID)
    parser.add_argument("--replay-id", default=DEFAULT_REPLAY_ID)
    parser.add_argument("--bar-timeframe", default="4h")
    parser.add_argument("--path-bars", type=int, default=42)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--history-root", type=Path, default=DEFAULT_HISTORY_ROOT)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--strict-preflight", dest="strict_preflight", action="store_true", default=True)
    parser.add_argument("--no-strict-preflight", dest="strict_preflight", action="store_false")
    parser.add_argument(
        "--include-late-monitor",
        action="store_true",
        help="Unsupported in BACKTEST-3A; true fails preflight before writes.",
    )
    args = parser.parse_args()
    if args.include_late_monitor:
        raise SystemExit("include_late_monitor=true is unsupported in BACKTEST-3A; late_monitor is excluded from Primary Trade Scope metrics")
    return args


def _is_finite_positive(value: Any) -> bool:
    if isinstance(value, bool) or value is None:
        return False
    try:
        number = float(value)
    except (TypeError, ValueError):
        return False
    return math.isfinite(number) and number > 0


def _finite_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def _parse_utc_timestamp(value: Any, *, field_name: str) -> datetime:
    if value is None or pd.isna(value):
        raise ValueError(f"{field_name} is missing")
    if isinstance(value, pd.Timestamp):
        if value.tzinfo is None:
            raise ValueError(f"{field_name} must be timezone-aware UTC, got naive timestamp")
        return value.to_pydatetime().astimezone(UTC)
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError(f"{field_name} must be timezone-aware UTC, got naive datetime")
        return value.astimezone(UTC)
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            raise ValueError(f"{field_name} is empty")
        normalized = raw[:-1] + "+00:00" if raw.endswith("Z") else raw
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            raise ValueError(f"{field_name} must include explicit timezone: {value!r}")
        return dt.astimezone(UTC)
    raise ValueError(f"{field_name} must be timezone-aware datetime or ISO-8601 string with timezone")


def _signal_anchor_4h(signal_timestamp: datetime) -> datetime:
    boundary_hour = (signal_timestamp.hour // 4) * 4
    boundary = signal_timestamp.replace(hour=boundary_hour, minute=0, second=0, microsecond=0)
    if signal_timestamp == boundary:
        return boundary
    return boundary + timedelta(hours=4)


def _timestamp_string(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _normalize_input_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str]]:
    result = df.copy()
    mappings: dict[str, str] = {}
    if "decision_bucket" not in result.columns and "historical_signal_bucket" in result.columns:
        result["decision_bucket"] = result["historical_signal_bucket"]
        mappings["decision_bucket"] = "historical_signal_bucket"
    if "signal_timestamp" not in result.columns:
        for candidate in ("event_timestamp_utc", "as_of_utc", "timestamp"):
            if candidate in result.columns:
                result["signal_timestamp"] = result[candidate]
                mappings["signal_timestamp"] = candidate
                break
    return result, mappings


def _stable_event_id(row: pd.Series, *, scenario_id: str, replay_id: str) -> str:
    existing = row.get("event_id")
    if isinstance(existing, str) and existing.strip():
        return existing.strip()
    parts = [
        scenario_id,
        replay_id,
        row.get("symbol"),
        row.get("signal_timestamp"),
        row.get("decision_bucket"),
        row.get("entry_pattern"),
        row.get("setup_cycle_id"),
    ]
    payload = "|".join("NULL" if part is None or pd.isna(part) else str(part) for part in parts)
    return "bt3a_" + hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]


def _resolve_reference_price(row: pd.Series) -> tuple[float | None, str, str, str | None]:
    ordered_sources = ["signal_reference_price", "entry_reference_price"]
    for col in ordered_sources:
        if col in row.index:
            value = row.get(col)
            if _is_finite_positive(value):
                return float(value), col, "available", None
            if value is not None:
                return None, "null", "invalid", f"invalid_{col}"

    decision_bucket = row.get("decision_bucket")
    state = row.get("state_machine_state")
    if (state == "early_ready" or decision_bucket == "early_candidates") and "close_at_early_entry_bar" in row.index:
        value = row.get("close_at_early_entry_bar")
        if _is_finite_positive(value):
            return float(value), "close_at_early_entry_bar", "available", None
        if value is not None:
            return None, "null", "invalid", "invalid_close_at_early_entry_bar"
    if (state == "confirmed_ready" or decision_bucket == "confirmed_candidates") and "close_at_confirmed_entry_bar" in row.index:
        value = row.get("close_at_confirmed_entry_bar")
        if _is_finite_positive(value):
            return float(value), "close_at_confirmed_entry_bar", "available", None
        if value is not None:
            return None, "null", "invalid", "invalid_close_at_confirmed_entry_bar"

    event_close_values: list[tuple[str, float]] = []
    invalid_close_seen = False
    for col in ("close", "close_price", "signal_close"):
        if col not in row.index:
            continue
        value = row.get(col)
        if value is None or pd.isna(value):
            continue
        if _is_finite_positive(value):
            event_close_values.append((col, float(value)))
        else:
            invalid_close_seen = True
    if event_close_values:
        first_value = event_close_values[0][1]
        if any(not math.isclose(value, first_value, rel_tol=0.0, abs_tol=1e-12) for _, value in event_close_values[1:]):
            return None, "null", "ambiguous", "conflicting_event_close_columns"
        return first_value, "event_close", "available", None
    if invalid_close_seen:
        return None, "null", "invalid", "invalid_event_close"
    return None, "null", "missing", "missing_reference_price"


def _history_partition_files(history_root: Path, symbol: str, timeframe: str) -> list[Path]:
    base = history_root / f"timeframe={timeframe}" / f"symbol={symbol}"
    return sorted(base.glob("year=*/month=*/*.parquet"))


def load_ohlcv_history(history_root: Path, *, symbol: str, timeframe: str = "4h") -> pd.DataFrame:
    files = _history_partition_files(history_root, symbol, timeframe)
    if not files:
        return pd.DataFrame()
    frames = [pd.read_parquet(path) for path in files]
    df = pd.concat(frames, ignore_index=True)
    if "timeframe" in df.columns:
        df = df[df["timeframe"].astype(str) == timeframe].copy()
    if "symbol" in df.columns:
        df = df[df["symbol"].astype(str) == symbol].copy()
    if df.empty:
        return df
    if "open_time_utc" in df.columns:
        ts = pd.to_datetime(df["open_time_utc"], utc=True, errors="coerce")
    elif "open_time" in df.columns:
        ts = pd.to_datetime(pd.to_numeric(df["open_time"], errors="coerce"), unit="ms", utc=True, errors="coerce")
    elif "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    else:
        raise ValueError("OHLCV parquet needs open_time_utc, open_time, or timestamp")
    df = df.assign(_open_ts=ts)
    for col in ("open", "high", "low", "close"):
        if col not in df.columns:
            raise ValueError(f"OHLCV parquet missing required column: {col}")
        df[col] = pd.to_numeric(df[col], errors="coerce")
    if "is_closed" in df.columns:
        df = df[df["is_closed"].fillna(True).astype(bool)].copy()
    df = df.dropna(subset=["_open_ts"]).sort_values("_open_ts", kind="mergesort")
    df = df.drop_duplicates("_open_ts", keep="last").reset_index(drop=True)
    return df


def _valid_ohlcv_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    out = df.copy()
    mask = pd.Series(True, index=out.index)
    for col in ("open", "high", "low", "close"):
        values = pd.to_numeric(out[col], errors="coerce")
        mask &= values.map(lambda x: math.isfinite(float(x)) and float(x) > 0 if not pd.isna(x) else False)
        out[col] = values
    return out[mask].copy()


def _compute_atr(ohlcv: pd.DataFrame, anchor: datetime, period: int) -> tuple[bool, float | None, str]:
    if ohlcv.empty:
        return False, None, "not_available"
    prior = _valid_ohlcv_rows(ohlcv[ohlcv["_open_ts"] < pd.Timestamp(anchor)])
    if len(prior) < period + 1:
        return False, None, "not_available"
    tail = prior.tail(period + 1).reset_index(drop=True)
    highs = tail["high"].astype(float)
    lows = tail["low"].astype(float)
    closes = tail["close"].astype(float)
    trs = []
    for idx in range(1, len(tail)):
        previous_close = closes.iloc[idx - 1]
        trs.append(max(highs.iloc[idx] - lows.iloc[idx], abs(highs.iloc[idx] - previous_close), abs(lows.iloc[idx] - previous_close)))
    if len(trs) < period:
        return False, None, "not_available"
    value = float(np.mean(trs[-period:]))
    return (True, value, "computed_from_4h_ohlcv") if math.isfinite(value) and value > 0 else (False, None, "not_available")


def _percentage(value: Any, reference_price: float | None) -> float | None:
    value_float = _finite_float_or_none(value)
    if reference_price is None or value_float is None:
        return None
    return (value_float / reference_price - 1.0) * 100.0


def _summarize_counts(frame: pd.DataFrame, column: str) -> dict[str, dict[str, int]]:
    result: dict[str, dict[str, int]] = {}
    for segment in PRIMARY_SEGMENTS:
        subset = frame[frame["segment_key"] == segment]
        counts = subset[column].value_counts(dropna=False).sort_index()
        result[segment] = {str(k): int(v) for k, v in counts.items()}
    return result


def _quantile_summary(frame: pd.DataFrame, column: str) -> dict[str, dict[str, float | None]]:
    result: dict[str, dict[str, float | None]] = {}
    for segment in PRIMARY_SEGMENTS:
        values = pd.to_numeric(frame.loc[frame["segment_key"] == segment, column], errors="coerce")
        values = values[np.isfinite(values)]
        if values.empty:
            result[segment] = {"p25": None, "median": None, "p75": None}
        else:
            result[segment] = {
                "p25": float(values.quantile(0.25)),
                "median": float(values.median()),
                "p75": float(values.quantile(0.75)),
            }
    return result


def validate_preflight(config: Backtest3AConfig) -> None:
    errors: list[str] = []
    if config.bar_timeframe != "4h":
        errors.append("bar_timeframe must be exactly '4h'")
    if not isinstance(config.path_bars, int) or not 1 <= config.path_bars <= 240:
        errors.append("path_bars must be an integer in [1, 240]")
    if config.primary_only is not True:
        errors.append("primary_only must be true for BACKTEST-3A")
    if not config.input_events_path.exists() or not config.input_events_path.is_file():
        errors.append(f"input_events_path does not exist or is not a readable file: {config.input_events_path}")
    if config.output_dir.exists() and not config.overwrite:
        errors.append(f"output_dir already exists; pass --overwrite to replace it atomically: {config.output_dir}")
    if not config.history_root.exists() or not config.history_root.is_dir():
        errors.append(f"history_root does not exist or is not a directory: {config.history_root}")
    if errors:
        raise ValueError("BACKTEST-3A preflight failed:\n- " + "\n- ".join(errors))

    events = pd.read_parquet(config.input_events_path)
    events, _mappings = _normalize_input_columns(events)
    required = {"symbol", "decision_bucket", "entry_pattern", "signal_timestamp"}
    missing = sorted(required - set(events.columns))
    if missing:
        raise ValueError(f"BACKTEST-3A preflight failed: input events missing required/mapped columns: {missing}")

    in_scope = events[
        events[["decision_bucket", "entry_pattern"]].apply(tuple, axis=1).isin(PRIMARY_SEGMENT_PAIRS)
    ]
    if not in_scope.empty:
        sample = in_scope["signal_timestamp"].dropna().head(10)
        for value in sample:
            _parse_utc_timestamp(value, field_name="signal_timestamp")


def build_exit_path_metrics(config: Backtest3AConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str, dict[str, str]]:
    events = pd.read_parquet(config.input_events_path)
    events, mappings = _normalize_input_columns(events)
    events = events.copy()
    events["decision_bucket"] = events["decision_bucket"].astype("string")
    events["entry_pattern"] = events["entry_pattern"].astype("string").fillna("none").str.strip().replace("", "none")
    events = events[events[["decision_bucket", "entry_pattern"]].apply(tuple, axis=1).isin(PRIMARY_SEGMENT_PAIRS)].copy()
    events["segment_key"] = events["decision_bucket"].astype(str) + "__" + events["entry_pattern"].astype(str)
    events["event_id"] = events.apply(lambda row: _stable_event_id(row, scenario_id=config.scenario_id, replay_id=config.replay_id), axis=1)

    ohlcv_cache: dict[str, pd.DataFrame] = {}
    event_rows: list[dict[str, Any]] = []
    bar_rows: list[dict[str, Any]] = []

    for _, row in events.iterrows():
        symbol = str(row["symbol"])
        signal_timestamp_str: str | None = None
        signal_dt: datetime | None = None
        path_status = "path_not_evaluated"
        metric_reason: str | None = None
        try:
            signal_dt = _parse_utc_timestamp(row.get("signal_timestamp"), field_name="signal_timestamp")
            signal_timestamp_str = _timestamp_string(signal_dt)
            anchor = _signal_anchor_4h(signal_dt)
        except Exception as exc:  # noqa: BLE001 - row-level not-evaluable status preserves the event.
            anchor = None
            path_status = "path_failed_invalid_input"
            metric_reason = f"invalid_signal_timestamp: {exc}"

        reference_price, reference_source, reference_status, reference_reason = _resolve_reference_price(row)
        base = {
            "event_id": row["event_id"],
            "symbol": symbol,
            "segment_key": row["segment_key"],
            "decision_bucket": str(row["decision_bucket"]),
            "entry_pattern": str(row["entry_pattern"]),
            "signal_timestamp": signal_timestamp_str,
            "reference_price": reference_price,
            "reference_price_source": reference_source,
            "reference_price_status": reference_status,
            "reference_price_reason": reference_reason,
            "required_path_bars": config.path_bars,
            "atr_4h_period": config.atr_4h_period,
        }

        if anchor is None:
            event_rows.append({
                **base,
                "path_bar_1_timestamp": None,
                "path_bar_1_open": None,
                "path_bar_1_high": None,
                "path_bar_1_low": None,
                "path_bar_1_close": None,
                "available_path_bars": 0,
                "path_coverage_ratio": 0.0,
                "path_coverage_status": path_status,
                "path_metric_reason": metric_reason,
                "mfe_pct": None,
                "mae_pct": None,
                "mfe_bar_index_4h": None,
                "mae_bar_index_4h": None,
                "time_to_mfe_hours": None,
                "time_to_mae_hours": None,
                "atr_4h_available": False,
                "atr_4h_value": None,
                "atr_4h_source": "not_available",
            })
            continue

        if symbol not in ohlcv_cache:
            ohlcv_cache[symbol] = load_ohlcv_history(config.history_root, symbol=symbol, timeframe=config.bar_timeframe)
        ohlcv = ohlcv_cache[symbol]
        valid_ohlcv = _valid_ohlcv_rows(ohlcv)
        if valid_ohlcv.empty:
            path = valid_ohlcv
        else:
            path = valid_ohlcv[valid_ohlcv["_open_ts"] >= pd.Timestamp(anchor)].head(config.path_bars).copy()
        available = int(len(path))
        if available >= config.path_bars:
            path_status = "path_evaluated"
        elif available >= 1:
            path_status = "path_partial"
        else:
            path_status = "path_not_evaluated"
        coverage_ratio = float(available / config.path_bars) if config.path_bars else 0.0

        atr_available, atr_value, atr_source = _compute_atr(valid_ohlcv, anchor, config.atr_4h_period)
        first = path.iloc[0] if available else None
        metric_reason = None
        mfe_pct = mae_pct = None
        mfe_idx = mae_idx = None
        if path_status == "path_not_evaluated":
            metric_reason = "no_post_signal_4h_bars"
        elif reference_status != "available":
            metric_reason = f"reference_price_{reference_status}"
        else:
            highs = path["high"].astype(float)
            lows = path["low"].astype(float)
            high_returns = (highs / float(reference_price) - 1.0) * 100.0
            low_returns = (lows / float(reference_price) - 1.0) * 100.0
            if high_returns.empty or low_returns.empty:
                metric_reason = "no_valid_ohlcv_bars"
            else:
                mfe_pct = float(high_returns.max())
                mae_pct = float(low_returns.min())
                mfe_idx = int(np.argmax(high_returns.to_numpy()) + 1)
                mae_idx = int(np.argmin(low_returns.to_numpy()) + 1)

        for idx, (_, bar) in enumerate(path.iterrows(), start=1):
            bar_rows.append({
                **{key: base[key] for key in ("event_id", "symbol", "segment_key", "decision_bucket", "entry_pattern", "signal_timestamp", "reference_price", "reference_price_source", "reference_price_status")},
                "bar_index_4h": idx,
                "bar_timestamp": _timestamp_string(bar["_open_ts"].to_pydatetime()),
                "open_4h": float(bar["open"]),
                "high_4h": float(bar["high"]),
                "low_4h": float(bar["low"]),
                "close_4h": float(bar["close"]),
                "return_open_pct": _percentage(bar["open"], reference_price if reference_status == "available" else None),
                "return_high_pct": _percentage(bar["high"], reference_price if reference_status == "available" else None),
                "return_low_pct": _percentage(bar["low"], reference_price if reference_status == "available" else None),
                "return_close_pct": _percentage(bar["close"], reference_price if reference_status == "available" else None),
            })

        event_rows.append({
            **base,
            "path_bar_1_timestamp": None if first is None else _timestamp_string(first["_open_ts"].to_pydatetime()),
            "path_bar_1_open": None if first is None else float(first["open"]),
            "path_bar_1_high": None if first is None else float(first["high"]),
            "path_bar_1_low": None if first is None else float(first["low"]),
            "path_bar_1_close": None if first is None else float(first["close"]),
            "available_path_bars": available,
            "path_coverage_ratio": coverage_ratio,
            "path_coverage_status": path_status,
            "path_metric_reason": metric_reason,
            "mfe_pct": mfe_pct,
            "mae_pct": mae_pct,
            "mfe_bar_index_4h": mfe_idx,
            "mae_bar_index_4h": mae_idx,
            "time_to_mfe_hours": None if mfe_idx is None else mfe_idx * 4,
            "time_to_mae_hours": None if mae_idx is None else mae_idx * 4,
            "atr_4h_available": bool(atr_available),
            "atr_4h_value": atr_value,
            "atr_4h_source": atr_source,
        })

    event_df = pd.DataFrame(event_rows, columns=EVENT_OUTPUT_COLUMNS)
    bar_df = pd.DataFrame(bar_rows, columns=BAR_OUTPUT_COLUMNS)
    if not event_df.empty:
        event_df = event_df.sort_values(["signal_timestamp", "symbol", "decision_bucket", "entry_pattern", "event_id"], kind="mergesort").reset_index(drop=True)
    if not bar_df.empty:
        bar_df = bar_df.sort_values(["signal_timestamp", "symbol", "event_id", "bar_index_4h"], kind="mergesort").reset_index(drop=True)

    summary = {
        "scenario_id": config.scenario_id,
        "replay_id": config.replay_id,
        "analysis_id": ANALYSIS_ID,
        "bar_timeframe": config.bar_timeframe,
        "required_path_bars": config.path_bars,
        "primary_scope_segments": list(PRIMARY_SEGMENTS),
        "late_monitor_included": False,
        "exit_simulation_performed": False,
        "counts": {
            "input_rows": int(len(pd.read_parquet(config.input_events_path))),
            "primary_scope_rows": int(len(event_df)),
            "bar_rows": int(len(bar_df)),
            "by_segment": {segment: int((event_df["segment_key"] == segment).sum()) if not event_df.empty else 0 for segment in PRIMARY_SEGMENTS},
        },
        "coverage_by_segment": _summarize_counts(event_df, "path_coverage_status") if not event_df.empty else {},
        "reference_price_by_segment": _summarize_counts(event_df, "reference_price_status") if not event_df.empty else {},
        "atr_4h_by_segment": _summarize_counts(event_df.assign(atr_status=event_df["atr_4h_available"].map(lambda x: "available" if x else "not_available")), "atr_status") if not event_df.empty else {},
        "mfe_pct_by_segment": _quantile_summary(event_df, "mfe_pct") if not event_df.empty else {},
        "mae_pct_by_segment": _quantile_summary(event_df, "mae_pct") if not event_df.empty else {},
        "column_mappings": mappings,
        "allowed_input_units_statement": "Allowed input types, units, coercion rules, and hard rejection rules are fully specified. Ambiguous inputs must not be silently reinterpreted.",
    }
    report = render_report(config, summary, mappings)
    return event_df, bar_df, summary, report, mappings


def render_report(config: Backtest3AConfig, summary: dict[str, Any], mappings: dict[str, str]) -> str:
    mapping_lines = [f"- `{target}` mapped from `{source}`" for target, source in sorted(mappings.items())] or ["- No column mappings were required."]
    coverage_lines = [f"- `{segment}`: {summary.get('coverage_by_segment', {}).get(segment, {})}" for segment in PRIMARY_SEGMENTS]
    ref_lines = [f"- `{segment}`: {summary.get('reference_price_by_segment', {}).get(segment, {})}" for segment in PRIMARY_SEGMENTS]
    atr_lines = [f"- `{segment}`: {summary.get('atr_4h_by_segment', {}).get(segment, {})}" for segment in PRIMARY_SEGMENTS]
    mfe_lines = [f"- `{segment}` MFE: {summary.get('mfe_pct_by_segment', {}).get(segment, {})}; MAE: {summary.get('mae_pct_by_segment', {}).get(segment, {})}" for segment in PRIMARY_SEGMENTS]
    return "\n".join([
        "# BACKTEST-3A — 4h Exit Path Metrics",
        "",
        "## Run metadata",
        f"- Analysis ID: `{ANALYSIS_ID}`",
        "- Script: `scripts/backtest/generate_exit_path_metrics_4h.py`",
        f"- Scenario ID: `{config.scenario_id}`",
        f"- Replay ID: `{config.replay_id}`",
        f"- Bar timeframe: `{config.bar_timeframe}`",
        f"- Required path bars: `{config.path_bars}`",
        "",
        "## Input / output paths",
        f"- Input events: `{config.input_events_path.as_posix()}`",
        f"- OHLCV history root: `{config.history_root.as_posix()}`",
        f"- Output directory: `{config.output_dir.as_posix()}`",
        "",
        "## Primary Trade Scope filter",
        "Rows are included iff they match exactly one of these pairs:",
        "- `early_candidates × base_reclaim`",
        "- `confirmed_candidates × ema_reclaim`",
        "- `early_candidates × early_reversal_break`",
        "",
        "`segment_key` is `{decision_bucket}__{entry_pattern}`.",
        "",
        "## Column mappings",
        *mapping_lines,
        "",
        "## Row counts by segment",
        *[f"- `{segment}`: {summary.get('counts', {}).get('by_segment', {}).get(segment, 0)}" for segment in PRIMARY_SEGMENTS],
        "",
        "## Path coverage summary by segment",
        *coverage_lines,
        "",
        "## Reference-price status summary by segment",
        *ref_lines,
        "",
        "## MFE / MAE quantiles by segment",
        *mfe_lines,
        "",
        "## ATR availability summary by segment",
        *atr_lines,
        "",
        "## Scope statements",
        "No exit simulation was performed in BACKTEST-3A.",
        "late_monitor was not included in Primary Trade Scope metrics.",
        "BACKTEST-3A is data production only and not a live-trading or exit-rule decision.",
        "Allowed input types, units, coercion rules, and hard rejection rules are fully specified. Ambiguous inputs must not be silently reinterpreted.",
        "",
        "## Prepared for BACKTEST-3B",
        "The event-level MFE/MAE, timing, return-path, and ATR diagnostic fields can support later stop, partial, trailing, and time-stop simulation research. This report does not choose or validate those rules.",
        "",
    ])


def _write_outputs_atomic(config: Backtest3AConfig, event_df: pd.DataFrame, bar_df: pd.DataFrame, summary: dict[str, Any], report: str) -> None:
    parent = config.output_dir.parent
    parent.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix=f".{config.output_dir.name}.", dir=parent))
    try:
        event_df.to_parquet(tmp / "exit_path_metrics_4h.parquet", index=False)
        event_df.to_csv(tmp / "exit_path_metrics_4h.csv", index=False)
        bar_df.to_parquet(tmp / "exit_path_returns_by_bar.parquet", index=False)
        bar_df.to_csv(tmp / "exit_path_returns_by_bar.csv", index=False)
        (tmp / "exit_path_metrics_4h_summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (tmp / "exit_path_metrics_4h_report.md").write_text(report, encoding="utf-8")
        for filename in REQUIRED_OUTPUT_FILES:
            if not (tmp / filename).exists():
                raise RuntimeError(f"missing generated output: {filename}")
        if config.output_dir.exists():
            shutil.rmtree(config.output_dir)
        tmp.replace(config.output_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True)
        raise


def run(config: Backtest3AConfig) -> dict[str, Any]:
    if config.strict_preflight:
        validate_preflight(config)
    event_df, bar_df, summary, report, _ = build_exit_path_metrics(config)
    _write_outputs_atomic(config, event_df, bar_df, summary, report)
    return summary


def main() -> None:
    args = _parse_args()
    config = Backtest3AConfig(
        input_events_path=args.input_events_path,
        scenario_id=args.scenario_id,
        replay_id=args.replay_id,
        bar_timeframe=args.bar_timeframe,
        path_bars=args.path_bars,
        output_dir=args.output_dir,
        strict_preflight=args.strict_preflight,
        overwrite=args.overwrite,
        history_root=args.history_root,
    )
    summary = run(config)
    print(json.dumps({"analysis_id": ANALYSIS_ID, "output_dir": config.output_dir.as_posix(), "counts": summary["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
