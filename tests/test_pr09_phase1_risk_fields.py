import pytest

from scanner.pipeline.scoring.breakout import score_breakouts
from scanner.pipeline.scoring.trade_levels import compute_phase1_risk_fields


def test_compute_phase1_risk_fields_valid_breakout_path() -> None:
    trade_levels = {
        "entry_trigger": 100.0,
        "atr_value": 2.0,
        "targets": [102.0, 104.0, 106.0],
    }
    cfg = {
        "risk": {
            "atr_multiple": 2.0,
            "min_stop_distance_pct": 3.0,
            "max_stop_distance_pct": 6.0,
            "min_rr_to_tp10": 0.4,
        }
    }

    fields = compute_phase1_risk_fields("breakout", trade_levels, cfg)

    assert fields["stop_price_initial"] == pytest.approx(96.0)
    assert fields["risk_pct_to_stop"] == pytest.approx(4.0)
    assert fields["rr_to_target_1"] == pytest.approx(0.5)
    assert fields["rr_to_target_2"] == pytest.approx(1.0)
    assert fields["risk_acceptable"] is True


def test_compute_phase1_risk_fields_missing_and_invalid_are_nullable() -> None:
    cfg = {"risk": {"atr_multiple": 2.0}}

    missing = compute_phase1_risk_fields("breakout", {"entry_trigger": 100.0, "targets": [110.0, 120.0]}, cfg)
    invalid = compute_phase1_risk_fields("breakout", {"entry_trigger": 100.0, "atr_value": -1.0, "targets": [110.0, 120.0]}, cfg)

    for row in (missing, invalid):
        assert row["stop_price_initial"] is None
        assert row["risk_pct_to_stop"] is None
        assert row["rr_to_target_1"] is None
        assert row["rr_to_target_2"] is None
        assert row["risk_acceptable"] is None


def test_breakout_scoring_emits_phase1_risk_fields() -> None:
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

    result = score_breakouts(
        features,
        {"XUSDT": 1_000_000},
        {
            "setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50},
            "risk": {
                "atr_multiple": 2.0,
                "min_stop_distance_pct": 1.0,
                "max_stop_distance_pct": 10.0,
                "min_rr_to_tp10": 0.2,
            },
        },
    )

    assert len(result) == 1
    row = result[0]
    assert row["stop_price_initial"] == pytest.approx(95.8)
    assert row["risk_pct_to_stop"] == pytest.approx(4.2)
    assert row["rr_to_target_1"] == pytest.approx(0.5)
    assert row["rr_to_target_2"] == pytest.approx(1.0)
    assert row["risk_acceptable"] is True
