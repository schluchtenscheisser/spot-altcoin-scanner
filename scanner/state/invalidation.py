from __future__ import annotations

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.cycle import resolve_cycle_state
from scanner.state.models import InvalidationCycleBundle, PersistedStateCycleContext

_ACTIVE_PRIOR_STATES = {"watch", "early_ready", "confirmed_ready", "late"}
_EARLY_OR_CONFIRMED = {"early_ready", "confirmed_ready"}


def _require_input_types(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    persisted_context: PersistedStateCycleContext,
    cfg: ScannerConfig,
) -> None:
    if not isinstance(phase_bundle, PhaseInterpretationBundle):
        raise TypeError("phase_bundle must be PhaseInterpretationBundle")
    if not isinstance(tier1_bundle, Tier1AxisBundle):
        raise TypeError("tier1_bundle must be Tier1AxisBundle")
    if not isinstance(tier2_bundle, Tier2AxisBundle):
        raise TypeError("tier2_bundle must be Tier2AxisBundle")
    if not isinstance(persisted_context, PersistedStateCycleContext):
        raise TypeError("persisted_context must be PersistedStateCycleContext")
    if not isinstance(cfg, ScannerConfig):
        raise TypeError("cfg must be ScannerConfig")


def _require_matching_identity(phase: PhaseInterpretationBundle, t1: Tier1AxisBundle, t2: Tier2AxisBundle) -> None:
    for field in ["symbol", "daily_bar_id", "intraday_bar_id", "data_4h_available"]:
        v1 = getattr(phase, field)
        if v1 != getattr(t1, field) or v1 != getattr(t2, field):
            raise ValueError(f"bundle mismatch for {field}")


def _g1_phase_to_none(phase: PhaseInterpretationBundle, context: PersistedStateCycleContext) -> bool:
    if phase.market_phase != "none":
        return False
    if context.prev_state_machine_state not in _ACTIVE_PRIOR_STATES:
        return False
    if context.current_setup_cycle_id is None:
        return False
    return context.state_recorded_in_cycle_id == context.current_setup_cycle_id


def _g2_insufficient_tier1(t1: Tier1AxisBundle) -> bool:
    fields = ["trend_strength", "reclaim_progress", "compression_strength", "volume_regime_shift"]
    null_like = 0
    for field in fields:
        value = getattr(t1, field)
        not_eval = getattr(t1, f"{field}_not_evaluable")
        if value is None or bool(not_eval):
            null_like += 1
    return null_like >= 2


def _compute_structural(
    phase: PhaseInterpretationBundle,
    t1: Tier1AxisBundle,
    t2: Tier2AxisBundle,
    context: PersistedStateCycleContext,
    invalidation_cfg: dict,
) -> tuple[bool, str | None]:
    reasons: list[str] = []

    if _g1_phase_to_none(phase, context):
        reasons.append("PHASE_TO_NONE")
    if _g2_insufficient_tier1(t1):
        reasons.append("INSUFFICIENT_TIER1_SUPPORT")

    if phase.market_phase == "pressure_build":
        if t1.compression_strength is not None and t1.compression_strength < invalidation_cfg["pressure_build"]["min_compression_hold"]:
            reasons.append("PRESSURE_BUILD_COMPRESSION_BREAK")
        if t2.base_integrity_simplified is not None and t2.base_integrity_simplified < invalidation_cfg["pressure_build"]["min_base_hold"]:
            reasons.append("PRESSURE_BUILD_BASE_BREAK")
        if t1.volume_regime_shift is not None and t1.volume_regime_shift < invalidation_cfg["pressure_build"]["min_volume_shift_hold"]:
            reasons.append("PRESSURE_BUILD_VOLUME_BREAK")
    elif phase.market_phase == "trend_resume":
        if t1.trend_strength is not None and t1.trend_strength < invalidation_cfg["trend_resume"]["min_trend_hold"]:
            reasons.append("TREND_RESUME_TREND_BREAK")
        if t1.reclaim_progress is not None and t1.reclaim_progress < invalidation_cfg["trend_resume"]["min_reclaim_hold"]:
            reasons.append("TREND_RESUME_RECLAIM_BREAK")
        if t2.pullback_quality_simplified is not None and t2.pullback_quality_simplified < invalidation_cfg["trend_resume"]["min_pullback_hold"]:
            reasons.append("TREND_RESUME_PULLBACK_FAILURE")
        if (
            context.prev_state_machine_state in _EARLY_OR_CONFIRMED
            and t2.reacceleration_strength_simplified is not None
            and t2.reacceleration_strength_simplified < invalidation_cfg["trend_resume"]["min_reaccel_hold"]
        ):
            reasons.append("TREND_RESUME_REACCEL_FAILURE")
    elif phase.market_phase == "transition_reclaim":
        if t1.reclaim_progress is not None and t1.reclaim_progress < invalidation_cfg["transition_reclaim"]["min_reclaim_hold"]:
            reasons.append("TRANSITION_RECLAIM_RECLAIM_BREAK")
        if t2.base_integrity_simplified is not None and t2.base_integrity_simplified < invalidation_cfg["transition_reclaim"]["min_base_hold"]:
            reasons.append("TRANSITION_RECLAIM_BASE_BREAK")
        if t1.volume_regime_shift is not None and t1.volume_regime_shift < invalidation_cfg["transition_reclaim"]["min_volume_shift_hold"]:
            reasons.append("TRANSITION_RECLAIM_VOLUME_BREAK")

    priority = [
        "PHASE_TO_NONE",
        "INSUFFICIENT_TIER1_SUPPORT",
        "PRESSURE_BUILD_COMPRESSION_BREAK",
        "PRESSURE_BUILD_BASE_BREAK",
        "PRESSURE_BUILD_VOLUME_BREAK",
        "TREND_RESUME_TREND_BREAK",
        "TREND_RESUME_RECLAIM_BREAK",
        "TREND_RESUME_PULLBACK_FAILURE",
        "TREND_RESUME_REACCEL_FAILURE",
        "TRANSITION_RECLAIM_RECLAIM_BREAK",
        "TRANSITION_RECLAIM_BASE_BREAK",
        "TRANSITION_RECLAIM_VOLUME_BREAK",
    ]
    for item in priority:
        if item in reasons:
            return True, item
    return False, None


