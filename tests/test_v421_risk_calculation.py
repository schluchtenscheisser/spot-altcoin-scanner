import math

import pytest

from scanner.config import ScannerConfig, validate_config
from scanner.pipeline.scoring.breakout import score_breakouts
from scanner.pipeline.scoring.trade_levels import compute_phase1_risk_fields


def _risk_cfg(**overrides):
    risk = {
        "atr_multiple": 2.0,
        "min_stop_distance_pct": 4.0,
        "max_stop_distance_pct": 12.0,
        "min_rr_to_tp10": 1.3,
    }
    risk.update(overrides)
    return {"risk": risk}


def _trade_levels(entry=100.0, atr=2.0, tp10=110.0, tp20=120.0, invalidation=None):
    return {
        "entry_trigger": entry,
        "atr_value": atr,
        "targets": [tp10, tp20],
        "invalidation": invalidation,
    }


def test_risk_uses_valid_invalidation_before_atr_fallback() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(invalidation=97.0), _risk_cfg())

    assert fields["stop_price_initial"] == pytest.approx(97.0)
    assert fields["stop_source"] == "invalidation"
    assert fields["risk_pct_to_stop"] == pytest.approx(3.0)
    assert fields["rr_to_target_1"] == pytest.approx(10.0 / 3.0)
    assert fields["rr_to_target_2"] == pytest.approx(20.0 / 3.0)
    assert fields["risk_acceptable"] is False


def test_risk_stop_calculation_falls_back_to_atr_path() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(), _risk_cfg())

    assert fields["stop_price_initial"] == pytest.approx(96.0)
    assert fields["stop_source"] == "atr_fallback"
    assert fields["risk_pct_to_stop"] == pytest.approx(4.0)
    assert fields["rr_to_target_1"] == pytest.approx(2.5)
    assert fields["rr_to_target_2"] == pytest.approx(5.0)
    assert fields["risk_acceptable"] is True


def test_risk_min_stop_distance_floor_gate() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(atr=1.5), _risk_cfg())

    assert fields["risk_pct_to_stop"] == pytest.approx(3.0)
    assert fields["risk_acceptable"] is False


def test_risk_max_stop_distance_cap_gate() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(atr=7.0), _risk_cfg())

    assert fields["risk_pct_to_stop"] == pytest.approx(14.0)
    assert fields["risk_acceptable"] is False


def test_risk_rr_threshold_true_and_false() -> None:
    acceptable = compute_phase1_risk_fields(
        "breakout",
        _trade_levels(tp10=106.0, tp20=112.0),
        _risk_cfg(min_rr_to_tp10=1.3),
    )
    unattractive = compute_phase1_risk_fields(
        "breakout",
        _trade_levels(tp10=104.0, tp20=108.0),
        _risk_cfg(min_rr_to_tp10=1.3),
    )

    assert acceptable["rr_to_target_1"] == pytest.approx(1.5)
    assert acceptable["risk_acceptable"] is True
    assert unattractive["rr_to_target_1"] == pytest.approx(1.0)
    assert unattractive["risk_acceptable"] is False


@pytest.mark.parametrize("invalidation", [math.nan, math.inf, -math.inf, 100.0, 101.0, -1.0, 0.0])
def test_invalid_invalidation_is_ignored_and_atr_fallback_used(invalidation: float) -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(invalidation=invalidation), _risk_cfg())

    assert fields["stop_price_initial"] == pytest.approx(96.0)
    assert fields["stop_source"] == "atr_fallback"
    assert fields["risk_acceptable"] is True


def test_no_valid_invalidation_and_no_valid_atr_keeps_all_risk_fields_nullable() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(atr=None, invalidation=101.0), _risk_cfg())

    assert fields["stop_price_initial"] is None
    assert fields["stop_source"] is None
    assert fields["risk_pct_to_stop"] is None
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


def test_stop_and_risk_distance_available_when_targets_missing() -> None:
    fields = compute_phase1_risk_fields(
        "breakout",
        {"entry_trigger": 100.0, "atr_value": 2.0, "targets": [None, 120.0], "invalidation": 98.0},
        _risk_cfg(),
    )

    assert fields["stop_price_initial"] == pytest.approx(98.0)
    assert fields["stop_source"] == "invalidation"
    assert fields["risk_pct_to_stop"] == pytest.approx(2.0)
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


