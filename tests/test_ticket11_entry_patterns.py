from __future__ import annotations

import dataclasses
import inspect

import pytest

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.entry import compute_breakout_expansion_fit, resolve_entry_pattern
from scanner.phase.models import PhaseInterpretationBundle


def _tier1(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 101,
        "intraday_bar_id": 202,
        "data_4h_available": True,
        "trend_strength": 70.0,
        "trend_strength_not_evaluable": False,
        "trend_strength_reduced_resolution": False,
        "trend_strength_effective_weight_ratio": 1.0,
        "reclaim_progress": 65.0,
        "reclaim_progress_not_evaluable": False,
        "reclaim_progress_reduced_resolution": False,
        "reclaim_progress_effective_weight_ratio": 1.0,
        "compression_strength": 70.0,
        "compression_strength_not_evaluable": False,
        "compression_strength_reduced_resolution": False,
        "compression_strength_effective_weight_ratio": 1.0,
        "expansion_progress_structural": 40.0,
        "expansion_progress_structural_not_evaluable": False,
        "expansion_progress_structural_reduced_resolution": False,
        "expansion_progress_structural_effective_weight_ratio": 1.0,
        "volume_regime_shift": 70.0,
        "volume_regime_shift_not_evaluable": False,
        "volume_regime_shift_reduced_resolution": False,
        "volume_regime_shift_effective_weight_ratio": 1.0,
        "freshness_distance_structural": 40.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
        "freshness_distance_structural_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier1AxisBundle(**base)


def _tier2(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 101,
        "intraday_bar_id": 202,
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


def _phase(market_phase: str = "pressure_build", **overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 101,
        "intraday_bar_id": 202,
        "data_4h_available": True,
        "market_phase": market_phase,
        "market_phase_confidence": 65.0,
        "market_phase_runner_up": "trend_resume",
        "market_phase_gap": 10.0,
        "market_phase_blended": False,
        "phase_score_pressure_build": 70.0,
        "phase_score_trend_resume": 60.0,
        "phase_score_transition_reclaim": 55.0,
        "phase_floor_margin_pressure_build": 5.0,
        "phase_floor_margin_trend_resume": 5.0,
        "phase_floor_margin_transition_reclaim": 5.0,
        "phase_floor_failed_pressure_build": False,
        "phase_floor_failed_trend_resume": False,
        "phase_floor_failed_transition_reclaim": False,
        "phase_eval_status_pressure_build": "score_computed",
        "phase_eval_status_trend_resume": "score_computed",
        "phase_eval_status_transition_reclaim": "score_computed",
        "freshness_distance_structural": 40.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": False,
    }
    base.update(overrides)
    return PhaseInterpretationBundle(**base)


def _cfg(overrides: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=overrides or {})


def test_phase_gate_for_none_and_unknown():
    out_none = resolve_entry_pattern(_phase("none"), _tier1(), _tier2(), _cfg())
    assert out_none.entry_pattern == "none"
    assert out_none.entry_pattern_score == 0.0
    assert out_none.candidate_pattern_scores_within_phase == {}

    out_unknown = resolve_entry_pattern(_phase("mystery"), _tier1(), _tier2(), _cfg())
    assert out_unknown.entry_pattern == "none"
    assert out_unknown.entry_pattern_score == 0.0
    assert out_unknown.candidate_pattern_scores_within_phase == {}


@pytest.mark.parametrize(
    ("expansion", "expected"),
    [(40.0, 100.0), (10.0, 70.0), (0.0, 60.0), (90.0, 50.0), (145.0, 0.0)],
)
def test_compute_breakout_expansion_fit_cases(expansion, expected):
    assert compute_breakout_expansion_fit(expansion, 40.0) == pytest.approx(expected)


def test_selection_and_candidate_dict_only_contains_admitted_patterns():
    out = resolve_entry_pattern(_phase("pressure_build"), _tier1(), _tier2(), _cfg())
    assert out.entry_pattern == "breakout"
    assert set(out.candidate_pattern_scores_within_phase.keys()) == {"range_reclaim", "breakout", "break_and_hold"}


def test_tie_break_order_is_deterministic_by_phase():
    cfg = _cfg(
        {
            "entry": {
                "pressure_build": {
                    "range_reclaim": {"min_reclaim": 0, "min_compression": 0, "max_freshness": 100},
                    "break_and_hold": {"min_reclaim": 0, "min_base_integrity": 0, "min_expansion": 0, "max_expansion": 100},
                },
                "trend_resume": {
                    "resume_reclaim": {"min_reclaim": 0, "min_reaccel": 0, "max_freshness": 100},
                    "shallow_pullback": {"min_pullback_quality": 0, "min_trend": 0, "max_freshness": 100},
                },
                "transition_reclaim": {
                    "base_reclaim": {"min_base_integrity": 0, "min_reclaim": 0},
                    "ema_reclaim": {"min_reclaim": 0, "min_trend": 0, "max_freshness": 100},
                },
            }
        }
    )

    pb = resolve_entry_pattern(
        _phase("pressure_build", freshness_distance_structural=0.0),
        _tier1(reclaim_progress=100, compression_strength=100, expansion_progress_structural=45, volume_regime_shift=100),
        _tier2(base_integrity_simplified=100),
        cfg,
    )
    assert pb.candidate_pattern_scores_within_phase["range_reclaim"] == pytest.approx(pb.candidate_pattern_scores_within_phase["break_and_hold"])
    assert pb.entry_pattern == "range_reclaim"

    tr = resolve_entry_pattern(
        _phase("trend_resume", freshness_distance_structural=0.0),
        _tier1(trend_strength=100, reclaim_progress=100, expansion_progress_structural=100),
        _tier2(pullback_quality_simplified=100, reacceleration_strength_simplified=100),
        cfg,
    )
    assert tr.candidate_pattern_scores_within_phase["resume_reclaim"] == pytest.approx(tr.candidate_pattern_scores_within_phase["shallow_pullback"])
    assert tr.entry_pattern == "resume_reclaim"

    trans = resolve_entry_pattern(
        _phase("transition_reclaim", freshness_distance_structural=0.0),
        _tier1(reclaim_progress=100, trend_strength=100, volume_regime_shift=100),
        _tier2(base_integrity_simplified=100),
        cfg,
    )
    assert trans.candidate_pattern_scores_within_phase["base_reclaim"] == pytest.approx(trans.candidate_pattern_scores_within_phase["ema_reclaim"])
    assert trans.entry_pattern == "base_reclaim"


def test_invalid_required_axis_blocks_admission_and_base_reclaim_requires_score_axis():
    out1 = resolve_entry_pattern(
        _phase("pressure_build"),
        _tier1(reclaim_progress=None),
        _tier2(),
        _cfg(),
    )
    assert "range_reclaim" not in out1.candidate_pattern_scores_within_phase

    out2 = resolve_entry_pattern(
        _phase("transition_reclaim"),
        _tier1(volume_regime_shift=None),
        _tier2(),
        _cfg(),
    )
    assert "base_reclaim" not in out2.candidate_pattern_scores_within_phase


def test_determinism_and_phase_isolation():
    phase = _phase("trend_resume")
    t1 = _tier1()
    t2 = _tier2()
    cfg = _cfg()
    out1 = resolve_entry_pattern(phase, t1, t2, cfg)
    out2 = resolve_entry_pattern(phase, t1, t2, cfg)
    assert dataclasses.asdict(out1) == dataclasses.asdict(out2)
    assert set(out1.candidate_pattern_scores_within_phase) <= {"shallow_pullback", "resume_reclaim", "continuation_breakout"}


def test_signature_has_exactly_four_declared_parameters():
    params = list(inspect.signature(resolve_entry_pattern).parameters)
    assert params == ["phase_bundle", "tier1_bundle", "tier2_bundle", "cfg"]
