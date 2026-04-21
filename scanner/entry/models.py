from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

EntryPattern = Literal[
    "range_reclaim",
    "breakout",
    "break_and_hold",
    "shallow_pullback",
    "resume_reclaim",
    "continuation_breakout",
    "ema_reclaim",
    "base_reclaim",
    "early_reversal_break",
    "none",
]

AdmittedEntryPattern = Literal[
    "range_reclaim",
    "breakout",
    "break_and_hold",
    "shallow_pullback",
    "resume_reclaim",
    "continuation_breakout",
    "ema_reclaim",
    "base_reclaim",
    "early_reversal_break",
]


@dataclass(frozen=True)
class EntryPatternBundle:
    entry_pattern: EntryPattern
    entry_pattern_score: float
    candidate_pattern_scores_within_phase: dict[AdmittedEntryPattern, float]
