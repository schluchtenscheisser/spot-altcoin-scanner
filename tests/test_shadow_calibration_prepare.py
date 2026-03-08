from __future__ import annotations

import json
from pathlib import Path

from scanner.tools import prepare_shadow_calibration as prep


def _write_eval_jsonl(path: Path, candidate_rows: list[dict]) -> Path:
    rows = [
        {
            "type": "meta",
            "run_id": "RID",
            "dataset_schema_version": "1.3",
        },
        *candidate_rows,
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
    return path


def test_prepare_report_is_deterministic_and_keeps_calibration_inactive(tmp_path: Path, monkeypatch) -> None:
    dataset = _write_eval_jsonl(
        tmp_path / "eval.jsonl",
        [
            {
                "type": "candidate_setup",
                "record_id": "RID:2026-02-01:A:breakout:s1",
                "setup_type": "breakout",
                "score": 70.0,
                "hit10_5d": True,
                "hit20_5d": False,
                "mfe_5d_pct": 11.0,
                "mae_5d_pct": -3.0,
            },
            {
                "type": "candidate_setup",
                "record_id": "RID:2026-02-01:B:pullback:s2",
                "setup_type": "pullback",
                "score": 40.0,
                "hit10_5d": None,
                "hit20_5d": None,
                "mfe_5d_pct": None,
                "mae_5d_pct": None,
            },
        ],
    )

    monkeypatch.setattr(prep, "_utc_now", lambda: prep.datetime(2026, 3, 8, 1, 2, 3, tzinfo=prep.timezone.utc))
    first = prep.run(
        prep.build_parser().parse_args(
            [
                "--eval-dataset",
                str(dataset),
                "--output-dir",
                str(tmp_path),
                "--report-id",
                "R1",
                "--min-samples-total",
                "1",
                "--min-samples-per-setup",
                "1",
                "--min-rr-samples",
                "1",
            ]
        )
    )
    second = prep.run(
        prep.build_parser().parse_args(
            [
                "--eval-dataset",
                str(dataset),
                "--output-dir",
                str(tmp_path),
                "--report-id",
                "R1",
                "--min-samples-total",
                "1",
                "--min-samples-per-setup",
                "1",
                "--min-rr-samples",
                "1",
            ]
        )
    )

    first_payload = json.loads(first.read_text(encoding="utf-8"))
    second_payload = json.loads(second.read_text(encoding="utf-8"))
    assert first_payload == second_payload
    assert first_payload["summary"] == {
        "candidate_rows": 2,
        "evaluable_rows": 1,
        "not_evaluable_rows": 1,
        "invalid_rows": 0,
        "invalid_ratio": 0.0,
    }
    assert first_payload["calibration_state"]["active"] is False
    assert first_payload["calibration_state"]["threshold_adjustment"] is None


def test_prepare_report_emits_shadow_recommendation_when_sample_is_sufficient(tmp_path: Path) -> None:
    dataset = _write_eval_jsonl(
        tmp_path / "eval.jsonl",
        [
            {
                "type": "candidate_setup",
                "record_id": "RID:1",
                "setup_type": "breakout",
                "score": 55.0,
                "hit10_5d": True,
                "hit20_5d": False,
                "mfe_5d_pct": 14.0,
                "mae_5d_pct": -4.0,
            },
            {
                "type": "candidate_setup",
                "record_id": "RID:2",
                "setup_type": "breakout",
                "score": 65.0,
                "hit10_5d": True,
                "hit20_5d": True,
                "mfe_5d_pct": 22.0,
                "mae_5d_pct": -2.0,
            },
            {
                "type": "candidate_setup",
                "record_id": "RID:3",
                "setup_type": "pullback",
                "score": 45.0,
                "hit10_5d": False,
                "hit20_5d": False,
                "mfe_5d_pct": 4.0,
                "mae_5d_pct": -5.0,
            },
        ],
    )

    out = prep.run(
        prep.build_parser().parse_args(
            [
                "--eval-dataset",
                str(dataset),
                "--output-dir",
                str(tmp_path),
                "--report-id",
                "R_REC",
                "--min-samples-total",
                "3",
                "--min-samples-per-setup",
                "1",
                "--target-hit10-rate",
                "0.6",
                "--target-hit20-rate",
                "0.2",
                "--min-rr-samples",
                "2",
                "--rr-quantile",
                "0.5",
            ]
        )
    )
    payload = json.loads(out.read_text(encoding="utf-8"))

    recommendation = payload["shadow_recommendation"]
    assert recommendation["status"] == "ready"
    assert recommendation["recommended_thresholds"] == {
        "min_score_for_enter": 45.0,
        "min_rr_to_tp10": 2.5,
    }
    assert recommendation["shadow_probabilities"]["overall"] == {
        "p_hit10_5d_est": 0.666667,
        "p_hit20_5d_est": 0.333333,
    }


def test_prepare_report_uses_null_recommendations_for_insufficient_data(tmp_path: Path) -> None:
    dataset = _write_eval_jsonl(
        tmp_path / "eval.jsonl",
        [
            {
                "type": "candidate_setup",
                "record_id": "RID:2026-02-01:X:reversal:s1",
                "setup_type": "reversal",
                "score": 60.0,
                "hit10_5d": True,
                "hit20_5d": True,
                "mfe_5d_pct": 22.0,
                "mae_5d_pct": -4.0,
            }
        ],
    )

    out = prep.run(
        prep.build_parser().parse_args(
            [
                "--eval-dataset",
                str(dataset),
                "--output-dir",
                str(tmp_path),
                "--report-id",
                "R_SMALL",
                "--min-samples-total",
                "5",
            ]
        )
    )
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["shadow_recommendation"]["status"] == "insufficient_data"
    assert payload["shadow_recommendation"]["recommended_thresholds"] == {
        "min_score_for_enter": None,
        "min_rr_to_tp10": None,
    }
    assert payload["shadow_recommendation"]["shadow_probabilities"]["overall"] == {
        "p_hit10_5d_est": None,
        "p_hit20_5d_est": None,
    }


def test_prepare_report_flags_non_finite_values_explicitly(tmp_path: Path) -> None:
    dataset = _write_eval_jsonl(
        tmp_path / "eval.jsonl",
        [
            {
                "type": "candidate_setup",
                "record_id": "RID:2026-02-01:X:reversal:s1",
                "setup_type": "reversal",
                "score": float("inf"),
                "hit10_5d": True,
                "hit20_5d": True,
                "mfe_5d_pct": 22.0,
                "mae_5d_pct": -4.0,
            }
        ],
    )

    out = prep.run(prep.build_parser().parse_args(["--eval-dataset", str(dataset), "--output-dir", str(tmp_path), "--report-id", "R2"]))
    payload = json.loads(out.read_text(encoding="utf-8"))

    assert payload["summary"]["invalid_rows"] == 1
    assert payload["invalid_examples"][0]["error"] == "non_finite:score"
    assert payload["shadow_recommendation"]["status"] == "invalid_data"


def test_prepare_strict_mode_has_no_partial_write_on_invalid_rows(tmp_path: Path) -> None:
    dataset = _write_eval_jsonl(
        tmp_path / "eval.jsonl",
        [
            {
                "type": "candidate_setup",
                "record_id": "RID:2026-02-01:X:reversal:s1",
                "setup_type": "reversal",
                "score": 50.0,
                "hit10_5d": "yes",
                "hit20_5d": False,
                "mfe_5d_pct": 1.0,
                "mae_5d_pct": -1.0,
            }
        ],
    )

    report_path = tmp_path / "shadow_calibration_prep_R3.json"
    rc = prep.main(
        [
            "--eval-dataset",
            str(dataset),
            "--output-dir",
            str(tmp_path),
            "--report-id",
            "R3",
            "--strict",
        ]
    )

    assert rc == 1
    assert not report_path.exists()


def test_prepare_requires_candidate_rows(tmp_path: Path) -> None:
    dataset = _write_eval_jsonl(tmp_path / "eval.jsonl", [])

    rc = prep.main(
        [
            "--eval-dataset",
            str(dataset),
            "--output-dir",
            str(tmp_path),
        ]
    )

    assert rc == 1
