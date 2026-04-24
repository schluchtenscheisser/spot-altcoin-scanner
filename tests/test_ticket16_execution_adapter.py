from __future__ import annotations

import pytest

from scanner.config import ScannerConfig
from scanner.decision.models import DecisionBucket, ExecutionInputContract
from scanner.execution.adapter import evaluate_execution_subset, select_execution_subset
from scanner.execution.grading import grade_execution_orderbook


class _Decision:
    def __init__(self, bucket: str, priority: float):
        self.decision_bucket = DecisionBucket(bucket)
        self.priority_score = priority


class _Client:
    def __init__(self, payload):
        self.payload = payload

    def get_orderbook(self, symbol: str, limit: int = 20):
        value = self.payload[symbol]
        if isinstance(value, Exception):
            raise value
        return value


def _cfg(raw: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=raw or {"independence_release": {}})


def test_execution_config_defaults_and_validation() -> None:
    cfg = _cfg()
    assert cfg.execution["min_phase_confidence"] == 60.0
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"execution_safety_limit": 0}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"min_phase_confidence": 101}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"min_phase_confidence": float("nan")}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"min_phase_confidence": float("inf")}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"min_phase_confidence": float("-inf")}}}).execution


def test_subset_selection_hard_exclusions_and_determinism() -> None:
    rows = [
        type("R", (), {"symbol": "B", "priority_score": 10.0, "decision_bucket": DecisionBucket.EARLY_CANDIDATES, "state_machine_state": "early_ready", "market_phase_confidence": 40.0})(),
        type("R", (), {"symbol": "A", "priority_score": 10.0, "decision_bucket": DecisionBucket.EARLY_CANDIDATES, "state_machine_state": "early_ready", "market_phase_confidence": 40.0})(),
        type("R", (), {"symbol": "X", "priority_score": 99.0, "decision_bucket": DecisionBucket.DISCARDED, "state_machine_state": "confirmed_ready", "market_phase_confidence": 99.0})(),
        type("R", (), {"symbol": "Y", "priority_score": 99.0, "decision_bucket": DecisionBucket.WATCHLIST, "state_machine_state": "chased", "market_phase_confidence": 99.0})(),
    ]
    subset = select_execution_subset(rows, _cfg().execution)
    assert subset == ["A", "B"]


def test_grade_unknown_and_mapping() -> None:
    unknown = grade_execution_orderbook({"bids": [], "asks": []}, _cfg().execution)
    assert unknown.contract is None
    assert unknown.execution_status_raw == "unknown"

    direct = grade_execution_orderbook(
        {
            "bids": [[100, 3000], [99.9, 3000]],
            "asks": [[100.05, 3000], [100.1, 3000]],
        },
        _cfg().execution,
    )
    assert isinstance(direct.contract, ExecutionInputContract)
    assert direct.contract.execution_status in {"direct_ok", "tranche_ok", "marginal", "fail"}
    assert direct.contract.execution_grade is None


def test_evaluate_execution_subset_unknown_on_fetch_failure() -> None:
    result = evaluate_execution_subset(
        ["AAA"],
        _cfg().execution,
        client=_Client({"AAA": RuntimeError("boom")}),
    )
    assert result.contracts == {}
    assert result.diagnostics["AAA"]["execution_status_raw"] == "unknown"
    assert result.diagnostics["AAA"]["execution_reason_raw"] == "UNKNOWN_FETCH_FAILED"


@pytest.mark.parametrize("payload", [None, [], "oops", 123])
def test_evaluate_execution_subset_non_mapping_payload_is_unknown(payload) -> None:
    result = evaluate_execution_subset(
        ["AAA"],
        _cfg().execution,
        client=_Client({"AAA": payload}),
    )
    assert result.contracts == {}
    assert result.diagnostics["AAA"]["execution_attempted"] is True
    assert result.diagnostics["AAA"]["execution_status_raw"] == "unknown"
    assert result.diagnostics["AAA"]["execution_reason_raw"] == "UNKNOWN_FETCH_FAILED"
