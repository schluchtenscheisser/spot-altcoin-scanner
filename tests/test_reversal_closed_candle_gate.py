from scanner.pipeline.scoring.reversal import score_reversals


def _features(meta):
    return {
        "TESTUSDT": {
            "1d": {
                "drawdown_from_ath": -60.0,
                "base_score": 70.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 2.5,
                "hh_20": True,
                "r_7": 5.0,
                "volume_quote_spike": 2.0,
            },
            "4h": {"volume_quote_spike": 2.0},
            "meta": meta,
            "quote_volume_24h": 2_000_000,
        }
    }


def test_reversal_history_gate_treats_none_as_insufficient_history():
    cfg = {"setup_validation": {"min_history_reversal_1d": 120, "min_history_reversal_4h": 80}}
    # missing 1d last_closed_idx -> _closed_candle_count(...) returns None
    features = _features({"last_closed_idx": {"4h": 100}})

    result = score_reversals(features, {"TESTUSDT": 2_000_000}, cfg)

    assert result == []


def test_reversal_history_gate_allows_boundary_min_history():
    cfg = {"setup_validation": {"min_history_reversal_1d": 120, "min_history_reversal_4h": 80}}
    # idx + 1 == min_history for both timeframes
    features = _features({"last_closed_idx": {"1d": 119, "4h": 79}})

    result = score_reversals(features, {"TESTUSDT": 2_000_000}, cfg)

    assert len(result) == 1
