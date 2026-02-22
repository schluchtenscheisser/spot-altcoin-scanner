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


def test_percent_rank_helper_duplicates_nans_insufficient_history() -> None:
    engine = FeatureEngine({})

    assert np.isnan(engine._calc_percent_rank(np.array([np.nan, 1.0]), min_history=2))

    ranked = engine._calc_percent_rank(np.array([1.0, 1.0, 2.0, 2.0]))
    assert ranked == 83.33333333333334

    ranked_with_nans = engine._calc_percent_rank(np.array([1.0, np.nan, 3.0, 2.0]))
    assert ranked_with_nans == 50.0


def test_bollinger_width_series_matches_expected_last_value() -> None:
    engine = FeatureEngine({})
    closes = np.arange(1.0, 31.0, dtype=float)

    series = engine._calc_bollinger_width_series(closes, period=20, stddev=2.0)

    window = closes[-20:]
    middle = float(np.mean(window))
    sigma = float(np.std(window))
    expected = ((middle + 2.0 * sigma) - (middle - 2.0 * sigma)) / middle * 100.0
    assert series[-1] == expected


def test_volume_sma_periods_overrides_legacy_key_for_1d_and_4h() -> None:
    engine = FeatureEngine(
        {
            "features": {
                "volume_sma_periods": {"1d": 20, "4h": 20},
                "volume_sma_period": 7,
            }
        }
    )
    data = {
        "XUSDT": {
            "1d": _series(140, 86_400_000, 100.0, 0.2),
            "4h": _series(160, 14_400_000, 10.0, 0.05),
        }
    }

    features = engine.compute_all(data)["XUSDT"]

    assert features["1d"]["volume_sma_period"] == 20
    assert features["4h"]["volume_sma_period"] == 20
    assert "atr_pct_rank_120" in features["1d"]
    assert "bb_width_pct" in features["4h"]
    assert "bb_width_rank_120" in features["4h"]
