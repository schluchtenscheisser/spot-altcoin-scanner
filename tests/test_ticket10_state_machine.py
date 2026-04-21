from __future__ import annotations

import sqlite3

import pytest

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.freshness import compute_state_freshness
from scanner.state.machine import compute_state_machine
from scanner.state.models import InvalidationCycleBundle, PersistedStateMachineContext, StateRuntimeContext
from scanner.storage.repositories import apply_state_persistence_patch, load_persisted_state_machine_context
from scanner.storage.schema import apply_schema


def _phase(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 111,
        "intraday_bar_id": 222,
        "data_4h_available": True,
        "market_phase": "trend_resume",
        "market_phase_confidence": 75.0,
        "market_phase_runner_up": "pressure_build",
        "market_phase_gap": 10.0,
        "market_phase_blended": False,
        "phase_score_pressure_build": 60.0,
        "phase_score_trend_resume": 70.0,
        "phase_score_transition_reclaim": 50.0,
        "phase_floor_margin_pressure_build": 1.0,
        "phase_floor_margin_trend_resume": 2.0,
        "phase_floor_margin_transition_reclaim": 0.5,
        "phase_floor_failed_pressure_build": False,
        "phase_floor_failed_trend_resume": False,
        "phase_floor_failed_transition_reclaim": False,
        "phase_eval_status_pressure_build": "score_computed",
        "phase_eval_status_trend_resume": "score_computed",
        "phase_eval_status_transition_reclaim": "score_computed",
        "freshness_distance_structural": 20.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
    }
    base.update(overrides)
    return PhaseInterpretationBundle(**base)


