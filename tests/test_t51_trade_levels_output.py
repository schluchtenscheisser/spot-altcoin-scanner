import pytest

from scanner.pipeline.scoring.trade_levels import (
    breakout_trade_levels,
    pullback_trade_levels,
    reversal_trade_levels,
)
from scanner.pipeline.scoring.breakout import score_breakouts


def test_breakout_trade_levels_include_breakout_level_20_and_targets():
    features = {
        "1d": {
            "close": 105.0,
            "breakout_dist_20": 5.0,
            "ema_20": 100.0,
            "atr_pct": 2.0,
        }
    }

    levels = breakout_trade_levels(features, [1.0, 2.0, 3.0])

    assert levels["breakout_level_20"] == pytest.approx(100.0)
    assert levels["entry_trigger"] == pytest.approx(100.0)
    assert levels["invalidation"] == pytest.approx(100.0)
    assert levels["targets"] == pytest.approx([102.1, 104.2, 106.3])


def test_pullback_trade_levels_zone_and_invalidation_are_deterministic():
    features = {
        "4h": {
            "ema_20": 50.0,
            "ema_50": 47.0,
            "close": 51.0,
            "atr_pct": 4.0,
        }
    }

    levels = pullback_trade_levels(features, [1.0, 2.0], pb_tol_pct=1.0)

    assert levels["entry_zone"]["center"] == pytest.approx(50.0)
    assert levels["entry_zone"]["lower"] == pytest.approx(49.5)
    assert levels["entry_zone"]["upper"] == pytest.approx(50.5)
    assert levels["invalidation"] == pytest.approx(47.0)
    assert levels["targets"] == pytest.approx([52.04, 54.08])


def test_reversal_trade_levels_uses_ema20_and_base_low():
    features = {
        "1d": {
            "ema_20": 10.0,
            "base_low": 8.5,
            "close": 10.5,
            "atr_pct": 10.0,
        }
    }

    levels = reversal_trade_levels(features, [1.0, 3.0])

    assert levels["entry_trigger"] == pytest.approx(10.0)
    assert levels["invalidation"] == pytest.approx(8.5)
    assert levels["targets"] == pytest.approx([11.05, 13.15])


def test_breakout_scoring_output_contains_trade_levels_without_score_change():
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
    result = score_breakouts(features, {"XUSDT": 1_000_000}, {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}})
    assert len(result) == 1
    assert result[0]["score"] > 0
    assert "analysis" in result[0]
    assert "trade_levels" in result[0]["analysis"]
    assert result[0]["analysis"]["trade_levels"]["breakout_level_20"] == pytest.approx(100.0)
