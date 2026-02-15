import numpy as np
import pytest

from scanner.pipeline.features import FeatureEngine


def test_drawdown_lookback_days_are_converted_to_timeframe_bars() -> None:
    engine = FeatureEngine(config={})

    assert engine._lookback_days_to_bars(7, "1d") == 7
    assert engine._lookback_days_to_bars(7, "4h") == 42
    assert engine._lookback_days_to_bars(1, "90m") == 16  # ceil(24h / 1.5h)


def test_drawdown_semantics_match_between_1d_and_4h_for_same_day_window() -> None:
    engine = FeatureEngine(config={})
    lookback_days = 2

    closes_1d = np.array([100.0, 95.0, 90.0], dtype=float)
    dd_1d = engine._calc_drawdown(closes_1d, lookback_bars=engine._lookback_days_to_bars(lookback_days, "1d"))

    # 4h: 6 candles/day, last 12 candles (2 days) all <=95, final close=90
    closes_4h = np.array([100.0] + [95.0] * 11 + [90.0], dtype=float)
    dd_4h = engine._calc_drawdown(closes_4h, lookback_bars=engine._lookback_days_to_bars(lookback_days, "4h"))

    expected = ((90.0 / 95.0) - 1.0) * 100.0
    assert dd_1d == pytest.approx(expected)
    assert dd_4h == pytest.approx(expected)
