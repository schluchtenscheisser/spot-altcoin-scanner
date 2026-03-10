import pytest
import json
from pathlib import Path

from scanner.pipeline.output import ReportGenerator
from scanner.tools.validate_features import validate_features


def test_markdown_report_contains_enter_wait_and_summary_sections(tmp_path: Path) -> None:
    generator = ReportGenerator({"output": {"reports_dir": str(tmp_path), "top_n_per_setup": 1}})

    global_top20 = [{
        "symbol": "XUSDT",
        "coin_name": "Example",
        "decision": "ENTER",
        "decision_reasons": [],
        "score": 81.23,
        "global_score": 81.23,
        "risk_acceptable": True,
        "rr_to_tp10": 1.2,
        "slippage_bps_20k": 15.0,
    }]

    md = generator.generate_markdown_report([], [], [], global_top20, "2026-02-20")

    assert "## ENTER Candidates" in md
    assert "## WAIT Candidates" in md
    assert "## Summary" in md


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
    assert "## Summary" in md
    assert "- ENTER: 0" in md


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
            "analysis": {"trade_levels": {"entry_trigger": 9.5, "targets": [11.0, 12.0]}},
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
            "analysis": {"trade_levels": {"entry_trigger": 0.95, "targets": [1.1, 1.2]}},
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
            "analysis": {"trade_levels": {"entry_zone": {"center": 2.1}, "targets": [2.2, 2.4]}},
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
        "rank", "symbol", "coin_name", "decision", "decision_reasons", "entry_price_usdt", "current_price_usdt", "stop_price_initial",
        "risk_pct_to_stop", "tp10_price", "tp20_price", "rr_to_tp10", "rr_to_tp20", "distance_to_entry_pct", "entry_state", "best_setup_type", "setup_subtype",
        "setup_score", "global_score", "entry_ready", "entry_readiness_reasons", "tradeability_class", "execution_mode",
        "spread_pct", "depth_bid_1pct_usd", "depth_ask_1pct_usd", "slippage_bps_5k", "slippage_bps_20k", "risk_acceptable",
        "market_cap_usd", "btc_regime", "flags",
    }
    assert required_fields.issubset(trade_candidates[0].keys())
    assert trade_candidates[0]["tp10_price"] == pytest.approx(1.045)
    assert trade_candidates[0]["tp20_price"] == pytest.approx(1.14)
    assert trade_candidates[0]["rr_to_tp10"] == pytest.approx(1.9)
    assert trade_candidates[0]["rr_to_tp20"] == pytest.approx(3.8)
    assert trade_candidates[0]["btc_regime"] == "RISK_OFF"
    assert trade_candidates[0]["entry_price_usdt"] == 0.95
    assert trade_candidates[0]["current_price_usdt"] == 1.0
    assert trade_candidates[0]["distance_to_entry_pct"] == 5.263157894736836
    assert trade_candidates[0]["entry_state"] == "chased"
    assert trade_candidates[1]["entry_price_usdt"] == 2.1
    assert trade_candidates[1]["tp10_price"] == pytest.approx(2.31)
    assert trade_candidates[1]["tp20_price"] == pytest.approx(2.52)
    assert trade_candidates[1]["rr_to_tp10"] == pytest.approx(0.7)
    assert trade_candidates[1]["rr_to_tp20"] == pytest.approx(1.4)
    assert trade_candidates[1]["current_price_usdt"] == 2.0
    assert trade_candidates[1]["distance_to_entry_pct"] == -4.761904761904767
    assert trade_candidates[1]["entry_state"] == "early"
    assert trade_candidates[2]["entry_price_usdt"] == 9.5
    assert trade_candidates[2]["tp10_price"] == pytest.approx(10.45)
    assert trade_candidates[2]["tp20_price"] == pytest.approx(11.4)
    assert trade_candidates[2]["rr_to_tp10"] is None
    assert trade_candidates[2]["rr_to_tp20"] is None
    assert trade_candidates[2]["current_price_usdt"] == 10.0
    assert trade_candidates[2]["distance_to_entry_pct"] == 5.263157894736836
    assert trade_candidates[2]["entry_state"] == "chased"


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
        "analysis": {"trade_levels": {"entry_trigger": float("inf"), "targets": ["bad", None]}},
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
    assert row["current_price_usdt"] is None
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


