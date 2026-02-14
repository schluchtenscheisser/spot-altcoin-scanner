import pytest

from scanner.pipeline.scoring.breakout import BreakoutScorer
from scanner.pipeline.scoring.pullback import PullbackScorer


def test_breakout_score_piecewise_formula():
    scorer = BreakoutScorer(
        {
            "scoring": {
                "breakout": {
                    "min_breakout_pct": 2.0,
                    "ideal_breakout_pct": 5.0,
                    "max_breakout_pct": 20.0,
                    "breakout_curve": {"floor_pct": -5.0, "fresh_cap_pct": 1.0, "overextended_cap_pct": 3.0},
                }
            }
        }
    )

    assert scorer._score_breakout({"breakout_dist_20": None}) == pytest.approx(0.0)
    assert scorer._score_breakout({"breakout_dist_20": -5.0}) == pytest.approx(0.0)
    assert scorer._score_breakout({"breakout_dist_20": -2.5}) == pytest.approx(15.0)
    assert scorer._score_breakout({"breakout_dist_20": 1.0}) == pytest.approx(50.0)
    assert scorer._score_breakout({"breakout_dist_20": 3.5}) == pytest.approx(85.0)
    assert scorer._score_breakout({"breakout_dist_20": 10.0}) == pytest.approx(66.66666666666667)
    assert scorer._score_breakout({"breakout_dist_20": 25.0}) == pytest.approx(0.0)


def test_breakout_overextended_zone_flag_and_ema20_penalty():
    scorer = BreakoutScorer(
        {
            "scoring": {
                "breakout": {
                    "breakout_curve": {"overextended_cap_pct": 3.0},
                    "penalties": {
                        "max_overextension_ema20_percent": 10.0,
                        "overextension_factor": 0.5,
                        "low_liquidity_threshold": 100.0,
                        "low_liquidity_factor": 0.8,
                    },
                }
            }
        }
    )

    result = scorer.score(
        "XUSDT",
        {
            "1d": {"breakout_dist_20": 4.0, "dist_ema20_pct": 11.0, "dist_ema50_pct": 1.0, "r_7": 1.0, "volume_spike": 1.6},
            "4h": {"volume_spike": 1.0},
        },
        quote_volume_24h=200.0,
    )

    assert "overextended_breakout_zone" in result["flags"]
    assert "overextended" in result["flags"]
    assert result["penalties"]["overextension"] == pytest.approx(0.5)


def test_pullback_volume_prefers_quote_spike():
    scorer = PullbackScorer({"scoring": {"pullback": {"min_volume_spike": 1.3}}})

    # raw volume says 3.0 (would be 100), quote volume says 1.5 -> should use quote and produce lower score
    score = scorer._score_volume(
        {"volume_spike": 3.0, "volume_quote_spike": 1.5},
        {"volume_spike": 1.0, "volume_quote_spike": 1.4},
    )
    expected = ((1.5 - 1.3) / (2.0 - 1.3)) * 70.0
    assert score == pytest.approx(expected)
