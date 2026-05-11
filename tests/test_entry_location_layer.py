from __future__ import annotations

import math

import pytest

from scanner.config import ScannerConfig, resolve_independence_entry_location_config, validate_config
from scanner.decision.entry_location import (
    build_entry_location_report_segments,
    evaluate_entry_location,
)


def _cfg(overrides=None):
    raw = {"independence_release": {"entry_location": overrides or {}}}
    return resolve_independence_entry_location_config(raw)


def _record(
    *,
    dist=1.0,
    close=1.0,
    pattern="ema_reclaim",
    bucket="confirmed_candidates",
    excluded=False,
    tradeable=True,
    size="full",
    symbol="AAAUSDT",
    priority=1.0,
    range_high=2.0,
):
    inputs = {
        "close_vs_ema20_4h_pct": close,
        "dist_to_ema20_4h_pct_abs": dist,
        "bars_above_ema20_4h": 3,
        "distance_to_last_structural_anchor_pct_abs": 1.0,
        "bars_since_last_structural_break_4h": 1,
        "distance_to_range_high_pct_abs": range_high,
    }
    if dist == "missing":
        inputs.pop("dist_to_ema20_4h_pct_abs")
    return {
        "symbol": symbol,
        "entry_location_inputs": inputs,
        "pattern": {"entry_pattern": pattern},
        "decision": {"decision_bucket": bucket, "priority_score": priority},
        "universe": {"candidate_excluded": excluded},
        "is_tradeable_candidate": tradeable,
        "execution_size_class": size,
    }


def _status(dist, pattern="ema_reclaim"):
    return evaluate_entry_location(_record(dist=dist, pattern=pattern), _cfg()).entry_location_status


def test_config_defaults_and_partial_override_merge() -> None:
    default = resolve_independence_entry_location_config({})
    assert default["enabled"] is True
    assert default["version"] == "v1"
    assert default["thresholds"]["default"]["dist_to_ema20_4h_pct_abs"]["fresh_max"] == 2.5

    merged = _cfg({"thresholds": {"default": {"dist_to_ema20_4h_pct_abs": {"fresh_max": 2.0}}}})
    block = merged["thresholds"]["default"]["dist_to_ema20_4h_pct_abs"]
    assert block == {"fresh_max": 2.0, "acceptable_max": 5.5, "extended_max": 8.5}
    assert "continuation_breakout" in merged["thresholds"]["pattern_overrides"]


@pytest.mark.parametrize(
    "overrides, expected",
    [
        ({"thresholds": {"default": {"dist_to_ema20_4h_pct_abs": {"fresh_max": 6.0}}}}, "fresh_max < acceptable_max"),
        ({"thresholds": {"default": {"dist_to_ema20_4h_pct_abs": {"fresh_max": math.inf}}}}, "finite number"),
        ({"guards": {"extreme_value_not_evaluable_pct": 8.5}}, "greater than all configured extended_max"),
        ({"auxiliary": {"distance_to_range_high_pct_abs": {"proximity_warning_max_pct": -0.1}}}, "must be >= 0.0"),
    ],
)
def test_invalid_config_fails_validation(overrides, expected) -> None:
    errors = validate_config(ScannerConfig(raw={"independence_release": {"entry_location": overrides}}))
    assert any(expected in error for error in errors)


@pytest.mark.parametrize(
    "dist, expected",
    [
        (0.0, "fresh_entry"),
        (2.5, "fresh_entry"),
        (2.51, "acceptable_entry"),
        (5.5, "acceptable_entry"),
        (5.51, "extended_entry"),
        (8.5, "extended_entry"),
        (8.51, "chased_entry"),
        (50.01, "not_evaluable"),
    ],
)
def test_default_status_boundaries(dist, expected) -> None:
    assert _status(dist) == expected


def test_continuation_breakout_override_and_secondary_inputs_do_not_change_status() -> None:
    assert _status(3.5, pattern="continuation_breakout") == "fresh_entry"
    assert _status(7.0, pattern="continuation_breakout") == "acceptable_entry"
    assert _status(10.0, pattern="continuation_breakout") == "extended_entry"
    baseline = evaluate_entry_location(_record(dist=4.0), _cfg()).entry_location_status
    changed = _record(dist=4.0)
    changed["entry_location_inputs"]["bars_above_ema20_4h"] = 99
    changed["entry_location_inputs"]["distance_to_last_structural_anchor_pct_abs"] = 99.0
    changed["entry_location_inputs"]["bars_since_last_structural_break_4h"] = 99
    assert evaluate_entry_location(changed, _cfg()).entry_location_status == baseline


@pytest.mark.parametrize(
    "record, reason",
    [
        ({}, "missing_entry_location_inputs"),
        ({"entry_location_inputs": []}, "invalid_entry_location_inputs_type"),
        (_record(dist="missing"), "missing_dist_to_ema20_4h_pct_abs"),
        (_record(dist=math.nan), "non_finite_dist_to_ema20_4h_pct_abs"),
        (_record(dist=-0.1), "invalid_negative_abs_ema20_distance"),
    ],
)
def test_not_evaluable_input_reasons(record, reason) -> None:
    result = evaluate_entry_location(record, _cfg())
    assert result.entry_location_status == "not_evaluable"
    assert result.entry_action_hint == "not_evaluable"
    assert result.entry_location_reason_primary == reason