def test_trade_candidates_uses_canonical_tp_from_entry_and_not_analysis_targets() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "CANONUSDT",
        "coin_name": "Canon",
        "decision": "WAIT",
        "decision_reasons": ["entry_not_confirmed"],
        "price_usdt": 100.0,
        "stop_price_initial": 95.0,
        "analysis": {"trade_levels": {"entry_trigger": 100.0, "targets": [150.0, 200.0]}},
        "tp10_price": 123.0,
        "tp20_price": 234.0,
        "rr_to_tp10": 9.9,
        "rr_to_tp20": 8.8,
        "best_setup_type": "breakout",
        "setup_subtype": "confirmed_breakout",
        "setup_score": 50.0,
        "global_score": 50.0,
        "entry_ready": False,
        "entry_readiness_reasons": ["entry_not_confirmed"],
        "tradeability_class": "DIRECT_OK",
        "execution_mode": "direct",
        "spread_pct": 0.1,
        "depth_bid_1pct_usd": 100_000.0,
        "depth_ask_1pct_usd": 100_000.0,
        "slippage_bps_5k": 5.0,
        "slippage_bps_20k": 15.0,
        "risk_acceptable": True,
        "market_cap": 100_000_000,
        "flags": [],
    }]

    row = generator.generate_json_report([], [], [], global_top20, "2026-03-09")["trade_candidates"][0]

    assert row["tp10_price"] == pytest.approx(110.0)
    assert row["tp20_price"] == pytest.approx(120.0)
    assert row["rr_to_tp10"] == pytest.approx(2.0)
    assert row["rr_to_tp20"] == pytest.approx(4.0)


def test_trade_candidates_sets_rr_null_when_stop_missing_or_not_below_entry() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "NOSTOPUSDT",
            "coin_name": "NoStop",
            "decision": "WAIT",
            "decision_reasons": ["risk_data_insufficient"],
            "price_usdt": 10.0,
            "stop_price_initial": None,
            "analysis": {"trade_levels": {"entry_trigger": 10.0}},
            "best_setup_type": "breakout",
            "global_score": 20.0,
        },
        {
            "symbol": "BADSTOPUSDT",
            "coin_name": "BadStop",
            "decision": "WAIT",
            "decision_reasons": ["risk_data_insufficient"],
            "price_usdt": 10.0,
            "stop_price_initial": 10.0,
            "analysis": {"trade_levels": {"entry_trigger": 10.0}},
            "best_setup_type": "breakout",
            "global_score": 19.0,
        },
    ]

    by_symbol = {
        row["symbol"]: row
        for row in generator.generate_json_report([], [], [], global_top20, "2026-03-09")["trade_candidates"]
    }

    assert by_symbol["NOSTOPUSDT"]["tp10_price"] == pytest.approx(11.0)
    assert by_symbol["NOSTOPUSDT"]["tp20_price"] == pytest.approx(12.0)
    assert by_symbol["NOSTOPUSDT"]["rr_to_tp10"] is None
    assert by_symbol["NOSTOPUSDT"]["rr_to_tp20"] is None
    assert by_symbol["BADSTOPUSDT"]["tp10_price"] == pytest.approx(11.0)
    assert by_symbol["BADSTOPUSDT"]["tp20_price"] == pytest.approx(12.0)
    assert by_symbol["BADSTOPUSDT"]["rr_to_tp10"] is None
    assert by_symbol["BADSTOPUSDT"]["rr_to_tp20"] is None


def test_trade_candidates_uses_setup_planned_entry_and_separate_spot_with_null_edge_cases() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "PULLUSDT",
            "coin_name": "Pull",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 1.5,
            "analysis": {"trade_levels": {"entry_zone": {"center": 1.25}}},
            "best_setup_type": "pullback",
            "global_score": 30.0,
        },
        {
            "symbol": "BRKUSDT",
            "coin_name": "Break",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 2.5,
            "analysis": {"trade_levels": {"entry_trigger": 2.2}},
            "best_setup_type": "breakout",
            "global_score": 29.0,
        },
        {
            "symbol": "MISSUSDT",
            "coin_name": "Missing",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 3.5,
            "analysis": {},
            "best_setup_type": "reversal",
            "global_score": 28.0,
        },
        {
            "symbol": "BADSPOTUSDT",
            "coin_name": "BadSpot",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": float("-inf"),
            "analysis": {"trade_levels": {"entry_trigger": 4.4}},
            "best_setup_type": "reversal",
            "global_score": 27.0,
        },
    ]

    by_symbol = {
        row["symbol"]: row
        for row in generator.generate_json_report([], [], [], global_top20, "2026-03-08")["trade_candidates"]
    }

    assert by_symbol["PULLUSDT"]["entry_price_usdt"] == 1.25
    assert by_symbol["PULLUSDT"]["current_price_usdt"] == 1.5
    assert by_symbol["BRKUSDT"]["entry_price_usdt"] == 2.2
    assert by_symbol["BRKUSDT"]["current_price_usdt"] == 2.5
    assert by_symbol["MISSUSDT"]["entry_price_usdt"] is None
    assert by_symbol["MISSUSDT"]["current_price_usdt"] == 3.5
    assert by_symbol["BADSPOTUSDT"]["entry_price_usdt"] == 4.4
    assert by_symbol["BADSPOTUSDT"]["current_price_usdt"] is None




