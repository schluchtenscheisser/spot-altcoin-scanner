from __future__ import annotations

from scanner.decision.models import DecisionBucket, DecisionBundle, DiscardedReason, ExecutionInputContract
from scanner.decision.ranking import _coerce_score_input_for_non_gated_path, compute_priority_score
from scanner.decision.reasons import assign_reasons
from scanner.entry.models import EntryPatternBundle
from scanner.phase.models import PhaseInterpretationBundle
from scanner.state.models import StateMachineBundle


def assign_bucket(
    phase_bundle: PhaseInterpretationBundle,
    state_bundle: StateMachineBundle,
    entry_bundle: EntryPatternBundle,
    cfg,
    execution_contract: ExecutionInputContract | None = None,
) -> DecisionBundle:
    state = state_bundle.state_machine_state
    if state is None:
        return _make_discarded(
            reason=DiscardedReason.INSUFFICIENT_CONFIDENCE,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    if phase_bundle.market_phase == "none":
        return _make_discarded(
            reason=DiscardedReason.PHASE_NONE,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )
    if state == "rejected":
        return _make_discarded(
            reason=DiscardedReason.STATE_REJECTED,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    sc = state_bundle.state_confidence
    confirmed_gate = _is_finite(sc) and float(sc) >= float(cfg.bucket["confirmed"]["min_state_confidence"])
    early_gate = _is_finite(sc) and float(sc) >= float(cfg.bucket["early"]["min_state_confidence"])
    watch_gate = _is_finite(sc) and float(sc) >= float(cfg.bucket["watchlist"]["min_state_confidence"])

    execution_status = execution_contract.execution_status if execution_contract else None

    if state == "confirmed_ready" and entry_bundle.entry_pattern != "none" and confirmed_gate and execution_status != "fail":
        return _build(
            decision_bucket=DecisionBucket.CONFIRMED_CANDIDATES,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
        )

    if state == "confirmed_ready" and entry_bundle.entry_pattern == "none":
        return _build(
            decision_bucket=DecisionBucket.LATE_MONITOR,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    if state == "confirmed_ready" and entry_bundle.entry_pattern != "none" and execution_status == "fail":
        return _build(
            decision_bucket=DecisionBucket.LATE_MONITOR,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    if state == "early_ready" and entry_bundle.entry_pattern != "none" and early_gate and execution_status != "fail":
        return _build(
            decision_bucket=DecisionBucket.EARLY_CANDIDATES,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
        )

    if state == "early_ready" and entry_bundle.entry_pattern == "none":
        return _build(
            decision_bucket=DecisionBucket.WATCHLIST,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
            early_none_penalty=float(cfg.priority["early_without_pattern_penalty"]),
        )

    if state == "early_ready" and entry_bundle.entry_pattern != "none" and execution_status == "fail":
        return _make_discarded(
            reason=DiscardedReason.EXECUTION_FAILED,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    if state == "watch" and watch_gate:
        return _build(
            decision_bucket=DecisionBucket.WATCHLIST,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
        )

    if state in {"late", "chased"} and phase_bundle.market_phase != "none":
        return _build(
            decision_bucket=DecisionBucket.LATE_MONITOR,
            phase_bundle=phase_bundle,
            state_bundle=state_bundle,
            entry_bundle=entry_bundle,
            execution_contract=execution_contract,
            non_gated=True,
        )

    return _make_discarded(
        reason=DiscardedReason.INSUFFICIENT_CONFIDENCE,
        phase_bundle=phase_bundle,
        state_bundle=state_bundle,
        entry_bundle=entry_bundle,
        execution_contract=execution_contract,
        non_gated=True,
    )


def _build(
    *,
    decision_bucket: DecisionBucket,
    phase_bundle: PhaseInterpretationBundle,
    state_bundle: StateMachineBundle,
    entry_bundle: EntryPatternBundle,
    execution_contract: ExecutionInputContract | None,
    non_gated: bool = False,
    early_none_penalty: float = 0.0,
) -> DecisionBundle:
    mpc = _coerce_market_phase_confidence_for_rankability(phase_bundle.market_phase_confidence)
    if non_gated:
        sc = _coerce_score_input_for_non_gated_path(state_bundle.state_confidence)
    else:
        sc = float(state_bundle.state_confidence)

    priority = compute_priority_score(
        market_phase_confidence=mpc,
        state_confidence=sc,
        entry_pattern_score=float(entry_bundle.entry_pattern_score),
        execution_status=execution_contract.execution_status if execution_contract else None,
        execution_grade=execution_contract.execution_grade if execution_contract else None,
    )
    if early_none_penalty:
        priority = max(0.0, priority - early_none_penalty)

    execution_required = decision_bucket in {DecisionBucket.EARLY_CANDIDATES, DecisionBucket.CONFIRMED_CANDIDATES}
    execution_pending = execution_required and execution_contract is None
    reasons = assign_reasons(
        decision_bucket=decision_bucket,
        state_machine_state=str(state_bundle.state_machine_state),
        entry_pattern=entry_bundle.entry_pattern,
        execution_status=execution_contract.execution_status if execution_contract else None,
    )
    return DecisionBundle(
        decision_bucket=decision_bucket,
        priority_score=priority,
        bucket_reason_primary=reasons.primary,
        bucket_reason_secondary=reasons.secondary,
        execution_required=execution_required,
        execution_pending=execution_pending,
        entry_pattern=entry_bundle.entry_pattern,
        entry_pattern_score=float(entry_bundle.entry_pattern_score),
    )


def _make_discarded(
    *,
    reason: DiscardedReason,
    phase_bundle: PhaseInterpretationBundle,
    state_bundle: StateMachineBundle,
    entry_bundle: EntryPatternBundle,
    execution_contract: ExecutionInputContract | None,
    non_gated: bool = False,
) -> DecisionBundle:
    mpc = _coerce_market_phase_confidence_for_rankability(phase_bundle.market_phase_confidence)
    if non_gated:
        sc = _coerce_score_input_for_non_gated_path(state_bundle.state_confidence)
    else:
        sc = float(state_bundle.state_confidence)

    priority = compute_priority_score(
        market_phase_confidence=mpc,
        state_confidence=sc,
        entry_pattern_score=float(entry_bundle.entry_pattern_score),
        execution_status=execution_contract.execution_status if execution_contract else None,
        execution_grade=execution_contract.execution_grade if execution_contract else None,
    )
    return DecisionBundle(
        decision_bucket=DecisionBucket.DISCARDED,
        priority_score=priority,
        bucket_reason_primary=reason,
        bucket_reason_secondary=None,
        execution_required=False,
        execution_pending=False,
        entry_pattern=entry_bundle.entry_pattern,
        entry_pattern_score=float(entry_bundle.entry_pattern_score),
    )


def _is_finite(value: float | None) -> bool:
    if value is None:
        return False
    try:
        x = float(value)
    except (TypeError, ValueError):
        return False
    return x == x and x not in {float("inf"), float("-inf")}


def _coerce_market_phase_confidence_for_rankability(value: float | None) -> float:
    """
    Narrow Ticket-12 floor policy:
    market_phase_confidence can be nullable/non-finite by contract and must stay rankable.
    """
    return _coerce_score_input_for_non_gated_path(value)
