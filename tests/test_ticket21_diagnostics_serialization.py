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