def test_negative_close_vs_ema_does_not_block_valid_abs_distance() -> None:
    result = evaluate_entry_location(_record(dist=2.0, close=-2.0), _cfg())
    assert result.entry_location_status == "fresh_entry"


@pytest.mark.parametrize("range_high, expected", [(0.5, True), (0.51, False), (None, None), (math.inf, None)])
def test_range_high_warning_is_auxiliary(range_high, expected) -> None:
    base = _record(dist=1.0, range_high=range_high)
    result = evaluate_entry_location(base, _cfg())
    assert result.range_high_proximity_warning is expected
    assert result.entry_location_status == "fresh_entry"
    assert result.entry_action_hint == "buy_now_candidate"


@pytest.mark.parametrize(
    "kwargs, hint",
    [
        ({"dist": 50.01, "tradeable": True}, "not_evaluable"),
        ({"dist": 9.0}, "avoid_chasing"),
        ({"excluded": True, "tradeable": True}, "monitor_only"),
        ({"tradeable": False}, "monitor_only"),
        ({"tradeable": None}, "monitor_only"),
        ({"bucket": "early_candidates", "dist": 1.0, "size": "full", "tradeable": True}, "monitor_only"),
        ({"bucket": "confirmed_candidates", "dist": 1.0, "size": "full", "tradeable": True}, "buy_now_candidate"),
        ({"bucket": "confirmed_candidates", "dist": 1.0, "size": "reduced_25", "tradeable": True}, "acceptable_if_strategy_allows"),
        ({"bucket": "confirmed_candidates", "dist": 4.0, "size": "full", "tradeable": True}, "acceptable_if_strategy_allows"),
        ({"bucket": "confirmed_candidates", "dist": 4.0, "size": "reduced_50", "tradeable": True}, "acceptable_if_strategy_allows"),
        ({"bucket": "confirmed_candidates", "dist": 4.0, "size": "reduced_25", "tradeable": True}, "wait_for_pullback"),
        ({"bucket": "confirmed_candidates", "dist": 6.0, "size": "full", "tradeable": True}, "wait_for_pullback"),
        ({"bucket": "confirmed_candidates", "dist": 1.0, "size": "surprise", "tradeable": True}, "monitor_only"),
    ],
)
def test_action_hint_ordered_matrix(kwargs, hint) -> None:
    result = evaluate_entry_location(_record(**kwargs), _cfg())
    assert result.entry_action_hint == hint
    if kwargs.get("size") == "surprise":
        assert "unhandled_action_hint_combination" in result.entry_location_reason_codes


def test_report_segments_and_sorting() -> None:
    records = [
        _record(symbol="BUY", dist=1.0, priority=2.0),
        _record(symbol="WAIT", dist=6.0, priority=4.0),
        _record(symbol="EARLY", bucket="early_candidates", dist=1.0, priority=3.0),
        _record(symbol="GOOD", tradeable=False, dist=1.0, priority=5.0),
        _record(symbol="CHASE", dist=9.0, priority=6.0),
        _record(symbol="A", dist=6.0, priority=4.0),
    ]
    enriched = [evaluate_entry_location(r, _cfg()).to_dict() for r in records]
    for r, block in zip(records, enriched):
        r["entry_location"] = block
    segments = build_entry_location_report_segments(records)
    assert [x["symbol"] for x in segments["buy_now_candidates"]] == ["BUY"]
    assert [x["symbol"] for x in segments["wait_pullback_candidates"]] == ["A", "WAIT"]
    assert [x["symbol"] for x in segments["early_watch_candidates"]] == ["EARLY"]
    assert [x["symbol"] for x in segments["good_location_but_not_tradeable"]] == ["GOOD"]
    assert [x["symbol"] for x in segments["tradeable_but_extended"]] == ["CHASE", "A", "WAIT"]


def test_regression_cases() -> None:
    aix = evaluate_entry_location(_record(symbol="AIXDROPUSDT", pattern="ema_reclaim", dist=50.01), _cfg())
    assert aix.entry_location_status == "not_evaluable"
    assert aix.entry_action_hint == "not_evaluable"

    usdp = evaluate_entry_location(_record(symbol="USDPUSDT", excluded=True, tradeable=True), _cfg())
    assert usdp.entry_action_hint == "monitor_only"

    oneinch = _record(symbol="1INCHUSDT", tradeable=False)
    oneinch["entry_location"] = evaluate_entry_location(oneinch, _cfg()).to_dict()
    assert oneinch["entry_location"]["entry_action_hint"] == "monitor_only"
    assert build_entry_location_report_segments([oneinch])["good_location_but_not_tradeable"][0]["symbol"] == "1INCHUSDT"

    assert evaluate_entry_location(_record(symbol="ASTERUSDT", dist=5.49), _cfg()).entry_location_status == "acceptable_entry"
