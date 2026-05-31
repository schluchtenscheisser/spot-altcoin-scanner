from __future__ import annotations

import argparse
import json
import math
import shutil
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

ANALYSIS_ID = "BACKTEST-3B_EXIT_MODEL_SIMULATION_4H"
DEFAULT_ROOT = Path("evaluation/backtest/reports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z")
DEFAULT_INPUT_EVENTS_PATH = DEFAULT_ROOT / "exit_path_metrics_4h/exit_path_metrics_4h.parquet"
DEFAULT_INPUT_BARS_PATH = DEFAULT_ROOT / "exit_path_metrics_4h/exit_path_returns_by_bar.parquet"
DEFAULT_INPUT_SUMMARY_PATH = DEFAULT_ROOT / "exit_path_metrics_4h/exit_path_metrics_4h_summary.json"
DEFAULT_OUTPUT_DIR = DEFAULT_ROOT / "exit_model_simulation_4h"
REQUIRED_OUTPUT_FILES = (
    "exit_model_simulation_4h.parquet", "exit_model_simulation_4h.csv",
    "exit_model_segment_summary.parquet", "exit_model_segment_summary.csv",
    "exit_model_simulation_summary.json", "exit_model_simulation_report.md",
)
EVENT_COLUMNS = {
    "event_id", "symbol", "segment_key", "decision_bucket", "entry_pattern", "signal_timestamp",
    "reference_price", "reference_price_source", "reference_price_status", "path_coverage_status",
    "available_path_bars", "required_path_bars", "mfe_pct", "mae_pct", "mfe_bar_index_4h",
    "mae_bar_index_4h", "time_to_mfe_hours", "time_to_mae_hours", "atr_4h_available",
    "atr_4h_value", "atr_4h_period", "atr_4h_source",
}
BAR_COLUMNS = {
    "event_id", "symbol", "segment_key", "decision_bucket", "entry_pattern", "signal_timestamp",
    "bar_index_4h", "bar_timestamp", "open_4h", "high_4h", "low_4h", "close_4h",
    "return_open_pct", "return_high_pct", "return_low_pct", "return_close_pct", "reference_price",
    "reference_price_source", "reference_price_status",
}
EVENT_OUTPUT_COLUMNS = [
    "event_id", "symbol", "segment_key", "decision_bucket", "entry_pattern", "signal_timestamp",
    "exit_model_id", "simulation_status", "initial_stop_mode", "initial_stop_value", "stop_price",
    "partial_mode", "partial_trigger_value", "partial_trigger_price", "partial_size", "trail_mode",
    "time_stop_hours", "exit_reason", "exit_bar_index_4h", "exit_timestamp", "exit_price",
    "gross_return_pct", "reference_price", "reference_price_source", "mfe_pct", "mae_pct",
    "mfe_bar_index_4h", "mae_bar_index_4h", "time_to_mfe_hours", "time_to_mae_hours",
    "partial_filled", "partial_bar_index_4h", "partial_timestamp", "stopped_before_partial",
    "stopped_before_mfe", "partial_before_stop", "mfe_before_mae", "mae_before_mfe",
    "recovery_after_initial_mae", "path_coverage_status", "available_path_bars", "required_path_bars",
]
SEGMENT_SUMMARY_COLUMNS = [
    "segment_key", "exit_model_id", "simulation_status_evaluated_count", "simulation_status_not_evaluable_count",
    "trade_count", "median_return_pct", "mean_return_pct", "p25_return_pct", "p75_return_pct", "win_rate",
    "loss_rate", "median_exit_hours", "partial_fill_rate", "stop_rate", "time_exit_rate", "trail_exit_rate",
    "path_incomplete_rate", "stopped_before_partial_rate", "stopped_before_mfe_rate", "partial_before_stop_rate",
    "mfe_before_mae_rate", "mae_before_mfe_rate", "recovery_after_initial_mae_rate",
]

