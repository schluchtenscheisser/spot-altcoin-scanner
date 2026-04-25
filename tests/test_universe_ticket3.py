from datetime import date

import pytest

from scanner.execution import select_execution_subset
from scanner.universe import (
    EligibilityInput,
    cap_non_bypass_candidates,
    evaluate_activity_gate,
    evaluate_monitoring_bypass,
    evaluate_pre_1d_eligibility,
    evaluate_pre_4h_candidate_filter,
)


def _cfg(overrides=None):
    base = {"independence_release": {"universe": {}, "market_data_budget": {}}}
    if overrides:
        base["independence_release"].update(overrides)
    return base


def test_pre_1d_eligibility_unknowns_pass_flagged():
    result = evaluate_pre_1d_eligibility(
        EligibilityInput(
            symbol="ABCUSDT",
            quote_asset="USDT",
            mexc_status="1",
            quote_volume_24h=600000,
            market_cap_usd=None,
            has_cmc_match=False,
            mexc_first_tradable_date=None,
            decision_timestamp_utc="2026-04-13T00:00:00Z",
        ),
        _cfg(),
        as_of_date=date(2026, 4, 13),
    )
    assert result["eligible_pre_1d"] is True
    assert result["listing_age_status"] == "unknown_pass"
    assert result["market_cap_status"] == "unknown_pass"


def test_activity_gate_not_evaluable_for_invalid_inputs_over_tolerance():
    bars = {f"2026-04-{d:02d}": {"quote_volume": 30000} for d in range(1, 15)}
    bars["2026-04-03"] = {"quote_volume": float("nan")}
    bars["2026-04-04"] = {"quote_volume": None}
    bars["2026-04-05"] = {"quote_volume": float("inf")}
    result = evaluate_activity_gate(
        daily_bar_id="2026-04-14",
        bars_by_date=bars,
        total_history_bar_count=14,
        cfg=_cfg(),
    )
    assert result["activity_gate_status"] == "not_evaluable"


def test_pre_4h_filter_priority_and_matching_order():
    result = evaluate_pre_4h_candidate_filter(
        {
            "close_vs_ema50_1d_pct": 1.0,
            "ema20_vs_ema50_1d_pct": 0.0,
            "ema20_slope_1d_pct_per_bar": 0.1,
            "volume_1d_current_vs_median10": 2.1,
            "range_width_10bars_1d_pct": 5.0,
            "close_position_in_range_10bars_1d": 0.9,
        },
        _cfg(),
    )
    assert result["pre_4h_filter_primary_reason"] == "FILTER_PASSED_COMPRESSION_1D"
    assert result["matched_filter_rules"] == [
        "FILTER_PASSED_COMPRESSION_1D",
        "FILTER_PASSED_TREND_1D",
        "FILTER_PASSED_VOLUME_IMPULSE_1D",
    ]


def test_bypass_and_cap_deterministic_tie_break():
    applied, reason = evaluate_monitoring_bypass(
        state_machine_state="watch", decision_bucket=None, market_phase_confidence=None, cfg=_cfg()
    )
    assert applied and reason == "BYPASS_STATE"

    selected, capped, remaining = cap_non_bypass_candidates(
        max_4h_fetch_count=1,
        bypass_symbols=[],
        non_bypass_passed=[
            {"symbol": "ZZZUSDT", "quote_volume_24h": 1000},
            {"symbol": "AAAUSDT", "quote_volume_24h": 1000},
        ],
    )
    assert remaining == 1
    assert selected == ["AAAUSDT"]
    assert capped == ["ZZZUSDT"]


def test_config_invalid_close_position_range_raises():
    with pytest.raises(ValueError, match="close_position_in_range_10bars_1d_min_inclusive"):
        evaluate_pre_4h_candidate_filter({}, _cfg({"market_data_budget": {"pre_4h_candidate_filter": {"rule_c": {"close_position_in_range_10bars_1d_min_inclusive": 1.5}}}}))


def test_activity_gate_missing_dates_in_window_count_as_inactive_not_insufficient_history():
    bars = {f"2026-04-{d:02d}": {"quote_volume": 30000} for d in range(1, 12)}
    result = evaluate_activity_gate(
        daily_bar_id="2026-04-14",
        bars_by_date=bars,
        total_history_bar_count=100,
        cfg=_cfg(),
    )
    assert result["activity_gate_status"] == "failed"
    assert result["activity_gate_reason"] == "ACTIVITY_GATE_INSUFFICIENT_ACTIVE_DAYS"


def test_activity_gate_uses_insufficient_history_only_for_true_history_shortage():
    bars = {f"2026-04-{d:02d}": {"quote_volume": 30000} for d in range(1, 11)}
    result = evaluate_activity_gate(
        daily_bar_id="2026-04-14",
        bars_by_date=bars,
        total_history_bar_count=10,
        cfg=_cfg(),
    )
    assert result["activity_gate_status"] == "not_evaluable"
    assert result["activity_gate_reason"] == "ACTIVITY_GATE_INSUFFICIENT_HISTORY"


def test_config_invalid_rule_b_threshold_raises_before_runtime_cast():
    with pytest.raises(ValueError, match="volume_1d_current_vs_median10_min_inclusive"):
        evaluate_pre_4h_candidate_filter(
            {},
            _cfg(
                {
                    "market_data_budget": {
                        "pre_4h_candidate_filter": {
                            "rule_b": {
                                "volume_1d_current_vs_median10_min_inclusive": 0,
                            }
                        }
                    }
                }
            ),
        )


def test_pre_4h_filter_failure_does_not_imply_fachlich_rejection_or_discarded() -> None:
    filter_result = evaluate_pre_4h_candidate_filter(
        {
            "close_vs_ema50_1d_pct": -2.0,
            "ema20_vs_ema50_1d_pct": -1.0,
            "ema20_slope_1d_pct_per_bar": -0.2,
            "volume_1d_current_vs_median10": 0.8,
            "range_width_10bars_1d_pct": 25.0,
            "close_position_in_range_10bars_1d": 0.2,
        },
        _cfg(),
    )
    assert filter_result["pre_4h_filter_status"] == "failed"

    row = type(
        "ExecutionSelectionRow",
        (),
        {
            "symbol": "AAAUSDT",
            "priority_score": 10.0,
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "state_machine_state": "watch",
            "pre_4h_filter_status": filter_result["pre_4h_filter_status"],
            "pre_4h_filter_primary_reason": filter_result["pre_4h_filter_primary_reason"],
        },
    )()
    subset = select_execution_subset([row], {"min_phase_confidence": 60.0})
    assert subset == []
    assert row.state_machine_state != "rejected"
    assert row.decision_bucket != "discarded"
    assert row.pre_4h_filter_primary_reason == "FILTER_FAILED_ALL_RULES"
