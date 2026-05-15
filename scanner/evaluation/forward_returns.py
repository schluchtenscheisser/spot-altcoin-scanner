from __future__ import annotations

from datetime import datetime
import math
from pathlib import Path
from typing import Any

import pandas as pd

SIGNAL_EVENTS = {"first_watch", "first_early_ready", "first_confirmed_ready"}
TERMINAL_EVENTS = {"first_late", "first_chased", "first_rejected"}
HORIZONS = (1, 3, 5, 10)


def _finite_pos(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) > 0


def _event_daily_bar_id(event_bar_id: Any, event_bar_id_type: Any) -> str | None:
    if not isinstance(event_bar_id, str) or not event_bar_id or event_bar_id == "unknown":
        return None
    if event_bar_id_type == "daily_bar_id":
        return event_bar_id
    if event_bar_id_type == "intraday_bar_id":
        return event_bar_id.split("T", 1)[0]
    return None


def _event_bar_close(df: pd.DataFrame, day: str | None) -> tuple[float | None, str]:
    if not isinstance(day, str):
        return None, "missing_or_unknown_event_bar_id"
    if df.empty:
        return None, "missing_ohlcv_history"
    if day not in set(df["daily_bar_id"].tolist()):
        return None, "missing_event_bar_ohlcv"
    close_value = df.loc[df["daily_bar_id"] == day, "close"].iloc[0]
    if not _finite_pos(close_value):
        return None, "invalid_event_bar_close"
    return float(close_value), "ok"


def _reference_price_from_event(event: dict[str, Any], df: pd.DataFrame) -> tuple[float | None, str, str, str, bool]:
    day = _event_daily_bar_id(event.get("event_bar_id"), event.get("event_bar_id_type"))
    event_type = event.get("event_type")
    persisted = None
    has_persisted = False
    if event_type == "first_early_ready":
        persisted = event.get("close_at_early_entry_bar")
        has_persisted = persisted is not None
    elif event_type == "first_confirmed_ready":
        persisted = event.get("close_at_confirmed_entry_bar")
        has_persisted = persisted is not None

    if event_type in {"first_early_ready", "first_confirmed_ready"} and _finite_pos(persisted):
        return float(persisted), "ok", "persisted_state_reference", "persisted_state_reference_available", False

    close, close_status = _event_bar_close(df, day)
    if close is not None:
        if event_type in {"first_early_ready", "first_confirmed_ready"}:
            return close, "ok", "ohlcv_event_bar_close", "fallback_missing_persisted_state_reference", True
        if event_type == "first_watch":
            return close, "ok", "ohlcv_event_bar_close", "watch_event_bar_close", False
        return close, "ok", "ohlcv_event_bar_close", "event_bar_close_no_persisted_state_reference_required", False

    if event_type == "first_watch":
        return None, "reference_price_not_evaluable", "not_available", close_status, False
    if has_persisted and not _finite_pos(persisted) and close_status == "missing_or_unknown_event_bar_id":
        return None, "reference_price_not_evaluable", "not_available", "invalid_persisted_state_reference", True
    return None, "reference_price_not_evaluable", "not_available", close_status, event_type in {"first_early_ready", "first_confirmed_ready"}


def _load_daily_ohlcv(project_root: Path, symbol: str, history_root: str = "snapshots/history") -> pd.DataFrame:
    base = project_root / history_root / "ohlcv" / "timeframe=1d" / f"symbol={symbol}"
    files = sorted(base.glob("year=*/month=*/*.parquet"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(p) for p in files], ignore_index=True)
    if "daily_bar_id" not in df.columns:
        if "close_time_utc_ms" in df.columns:
            df["daily_bar_id"] = pd.to_datetime(df["close_time_utc_ms"], unit="ms", utc=True).dt.strftime("%Y-%m-%d")
        elif "timestamp" in df.columns:
            df["daily_bar_id"] = pd.to_datetime(df["timestamp"], utc=True).dt.strftime("%Y-%m-%d")
        else:
            raise ValueError("OHLCV parquet needs daily_bar_id or close_time_utc_ms/timestamp")
    req = {"daily_bar_id", "close", "high", "low"}
    if not req.issubset(df.columns):
        raise ValueError("OHLCV parquet missing required columns")
    df = df.sort_values("daily_bar_id", kind="mergesort").drop_duplicates("daily_bar_id", keep="last")
    return df.reset_index(drop=True)


