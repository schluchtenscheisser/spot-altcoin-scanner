import pytest

from scanner.pipeline.scoring.breakout import BreakoutScorer
from scanner.pipeline.scoring.pullback import PullbackScorer
from scanner.pipeline.scoring.reversal import ReversalScorer


def test_breakout_canonical_weights_are_used_without_renormalization() -> None:
    scorer = BreakoutScorer(
        {
            "scoring": {
                "breakout": {
                    "weights": {
                        "breakout": 0.40,
                        "volume": 0.30,
                        "trend": 0.20,
                        "momentum": 0.10,
                    }
                }
            }
        }
    )

    assert scorer.weights == pytest.approx({"breakout": 0.40, "volume": 0.30, "trend": 0.20, "momentum": 0.10})


def test_legacy_alias_weights_map_to_canonical_keys() -> None:
    scorer = PullbackScorer(
        {
            "scoring": {
                "pullback": {
                    "weights": {
                        "trend_quality": 0.25,
                        "pullback_quality": 0.25,
                        "rebound_signal": 0.25,
                        "volume": 0.25,
                    }
                }
            }
        }
    )

    assert scorer.weights == pytest.approx({"trend": 0.25, "pullback": 0.25, "rebound": 0.25, "volume": 0.25})


def test_invalid_weight_sum_uses_defaults_without_silent_renormalization() -> None:
    scorer = ReversalScorer(
        {
            "scoring": {
                "reversal": {
                    "weights": {
                        "drawdown": 2.0,
                        "base": 0.0,
                        "reclaim": 0.0,
                        "volume": 0.0,
                    }
                }
            }
        }
    )

    assert scorer.weights == pytest.approx({"drawdown": 0.30, "base": 0.25, "reclaim": 0.25, "volume": 0.20})


def test_strict_mode_requires_all_canonical_keys() -> None:
    scorer = BreakoutScorer(
        {
            "scoring": {
                "breakout": {
                    "weights_mode": "strict",
                    "weights": {
                        "price_break": 0.4,
                        "volume": 0.3,
                        "trend": 0.2,
                        "momentum": 0.1,
                    },
                }
            }
        }
    )

    assert scorer.weights == pytest.approx({"breakout": 0.35, "volume": 0.30, "trend": 0.20, "momentum": 0.15})
