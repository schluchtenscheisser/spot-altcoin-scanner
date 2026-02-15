import math

import pytest

from scanner.pipeline.features import FeatureEngine
from scanner.pipeline.scoring.breakout import BreakoutScorer
from scanner.pipeline.scoring.pullback import PullbackScorer
from scanner.pipeline.scoring.reversal import ReversalScorer


def test_reversal_base_uses_feature_engine_base_score_directly() -> None:
    scorer = ReversalScorer(config={})

    # base_detected should be ignored; base_score is canonical input.
    assert scorer._score_base({"base_detected": False, "base_score": 73.5}) == pytest.approx(73.5)
    assert scorer._score_base({"base_detected": True, "base_score": 110.0}) == pytest.approx(100.0)
    assert scorer._score_base({"base_detected": True, "base_score": -10.0}) == pytest.approx(0.0)
    assert scorer._score_base({"base_detected": True, "base_score": float("nan")}) == pytest.approx(0.0)
    assert scorer._score_base({"base_detected": True, "base_score": math.inf}) == pytest.approx(0.0)


def test_reversal_penalties_are_config_driven() -> None:
    cfg = {
        "scoring": {
            "reversal": {
                "penalties": {
                    "overextension_threshold_pct": 1,
                    "overextension_factor": 0.5,
                    "low_liquidity_threshold": 2_000_000,
                    "low_liquidity_factor": 0.9,
                }
            }
        }
    }
    scorer = ReversalScorer(cfg)

    result = scorer.score(
        symbol="TESTUSDT",
        features={
            "1d": {
                "drawdown_from_ath": -60.0,
                "base_score": 80.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 2.0,
                "hh_20": True,
                "r_7": 10.0,
                "volume_spike": 2.0,
            },
            "4h": {"volume_spike": 1.0},
        },
        quote_volume_24h=1_000_000,
    )

    assert result["penalties"]["overextension"] == pytest.approx(0.5)
    assert result["penalties"]["low_liquidity"] == pytest.approx(0.9)


def test_drawdown_uses_bounded_lookback() -> None:
    engine = FeatureEngine(config={"features": {"drawdown_lookback_days": 3}})

    # Full history ATH would be 100, but 3-day lookback ATH is 95.
    closes = [100.0, 90.0, 95.0, 94.0, 93.0]
    dd = engine._calc_drawdown(closes, lookback_bars=3)

    expected = ((93.0 / 95.0) - 1.0) * 100.0
    assert dd == pytest.approx(expected)


def test_breakout_momentum_is_continuous_linear_scaling() -> None:
    scorer = BreakoutScorer(config={"scoring": {"breakout": {"momentum": {"r7_divisor": 10}}}})

    assert scorer._score_momentum({"r_7": -1.0}) == pytest.approx(0.0)
    assert scorer._score_momentum({"r_7": 5.0}) == pytest.approx(50.0)
    assert scorer._score_momentum({"r_7": 10.0}) == pytest.approx(100.0)
    assert scorer._score_momentum({"r_7": 20.0}) == pytest.approx(100.0)


def test_pullback_rebound_includes_continuous_r7_component() -> None:
    scorer = PullbackScorer(config={"scoring": {"pullback": {"momentum": {"r7_divisor": 10}}}})

    # No step-based r3/r3_4h rebound, only r7 contributes via continuous term.
    rebound = scorer._score_rebound({"r_3": 0.0, "r_7": 5.0}, {"r_3": 0.0})
    assert rebound == pytest.approx(10.0)  # 0.2 * 50


def test_reversal_reasons_use_same_volume_spike_path_as_scoring() -> None:
    scorer = ReversalScorer(config={"scoring": {"reversal": {"min_volume_spike": 1.5}}})

    result = scorer.score(
        symbol="TESTUSDT",
        features={
            "1d": {
                "drawdown_from_ath": -60.0,
                "base_score": 80.0,
                "dist_ema20_pct": 1.0,
                "dist_ema50_pct": 1.0,
                "hh_20": True,
                "r_7": 0.0,
                # intentionally conflicting values to verify reason path matches scoring path
                "volume_spike": 5.0,
                "volume_quote_spike": 2.2,
            },
            "4h": {"volume_spike": 5.0, "volume_quote_spike": 1.2},
        },
        quote_volume_24h=2_000_000,
    )

    # scoring uses quote-based fallback path => max spike should be 2.2, not raw 5.0
    volume_reasons = [r for r in result["reasons"] if "volume" in r.lower()]
    assert any("2.2x" in r for r in volume_reasons)
    assert not any("5.0x" in r for r in volume_reasons)
