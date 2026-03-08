import json
from pathlib import Path

from scanner.pipeline.output import ReportGenerator
from scanner.tools.validate_features import validate_features


def test_markdown_report_includes_score_transparency_fields(tmp_path: Path) -> None:
    generator = ReportGenerator({"output": {"reports_dir": str(tmp_path), "top_n_per_setup": 1}})

    sample = {
        "symbol": "XUSDT",
        "coin_name": "Example",
        "score": 81.23,
        "raw_score": 90.0,
        "penalty_multiplier": 0.9025,
        "components": {"trend": 80.0, "volume": 70.0},
        "flags": ["low_liquidity"],
    }

    md = generator.generate_markdown_report([sample], [], [], [], "2026-02-20")

    assert "Score Details:" in md
    assert "raw_score=90.00" in md
    assert "penalty_multiplier=0.9025" in md


def test_validate_features_checks_phase4_ranges(tmp_path: Path) -> None:
    report = {
        "setups": {
            "reversals": [
                {
                    "symbol": "XUSDT",
                    "score": 75.5,
                    "raw_score": 80.0,
                    "penalty_multiplier": 0.9,
                    "components": {"drawdown": 80.0, "base": 70.0},
                }
            ],
            "breakouts": [],
            "pullbacks": [],
        }
    }

    path = tmp_path / "valid.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert validate_features(str(path)) == 0

    report["setups"]["reversals"][0]["penalty_multiplier"] = 1.2
    invalid = tmp_path / "invalid.json"
    invalid.write_text(json.dumps(report), encoding="utf-8")
    assert validate_features(str(invalid)) == 1


def test_validate_features_requires_transparency_fields(tmp_path: Path) -> None:
    report = {
        "setups": {
            "reversals": [
                {
                    "symbol": "XUSDT",
                    "score": 75.5,
                    "components": {"drawdown": 80.0, "base": 70.0},
                }
            ],
            "breakouts": [],
            "pullbacks": [],
        }
    }

    path = tmp_path / "missing_fields.json"
    path.write_text(json.dumps(report), encoding="utf-8")
    assert validate_features(str(path)) == 1


def test_validate_features_emits_machine_readable_json(capsys, tmp_path: Path) -> None:
    report = {
        "setups": {
            "reversals": [
                {
                    "symbol": "XUSDT",
                    "score": 101,
                    "raw_score": 80.0,
                    "penalty_multiplier": 0.9,
                    "components": {"drawdown": 80.0, "base": 70.0},
                }
            ],
            "breakouts": [],
            "pullbacks": [],
        }
    }

    path = tmp_path / "json_errors.json"
    path.write_text(json.dumps(report), encoding="utf-8")

    rc = validate_features(str(path))
    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["errors"][0]["code"] == "RANGE"
    assert payload["errors"][0]["path"] == "setups.reversals[0].score"


def test_report_payload_contains_score_details_for_pipeline_like_entries(tmp_path: Path) -> None:
    generator = ReportGenerator({"output": {"reports_dir": str(tmp_path), "top_n_per_setup": 5}})

    reversals = [{"symbol": "RUSDT", "coin_name": "Rev", "score": 70.0, "raw_score": 80.0, "penalty_multiplier": 0.875, "components": {"drawdown": 70.0}}]
    breakouts = [{"symbol": "BUSDT", "coin_name": "Brk", "score": 65.0, "raw_score": 72.2, "penalty_multiplier": 0.9, "components": {"breakout": 65.0}}]
    pullbacks = [{"symbol": "PUSDT", "coin_name": "Pbk", "score": 60.0, "raw_score": 75.0, "penalty_multiplier": 0.8, "components": {"trend": 60.0}}]

    report = generator.generate_json_report(reversals, breakouts, pullbacks, [], "2026-02-20")

    assert report["setups"]["reversals"][0]["raw_score"] == 80.0
    assert report["setups"]["reversals"][0]["penalty_multiplier"] == 0.875
    assert report["setups"]["breakouts"][0]["raw_score"] == 72.2
    assert report["setups"]["breakouts"][0]["penalty_multiplier"] == 0.9
    assert report["setups"]["pullbacks"][0]["raw_score"] == 75.0
    assert report["setups"]["pullbacks"][0]["penalty_multiplier"] == 0.8

    md = generator.generate_markdown_report(reversals, breakouts, pullbacks, [], "2026-02-20")
    assert md.count("**Score Details:**") == 3


