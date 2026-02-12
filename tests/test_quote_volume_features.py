import numpy as np

from scanner.pipeline.features import FeatureEngine


def test_quote_volume_features_return_nan_when_unavailable() -> None:
    engine = FeatureEngine(config={})
    qv = np.array([np.nan, np.nan, np.nan], dtype=float)

    actual = engine._calc_quote_volume_features("TESTUSDT", qv)

    assert actual["volume_quote"] is None or np.isnan(actual["volume_quote"])
    assert actual["volume_quote_sma_14"] is None or np.isnan(actual["volume_quote_sma_14"])
    assert actual["volume_quote_spike"] is None or np.isnan(actual["volume_quote_spike"])


def test_quote_volume_features_use_baseline_excluding_current() -> None:
    engine = FeatureEngine(config={})
    # 15 candles so period=14 baseline exists; last value is current candle and must be excluded from baseline
    qv = np.array([100.0 + i * 10.0 for i in range(14)] + [1000.0], dtype=float)

    actual = engine._calc_quote_volume_features("TESTUSDT", qv)

    expected_baseline = float(np.mean(qv[-15:-1]))
    expected_spike = float(qv[-1] / expected_baseline)

    assert actual["volume_quote"] == qv[-1]
    assert actual["volume_quote_sma_14"] == expected_baseline
    assert actual["volume_quote_spike"] == expected_spike
