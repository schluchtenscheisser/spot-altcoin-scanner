from __future__ import annotations

import math
from typing import Any, Callable

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.entry.models import EntryPatternBundle
from scanner.phase.models import PhaseInterpretationBundle

_POSITIVE_PHASES = {"pressure_build", "trend_resume", "transition_reclaim"}
_PATTERN_ORDER: dict[str, list[str]] = {
    "pressure_build": ["range_reclaim", "break_and_hold", "breakout"],
    "trend_resume": ["resume_reclaim", "shallow_pullback", "continuation_breakout"],
    "transition_reclaim": ["base_reclaim", "ema_reclaim", "early_reversal_break"],
}


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _value_from_axis(phase_bundle: PhaseInterpretationBundle, tier1_bundle: Tier1AxisBundle, tier2_bundle: Tier2AxisBundle, axis: str) -> float | None:
    if axis == "freshness_distance_structural":
        return phase_bundle.freshness_distance_structural

    if hasattr(tier1_bundle, axis):
        return getattr(tier1_bundle, axis)

    if hasattr(tier2_bundle, axis):
        return getattr(tier2_bundle, axis)

    return None


def _all_required_finite(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    required_axes: set[str],
) -> bool:
    return all(_is_finite_number(_value_from_axis(phase_bundle, tier1_bundle, tier2_bundle, axis)) for axis in required_axes)


def compute_breakout_expansion_fit(expansion_progress_structural: float, target_expansion: float) -> float:
    return max(0.0, min(100.0, 100.0 - abs(expansion_progress_structural - target_expansion)))


