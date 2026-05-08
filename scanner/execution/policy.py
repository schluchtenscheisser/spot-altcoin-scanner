from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Any


TRADEABLE_SIZE_CLASSES = {"full", "reduced_75", "reduced_50", "reduced_25"}
TRADEABLE_STATUSES = {"direct_ok", "tranche_ok", "marginal"}
TOP_TRADEABLE_BUCKETS = {"confirmed_candidates", "early_candidates"}


@dataclass(frozen=True)
class ExecutionSizePolicyResult:
    execution_size_class: str
    recommended_position_factor: float | None
    execution_grade_effective: float | None


def finite_float_or_none(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    parsed = float(value)
    return parsed if isfinite(parsed) else None


def depth_ratio_band(available_depth_ratio: float | None) -> str:
    ratio = finite_float_or_none(available_depth_ratio)
    if ratio is None:
        return "not_evaluable"
    if ratio >= 1.0:
        return "full"
    if ratio >= 0.75:
        return "reduced_75"
    if ratio >= 0.5:
        return "reduced_50"
    if ratio >= 0.25:
        return "reduced_25"
    return "below_min"


def classify_execution_size(
    *,
    execution_attempted: bool,
    execution_status_raw: str | None,
    depth_ratio_band_value: str | None,
) -> ExecutionSizePolicyResult:
    if execution_attempted is False:
        return ExecutionSizePolicyResult("not_evaluated", None, None)

    if execution_status_raw == "direct_ok":
        return ExecutionSizePolicyResult("full", 1.0, 100.0)
    if execution_status_raw == "tranche_ok":
        return ExecutionSizePolicyResult("full", 1.0, 75.0)
    if execution_status_raw == "fail":
        return ExecutionSizePolicyResult("blocked", 0.0, 0.0)
    if execution_status_raw == "unknown":
        return ExecutionSizePolicyResult("not_evaluable", None, None)

    if execution_status_raw == "marginal":
        band = depth_ratio_band_value
        if band == "full":
            return ExecutionSizePolicyResult("full", 1.0, 75.0)
        if band == "reduced_75":
            return ExecutionSizePolicyResult("reduced_75", 0.75, 75.0)
        if band == "reduced_50":
            return ExecutionSizePolicyResult("reduced_50", 0.5, 60.0)
        if band == "reduced_25":
            return ExecutionSizePolicyResult("reduced_25", 0.25, 40.0)
        if band == "below_min":
            return ExecutionSizePolicyResult("observe_only", 0.0, 0.0)
        return ExecutionSizePolicyResult("not_evaluable", None, None)

    return ExecutionSizePolicyResult("not_evaluable", None, None)


def is_reduced_size_eligible(
    *,
    execution_status_raw: str | None,
    execution_size_class: str | None,
    execution_reason_raw: str | None = None,
) -> bool:
    if execution_status_raw not in TRADEABLE_STATUSES:
        return False
    if execution_size_class not in TRADEABLE_SIZE_CLASSES:
        return False
    reason = str(execution_reason_raw or "").lower()
    if "spread" in reason or "slippage" in reason:
        return False
    return True


def is_tradeable_candidate(*, decision_bucket: str | None, is_reduced_size_eligible_value: bool) -> bool:
    return decision_bucket in TOP_TRADEABLE_BUCKETS and bool(is_reduced_size_eligible_value)
