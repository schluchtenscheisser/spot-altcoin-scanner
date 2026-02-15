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

    md = generator.generate_markdown_report([sample], [], [], "2026-02-20")

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

    report = generator.generate_json_report(reversals, breakouts, pullbacks, "2026-02-20")

    assert report["setups"]["reversals"][0]["raw_score"] == 80.0
    assert report["setups"]["reversals"][0]["penalty_multiplier"] == 0.875
    assert report["setups"]["breakouts"][0]["raw_score"] == 72.2
    assert report["setups"]["breakouts"][0]["penalty_multiplier"] == 0.9
    assert report["setups"]["pullbacks"][0]["raw_score"] == 75.0
    assert report["setups"]["pullbacks"][0]["penalty_multiplier"] == 0.8

    md = generator.generate_markdown_report(reversals, breakouts, pullbacks, "2026-02-20")
    assert md.count("**Score Details:**") == 3
