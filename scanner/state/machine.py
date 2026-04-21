from __future__ import annotations

from scanner.axes.models import Tier1AxisBundle, Tier2AxisBundle
from scanner.config import ScannerConfig
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.freshness import compute_state_freshness
from scanner.state.models import (
    InvalidationCycleBundle,
    PersistedStateMachineContext,
    StateEvaluationDisposition,
    StateMachineBundle,
    StatePersistencePatch,
    StateRuntimeContext,
)


def _require(field: str, phase: PhaseInterpretationBundle, t1: Tier1AxisBundle, t2: Tier2AxisBundle, inv: InvalidationCycleBundle) -> None:
    base = getattr(phase, field)
    if base != getattr(t1, field) or base != getattr(t2, field) or base != getattr(inv, field):
        raise ValueError(f"bundle mismatch for {field}")


def _derive_data_resolution_class(
    state: str,
    phase: PhaseInterpretationBundle,
    t1: Tier1AxisBundle,
    t2: Tier2AxisBundle,
) -> str:
    if not phase.data_4h_available:
        return "daily_only"
    reduced_flags = [phase.freshness_distance_structural_reduced_resolution]
    if state in {"early_ready", "watch"}:
        reduced_flags.extend([t1.compression_strength_reduced_resolution, t1.volume_regime_shift_reduced_resolution])
    if state in {"confirmed_ready", "late", "chased"}:
        reduced_flags.extend([t1.reclaim_progress_reduced_resolution, t1.trend_strength_reduced_resolution])
    if state in {"early_ready", "confirmed_ready"}:
        reduced_flags.append(t2.reacceleration_strength_simplified_reduced_resolution)
    return "reduced_1d_4h" if any(bool(v) for v in reduced_flags) else "full_1d_4h"