def test_trade_candidates_prefers_top_level_entry_price_over_analysis_trade_levels() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "ENTRYUSDT",
        "coin_name": "Entry",
        "decision": "WAIT",
        "decision_reasons": ["entry_not_confirmed"],
        "price_usdt": 101.0,
        "entry_price_usdt": 100.0,
        "stop_price_initial": 95.0,
        "analysis": {"trade_levels": {"entry_trigger": 80.0, "targets": [88.0, 96.0]}},
        "best_setup_type": "breakout",
        "global_score": 10.0,
    }]

    row = generator.generate_json_report([], [], [], global_top20, "2026-03-10")["trade_candidates"][0]

    assert row["entry_price_usdt"] == pytest.approx(100.0)
    assert row["tp10_price"] == pytest.approx(110.0)
    assert row["tp20_price"] == pytest.approx(120.0)
    assert row["rr_to_tp10"] == pytest.approx(2.0)
    assert row["rr_to_tp20"] == pytest.approx(4.0)


def test_trade_candidates_invalid_top_level_entry_does_not_fallback_to_analysis() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "BADENTRYUSDT",
        "coin_name": "BadEntry",
        "decision": "WAIT",
        "decision_reasons": ["entry_not_confirmed"],
        "price_usdt": 101.0,
        "entry_price_usdt": float("inf"),
        "stop_price_initial": 95.0,
        "analysis": {"trade_levels": {"entry_trigger": 100.0, "targets": [110.0, 120.0]}},
        "best_setup_type": "breakout",
        "global_score": 10.0,
    }]

    row = generator.generate_json_report([], [], [], global_top20, "2026-03-10")["trade_candidates"][0]

    assert row["entry_price_usdt"] is None
    assert row["tp10_price"] is None
    assert row["tp20_price"] is None
    assert row["rr_to_tp10"] is None
    assert row["rr_to_tp20"] is None

def test_trade_candidates_directional_volume_preparation_is_optional_and_nullable() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "OPTUSDT",
            "coin_name": "Optional",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 1.0,
            "global_score": 50.0,
            "best_setup_type": "breakout",
            "setup_subtype": "confirmed_breakout",
            "directional_volume_preparation": None,
        },
        {
            "symbol": "MISSUSDT",
            "coin_name": "Missing",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 1.1,
            "global_score": 49.0,
            "best_setup_type": "breakout",
            "setup_subtype": "confirmed_breakout",
        },
    ]

    report = generator.generate_json_report([], [], [], global_top20, "2026-03-08")
    by_symbol = {row["symbol"]: row for row in report["trade_candidates"]}

    assert "directional_volume_preparation" in by_symbol["OPTUSDT"]
    assert by_symbol["OPTUSDT"]["directional_volume_preparation"] is None
    assert "directional_volume_preparation" not in by_symbol["MISSUSDT"]


def test_trade_candidates_directional_volume_preparation_invalid_is_rejected() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "BADUSDT",
        "coin_name": "Bad",
        "decision": "WAIT",
        "decision_reasons": ["entry_not_confirmed"],
        "price_usdt": 1.0,
        "global_score": 50.0,
        "best_setup_type": "breakout",
        "setup_subtype": "confirmed_breakout",
        "directional_volume_preparation": {"lookback_bars": 0},
    }]

    import pytest
    with pytest.raises(ValueError, match="lookback_bars"):
        generator.generate_json_report([], [], [], global_top20, "2026-03-08")


def test_trade_candidates_directional_volume_preparation_sanitizes_finite_fields() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [{
        "symbol": "GOODUSDT",
        "coin_name": "Good",
        "decision": "WAIT",
        "decision_reasons": ["entry_not_confirmed"],
        "price_usdt": 1.0,
        "global_score": 50.0,
        "best_setup_type": "breakout",
        "setup_subtype": "confirmed_breakout",
        "directional_volume_preparation": {
            "buy_volume_share": "0.6",
            "sell_volume_share": 0.4,
            "imbalance_ratio": 1.5,
            "lookback_bars": 48,
        },
    }]

    row = generator.generate_json_report([], [], [], global_top20, "2026-03-08")["trade_candidates"][0]
    assert row["directional_volume_preparation"] == {
        "buy_volume_share": 0.6,
        "sell_volume_share": 0.4,
        "imbalance_ratio": 1.5,
        "lookback_bars": 48,
    }


