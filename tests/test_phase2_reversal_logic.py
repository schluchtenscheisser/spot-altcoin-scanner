import pytest

from scanner.pipeline.features import FeatureEngine
from scanner.pipeline.scoring.reversal import ReversalScorer, score_reversals


def _gen_1d_klines_with_base(pass_condition: bool) -> list[list[float]]:
    rows = []
    start_ts = 1_700_000_000_000
    lookback = 45
    # older segment: 50 candles around low~80
    for i in range(50):
        close = 90 + i * 0.2
        low = 80.0 if i == 20 else close - 2
        high = close + 2
        vol = 1_000 + i
        rows.append([start_ts + i * 86_400_000, close * 0.99, high, low, close, vol, start_ts + (i + 1) * 86_400_000 - 1, vol * close])

    # recent segment: 10 candles
    for j in range(10):
        close = 98.0 + (0.05 * j)  # tight range
        if pass_condition:
            low = 78.0 + (0.02 * j)  # within tolerance for base_low=80 and tol=3% => threshold 77.6
        else:
            low = 76.5 - (0.02 * j)  # breaks base low tolerance
        high = close + 1.0
        vol = 1_200 + j
        idx = 50 + j
        rows.append([start_ts + idx * 86_400_000, close * 0.99, high, low, close, vol, start_ts + (idx + 1) * 86_400_000 - 1, vol * close])
    return rows


def test_feature_engine_phase2_base_score_pass_and_debug_fields():
    cfg = {
        "scoring": {
            "reversal": {
                "base_lookback_days": 45,
                "min_base_days_without_new_low": 10,
                "max_allowed_new_low_percent_vs_base_low": 3,
            }
        }
    }
    engine = FeatureEngine(cfg)
    out = engine.compute_all({"XUSDT": {"1d": _gen_1d_klines_with_base(True)}})["XUSDT"]["1d"]

    assert out["base_no_new_lows_pass"] is True
    assert out["base_score"] > 60
    assert out["base_low"] is not None
    assert out["base_recent_low"] is not None
    assert out["base_range_pct"] is not None


def test_feature_engine_phase2_base_score_fail_on_new_lows():
    cfg = {
        "scoring": {
            "reversal": {
                "base_lookback_days": 45,
                "min_base_days_without_new_low": 10,
                "max_allowed_new_low_percent_vs_base_low": 3,
            }
        }
    }
    engine = FeatureEngine(cfg)
    out = engine.compute_all({"XUSDT": {"1d": _gen_1d_klines_with_base(False)}})["XUSDT"]["1d"]

    assert out["base_no_new_lows_pass"] is False
    assert out["base_score"] == pytest.approx(0.0)


def test_reversal_drawdown_score_piecewise_and_volume_quote_preferred():
    scorer = ReversalScorer(
        {
            "scoring": {
                "reversal": {
                    "min_drawdown_pct": 40,
                    "ideal_drawdown_min": 50,
                    "ideal_drawdown_max": 80,
                    "min_volume_spike": 1.5,
                }
            }
        }
    )

    # dd=45 => between min and ideal_min -> score 75
    assert scorer._score_drawdown({"drawdown_from_ath": -45}) == pytest.approx(75.0)
    # dd=90 => excess=10 -> penalty=0.5 max? actually 10/20=0.5 -> score 50
    assert scorer._score_drawdown({"drawdown_from_ath": -90}) == pytest.approx(50.0)

    vol = scorer._score_volume(
        {"volume_spike": 3.0, "volume_quote_spike": 1.6},
        {"volume_spike": 1.0, "volume_quote_spike": 2.0},
    )
    # preferred quote spikes => max=2.0, not 3.0
    expected = ((2.0 - 1.5) / (3.0 - 1.5)) * 100.0
    assert vol == pytest.approx(expected)


def test_reversal_setup_payload_propagates_raw_score_and_penalty_multiplier() -> None:
    features = {
        "XUSDT": {
            "1d": {
                "drawdown_from_ath": -60.0,
                "base_detected": True,
                "base_score": 80.0,
                "reclaim_ema50": True,
                "dist_ema50_pct": 1.0,
                "volume_spike": 1.7,
            },
            "4h": {"volume_spike": 1.6},
            "meta": {"last_closed_idx": {"1d": 200, "4h": 200}},
        }
    }
    volumes = {"XUSDT": 2_000_000.0}

    results = score_reversals(features, volumes, {})

    assert "raw_score" in results[0]
    assert "penalty_multiplier" in results[0]
