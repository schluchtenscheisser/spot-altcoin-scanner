from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

from scripts.backtest.simulate_exit_model_variants_4h import (
    Backtest3BConfig,
    ExitModel,
    REQUIRED_OUTPUT_FILES,
    build_exit_model_matrix,
    build_outputs,
    build_segment_summary,
    run,
    simulate_event_model,
    validate_config,
)


def _event(**overrides: object) -> pd.Series:
    row = {
        "event_id": "e1", "symbol": "AAAUSDT", "segment_key": "early_candidates__base_reclaim",
        "decision_bucket": "early_candidates", "entry_pattern": "base_reclaim", "signal_timestamp": "2026-05-01T00:00:00Z",
        "reference_price": 100.0, "reference_price_source": "path_bar_1_open", "reference_price_status": "available",
        "path_coverage_status": "full", "available_path_bars": 42, "required_path_bars": 42,
        "mfe_pct": 10.0, "mae_pct": -4.0, "mfe_bar_index_4h": 4, "mae_bar_index_4h": 1,
        "time_to_mfe_hours": 16, "time_to_mae_hours": 4, "atr_4h_available": True, "atr_4h_value": 5.0,
        "atr_4h_period": 14, "atr_4h_source": "wilder_4h",
    }
    row.update(overrides)
    return pd.Series(row)


def _bars(prices: list[tuple[float, float, float]], event: pd.Series | None = None) -> pd.DataFrame:
    event = _event() if event is None else event
    rows = []
    for index, (high, low, close) in enumerate(prices, 1):
        rows.append({"event_id": event["event_id"], "symbol": event["symbol"], "segment_key": event["segment_key"],
            "decision_bucket": event["decision_bucket"], "entry_pattern": event["entry_pattern"], "signal_timestamp": event["signal_timestamp"],
            "bar_index_4h": index, "bar_timestamp": f"2026-05-01T{(index - 1) * 4:02d}:00:00Z", "open_4h": 100.0,
            "high_4h": high, "low_4h": low, "close_4h": close, "return_open_pct": 0.0, "return_high_pct": high - 100,
            "return_low_pct": low - 100, "return_close_pct": close - 100, "reference_price": event["reference_price"],
            "reference_price_source": event["reference_price_source"], "reference_price_status": event["reference_price_status"]})
    return pd.DataFrame(rows)


def _model(**overrides: object) -> ExitModel:
    values = {"initial_stop_mode": "fixed_pct", "initial_stop_value": 5.0, "partial_mode": "fixed_pct",
        "partial_trigger_value": 5.0, "partial_size": 0.5, "trail_mode": "none", "time_stop_hours": 12}
    values.update(overrides)
    return ExitModel(**values)  # type: ignore[arg-type]


def _fixture(tmp_path: Path, events: list[pd.Series] | None = None, bars: pd.DataFrame | None = None, **config: object) -> Backtest3BConfig:
    events_df = pd.DataFrame(events or [_event()]); bars = _bars([(102, 99, 101), (106, 100, 105), (108, 101, 107)]) if bars is None else bars
    events_path, bars_path, summary_path = tmp_path / "events.parquet", tmp_path / "bars.parquet", tmp_path / "summary.json"
    events_df.to_parquet(events_path, index=False); bars.to_parquet(bars_path, index=False)
    summary_path.write_text(json.dumps({"scenario_id": "scenario", "replay_id": "replay"}), encoding="utf-8")
    values = {"input_events_path": events_path, "input_bars_path": bars_path, "input_summary_path": summary_path,
        "output_dir": tmp_path / "output", "time_stops_hours": (12,), "atr_stop_multipliers": (1.0,), "fixed_stop_pcts": (5.0,),
        "fixed_partial_trigger_pcts": (5.0,), "r_partial_triggers": (1.0,), "partial_sizes": (0.5,), "trail_modes": ("none",)}
    values.update(config)
    return Backtest3BConfig(**values)  # type: ignore[arg-type]


def test_default_matrix_count_and_exit_model_id_format() -> None:
    models = build_exit_model_matrix()
    assert len(models) == 1230
    assert len({model.exit_model_id for model in models}) == 1230
    assert _model(initial_stop_mode="atr", initial_stop_value=1.2, partial_trigger_value=7.5, partial_size=.4, trail_mode="low_2bars", time_stop_hours=96).exit_model_id == "stop_atr1p2__partial_fixed7p5pct_40pct__trail_low2bars__time96h"
    assert _model(initial_stop_mode="atr", initial_stop_value=1.5, partial_mode="r_multiple", partial_trigger_value=1.5, partial_size=.4, trail_mode="low_3bars", time_stop_hours=168).exit_model_id == "stop_atr1p5__partial_r1p5_40pct__trail_low3bars__time168h"
    assert _model(initial_stop_mode="atr", initial_stop_value=1.0, partial_mode="none", partial_trigger_value=None, partial_size=0, trail_mode="none", time_stop_hours=24).exit_model_id == "stop_atr1p0__partial_none_0pct__trail_none__time24h"


