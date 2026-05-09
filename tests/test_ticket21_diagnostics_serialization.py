from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.decision.models import DecisionBucket
from scanner.evaluation.replay import reconstruct_event_timeline
from scanner.output.diagnostics_serialization import (
    serialize_axes_block,
    serialize_decision_block,
    serialize_reasons_block,
)
from scanner.output.schema import SCHEMA_VERSION, validate_diagnostics_record
from scanner.state.models import InvalidationCycleBundle


def _base_record() -> dict:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": "r1",
        "scan_mode": "daily",
        "symbol": "AAAUSDT",
        "as_of_utc": "2026-04-01T00:00:00Z",
        "daily_bar_id": "2026-04-01",
        "intraday_bar_id": None,
        "data_4h_available": True,
        "axes": {},
        "phase": {},
        "invalidation": {},
        "cycle": {},
        "state": {},
        "pattern": {},
        "decision": {},
        "reasons": {},
        "universe": {
            "universe_category": "classic_crypto",
            "universe_category_confidence": "low",
            "universe_category_reason": "no_non_classic_rule_matched",
            "candidate_excluded": False,
            "candidate_exclusion_reason": None,
        },
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_fetch_duration_ms": None,
    }


def test_serialize_axes_preserves_null_zero_and_false() -> None:
    t1 = Tier1AxisBundle(
        symbol="AAAUSDT",
        daily_bar_id="2026-04-01",
        intraday_bar_id=None,
        data_4h_available=True,
        trend_strength=0.0,
        trend_strength_not_evaluable=False,
        trend_strength_reduced_resolution=False,
        trend_strength_effective_weight_ratio=0.0,
        reclaim_progress=None,
        reclaim_progress_not_evaluable=True,
        reclaim_progress_reduced_resolution=False,
        reclaim_progress_effective_weight_ratio=None,
        compression_strength=10.0,
        compression_strength_not_evaluable=False,
        compression_strength_reduced_resolution=False,
        compression_strength_effective_weight_ratio=1.0,
        expansion_progress_structural=20.0,
        expansion_progress_structural_not_evaluable=False,
        expansion_progress_structural_reduced_resolution=False,
        expansion_progress_structural_effective_weight_ratio=1.0,
        volume_regime_shift=30.0,
        volume_regime_shift_not_evaluable=False,
        volume_regime_shift_reduced_resolution=False,
        volume_regime_shift_effective_weight_ratio=1.0,
        freshness_distance_structural=None,
        freshness_distance_structural_not_evaluable=True,
        freshness_distance_structural_reduced_resolution=False,
        freshness_distance_structural_effective_weight_ratio=None,
    )
    t2 = Tier2AxisBundle(
        symbol="AAAUSDT",
        daily_bar_id="2026-04-01",
        intraday_bar_id=None,
        data_4h_available=True,
        base_integrity_simplified=0.0,
        base_integrity_simplified_not_evaluable=False,
        base_integrity_simplified_reduced_resolution=False,
        base_integrity_simplified_effective_weight_ratio=0.0,
        pullback_quality_simplified=None,
        pullback_quality_simplified_not_evaluable=True,
        pullback_quality_simplified_reduced_resolution=False,
        pullback_quality_simplified_effective_weight_ratio=None,
        reacceleration_strength_simplified=0.0,
        reacceleration_strength_simplified_not_evaluable=False,
        reacceleration_strength_simplified_reduced_resolution=False,
        reacceleration_strength_simplified_effective_weight_ratio=0.0,
    )
    out = serialize_axes_block(t1, t2)
    assert out["trend_strength"] == 0.0
    assert out["trend_strength_not_evaluable"] is False
    assert "reclaim_progress" in out and out["reclaim_progress"] is None
    assert out["base_integrity_simplified_effective_weight_ratio"] == 0.0


def test_serialize_decision_enum_and_reasons_execution_reason_passthrough() -> None:
    class _Decision:
        decision_bucket = DecisionBucket.WATCHLIST
        priority_score = 0.0
        bucket_reason_primary = DecisionBucket.WATCHLIST
        bucket_reason_secondary = None
        execution_required = False
        execution_pending = False
        entry_pattern = "none"
        entry_pattern_score = 0.0

    decision = _Decision()
    serialized_decision = serialize_decision_block(decision)  # type: ignore[arg-type]
    assert serialized_decision["decision_bucket"] == "watchlist"

    inv = InvalidationCycleBundle(
        symbol="AAAUSDT",
        daily_bar_id="2026-04-01",
        intraday_bar_id=None,
        data_4h_available=True,
        structural_invalidation=False,
        structural_invalidation_reason=None,
        timing_invalidation=False,
        timing_invalidation_reason=None,
        new_cycle_detected=False,
        cycle_reason_code="FIRST_CYCLE_INITIALIZED",
        resolved_setup_cycle_id=1,
        phase_floor_recovered_since_cycle_end=False,
        expansion_reset_condition_met=None,
        reclaim_reset_condition_met=None,
    )
    reasons = serialize_reasons_block(inv, None, None, execution_diagnostics={"execution_reason_raw": "NO_L2"})
    assert reasons["execution_reason_raw"] == "NO_L2"


