from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd
import pytest

from scanner.evaluation.dataset_export import run_evaluation_export
from scanner.evaluation.forward_returns import build_signal_metrics
from scripts import run_t30_evaluation as t30


def _write_daily_ohlcv(root: Path, symbol: str, rows: list[dict]) -> None:
    out = root / "snapshots" / "history" / "ohlcv" / "timeframe=1d" / f"symbol={symbol}" / "year=2026" / "month=05"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out / "part-000.parquet", index=False)


def _event(symbol: str = "AAAUSDT", event_type: str = "first_confirmed_ready", **overrides: object) -> dict:
    order = {"first_watch": 10, "first_early_ready": 20, "first_confirmed_ready": 30}[event_type]
    row = {
        "symbol": symbol,
        "setup_cycle_id": 1,
        "event_type": event_type,
        "event_order": order,
        "event_timestamp_utc": "2026-05-05T00:00:00Z",
        "event_bar_id": "2026-05-05",
        "event_bar_id_type": "daily_bar_id",
        "first_observed_run_id": "r1",
        "first_observed_run_mode": "daily",
    }
    row.update(overrides)
    return row


def _basic_ohlcv(close: object = 10.0) -> list[dict]:
    return [
        {"daily_bar_id": "2026-05-05", "close": close, "high": 10.5, "low": 9.5},
        {"daily_bar_id": "2026-05-06", "close": 11.0, "high": 11.5, "low": 10.5},
    ]


def _signal_row(tmp_path: Path, event: dict) -> dict:
    signal, _terminal, _transitions, _diag = build_signal_metrics([event], project_root=tmp_path)
    assert len(signal) == 1
    return signal.iloc[0].to_dict()


@pytest.mark.parametrize("event_type", ["first_early_ready", "first_confirmed_ready"])
def test_reference_fallback_succeeds_for_early_and_confirmed_events(tmp_path: Path, event_type: str) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())

    row = _signal_row(tmp_path, _event(event_type=event_type))

    assert row["reference_price"] == 10.0
    assert row["reference_price_status"] == "ok"
    assert row["reference_price_source"] == "ohlcv_event_bar_close"
    assert row["reference_price_reason"] == "fallback_missing_persisted_state_reference"
    assert row["metric_status_1d"] == "ok"
    assert row["forward_return_1d_pct"] == pytest.approx(10.0)


def test_watch_event_bar_close_uses_watch_specific_reason(tmp_path: Path) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())

    row = _signal_row(tmp_path, _event(event_type="first_watch"))

    assert row["reference_price"] == 10.0
    assert row["reference_price_status"] == "ok"
    assert row["reference_price_source"] == "ohlcv_event_bar_close"
    assert row["reference_price_reason"] == "watch_event_bar_close"
    assert row["reference_price_reason"] != "fallback_missing_persisted_state_reference"


def test_persisted_reference_takes_precedence_over_ohlcv_close(tmp_path: Path) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())

    row = _signal_row(tmp_path, _event(close_at_confirmed_entry_bar=9.5))

    assert row["reference_price"] == 9.5
    assert row["reference_price_source"] == "persisted_state_reference"
    assert row["reference_price_reason"] == "persisted_state_reference_available"


def test_missing_event_bar_ohlcv_remains_non_evaluable(tmp_path: Path) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", [{"daily_bar_id": "2026-05-06", "close": 11.0, "high": 11.5, "low": 10.5}])

    row = _signal_row(tmp_path, _event())

    assert row["reference_price_status"] == "reference_price_not_evaluable"
    assert row["reference_price_source"] == "not_available"
    assert row["reference_price_reason"] == "missing_event_bar_ohlcv"


def test_missing_symbol_ohlcv_remains_missing_ohlcv(tmp_path: Path) -> None:
    row = _signal_row(tmp_path, _event())

    assert row["metric_status_1d"] == "missing_ohlcv_history"
    assert row["reference_price_status"] == "reference_price_not_evaluable"
    assert row["reference_price_reason"] == "missing_ohlcv_history"


@pytest.mark.parametrize("close", [None, float("nan"), float("inf"), float("-inf"), 0, -1])
def test_invalid_event_bar_close_is_rejected(tmp_path: Path, close: object) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv(close=close))

    row = _signal_row(tmp_path, _event())

    assert row["reference_price_status"] == "reference_price_not_evaluable"
    assert row["reference_price_reason"] == "invalid_event_bar_close"


def test_early_and_confirmed_events_become_evaluable_with_complete_ohlcv(tmp_path: Path) -> None:
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())

    signal, _terminal, _transitions, _diag = build_signal_metrics(
        [_event(event_type="first_early_ready"), _event(event_type="first_confirmed_ready")],
        project_root=tmp_path,
    )

    assert set(signal["event_type"].tolist()) == {"first_early_ready", "first_confirmed_ready"}
    assert set(signal["metric_status_1d"].tolist()) == {"ok"}
    assert set(signal["reference_price_source"].tolist()) == {"ohlcv_event_bar_close"}


def _write_manifest(project_root: Path, run_id: str = "r1") -> None:
    path = project_root / "snapshots" / "runs" / "2026" / "05" / "05" / run_id / "run.manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run_id": run_id, "scan_mode": "daily"}), encoding="utf-8")


