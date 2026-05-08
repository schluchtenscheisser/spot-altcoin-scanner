from __future__ import annotations

import math
import re
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
    "RECLAIM_RESET_UNKNOWN",
    "FIRST_CYCLE_INITIALIZED",
}
_ALLOWED_DISPOSITION_REASONS = {"PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE"}
_ALLOWED_TRANSITION_REASONS = {
    "NEW_CYCLE_RESET_TO_WATCH",
    "STRUCTURAL_INVALIDATION_REJECTED",
    "CHASED_FROM_EXPANSION",
    "CHASED_FROM_CONFIRMED_FRESHNESS",
    "CHASED_FROM_EARLY_FRESHNESS",
    "LATE_FROM_CONFIRMED_FRESHNESS",
    "LATE_FROM_EARLY_FRESHNESS",
    "LATE_FROM_CONFIRMED_LOST",
    "STATE_HOLD",
    "STATE_PROMOTED_TO_EARLY",
    "STATE_PROMOTED_TO_CONFIRMED",
    "STATE_DEMOTED_TO_WATCH",
}
_ALLOWED_RESOLUTION_CLASSES = {"full_1d_4h", "reduced_1d_4h", "daily_only"}
_DAILY_BAR_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def _validate_positive_price(field: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or float(value) <= 0:
        raise ValueError(f"{field} must be finite > 0 or None")


def _validate_finite(field: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError(f"{field} must be finite number or None")


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
    daily_bar_id: str
    intraday_bar_id: str | None
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


@dataclass(frozen=True)
class StateRuntimeContext:
    current_close: float
    current_bar_index: int
    delta_closed_bars_relevant: int

    def __post_init__(self) -> None:
        _validate_positive_price("current_close", self.current_close)
        if isinstance(self.current_bar_index, bool) or not isinstance(self.current_bar_index, int) or self.current_bar_index < 0:
            raise ValueError("current_bar_index must be non-negative int")
        if (
            isinstance(self.delta_closed_bars_relevant, bool)
            or not isinstance(self.delta_closed_bars_relevant, int)
            or self.delta_closed_bars_relevant < 0
        ):
            raise ValueError("delta_closed_bars_relevant must be non-negative int")


@dataclass(frozen=True)
class PersistedStateMachineContext:
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
    close_at_early_entry_bar: float | None
    close_at_confirmed_entry_bar: float | None
    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None
    cycle_end_bar_index: int | None
    cycle_end_timestamp: int | None
    last_aging_daily_bar_id: str | None = None

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
        _validate_positive_price("close_at_early_entry_bar", self.close_at_early_entry_bar)
        _validate_positive_price("close_at_confirmed_entry_bar", self.close_at_confirmed_entry_bar)
        _validate_finite("distance_from_ideal_entry_after_early", self.distance_from_ideal_entry_after_early)
        _validate_finite("distance_from_ideal_entry_after_confirmed", self.distance_from_ideal_entry_after_confirmed)
        _validate_non_negative_int("cycle_end_bar_index", self.cycle_end_bar_index)
        _validate_non_negative_int("cycle_end_timestamp", self.cycle_end_timestamp)
        if self.last_aging_daily_bar_id is not None and _DAILY_BAR_ID_RE.fullmatch(self.last_aging_daily_bar_id) is None:
            raise ValueError("last_aging_daily_bar_id must match YYYY-MM-DD or None")
        if self.reclaim_below_reset_floor_seen_since_cycle_end not in {True, False, None}:
            raise ValueError("reclaim_below_reset_floor_seen_since_cycle_end must be bool or None")


@dataclass(frozen=True)
class StateEvaluationDisposition:
    admitted: bool
    disposition_reason: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.admitted, bool):
            raise ValueError("admitted must be bool")
        if self.disposition_reason is not None and self.disposition_reason not in _ALLOWED_DISPOSITION_REASONS:
            raise ValueError("invalid disposition_reason")
        if (not self.admitted) and self.disposition_reason is None:
            raise ValueError("disposition_reason is required when admitted is false")


@dataclass(frozen=True)
class StateFreshnessBundle:
    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None
    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None


@dataclass(frozen=True)
class StatePersistencePatch:
    symbol: str
    setup_cycle_id: int
    previous_setup_cycle_id: int | None
    state_recorded_in_cycle_id: int
    state_machine_state: str
    state_confidence: float
    state_transition_reason: str
    bars_since_state_entered: int
    bars_since_early_entered: int | None
    bars_since_confirmed_entered: int | None
    bars_since_cycle_end: int | None
    close_at_early_entry_bar: float | None
    close_at_confirmed_entry_bar: float | None
    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None
    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None
    cycle_end_bar_index: int | None
    cycle_end_timestamp: int | None
    reclaim_below_reset_floor_seen_since_cycle_end: bool | None
    data_resolution_class: str
    last_aging_daily_bar_id: str | None = None

    def __post_init__(self) -> None:
        if self.state_machine_state not in _ALLOWED_STATES:
            raise ValueError("invalid state_machine_state")
        if self.state_transition_reason not in _ALLOWED_TRANSITION_REASONS:
            raise ValueError("invalid state_transition_reason")
        if self.data_resolution_class not in _ALLOWED_RESOLUTION_CLASSES:
            raise ValueError("invalid data_resolution_class")
        if self.last_aging_daily_bar_id is not None and _DAILY_BAR_ID_RE.fullmatch(self.last_aging_daily_bar_id) is None:
            raise ValueError("last_aging_daily_bar_id must match YYYY-MM-DD or None")


@dataclass(frozen=True)
class StateMachineBundle:
    symbol: str
    daily_bar_id: str
    intraday_bar_id: str | None
    data_4h_available: bool
    disposition: StateEvaluationDisposition
    state_machine_state: str | None
    state_confidence: float | None
    state_transition_reason: str | None
    data_resolution_class: str | None
    freshness: StateFreshnessBundle
    persistence_patch: StatePersistencePatch | None
