import numpy as np

from scanner.pipeline.features import FeatureEngine


from scanner.pipeline.scoring.breakout_trend_1_5d import score_breakout_trend_1_5d


def test_timeframe_features_emit_native_ohlc_series_and_align_with_scalars() -> None:
    engine = FeatureEngine({})
    data = {
        "XUSDT": {
            "1d": _series(80, 86_400_000, 100.0, 0.5),
            "4h": _series(160, 14_400_000, 20.0, 0.1),
        }
    }

    features = engine.compute_all(data)["XUSDT"]
    for timeframe in ("1d", "4h"):
        tf = features[timeframe]
        assert isinstance(tf["close_series"], list)
        assert isinstance(tf["high_series"], list)
        assert isinstance(tf["low_series"], list)
        assert len(tf["close_series"]) == features["meta"]["last_closed_idx"][timeframe] + 1
        assert len(tf["high_series"]) == len(tf["close_series"])
        assert len(tf["low_series"]) == len(tf["close_series"])
        assert tf["close"] == tf["close_series"][-1]
        assert tf["high"] == tf["high_series"][-1]
        assert tf["low"] == tf["low_series"][-1]


def test_timeframe_features_keep_insufficient_history_behavior_without_series() -> None:
    engine = FeatureEngine({})

    features = engine.compute_all({"XUSDT": {"1d": _series(49, 86_400_000, 100.0, 0.3)}})["XUSDT"]

    assert features["1d"] == {}


def test_breakout_trend_scorer_consumes_real_feature_engine_series() -> None:
    engine = FeatureEngine({})

    data_1d = _series(80, 86_400_000, 80.0, 0.4)
    high_20_ex_current = max(k[2] for k in data_1d[-21:-1])

    data_4h = _series(160, 14_400_000, 60.0, 0.05)
    for i in range(140, 160):
        close = high_20_ex_current + 1.5 + (i - 140) * 0.1
        data_4h[i] = _kline(i, 14_400_000, close)

    features = engine.compute_all({"BRKUSDT": {"1d": data_1d, "4h": data_4h}})

    rows = score_breakout_trend_1_5d(
        features,
        {"BRKUSDT": 30_000_000.0},
        {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}},
        btc_regime={"state": "RISK_ON"},
    )

    assert rows
    assert any(row["setup_id"] == "breakout_immediate_1_5d" for row in rows)


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