def _write_diag(project_root: Path, rows: list[dict], run_id: str = "r1") -> None:
    path = project_root / "reports" / "runs" / "2026" / "05" / "05" / run_id / "symbol_diagnostics.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def test_segment_fields_are_exported_from_canonical_paths(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_diag(
        tmp_path,
        [
            {
                "schema_version": "ir1.5",
                "scan_mode": "daily",
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "confirmed_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "execution_status_raw": "ok",
                "execution_size_class": "reduced_50",
                "is_tradeable_candidate": True,
                "is_reduced_size_eligible": True,
                "is_operational_trade_candidate": True,
                "candidate_excluded": False,
                "recommended_position_factor": 0.5,
                "execution_grade_effective": 82.0,
                "available_depth_ratio": 0.54,
                "depth_ratio_band": "reduced_50",
                "decision": {"decision_bucket": "confirmed_candidates", "priority_score": 66.7},
                "phase": {"market_phase": "trend_resume", "market_phase_confidence": 81.0},
                "state": {"state_machine_state": "confirmed_ready", "state_confidence": 77.0},
                "pattern": {"entry_pattern": "resume_reclaim"},
                "universe": {"universe_category": "standard_altcoin"},
                "entry_location": {
                    "entry_location_status": "fresh_entry",
                    "entry_action_hint": "acceptable_if_strategy_allows",
                    "range_high_proximity_warning": False,
                },
            }
        ],
    )
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())

    run_evaluation_export(project_root=tmp_path)
    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    row = signal.iloc[0]

    assert row["schema_version"] == "ir1.5"
    assert row["execution_size_class"] == "reduced_50"
    assert bool(row["is_tradeable_candidate"]) is True
    assert bool(row["is_reduced_size_eligible"]) is True
    assert bool(row["is_operational_trade_candidate"]) is True
    assert row["operational_tradeability_source"] == "native_ir1_5"
    assert row["available_depth_ratio"] == pytest.approx(0.54)
    assert row["decision_bucket"] == "confirmed_candidates"
    assert row["priority_score"] == pytest.approx(66.7)
    assert row["market_phase"] == "trend_resume"
    assert row["state_confidence"] == pytest.approx(77.0)
    assert row["entry_pattern"] == "resume_reclaim"
    assert row["universe_category"] == "standard_altcoin"
    assert row["entry_location_status"] == "fresh_entry"
    assert row["entry_action_hint"] == "acceptable_if_strategy_allows"
    assert bool(row["range_high_proximity_warning"]) is False


def test_missing_segments_stay_null_and_operational_compatibility_is_explicit(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_diag(
        tmp_path,
        [
            {
                "schema_version": "ir1.4",
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "early_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "is_tradeable_candidate": True,
                "candidate_excluded": False,
            },
            {
                "schema_version": "ir1.4",
                "symbol": "BBBUSDT",
                "setup_cycle_id": 2,
                "state_machine_state": "early_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "is_tradeable_candidate": True,
                "candidate_excluded": True,
            },
            {
                "schema_version": "ir1.4",
                "symbol": "CCCUSDT",
                "setup_cycle_id": 3,
                "state_machine_state": "early_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "candidate_excluded": False,
            },
            {
                "schema_version": "ir1.4",
                "symbol": "DDDUSDT",
                "setup_cycle_id": 4,
                "state_machine_state": "early_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "is_tradeable_candidate": True,
            },
        ],
    )
    for symbol in ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT"]:
        _write_daily_ohlcv(tmp_path, symbol, _basic_ohlcv())

    run_evaluation_export(project_root=tmp_path)
    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet").set_index("symbol")

    assert pd.isna(signal.loc["AAAUSDT", "is_operational_trade_candidate"])
    assert bool(signal.loc["AAAUSDT", "operational_tradeability_compat"]) is True
    assert signal.loc["AAAUSDT", "operational_tradeability_source"] == "compat_backfill"
    assert bool(signal.loc["BBBUSDT", "operational_tradeability_compat"]) is False
    assert signal.loc["BBBUSDT", "operational_tradeability_source"] == "compat_backfill"
    assert pd.isna(signal.loc["CCCUSDT", "operational_tradeability_compat"])
    assert signal.loc["CCCUSDT", "operational_tradeability_source"] == "not_available"
    assert pd.isna(signal.loc["DDDUSDT", "operational_tradeability_compat"])
    assert signal.loc["DDDUSDT", "operational_tradeability_source"] == "not_available"
    assert pd.isna(signal.loc["AAAUSDT", "entry_location_status"])
    assert pd.isna(signal.loc["AAAUSDT", "execution_size_class"])


def test_t30_note_reports_reference_coverage_and_segment_observations(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_diag(
        tmp_path,
        [
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "watch",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "execution_size_class": "full",
                "is_tradeable_candidate": True,
                "candidate_excluded": False,
            },
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 3,
                "state_machine_state": "early_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "execution_size_class": "full",
                "is_tradeable_candidate": True,
                "candidate_excluded": False,
            },
            {
                "symbol": "BBBUSDT",
                "setup_cycle_id": 2,
                "state_machine_state": "confirmed_ready",
                "as_of_utc": "2026-05-05T00:00:00Z",
                "daily_bar_id": "2026-05-05",
                "execution_size_class": "reduced_50",
                "is_tradeable_candidate": True,
                "candidate_excluded": False,
            },
        ],
    )
    _write_daily_ohlcv(tmp_path, "AAAUSDT", _basic_ohlcv())
    _write_daily_ohlcv(tmp_path, "BBBUSDT", _basic_ohlcv())

    assert t30.main(["--project-root", str(tmp_path)]) == 0
    note = (tmp_path / "evaluation" / "notes" / "T30_forward_return_evaluation_v1.md").read_text(encoding="utf-8")

    assert "## Reference Price Coverage" in note
    assert "first_early_ready" in note
    assert "first_confirmed_ready" in note
    assert "ohlcv_event_bar_close" in note
    assert "watch_event_bar_close" in note
    assert "fallback_missing_persisted_state_reference" in note
    assert "## Metric Status by Event Type" in note
    assert "### `execution_size_class`" in note
    assert "Status: exploratory / validation note" in note
    assert "Not a final performance conclusion" in note