def test_json_report_adds_explicit_rank_field_per_setup() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 2}})

    reversals = [
        {"symbol": "AUSDT", "score": 90.0, "raw_score": 95.0, "penalty_multiplier": 0.95, "components": {}},
        {"symbol": "BUSDT", "score": 80.0, "raw_score": 90.0, "penalty_multiplier": 0.89, "components": {}},
        {"symbol": "CUSDT", "score": 70.0, "raw_score": 88.0, "penalty_multiplier": 0.80, "components": {}},
    ]
    breakouts = [{"symbol": "DUSDT", "score": 77.0, "raw_score": 80.0, "penalty_multiplier": 0.96, "components": {}}]
    pullbacks = []

    report = generator.generate_json_report(reversals, breakouts, pullbacks, [], "2026-02-20")

    assert [e["symbol"] for e in report["setups"]["reversals"]] == ["AUSDT", "BUSDT"]
    assert [e["rank"] for e in report["setups"]["reversals"]] == [1, 2]
    assert report["setups"]["breakouts"][0]["rank"] == 1
    assert "rank" not in reversals[0]


def test_trade_candidates_contains_required_fields_and_deterministic_sorting() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "CCCUSDT",
            "coin_name": "CCC",
            "decision": "NO_TRADE",
            "decision_reasons": ["insufficient_edge"],
            "price_usdt": 10.0,
            "stop_price_initial": None,
            "risk_pct_to_stop": None,
            "analysis": {"trade_levels": {"targets": [11.0, 12.0]}},
            "rr_to_tp10": None,
            "rr_to_tp20": None,
            "best_setup_type": "reversal",
            "setup_subtype": "reversal_base_reclaim",
            "setup_score": 40.0,
            "global_score": 40.0,
            "entry_ready": False,
            "entry_readiness_reasons": ["entry_not_confirmed"],
            "tradeability_class": "DIRECT_OK",
            "execution_mode": "direct",
            "spread_pct": 0.1,
            "depth_bid_1pct_usd": 100_000.0,
            "depth_ask_1pct_usd": 100_000.0,
            "slippage_bps_5k": 10.0,
            "slippage_bps_20k": 20.0,
            "risk_acceptable": False,
            "market_cap": 100_000_000,
            "flags": ["sample"],
        },
        {
            "symbol": "AAAUSDT",
            "coin_name": "AAA",
            "decision": "ENTER",
            "decision_reasons": [],
            "price_usdt": 1.0,
            "stop_price_initial": 0.9,
            "risk_pct_to_stop": 10.0,
            "analysis": {"trade_levels": {"targets": [1.1, 1.2]}},
            "rr_to_tp10": 1.0,
            "rr_to_tp20": 2.0,
            "best_setup_type": "breakout",
            "setup_subtype": "confirmed_breakout",
            "setup_score": 80.0,
            "global_score": 80.0,
            "entry_ready": True,
            "entry_readiness_reasons": [],
            "tradeability_class": "DIRECT_OK",
            "execution_mode": "direct",
            "spread_pct": 0.05,
            "depth_bid_1pct_usd": 200_000.0,
            "depth_ask_1pct_usd": 200_000.0,
            "slippage_bps_5k": 5.0,
            "slippage_bps_20k": 12.0,
            "risk_acceptable": True,
            "market_cap": 200_000_000,
            "flags": [],
        },
        {
            "symbol": "BBBUSDT",
            "coin_name": "BBB",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 2.0,
            "stop_price_initial": 1.8,
            "risk_pct_to_stop": 10.0,
            "analysis": {"trade_levels": {"targets": [2.2, 2.4]}},
            "rr_to_tp10": 1.0,
            "rr_to_tp20": 2.0,
            "best_setup_type": "pullback",
            "setup_subtype": "pullback_to_ema",
            "setup_score": 70.0,
            "global_score": 70.0,
            "entry_ready": False,
            "entry_readiness_reasons": ["rebound_not_confirmed"],
            "tradeability_class": "TRANCHE_OK",
            "execution_mode": "tranches",
            "spread_pct": 0.08,
            "depth_bid_1pct_usd": 150_000.0,
            "depth_ask_1pct_usd": 150_000.0,
            "slippage_bps_5k": 8.0,
            "slippage_bps_20k": 40.0,
            "risk_acceptable": True,
            "market_cap": 150_000_000,
            "flags": [],
        },
    ]

    report = generator.generate_json_report([], [], [], global_top20, "2026-03-08", btc_regime={"state": "RISK_OFF"})
    trade_candidates = report["trade_candidates"]

    assert [row["symbol"] for row in trade_candidates] == ["AAAUSDT", "BBBUSDT", "CCCUSDT"]
    assert [row["rank"] for row in trade_candidates] == [1, 2, 3]

    required_fields = {
        "rank", "symbol", "coin_name", "decision", "decision_reasons", "entry_price_usdt", "stop_price_initial",
        "risk_pct_to_stop", "tp10_price", "tp20_price", "rr_to_tp10", "rr_to_tp20", "best_setup_type", "setup_subtype",
        "setup_score", "global_score", "entry_ready", "entry_readiness_reasons", "tradeability_class", "execution_mode",
        "spread_pct", "depth_bid_1pct_usd", "depth_ask_1pct_usd", "slippage_bps_5k", "slippage_bps_20k", "risk_acceptable",
        "market_cap_usd", "btc_regime", "flags",
    }
    assert required_fields.issubset(trade_candidates[0].keys())
    assert trade_candidates[0]["tp10_price"] == 1.1
    assert trade_candidates[0]["tp20_price"] == 1.2
    assert trade_candidates[0]["btc_regime"] == "RISK_OFF"


