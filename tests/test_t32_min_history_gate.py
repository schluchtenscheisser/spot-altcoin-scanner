from scanner.pipeline.scoring.breakout import score_breakouts
from scanner.pipeline.scoring.pullback import score_pullbacks
from scanner.pipeline.scoring.reversal import score_reversals


def _base_features(last_closed_1d: int, last_closed_4h: int):
    return {
        "TESTUSDT": {
            "1d": {
                "breakout_dist_20": 3.0,
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 2.0,
                "dist_ema50_pct": 3.0,
                "r_7": 5.0,
                "drawdown_from_ath": -55.0,
                "base_score": 80.0,
                "hh_20": True,
                "hl_20": True,
            },
            "4h": {
                "volume_spike": 2.0,
                "volume_quote_spike": 2.0,
                "dist_ema20_pct": 1.0,
                "dist_ema50_pct": 1.0,
                "r_1": 2.0,
            },
            "meta": {
                "last_closed_idx": {
                    "1d": last_closed_1d,
                    "4h": last_closed_4h,
                }
            },
        }
    }


def test_breakout_history_gate_blocks_insufficient_history():
    cfg = {"setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50}}
    result = score_breakouts(_base_features(last_closed_1d=10, last_closed_4h=20), {"TESTUSDT": 1_000_000}, cfg)
    assert result == []


def test_pullback_history_gate_blocks_insufficient_history():
    cfg = {"setup_validation": {"min_history_pullback_1d": 60, "min_history_pullback_4h": 80}}
    result = score_pullbacks(_base_features(last_closed_1d=40, last_closed_4h=60), {"TESTUSDT": 1_000_000}, cfg)
    assert result == []


def test_reversal_history_gate_blocks_insufficient_history():
    cfg = {"setup_validation": {"min_history_reversal_1d": 120, "min_history_reversal_4h": 80}}
    result = score_reversals(_base_features(last_closed_1d=100, last_closed_4h=70), {"TESTUSDT": 1_000_000}, cfg)
    assert result == []


def test_history_gate_allows_sufficient_history():
    cfg = {
        "setup_validation": {
            "min_history_breakout_1d": 30,
            "min_history_breakout_4h": 50,
            "min_history_pullback_1d": 60,
            "min_history_pullback_4h": 80,
            "min_history_reversal_1d": 120,
            "min_history_reversal_4h": 80,
        }
    }
    features = _base_features(last_closed_1d=150, last_closed_4h=100)
    volumes = {"TESTUSDT": 1_000_000}

    assert len(score_breakouts(features, volumes, cfg)) == 1
    assert len(score_pullbacks(features, volumes, cfg)) == 1
    assert len(score_reversals(features, volumes, cfg)) == 1
