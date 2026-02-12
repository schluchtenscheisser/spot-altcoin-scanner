import numpy as np
import pytest

from scanner.pipeline.features import FeatureEngine


def test_baselines_exclude_current_candle() -> None:
    """Thema 6 invariant: baseline windows must exclude current candle (idx T)."""
    engine = FeatureEngine(config={})

    # volume baseline (period=3): use [20, 30, 40], exclude current=100
    volumes = np.array([10.0, 20.0, 30.0, 40.0, 100.0], dtype=float)
    baseline = engine._calc_sma(volumes, 3, include_current=False)
    assert baseline == pytest.approx((20.0 + 30.0 + 40.0) / 3.0, rel=1e-12, abs=1e-12)

    # breakout resistance (lookback=3): prior highs [11, 12, 13], current high=20 must be excluded
    closes = np.array([9.5, 10.5, 11.5, 12.5, 14.0], dtype=float)
    highs = np.array([10.0, 11.0, 12.0, 13.0, 20.0], dtype=float)
    breakout_dist = engine._calc_breakout_distance("TESTUSDT", closes, highs, 3)
    expected = ((14.0 / 13.0) - 1.0) * 100.0
    assert breakout_dist == pytest.approx(expected, rel=1e-12, abs=1e-12)
