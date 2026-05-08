from __future__ import annotations

import pytest

from scanner.config import ScannerConfig
from scanner.decision.ranking import compute_priority_score
from scanner.execution.policy import (
    classify_execution_size,
    depth_ratio_band,
    has_non_depth_blocking_reason,
    is_reduced_size_eligible,
)
from scanner.output.schema import validate_diagnostics_record
from scanner.runners.daily import _build_execution_aware_report_payload


class _Ranked:
    def __init__(self, symbol: str, bucket: str):
        self.symbol = symbol
        self.decision = type("D", (), {"decision_bucket": type("B", (), {"value": bucket})()})()


def _cfg(raw: dict | None = None) -> ScannerConfig:
    return ScannerConfig(raw=raw or {"independence_release": {}})


def test_t29_execution_config_defaults_and_validation() -> None:
    cfg = _cfg().execution
    assert cfg["notional_total_usdt"] == 10_000.0
    assert cfg["notional_chunk_usdt"] == 5_000.0
    assert cfg["max_tranches"] == 2
    assert cfg["depth_buffer_multiple"] == 10.0
    assert cfg["min_depth_1pct_usd"] == 100_000.0

    override = _cfg({"independence_release": {"execution": {"min_phase_confidence": 70.0}}}).execution
    assert override["min_phase_confidence"] == 70.0
    assert override["notional_total_usdt"] == 10_000.0

    invalid_values = [float("nan"), float("inf"), -1.0, 0.0]
    for value in invalid_values:
        with pytest.raises(ValueError):
            _cfg({"independence_release": {"execution": {"notional_total_usdt": value}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"max_tranches": 2.5}}}).execution
    with pytest.raises(ValueError):
        _cfg({"independence_release": {"execution": {"min_depth_1pct_usd": 200_000.0}}}).execution


@pytest.mark.parametrize(
    ("ratio", "size_class", "factor", "grade"),
    [
        (1.0, "full", 1.0, 75.0),
        (0.75, "reduced_75", 0.75, 75.0),
        (0.50, "reduced_50", 0.50, 60.0),
        (0.25, "reduced_25", 0.25, 40.0),
        (0.24, "observe_only", 0.0, 0.0),
    ],
)
def test_t29_marginal_size_policy_mapping(ratio, size_class, factor, grade) -> None:
    result = classify_execution_size(
        execution_attempted=True,
        execution_status_raw="marginal",
        depth_ratio_band_value=depth_ratio_band(ratio),
    )
    assert result.execution_size_class == size_class
    assert result.recommended_position_factor == factor
    assert result.execution_grade_effective == grade


def test_t29_non_marginal_and_not_evaluated_size_policy_mapping() -> None:
    assert classify_execution_size(execution_attempted=True, execution_status_raw="direct_ok", depth_ratio_band_value="below_min").execution_grade_effective == 100.0
    assert classify_execution_size(execution_attempted=True, execution_status_raw="tranche_ok", depth_ratio_band_value="below_min").execution_grade_effective == 75.0
    fail = classify_execution_size(execution_attempted=True, execution_status_raw="fail", depth_ratio_band_value="full")
    assert fail.execution_size_class == "blocked"
    assert fail.recommended_position_factor == 0.0
    assert fail.execution_grade_effective == 0.0
    unknown = classify_execution_size(execution_attempted=True, execution_status_raw="unknown", depth_ratio_band_value="not_evaluable")
    assert unknown.execution_size_class == "not_evaluable"
    assert unknown.recommended_position_factor is None
    assert unknown.execution_grade_effective is None
    not_evaluated = classify_execution_size(execution_attempted=False, execution_status_raw=None, depth_ratio_band_value=None)
    assert not_evaluated.execution_size_class == "not_evaluated"


def _clean_gate_flags() -> dict[str, bool]:
    return {
        "orderbook_available": True,
        "orderbook_stale": False,
        "spread_gate_pass": True,
        "slippage_gate_pass": True,
    }


