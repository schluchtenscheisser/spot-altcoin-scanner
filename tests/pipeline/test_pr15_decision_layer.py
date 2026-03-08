from __future__ import annotations

import pytest

from scanner.pipeline.decision import apply_decision_layer


def _cfg(**overrides):
    base = {
        "decision": {
            "min_score_for_enter": 65,
            "min_score_for_wait": 40,
            "require_risk_acceptable_for_enter": True,
        },
        "btc_regime": {
            "risk_off_enter_boost": 15,
        },
    }
    for section, values in overrides.items():
        base.setdefault(section, {}).update(values)
    return base


def _single(row, config=None, btc_regime=None):
    out = apply_decision_layer([row], config or _cfg(), btc_regime=btc_regime)
    assert len(out) == 1
    return out[0]


def test_enter_for_direct_ok_when_all_requirements_are_met():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 70})
    assert out["decision"] == "ENTER"
    assert out["decision_reasons"] == []


def test_enter_for_tranche_ok_when_all_requirements_are_met():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "TRANCHE_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 66})
    assert out["decision"] == "ENTER"


def test_wait_when_entry_not_ready_but_quality_is_sufficient():
    out = _single(
        {
            "symbol": "AAAUSDT",
            "tradeability_class": "DIRECT_OK",
            "entry_ready": False,
            "entry_readiness_reasons": ["breakout_not_confirmed"],
            "risk_acceptable": True,
            "setup_score": 55,
        }
    )
    assert out["decision"] == "WAIT"
    assert out["decision_reasons"] == ["entry_not_confirmed", "breakout_not_confirmed"]


def test_wait_for_marginal_tradeability_even_when_entry_ready():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "MARGINAL", "entry_ready": True, "risk_acceptable": True, "setup_score": 75})
    assert out["decision"] == "WAIT"
    assert out["decision_reasons"] == ["tradeability_marginal"]


def test_wait_when_btc_regime_boost_prevents_enter():
    out = _single(
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 70},
        btc_regime={"state": "RISK_OFF"},
    )
    assert out["decision"] == "WAIT"
    assert out["decision_reasons"] == ["btc_regime_caution"]


def test_risk_on_uses_baseline_enter_threshold():
    out = _single(
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 70},
        btc_regime={"state": "RISK_ON"},
    )
    assert out["decision"] == "ENTER"
    assert out["decision_reasons"] == []


def test_missing_btc_regime_state_uses_neutral_baseline_without_caution():
    out = _single(
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 70},
        btc_regime={},
    )
    assert out["decision"] == "ENTER"
    assert out["decision_reasons"] == []


def test_invalid_btc_regime_state_is_rejected():
    with pytest.raises(ValueError, match="btc_regime.state must be one of"):
        _single(
            {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 70},
            btc_regime={"state": "bad_state"},
        )


def test_decision_output_contains_explicit_btc_regime_state_context():
    out = _single(
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 85},
        btc_regime={"state": "RISK_OFF"},
    )
    assert out["btc_regime_state"] == "RISK_OFF"


def test_no_trade_for_rejected_risk():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": False, "setup_score": 90})
    assert out["decision"] == "NO_TRADE"
    assert out["decision_reasons"] == ["risk_reward_unattractive"]


def test_no_trade_when_risk_data_is_insufficient_nullable_path():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": None, "setup_score": 90})
    assert out["decision"] == "NO_TRADE"
    assert out["decision_reasons"] == ["risk_data_insufficient"]


def test_no_trade_below_minimum_wait_score():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": False, "risk_acceptable": True, "setup_score": 30})
    assert out["decision"] == "NO_TRADE"
    assert out["decision_reasons"] == ["insufficient_edge", "entry_not_confirmed"]


def test_no_trade_when_hard_risk_flag_is_present():
    out = _single(
        {
            "symbol": "AAAUSDT",
            "tradeability_class": "DIRECT_OK",
            "entry_ready": True,
            "risk_acceptable": True,
            "risk_flags": ["stop_distance_too_wide"],
            "setup_score": 90,
        }
    )
    assert out["decision"] == "NO_TRADE"
    assert out["decision_reasons"] == ["risk_flag_blocked", "stop_distance_too_wide"]


def test_one_status_and_at_least_one_reason_for_non_enter_rows():
    rows = [
        {"symbol": "A", "tradeability_class": "UNKNOWN", "setup_score": 99, "entry_ready": True, "risk_acceptable": True},
        {"symbol": "B", "tradeability_class": "MARGINAL", "setup_score": 70, "entry_ready": True, "risk_acceptable": True},
        {"symbol": "C", "tradeability_class": "DIRECT_OK", "setup_score": 35, "entry_ready": False, "risk_acceptable": True},
    ]
    out = apply_decision_layer(rows, _cfg())
    for row in out:
        assert row["decision"] in {"ENTER", "WAIT", "NO_TRADE"}
        if row["decision"] != "ENTER":
            assert len(row["decision_reasons"]) >= 1


def test_unknown_and_fail_never_become_enter_or_wait():
    rows = [
        {"symbol": "AAAUSDT", "tradeability_class": "UNKNOWN", "setup_score": 99, "entry_ready": True, "risk_acceptable": True},
        {"symbol": "BBBUSDT", "tradeability_class": "FAIL", "setup_score": 99, "entry_ready": True, "risk_acceptable": True},
    ]
    out = apply_decision_layer(rows, _cfg())
    assert {row["symbol"]: row["decision"] for row in out} == {"AAAUSDT": "NO_TRADE", "BBBUSDT": "NO_TRADE"}


def test_missing_config_keys_use_canonical_defaults():
    out = _single({"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": True, "risk_acceptable": True, "setup_score": 65}, config={})
    assert out["decision"] == "ENTER"


def test_invalid_decision_config_is_rejected_when_wait_threshold_above_enter_threshold():
    with pytest.raises(ValueError, match="decision.min_score_for_wait must be <= decision.min_score_for_enter"):
        apply_decision_layer([], {"decision": {"min_score_for_enter": 30, "min_score_for_wait": 40}})


def test_invalid_btc_regime_boost_value_is_rejected():
    with pytest.raises(ValueError, match="btc_regime.risk_off_enter_boost must be numeric"):
        apply_decision_layer([], {"btc_regime": {"risk_off_enter_boost": "bad"}})


def test_reason_order_is_stable_when_multiple_wait_reasons_apply():
    out = _single(
        {
            "symbol": "AAAUSDT",
            "tradeability_class": "MARGINAL",
            "entry_ready": False,
            "entry_readiness_reasons": ["retest_not_reclaimed", "breakout_not_confirmed"],
            "risk_acceptable": True,
            "setup_score": 60,
        }
    )
    assert out["decision"] == "WAIT"
    assert out["decision_reasons"] == [
        "tradeability_marginal",
        "entry_not_confirmed",
        "breakout_not_confirmed",
        "retest_not_reclaimed",
    ]


def test_decision_output_is_deterministic_for_identical_inputs():
    rows = [
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK", "entry_ready": False, "entry_readiness_reasons": ["retest_not_reclaimed"], "risk_acceptable": True, "setup_score": 60},
        {"symbol": "BBBUSDT", "tradeability_class": "MARGINAL", "entry_ready": True, "risk_acceptable": True, "setup_score": 62},
    ]
    out1 = apply_decision_layer(rows, _cfg(), btc_regime={"state": "RISK_OFF"})
    out2 = apply_decision_layer(rows, _cfg(), btc_regime={"state": "RISK_OFF"})
    assert out1 == out2
