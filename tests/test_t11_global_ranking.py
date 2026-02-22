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

    assert report["schema_version"] == "v1.7"
    assert report["meta"]["version"] == "1.7"