def _tier1(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 111,
        "intraday_bar_id": 222,
        "data_4h_available": True,
        "trend_strength": 70.0,
        "trend_strength_not_evaluable": False,
        "trend_strength_reduced_resolution": False,
        "trend_strength_effective_weight_ratio": 1.0,
        "reclaim_progress": 70.0,
        "reclaim_progress_not_evaluable": False,
        "reclaim_progress_reduced_resolution": False,
        "reclaim_progress_effective_weight_ratio": 1.0,
        "compression_strength": 70.0,
        "compression_strength_not_evaluable": False,
        "compression_strength_reduced_resolution": False,
        "compression_strength_effective_weight_ratio": 1.0,
        "expansion_progress_structural": 20.0,
        "expansion_progress_structural_not_evaluable": False,
        "expansion_progress_structural_reduced_resolution": False,
        "expansion_progress_structural_effective_weight_ratio": 1.0,
        "volume_regime_shift": 70.0,
        "volume_regime_shift_not_evaluable": False,
        "volume_regime_shift_reduced_resolution": False,
        "volume_regime_shift_effective_weight_ratio": 1.0,
        "freshness_distance_structural": 20.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
        "freshness_distance_structural_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier1AxisBundle(**base)


def _tier2(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 111,
        "intraday_bar_id": 222,
        "data_4h_available": True,
        "base_integrity_simplified": 70.0,
        "base_integrity_simplified_not_evaluable": False,
        "base_integrity_simplified_reduced_resolution": False,
        "base_integrity_simplified_effective_weight_ratio": 1.0,
        "pullback_quality_simplified": 70.0,
        "pullback_quality_simplified_not_evaluable": False,
        "pullback_quality_simplified_reduced_resolution": False,
        "pullback_quality_simplified_effective_weight_ratio": 1.0,
        "reacceleration_strength_simplified": 70.0,
        "reacceleration_strength_simplified_not_evaluable": False,
        "reacceleration_strength_simplified_reduced_resolution": False,
        "reacceleration_strength_simplified_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier2AxisBundle(**base)


def _inv(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 111,
        "intraday_bar_id": 222,
        "data_4h_available": True,
        "structural_invalidation": False,
        "structural_invalidation_reason": None,
        "timing_invalidation": False,
        "timing_invalidation_reason": None,
        "new_cycle_detected": False,
        "cycle_reason_code": "NEW_CYCLE_BLOCKED_MIN_BARS_NOT_MET",
        "resolved_setup_cycle_id": 3,
        "phase_floor_recovered_since_cycle_end": True,
        "expansion_reset_condition_met": True,
        "reclaim_reset_condition_met": None,
    }
    base.update(overrides)
    return InvalidationCycleBundle(**base)


def _ctx(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "current_setup_cycle_id": 3,
        "previous_setup_cycle_id": 2,
        "state_recorded_in_cycle_id": 3,
        "prev_state_machine_state": "watch",
        "freshness_distance_state_early": None,
        "freshness_distance_state_confirmed": None,
        "bars_since_state_entered": 1,
        "bars_since_early_entered": None,
        "bars_since_confirmed_entered": None,
        "bars_since_cycle_end": None,
        "reclaim_below_reset_floor_seen_since_cycle_end": None,
        "close_at_early_entry_bar": None,
        "close_at_confirmed_entry_bar": None,
        "distance_from_ideal_entry_after_early": None,
        "distance_from_ideal_entry_after_confirmed": None,
        "cycle_end_bar_index": None,
        "cycle_end_timestamp": None,
    }
    base.update(overrides)
    return PersistedStateMachineContext(**base)


def test_not_admitted_disposition_has_no_patch():
    out = compute_state_machine(
        _phase(market_phase="none"),
        _tier1(),
        _tier2(),
        _inv(),
        _ctx(prev_state_machine_state=None, current_setup_cycle_id=None, state_recorded_in_cycle_id=None),
        StateRuntimeContext(current_close=100.0, current_bar_index=50, delta_closed_bars_relevant=1),
        ScannerConfig(raw={}),
    )
    assert out.disposition.admitted is False
    assert out.state_machine_state is None
    assert out.persistence_patch is None


def test_terminal_daily_run_uses_daily_bar_id_for_cycle_end_timestamp():
    out = compute_state_machine(
        _phase(intraday_bar_id=None),
        _tier1(expansion_progress_structural=95.0, intraday_bar_id=None),
        _tier2(intraday_bar_id=None),
        _inv(intraday_bar_id=None),
        _ctx(prev_state_machine_state="confirmed_ready"),
        StateRuntimeContext(current_close=100.0, current_bar_index=77, delta_closed_bars_relevant=2),
        ScannerConfig(raw={}),
    )
    assert out.state_machine_state == "chased"
    assert out.persistence_patch is not None
    assert out.persistence_patch.cycle_end_timestamp == 111
    assert out.persistence_patch.cycle_end_bar_index == 77
    assert out.persistence_patch.bars_since_cycle_end == 0


def test_state_config_defaults_and_validation():
    cfg = ScannerConfig(raw={})
    assert cfg.state["late"]["min_state_freshness"] == 60.0
    with pytest.raises(ValueError, match="state.freshness.bars_points"):
        ScannerConfig(raw={"state": {"freshness": {"bars_points": [[0, 0], [0, 10]]}}}).state


def test_state_persistence_repository_roundtrip():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    apply_schema(conn)

    out = compute_state_machine(
        _phase(),
        _tier1(),
        _tier2(),
        _inv(),
        _ctx(prev_state_machine_state="watch"),
        StateRuntimeContext(current_close=100.0, current_bar_index=12, delta_closed_bars_relevant=1),
        ScannerConfig(raw={}),
    )
    assert out.persistence_patch is not None
    apply_state_persistence_patch(conn, out.persistence_patch)

    loaded = load_persisted_state_machine_context(conn, "TESTUSDT")
    assert loaded.current_setup_cycle_id == out.persistence_patch.setup_cycle_id
    assert loaded.prev_state_machine_state == out.persistence_patch.state_machine_state


def test_compute_state_freshness_type_validation():
    with pytest.raises(TypeError):
        compute_state_freshness({}, _ctx(), StateRuntimeContext(current_close=100.0, current_bar_index=1, delta_closed_bars_relevant=1), ScannerConfig(raw={}))
