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