def test_validate_diagnostics_record_invariants_enforced() -> None:
    record = _base_record()
    record["execution_attempted"] = True
    record["decision"] = {"decision_bucket": "watchlist", "priority_score": 0.0}
    record["state"] = {"state_machine_state": "watch", "setup_cycle_id": 1}
    record["phase"] = {"market_phase": "pressure_build", "market_phase_confidence": 0.0}
    validate_diagnostics_record(record)

    bad = _base_record()
    bad["decision"] = {"decision_bucket": "watchlist"}
    with pytest.raises(ValueError, match="state.state_machine_state"):
        validate_diagnostics_record(bad)


def test_validate_diagnostics_allows_discarded_without_state() -> None:
    record = _base_record()
    record["decision"] = {"decision_bucket": "discarded", "priority_score": 0.0}
    record["state"] = {"state_machine_state": None}
    validate_diagnostics_record(record)


def test_validate_diagnostics_execution_attempted_still_requires_state_for_discarded() -> None:
    record = _base_record()
    record["execution_attempted"] = True
    record["decision"] = {"decision_bucket": "discarded", "priority_score": 0.0}
    record["state"] = {"state_machine_state": None, "setup_cycle_id": 1}
    record["phase"] = {"market_phase": "none", "market_phase_confidence": 0.0}
    with pytest.raises(ValueError, match="state.state_machine_state"):
        validate_diagnostics_record(record)


def test_replay_cycle_id_level4_fallback_from_cycle_block(tmp_path: Path) -> None:
    run = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r1"
    run.mkdir(parents=True, exist_ok=True)
    (run / "run.manifest.json").write_text(json.dumps({"run_id": "r1"}), encoding="utf-8")
    diag = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r1" / "symbol_diagnostics.jsonl.gz"
    diag.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": "AAAUSDT",
        "as_of_utc": "2026-04-01T00:00:00Z",
        "state": {"state_machine_state": "watch"},
        "cycle": {"resolved_setup_cycle_id": 42},
        "decision": {"decision_bucket": "watchlist"},
        "daily_bar_id": "2026-04-01",
    }
    with gzip.open(diag, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")

    events, _ = reconstruct_event_timeline(project_root=tmp_path)
    assert len(events) == 1
    assert events[0]["setup_cycle_id"] == 42


def test_replay_cycle_id_level4_fallback_skips_null_nested_state_ids(tmp_path: Path) -> None:
    run = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r2"
    run.mkdir(parents=True, exist_ok=True)
    (run / "run.manifest.json").write_text(json.dumps({"run_id": "r2"}), encoding="utf-8")
    diag = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r2" / "symbol_diagnostics.jsonl.gz"
    diag.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": "BBBUSDT",
        "as_of_utc": "2026-04-01T00:00:00Z",
        "state": {"state_machine_state": "watch", "setup_cycle_id": None, "current_setup_cycle_id": None},
        "cycle": {"resolved_setup_cycle_id": 1},
        "decision": {"decision_bucket": "watchlist"},
        "daily_bar_id": "2026-04-01",
    }
    with gzip.open(diag, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")

    events, _ = reconstruct_event_timeline(project_root=tmp_path)
    assert len(events) == 1
    assert events[0]["setup_cycle_id"] == 1


def test_replay_cycle_id_prefers_state_setup_cycle_id_over_cycle_block(tmp_path: Path) -> None:
    run = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r3"
    run.mkdir(parents=True, exist_ok=True)
    (run / "run.manifest.json").write_text(json.dumps({"run_id": "r3"}), encoding="utf-8")
    diag = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r3" / "symbol_diagnostics.jsonl.gz"
    diag.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "symbol": "CCCUSDT",
        "as_of_utc": "2026-04-01T00:00:00Z",
        "state": {"state_machine_state": "watch", "setup_cycle_id": 7},
        "cycle": {"resolved_setup_cycle_id": 99},
        "decision": {"decision_bucket": "watchlist"},
        "daily_bar_id": "2026-04-01",
    }
    with gzip.open(diag, "wt", encoding="utf-8") as fh:
        fh.write(json.dumps(payload) + "\n")

    events, _ = reconstruct_event_timeline(project_root=tmp_path)
    assert len(events) == 1
    assert events[0]["setup_cycle_id"] == 7


