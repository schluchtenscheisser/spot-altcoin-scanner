from __future__ import annotations

import dataclasses
import math

import pytest

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase import PhaseInterpretationBundle, compute_phase_interpretation


def _tier1(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 1,
        "intraday_bar_id": 2,
        "data_4h_available": True,
        "trend_strength": 70.0,
        "trend_strength_not_evaluable": False,
        "trend_strength_reduced_resolution": False,
        "trend_strength_effective_weight_ratio": 1.0,
        "reclaim_progress": 65.0,
        "reclaim_progress_not_evaluable": False,
        "reclaim_progress_reduced_resolution": False,
        "reclaim_progress_effective_weight_ratio": 1.0,
        "compression_strength": 68.0,
        "compression_strength_not_evaluable": False,
        "compression_strength_reduced_resolution": False,
        "compression_strength_effective_weight_ratio": 1.0,
        "expansion_progress_structural": 35.0,
        "expansion_progress_structural_not_evaluable": False,
        "expansion_progress_structural_reduced_resolution": False,
        "expansion_progress_structural_effective_weight_ratio": 1.0,
        "volume_regime_shift": 72.0,
        "volume_regime_shift_not_evaluable": False,
        "volume_regime_shift_reduced_resolution": False,
        "volume_regime_shift_effective_weight_ratio": 1.0,
        "freshness_distance_structural": 40.0,
        "freshness_distance_structural_not_evaluable": False,
        "freshness_distance_structural_reduced_resolution": True,
        "freshness_distance_structural_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier1AxisBundle(**base)


def _tier2(**overrides):
    base = {
        "symbol": "TESTUSDT",
        "daily_bar_id": 1,
        "intraday_bar_id": 2,
        "data_4h_available": True,
        "base_integrity_simplified": 74.0,
        "base_integrity_simplified_not_evaluable": False,
        "base_integrity_simplified_reduced_resolution": False,
        "base_integrity_simplified_effective_weight_ratio": 1.0,
        "pullback_quality_simplified": 69.0,
        "pullback_quality_simplified_not_evaluable": False,
        "pullback_quality_simplified_reduced_resolution": False,
        "pullback_quality_simplified_effective_weight_ratio": 1.0,
        "reacceleration_strength_simplified": 63.0,
        "reacceleration_strength_simplified_not_evaluable": False,
        "reacceleration_strength_simplified_reduced_resolution": False,
        "reacceleration_strength_simplified_effective_weight_ratio": 1.0,
    }
    base.update(overrides)
    return Tier2AxisBundle(**base)


def _cfg(overrides: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=overrides or {})


def test_output_contract_and_determinism():
    out1 = compute_phase_interpretation(_tier1(), _tier2(), _cfg())
    out2 = compute_phase_interpretation(_tier1(), _tier2(), _cfg())
    assert isinstance(out1, PhaseInterpretationBundle)
    assert dataclasses.asdict(out1) == dataclasses.asdict(out2)


def test_type_validation_and_bundle_identity_validation():
    with pytest.raises(TypeError):
        compute_phase_interpretation({}, _tier2(), _cfg())
    with pytest.raises(TypeError):
        compute_phase_interpretation(_tier1(), _tier2(), {})
    with pytest.raises(ValueError, match="symbol"):
        compute_phase_interpretation(_tier1(symbol="AAAUSDT"), _tier2(symbol="BBB"), _cfg())


def test_axis_validation_rejects_non_finite_and_inconsistent_nullability():
    t1 = _tier1(trend_strength=float("nan"))
    with pytest.raises(ValueError, match="trend_strength"):
        compute_phase_interpretation(t1, _tier2(), _cfg())

    t2 = _tier2(pullback_quality_simplified=None, pullback_quality_simplified_not_evaluable=False)
    with pytest.raises(ValueError, match="pullback_quality_simplified"):
        compute_phase_interpretation(_tier1(), t2, _cfg())


def test_minimum_basis_failures():
    out_pb = compute_phase_interpretation(
        _tier1(compression_strength=None, compression_strength_not_evaluable=True, compression_strength_effective_weight_ratio=None),
        _tier2(),
        _cfg(),
    )
    assert out_pb.phase_eval_status_pressure_build == "minimum_basis_not_met"
    assert out_pb.phase_floor_margin_pressure_build is None

    out_tr = compute_phase_interpretation(
        _tier1(trend_strength=None, trend_strength_not_evaluable=True, trend_strength_effective_weight_ratio=None),
        _tier2(),
        _cfg(),
    )
    assert out_tr.phase_eval_status_trend_resume == "minimum_basis_not_met"

    out_trans = compute_phase_interpretation(
        _tier1(
            trend_strength=None,
            trend_strength_not_evaluable=True,
            trend_strength_effective_weight_ratio=None,
            volume_regime_shift=None,
            volume_regime_shift_not_evaluable=True,
            volume_regime_shift_effective_weight_ratio=None,
        ),
        _tier2(),
        _cfg(),
    )
    assert out_trans.phase_eval_status_transition_reclaim == "minimum_basis_not_met"


def test_hard_floor_failure_vs_basis_failure():
    out = compute_phase_interpretation(
        _tier1(compression_strength=58.0, volume_regime_shift=70.0, expansion_progress_structural=20.0),
        _tier2(),
        _cfg(),
    )
    assert out.phase_eval_status_pressure_build == "hard_floor_failed"
    assert out.phase_floor_margin_pressure_build < 0

    out2 = compute_phase_interpretation(
        _tier1(
            expansion_progress_structural=None,
            expansion_progress_structural_not_evaluable=True,
            expansion_progress_structural_effective_weight_ratio=None,
        ),
        _tier2(),
        _cfg(),
    )
    assert out2.phase_eval_status_pressure_build == "hard_floor_failed"
    assert out2.phase_floor_margin_pressure_build is None


def test_weighted_score_goldens_and_phase_local_dropout():
    out = compute_phase_interpretation(_tier1(), _tier2(), _cfg())
    expected_pressure = 0.40 * 68 + 0.20 * 74 + 0.20 * 72 + 0.20 * (100 - 35)
    expected_trend = 0.35 * 70 + 0.25 * 69 + 0.20 * 63 + 0.20 * 65
    expected_transition = 0.40 * 65 + 0.20 * 74 + 0.20 * 72 + 0.20 * (100 - 35)
    assert out.phase_score_pressure_build == pytest.approx(expected_pressure)
    assert out.phase_score_trend_resume == pytest.approx(expected_trend)
    assert out.phase_score_transition_reclaim == pytest.approx(expected_transition)

    out_dropout = compute_phase_interpretation(
        _tier1(),
        _tier2(base_integrity_simplified=None, base_integrity_simplified_not_evaluable=True, base_integrity_simplified_effective_weight_ratio=None),
        _cfg(),
    )
    expected_pb_dropout = (0.40 * 68 + 0.20 * 72 + 0.20 * (100 - 35)) / 0.80
    assert out_dropout.phase_score_pressure_build == pytest.approx(expected_pb_dropout)


def test_trend_optional_dropout_below_weight_ratio_is_hard_floor_failed_with_margin_kept():
    out = compute_phase_interpretation(
        _tier1(trend_strength=70.0, reclaim_progress=60.0, expansion_progress_structural=40.0),
        _tier2(
            pullback_quality_simplified=None,
            pullback_quality_simplified_not_evaluable=True,
            pullback_quality_simplified_effective_weight_ratio=None,
            reacceleration_strength_simplified=None,
            reacceleration_strength_simplified_not_evaluable=True,
            reacceleration_strength_simplified_effective_weight_ratio=None,
        ),
        _cfg(),
    )
    assert out.phase_score_trend_resume == 0.0
    assert out.phase_eval_status_trend_resume == "hard_floor_failed"
    assert out.phase_floor_margin_trend_resume == pytest.approx(15.0)


def test_reduced_resolution_cap_and_floor_only_rr_not_triggered():
    out_cap = compute_phase_interpretation(
        _tier1(compression_strength_reduced_resolution=True),
        _tier2(),
        _cfg({"phase": {"reduced_resolution_confidence_cap": 60.0}}),
    )
    assert out_cap.market_phase == "pressure_build"
    assert out_cap.market_phase_confidence == 60.0

    out_no_cap = compute_phase_interpretation(
        _tier1(
            expansion_progress_structural_reduced_resolution=True,
            compression_strength=60.0,
            volume_regime_shift=50.0,
            reclaim_progress=55.0,
        ),
        _tier2(),
        _cfg({"phase": {"reduced_resolution_confidence_cap": 60.0}}),
    )
    assert out_no_cap.market_phase == "trend_resume"
    assert out_no_cap.market_phase_confidence > 60.0


def test_global_confidence_floor_none_path_and_blended_logic():
    out_none = compute_phase_interpretation(
        _tier1(compression_strength=52.0, trend_strength=52.0, reclaim_progress=50.0, volume_regime_shift=52.0),
        _tier2(base_integrity_simplified=52.0, pullback_quality_simplified=52.0, reacceleration_strength_simplified=52.0),
        _cfg({"phase": {"global_confidence_floor": 55.0}}),
    )
    assert out_none.market_phase == "none"
    assert out_none.market_phase_blended is False

    out_blended = compute_phase_interpretation(
        _tier1(compression_strength=72.0, trend_strength=70.0, reclaim_progress=66.0, volume_regime_shift=70.0, expansion_progress_structural=35.0),
        _tier2(base_integrity_simplified=70.0, pullback_quality_simplified=67.0, reacceleration_strength_simplified=65.0),
        _cfg({"phase": {"phase_gap_floor": 10.0}}),
    )
    assert out_blended.market_phase != "none"
    assert out_blended.market_phase_gap < 10.0
    assert out_blended.market_phase_blended is True


def test_tie_break_and_runner_up_are_deterministic_even_all_zero():
    out_tie = compute_phase_interpretation(
        _tier1(compression_strength=60.0, trend_strength=55.0, reclaim_progress=45.0, volume_regime_shift=50.0, expansion_progress_structural=50.0),
        _tier2(base_integrity_simplified=0.0, pullback_quality_simplified=0.0, reacceleration_strength_simplified=0.0),
        _cfg({"phase": {"global_confidence_floor": 0.0}}),
    )
    assert out_tie.market_phase in {"pressure_build", "trend_resume", "transition_reclaim"}
    assert out_tie.market_phase_runner_up in {"pressure_build", "trend_resume", "transition_reclaim"}

    out_zero = compute_phase_interpretation(
        _tier1(
            compression_strength=None,
            compression_strength_not_evaluable=True,
            compression_strength_effective_weight_ratio=None,
            trend_strength=None,
            trend_strength_not_evaluable=True,
            trend_strength_effective_weight_ratio=None,
            reclaim_progress=None,
            reclaim_progress_not_evaluable=True,
            reclaim_progress_effective_weight_ratio=None,
            volume_regime_shift=None,
            volume_regime_shift_not_evaluable=True,
            volume_regime_shift_effective_weight_ratio=None,
        ),
        _tier2(),
        _cfg(),
    )
    assert out_zero.market_phase == "none"
    assert out_zero.market_phase_gap == 0.0
    assert out_zero.market_phase_runner_up in {"pressure_build", "trend_resume", "transition_reclaim"}


def test_freshness_passthrough_without_phase_influence_and_null_stays_null():
    base = compute_phase_interpretation(_tier1(freshness_distance_structural=20.0), _tier2(), _cfg())
    changed = compute_phase_interpretation(_tier1(freshness_distance_structural=90.0), _tier2(), _cfg())
    assert base.market_phase == changed.market_phase
    assert base.market_phase_confidence == changed.market_phase_confidence

    out_null = compute_phase_interpretation(
        _tier1(
            freshness_distance_structural=None,
            freshness_distance_structural_not_evaluable=True,
            freshness_distance_structural_reduced_resolution=False,
            freshness_distance_structural_effective_weight_ratio=None,
        ),
        _tier2(),
        _cfg(),
    )
    assert out_null.freshness_distance_structural is None
    assert out_null.freshness_distance_structural_not_evaluable is True


def test_phase_config_defaults_merge_and_invalid_values():
    cfg = _cfg()
    assert cfg.phase["global_confidence_floor"] == pytest.approx(55.0)

    cfg_partial = _cfg({"phase": {"pressure_build": {"floor_compression": 62.0}}})
    assert cfg_partial.phase["pressure_build"]["floor_compression"] == pytest.approx(62.0)
    assert cfg_partial.phase["pressure_build"]["floor_volume_shift"] == pytest.approx(50.0)

    with pytest.raises(ValueError, match="phase.trend_resume"):
        _cfg({"phase": {"trend_resume": "bad"}}).phase

    with pytest.raises(ValueError, match="phase.phase_gap_floor"):
        _cfg({"phase": {"phase_gap_floor": math.nan}}).phase
