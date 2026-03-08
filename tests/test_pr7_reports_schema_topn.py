from scanner.pipeline.output import ReportGenerator


def _mk_row(symbol: str, setup_id: str) -> dict:
    return {
        "symbol": symbol,
        "coin_name": symbol.replace("USDT", ""),
        "setup_id": setup_id,
        "score": 75.0,
        "final_score": 75.0,
        "entry": 1.0,
        "stop_loss": 0.9,
        "target_1": 1.1,
        "target_2": 1.2,
        "risk_reward": 2.0,
        "risk_flags": [],
    }


def test_pr7_json_schema_version_and_btc_regime_present() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 1}})
    btc_regime = {
        "state": "RISK_ON",
        "multiplier_risk_on": 1.0,
        "multiplier_risk_off": 0.85,
        "checks": {"close_gt_ema50": True, "ema20_gt_ema50": True},
    }

    report = generator.generate_json_report([], [], [], [], "2026-02-22", btc_regime=btc_regime)

    assert report["schema_version"] == "v1.11"
    assert report["btc_regime"]["state"] == "RISK_ON"


def test_pr7_breakout_lists_honor_top_n_per_setup_in_json_and_markdown() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 1}})
    breakout_rows = [
        _mk_row("AAAUSDT", "breakout_immediate_1_5d"),
        _mk_row("BBBUSDT", "breakout_immediate_1_5d"),
        _mk_row("CCCUSDT", "breakout_retest_1_5d"),
        _mk_row("DDDUSDT", "breakout_retest_1_5d"),
    ]

    report = generator.generate_json_report([], breakout_rows, [], [], "2026-02-22")
    md = generator.generate_markdown_report([], breakout_rows, [], [], "2026-02-22")

    assert len(report["setups"]["breakout_immediate_1_5d"]) == 1
    assert len(report["setups"]["breakout_retest_1_5d"]) == 1

    # One row per breakout section + one global ranking mention in summary.
    assert md.count("### 1.") == 2