def build_signal_metrics(
    events: list[dict[str, Any]],
    *,
    project_root: Path,
    history_root: str = "snapshots/history",
    include_first_watch_metrics: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    by_symbol: dict[str, pd.DataFrame] = {}
    signal_rows: list[dict[str, Any]] = []
    terminal_rows: list[dict[str, Any]] = []
    transition_rows: list[dict[str, Any]] = []
    metric_status_counts: dict[str, int] = {}
    missing_persisted_refs = 0

    grouped: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for e in events:
        grouped.setdefault((str(e["symbol"]), int(e["setup_cycle_id"])), []).append(e)

    for (symbol, cycle), rows in sorted(grouped.items()):
        rows = sorted(rows, key=lambda r: (int(r["event_order"]), str(r["event_timestamp_utc"]), str(r["event_type"])))
        for source, target in [
            ("first_watch", "first_early_ready"),
            ("first_watch", "first_confirmed_ready"),
            ("first_watch", "first_rejected"),
            ("first_early_ready", "first_confirmed_ready"),
            ("first_confirmed_ready", "first_late"),
            ("first_confirmed_ready", "first_chased"),
            ("first_confirmed_ready", "first_rejected"),
            ("first_early_ready", "first_late"),
            ("first_early_ready", "first_chased"),
            ("first_early_ready", "first_rejected"),
        ]:
            s = next((x for x in rows if x["event_type"] == source), None)
            t = next((x for x in rows if x["event_type"] == target), None)
            status = "ok" if (s and t) else "target_event_not_observed"
            elapsed_hours = None
            if s and t:
                dt_s = datetime.fromisoformat(str(s["event_timestamp_utc"]).replace("Z", "+00:00"))
                dt_t = datetime.fromisoformat(str(t["event_timestamp_utc"]).replace("Z", "+00:00"))
                elapsed_hours = (dt_t - dt_s).total_seconds() / 3600.0
            transition_rows.append({
                "symbol": symbol,
                "setup_cycle_id": cycle,
                "source_event_type": source,
                "target_event_type": target,
                "source_event_timestamp_utc": s["event_timestamp_utc"] if s else None,
                "target_event_timestamp_utc": t["event_timestamp_utc"] if t else None,
                "source_event_bar_id": s["event_bar_id"] if s else None,
                "target_event_bar_id": t["event_bar_id"] if t else None,
                "bars_between": None,
                "elapsed_hours": elapsed_hours,
                "transition_status": status,
            })

        for event in rows:
            if event["event_type"] in TERMINAL_EVENTS:
                terminal_rows.append({
                    **{k: event.get(k) for k in [
                        "symbol", "setup_cycle_id", "event_type", "event_order", "event_timestamp_utc", "event_bar_id", "event_bar_id_type",
                        "state_machine_state", "decision_bucket", "market_phase", "market_phase_confidence", "state_confidence",
                        "first_observed_run_id", "first_observed_run_mode", "source_snapshot_path",
                    ]},
                    "return_metrics_status": "terminal_event_returns_out_of_scope",
                })
                continue
            if event["event_type"] not in SIGNAL_EVENTS:
                continue
            if not include_first_watch_metrics and event["event_type"] == "first_watch":
                continue

            if symbol not in by_symbol:
                by_symbol[symbol] = _load_daily_ohlcv(project_root, symbol, history_root=history_root)
            df = by_symbol[symbol]
            metric_context_fields = [
                "symbol", "setup_cycle_id", "event_type", "event_order", "event_timestamp_utc", "event_bar_id", "event_bar_id_type",
                "run_id", "scan_mode", "first_observed_run_id", "first_observed_run_mode", "source_snapshot_path",
                "schema_version", "market_phase", "market_phase_confidence", "state_machine_state", "state_confidence",
                "decision_bucket", "priority_score", "entry_pattern", "execution_status_raw", "execution_size_class",
                "is_tradeable_candidate", "is_reduced_size_eligible", "recommended_position_factor", "execution_grade_effective",
                "available_depth_ratio", "depth_ratio_band", "candidate_excluded", "universe_category",
                "is_operational_trade_candidate", "operational_tradeability_compat", "operational_tradeability_source",
                "entry_location_status", "entry_action_hint", "range_high_proximity_warning",
            ]
            row = {**{k: event.get(k) for k in metric_context_fields}}

            ref_price, ref_status, ref_source, ref_reason, counted_missing_persisted = _reference_price_from_event(event, df)
            if counted_missing_persisted:
                missing_persisted_refs += 1

            row["reference_price"] = ref_price
            row["reference_price_status"] = ref_status
            row["reference_price_source"] = ref_source
            row["reference_price_reason"] = ref_reason

            ref_day = _event_daily_bar_id(event.get("event_bar_id"), event.get("event_bar_id_type"))
            idx_map = {str(d): i for i, d in enumerate(df["daily_bar_id"].tolist())} if not df.empty else {}
            start_idx = idx_map.get(ref_day) if isinstance(ref_day, str) else None

            for h in HORIZONS:
                k_ret = f"forward_return_{h}d_pct"
                k_mfe = f"mfe_{h}d_pct"
                k_mae = f"mae_{h}d_pct"
                k_status = f"metric_status_{h}d"
                if ref_status != "ok" or ref_price is None:
                    row[k_ret] = None
                    row[k_mfe] = None
                    row[k_mae] = None
                    row[k_status] = "missing_ohlcv_history" if ref_reason == "missing_ohlcv_history" else ref_status
                elif df.empty:
                    row[k_ret] = None
                    row[k_mfe] = None
                    row[k_mae] = None
                    row[k_status] = "missing_ohlcv_history"
                elif start_idx is None or (start_idx + h) >= len(df):
                    row[k_ret] = None
                    row[k_mfe] = None
                    row[k_mae] = None
                    row[k_status] = "insufficient_future_data"
                else:
                    end_idx = start_idx + h
                    close = float(df.iloc[end_idx]["close"])
                    window = df.iloc[start_idx + 1 : end_idx + 1]
                    hi = float(window["high"].max())
                    lo = float(window["low"].min())
                    row[k_ret] = ((close - ref_price) / ref_price) * 100.0
                    row[k_mfe] = ((hi - ref_price) / ref_price) * 100.0
                    row[k_mae] = ((lo - ref_price) / ref_price) * 100.0
                    row[k_status] = "ok"
                metric_status_counts[row[k_status]] = metric_status_counts.get(row[k_status], 0) + 1
            signal_rows.append(row)

    signal_df = pd.DataFrame(signal_rows)
    terminal_df = pd.DataFrame(terminal_rows)
    transitions_df = pd.DataFrame(transition_rows)
    diagnostics = {
        "metric_status_counts": metric_status_counts,
        "missing_persisted_reference_price_count": missing_persisted_refs,
    }
    return signal_df, terminal_df, transitions_df, diagnostics