def test_matrix_invariants() -> None:
    models = build_exit_model_matrix()
    assert all(model.trail_mode == "none" for model in models if model.partial_mode == "none")
    assert all(model.initial_stop_mode == "atr" for model in models if model.partial_mode == "r_multiple")


@pytest.mark.parametrize("field,value", [("time_stops_hours", (10,)), ("partial_sizes", (0.0,)), ("partial_sizes", (1.1,)), ("atr_stop_multipliers", (float("inf"),)), ("trail_modes", ("ema20",))])
def test_invalid_matrix_values_fail_preflight(field: str, value: tuple[object, ...]) -> None:
    values = {field: value}
    with pytest.raises(ValueError): validate_config(Backtest3BConfig(**values))


@pytest.mark.parametrize(
    ("field", "value", "duplicate"),
    [
        ("time_stops_hours", (24, 24), "24"),
        ("atr_stop_multipliers", (1.2, 1.2), "1.2"),
        ("fixed_partial_trigger_pcts", (7.5, 7.5), "7.5"),
        ("trail_modes", ("none", "none"), "none"),
    ],
)
def test_duplicate_matrix_values_rejected(field: str, value: tuple[object, ...], duplicate: str) -> None:
    with pytest.raises(ValueError, match=rf"Duplicate matrix values are not allowed: {field} contains {duplicate}"):
        validate_config(Backtest3BConfig(**{field: value}))


def test_same_bar_stop_partial_collision_stop_wins() -> None:
    row = simulate_event_model(_event(), _bars([(106, 94, 103)]), _model(time_stop_hours=4))
    assert row["exit_reason"] == "stop" and row["partial_filled"] is False and row["exit_price"] == 95


def test_exit_price_semantics_and_partial_then_time_stop_same_bar() -> None:
    stop = simulate_event_model(_event(), _bars([(101, 94, 96)]), _model(time_stop_hours=4))
    time = simulate_event_model(_event(), _bars([(101, 99, 102)]), _model(partial_mode="none", partial_trigger_value=None, partial_size=0, time_stop_hours=4))
    partial_time = simulate_event_model(_event(), _bars([(106, 99, 104)]), _model(time_stop_hours=4))
    assert (stop["exit_reason"], stop["exit_price"]) == ("stop", 95)
    assert (time["exit_reason"], time["exit_price"]) == ("time_stop", 102)
    assert (partial_time["exit_reason"], partial_time["exit_price"]) == ("partial_then_time_stop", 104)
    assert partial_time["gross_return_pct"] == pytest.approx(4.5)


def test_stopped_before_mfe_for_partial_then_stop_and_false_after_mfe() -> None:
    before = simulate_event_model(_event(mfe_bar_index_4h=4), _bars([(106, 99, 105), (104, 94, 95)]), _model(time_stop_hours=8))
    after = simulate_event_model(_event(mfe_bar_index_4h=1), _bars([(106, 99, 105), (104, 94, 95)]), _model(time_stop_hours=8))
    assert before["exit_reason"] == "partial_then_stop" and before["stopped_before_mfe"] is True
    assert after["stopped_before_mfe"] is False


def test_trail_activates_only_after_partial_bar_and_uses_preceding_lows() -> None:
    rows = _bars([(106, 99, 98), (104, 100, 99), (103, 101, 100), (102, 98, 98.5)])
    result = simulate_event_model(_event(), rows, _model(trail_mode="low_2bars", time_stop_hours=16))
    assert result["exit_reason"] == "partial_then_trail"
    assert result["partial_bar_index_4h"] == 1 and result["exit_bar_index_4h"] == 4 and result["exit_price"] == 98.5


def test_missing_reference_and_missing_atr_nullability() -> None:
    missing_reference = simulate_event_model(_event(reference_price=None, reference_price_status="missing"), _bars([(101, 99, 100)]), _model(time_stop_hours=4))
    missing_atr = simulate_event_model(_event(atr_4h_available=False, atr_4h_value=None), _bars([(101, 99, 100)]), _model(initial_stop_mode="atr", initial_stop_value=1.0, time_stop_hours=4))
    fixed = simulate_event_model(_event(atr_4h_available=False, atr_4h_value=None), _bars([(101, 99, 100)]), _model(time_stop_hours=4))
    assert missing_reference["exit_reason"] == "not_evaluable_missing_reference_price" and missing_reference["gross_return_pct"] is None
    assert missing_atr["exit_reason"] == "not_evaluable_missing_atr" and missing_atr["exit_price"] is None
    assert fixed["simulation_status"] == "evaluated"


def test_path_incomplete_when_time_stop_bar_missing() -> None:
    row = simulate_event_model(_event(), _bars([(101, 99, 100)]), _model(partial_mode="none", partial_trigger_value=None, partial_size=0, time_stop_hours=8))
    assert row["simulation_status"] == "not_evaluable" and row["exit_reason"] == "path_incomplete" and row["gross_return_pct"] is None


def test_non_finite_row_value_is_not_evaluable() -> None:
    row = simulate_event_model(_event(), _bars([(101, float("inf"), 100)]), _model(time_stop_hours=4))
    assert row["simulation_status"] == "not_evaluable" and row["exit_reason"] == "path_incomplete"


