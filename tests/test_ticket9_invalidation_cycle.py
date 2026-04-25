from __future__ import annotations

import dataclasses

import pytest

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state import InvalidationCycleBundle, PersistedStateCycleContext, compute_invalidation_and_cycle


def _phase(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": "2026-01-01",
        "intraday_bar_id": 20,
        "data_4h_available": True,
        "market_phase": "trend_resume",
        "market_phase_confidence": 70.0,
        "market_phase_runner_up": "pressure_build",
        "market_phase_gap": 12.0,
        "market_phase_blended": False,
        "phase_score_pressure_build": 62.0,
        "phase_score_trend_resume": 70.0,
        "phase_score_transition_reclaim": 58.0,
        "phase_floor_margin_pressure_build": 5.0,
        "phase_floor_margin_trend_resume": 7.0,
        "phase_floor_margin_transition_reclaim": 4.0,
        "phase_floor_failed_pressure_build": False,
        "phase_floor_failed_trend_resume": False,
        "phase_floor_failed_transition_reclaim": False,
        "phase_eval_status_pressure_build": "score_computed",
        "phase_eval_status_trend_resume": "score_computed",
        "phase_eval_status_transition_reclaim": "score_computed",
        "freshness_distance_structural": 30.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
    }
    base.update(overrides)
    return PhaseInterpretationBundle(**base)


