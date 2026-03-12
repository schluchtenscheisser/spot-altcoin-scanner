import json
from pathlib import Path

from scanner.pipeline.output import ReportGenerator


def _metadata_with_manifest_overrides() -> dict:
    return {
        "run_id": "2026-03-08_051355Z_001",
        "timestamp_utc": "2026-03-08T05:13:55Z",
        "asof_ts_ms": 1772946835000,
        "stage_counts": {
            "universe": 300,
            "filtered": 120,
            "shortlist": 80,
            "orderbook_requested": 80,
            "orderbook_selected": 40,
            "tradeability_passed": 32,
            "tradeability_stopped": 8,
            "ohlcv_symbols": 30,
            "features": 30,
            "reversal_scored": 10,
            "breakout_scored": 12,
            "pullback_scored": 11,
            "global_top20": 20,
            "trade_candidates": 20,
        },
        "warnings": ["orderbook_partial_fetch"],
        "duration_seconds": 12.5,
        "shortlist_size_used": 200,
        "orderbook_top_k_used": 200,
        "data_freshness": {
            "exchange_info_ts_utc": "2026-03-08T05:13:01Z",
            "tickers_24h_ts_utc": "2026-03-08T05:13:05Z",
            "market_cap_listings_ts_utc": "2026-03-08T05:13:10Z",
            "asof_iso_utc": "2026-03-08T05:13:55Z",
            "asof_ts_ms": 1772946835000,
        },
    }


def test_generate_json_report_includes_required_run_manifest_fields() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 1}})

    report = generator.generate_json_report([], [], [], [], "2026-03-08", metadata=_metadata_with_manifest_overrides())

    manifest = report["run_manifest"]
    required_keys = {
        "run_id",
        "timestamp_utc",
        "config_hash",
        "canonical_schema_version",
        "feature_flags",
        "pipeline_paths",
        "counts_per_stage",
        "shortlist_size_used",
        "orderbook_top_k_used",
        "data_freshness",
        "warnings",
        "duration_seconds",
    }

    assert required_keys.issubset(manifest.keys())
    assert manifest["warnings"] == ["orderbook_partial_fetch"]
    assert manifest["counts_per_stage"]["tradeability_stopped"] == 8
    assert manifest["feature_flags"]["decision_enabled"] is True
    assert manifest["feature_flags"]["btc_regime_enabled"] is False
    assert manifest["canonical_schema_version"] == "6.1.0"
    assert manifest["pipeline_paths"] == {"shadow_mode": "parallel", "legacy_path_enabled": True, "new_path_enabled": True, "primary_path": "legacy", "primary_path_source": "default"}
    assert report["trade_candidates"] == []


def test_save_reports_writes_separate_manifest_file(tmp_path: Path) -> None:
    generator = ReportGenerator({"output": {"reports_dir": str(tmp_path), "top_n_per_setup": 1}})

    report_paths = generator.save_reports(
        [],
        [],
        [],
        [],
        run_date="2026-03-08",
        metadata=_metadata_with_manifest_overrides(),
    )

    manifest_path = report_paths["manifest"]
    assert manifest_path.exists()
    assert manifest_path.name == "2026-03-08_2026-03-08_051355Z_001.manifest.json"

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["run_id"] == "2026-03-08_051355Z_001"
    assert payload["warnings"] == ["orderbook_partial_fetch"]


def test_run_manifest_warnings_default_to_empty_list() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 1}})

    report = generator.generate_json_report([], [], [], [], "2026-03-08", metadata={"asof_ts_ms": 1772946835000})

    assert report["run_manifest"]["warnings"] == []
