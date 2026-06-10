from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping

from scanner.decision.models import ExecutionInputContract
from scanner.execution.tradeability_metrics import compute_tradeability_metrics


@dataclass(frozen=True)
class ExecutionGradeResult:
    contract: ExecutionInputContract | None
    execution_status_raw: str
    execution_reason_raw: str | None
    execution_pass: bool | None
    metrics: Mapping[str, Any] | None = None


class _LegacyExecutionCfg:
    def __init__(self, execution_cfg: Mapping[str, Any]):
        self.raw = {}
        self.tradeability_notional_total_usdt = float(execution_cfg["notional_total_usdt"])
        self.tradeability_notional_chunk_usdt = float(execution_cfg["notional_chunk_usdt"])
        self.tradeability_max_tranches = int(execution_cfg["max_tranches"])
        self.tradeability_band_pct = 1.0
        self.tradeability_max_spread_pct = float(execution_cfg["max_spread_pct"])
        self.tradeability_min_depth_1pct_usd = float(execution_cfg["min_depth_1pct_usd"])
        self.tradeability_class_thresholds = {
            "direct_ok_max_slippage_bps": float(execution_cfg["direct_ok_max_slippage_bps"]),
            "tranche_ok_max_slippage_bps": float(execution_cfg["tranche_ok_max_slippage_bps"]),
            "marginal_max_slippage_bps": float(execution_cfg["marginal_max_slippage_bps"]),
        }


def _has_invalid_levels(orderbook: Mapping[str, Any]) -> bool:
    for side in ("bids", "asks"):
        levels = orderbook.get(side)
        if not isinstance(levels, list) or not levels:
            return True
        for level in levels:
            if not isinstance(level, (list, tuple)) or len(level) < 2:
                return True
            try:
                p = float(level[0])
                q = float(level[1])
            except (TypeError, ValueError):
                return True
            if not math.isfinite(p) or not math.isfinite(q) or p <= 0 or q <= 0:
                return True
    return False


def _map_reason(status: str, metrics: Mapping[str, Any]) -> str | None:
    if status == "direct_ok":
        return "DIRECT_OK_SPREAD_DEPTH"
    if status == "tranche_ok":
        return "TRANCHE_OK_SPREAD_DEPTH"

    reasons = set(metrics.get("tradeability_reason_keys") or [])
    if status == "marginal":
        if "spread_too_wide" in reasons or "depth_1pct_insufficient" in reasons:
            return "MARGINAL_SPREAD_OR_DEPTH"
        return None

    if "spread_too_wide" in reasons:
        return "FAIL_SPREAD"
    if "depth_1pct_insufficient" in reasons:
        return "FAIL_DEPTH"
    if "slippage_20k_too_high" in reasons or "slippage_5k_too_high" in reasons:
        return "FAIL_SLIPPAGE"
    return None


def grade_execution_orderbook(orderbook: Mapping[str, Any], execution_cfg: Mapping[str, Any]) -> ExecutionGradeResult:
    if _has_invalid_levels(orderbook):
        return ExecutionGradeResult(None, "unknown", "UNKNOWN_ORDERBOOK_MISSING", None, None)

    if bool(orderbook.get("stale") or orderbook.get("is_stale")):
        return ExecutionGradeResult(None, "unknown", "UNKNOWN_ORDERBOOK_STALE", None, None)

    try:
        metrics = compute_tradeability_metrics(dict(orderbook), _LegacyExecutionCfg(execution_cfg))
    except Exception:
        return ExecutionGradeResult(None, "unknown", "UNKNOWN_FETCH_FAILED", None, None)

    status_map = {
        "DIRECT_OK": "direct_ok",
        "TRANCHE_OK": "tranche_ok",
        "MARGINAL": "marginal",
        "FAIL": "fail",
    }
    raw_class = str(metrics.get("tradeability_class") or "UNKNOWN")
    if raw_class == "UNKNOWN":
        raw_reason = (metrics.get("tradeability_reason_keys") or [None])[0]
        reason_map = {
            "orderbook_data_missing": "UNKNOWN_ORDERBOOK_MISSING",
            "orderbook_data_stale": "UNKNOWN_ORDERBOOK_STALE",
            "orderbook_not_in_budget": "UNKNOWN_ORDERBOOK_MISSING",
        }
        return ExecutionGradeResult(None, "unknown", reason_map.get(raw_reason, "UNKNOWN_FETCH_FAILED"), None, metrics)

    status = status_map[raw_class]
    execution_pass = status in {"direct_ok", "tranche_ok"}
    contract = ExecutionInputContract(
        execution_status=status,
        execution_grade=None,
        execution_pass=execution_pass,
        execution_reason=_map_reason(status, metrics),
    )
    raw_reasons = metrics.get("tradeability_reason_keys") or []
    raw_reason = raw_reasons[0] if raw_reasons else None
    return ExecutionGradeResult(contract, status, raw_reason, execution_pass, metrics)