def test_t29_reduced_size_eligibility_allows_depth_only_reason_set() -> None:
    assert is_reduced_size_eligible(
        execution_status_raw="marginal",
        execution_size_class="reduced_50",
        reason_keys={"depth_1pct_insufficient"},
        gate_flags=_clean_gate_flags(),
    ) is True


def test_t29_reduced_size_eligibility_blocks_depth_plus_slippage_reason_set() -> None:
    assert is_reduced_size_eligible(
        execution_status_raw="marginal",
        execution_size_class="reduced_50",
        reason_keys={"depth_1pct_insufficient", "slippage_5k_too_high"},
        gate_flags=_clean_gate_flags(),
    ) is False


def test_t29_reduced_size_eligibility_blocks_depth_plus_spread_reason_set() -> None:
    assert is_reduced_size_eligible(
        execution_status_raw="marginal",
        execution_size_class="reduced_75",
        reason_keys={"depth_1pct_insufficient", "spread_too_wide"},
        gate_flags=_clean_gate_flags(),
    ) is False


def test_t29_reduced_size_eligibility_uses_full_reason_set_not_first_reason_order() -> None:
    ordered_reasons = ["depth_1pct_insufficient", "slippage_5k_too_high"]
    assert ordered_reasons == sorted(ordered_reasons)
    assert has_non_depth_blocking_reason(ordered_reasons) is True
    assert is_reduced_size_eligible(
        execution_status_raw="marginal",
        execution_size_class="reduced_50",
        reason_keys=ordered_reasons,
        gate_flags=_clean_gate_flags(),
    ) is False


def test_t29_reduced_size_eligibility_missing_reason_set_is_conservative_without_gate_flags() -> None:
    assert is_reduced_size_eligible(
        execution_status_raw="marginal",
        execution_size_class="reduced_50",
        reason_keys=None,
        gate_flags=None,
    ) is False


def test_t29_priority_score_uses_effective_grade_override() -> None:
    reduced_50 = compute_priority_score(
        market_phase_confidence=80.0,
        state_confidence=80.0,
        entry_pattern_score=80.0,
        execution_status="marginal",
        execution_grade=60.0,
    )
    reduced_25 = compute_priority_score(
        market_phase_confidence=80.0,
        state_confidence=80.0,
        entry_pattern_score=80.0,
        execution_status="marginal",
        execution_grade=40.0,
    )
    assert reduced_50 == pytest.approx(77.0)
    assert reduced_25 == pytest.approx(74.0)
    assert reduced_50 > reduced_25


def _diag(symbol: str, *, bucket: str, size_class: str, status: str = "marginal") -> dict:
    return {
        "symbol": symbol,
        "universe": {"universe_category": "classic_crypto", "candidate_excluded": False},
        "decision": {"decision_bucket": bucket, "priority_score": 50.0},
        "execution_attempted": True,
        "execution_status_raw": status,
        "execution_reason_raw": "depth_1pct_insufficient" if size_class == "observe_only" else None,
        "execution_pass": status in {"direct_ok", "tranche_ok"},
        "execution_size_class": size_class,
        "recommended_position_factor": {"full": 1.0, "reduced_50": 0.5, "observe_only": 0.0, "blocked": 0.0}.get(size_class),
        "execution_grade_effective": {"full": 75.0, "reduced_50": 60.0, "observe_only": 0.0, "blocked": 0.0}.get(size_class),
        "available_depth_ratio": 0.5,
        "depth_ratio_band": "reduced_50" if size_class == "reduced_50" else "below_min",
        "spread_pct": 0.1,
        "estimated_slippage_bps": 10.0,
        "is_reduced_size_eligible": size_class in {"full", "reduced_50"},
        "is_tradeable_candidate": size_class in {"full", "reduced_50"} and bucket in {"confirmed_candidates", "early_candidates"},
        "tradeability_reason_keys": ["depth_1pct_insufficient"] if size_class in {"reduced_50", "observe_only"} else [],
    }


