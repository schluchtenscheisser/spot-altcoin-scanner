import logging

import numpy as np

from scanner.pipeline.features import FeatureEngine


def _kline(i: int, step_ms: int, close: float) -> list[float]:
    ts = 1_700_000_000_000 + (i * step_ms)
    high = close * 1.01
    low = close * 0.99
    open_ = close * 0.995
    vol = 1000 + (i * 10)
    close_time = ts + step_ms - 1
    quote = vol * close
    return [ts, open_, high, low, close, vol, close_time, quote]


def _series(n: int, step_ms: int, start: float, inc: float) -> list[list[float]]:
    return [_kline(i, step_ms, start + (i * inc)) for i in range(n)]


def test_atr_pct_series_matches_single_value_at_end() -> None:
    engine = FeatureEngine({})
    period = 14

    closes = np.linspace(100.0, 180.0, 30, dtype=float)
    highs = closes * 1.02
    lows = closes * 0.98

    atr_pct_series = engine._calc_atr_pct_series(highs, lows, closes, period)
    single = engine._calc_atr_pct("TESTUSDT", highs, lows, closes, period)

    assert np.all(np.isnan(atr_pct_series[:period]))
    assert atr_pct_series[-1] == single


def test_compute_timeframe_features_no_repeated_atr14_warmup_warning(caplog) -> None:
    engine = FeatureEngine({})
    klines_1d = _series(60, 86_400_000, 100.0, 0.5)

    with caplog.at_level(logging.WARNING):
        result = engine._compute_timeframe_features(klines_1d, "1d", "TESTUSDT")

    assert "atr_pct" in result
    atr_warnings = [
        rec.message for rec in caplog.records if "insufficient candles for ATR14" in rec.message
    ]
    assert len(atr_warnings) == 0


def test_atr_pct_series_invalid_high_low_ordering_keeps_series_non_negative() -> None:
    engine = FeatureEngine({})

    closes = np.array([100.0, 102.0, 101.0, 103.0, 104.0, 105.0], dtype=float)
    highs = np.array([101.0, 103.0, 102.0, 100.0, 105.0, 106.0], dtype=float)
    lows = np.array([99.0, 100.0, 99.5, 101.0, 102.0, 103.0], dtype=float)

    atr_pct_series = engine._calc_atr_pct_series(highs, lows, closes, period=3)

    assert np.all(np.isnan(atr_pct_series) | (atr_pct_series >= 0.0))


def test_percent_rank_handles_nans_with_min_history_semantics() -> None:
    engine = FeatureEngine({})

    rank_with_enough_history = engine._calc_percent_rank(np.array([1.0, np.nan, 2.0, 3.0], dtype=float))
    rank_with_insufficient_history = engine._calc_percent_rank(np.array([np.nan, 5.0], dtype=float))

    assert np.isfinite(rank_with_enough_history)
    assert np.isnan(rank_with_insufficient_history)


def test_atr_pct_series_early_nan_does_not_kill_later_values() -> None:
    engine = FeatureEngine({})

    closes = np.array([100.0, 101.0, 102.0, 103.0, 105.0, 106.0, 108.0, 110.0], dtype=float)
    highs = closes + 2.0
    lows = closes - 2.0
    highs[2] = np.nan

    atr_pct_series = engine._calc_atr_pct_series(highs, lows, closes, period=3)

    assert np.isnan(atr_pct_series[:3]).all()
    assert np.isfinite(atr_pct_series[-1])
    assert np.all(np.isnan(atr_pct_series) | (atr_pct_series >= 0.0))


def test_atr_pct_series_last_value_matches_scalar_with_partial_nans() -> None:
    engine = FeatureEngine({})

    closes = np.array([100.0, 101.0, 102.0, 103.0, 105.0, 106.0, 108.0, 110.0], dtype=float)
    highs = closes + 2.0
    lows = closes - 2.0
    highs[2] = np.nan

    scalar = engine._calc_atr_pct("TESTUSDT", highs, lows, closes, period=3)
    series_last = engine._calc_atr_pct_series(highs, lows, closes, period=3)[-1]

    if np.isfinite(scalar):
        assert series_last == scalar
    else:
        assert np.isnan(series_last)


def test_percent_rank_computable_with_mixed_nan_window() -> None:
    engine = FeatureEngine({})

    window = np.array([np.nan, 3.0, np.nan, 5.0, 4.0], dtype=float)
    rank = engine._calc_percent_rank(window)

    assert np.isfinite(rank)
