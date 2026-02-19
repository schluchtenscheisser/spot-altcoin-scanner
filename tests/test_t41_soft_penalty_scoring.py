from scanner.pipeline.scoring.breakout import score_breakouts


def test_minor_unlock_soft_penalty_reduces_score():
    features = {
        "AAAUSDT": {
            "1d": {
                "breakout_dist_20": 3.0,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 1.0,
                "dist_ema50_pct": 2.0,
                "r_7": 5.0,
                "hh_20": True,
                "hl_20": True,
            },
            "4h": {"volume_spike": 2.0, "volume_quote_spike": 2.0, "dist_ema20_pct": 1.0, "r_1": 1.0},
            "meta": {"last_closed_idx": {"1d": 100, "4h": 100}},
            "soft_penalties": {"minor_unlock_within_14d": 0.8},
            "risk_flags": ["minor_unlock_within_14d"],
        }
    }

    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    result = score_breakouts(features, {"AAAUSDT": 1_000_000}, cfg)

    assert len(result) == 1
    assert result[0]["penalty_multiplier"] < 1.0
    assert "minor_unlock_within_14d" in result[0]["penalties"]
    assert result[0]["risk_flags"] == ["minor_unlock_within_14d"]