def _tier1(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": "2026-01-01",
        "intraday_bar_id": 20,
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
        "freshness_distance_structural": 30.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
        "freshness_distance_structural_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier1AxisBundle(**base)


def _tier2(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": "2026-01-01",
        "intraday_bar_id": 20,
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


def _context(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "current_setup_cycle_id": 3,
        "previous_setup_cycle_id": 2,
        "state_recorded_in_cycle_id": 3,
        "prev_state_machine_state": "watch",
        "freshness_distance_state_early": 20.0,
        "freshness_distance_state_confirmed": 20.0,
        "bars_since_state_entered": 3,
        "bars_since_early_entered": 3,
        "bars_since_confirmed_entered": None,
        "bars_since_cycle_end": 3,
        "reclaim_below_reset_floor_seen_since_cycle_end": None,
    }
    base.update(overrides)
    return PersistedStateCycleContext(**base)


def _cfg(overrides: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=overrides or {})


def test_output_contract_and_determinism():
    out1 = compute_invalidation_and_cycle(_phase(), _tier1(), _tier2(), _context(), _cfg())
    out2 = compute_invalidation_and_cycle(_phase(), _tier1(), _tier2(), _context(), _cfg())
    assert isinstance(out1, InvalidationCycleBundle)
    assert dataclasses.asdict(out1) == dataclasses.asdict(out2)


def test_type_validation_and_bundle_identity_validation():
    with pytest.raises(TypeError):
        compute_invalidation_and_cycle({}, _tier1(), _tier2(), _context(), _cfg())
    with pytest.raises(TypeError):
        compute_invalidation_and_cycle(_phase(), _tier1(), _tier2(), _context(), {})
    with pytest.raises(ValueError, match="daily_bar_id"):
        compute_invalidation_and_cycle(_phase(daily_bar_id="2026-02-02"), _tier1(), _tier2(), _context(), _cfg())
    with pytest.raises(ValueError, match="symbol"):
        compute_invalidation_and_cycle(_phase(), _tier1(), _tier2(), _context(symbol="X"), _cfg())


def test_structural_precedence_suppresses_timing():
    out = compute_invalidation_and_cycle(
        _phase(market_phase="none"),
        _tier1(expansion_progress_structural=100.0),
        _tier2(),
        _context(prev_state_machine_state="watch", state_recorded_in_cycle_id=3),
        _cfg({"invalidation": {"max_expansion_progress": 80.0}}),
    )
    assert out.structural_invalidation is True
    assert out.timing_invalidation is False
    assert out.timing_invalidation_reason is None


def test_g1_phase_none_semantics_and_stale_cycle_guard():
    out = compute_invalidation_and_cycle(
        _phase(market_phase="none"),
        _tier1(),
        _tier2(),
        _context(prev_state_machine_state="late", state_recorded_in_cycle_id=3),
        _cfg(),
    )
    assert out.structural_invalidation_reason == "PHASE_TO_NONE"

    out_stale = compute_invalidation_and_cycle(
        _phase(market_phase="none"),
        _tier1(),
        _tier2(),
        _context(prev_state_machine_state="late", state_recorded_in_cycle_id=2),
        _cfg(),
    )
    assert out_stale.structural_invalidation is False


def test_trend_resume_rules_and_t4_guard():
    out_t1 = compute_invalidation_and_cycle(
        _phase(market_phase="trend_resume"),
        _tier1(trend_strength=40.0),
        _tier2(),
        _context(prev_state_machine_state="watch"),
        _cfg(),
    )
    assert out_t1.structural_invalidation_reason == "TREND_RESUME_TREND_BREAK"

    out_t4 = compute_invalidation_and_cycle(
        _phase(market_phase="trend_resume"),
        _tier1(),
        _tier2(reacceleration_strength_simplified=30.0),
        _context(prev_state_machine_state="early_ready"),
        _cfg(),
    )
    assert out_t4.structural_invalidation_reason == "TREND_RESUME_REACCEL_FAILURE"

    out_t4_guard = compute_invalidation_and_cycle(
        _phase(market_phase="trend_resume"),
        _tier1(),
        _tier2(reacceleration_strength_simplified=30.0),
        _context(prev_state_machine_state="watch"),
        _cfg(),
    )
    assert out_t4_guard.structural_invalidation_reason is None


def test_timing_reason_priority():
    out = compute_invalidation_and_cycle(
        _phase(freshness_distance_structural=99.0),
        _tier1(expansion_progress_structural=95.0),
        _tier2(),
        _context(
            prev_state_machine_state="early_ready",
            freshness_distance_state_early=99.0,
            freshness_distance_state_confirmed=99.0,
        ),
        _cfg(
            {
                "invalidation": {
                    "max_state_freshness": 90.0,
                    "max_expansion_progress": 90.0,
                    "max_structural_freshness": 90.0,
                }
            }
        ),
    )
    assert out.timing_invalidation is True
    assert out.timing_invalidation_reason == "STATE_FRESHNESS_EARLY_MAXED"


def test_cycle_detection_and_first_seen_initialization():
    out_new = compute_invalidation_and_cycle(
        _phase(phase_floor_failed_pressure_build=False, phase_floor_failed_trend_resume=True, phase_floor_failed_transition_reclaim=True),
        _tier1(),
        _tier2(),
        _context(prev_state_machine_state="rejected", bars_since_cycle_end=5),
        _cfg({"cycle": {"expansion_reset_max": 40.0, "min_bars_since_cycle_end": 2}}),
    )
    assert out_new.new_cycle_detected is True
    assert out_new.cycle_reason_code == "NEW_CYCLE_AFTER_REJECTION"
    assert out_new.resolved_setup_cycle_id == 4

    out_first = compute_invalidation_and_cycle(
        _phase(),
        _tier1(),
        _tier2(),
        _context(
            current_setup_cycle_id=None,
            previous_setup_cycle_id=None,
            state_recorded_in_cycle_id=None,
            prev_state_machine_state=None,
            freshness_distance_state_early=None,
            freshness_distance_state_confirmed=None,
            bars_since_state_entered=None,
            bars_since_early_entered=None,
            bars_since_cycle_end=None,
            reclaim_below_reset_floor_seen_since_cycle_end=None,
        ),
        _cfg(),
    )
    assert out_first.new_cycle_detected is False
    assert out_first.resolved_setup_cycle_id == 1
    assert out_first.cycle_reason_code == "FIRST_CYCLE_INITIALIZED"


def test_z1_uses_expansion_progress_not_structural_freshness():
    out_blocked = compute_invalidation_and_cycle(
        _phase(freshness_distance_structural=10.0),
        _tier1(expansion_progress_structural=95.0),
        _tier2(),
        _context(prev_state_machine_state="rejected", bars_since_cycle_end=5),
        _cfg({"cycle": {"expansion_reset_max": 40.0, "min_bars_since_cycle_end": 2}}),
    )
    assert out_blocked.expansion_reset_condition_met is False
    assert out_blocked.new_cycle_detected is False
    assert out_blocked.cycle_reason_code == "NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET"

    out_allowed = compute_invalidation_and_cycle(
        _phase(freshness_distance_structural=95.0),
        _tier1(expansion_progress_structural=10.0),
        _tier2(),
        _context(prev_state_machine_state="rejected", bars_since_cycle_end=5),
        _cfg({"cycle": {"expansion_reset_max": 40.0, "min_bars_since_cycle_end": 2}}),
    )
    assert out_allowed.expansion_reset_condition_met is True
    assert out_allowed.new_cycle_detected is True


def test_reclaim_reset_preserves_unknown_and_emits_reason_code() -> None:
    cfg = _cfg({"cycle": {"enable_reclaim_reset": True, "expansion_reset_max": 40.0, "min_bars_since_cycle_end": 2}})
    out_unknown = compute_invalidation_and_cycle(
        _phase(phase_floor_failed_pressure_build=False, phase_floor_failed_trend_resume=False, phase_floor_failed_transition_reclaim=False),
        _tier1(expansion_progress_structural=10.0),
        _tier2(),
        _context(
            prev_state_machine_state="rejected",
            bars_since_cycle_end=5,
            reclaim_below_reset_floor_seen_since_cycle_end=None,
        ),
        cfg,
    )
    assert out_unknown.reclaim_reset_condition_met is None
    assert out_unknown.new_cycle_detected is False
    assert out_unknown.cycle_reason_code == "RECLAIM_RESET_UNKNOWN"

    out_false = compute_invalidation_and_cycle(
        _phase(phase_floor_failed_pressure_build=False, phase_floor_failed_trend_resume=False, phase_floor_failed_transition_reclaim=False),
        _tier1(expansion_progress_structural=10.0),
        _tier2(),
        _context(
            prev_state_machine_state="rejected",
            bars_since_cycle_end=5,
            reclaim_below_reset_floor_seen_since_cycle_end=False,
        ),
        cfg,
    )
    assert out_false.reclaim_reset_condition_met is False
    assert out_false.new_cycle_detected is False
    assert out_false.cycle_reason_code == "NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET"

    out_true = compute_invalidation_and_cycle(
        _phase(phase_floor_failed_pressure_build=False, phase_floor_failed_trend_resume=False, phase_floor_failed_transition_reclaim=False),
        _tier1(expansion_progress_structural=10.0),
        _tier2(),
        _context(
            prev_state_machine_state="rejected",
            bars_since_cycle_end=5,
            reclaim_below_reset_floor_seen_since_cycle_end=True,
        ),
        cfg,
    )
    assert out_true.reclaim_reset_condition_met is True
    assert out_true.new_cycle_detected is True


def test_reclaim_reset_unknown_is_not_emitted_when_gate_disabled() -> None:
    out = compute_invalidation_and_cycle(
        _phase(
            phase_floor_failed_pressure_build=False,
            phase_floor_failed_trend_resume=False,
            phase_floor_failed_transition_reclaim=False,
        ),
        _tier1(expansion_progress_structural=10.0),
        _tier2(),
        _context(
            prev_state_machine_state="rejected",
            bars_since_cycle_end=5,
            reclaim_below_reset_floor_seen_since_cycle_end=None,
        ),
        _cfg({"cycle": {"enable_reclaim_reset": False, "expansion_reset_max": 40.0, "min_bars_since_cycle_end": 2}}),
    )
    assert out.reclaim_reset_condition_met is None
    assert out.cycle_reason_code != "RECLAIM_RESET_UNKNOWN"
    assert out.new_cycle_detected is True


def test_gate_disabled_with_expansion_none_keeps_non_reclaim_reason() -> None:
    out = compute_invalidation_and_cycle(
        _phase(),
        _tier1(expansion_progress_structural=None, expansion_progress_structural_not_evaluable=True),
        _tier2(),
        _context(
            prev_state_machine_state="rejected",
            bars_since_cycle_end=5,
            reclaim_below_reset_floor_seen_since_cycle_end=None,
        ),
        _cfg({"cycle": {"enable_reclaim_reset": False, "min_bars_since_cycle_end": 2}}),
    )
    assert out.expansion_reset_condition_met is None
    assert out.cycle_reason_code == "NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET"


def test_optional_reclaim_reset_gate():
    out = compute_invalidation_and_cycle(
        _phase(),
        _tier1(),
        _tier2(),
        _context(reclaim_below_reset_floor_seen_since_cycle_end=False),
        _cfg({"cycle": {"enable_reclaim_reset": True}}),
    )
    assert out.new_cycle_detected is False
    assert out.reclaim_reset_condition_met is False
    assert out.cycle_reason_code == "NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET"


def test_config_defaults_and_invalid_values_and_persisted_validation():
    cfg = _cfg({"invalidation": {"max_state_freshness": 80.0}})
    assert cfg.invalidation["max_state_freshness"] == 80.0
    assert cfg.invalidation["trend_resume"]["min_trend_hold"] == 55.0

    assert _cfg({"cycle": {"min_bars_since_cycle_end": 2}}).cycle["min_bars_since_cycle_end"] == 2

    with pytest.raises(ValueError, match=r"cycle.min_bars_since_cycle_end.*2.0"):
        _cfg({"cycle": {"min_bars_since_cycle_end": 2.0}}).cycle
    with pytest.raises(ValueError, match=r"cycle.min_bars_since_cycle_end.*2.9"):
        _cfg({"cycle": {"min_bars_since_cycle_end": 2.9}}).cycle
    with pytest.raises(ValueError, match=r"cycle.min_bars_since_cycle_end.*'3'"):
        _cfg({"cycle": {"min_bars_since_cycle_end": "3"}}).cycle
    with pytest.raises(ValueError, match=r"cycle.min_bars_since_cycle_end.*True"):
        _cfg({"cycle": {"min_bars_since_cycle_end": True}}).cycle
    with pytest.raises(ValueError, match=r"cycle.min_bars_since_cycle_end.*None"):
        _cfg({"cycle": {"min_bars_since_cycle_end": None}}).cycle
    with pytest.raises(ValueError, match="cycle.min_bars_since_cycle_end"):
        _cfg({"cycle": {"min_bars_since_cycle_end": -1}}).cycle

    with pytest.raises(ValueError, match="bars_since_early_entered"):
        _context(bars_since_early_entered=True)
