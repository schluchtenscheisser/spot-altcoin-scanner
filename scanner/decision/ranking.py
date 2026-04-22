from __future__ import annotations

import math

from scanner.decision.models import DecisionBucket, RankedDecision


def map_execution_grade(execution_status: str) -> float:
    mapping = {
        "direct_ok": 100.0,
        "tranche_ok": 75.0,
        "marginal": 40.0,
        "fail": 0.0,
    }
    if execution_status not in mapping:
        raise ValueError("Unknown execution_status")
    return mapping[execution_status]


def compute_priority_score(
    *,
    market_phase_confidence: float,
    state_confidence: float,
    entry_pattern_score: float,
    execution_status: str | None = None,
    execution_grade: float | None = None,
) -> float:
    _require_finite("market_phase_confidence", market_phase_confidence)
    _require_finite("state_confidence", state_confidence)
    _require_finite("entry_pattern_score", entry_pattern_score)

    if execution_status is None:
        raw = 0.35 * market_phase_confidence + 0.40 * state_confidence + 0.25 * entry_pattern_score
    else:
        grade = execution_grade
        if grade is None or not isinstance(grade, (int, float)) or isinstance(grade, bool) or not math.isfinite(float(grade)):
            grade = map_execution_grade(execution_status)
        raw = 0.30 * market_phase_confidence + 0.35 * state_confidence + 0.20 * entry_pattern_score + 0.15 * float(grade)

    return float(max(0.0, min(100.0, raw)))


def _coerce_score_input_for_non_gated_path(value: float | None) -> float:
    if value is None:
        return 0.0
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return 0.0
    return float(value)


def rank_coins(decisions: list[RankedDecision], cfg: object | None = None) -> list[RankedDecision]:
    bucket_order = {
        DecisionBucket.CONFIRMED_CANDIDATES: 0,
        DecisionBucket.EARLY_CANDIDATES: 1,
        DecisionBucket.WATCHLIST: 2,
        DecisionBucket.LATE_MONITOR: 3,
        DecisionBucket.DISCARDED: 4,
    }

    sorted_records = sorted(
        decisions,
        key=lambda rd: (
            bucket_order[rd.decision.decision_bucket],
            -rd.decision.priority_score,
            -_sort_nullable_desc(rd.state_confidence),
            -_sort_nullable_desc(rd.market_phase_confidence),
            -rd.decision.entry_pattern_score,
            rd.symbol,
        ),
    )

    ranks: dict[DecisionBucket, int] = {}
    out: list[RankedDecision] = []
    for record in sorted_records:
        bucket = record.decision.decision_bucket
        ranks[bucket] = ranks.get(bucket, 0) + 1
        out.append(
            RankedDecision(
                symbol=record.symbol,
                decision=record.decision,
                state_confidence=record.state_confidence,
                market_phase_confidence=record.market_phase_confidence,
                rank_within_bucket=ranks[bucket],
            )
        )
    return out


def _require_finite(field: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field} must be finite float")
    if not math.isfinite(float(value)):
        raise TypeError(f"{field} must be finite float")


def _sort_nullable_desc(value: float | None) -> float:
    if value is None:
        return float("-inf")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return float("-inf")
    return float(value)