def test_entry_location_inputs_are_normalized_with_schema_ir12() -> None:
    record = _base_record()
    record["entry_location_inputs"] = {
        "close_vs_ema20_4h_pct": 6.14,
        "bars_above_ema20_4h": 4,
        "dist_to_ema20_4h_pct_abs": 6.14,
        "distance_to_last_structural_anchor_pct_abs": 8.32,
        "distance_to_range_high_pct_abs": None,
        "bars_since_last_structural_break_4h": 3,
    }

    out = validate_diagnostics_record(record)

    assert out["schema_version"] == "ir1.2"
    assert out["entry_location_inputs"] == {
        "close_vs_ema20_4h_pct": 6.14,
        "bars_above_ema20_4h": 4,
        "dist_to_ema20_4h_pct_abs": 6.14,
        "distance_to_last_structural_anchor_pct_abs": 8.32,
        "distance_to_range_high_pct_abs": None,
        "bars_since_last_structural_break_4h": 3,
    }


def test_entry_location_inputs_null_when_4h_unavailable() -> None:
    record = _base_record()
    record["data_4h_available"] = False
    record["entry_location_inputs"] = {
        "close_vs_ema20_4h_pct": 6.14,
        "bars_above_ema20_4h": 4,
        "dist_to_ema20_4h_pct_abs": 6.14,
        "distance_to_last_structural_anchor_pct_abs": 8.32,
        "distance_to_range_high_pct_abs": 1.2,
        "bars_since_last_structural_break_4h": 3,
    }

    out = validate_diagnostics_record(record)

    assert set(out["entry_location_inputs"]) == {
        "close_vs_ema20_4h_pct",
        "bars_above_ema20_4h",
        "dist_to_ema20_4h_pct_abs",
        "distance_to_last_structural_anchor_pct_abs",
        "distance_to_range_high_pct_abs",
        "bars_since_last_structural_break_4h",
    }
    assert all(value is None for value in out["entry_location_inputs"].values())


def test_entry_location_inputs_non_finite_values_serialize_as_null() -> None:
    record = _base_record()
    record["entry_location_inputs"] = {
        "close_vs_ema20_4h_pct": float("nan"),
        "bars_above_ema20_4h": 4,
        "dist_to_ema20_4h_pct_abs": float("inf"),
        "distance_to_last_structural_anchor_pct_abs": float("-inf"),
        "distance_to_range_high_pct_abs": None,
        "bars_since_last_structural_break_4h": 3,
    }

    out = validate_diagnostics_record(record)

    assert out["entry_location_inputs"]["close_vs_ema20_4h_pct"] is None
    assert out["entry_location_inputs"]["dist_to_ema20_4h_pct_abs"] is None
    assert out["entry_location_inputs"]["distance_to_last_structural_anchor_pct_abs"] is None
    assert out["entry_location_inputs"]["bars_above_ema20_4h"] == 4


def test_serialize_entry_location_inputs_reads_current_t5_raw_4h_names() -> None:
    from types import SimpleNamespace

    from scanner.output.diagnostics_serialization import serialize_entry_location_inputs

    raw_4h = SimpleNamespace(
        close_vs_ema20_4h_pct=6.14,
        close_vs_ema20_4h_pct_status="ok",
        bars_above_ema20_4h=4,
        bars_above_ema20_4h_status="ok",
        dist_to_ema20_4h_pct_abs=6.14,
        dist_to_ema20_4h_pct_abs_status="ok",
        distance_to_last_structural_anchor_pct_abs=8.32,
        distance_to_last_structural_anchor_pct_abs_status="ok",
        distance_to_range_high_pct_abs=2.5,
        distance_to_range_high_pct_abs_status="ok",
        bars_since_last_structural_break_4h=3,
        bars_since_last_structural_break_4h_status="ok",
    )
    feature_bundle = SimpleNamespace(
        symbol="ASTERUSDT",
        data_4h_available=True,
        raw_4h=raw_4h,
    )

    assert serialize_entry_location_inputs(feature_bundle) == {
        "close_vs_ema20_4h_pct": 6.14,
        "bars_above_ema20_4h": 4,
        "dist_to_ema20_4h_pct_abs": 6.14,
        "distance_to_last_structural_anchor_pct_abs": 8.32,
        "distance_to_range_high_pct_abs": 2.5,
        "bars_since_last_structural_break_4h": 3,
    }
