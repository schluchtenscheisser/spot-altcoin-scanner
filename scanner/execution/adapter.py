from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Any, Iterable, Mapping

from scanner.clients.mexc_client import MEXCClient
from scanner.decision.models import ExecutionInputContract, RankedDecision
from scanner.execution.grading import grade_execution_orderbook

_ACTIVE_BUCKETS = {"early_candidates", "confirmed_candidates", "late_monitor"}
_HARD_EXCLUDED_STATES = {"rejected", "chased"}
_UNKNOWN_NON_MAPPING_PAYLOAD_REASON = "UNKNOWN_FETCH_FAILED"


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    v = float(value)
    from math import isfinite
    return v if isfinite(v) else None


def _depth_band(ratio: float | None) -> str:
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


def _factor_preview(band: str) -> float | None:
    return {"full":1.0,"reduced_75":0.75,"reduced_50":0.5,"reduced_25":0.25,"below_min":0.0}.get(band)


def _limiting_metric(execution_status_raw: str, execution_reason_raw: str | None, attempted: bool) -> str:
    if not attempted:
        return "not_evaluated"
    reason = str(execution_reason_raw or "").lower()
    if "stale" in reason:
        return "stale_orderbook"
    if "missing" in reason:
        return "missing_orderbook"
    if "depth" in reason:
        return "depth_1pct"
    if "spread" in reason:
        return "spread"
    if "slippage" in reason:
        return "slippage"
    if execution_status_raw == "unknown":
        return "unknown"
    return "none"


@dataclass(frozen=True)
class ExecutionEvaluationResult:
    contracts: dict[str, ExecutionInputContract]
    diagnostics: dict[str, dict[str, Any]]


def select_execution_subset(pre_execution_decisions: Iterable[RankedDecision], execution_cfg: Mapping[str, Any]) -> list[str]:
    selected: list[tuple[str, float]] = []
    for row in pre_execution_decisions:
        state = getattr(row, "state_machine_state", None)
        bucket = getattr(row, "decision_bucket", None)
        if bucket is None:
            bucket = getattr(getattr(row, "decision", None), "decision_bucket", None)
        bucket_value = getattr(bucket, "value", bucket)
        if state in _HARD_EXCLUDED_STATES or bucket_value == "discarded":
            continue

        confidence = row.market_phase_confidence if isinstance(row.market_phase_confidence, (int, float)) else None
        cond_state = state in {"early_ready", "confirmed_ready", "late"}
        cond_conf = confidence is not None and float(confidence) >= float(execution_cfg["min_phase_confidence"])
        cond_bucket = bucket_value in _ACTIVE_BUCKETS
        if cond_state or cond_conf or cond_bucket:
            priority = getattr(row, "priority_score", None)
            if priority is None:
                priority = getattr(getattr(row, "decision", None), "priority_score", 0.0)
            selected.append((row.symbol, float(priority)))

    selected.sort(key=lambda x: (-x[1], x[0]))
    return [symbol for symbol, _ in selected]


