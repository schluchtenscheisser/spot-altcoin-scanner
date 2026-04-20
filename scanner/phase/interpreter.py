from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Mapping

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase.models import PhaseInterpretationBundle

_PHASE_PRIORITY = ["pressure_build", "trend_resume", "transition_reclaim"]


@dataclass(frozen=True)
class _Axis:
    value: float | None
    not_evaluable: bool
    reduced_resolution: bool
    effective_weight_ratio: float | None


@dataclass(frozen=True)
class _PhaseResult:
    score: float
    floor_margin: float | None
    floor_failed: bool
    eval_status: str


def _is_finite_0_100(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and 0.0 <= float(value) <= 100.0


def _validate_axis(name: str, axis: _Axis) -> None:
    if axis.not_evaluable:
        if axis.value is not None:
            raise ValueError(f"{name} invalid: value must be None when not_evaluable=True")
        if axis.effective_weight_ratio is not None:
            raise ValueError(f"{name} invalid: effective_weight_ratio must be None when not_evaluable=True")
        if axis.reduced_resolution:
            raise ValueError(f"{name} invalid: reduced_resolution must be False when not_evaluable=True")
        return

    if axis.value is None:
        raise ValueError(f"{name} invalid: value must not be None when not_evaluable=False")
    if not _is_finite_0_100(axis.value):
        raise ValueError(f"{name} invalid: value {axis.value!r} must be finite in [0,100]")
    if axis.effective_weight_ratio is None:
        raise ValueError(f"{name} invalid: effective_weight_ratio must not be None when evaluable")
    if not _is_finite_0_100(float(axis.effective_weight_ratio) * 100.0):
        raise ValueError(
            f"{name} invalid: effective_weight_ratio {axis.effective_weight_ratio!r} must be finite in [0,1]"
        )


def _axis_from_bundle(bundle: Any, name: str) -> _Axis:
    return _Axis(
        value=getattr(bundle, name),
        not_evaluable=getattr(bundle, f"{name}_not_evaluable"),
        reduced_resolution=getattr(bundle, f"{name}_reduced_resolution"),
        effective_weight_ratio=getattr(bundle, f"{name}_effective_weight_ratio"),
    )


def _weighted_score(
    components: list[tuple[str, float, _Axis]],
    min_effective_weight_ratio: float,
) -> tuple[float | None, bool]:
    total_weight = sum(weight for _, weight, _ in components)
    used = [(name, weight, axis) for name, weight, axis in components if axis.value is not None]
    retained_weight = sum(weight for _, weight, _ in used)
    effective_ratio = retained_weight / total_weight if total_weight > 0 else 0.0
    if retained_weight == 0 or effective_ratio < min_effective_weight_ratio:
        return None, False

    score = sum(weight * float(axis.value) for _, weight, axis in used) / retained_weight
    reduced_resolution = any(axis.reduced_resolution for _, _, axis in used)
    return score, reduced_resolution


def _rank_phases(results: Mapping[str, _PhaseResult]) -> list[str]:
    def margin_value(phase: str) -> float:
        margin = results[phase].floor_margin
        return float("-inf") if margin is None else float(margin)

    return sorted(
        _PHASE_PRIORITY,
        key=lambda phase: (-results[phase].score, -margin_value(phase), _PHASE_PRIORITY.index(phase)),
    )


def _phase_cfg(cfg: ScannerConfig) -> dict[str, Any]:
    return cfg.phase


def _require_matching_identity(t1: Tier1AxisBundle, t2: Tier2AxisBundle) -> None:
    for field in ["symbol", "daily_bar_id", "intraday_bar_id", "data_4h_available"]:
        if getattr(t1, field) != getattr(t2, field):
            raise ValueError(f"bundle mismatch for {field}")


def _evaluate_pressure_build(
    axes: Mapping[str, _Axis],
    phase_cfg: Mapping[str, Any],
    min_effective_weight_ratio: float,
) -> tuple[_PhaseResult, bool]:
    cs, vrs, eps, bis = (
        axes["compression_strength"],
        axes["volume_regime_shift"],
        axes["expansion_progress_structural"],
        axes["base_integrity_simplified"],
    )

    if cs.not_evaluable or vrs.not_evaluable:
        return _PhaseResult(0.0, None, True, "minimum_basis_not_met"), False

    if eps.not_evaluable:
        return _PhaseResult(0.0, None, True, "hard_floor_failed"), False

    floor_margin = min(
        float(cs.value) - float(phase_cfg["floor_compression"]),
        float(vrs.value) - float(phase_cfg["floor_volume_shift"]),
        float(phase_cfg["max_expansion"]) - float(eps.value),
    )
    floors_ok = (
        float(cs.value) >= float(phase_cfg["floor_compression"])
        and float(vrs.value) >= float(phase_cfg["floor_volume_shift"])
        and float(eps.value) <= float(phase_cfg["max_expansion"])
    )
    if not floors_ok:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False

    score, reduced = _weighted_score(
        [
            ("compression_strength", 0.40, cs),
            ("base_integrity_simplified", 0.20, bis),
            ("volume_regime_shift", 0.20, vrs),
            ("expansion_progress_structural_inverse", 0.20, _Axis(100.0 - float(eps.value), False, eps.reduced_resolution, 1.0)),
        ],
        min_effective_weight_ratio,
    )
    if score is None:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False
    return _PhaseResult(float(score), floor_margin, False, "score_computed"), reduced


def _evaluate_trend_resume(
    axes: Mapping[str, _Axis],
    phase_cfg: Mapping[str, Any],
    min_effective_weight_ratio: float,
) -> tuple[_PhaseResult, bool]:
    ts, rp, eps, pqs, rss = (
        axes["trend_strength"],
        axes["reclaim_progress"],
        axes["expansion_progress_structural"],
        axes["pullback_quality_simplified"],
        axes["reacceleration_strength_simplified"],
    )
    if ts.not_evaluable or rp.not_evaluable:
        return _PhaseResult(0.0, None, True, "minimum_basis_not_met"), False
    if eps.not_evaluable:
        return _PhaseResult(0.0, None, True, "hard_floor_failed"), False

    floor_margin = min(
        float(ts.value) - float(phase_cfg["floor_trend"]),
        float(rp.value) - float(phase_cfg["floor_reclaim"]),
        float(phase_cfg["max_expansion"]) - float(eps.value),
    )
    floors_ok = (
        float(ts.value) >= float(phase_cfg["floor_trend"])
        and float(rp.value) >= float(phase_cfg["floor_reclaim"])
        and float(eps.value) <= float(phase_cfg["max_expansion"])
    )
    if not floors_ok:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False

    score, reduced = _weighted_score(
        [
            ("trend_strength", 0.35, ts),
            ("pullback_quality_simplified", 0.25, pqs),
            ("reacceleration_strength_simplified", 0.20, rss),
            ("reclaim_progress", 0.20, rp),
        ],
        min_effective_weight_ratio,
    )
    if score is None:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False
    return _PhaseResult(float(score), floor_margin, False, "score_computed"), reduced


def _evaluate_transition_reclaim(
    axes: Mapping[str, _Axis],
    phase_cfg: Mapping[str, Any],
    min_effective_weight_ratio: float,
) -> tuple[_PhaseResult, bool]:
    rp, vrs, eps, ts, bis = (
        axes["reclaim_progress"],
        axes["volume_regime_shift"],
        axes["expansion_progress_structural"],
        axes["trend_strength"],
        axes["base_integrity_simplified"],
    )
    if rp.not_evaluable or (vrs.not_evaluable and ts.not_evaluable):
        return _PhaseResult(0.0, None, True, "minimum_basis_not_met"), False
    if vrs.not_evaluable or eps.not_evaluable:
        return _PhaseResult(0.0, None, True, "hard_floor_failed"), False

    floor_margin = min(
        float(rp.value) - float(phase_cfg["floor_reclaim"]),
        float(vrs.value) - float(phase_cfg["floor_volume_shift"]),
        float(phase_cfg["max_expansion"]) - float(eps.value),
    )
    floors_ok = (
        float(rp.value) >= float(phase_cfg["floor_reclaim"])
        and float(vrs.value) >= float(phase_cfg["floor_volume_shift"])
        and float(eps.value) <= float(phase_cfg["max_expansion"])
    )
    if not floors_ok:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False

    score, reduced = _weighted_score(
        [
            ("reclaim_progress", 0.40, rp),
            ("base_integrity_simplified", 0.20, bis),
            ("volume_regime_shift", 0.20, vrs),
            ("expansion_progress_structural_inverse", 0.20, _Axis(100.0 - float(eps.value), False, eps.reduced_resolution, 1.0)),
        ],
        min_effective_weight_ratio,
    )
    if score is None:
        return _PhaseResult(0.0, floor_margin, True, "hard_floor_failed"), False
    return _PhaseResult(float(score), floor_margin, False, "score_computed"), reduced


def compute_phase_interpretation(
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: ScannerConfig,
) -> PhaseInterpretationBundle:
    if not isinstance(tier1_bundle, Tier1AxisBundle):
        raise TypeError("tier1_bundle must be Tier1AxisBundle")
    if not isinstance(tier2_bundle, Tier2AxisBundle):
        raise TypeError("tier2_bundle must be Tier2AxisBundle")
    if not isinstance(cfg, ScannerConfig):
        raise TypeError("cfg must be ScannerConfig")

    _require_matching_identity(tier1_bundle, tier2_bundle)

    axes = {
        name: _axis_from_bundle(tier1_bundle, name)
        for name in [
            "trend_strength",
            "reclaim_progress",
            "compression_strength",
            "expansion_progress_structural",
            "volume_regime_shift",
            "freshness_distance_structural",
        ]
    }
    axes.update(
        {
            name: _axis_from_bundle(tier2_bundle, name)
            for name in [
                "base_integrity_simplified",
                "pullback_quality_simplified",
                "reacceleration_strength_simplified",
            ]
        }
    )

    for name, axis in axes.items():
        _validate_axis(name, axis)

    pcfg = _phase_cfg(cfg)
    min_effective_weight_ratio = float(pcfg["min_effective_weight_ratio"])

    pressure, pressure_rr = _evaluate_pressure_build(axes, pcfg["pressure_build"], min_effective_weight_ratio)
    trend, trend_rr = _evaluate_trend_resume(axes, pcfg["trend_resume"], min_effective_weight_ratio)
    transition, transition_rr = _evaluate_transition_reclaim(axes, pcfg["transition_reclaim"], min_effective_weight_ratio)

    results = {
        "pressure_build": pressure,
        "trend_resume": trend,
        "transition_reclaim": transition,
    }
    ranked = _rank_phases(results)
    top_phase = ranked[0]
    runner_up_phase = ranked[1]
    top_score = results[top_phase].score
    runner_up_score = results[runner_up_phase].score

    market_phase = top_phase
    market_phase_confidence = top_score
    if top_score < float(pcfg["global_confidence_floor"]):
        market_phase = "none"
        market_phase_confidence = top_score
    else:
        rr_map = {
            "pressure_build": pressure_rr,
            "trend_resume": trend_rr,
            "transition_reclaim": transition_rr,
        }
        if rr_map[top_phase]:
            market_phase_confidence = min(top_score, float(pcfg["reduced_resolution_confidence_cap"]))

    market_phase_gap = top_score - runner_up_score
    market_phase_blended = market_phase != "none" and market_phase_gap < float(pcfg["phase_gap_floor"])

    fresh = axes["freshness_distance_structural"]

    return PhaseInterpretationBundle(
        symbol=tier1_bundle.symbol,
        daily_bar_id=tier1_bundle.daily_bar_id,
        intraday_bar_id=tier1_bundle.intraday_bar_id,
        data_4h_available=tier1_bundle.data_4h_available,
        market_phase=market_phase,
        market_phase_confidence=float(market_phase_confidence),
        market_phase_runner_up=runner_up_phase,
        market_phase_gap=float(market_phase_gap),
        market_phase_blended=market_phase_blended,
        phase_score_pressure_build=float(pressure.score),
        phase_score_trend_resume=float(trend.score),
        phase_score_transition_reclaim=float(transition.score),
        phase_floor_margin_pressure_build=pressure.floor_margin,
        phase_floor_margin_trend_resume=trend.floor_margin,
        phase_floor_margin_transition_reclaim=transition.floor_margin,
        phase_floor_failed_pressure_build=pressure.floor_failed,
        phase_floor_failed_trend_resume=trend.floor_failed,
        phase_floor_failed_transition_reclaim=transition.floor_failed,
        phase_eval_status_pressure_build=pressure.eval_status,
        phase_eval_status_trend_resume=trend.eval_status,
        phase_eval_status_transition_reclaim=transition.eval_status,
        freshness_distance_structural=fresh.value,
        freshness_distance_structural_not_evaluable=fresh.not_evaluable,
        freshness_distance_structural_reduced_resolution=fresh.reduced_resolution,
    )
