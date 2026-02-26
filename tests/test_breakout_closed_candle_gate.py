from scanner.pipeline.scoring.breakout import score_breakouts


def _features(meta):
    return {
        "TESTUSDT": {
            "1d": {
                "breakout_dist_20": 3.0,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 3.0,
                "r_7": 5.0,
            },
            "4h": {
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
            },
            "meta": meta,
            "quote_volume_24h": 2_000_000,
        }
    }


def test_breakout_history_gate_treats_none_as_insufficient_history():
    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    # missing 1d last_closed_idx -> _closed_candle_count(...) returns None
    features = _features({"last_closed_idx": {"4h": 100}})

    result = score_breakouts(features, {"TESTUSDT": 2_000_000}, cfg)

    assert result == []


def test_breakout_history_gate_allows_boundary_min_history():
    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    # idx + 1 == min_history for both timeframes
    features = _features({"last_closed_idx": {"1d": 29, "4h": 49}})

    result = score_breakouts(features, {"TESTUSDT": 2_000_000}, cfg)

    assert len(result) == 1
