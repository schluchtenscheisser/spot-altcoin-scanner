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
