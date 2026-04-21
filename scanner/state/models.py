from __future__ import annotations

import math
from dataclasses import dataclass

_ALLOWED_STATES = {"watch", "early_ready", "confirmed_ready", "late", "chased", "rejected"}
_ALLOWED_STRUCTURAL_REASONS = {
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
}
_ALLOWED_TIMING_REASONS = {
    "STATE_FRESHNESS_EARLY_MAXED",
    "STATE_FRESHNESS_CONFIRMED_MAXED",
    "EXPANSION_PROGRESS_MAXED",
    "STRUCTURAL_FRESHNESS_MAXED",
}
_ALLOWED_CYCLE_CODES = {
    "NEW_CYCLE_AFTER_RESET",
    "NEW_CYCLE_AFTER_REJECTION",
    "NEW_CYCLE_AFTER_CHASED",
    "NEW_CYCLE_BLOCKED_NO_PRIOR_ENDED_CYCLE",
    "NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET",
    "NEW_CYCLE_BLOCKED_MIN_BARS_NOT_MET",
    "NEW_CYCLE_BLOCKED_PHASE_FLOOR_NOT_RECOVERED",
    "NEW_CYCLE_BLOCKED_STRUCTURAL_INVALIDATION_ACTIVE",
    "NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET",
    "FIRST_CYCLE_INITIALIZED",
}


def _is_finite_0_100(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)) and 0.0 <= float(value) <= 100.0


def _validate_cycle_id(field: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{field} must be positive int or None")


def _validate_non_negative_int(field: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be non-negative int or None")


@dataclass(frozen=True)
class PersistedStateCycleContext:
    symbol: str

    current_setup_cycle_id: int | None
    previous_setup_cycle_id: int | None
    state_recorded_in_cycle_id: int | None

    prev_state_machine_state: str | None

    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None

    bars_since_state_entered: int | None
    bars_since_early_entered: int | None
    bars_since_confirmed_entered: int | None
    bars_since_cycle_end: int | None

    reclaim_below_reset_floor_seen_since_cycle_end: bool | None

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be non-empty str")

        _validate_cycle_id("current_setup_cycle_id", self.current_setup_cycle_id)
        _validate_cycle_id("previous_setup_cycle_id", self.previous_setup_cycle_id)
        _validate_cycle_id("state_recorded_in_cycle_id", self.state_recorded_in_cycle_id)

        if self.prev_state_machine_state is not None and self.prev_state_machine_state not in _ALLOWED_STATES:
            raise ValueError("prev_state_machine_state has invalid enum value")

        for field in ["freshness_distance_state_early", "freshness_distance_state_confirmed"]:
            value = getattr(self, field)
            if value is not None and not _is_finite_0_100(value):
                raise ValueError(f"{field} must be finite and in [0,100] or None")

        _validate_non_negative_int("bars_since_state_entered", self.bars_since_state_entered)
        _validate_non_negative_int("bars_since_early_entered", self.bars_since_early_entered)
        _validate_non_negative_int("bars_since_confirmed_entered", self.bars_since_confirmed_entered)
        _validate_non_negative_int("bars_since_cycle_end", self.bars_since_cycle_end)

        if self.reclaim_below_reset_floor_seen_since_cycle_end not in {True, False, None}:
            raise ValueError("reclaim_below_reset_floor_seen_since_cycle_end must be bool or None")

        bootstrap_none = self.current_setup_cycle_id is None
        non_bootstrap_fields_present = any(
            value is not None
            for value in [
                self.previous_setup_cycle_id,
                self.state_recorded_in_cycle_id,
                self.prev_state_machine_state,
                self.freshness_distance_state_early,
                self.freshness_distance_state_confirmed,
                self.bars_since_cycle_end,
            ]
        )
        if bootstrap_none and non_bootstrap_fields_present:
            raise ValueError("current_setup_cycle_id=None is only allowed for bootstrap context")


@dataclass(frozen=True)
class InvalidationCycleBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    structural_invalidation: bool
    structural_invalidation_reason: str | None

    timing_invalidation: bool
    timing_invalidation_reason: str | None

    new_cycle_detected: bool
    cycle_reason_code: str

    resolved_setup_cycle_id: int

    phase_floor_recovered_since_cycle_end: bool
    expansion_reset_condition_met: bool | None
    reclaim_reset_condition_met: bool | None

    def __post_init__(self) -> None:
        if self.structural_invalidation:
            if self.structural_invalidation_reason not in _ALLOWED_STRUCTURAL_REASONS:
                raise ValueError("invalid structural_invalidation_reason")
            if self.timing_invalidation:
                raise ValueError("timing_invalidation must be false when structural_invalidation is true")
            if self.timing_invalidation_reason is not None:
                raise ValueError("timing_invalidation_reason must be None when structural_invalidation is true")
        else:
            if self.structural_invalidation_reason is not None:
                raise ValueError("structural_invalidation_reason must be None when structural_invalidation is false")

        if self.timing_invalidation:
            if self.timing_invalidation_reason not in _ALLOWED_TIMING_REASONS:
                raise ValueError("invalid timing_invalidation_reason")
        else:
            if self.timing_invalidation_reason is not None:
                raise ValueError("timing_invalidation_reason must be None when timing_invalidation is false")

        if self.new_cycle_detected and self.structural_invalidation:
            raise ValueError("new_cycle_detected and structural_invalidation cannot both be true")

        if self.cycle_reason_code not in _ALLOWED_CYCLE_CODES:
            raise ValueError("invalid cycle_reason_code")
        if isinstance(self.resolved_setup_cycle_id, bool) or not isinstance(self.resolved_setup_cycle_id, int) or self.resolved_setup_cycle_id <= 0:
            raise ValueError("resolved_setup_cycle_id must be positive int")