@dataclass(frozen=True)
class Backtest3BConfig:
    input_events_path: Path = DEFAULT_INPUT_EVENTS_PATH
    input_bars_path: Path = DEFAULT_INPUT_BARS_PATH
    input_summary_path: Path = DEFAULT_INPUT_SUMMARY_PATH
    output_dir: Path = DEFAULT_OUTPUT_DIR
    time_stops_hours: tuple[int, ...] = (24, 48, 72, 96, 120, 168)
    atr_stop_multipliers: tuple[float, ...] = (1.0, 1.2, 1.5, 2.0)
    fixed_stop_pcts: tuple[float, ...] = (5.0, 8.0, 12.0)
    fixed_partial_trigger_pcts: tuple[float, ...] = (5.0, 7.5, 10.0)
    r_partial_triggers: tuple[float, ...] = (1.0, 1.5, 2.0)
    partial_sizes: tuple[float, ...] = (0.4, 0.5)
    trail_modes: tuple[str, ...] = ("none", "low_2bars", "low_3bars")
    strict_preflight: bool = True
    overwrite: bool = False

@dataclass(frozen=True)
class ExitModel:
    initial_stop_mode: str
    initial_stop_value: float
    partial_mode: str
    partial_trigger_value: float | None
    partial_size: float
    trail_mode: str
    time_stop_hours: int

    @property
    def exit_model_id(self) -> str:
        stop = f"atr{_token(self.initial_stop_value, keep_decimal=True)}" if self.initial_stop_mode == "atr" else f"fixed{_token(self.initial_stop_value)}pct"
        if self.partial_mode == "none":
            partial = "none_0pct"
        elif self.partial_mode == "fixed_pct":
            partial = f"fixed{_token(self.partial_trigger_value)}pct_{_token(self.partial_size * 100)}pct"
        else:
            partial = f"r{_token(self.partial_trigger_value, keep_decimal=True)}_{_token(self.partial_size * 100)}pct"
        trail = {"none": "none", "low_2bars": "low2bars", "low_3bars": "low3bars"}[self.trail_mode]
        return f"stop_{stop}__partial_{partial}__trail_{trail}__time{self.time_stop_hours}h"

def _token(value: Any, *, keep_decimal: bool = False) -> str:
    number = float(value)
    text = f"{number:.12g}"
    if keep_decimal and "." not in text:
        text += ".0"
    return text.replace(".", "p")

def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool): return None
    try: number = float(value)
    except (TypeError, ValueError): return None
    return number if math.isfinite(number) else None

def _nullable_bool(value: bool | None) -> bool | None:
    return None if value is None else bool(value)

def _mean_bool(values: Iterable[Any]) -> float | None:
    series = pd.Series(list(values), dtype="boolean").dropna()
    return None if series.empty else float(series.mean())