def evaluate_execution_subset(
    symbols: list[str],
    cfg: Mapping[str, Any],
    client: MEXCClient | None = None,
) -> ExecutionEvaluationResult:
    execution_cfg = cfg["execution"] if "execution" in cfg else cfg
    api = client or MEXCClient(
        max_retries=int(execution_cfg["fetch_max_retries"]),
        timeout=int(execution_cfg["fetch_timeout_seconds"]),
    )

    contracts: dict[str, ExecutionInputContract] = {}
    diagnostics: dict[str, dict[str, Any]] = {}

    for symbol in symbols:
        t0 = perf_counter()
        try:
            orderbook = api.get_orderbook(symbol=symbol, limit=int(execution_cfg["orderbook_depth_levels"]))
        except Exception:
            duration_ms = max(0, int((perf_counter() - t0) * 1000))
            diagnostics[symbol] = {
                "execution_attempted": True,
                "execution_status_raw": "unknown",
                "execution_reason_raw": "UNKNOWN_FETCH_FAILED",
                "execution_pass": None,
                "execution_grade_t16": None,
                "execution_fetch_duration_ms": duration_ms,
                "available_depth_1pct_usdt": None,
                "depth_threshold_1pct_usdt": _finite_number(execution_cfg.get("min_depth_1pct_usd")),
                "available_depth_ratio": None,
                "depth_ratio_band": "not_evaluable",
                "recommended_position_factor_preview": None,
                "execution_limiting_metric": "unknown",
                "spread_pct": None,
                "estimated_slippage_bps": None,
                "orderbook_snapshot_age_ms": None,
                "bid_depth_1pct_usdt": None,
                "ask_depth_1pct_usdt": None,
                "depth_side_used": "unknown",
            }
            continue

        if not isinstance(orderbook, Mapping):
            # Re-use existing UNKNOWN_* taxonomy without schema expansion:
            # non-mapping payloads are treated as fetch/transport-level invalid responses.
            duration_ms = max(0, int((perf_counter() - t0) * 1000))
            diagnostics[symbol] = {
                "execution_attempted": True,
                "execution_status_raw": "unknown",
                "execution_reason_raw": _UNKNOWN_NON_MAPPING_PAYLOAD_REASON,
                "execution_pass": None,
                "execution_grade_t16": None,
                "execution_fetch_duration_ms": duration_ms,
                "available_depth_1pct_usdt": None,
                "depth_threshold_1pct_usdt": _finite_number(execution_cfg.get("min_depth_1pct_usd")),
                "available_depth_ratio": None,
                "depth_ratio_band": "not_evaluable",
                "recommended_position_factor_preview": None,
                "execution_limiting_metric": "unknown",
                "spread_pct": None,
                "estimated_slippage_bps": None,
                "orderbook_snapshot_age_ms": None,
                "bid_depth_1pct_usdt": None,
                "ask_depth_1pct_usdt": None,
                "depth_side_used": "unknown",
            }
            continue

        freshness = int(execution_cfg["orderbook_freshness_max_seconds"])
        ts = orderbook.get("timestamp") or orderbook.get("ts")
        if isinstance(ts, (int, float)):
            from time import time
            age_seconds = max(0.0, time() - (float(ts) / 1000.0 if float(ts) > 10_000_000_000 else float(ts)))
            if age_seconds > freshness:
                orderbook = dict(orderbook)
                orderbook["is_stale"] = True

        graded = grade_execution_orderbook(orderbook, execution_cfg)
        duration_ms = max(0, int((perf_counter() - t0) * 1000))
        if graded.contract is not None:
            contracts[symbol] = graded.contract
        metrics = dict(graded.metrics or {})
        depth_threshold = _finite_number(execution_cfg.get("min_depth_1pct_usd"))
        bid_depth = _finite_number(metrics.get("depth_bid_1pct_usd"))
        ask_depth = _finite_number(metrics.get("depth_ask_1pct_usd"))
        available_depth = ask_depth
        depth_side_used = "ask" if available_depth is not None else ("not_evaluated" if graded.execution_status_raw == "unknown" and graded.execution_reason_raw == "UNKNOWN_ORDERBOOK_MISSING" else "unknown")
        ratio = (available_depth / depth_threshold) if (available_depth is not None and depth_threshold is not None and depth_threshold > 0) else None
        band = _depth_band(ratio)
        ts = orderbook.get("timestamp") or orderbook.get("ts")
        age_ms = None
        if isinstance(ts, (int, float)):
            from time import time
            tsv = float(ts)
            ts_sec = tsv / 1000.0 if tsv > 10_000_000_000 else tsv
            age_calc = int((time() - ts_sec) * 1000)
            age_ms = age_calc if age_calc >= 0 else None
        diagnostics[symbol] = {
            "execution_attempted": True,
            "execution_status_raw": graded.execution_status_raw,
            "execution_reason_raw": graded.execution_reason_raw,
            "execution_pass": graded.execution_pass,
            "execution_grade_t16": None,
            "execution_fetch_duration_ms": duration_ms,
            "available_depth_1pct_usdt": available_depth,
            "depth_threshold_1pct_usdt": depth_threshold,
            "available_depth_ratio": ratio,
            "depth_ratio_band": band,
            "recommended_position_factor_preview": _factor_preview(band),
            "execution_limiting_metric": _limiting_metric(graded.execution_status_raw, graded.execution_reason_raw, True),
            "spread_pct": _finite_number(metrics.get("spread_pct")),
            "estimated_slippage_bps": _finite_number(metrics.get("slippage_bps_20k")),
            "orderbook_snapshot_age_ms": age_ms,
            "bid_depth_1pct_usdt": bid_depth,
            "ask_depth_1pct_usdt": ask_depth,
            "depth_side_used": depth_side_used,
        }

    return ExecutionEvaluationResult(contracts=contracts, diagnostics=diagnostics)
