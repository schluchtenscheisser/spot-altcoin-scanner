from __future__ import annotations

from scanner.decision.models import (
    ConfirmedReason,
    DecisionBucket,
    DiscardedReason,
    EarlyReason,
    LateMonitorReason,
    ReasonAssignment,
    WatchlistReason,
)


def assign_reasons(
    *,
    decision_bucket: DecisionBucket,
    state_machine_state: str,
    entry_pattern: str,
    execution_status: str | None,
) -> ReasonAssignment:
    if decision_bucket is DecisionBucket.WATCHLIST:
        if state_machine_state == "watch":
            return ReasonAssignment(
                primary=WatchlistReason.WATCH_STATE_VALID,
                secondary=WatchlistReason.WATCH_WAITING_FOR_PROMOTION,
            )
        if state_machine_state == "early_ready" and entry_pattern == "none":
            return ReasonAssignment(primary=WatchlistReason.WATCH_EARLY_NO_PATTERN)

    if decision_bucket is DecisionBucket.EARLY_CANDIDATES:
        if execution_status is None:
            return ReasonAssignment(
                primary=EarlyReason.EARLY_EXECUTION_PENDING,
                secondary=EarlyReason.EARLY_PATTERN_VALID,
            )
        return ReasonAssignment(
            primary=EarlyReason.EARLY_EXECUTION_OK,
            secondary=EarlyReason.EARLY_PATTERN_VALID,
        )

    if decision_bucket is DecisionBucket.CONFIRMED_CANDIDATES:
        if execution_status is None:
            return ReasonAssignment(
                primary=ConfirmedReason.CONFIRMED_EXECUTION_PENDING,
                secondary=ConfirmedReason.CONFIRMED_PATTERN_VALID,
            )
        return ReasonAssignment(
            primary=ConfirmedReason.CONFIRMED_EXECUTION_OK,
            secondary=ConfirmedReason.CONFIRMED_PATTERN_VALID,
        )

    if decision_bucket is DecisionBucket.LATE_MONITOR:
        if state_machine_state == "confirmed_ready" and entry_pattern == "none":
            return ReasonAssignment(primary=LateMonitorReason.CONFIRMED_PATTERN_UNRESOLVED)
        if state_machine_state == "confirmed_ready" and execution_status == "fail":
            return ReasonAssignment(primary=LateMonitorReason.EXECUTION_FAILED_MONITOR)
        if state_machine_state == "late":
            return ReasonAssignment(primary=LateMonitorReason.LATE_STATE)
        if state_machine_state == "chased":
            return ReasonAssignment(primary=LateMonitorReason.CHASED_STATE)

    if decision_bucket is DecisionBucket.DISCARDED:
        if execution_status == "fail" and state_machine_state == "early_ready" and entry_pattern != "none":
            return ReasonAssignment(primary=DiscardedReason.EXECUTION_FAILED)

    raise ValueError("No deterministic reason assignment found for path")
