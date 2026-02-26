from scanner.pipeline.scoring.pullback import score_pullbacks


def _features(meta):
    return {
        "TESTUSDT": {
            "1d": {
                "dist_ema20_pct": 1.5,
                "dist_ema50_pct": 2.0,
                "r_3": 4.0,
                "r_7": 5.0,
                "hh_20": True,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
            },
            "4h": {
                "r_3": 2.5,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
            },
            "meta": meta,
            "quote_volume_24h": 2_000_000,
        }
    }


def test_pullback_history_gate_treats_none_as_insufficient_history():
    cfg = {"setup_validation": {"min_history_pullback_1d": 60, "min_history_pullback_4h": 80}}
    # missing 4h last_closed_idx -> _closed_candle_count(...) returns None
    features = _features({"last_closed_idx": {"1d": 120}})

    result = score_pullbacks(features, {"TESTUSDT": 2_000_000}, cfg)

    assert result == []


def test_pullback_history_gate_allows_boundary_min_history():
    cfg = {"setup_validation": {"min_history_pullback_1d": 60, "min_history_pullback_4h": 80}}
    # idx + 1 == min_history for both timeframes
    features = _features({"last_closed_idx": {"1d": 59, "4h": 79}})

    result = score_pullbacks(features, {"TESTUSDT": 2_000_000}, cfg)

    assert len(result) == 1