def test_trade_candidate_entry_timing_fields_follow_thresholds_and_nullability() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "ATUSDT",
            "coin_name": "At",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 100.0,
        },
        {
            "symbol": "LTUSDT",
            "coin_name": "Late",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 101.0,
        },
        {
            "symbol": "ERUSDT",
            "coin_name": "Early",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 97.0,
        },
        {
            "symbol": "NULUSDT",
            "coin_name": "Null",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": None}},
            "price_usdt": None,
        },
    ]

    trade_candidates = generator.generate_json_report([], [], [], global_top20, "2026-03-09")["trade_candidates"]
    by_symbol = {row["symbol"]: row for row in trade_candidates}

    assert by_symbol["ATUSDT"]["distance_to_entry_pct"] == 0.0
    assert by_symbol["ATUSDT"]["entry_state"] == "at_trigger"

    assert by_symbol["ERUSDT"]["distance_to_entry_pct"] == pytest.approx(-3.0)
    assert by_symbol["ERUSDT"]["entry_state"] == "early"

    assert by_symbol["LTUSDT"]["distance_to_entry_pct"] == pytest.approx(1.0)
    assert by_symbol["LTUSDT"]["entry_state"] == "late"

    assert by_symbol["NULUSDT"]["distance_to_entry_pct"] is None
    assert by_symbol["NULUSDT"]["entry_state"] is None


def test_trade_candidates_adds_diagnostic_timing_reasons_without_reordering_existing_reasons() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "EARLYUSDT",
            "coin_name": "Early",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 97.0,
        },
        {
            "symbol": "LATEUSDT",
            "coin_name": "Late",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed", "entry_late"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 101.0,
        },
        {
            "symbol": "CHASEUSDT",
            "coin_name": "Chase",
            "decision": "NO_TRADE",
            "decision_reasons": ["risk_reward_unattractive"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 105.0,
        },
    ]

    rows = generator.generate_json_report([], [], [], global_top20, "2026-03-09")["trade_candidates"]
    by_symbol = {row["symbol"]: row for row in rows}

    assert by_symbol["EARLYUSDT"]["decision_reasons"] == ["entry_not_confirmed", "entry_too_early"]
    assert by_symbol["LATEUSDT"]["decision_reasons"] == ["entry_not_confirmed", "entry_late"]
    assert by_symbol["CHASEUSDT"]["decision_reasons"] == ["risk_reward_unattractive", "entry_chased"]


def test_trade_candidates_do_not_add_timing_reason_for_at_trigger_or_null() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "ATUSDT",
            "coin_name": "At",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 100.0,
        },
        {
            "symbol": "NULUSDT",
            "coin_name": "Null",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": None}},
            "price_usdt": 100.0,
        },
    ]

    rows = generator.generate_json_report([], [], [], global_top20, "2026-03-09")["trade_candidates"]
    by_symbol = {row["symbol"]: row for row in rows}

    assert by_symbol["ATUSDT"]["decision_reasons"] == ["entry_not_confirmed"]
    assert by_symbol["NULUSDT"]["decision_reasons"] == ["entry_not_confirmed"]


def test_json_summary_contains_entry_state_counts_all_and_by_decision() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "ENUSDT",
            "coin_name": "Enter",
            "decision": "ENTER",
            "decision_reasons": [],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 97.0,
        },
        {
            "symbol": "WTUSDT",
            "coin_name": "Wait",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 100.0,
        },
        {
            "symbol": "NTUSDT",
            "coin_name": "NoTrade",
            "decision": "NO_TRADE",
            "decision_reasons": ["risk_reward_unattractive"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": 100.0}},
            "price_usdt": 102.0,
        },
        {
            "symbol": "NULUSDT",
            "coin_name": "Null",
            "decision": "NO_TRADE",
            "decision_reasons": ["risk_data_insufficient"],
            "best_setup_type": "breakout",
            "analysis": {"trade_levels": {"entry_trigger": None}},
            "price_usdt": 100.0,
        },
    ]

    summary = generator.generate_json_report([], [], [], global_top20, "2026-03-09")["summary"]

    assert summary["entry_state_counts_all"] == {
        "early": 1,
        "at_trigger": 1,
        "late": 1,
        "chased": 0,
        "null": 1,
    }
    assert summary["entry_state_counts_enter"]["early"] == 1
    assert summary["entry_state_counts_wait"]["at_trigger"] == 1
    assert summary["entry_state_counts_no_trade"]["late"] == 1
    assert summary["entry_state_counts_no_trade"]["null"] == 1
