from __future__ import annotations

from dataclasses import dataclass

from scanner.axes.models import Tier1AxisBundle
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.models import PersistedStateCycleContext


@dataclass(frozen=True)
class CycleResolution:
    new_cycle_detected: bool
    cycle_reason_code: str
    resolved_setup_cycle_id: int
    phase_floor_recovered_since_cycle_end: bool
    expansion_reset_condition_met: bool | None
    reclaim_reset_condition_met: bool | None


def _phase_floor_recovered(phase_bundle: PhaseInterpretationBundle) -> bool:
    return any(
        not failed
        for failed in [
            phase_bundle.phase_floor_failed_pressure_build,
            phase_bundle.phase_floor_failed_trend_resume,
            phase_bundle.phase_floor_failed_transition_reclaim,
        ]
    )


def resolve_cycle_state(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    persisted_context: PersistedStateCycleContext,
    cycle_cfg: dict,
    structural_invalidation: bool,
) -> CycleResolution:
    reclaim_reset_enabled = bool(cycle_cfg["enable_reclaim_reset"])
    if persisted_context.current_setup_cycle_id is None:
        return CycleResolution(
            new_cycle_detected=False,
            cycle_reason_code="FIRST_CYCLE_INITIALIZED",
            resolved_setup_cycle_id=1,
            phase_floor_recovered_since_cycle_end=_phase_floor_recovered(phase_bundle),
            expansion_reset_condition_met=None,
            reclaim_reset_condition_met=None,
        )

    expansion_value = tier1_bundle.expansion_progress_structural
    expansion_reset_condition_met: bool | None
    if expansion_value is None or tier1_bundle.expansion_progress_structural_not_evaluable:
        expansion_reset_condition_met = None
    else:
        expansion_reset_condition_met = float(expansion_value) <= float(cycle_cfg["expansion_reset_max"])

    if persisted_context.bars_since_cycle_end is None:
        min_bars_met = False
    else:
        min_bars_met = int(persisted_context.bars_since_cycle_end) >= int(cycle_cfg["min_bars_since_cycle_end"])

    phase_floor_recovered = _phase_floor_recovered(phase_bundle)

    reclaim_reset_condition_met: bool | None = None
    if reclaim_reset_enabled:
        flag = persisted_context.reclaim_below_reset_floor_seen_since_cycle_end
        reclaim_reset_condition_met = bool(flag) if flag is not None else None

    z1 = expansion_reset_condition_met is True
    z2 = min_bars_met
    z3 = phase_floor_recovered
    z4 = not structural_invalidation
    z5 = reclaim_reset_condition_met is True if reclaim_reset_enabled else True

    if z1 and z2 and z3 and z4 and z5:
        prev = persisted_context.prev_state_machine_state
        if prev == "rejected":
            reason = "NEW_CYCLE_AFTER_REJECTION"
        elif prev == "chased":
            reason = "NEW_CYCLE_AFTER_CHASED"
        else:
            reason = "NEW_CYCLE_AFTER_RESET"
        return CycleResolution(
            new_cycle_detected=True,
            cycle_reason_code=reason,
            resolved_setup_cycle_id=persisted_context.current_setup_cycle_id + 1,
            phase_floor_recovered_since_cycle_end=phase_floor_recovered,
            expansion_reset_condition_met=expansion_reset_condition_met,
            reclaim_reset_condition_met=reclaim_reset_condition_met,
        )

    if structural_invalidation:
        reason = "NEW_CYCLE_BLOCKED_STRUCTURAL_INVALIDATION_ACTIVE"
    elif persisted_context.bars_since_cycle_end is None:
        reason = "NEW_CYCLE_BLOCKED_NO_PRIOR_ENDED_CYCLE"
    elif expansion_reset_condition_met is False:
        reason = "NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET"
    elif not z2:
        reason = "NEW_CYCLE_BLOCKED_MIN_BARS_NOT_MET"
    elif not z3:
        reason = "NEW_CYCLE_BLOCKED_PHASE_FLOOR_NOT_RECOVERED"
    elif reclaim_reset_enabled and reclaim_reset_condition_met is None:
        reason = "RECLAIM_RESET_UNKNOWN"
    elif reclaim_reset_enabled and reclaim_reset_condition_met is False:
        reason = "NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET"
    else:
        reason = "NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET"

    return CycleResolution(
        new_cycle_detected=False,
        cycle_reason_code=reason,
        resolved_setup_cycle_id=persisted_context.current_setup_cycle_id,
        phase_floor_recovered_since_cycle_end=phase_floor_recovered,
        expansion_reset_condition_met=expansion_reset_condition_met,
        reclaim_reset_condition_met=reclaim_reset_condition_met,
    )