def compute_state_machine(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    invalidation_cycle_bundle: InvalidationCycleBundle,
    persisted_context: PersistedStateMachineContext,
    runtime_context: StateRuntimeContext,
    cfg: ScannerConfig,
) -> StateMachineBundle:
    for value, expected, name in [
        (phase_bundle, PhaseInterpretationBundle, "phase_bundle"),
        (tier1_bundle, Tier1AxisBundle, "tier1_bundle"),
        (tier2_bundle, Tier2AxisBundle, "tier2_bundle"),
        (invalidation_cycle_bundle, InvalidationCycleBundle, "invalidation_cycle_bundle"),
        (persisted_context, PersistedStateMachineContext, "persisted_context"),
        (runtime_context, StateRuntimeContext, "runtime_context"),
        (cfg, ScannerConfig, "cfg"),
    ]:
        if not isinstance(value, expected):
            raise TypeError(f"{name} must be {expected.__name__}")

    for field in ["symbol", "daily_bar_id", "intraday_bar_id", "data_4h_available"]:
        _require(field, phase_bundle, tier1_bundle, tier2_bundle, invalidation_cycle_bundle)
    if persisted_context.symbol != phase_bundle.symbol:
        raise ValueError("bundle mismatch for symbol")

    prior_active = persisted_context.prev_state_machine_state in {"watch", "early_ready", "confirmed_ready", "late"}
    in_current_cycle = (
        persisted_context.current_setup_cycle_id is not None
        and persisted_context.state_recorded_in_cycle_id == persisted_context.current_setup_cycle_id
    )
    if phase_bundle.market_phase == "none" and not (prior_active and in_current_cycle):
        disposition = StateEvaluationDisposition(False, "PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE")
        freshness = compute_state_freshness(invalidation_cycle_bundle, persisted_context, runtime_context, cfg)
        return StateMachineBundle(
            symbol=phase_bundle.symbol,
            daily_bar_id=phase_bundle.daily_bar_id,
            intraday_bar_id=phase_bundle.intraday_bar_id,
            data_4h_available=phase_bundle.data_4h_available,
            disposition=disposition,
            state_machine_state=None,
            state_confidence=None,
            state_transition_reason=None,
            data_resolution_class=None,
            freshness=freshness,
            persistence_patch=None,
        )

    freshness = compute_state_freshness(invalidation_cycle_bundle, persisted_context, runtime_context, cfg)
    prev_state = persisted_context.prev_state_machine_state or "watch"

    if invalidation_cycle_bundle.new_cycle_detected:
        state = "watch"
        reason = "NEW_CYCLE_RESET_TO_WATCH"
    elif invalidation_cycle_bundle.structural_invalidation:
        state = "rejected"
        reason = "STRUCTURAL_INVALIDATION_REJECTED"
    else:
        state = prev_state
        reason = "STATE_HOLD"
        early_ok = (
            phase_bundle.market_phase in {"pressure_build", "trend_resume", "transition_reclaim"}
            and (tier1_bundle.compression_strength or 0) >= cfg.state["early"]["pressure_build"]["min_compression"]
            and (tier1_bundle.volume_regime_shift or 0) >= cfg.state["early"]["pressure_build"]["min_volume_shift"]
        )
        confirmed_ok = (
            phase_bundle.market_phase in {"trend_resume", "transition_reclaim"}
            and (tier1_bundle.reclaim_progress or 0) >= cfg.state["confirmed"]["trend_resume"]["min_reclaim"]
            and (tier1_bundle.trend_strength or 0) >= cfg.state["confirmed"]["trend_resume"]["min_trend"]
        )
        if phase_bundle.market_phase == "pressure_build" and not phase_bundle.data_4h_available:
            confirmed_ok = False
        if confirmed_ok and prev_state not in {"late", "chased", "rejected"}:
            state = "confirmed_ready"
            reason = "STATE_PROMOTED_TO_CONFIRMED"
        elif early_ok and prev_state not in {"chased", "rejected"}:
            state = "early_ready"
            reason = "STATE_PROMOTED_TO_EARLY"
        elif prev_state in {"early_ready", "confirmed_ready"}:
            state = "watch"
            reason = "STATE_DEMOTED_TO_WATCH"

    if state != "rejected":
        if (tier1_bundle.expansion_progress_structural or 0) >= cfg.state["chased"]["min_expansion_progress"]:
            state = "chased"
            reason = "CHASED_FROM_EXPANSION"
        elif freshness.freshness_distance_state_confirmed is not None and freshness.freshness_distance_state_confirmed >= cfg.state["chased"]["min_state_freshness"]:
            state = "chased"
            reason = "CHASED_FROM_CONFIRMED_FRESHNESS"
        elif freshness.freshness_distance_state_early is not None and freshness.freshness_distance_state_early >= cfg.state["chased"]["min_state_freshness"]:
            state = "chased"
            reason = "CHASED_FROM_EARLY_FRESHNESS"
        elif freshness.freshness_distance_state_confirmed is not None and freshness.freshness_distance_state_confirmed >= cfg.state["late"]["min_state_freshness"]:
            state = "late"
            reason = "LATE_FROM_CONFIRMED_FRESHNESS"
        elif freshness.freshness_distance_state_early is not None and freshness.freshness_distance_state_early >= cfg.state["late"]["min_state_freshness"]:
            state = "late"
            reason = "LATE_FROM_EARLY_FRESHNESS"

    if prev_state == "chased" and not invalidation_cycle_bundle.new_cycle_detected:
        state = "chased"
    if prev_state == "rejected" and not invalidation_cycle_bundle.new_cycle_detected:
        state = "rejected"

    delta = runtime_context.delta_closed_bars_relevant
    bars_since_state_entered = 0 if state != prev_state else (persisted_context.bars_since_state_entered or 0) + delta

    close_early = persisted_context.close_at_early_entry_bar
    bars_early = persisted_context.bars_since_early_entered
    if invalidation_cycle_bundle.new_cycle_detected:
        close_early = None
        bars_early = None
    elif close_early is None and state == "early_ready":
        close_early = runtime_context.current_close
        bars_early = 0
    elif bars_early is not None:
        bars_early += delta

    close_confirmed = persisted_context.close_at_confirmed_entry_bar
    bars_confirmed = persisted_context.bars_since_confirmed_entered
    if invalidation_cycle_bundle.new_cycle_detected:
        close_confirmed = None
        bars_confirmed = None
    elif close_confirmed is None and state == "confirmed_ready":
        close_confirmed = runtime_context.current_close
        bars_confirmed = 0
    elif bars_confirmed is not None:
        bars_confirmed += delta

    cycle_end_bar_index = persisted_context.cycle_end_bar_index
    cycle_end_timestamp = persisted_context.cycle_end_timestamp
    if invalidation_cycle_bundle.new_cycle_detected:
        bars_since_cycle_end = None
        cycle_end_bar_index = None
        cycle_end_timestamp = None
    elif state in {"rejected", "chased"} and prev_state not in {"rejected", "chased"}:
        bars_since_cycle_end = 0
        cycle_end_bar_index = runtime_context.current_bar_index
        cycle_end_timestamp = phase_bundle.intraday_bar_id if phase_bundle.intraday_bar_id is not None else phase_bundle.daily_bar_id
    elif persisted_context.bars_since_cycle_end is not None:
        bars_since_cycle_end = persisted_context.bars_since_cycle_end + delta
    else:
        bars_since_cycle_end = None

    confidence = float(phase_bundle.market_phase_confidence)
    if phase_bundle.market_phase_blended:
        confidence -= float(cfg.state["confidence"]["blended_penalty"])
    data_resolution_class = _derive_data_resolution_class(state, phase_bundle, tier1_bundle, tier2_bundle)
    if data_resolution_class != "full_1d_4h":
        confidence -= float(cfg.state["confidence"]["not_full_resolution_penalty"])
    confidence = max(0.0, min(100.0, confidence))

    patch = StatePersistencePatch(
        symbol=phase_bundle.symbol,
        setup_cycle_id=invalidation_cycle_bundle.resolved_setup_cycle_id,
        previous_setup_cycle_id=(persisted_context.current_setup_cycle_id if invalidation_cycle_bundle.new_cycle_detected else persisted_context.previous_setup_cycle_id),
        state_recorded_in_cycle_id=invalidation_cycle_bundle.resolved_setup_cycle_id,
        state_machine_state=state,
        state_confidence=confidence,
        state_transition_reason=reason,
        bars_since_state_entered=bars_since_state_entered,
        bars_since_early_entered=bars_early,
        bars_since_confirmed_entered=bars_confirmed,
        bars_since_cycle_end=bars_since_cycle_end,
        close_at_early_entry_bar=close_early,
        close_at_confirmed_entry_bar=close_confirmed,
        distance_from_ideal_entry_after_early=freshness.distance_from_ideal_entry_after_early,
        distance_from_ideal_entry_after_confirmed=freshness.distance_from_ideal_entry_after_confirmed,
        freshness_distance_state_early=freshness.freshness_distance_state_early,
        freshness_distance_state_confirmed=freshness.freshness_distance_state_confirmed,
        cycle_end_bar_index=cycle_end_bar_index,
        cycle_end_timestamp=cycle_end_timestamp,
        reclaim_below_reset_floor_seen_since_cycle_end=persisted_context.reclaim_below_reset_floor_seen_since_cycle_end,
        data_resolution_class=data_resolution_class,
    )

    return StateMachineBundle(
        symbol=phase_bundle.symbol,
        daily_bar_id=phase_bundle.daily_bar_id,
        intraday_bar_id=phase_bundle.intraday_bar_id,
        data_4h_available=phase_bundle.data_4h_available,
        disposition=StateEvaluationDisposition(True, None),
        state_machine_state=state,
        state_confidence=confidence,
        state_transition_reason=reason,
        data_resolution_class=data_resolution_class,
        freshness=freshness,
        persistence_patch=patch,
    )
