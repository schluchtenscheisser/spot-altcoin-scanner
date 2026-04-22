from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from scanner.entry.models import EntryPattern


class DecisionBucket(str, Enum):
    WATCHLIST = "watchlist"
    EARLY_CANDIDATES = "early_candidates"
    CONFIRMED_CANDIDATES = "confirmed_candidates"
    LATE_MONITOR = "late_monitor"
    DISCARDED = "discarded"


class WatchlistReason(str, Enum):
    WATCH_PHASE_VALID = "WATCH_PHASE_VALID"
    WATCH_STATE_VALID = "WATCH_STATE_VALID"
    WATCH_WAITING_FOR_PROMOTION = "WATCH_WAITING_FOR_PROMOTION"
    WATCH_EARLY_NO_PATTERN = "WATCH_EARLY_NO_PATTERN"


class EarlyReason(str, Enum):
    EARLY_STATE_VALID = "EARLY_STATE_VALID"
    EARLY_PATTERN_VALID = "EARLY_PATTERN_VALID"
    EARLY_EXECUTION_OK = "EARLY_EXECUTION_OK"
    EARLY_EXECUTION_PENDING = "EARLY_EXECUTION_PENDING"


class ConfirmedReason(str, Enum):
    CONFIRMED_STATE_VALID = "CONFIRMED_STATE_VALID"
    CONFIRMED_PATTERN_VALID = "CONFIRMED_PATTERN_VALID"
    CONFIRMED_EXECUTION_OK = "CONFIRMED_EXECUTION_OK"
    CONFIRMED_EXECUTION_PENDING = "CONFIRMED_EXECUTION_PENDING"


class LateMonitorReason(str, Enum):
    LATE_STATE = "LATE_STATE"
    CHASED_STATE = "CHASED_STATE"
    EXECUTION_FAILED_MONITOR = "EXECUTION_FAILED_MONITOR"
    FORMER_CANDIDATE_STALE = "FORMER_CANDIDATE_STALE"
    CONFIRMED_PATTERN_UNRESOLVED = "CONFIRMED_PATTERN_UNRESOLVED"


class DiscardedReason(str, Enum):
    STATE_REJECTED = "STATE_REJECTED"
    PHASE_NONE = "PHASE_NONE"
    PATTERN_NONE_CONFIRMED = "PATTERN_NONE_CONFIRMED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INSUFFICIENT_CONFIDENCE = "INSUFFICIENT_CONFIDENCE"


ReasonCode = WatchlistReason | EarlyReason | ConfirmedReason | LateMonitorReason | DiscardedReason


@dataclass(frozen=True)
class ExecutionInputContract:
    execution_status: str
    execution_grade: float | None = None
    execution_pass: bool | None = None
    execution_reason: str | None = None

    def __post_init__(self) -> None:
        allowed = {"direct_ok", "tranche_ok", "marginal", "fail"}
        if self.execution_status not in allowed:
            raise ValueError("execution_status has invalid enum value")
        if self.execution_grade is not None:
            if isinstance(self.execution_grade, bool) or not isinstance(self.execution_grade, (int, float)):
                raise ValueError("execution_grade must be finite number or None")
            if not math.isfinite(float(self.execution_grade)):
                raise ValueError("execution_grade must be finite number or None")


@dataclass(frozen=True)
class ReasonAssignment:
    primary: ReasonCode
    secondary: ReasonCode | None = None


@dataclass(frozen=True)
class DecisionBundle:
    decision_bucket: DecisionBucket
    priority_score: float
    bucket_reason_primary: ReasonCode
    bucket_reason_secondary: ReasonCode | None
    execution_required: bool
    execution_pending: bool
    entry_pattern: EntryPattern
    entry_pattern_score: float

    def __post_init__(self) -> None:
        if not isinstance(self.priority_score, (int, float)) or isinstance(self.priority_score, bool):
            raise ValueError("priority_score must be finite float in [0,100]")
        if not math.isfinite(float(self.priority_score)):
            raise ValueError("priority_score must be finite float in [0,100]")
        if float(self.priority_score) < 0.0 or float(self.priority_score) > 100.0:
            raise ValueError("priority_score must be finite float in [0,100]")
        if self.execution_pending and not self.execution_required:
            raise ValueError("execution_pending=True requires execution_required=True")


@dataclass(frozen=True)
class RankedDecision:
    symbol: str
    decision: DecisionBundle
    state_confidence: float | None
    market_phase_confidence: float | None
    rank_within_bucket: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be non-empty str")
