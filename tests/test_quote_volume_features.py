import numpy as np

from scanner.pipeline.features import FeatureEngine


def test_quote_volume_features_return_none_when_unavailable() -> None:
    engine = FeatureEngine(config={})
    qv = np.array([np.nan, np.nan, np.nan], dtype=float)

    actual = engine._calc_quote_volume_features("TESTUSDT", qv, period=14)

    assert actual == {
        "volume_quote": None,
        "volume_quote_sma": None,
        "volume_quote_spike": None,
        "volume_quote_sma_14": None,
    }


def test_quote_volume_features_use_baseline_excluding_current() -> None:
    engine = FeatureEngine(config={})
    qv = np.array([100.0 + i * 10.0 for i in range(14)] + [1000.0], dtype=float)

    actual = engine._calc_quote_volume_features("TESTUSDT", qv, period=14)

    expected_baseline = float(np.mean(qv[-15:-1]))
    expected_spike = float(qv[-1] / expected_baseline)

    assert actual["volume_quote"] == qv[-1]
    assert actual["volume_quote_sma"] == expected_baseline
    assert actual["volume_quote_sma_14"] == expected_baseline
    assert actual["volume_quote_spike"] == expected_spike
