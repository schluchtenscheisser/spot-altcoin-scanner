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
        diagnostics[symbol] = {
            "execution_attempted": True,
            "execution_status_raw": graded.execution_status_raw,
            "execution_reason_raw": graded.execution_reason_raw,
            "execution_pass": graded.execution_pass,
            "execution_grade_t16": None,
            "execution_fetch_duration_ms": duration_ms,
        }

    return ExecutionEvaluationResult(contracts=contracts, diagnostics=diagnostics)
