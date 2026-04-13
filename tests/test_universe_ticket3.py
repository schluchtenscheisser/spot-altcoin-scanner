from datetime import date

import pytest

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
    result = evaluate_activity_gate(daily_bar_id="2026-04-14", bars_by_date=bars, cfg=_cfg())
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
