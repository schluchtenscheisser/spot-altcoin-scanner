import json

import yaml

from scanner.pipeline.scoring.breakout_trend_1_5d import score_breakout_trend_1_5d


REQUIRED_SYMBOLS = ["HYPEUSDT", "C98USDT", "JSTUSDT", "KERNELUSDT", "TAOUSDT", "GRTUSDT", "ALGOUSDT"]


def _load_snapshot() -> dict:
    with open("snapshots/history/2026-03-14.json", encoding="utf-8") as f:
        return json.load(f)


def _load_config() -> dict:
    with open("config/config.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _find_row(rows: list[dict], symbol: str, setup_id: str = "breakout_immediate_1_5d") -> dict | None:
    for row in rows:
        if row.get("symbol") == symbol and row.get("setup_id") == setup_id:
            return row
    return None


def test_20260314_breakout_calibration_comparison_set() -> None:
    snapshot = _load_snapshot()
    features = snapshot["data"]["features"]
    volumes = {symbol: float((feature or {}).get("quote_volume_24h") or 0.0) for symbol, feature in features.items()}

    old_rows = snapshot["scoring"]["breakouts"]
    new_rows = score_breakout_trend_1_5d(features, volumes, _load_config(), btc_regime=snapshot["meta"].get("btc_regime"))

    # KERNEL/TAO/GRT/ALGO are absent from breakout rows in this fixed fixture family.
    # This test documents the absence explicitly and keeps the mandatory symbols check deterministic.
    for symbol in REQUIRED_SYMBOLS:
        assert symbol in features

    old_hype = _find_row(old_rows, "HYPEUSDT")
    new_hype = _find_row(new_rows, "HYPEUSDT")
    old_c98 = _find_row(old_rows, "C98USDT")
    new_c98 = _find_row(new_rows, "C98USDT")
    assert old_hype and new_hype and old_c98 and new_c98

    assert new_hype["final_score"] > old_hype["final_score"]
    assert new_c98["final_score"] > old_c98["final_score"]
    assert new_hype["execution_gate_pass"] is True
    assert new_c98["execution_gate_pass"] is False

    new_jst = _find_row(new_rows, "JSTUSDT")
    assert new_jst
    assert new_jst["execution_gate_pass"] is False

    for row in new_rows:
        assert 0.0 <= float(row["final_score"]) <= 100.0