def test_final_bar_mae_is_unrecovered_and_included_in_segment_rate() -> None:
    event = _event(mae_bar_index_4h=2)
    row = simulate_event_model(
        event,
        _bars([(101, 99, 100), (102, 95, 101)]),
        _model(partial_mode="none", partial_trigger_value=None, partial_size=0, time_stop_hours=8),
    )
    summary = build_segment_summary(pd.DataFrame([row]))

    assert row["simulation_status"] == "evaluated"
    assert row["recovery_after_initial_mae"] is False
    assert summary.iloc[0]["recovery_after_initial_mae_rate"] == 0.0


def test_build_outputs_is_deterministic_and_segmentwise(tmp_path: Path) -> None:
    event2 = _event(event_id="e2", symbol="BBBUSDT", segment_key="confirmed_candidates__ema_reclaim", decision_bucket="confirmed_candidates", entry_pattern="ema_reclaim")
    bars = pd.concat([_bars([(102, 99, 101), (106, 100, 105), (108, 101, 107)]), _bars([(101, 99, 100), (102, 99, 101), (103, 99, 102)], event2)], ignore_index=True)
    config = _fixture(tmp_path, events=[_event(), event2], bars=bars)
    first, first_summary, _, report = build_outputs(config); second, second_summary, _, _ = build_outputs(config)
    pd.testing.assert_frame_equal(first, second); pd.testing.assert_frame_equal(first_summary, second_summary)
    assert set(first_summary["segment_key"]) == {"early_candidates__base_reclaim", "confirmed_candidates__ema_reclaim"}
    assert not any(phrase in report.lower() for phrase in ("recommended live exit model", "approved live exit rule", "production exit configuration"))


def test_run_writes_expected_files_atomically(tmp_path: Path) -> None:
    config = _fixture(tmp_path)
    summary = run(config)
    assert set(path.name for path in config.output_dir.iterdir()) == set(REQUIRED_OUTPUT_FILES)
    assert summary["analysis_id"] == "BACKTEST-3B_EXIT_MODEL_SIMULATION_4H" and summary["exit_simulation_performed"] is True
    assert summary["fees_included"] is False and summary["slippage_included"] is False and summary["execution_simulation_included"] is False


def test_duplicate_matrix_preflight_failure_writes_no_output_files(tmp_path: Path) -> None:
    config = _fixture(tmp_path, time_stops_hours=(12, 12))
    with pytest.raises(ValueError, match="Duplicate matrix values"):
        run(config)
    assert not config.output_dir.exists()


def test_existing_output_without_overwrite_fails_before_writes(tmp_path: Path) -> None:
    config = _fixture(tmp_path)
    config.output_dir.mkdir()
    sentinel = config.output_dir / "previous-report.txt"
    sentinel.write_text("previous", encoding="utf-8")

    with pytest.raises(ValueError, match="pass --overwrite"):
        run(config)

    assert sentinel.read_text(encoding="utf-8") == "previous"
    assert set(config.output_dir.iterdir()) == {sentinel}


def test_overwrite_replaces_existing_output(tmp_path: Path) -> None:
    config = _fixture(tmp_path, overwrite=True)
    config.output_dir.mkdir()
    sentinel = config.output_dir / "previous-report.txt"
    sentinel.write_text("previous", encoding="utf-8")

    run(config)

    assert not sentinel.exists()
    assert set(path.name for path in config.output_dir.iterdir()) == set(REQUIRED_OUTPUT_FILES)


def test_failed_overwrite_swap_restores_previous_output_without_partial_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    config = _fixture(tmp_path, overwrite=True)
    config.output_dir.mkdir()
    sentinel = config.output_dir / "previous-report.txt"
    sentinel.write_text("previous", encoding="utf-8")
    original_replace = Path.replace

    def fail_new_report_swap(source: Path, target: Path) -> Path:
        if target == config.output_dir and source.name.startswith(f".{config.output_dir.name}.tmp."):
            raise OSError("simulated replacement failure")
        return original_replace(source, target)

    monkeypatch.setattr(Path, "replace", fail_new_report_swap)

    with pytest.raises(OSError, match="simulated replacement failure"):
        run(config)

    assert sentinel.read_text(encoding="utf-8") == "previous"
    assert set(config.output_dir.iterdir()) == {sentinel}


def test_cli_invalid_input_schema_fails_before_writes(tmp_path: Path) -> None:
    config = _fixture(tmp_path)
    pd.DataFrame({"event_id": ["e1"]}).to_parquet(config.input_events_path, index=False)
    command = [sys.executable, "scripts/backtest/simulate_exit_model_variants_4h.py", "--input-events-path", str(config.input_events_path), "--input-bars-path", str(config.input_bars_path), "--input-summary-path", str(config.input_summary_path), "--output-dir", str(config.output_dir)]
    result = subprocess.run(command, capture_output=True, text=True)
    assert result.returncode != 0 and not config.output_dir.exists()