def test_trade_candidates_keeps_nullable_fields_as_null_without_coercion() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "NANUSDT",
        "coin_name": "Nan",
        "decision": "WAIT",
        "decision_reasons": ["risk_data_insufficient"],
        "price_usdt": "bad",
        "stop_price_initial": "bad",
        "risk_pct_to_stop": float("nan"),
        "analysis": {"trade_levels": {"targets": ["bad", None]}},
        "rr_to_tp10": "bad",
        "rr_to_tp20": None,
        "best_setup_type": "breakout",
        "setup_subtype": "confirmed_breakout",
        "setup_score": "bad",
        "global_score": "bad",
        "entry_ready": "bad",
        "entry_readiness_reasons": "bad",
        "tradeability_class": "UNKNOWN",
        "execution_mode": "none",
        "spread_pct": "bad",
        "depth_bid_1pct_usd": "bad",
        "depth_ask_1pct_usd": "bad",
        "slippage_bps_5k": "bad",
        "slippage_bps_20k": "bad",
        "risk_acceptable": "bad",
        "market_cap": "bad",
        "flags": [],
    }]

    report = generator.generate_json_report([], [], [], global_top20, "2026-03-08")
    row = report["trade_candidates"][0]

    assert row["entry_price_usdt"] is None
    assert row["stop_price_initial"] is None
    assert row["risk_pct_to_stop"] is None
    assert row["tp10_price"] is None
    assert row["tp20_price"] is None
    assert row["rr_to_tp10"] is None
    assert row["setup_score"] is None
    assert row["global_score"] is None
    assert row["entry_ready"] is None
    assert row["entry_readiness_reasons"] == []
    assert row["risk_acceptable"] is None
