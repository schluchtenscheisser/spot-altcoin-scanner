from __future__ import annotations

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from math import isfinite
from typing import Any


TRADEABLE_SIZE_CLASSES = {"full", "reduced_75", "reduced_50", "reduced_25"}
TRADEABLE_STATUSES = {"direct_ok", "tranche_ok", "marginal"}
TOP_TRADEABLE_BUCKETS = {"confirmed_candidates", "early_candidates"}

ALLOWED_REDUCED_SIZE_CAPACITY_REASON_KEYS = {
    "depth_1pct_insufficient",
    # Current tradeability metrics add this when tranche feasibility fails.
    # It is only accepted together with explicit clean spread/slippage gates;
    # spread/slippage reason keys still block eligibility.
    "tranche_execution_not_feasible",
}


def _normalize_reason_keys(reason_keys: Collection[str] | None) -> set[str] | None:
    if reason_keys is None:
        return None
    normalized: set[str] = set()
    for reason in reason_keys:
        if reason is None:
            continue
        value = str(reason).strip().lower()
        if value:
            normalized.add(value)
    return normalized


def has_non_depth_blocking_reason(reason_keys: Collection[str]) -> bool:
    normalized = _normalize_reason_keys(reason_keys)
    if normalized is None or not normalized:
        return False
    return any(reason not in ALLOWED_REDUCED_SIZE_CAPACITY_REASON_KEYS for reason in normalized)


def _nullable_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def passes_reduced_size_non_depth_gates(
    *,
    reason_keys: Collection[str] | None,
    gate_flags: Mapping[str, Any] | None = None,
) -> bool:
    normalized = _normalize_reason_keys(reason_keys)
    gates = gate_flags or {}
    orderbook_available = _nullable_bool(gates.get("orderbook_available"))
    orderbook_stale = _nullable_bool(gates.get("orderbook_stale"))
    spread_gate_pass = _nullable_bool(gates.get("spread_gate_pass"))
    slippage_gate_pass = _nullable_bool(gates.get("slippage_gate_pass"))
    has_explicit_gate_state = all(
        value is not None
        for value in (orderbook_available, orderbook_stale, spread_gate_pass, slippage_gate_pass)
    )

    if has_explicit_gate_state:
        if not orderbook_available or orderbook_stale or not spread_gate_pass or not slippage_gate_pass:
            return False
        if normalized:
            return not has_non_depth_blocking_reason(normalized)
        return True

    if not normalized:
        return False
    return not has_non_depth_blocking_reason(normalized)


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
    reason_keys: Collection[str] | None = None,
    gate_flags: Mapping[str, Any] | None = None,
) -> bool:
    if execution_status_raw not in TRADEABLE_STATUSES:
        return False
    if execution_size_class not in TRADEABLE_SIZE_CLASSES:
        return False
    if execution_status_raw in {"direct_ok", "tranche_ok"}:
        return True
    return passes_reduced_size_non_depth_gates(reason_keys=reason_keys, gate_flags=gate_flags)


def is_tradeable_candidate(*, decision_bucket: str | None, is_reduced_size_eligible_value: bool) -> bool:
    return decision_bucket in TOP_TRADEABLE_BUCKETS and bool(is_reduced_size_eligible_value)