def test_t29_report_counts_tradeable_and_observe_only_candidates() -> None:
    ranked = [_Ranked("A", "confirmed_candidates"), _Ranked("B", "confirmed_candidates"), _Ranked("C", "early_candidates")]
    diagnostics = [
        _diag("A", bucket="confirmed_candidates", size_class="reduced_50"),
        _diag("B", bucket="confirmed_candidates", size_class="observe_only"),
        _diag("C", bucket="early_candidates", size_class="blocked", status="fail"),
    ]
    payload = _build_execution_aware_report_payload(ranked=ranked, diagnostics=diagnostics)
    summary = payload["reduced_size_policy_summary"]
    assert summary["confirmed_candidates_total"] == 2
    assert summary["confirmed_tradeable_candidates"] == 1
    assert summary["confirmed_observe_only_candidates"] == 1
    assert summary["fail_blocked_count"] == 1


def test_t29_diagnostics_schema_accepts_new_fields_and_rejects_non_finite() -> None:
    base = {
        "run_id": "daily-2026-05-08-abcdef123456",
        "scan_mode": "daily",
        "symbol": "AAAUSDT",
        "as_of_utc": "2026-05-08T00:00:00Z",
        "daily_bar_id": "2026-05-08",
        "intraday_bar_id": None,
        "data_4h_available": True,
        "axes": {},
        "phase": {},
        "invalidation": {},
        "cycle": {},
        "state": {},
        "pattern": {},
        "decision": {},
        "reasons": {},
        "execution_attempted": False,
        "execution_status_raw": None,
        "execution_reason_raw": None,
        "execution_pass": None,
        "execution_grade_t16": None,
        "execution_size_class": "not_evaluated",
        "recommended_position_factor": None,
        "execution_grade_effective": None,
        "is_reduced_size_eligible": False,
        "is_tradeable_candidate": False,
        "tradeability_reason_keys": [],
        "execution_fetch_duration_ms": None,
    }
    validated = validate_diagnostics_record(base)
    assert validated["execution_size_class"] == "not_evaluated"
    assert validated["tradeability_reason_keys"] == []
    invalid = dict(base)
    invalid["execution_grade_effective"] = float("inf")
    with pytest.raises(ValueError):
        validate_diagnostics_record(invalid)


def test_t29_adapter_uses_full_reason_set_for_reduced_size_eligibility(monkeypatch) -> None:
    from scanner.decision.models import ExecutionInputContract
    import scanner.execution.adapter as adapter
    from scanner.execution.grading import ExecutionGradeResult

    def fake_grade(_orderbook, _execution_cfg):
        return ExecutionGradeResult(
            contract=ExecutionInputContract(execution_status="marginal", execution_pass=False),
            execution_status_raw="marginal",
            execution_reason_raw="depth_1pct_insufficient",
            execution_pass=False,
            metrics={
                "depth_bid_1pct_usd": 75_000.0,
                "depth_ask_1pct_usd": 75_000.0,
                "spread_pct": 0.10,
                "slippage_bps_5k": 150.0,
                "slippage_bps_20k": 150.0,
                "tradeability_reason_keys": ["depth_1pct_insufficient", "slippage_5k_too_high"],
            },
        )

    monkeypatch.setattr(adapter, "grade_execution_orderbook", fake_grade)
    result = adapter.evaluate_execution_subset(["AAA"], _cfg().execution, client=type("C", (), {"get_orderbook": lambda self, symbol, limit: {"bids": [[100, 1]], "asks": [[100.1, 1]]}})())
    row = result.diagnostics["AAA"]
    assert row["execution_reason_raw"] == "depth_1pct_insufficient"
    assert row["tradeability_reason_keys"] == ["depth_1pct_insufficient", "slippage_5k_too_high"]
    assert row["depth_ratio_band"] == "reduced_75"
    assert row["execution_size_class"] == "reduced_75"
    assert row["is_reduced_size_eligible"] is False