def _evaluate_pressure_build(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: ScannerConfig,
) -> dict[str, float]:
    out: dict[str, float] = {}
    pressure_cfg = cfg.entry["pressure_build"]

    required = {"reclaim_progress", "compression_strength", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        reclaim = float(tier1_bundle.reclaim_progress)
        compression = float(tier1_bundle.compression_strength)
        freshness = float(phase_bundle.freshness_distance_structural)
        rr_cfg = pressure_cfg["range_reclaim"]
        if reclaim >= rr_cfg["min_reclaim"] and compression >= rr_cfg["min_compression"] and freshness <= rr_cfg["max_freshness"]:
            out["range_reclaim"] = 0.45 * reclaim + 0.30 * compression + 0.25 * (100.0 - freshness)

    required = {"expansion_progress_structural", "volume_regime_shift", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        expansion = float(tier1_bundle.expansion_progress_structural)
        volume = float(tier1_bundle.volume_regime_shift)
        freshness = float(phase_bundle.freshness_distance_structural)
        bo_cfg = pressure_cfg["breakout"]
        if expansion >= bo_cfg["min_expansion"] and volume >= bo_cfg["min_volume_shift"] and freshness <= bo_cfg["max_freshness"]:
            fit = compute_breakout_expansion_fit(expansion, float(bo_cfg["target_expansion"]))
            out["breakout"] = 0.40 * fit + 0.35 * volume + 0.25 * (100.0 - freshness)

    required = {"reclaim_progress", "base_integrity_simplified", "expansion_progress_structural", "volume_regime_shift"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        reclaim = float(tier1_bundle.reclaim_progress)
        base_integrity = float(tier2_bundle.base_integrity_simplified)
        expansion = float(tier1_bundle.expansion_progress_structural)
        volume = float(tier1_bundle.volume_regime_shift)
        bh_cfg = pressure_cfg["break_and_hold"]
        if (
            reclaim >= bh_cfg["min_reclaim"]
            and base_integrity >= bh_cfg["min_base_integrity"]
            and bh_cfg["min_expansion"] <= expansion <= bh_cfg["max_expansion"]
        ):
            out["break_and_hold"] = (
                0.35 * reclaim
                + 0.25 * base_integrity
                + 0.20 * volume
                + 0.20 * max(0.0, min(100.0, 100.0 - abs(expansion - 45.0)))
            )

    return out


def _evaluate_trend_resume(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: ScannerConfig,
) -> dict[str, float]:
    out: dict[str, float] = {}
    trend_cfg = cfg.entry["trend_resume"]

    required = {"pullback_quality_simplified", "trend_strength", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        pullback = float(tier2_bundle.pullback_quality_simplified)
        trend = float(tier1_bundle.trend_strength)
        freshness = float(phase_bundle.freshness_distance_structural)
        sp_cfg = trend_cfg["shallow_pullback"]
        if pullback >= sp_cfg["min_pullback_quality"] and trend >= sp_cfg["min_trend"] and freshness <= sp_cfg["max_freshness"]:
            out["shallow_pullback"] = 0.40 * pullback + 0.30 * trend + 0.30 * (100.0 - freshness)

    required = {"reclaim_progress", "reacceleration_strength_simplified", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        reclaim = float(tier1_bundle.reclaim_progress)
        reaccel = float(tier2_bundle.reacceleration_strength_simplified)
        freshness = float(phase_bundle.freshness_distance_structural)
        rr_cfg = trend_cfg["resume_reclaim"]
        if reclaim >= rr_cfg["min_reclaim"] and reaccel >= rr_cfg["min_reaccel"] and freshness <= rr_cfg["max_freshness"]:
            out["resume_reclaim"] = 0.35 * reclaim + 0.35 * reaccel + 0.30 * (100.0 - freshness)

    required = {"trend_strength", "reacceleration_strength_simplified", "expansion_progress_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        trend = float(tier1_bundle.trend_strength)
        reaccel = float(tier2_bundle.reacceleration_strength_simplified)
        expansion = float(tier1_bundle.expansion_progress_structural)
        cb_cfg = trend_cfg["continuation_breakout"]
        if trend >= cb_cfg["min_trend"] and reaccel >= cb_cfg["min_reaccel"] and expansion <= cb_cfg["max_expansion"]:
            out["continuation_breakout"] = 0.35 * trend + 0.35 * reaccel + 0.30 * (100.0 - expansion)

    return out


def _evaluate_transition_reclaim(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: ScannerConfig,
) -> dict[str, float]:
    out: dict[str, float] = {}
    trans_cfg = cfg.entry["transition_reclaim"]

    required = {"reclaim_progress", "trend_strength", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        reclaim = float(tier1_bundle.reclaim_progress)
        trend = float(tier1_bundle.trend_strength)
        freshness = float(phase_bundle.freshness_distance_structural)
        er_cfg = trans_cfg["ema_reclaim"]
        if reclaim >= er_cfg["min_reclaim"] and trend >= er_cfg["min_trend"] and freshness <= er_cfg["max_freshness"]:
            out["ema_reclaim"] = 0.45 * reclaim + 0.25 * trend + 0.30 * (100.0 - freshness)

    required = {"base_integrity_simplified", "reclaim_progress", "volume_regime_shift"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        base_integrity = float(tier2_bundle.base_integrity_simplified)
        reclaim = float(tier1_bundle.reclaim_progress)
        volume = float(tier1_bundle.volume_regime_shift)
        br_cfg = trans_cfg["base_reclaim"]
        if base_integrity >= br_cfg["min_base_integrity"] and reclaim >= br_cfg["min_reclaim"]:
            out["base_reclaim"] = 0.40 * base_integrity + 0.35 * reclaim + 0.25 * volume

    required = {"reclaim_progress", "volume_regime_shift", "freshness_distance_structural"}
    if _all_required_finite(phase_bundle, tier1_bundle, tier2_bundle, required):
        reclaim = float(tier1_bundle.reclaim_progress)
        volume = float(tier1_bundle.volume_regime_shift)
        freshness = float(phase_bundle.freshness_distance_structural)
        erb_cfg = trans_cfg["early_reversal_break"]
        if reclaim >= erb_cfg["min_reclaim"] and volume >= erb_cfg["min_volume_shift"] and freshness <= erb_cfg["max_freshness"]:
            out["early_reversal_break"] = 0.40 * reclaim + 0.30 * volume + 0.30 * (100.0 - freshness)

    return out


def _pick_best_pattern(scores: dict[str, float], phase: str) -> tuple[str, float]:
    if not scores:
        return "none", 0.0

    order = _PATTERN_ORDER[phase]
    best = sorted(scores.items(), key=lambda item: (-item[1], order.index(item[0])))[0]
    return best[0], float(best[1])


def resolve_entry_pattern(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: ScannerConfig,
) -> EntryPatternBundle:
    if not isinstance(phase_bundle, PhaseInterpretationBundle):
        raise TypeError("phase_bundle must be PhaseInterpretationBundle")
    if not isinstance(tier1_bundle, Tier1AxisBundle):
        raise TypeError("tier1_bundle must be Tier1AxisBundle")
    if not isinstance(tier2_bundle, Tier2AxisBundle):
        raise TypeError("tier2_bundle must be Tier2AxisBundle")
    if not isinstance(cfg, ScannerConfig):
        raise TypeError("cfg must be ScannerConfig")

    for field in ["symbol", "daily_bar_id", "intraday_bar_id", "data_4h_available"]:
        if getattr(phase_bundle, field) != getattr(tier1_bundle, field) or getattr(phase_bundle, field) != getattr(tier2_bundle, field):
            raise ValueError(f"bundle mismatch for {field}")

    phase = phase_bundle.market_phase
    if phase not in _POSITIVE_PHASES:
        return EntryPatternBundle(
            entry_pattern="none",
            entry_pattern_score=0.0,
            candidate_pattern_scores_within_phase={},
        )

    evaluators: dict[str, Callable[[PhaseInterpretationBundle, Tier1AxisBundle, Tier2AxisBundle, ScannerConfig], dict[str, float]]] = {
        "pressure_build": _evaluate_pressure_build,
        "trend_resume": _evaluate_trend_resume,
        "transition_reclaim": _evaluate_transition_reclaim,
    }
    candidate_scores = evaluators[phase](phase_bundle, tier1_bundle, tier2_bundle, cfg)
    best_pattern, best_score = _pick_best_pattern(candidate_scores, phase)

    return EntryPatternBundle(
        entry_pattern=best_pattern,
        entry_pattern_score=best_score,
        candidate_pattern_scores_within_phase=candidate_scores,
    )
