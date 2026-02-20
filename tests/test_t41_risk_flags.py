from pathlib import Path

from scanner.pipeline.risk_flags import RiskFlagEngine
from scanner.pipeline.scoring.breakout import score_breakouts


def test_risk_flags_hard_exclude_denylist_and_major_unlock(tmp_path: Path):
    denylist = tmp_path / "denylist.yaml"
    unlocks = tmp_path / "unlock_overrides.yaml"
    denylist.write_text("symbols:\n  - BAD\n")
    unlocks.write_text("major:\n  - MAJOR\nminor: []\n")

    engine = RiskFlagEngine(
        {
            "risk_flags": {
                "denylist_file": str(denylist),
                "unlock_overrides_file": str(unlocks),
            }
        }
    )

    filtered, _ = engine.apply_to_universe(
        [
            {"symbol": "BADUSDT", "base": "BAD"},
            {"symbol": "MAJORUSDT", "base": "MAJOR"},
            {"symbol": "GOODUSDT", "base": "GOOD"},
        ]
    )

    assert [x["symbol"] for x in filtered] == ["GOODUSDT"]


def test_risk_flags_minor_unlock_is_soft_flag_and_penalty(tmp_path: Path):
    denylist = tmp_path / "denylist.yaml"
    unlocks = tmp_path / "unlock_overrides.yaml"
    denylist.write_text("symbols: []\n")
    unlocks.write_text("major: []\nminor:\n  - TEST\n")

    engine = RiskFlagEngine(
        {
            "risk_flags": {
                "denylist_file": str(denylist),
                "unlock_overrides_file": str(unlocks),
            }
        }
    )
    filtered, _ = engine.apply_to_universe([{"symbol": "TESTUSDT", "base": "TEST", "quote_volume_24h": 2_000_000}])
    assert filtered[0]["risk_flags"] == ["minor_unlock_within_14d"]

    features = {
        "TESTUSDT": {
            "risk_flags": ["minor_unlock_within_14d"],
            "1d": {"breakout_dist_20": 2.0, "volume_spike": 2.0, "volume_quote_spike": 2.0, "dist_ema50_pct": 2.0, "r_7": 5.0},
            "4h": {"volume_spike": 2.0, "volume_quote_spike": 2.0, "r_1": 1.0},
            "meta": {"last_closed_idx": {"1d": 100, "4h": 100}},
        }
    }
    cfg = {
        "setup_validation": {"min_history_breakout_1d": 30, "min_history_breakout_4h": 50},
        "scoring": {"breakout": {"penalties": {"minor_unlock_penalty_factor": 0.5}}},
    }
    out = score_breakouts(features, {"TESTUSDT": 2_000_000}, cfg)

    assert len(out) == 1
    assert "minor_unlock_within_14d" in out[0]["flags"]
    assert out[0]["penalties"]["minor_unlock_within_14d"] == 0.5