def _read_table(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".parquet": return pd.read_parquet(path)
    if path.suffix.lower() == ".csv": return pd.read_csv(path)
    raise ValueError(f"unsupported table extension for {path}; use explicit .parquet or .csv path")

def _positive_list(values: Iterable[Any], name: str, *, integers: bool = False) -> tuple[Any, ...]:
    result = []
    for raw in values:
        value = _finite(raw)
        if value is None or value <= 0 or (integers and not value.is_integer()):
            raise ValueError(f"{name} values must be finite positive {'integers' if integers else 'numbers'}: {raw!r}")
        result.append(int(value) if integers else float(value))
    if not result: raise ValueError(f"{name} must not be empty")
    return tuple(result)

def validate_config(config: Backtest3BConfig) -> None:
    _positive_list(config.time_stops_hours, "time_stops_hours", integers=True)
    if any(value % 4 for value in config.time_stops_hours): raise ValueError("time_stops_hours values must divide exactly by 4")
    _positive_list(config.atr_stop_multipliers, "atr_stop_multipliers")
    _positive_list(config.fixed_stop_pcts, "fixed_stop_pcts")
    _positive_list(config.fixed_partial_trigger_pcts, "fixed_partial_trigger_pcts")
    _positive_list(config.r_partial_triggers, "r_partial_triggers")
    sizes = _positive_list(config.partial_sizes, "partial_sizes")
    if any(value > 1 for value in sizes): raise ValueError("partial_sizes values must be in (0, 1]")
    if not config.trail_modes or any(value not in {"none", "low_2bars", "low_3bars"} for value in config.trail_modes):
        raise ValueError("trail_modes values must be one of: none, low_2bars, low_3bars")

def build_exit_model_matrix(config: Backtest3BConfig = Backtest3BConfig()) -> list[ExitModel]:
    validate_config(config)
    models: list[ExitModel] = []
    for stop_mode, stop_values in (("atr", config.atr_stop_multipliers), ("fixed_pct", config.fixed_stop_pcts)):
        partials: list[tuple[str, float | None, float, str]] = [("none", None, 0.0, "none")]
        partials += [("fixed_pct", trigger, size, trail) for trigger in config.fixed_partial_trigger_pcts for size in config.partial_sizes for trail in config.trail_modes]
        if stop_mode == "atr": partials += [("r_multiple", trigger, size, trail) for trigger in config.r_partial_triggers for size in config.partial_sizes for trail in config.trail_modes]
        for stop in stop_values:
            for partial_mode, trigger, size, trail in partials:
                for hours in config.time_stops_hours:
                    models.append(ExitModel(stop_mode, float(stop), partial_mode, trigger, float(size), trail, int(hours)))
    return sorted(models, key=lambda model: model.exit_model_id)

def validate_preflight(config: Backtest3BConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    validate_config(config)
    errors = []
    for name, path in (("input_events_path", config.input_events_path), ("input_bars_path", config.input_bars_path), ("input_summary_path", config.input_summary_path)):
        if not path.exists() or not path.is_file(): errors.append(f"{name} does not exist or is not a readable file: {path}")
    if config.output_dir.exists() and not config.overwrite: errors.append(f"output_dir already exists; pass --overwrite to replace it atomically: {config.output_dir}")
    if errors: raise ValueError("BACKTEST-3B preflight failed:\n- " + "\n- ".join(errors))
    events, bars = _read_table(config.input_events_path), _read_table(config.input_bars_path)
    try: input_summary = json.loads(config.input_summary_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc: raise ValueError(f"BACKTEST-3B preflight failed: invalid input summary: {exc}") from exc
    missing_events, missing_bars = sorted(EVENT_COLUMNS - set(events)), sorted(BAR_COLUMNS - set(bars))
    if missing_events or missing_bars: raise ValueError(f"BACKTEST-3B preflight failed: missing required columns: events={missing_events}, bars={missing_bars}")
    if events["event_id"].isna().any() or events["event_id"].duplicated().any(): raise ValueError("BACKTEST-3B preflight failed: event-level event_id must be present and unique")
    unknown = sorted(set(bars["event_id"].dropna()) - set(events["event_id"]))
    if unknown: raise ValueError(f"BACKTEST-3B preflight failed: bar-level rows reference unknown event IDs: {unknown[:5]}")
    indexes = pd.to_numeric(bars["bar_index_4h"], errors="coerce")
    if indexes.isna().any() or (indexes <= 0).any() or (indexes % 1 != 0).any(): raise ValueError("BACKTEST-3B preflight failed: bar_index_4h values must be positive integers")
    if bars.assign(_index=indexes).duplicated(["event_id", "_index"]).any(): raise ValueError("BACKTEST-3B preflight failed: duplicate event_id/bar_index_4h rows")
    bars = bars.assign(bar_index_4h=indexes.astype(int)).sort_values(["event_id", "bar_index_4h", "bar_timestamp"], kind="stable").reset_index(drop=True)
    return events.copy(), bars, input_summary

def _base_row(event: pd.Series, model: ExitModel) -> dict[str, Any]:
    mfe_i, mae_i = _finite(event.get("mfe_bar_index_4h")), _finite(event.get("mae_bar_index_4h"))
    return {**{key: event.get(key) for key in ("event_id", "symbol", "segment_key", "decision_bucket", "entry_pattern", "signal_timestamp")},
        "exit_model_id": model.exit_model_id, "simulation_status": "not_evaluable", "initial_stop_mode": model.initial_stop_mode,
        "initial_stop_value": model.initial_stop_value, "stop_price": None, "partial_mode": model.partial_mode,
        "partial_trigger_value": model.partial_trigger_value, "partial_trigger_price": None, "partial_size": model.partial_size,
        "trail_mode": model.trail_mode, "time_stop_hours": model.time_stop_hours, "exit_reason": None, "exit_bar_index_4h": None,
        "exit_timestamp": None, "exit_price": None, "gross_return_pct": None, "reference_price": event.get("reference_price"),
        "reference_price_source": event.get("reference_price_source"), "mfe_pct": event.get("mfe_pct"), "mae_pct": event.get("mae_pct"),
        "mfe_bar_index_4h": event.get("mfe_bar_index_4h"), "mae_bar_index_4h": event.get("mae_bar_index_4h"),
        "time_to_mfe_hours": event.get("time_to_mfe_hours"), "time_to_mae_hours": event.get("time_to_mae_hours"),
        "partial_filled": None, "partial_bar_index_4h": None, "partial_timestamp": None, "stopped_before_partial": None,
        "stopped_before_mfe": None, "partial_before_stop": None, "mfe_before_mae": None if mfe_i is None or mae_i is None else mfe_i < mae_i,
        "mae_before_mfe": None if mfe_i is None or mae_i is None else mae_i < mfe_i, "recovery_after_initial_mae": None,
        "path_coverage_status": event.get("path_coverage_status"), "available_path_bars": event.get("available_path_bars"), "required_path_bars": event.get("required_path_bars")}

def _finish(row: dict[str, Any], *, reason: str, bar: pd.Series | None = None, price: float | None = None, partial: bool = False, stop_bar: int | None = None) -> dict[str, Any]:
    row["exit_reason"] = reason
    if reason.startswith("not_evaluable") or reason.endswith("path_incomplete"):
        row.update(simulation_status="not_evaluable", exit_price=None, gross_return_pct=None, exit_bar_index_4h=None, exit_timestamp=None)
        return row
    assert bar is not None and price is not None
    row.update(simulation_status="evaluated", exit_bar_index_4h=int(bar["bar_index_4h"]), exit_timestamp=bar["bar_timestamp"], exit_price=float(price))
    reference = float(row["reference_price"])
    remaining = (price / reference - 1) * 100
    if partial:
        partial_return = (float(row["partial_trigger_price"]) / reference - 1) * 100
        row["gross_return_pct"] = row["partial_size"] * partial_return + (1 - row["partial_size"]) * remaining
    else: row["gross_return_pct"] = remaining
    row["stopped_before_partial"] = reason == "stop" and row["partial_filled"] is False
    row["partial_before_stop"] = reason == "partial_then_stop"
    if stop_bar is not None:
        mfe = _finite(row["mfe_bar_index_4h"])
        row["stopped_before_mfe"] = None if mfe is None else stop_bar < mfe
    else: row["stopped_before_mfe"] = False
    return row

def simulate_event_model(event: pd.Series, event_bars: pd.DataFrame, model: ExitModel) -> dict[str, Any]:
    row = _base_row(event, model)
    reference = _finite(event.get("reference_price"))
    if reference is None or reference <= 0 or event.get("reference_price_status") != "available": return _finish(row, reason="not_evaluable_missing_reference_price")
    if model.initial_stop_mode == "atr":
        atr = _finite(event.get("atr_4h_value"))
        if atr is None or atr <= 0 or event.get("atr_4h_available") is not True: return _finish(row, reason="not_evaluable_missing_atr")
        stop = reference - atr * model.initial_stop_value
    else: stop = reference * (1 - model.initial_stop_value / 100)
    if not math.isfinite(stop) or stop <= 0 or stop >= reference: return _finish(row, reason="not_evaluable_invalid_stop")
    row["stop_price"] = stop
    trigger = None if model.partial_mode == "none" else reference * (1 + model.partial_trigger_value / 100) if model.partial_mode == "fixed_pct" else reference + model.partial_trigger_value * (reference - stop)
    if trigger is not None and (not math.isfinite(trigger) or trigger <= reference): return _finish(row, reason="not_evaluable_invalid_partial_trigger")
    row["partial_trigger_price"] = trigger
    if event_bars.empty: return _finish(row, reason="not_evaluable_missing_bar_path")
    bar_map = {int(bar.bar_index_4h): bar for _, bar in event_bars.iterrows()}
    mae_index = _finite(event.get("mae_bar_index_4h"))
    if mae_index is not None:
        later_closes = [_finite(bar.get("return_close_pct")) for index, bar in bar_map.items() if index > mae_index]
        valid = [value for value in later_closes if value is not None]
        row["recovery_after_initial_mae"] = None if not valid else any(value >= 0 for value in valid)
    partial_bar = None
    row["partial_filled"] = False
    time_index = model.time_stop_hours // 4
    for index in range(1, time_index + 1):
        bar = bar_map.get(index)
        if bar is None: return _finish(row, reason="partial_then_path_incomplete" if partial_bar else "path_incomplete")
        high, low, close = (_finite(bar.get(name)) for name in ("high_4h", "low_4h", "close_4h"))
        if high is None or low is None or close is None: return _finish(row, reason="partial_then_path_incomplete" if partial_bar else "path_incomplete")
        if low <= stop: return _finish(row, reason="partial_then_stop" if partial_bar else "stop", bar=bar, price=stop, partial=partial_bar is not None, stop_bar=index)
        if partial_bar is None and trigger is not None and high >= trigger:
            partial_bar = index; row.update(partial_filled=True, partial_bar_index_4h=index, partial_timestamp=bar["bar_timestamp"])
        if partial_bar is not None and index > partial_bar and model.trail_mode != "none":
            window = 2 if model.trail_mode == "low_2bars" else 3
            preceding = [bar_map.get(prior) for prior in range(index - window, index)]
            lows = [_finite(prior.get("low_4h")) for prior in preceding if prior is not None]
            if len(lows) == window and all(value is not None for value in lows) and close < min(lows):
                return _finish(row, reason="partial_then_trail", bar=bar, price=close, partial=True)
        if index == time_index: return _finish(row, reason="partial_then_time_stop" if partial_bar else "time_stop", bar=bar, price=close, partial=partial_bar is not None)
    raise AssertionError("unreachable")

def build_segment_summary(rows: pd.DataFrame) -> pd.DataFrame:
    output = []
    for (segment, model), frame in rows.groupby(["segment_key", "exit_model_id"], sort=True, dropna=False):
        evaluated = frame[frame["simulation_status"] == "evaluated"]
        gross = pd.to_numeric(evaluated["gross_return_pct"], errors="coerce").dropna(); exits = pd.to_numeric(evaluated["exit_bar_index_4h"], errors="coerce").dropna()
        rate = lambda column: _mean_bool(evaluated[column])
        output.append({"segment_key": segment, "exit_model_id": model, "simulation_status_evaluated_count": int(len(evaluated)),
            "simulation_status_not_evaluable_count": int((frame["simulation_status"] == "not_evaluable").sum()), "trade_count": int(len(evaluated)),
            "median_return_pct": None if gross.empty else float(gross.median()), "mean_return_pct": None if gross.empty else float(gross.mean()),
            "p25_return_pct": None if gross.empty else float(gross.quantile(.25)), "p75_return_pct": None if gross.empty else float(gross.quantile(.75)),
            "win_rate": None if gross.empty else float((gross > 0).mean()), "loss_rate": None if gross.empty else float((gross < 0).mean()),
            "median_exit_hours": None if exits.empty else float((exits * 4).median()), "partial_fill_rate": rate("partial_filled"),
            "stop_rate": None if evaluated.empty else float(evaluated["exit_reason"].isin({"stop", "partial_then_stop"}).mean()),
            "time_exit_rate": None if evaluated.empty else float(evaluated["exit_reason"].isin({"time_stop", "partial_then_time_stop"}).mean()),
            "trail_exit_rate": None if evaluated.empty else float((evaluated["exit_reason"] == "partial_then_trail").mean()),
            "path_incomplete_rate": float(frame["exit_reason"].isin({"path_incomplete", "partial_then_path_incomplete"}).mean()),
            "stopped_before_partial_rate": rate("stopped_before_partial"), "stopped_before_mfe_rate": rate("stopped_before_mfe"),
            "partial_before_stop_rate": rate("partial_before_stop"), "mfe_before_mae_rate": rate("mfe_before_mae"),
            "mae_before_mfe_rate": rate("mae_before_mfe"), "recovery_after_initial_mae_rate": rate("recovery_after_initial_mae")})
    result = pd.DataFrame(output, columns=SEGMENT_SUMMARY_COLUMNS)
    return result.sort_values(["segment_key", "median_return_pct", "exit_model_id"], ascending=[True, False, True], na_position="last", kind="stable").reset_index(drop=True)

def build_outputs(config: Backtest3BConfig) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], str]:
    events, bars, source = validate_preflight(config); models = build_exit_model_matrix(config); grouped = {key: frame for key, frame in bars.groupby("event_id", sort=False)}
    records = [simulate_event_model(event, grouped.get(event["event_id"], pd.DataFrame()), model) for _, event in events.iterrows() for model in models]
    rows = pd.DataFrame(records, columns=EVENT_OUTPUT_COLUMNS).sort_values(["segment_key", "event_id", "exit_model_id"], kind="stable").reset_index(drop=True)
    segments = {str(key): int(value) for key, value in events["segment_key"].value_counts().sort_index().items()}
    segment_summary = build_segment_summary(rows)
    best = []
    for segment, frame in segment_summary[segment_summary["trade_count"] > 0].groupby("segment_key", sort=True):
        best.append(frame.sort_values(["median_return_pct", "exit_model_id"], ascending=[False, True], kind="stable").iloc[0][["segment_key", "exit_model_id", "median_return_pct", "trade_count"]].to_dict())
    summary = {"analysis_id": ANALYSIS_ID, "scenario_id": source.get("scenario_id"), "replay_id": source.get("replay_id"),
        "input_events_path": config.input_events_path.as_posix(), "input_bars_path": config.input_bars_path.as_posix(), "input_summary_path": config.input_summary_path.as_posix(), "output_dir": config.output_dir.as_posix(),
        "event_count": int(len(events)), "bar_row_count": int(len(bars)), "exit_model_variant_count": int(len(models)), "event_model_row_count": int(len(rows)),
        "simulation_status_counts": {str(k): int(v) for k, v in rows["simulation_status"].value_counts().sort_index().items()}, "segments": segments,
        "model_grid": {key: list(value) if isinstance(value, tuple) else value for key, value in asdict(config).items() if key in {"time_stops_hours", "atr_stop_multipliers", "fixed_stop_pcts", "fixed_partial_trigger_pcts", "r_partial_triggers", "partial_sizes", "trail_modes"}},
        "best_by_segment_observed_in_sample": best, "created_utc": datetime.now(UTC).isoformat().replace("+00:00", "Z"), "exit_simulation_performed": True,
        "late_monitor_included": False, "fees_included": False, "slippage_included": False, "execution_simulation_included": False}
    report = render_report(summary)
    return rows, segment_summary, summary, report

def render_report(summary: dict[str, Any]) -> str:
    best = [f"- `{row['segment_key']}`: `{row['exit_model_id']}` (median `{row['median_return_pct']:.6g}%`, trades `{row['trade_count']}`)" for row in summary["best_by_segment_observed_in_sample"]]
    return "\n".join(["# BACKTEST-3B 4h Exit Model Simulation", "", "Analytics-only in-sample evidence. This report does not define a live exit rule.", "", "## Scope", "", "- Closed-candle-only path simulation", "- Fees, slippage, and execution simulation are excluded", "- `late_monitor` is excluded", "", "## Counts", "", f"- Events: {summary['event_count']}", f"- Models: {summary['exit_model_variant_count']}", f"- Event-model rows: {summary['event_model_row_count']}", "", "## best_by_segment_observed_in_sample", "", *(best or ["- No evaluable rows."]), ""])

def _write_outputs_atomic(config: Backtest3BConfig, rows: pd.DataFrame, segments: pd.DataFrame, summary: dict[str, Any], report: str) -> None:
    parent = config.output_dir.parent; parent.mkdir(parents=True, exist_ok=True); tmp = Path(tempfile.mkdtemp(prefix=f".{config.output_dir.name}.", dir=parent))
    try:
        rows.to_parquet(tmp / REQUIRED_OUTPUT_FILES[0], index=False); rows.to_csv(tmp / REQUIRED_OUTPUT_FILES[1], index=False)
        segments.to_parquet(tmp / REQUIRED_OUTPUT_FILES[2], index=False); segments.to_csv(tmp / REQUIRED_OUTPUT_FILES[3], index=False)
        (tmp / REQUIRED_OUTPUT_FILES[4]).write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (tmp / REQUIRED_OUTPUT_FILES[5]).write_text(report, encoding="utf-8")
        if config.output_dir.exists(): shutil.rmtree(config.output_dir)
        tmp.replace(config.output_dir)
    except Exception:
        shutil.rmtree(tmp, ignore_errors=True); raise

def run(config: Backtest3BConfig) -> dict[str, Any]:
    rows, segments, summary, report = build_outputs(config); _write_outputs_atomic(config, rows, segments, summary, report); return summary

def _csv(raw: str, cast: Any) -> tuple[Any, ...]:
    try: return tuple(cast(item.strip()) for item in raw.split(",") if item.strip())
    except ValueError as exc: raise argparse.ArgumentTypeError(str(exc)) from exc

def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Simulate analytics-only BACKTEST-3B 4h exit model variants.")
    parser.add_argument("--input-events-path", type=Path, default=DEFAULT_INPUT_EVENTS_PATH); parser.add_argument("--input-bars-path", type=Path, default=DEFAULT_INPUT_BARS_PATH)
    parser.add_argument("--input-summary-path", type=Path, default=DEFAULT_INPUT_SUMMARY_PATH); parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--time-stops-hours", type=lambda x: _csv(x, int), default=Backtest3BConfig.time_stops_hours)
    parser.add_argument("--atr-stop-multipliers", type=lambda x: _csv(x, float), default=Backtest3BConfig.atr_stop_multipliers); parser.add_argument("--fixed-stop-pcts", type=lambda x: _csv(x, float), default=Backtest3BConfig.fixed_stop_pcts)
    parser.add_argument("--fixed-partial-trigger-pcts", type=lambda x: _csv(x, float), default=Backtest3BConfig.fixed_partial_trigger_pcts); parser.add_argument("--r-partial-triggers", type=lambda x: _csv(x, float), default=Backtest3BConfig.r_partial_triggers)
    parser.add_argument("--partial-sizes", type=lambda x: _csv(x, float), default=Backtest3BConfig.partial_sizes); parser.add_argument("--trail-modes", type=lambda x: _csv(x, str), default=Backtest3BConfig.trail_modes)
    parser.add_argument("--strict-preflight", dest="strict_preflight", action="store_true", default=True); parser.add_argument("--no-strict-preflight", dest="strict_preflight", action="store_false"); parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()

def main() -> None:
    args = _parse_args(); config = Backtest3BConfig(**vars(args))
    try: summary = run(config)
    except ValueError as exc: raise SystemExit(str(exc)) from exc
    print(json.dumps({"analysis_id": ANALYSIS_ID, "output_dir": config.output_dir.as_posix(), "event_model_row_count": summary["event_model_row_count"]}, sort_keys=True))

if __name__ == "__main__": main()