def _compute_timing(
    phase: PhaseInterpretationBundle,
    t1: Tier1AxisBundle,
    context: PersistedStateCycleContext,
    invalidation_cfg: dict,
) -> tuple[bool, str | None]:
    reasons: list[str] = []

    if context.freshness_distance_state_early is not None and context.freshness_distance_state_early >= invalidation_cfg["max_state_freshness"]:
        reasons.append("STATE_FRESHNESS_EARLY_MAXED")
    if (
        context.freshness_distance_state_confirmed is not None
        and context.freshness_distance_state_confirmed >= invalidation_cfg["max_state_freshness"]
    ):
        reasons.append("STATE_FRESHNESS_CONFIRMED_MAXED")
    if t1.expansion_progress_structural is not None and t1.expansion_progress_structural >= invalidation_cfg["max_expansion_progress"]:
        reasons.append("EXPANSION_PROGRESS_MAXED")
    if (
        context.prev_state_machine_state in _EARLY_OR_CONFIRMED
        and phase.freshness_distance_structural is not None
        and phase.freshness_distance_structural >= invalidation_cfg["max_structural_freshness"]
    ):
        reasons.append("STRUCTURAL_FRESHNESS_MAXED")

    priority = [
        "STATE_FRESHNESS_EARLY_MAXED",
        "STATE_FRESHNESS_CONFIRMED_MAXED",
        "EXPANSION_PROGRESS_MAXED",
        "STRUCTURAL_FRESHNESS_MAXED",
    ]
    for item in priority:
        if item in reasons:
            return True, item
    return False, None


def compute_invalidation_and_cycle(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    persisted_context: PersistedStateCycleContext,
    cfg: ScannerConfig,
) -> InvalidationCycleBundle:
    _require_input_types(phase_bundle, tier1_bundle, tier2_bundle, persisted_context, cfg)
    _require_matching_identity(phase_bundle, tier1_bundle, tier2_bundle)
    if persisted_context.symbol != phase_bundle.symbol:
        raise ValueError("bundle mismatch for symbol")

    structural, structural_reason = _compute_structural(
        phase_bundle,
        tier1_bundle,
        tier2_bundle,
        persisted_context,
        cfg.invalidation,
    )

    if structural:
        timing = False
        timing_reason = None
    else:
        timing, timing_reason = _compute_timing(phase_bundle, tier1_bundle, persisted_context, cfg.invalidation)

    cycle = resolve_cycle_state(
        phase_bundle=phase_bundle,
        tier1_bundle=tier1_bundle,
        persisted_context=persisted_context,
        cycle_cfg=cfg.cycle,
        structural_invalidation=structural,
    )

    return InvalidationCycleBundle(
        symbol=phase_bundle.symbol,
        daily_bar_id=phase_bundle.daily_bar_id,
        intraday_bar_id=phase_bundle.intraday_bar_id,
        data_4h_available=phase_bundle.data_4h_available,
        structural_invalidation=structural,
        structural_invalidation_reason=structural_reason,
        timing_invalidation=timing,
        timing_invalidation_reason=timing_reason,
        new_cycle_detected=cycle.new_cycle_detected,
        cycle_reason_code=cycle.cycle_reason_code,
        resolved_setup_cycle_id=cycle.resolved_setup_cycle_id,
        phase_floor_recovered_since_cycle_end=cycle.phase_floor_recovered_since_cycle_end,
        expansion_reset_condition_met=cycle.expansion_reset_condition_met,
        reclaim_reset_condition_met=cycle.reclaim_reset_condition_met,
    )