@pytest.mark.parametrize(
    "trade_levels",
    [
        {"entry_trigger": 100.0, "targets": [110.0, 120.0]},
        {"atr_value": 2.0, "targets": [110.0, 120.0]},
    ],
)
def test_missing_required_inputs_keep_risk_nullable(trade_levels) -> None:
    fields = compute_phase1_risk_fields("breakout", trade_levels, _risk_cfg())

    assert fields["stop_price_initial"] is None
    assert fields["stop_source"] is None
    assert fields["risk_pct_to_stop"] is None
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


def test_missing_targets_keep_rr_and_acceptability_nullable_but_preserve_stop_fields() -> None:
    fields = compute_phase1_risk_fields(
        "breakout",
        {"entry_trigger": 100.0, "atr_value": 2.0, "targets": [None, 120.0]},
        _risk_cfg(),
    )

    assert fields["stop_price_initial"] == pytest.approx(96.0)
    assert fields["stop_source"] == "atr_fallback"
    assert fields["risk_pct_to_stop"] == pytest.approx(4.0)
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_non_finite_inputs_are_not_evaluable(value: float) -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(atr=value), _risk_cfg())

    assert fields["stop_price_initial"] is None
    assert fields["stop_source"] is None
    assert fields["risk_pct_to_stop"] is None
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


@pytest.mark.parametrize("field", ["entry", "tp10", "tp20"])
def test_non_finite_entry_and_targets_are_not_evaluable(field: str) -> None:
    values = {"entry": 100.0, "tp10": 110.0, "tp20": 120.0}
    values[field] = math.nan

    fields = compute_phase1_risk_fields(
        "breakout",
        _trade_levels(entry=values["entry"], tp10=values["tp10"], tp20=values["tp20"]),
        _risk_cfg(),
    )

    if field == "entry":
        assert fields["stop_price_initial"] is None
        assert fields["stop_source"] is None
        assert fields["risk_pct_to_stop"] is None
    else:
        assert fields["stop_price_initial"] == pytest.approx(96.0)
        assert fields["stop_source"] == "atr_fallback"
        assert fields["risk_pct_to_stop"] == pytest.approx(4.0)
    assert fields["rr_to_target_1"] is None
    assert fields["rr_to_target_2"] is None
    assert fields["risk_acceptable"] is None


def test_missing_risk_keys_use_defaults_in_compute() -> None:
    fields = compute_phase1_risk_fields("breakout", _trade_levels(), {"risk": {}})

    assert fields["stop_price_initial"] == pytest.approx(96.0)
    assert fields["stop_source"] == "atr_fallback"
    assert fields["risk_pct_to_stop"] == pytest.approx(4.0)
    assert fields["risk_acceptable"] is True


def test_invalid_risk_config_value_raises_clear_error() -> None:
    with pytest.raises(ValueError):
        compute_phase1_risk_fields("breakout", _trade_levels(), {"risk": {"atr_multiple": "invalid"}})


def test_validate_config_risk_missing_vs_invalid() -> None:
    base = {
        "general": {"run_mode": "offline"},
        "universe_filters": {"market_cap": {"min_usd": 1, "max_usd": 2}},
    }

    missing_errors = validate_config(ScannerConfig(raw=base))
    invalid_raw = dict(base)
    invalid_raw["risk"] = {"min_rr_to_tp10": "bad"}
    invalid_errors = validate_config(ScannerConfig(raw=invalid_raw))

    assert missing_errors == []
    assert any("risk.min_rr_to_tp10" in err for err in invalid_errors)


def test_breakout_result_preserves_invalidation_anchor_with_risk_fields() -> None:
    features = {
        "XUSDT": {
            "1d": {
                "close": 105.0,
                "breakout_dist_20": 5.0,
                "ema_20": 100.0,
                "ema_50": 98.0,
                "atr_pct": 2.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 3.0,
                "r_7": 3.0,
                "volume_spike": 2.0,
            },
            "4h": {"volume_spike": 1.8},
            "meta": {"last_closed_idx": {"1d": 40, "4h": 80}},
        }
    }

    rows = score_breakouts(
        features,
        {"XUSDT": 1_000_000},
        {
            "setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50},
            "risk": {
                "atr_multiple": 2.0,
                "min_stop_distance_pct": 4.0,
                "max_stop_distance_pct": 12.0,
                "min_rr_to_tp10": 1.3,
            },
        },
    )

    assert len(rows) == 1
    row = rows[0]
    assert row["invalidation_anchor_type"] == "breakout_level"
    assert row["invalidation_anchor_price"] == pytest.approx(100.0)
    assert row["invalidation_derivable"] is True
    assert row["risk_pct_to_stop"] == pytest.approx(4.2)
    assert row["risk_acceptable"] is False
