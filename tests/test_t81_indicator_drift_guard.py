import numpy as np
import pytest

from scanner.pipeline.features import FeatureEngine


def test_t81_ema_reference_fixture_is_deterministic() -> None:
    engine = FeatureEngine(config={})

    closes = np.array([100.0, 102.0, 101.0, 105.0, 107.0, 106.0], dtype=float)
    ema = engine._calc_ema("TESTUSDT", closes, period=4)

    # period=4
    # seed SMA=(100+102+101+105)/4 = 102.0
    # alpha=2/(4+1)=0.4
    # t=4: 0.4*107 + 0.6*102 = 104.0
    # t=5: 0.4*106 + 0.6*104 = 104.8
    assert ema == pytest.approx(104.8, rel=1e-12, abs=1e-12)


def test_t81_atr_reference_fixture_is_deterministic() -> None:
    engine = FeatureEngine(config={})

    highs = np.array([101.0, 104.0, 106.0, 107.0, 108.0], dtype=float)
    lows = np.array([99.0, 100.0, 102.0, 104.0, 105.0], dtype=float)
    closes = np.array([100.0, 102.0, 104.0, 106.0, 107.0], dtype=float)

    atr_pct = engine._calc_atr_pct("TESTUSDT", highs, lows, closes, period=3)

    # TR t=1..4: [4, 4, 3, 3]
    # ATR seed (period=3): mean([4,4,3]) = 11/3
    # Wilder step: ((11/3)*2 + 3) / 3 = 31/9
    # ATR%: (31/9)/107*100 = 3100 / 963 ~= 3.2191069574247138
    assert atr_pct == pytest.approx(3.2191069574247138, rel=1e-12, abs=1e-12)


def test_t81_ema_short_series_returns_nan() -> None:
    engine = FeatureEngine(config={})
    closes = np.array([1.0, 2.0, 3.0], dtype=float)

    ema = engine._calc_ema("TESTUSDT", closes, period=5)

    assert np.isnan(ema)


def test_t81_atr_short_series_and_zero_close_return_nan() -> None:
    engine = FeatureEngine(config={})

    highs_short = np.array([10.0, 11.0, 12.0], dtype=float)
    lows_short = np.array([9.0, 10.0, 11.0], dtype=float)
    closes_short = np.array([9.5, 10.5, 11.5], dtype=float)
    atr_short = engine._calc_atr_pct("TESTUSDT", highs_short, lows_short, closes_short, period=3)
    assert np.isnan(atr_short)

    highs = np.array([10.0, 11.0, 12.0, 13.0], dtype=float)
    lows = np.array([9.0, 10.0, 11.0, 12.0], dtype=float)
    closes_zero = np.array([9.5, 10.5, 11.5, 0.0], dtype=float)
    atr_zero_close = engine._calc_atr_pct("TESTUSDT", highs, lows, closes_zero, period=3)
    assert np.isnan(atr_zero_close)
