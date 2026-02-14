from scanner.pipeline.features import FeatureEngine


def _gen_klines(n: int, step_ms: int, with_quote: bool = True):
    out = []
    start_ts = 1_700_000_000_000
    for i in range(n):
        c = 100 + i
        v = 1000 + i * 10
        qv = 2000 + i * 20
        row = [start_ts + i * step_ms, c * 0.99, c * 1.01, c * 0.98, c, v, start_ts + (i + 1) * step_ms - 1]
        if with_quote:
            row.append(qv)
        out.append(row)
    return out


def test_timeframe_specific_volume_periods_are_used():
    engine = FeatureEngine({"features": {"volume_sma_periods": {"1d": 14, "4h": 7}}})
    data = {"XUSDT": {"1d": _gen_klines(60, 86_400_000), "4h": _gen_klines(60, 14_400_000)}}

    result = engine.compute_all(data)["XUSDT"]

    assert result["1d"]["volume_sma_period"] == 14
    assert result["4h"]["volume_sma_period"] == 7
    assert result["1d"]["volume_sma"] is not None
    assert result["4h"]["volume_sma"] is not None
    assert result["1d"]["volume_quote_sma"] is not None
    assert result["4h"]["volume_quote_sma"] is not None


def test_legacy_volume_period_fallback_applies_to_all_timeframes():
    engine = FeatureEngine({"features": {"volume_sma_period": 9}})
    data = {"XUSDT": {"1d": _gen_klines(60, 86_400_000), "4h": _gen_klines(60, 14_400_000)}}

    result = engine.compute_all(data)["XUSDT"]

    assert result["1d"]["volume_sma_period"] == 9
    assert result["4h"]["volume_sma_period"] == 9


def test_volume_spike_fallback_to_one_when_baseline_invalid():
    engine = FeatureEngine({"features": {"volume_sma_periods": {"1d": 1000}}})
    data = {"XUSDT": {"1d": _gen_klines(60, 86_400_000, with_quote=False)}}

    result = engine.compute_all(data)["XUSDT"]["1d"]

    assert result["volume_sma"] is None
    assert result["volume_spike"] == 1.0
    assert result["volume_quote_sma"] is None
    assert result["volume_quote_spike"] is None
