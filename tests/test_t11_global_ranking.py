from scanner.pipeline.global_ranking import compute_global_top20
from scanner.pipeline.output import ReportGenerator


def test_compute_global_top20_deduplicates_by_symbol_and_sets_best_setup():
    reversals = [{"symbol": "ABCUSDT", "score": 90.0, "coin_name": "ABC"}]
    breakouts = [{"symbol": "ABCUSDT", "score": 80.0, "coin_name": "ABC"}, {"symbol": "XYZUSDT", "score": 70.0, "coin_name": "XYZ"}]
    pullbacks = [{"symbol": "ABCUSDT", "score": 95.0, "coin_name": "ABC"}]

    global_top20 = compute_global_top20(reversals, breakouts, pullbacks, {})

    assert [e["symbol"] for e in global_top20] == ["ABCUSDT", "XYZUSDT"]
    assert global_top20[0]["best_setup_type"] == "pullback"
    assert global_top20[0]["confluence"] == 3


def test_json_report_contains_global_top20():
    generator = ReportGenerator({"output": {"top_n_per_setup": 2}})
    global_top20 = [{"symbol": "ABCUSDT", "score": 80.0, "global_score": 82.0, "best_setup_type": "breakout", "confluence": 2}]

    report = generator.generate_json_report([], [], [], global_top20, "2026-02-20")

    assert "global_top20" in report["setups"]
    assert report["setups"]["global_top20"][0]["symbol"] == "ABCUSDT"
    assert report["summary"]["global_top20_count"] == 1


def test_json_report_contains_explicit_schema_version():
    generator = ReportGenerator({"output": {"top_n_per_setup": 2}})

    report = generator.generate_json_report([], [], [], [], "2026-02-20")

    assert report["schema_version"] == "v1.18"
    assert report["meta"]["version"] == "1.9"


def test_setup_weight_applied_to_global_score():
    reversals = [{"symbol": "AAAUSDT", "score": 60.0, "final_score": 60.0, "setup_id": "reversal"}]
    breakouts = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]
    cfg = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": 1.0, "pullback": 0.9, "reversal": 0.8},
    }

    out = compute_global_top20(reversals, breakouts, [], cfg)

    assert out[0]["best_setup_type"] == "breakout"
    assert out[0]["global_score"] == 50.0


def test_setup_weights_inactive_flag_bypasses_weights():
    reversals = [{"symbol": "AAAUSDT", "score": 60.0, "final_score": 60.0, "setup_id": "reversal"}]
    breakouts = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]
    cfg = {
        "phase_policy": {"setup_weights_active": False},
        "setup_weights_by_category": {"breakout": 1.0, "pullback": 0.9, "reversal": 0.8},
    }

    out = compute_global_top20(reversals, breakouts, [], cfg)

    assert out[0]["best_setup_type"] == "reversal"
    assert out[0]["global_score"] == 60.0
    assert out[0]["setup_weight"] == 1.0


def test_setup_weight_missing_key_defaults_to_1():
    reversals = []
    breakouts = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]
    pullbacks = [{"symbol": "AAAUSDT", "score": 45.0, "final_score": 45.0, "setup_id": "pullback"}]
    cfg = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"reversal": 0.8},
    }

    out = compute_global_top20(reversals, breakouts, pullbacks, cfg)

    assert out[0]["best_setup_type"] == "breakout"
    assert out[0]["global_score"] == 50.0
    assert out[0]["setup_weight"] == 1.0


def test_setup_weight_invalid_value_raises():
    base_rows = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]

    cfg_negative = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": -1},
    }
    try:
        compute_global_top20([], base_rows, [], cfg_negative)
    except ValueError as exc:
        assert "Invalid setup weight" in str(exc)
    else:
        raise AssertionError("Expected ValueError for negative setup weight")

    cfg_nan = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": "NaN"},
    }
    try:
        compute_global_top20([], base_rows, [], cfg_nan)
    except ValueError as exc:
        assert "Invalid setup weight" in str(exc)
    else:
        raise AssertionError("Expected ValueError for NaN setup weight")


def test_setup_weight_field_in_output_row():
    breakouts = [{"symbol": "AAAUSDT", "score": 70.0, "final_score": 70.0, "setup_id": "breakout_immediate_1_5d"}]
    cfg = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": 0.7},
    }

    out = compute_global_top20([], breakouts, [], cfg)

    assert out[0]["setup_weight"] == 0.7
    assert out[0]["global_score"] == 49.0


def test_global_score_deterministic():
    reversals = [{"symbol": "AAAUSDT", "score": 60.0, "final_score": 60.0, "setup_id": "reversal"}]
    breakouts = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]
    cfg = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": 1.0, "pullback": 0.9, "reversal": 0.8},
    }

    out1 = compute_global_top20(reversals, breakouts, [], cfg)
    out2 = compute_global_top20(reversals, breakouts, [], cfg)

    assert out1 == out2


def test_confluence_unaffected_by_weights():
    reversals = [{"symbol": "AAAUSDT", "score": 60.0, "final_score": 60.0, "setup_id": "reversal"}]
    breakouts = [{"symbol": "AAAUSDT", "score": 50.0, "final_score": 50.0, "setup_id": "breakout_immediate_1_5d"}]
    cfg = {
        "phase_policy": {"setup_weights_active": True},
        "setup_weights_by_category": {"breakout": 1.0, "pullback": 0.9, "reversal": 0.8},
    }

    out = compute_global_top20(reversals, breakouts, [], cfg)

    assert out[0]["confluence"] == 2
    assert out[0]["valid_setups"] == ["breakout", "reversal"]
