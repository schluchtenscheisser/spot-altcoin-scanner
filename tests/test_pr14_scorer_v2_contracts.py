import copy

import pytest

from scanner.pipeline.scoring.breakout import BreakoutScorer
from scanner.pipeline.scoring.pullback import PullbackScorer
from scanner.pipeline.scoring.reversal import ReversalScorer


def test_breakout_v2_not_confirmed_when_close_is_below_breakout_level() -> None:
    scorer = BreakoutScorer({})

    result = scorer.score(
        "X",
        {
            "1d": {
                "close": 99.0,
                "breakout_dist_20": -1.0,
                "dist_ema20_pct": 0.1,
                "dist_ema50_pct": 0.5,
                "r_7": 1.0,
                "volume_spike": 1.6,
            },
            "4h": {"volume_spike": 1.4},
        },
        quote_volume_24h=1_000_000.0,
    )

    assert result["breakout_confirmed"] is False
    assert result["entry_ready"] is False
    assert result["entry_readiness_reasons"] == ["breakout_not_confirmed"]


def test_pullback_v2_retest_reclaimed_false_when_rebound_is_not_confirmed() -> None:
    scorer = PullbackScorer({})

    result = scorer.score(
        "X",
        {
            "1d": {
                "dist_ema20_pct": -0.5,
                "dist_ema50_pct": 0.2,
                "hh_20": True,
                "r_3": 2.9,
                "r_7": 0.5,
                "volume_spike": 1.4,
            },
            "4h": {"r_3": 2.8, "volume_spike": 1.3},
        },
        quote_volume_24h=1_000_000.0,
    )

    assert result["rebound_confirmed"] is False
    assert result["retest_reclaimed"] is False
    assert result["entry_ready"] is False
    assert result["entry_readiness_reasons"] == ["rebound_not_confirmed"]


def test_reversal_v2_without_reclaim_is_not_entry_ready_and_has_reason_key() -> None:
    scorer = ReversalScorer({})

    result = scorer.score(
        "X",
        {
            "1d": {
                "drawdown_from_ath": -60.0,
                "base_score": 80.0,
                "dist_ema20_pct": -0.3,
                "dist_ema50_pct": -0.1,
                "hh_20": False,
                "r_7": -0.2,
                "volume_spike": 2.0,
            },
            "4h": {"volume_spike": 2.0},
        },
        quote_volume_24h=2_000_000.0,
    )

    assert result["reclaim_confirmed"] is False
    assert result["retest_reclaimed"] is False
    assert result["entry_ready"] is False
    assert "retest_not_reclaimed" in result["entry_readiness_reasons"]


@pytest.mark.parametrize(
    "scorer,features,volume",
    [
        (
            BreakoutScorer({}),
            {
                "1d": {
                    "close": 99.5,
                    "breakout_dist_20": -0.5,
                    "dist_ema20_pct": 0.2,
                    "dist_ema50_pct": 0.4,
                    "r_7": 0.4,
                    "volume_spike": 1.0,
                },
                "4h": {"volume_spike": 1.0},
            },
            1_000_000.0,
        ),
        (
            PullbackScorer({}),
            {
                "1d": {
                    "dist_ema20_pct": -0.5,
                    "dist_ema50_pct": 0.1,
                    "hh_20": True,
                    "r_3": 1.0,
                    "r_7": 0.5,
                    "volume_spike": 1.2,
                },
                "4h": {"r_3": 1.1, "volume_spike": 1.1},
            },
            1_000_000.0,
        ),
        (
            ReversalScorer({}),
            {
                "1d": {
                    "drawdown_from_ath": -50.0,
                    "base_score": 70.0,
                    "dist_ema20_pct": -0.3,
                    "dist_ema50_pct": -0.1,
                    "hh_20": False,
                    "r_7": -0.2,
                    "volume_spike": 1.5,
                },
                "4h": {"volume_spike": 1.5},
            },
            1_000_000.0,
        ),
    ],
)
def test_not_entry_ready_outputs_have_non_empty_reason_lists(scorer, features, volume) -> None:
    result = scorer.score("X", features, quote_volume_24h=volume)

    assert result["entry_ready"] is False
    assert result["entry_readiness_reasons"]


def test_pullback_v2_uses_default_min_rebound_when_key_is_missing() -> None:
    scorer = PullbackScorer({"scoring": {"pullback": {}}})

    below = scorer.score(
        "X",
        {
            "1d": {"dist_ema20_pct": 0.0, "dist_ema50_pct": 0.0, "hh_20": True, "r_3": 2.99, "r_7": 0.0, "volume_spike": 1.5},
            "4h": {"r_3": 2.5, "volume_spike": 1.4},
        },
        quote_volume_24h=1_000_000.0,
    )
    at_threshold = scorer.score(
        "X",
        {
            "1d": {"dist_ema20_pct": 0.0, "dist_ema50_pct": 0.0, "hh_20": True, "r_3": 3.0, "r_7": 0.0, "volume_spike": 1.5},
            "4h": {"r_3": 2.5, "volume_spike": 1.4},
        },
        quote_volume_24h=1_000_000.0,
    )

    assert below["rebound_confirmed"] is False
    assert at_threshold["rebound_confirmed"] is True


def test_pullback_invalid_min_rebound_value_raises_clear_error() -> None:
    with pytest.raises(ValueError):
        PullbackScorer({"scoring": {"pullback": {"min_rebound": "invalid-number"}}})


def test_setup_scorer_v2_outputs_are_deterministic_for_identical_input() -> None:
    scorer = ReversalScorer({"scoring": {"reversal": {"min_volume_spike": 1.5}}})
    features = {
        "1d": {
            "drawdown_from_ath": -55.0,
            "base_score": 75.0,
            "dist_ema20_pct": -0.1,
            "dist_ema50_pct": -0.1,
            "hh_20": False,
            "r_7": 0.0,
            "volume_spike": 1.8,
        },
        "4h": {"volume_spike": 1.7},
    }

    first = scorer.score("X", copy.deepcopy(features), quote_volume_24h=1_000_000.0)
    second = scorer.score("X", copy.deepcopy(features), quote_volume_24h=1_000_000.0)

    assert first == second
