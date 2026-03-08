from __future__ import annotations

import argparse
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_LABEL_FIELDS = ("hit10_5d", "hit20_5d", "mfe_5d_pct", "mae_5d_pct")
_EPSILON = 1e-9


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw.strip()
        if not line:
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Invalid JSON object at line {line_no}")
        rows.append(payload)
    if not rows:
        raise ValueError("Evaluation dataset is empty")
    return rows


def _is_finite_or_none(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, bool):
        return True
    if isinstance(value, (int, float)):
        return math.isfinite(float(value))
    return False


def _bool_or_none(value: Any) -> bool:
    return value is None or isinstance(value, bool)


def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        v = float(value)
        if math.isfinite(v):
            return v
    return None


def _status_from_quality(*, invalid_rows: int, sample_ready: bool) -> str:
    if invalid_rows > 0:
        return "invalid_data"
    if not sample_ready:
        return "insufficient_data"
    return "ready"


def _derive_recommendation(
    recommendation_rows: list[dict[str, Any]],
    *,
    min_samples_total: int,
    min_samples_per_setup: int,
    target_hit10_rate: float,
    target_hit20_rate: float,
    min_rr_samples: int,
    rr_quantile: float,
    invalid_rows: int,
) -> dict[str, Any]:
    notes: list[str] = []

    n_total = len(recommendation_rows)
    sample_ready = n_total >= min_samples_total

    p_hit10_overall: float | None = None
    p_hit20_overall: float | None = None
    if sample_ready:
        p_hit10_overall = round(sum(1 for row in recommendation_rows if row["hit10_5d"] is True) / n_total, 6)
        p_hit20_overall = round(sum(1 for row in recommendation_rows if row["hit20_5d"] is True) / n_total, 6)

    setup_types = sorted({str(row.get("setup_type")) for row in recommendation_rows})
    by_setup: dict[str, dict[str, float | None]] = {}
    for setup in setup_types:
        rows_for_setup = [row for row in recommendation_rows if row.get("setup_type") == setup]
        if len(rows_for_setup) < min_samples_per_setup:
            by_setup[setup] = {"p_hit10_5d_est": None, "p_hit20_5d_est": None}
            continue
        by_setup[setup] = {
            "p_hit10_5d_est": round(sum(1 for row in rows_for_setup if row["hit10_5d"] is True) / len(rows_for_setup), 6),
            "p_hit20_5d_est": round(sum(1 for row in rows_for_setup if row["hit20_5d"] is True) / len(rows_for_setup), 6),
        }

    recommended_min_score_for_enter: float | None = None
    if sample_ready:
        sorted_scores = sorted({float(row["score"]) for row in recommendation_rows})
        for threshold in sorted_scores:
            subset = [row for row in recommendation_rows if float(row["score"]) >= threshold]
            if len(subset) < min_samples_total:
                continue
            hit10_rate = sum(1 for row in subset if row["hit10_5d"] is True) / len(subset)
            hit20_rate = sum(1 for row in subset if row["hit20_5d"] is True) / len(subset)
            if hit10_rate + _EPSILON >= target_hit10_rate and hit20_rate + _EPSILON >= target_hit20_rate:
                recommended_min_score_for_enter = round(float(threshold), 6)
                break
        if recommended_min_score_for_enter is None:
            notes.append("no_score_threshold_meets_constraints")

    realized_rr_values: list[float] = []
    for row in recommendation_rows:
        if row["hit10_5d"] is not True:
            continue
        mae = float(row["mae_5d_pct"])
        if mae >= -_EPSILON:
            continue
        realized_rr_values.append(10.0 / abs(mae))

    recommended_min_rr_to_tp10: float | None = None
    if len(realized_rr_values) >= min_rr_samples:
        sorted_rr = sorted(realized_rr_values)
        idx = int(round((len(sorted_rr) - 1) * rr_quantile))
        idx = min(max(idx, 0), len(sorted_rr) - 1)
        recommended_min_rr_to_tp10 = round(sorted_rr[idx], 6)

    if len(realized_rr_values) < min_rr_samples:
        notes.append("insufficient_rr_samples")

    status = _status_from_quality(invalid_rows=invalid_rows, sample_ready=sample_ready)
    if status != "ready":
        recommended_min_score_for_enter = None
        recommended_min_rr_to_tp10 = None

    return {
        "status": status,
        "recommended_thresholds": {
            "min_score_for_enter": recommended_min_score_for_enter,
            "min_rr_to_tp10": recommended_min_rr_to_tp10,
        },
        "shadow_probabilities": {
            "overall": {
                "p_hit10_5d_est": p_hit10_overall if status == "ready" else None,
                "p_hit20_5d_est": p_hit20_overall if status == "ready" else None,
            },
            "by_setup": by_setup,
        },
        "constraints": {
            "min_samples_total": min_samples_total,
            "min_samples_per_setup": min_samples_per_setup,
            "target_hit10_rate": target_hit10_rate,
            "target_hit20_rate": target_hit20_rate,
            "min_rr_samples": min_rr_samples,
            "rr_quantile": rr_quantile,
        },
        "notes": sorted(set(notes)),
    }


def build_shadow_calibration_prep_report(
    rows: list[dict[str, Any]],
    *,
    report_id: str,
    min_samples_total: int,
    min_samples_per_setup: int,
    target_hit10_rate: float,
    target_hit20_rate: float,
    min_rr_samples: int,
    rr_quantile: float,
) -> dict[str, Any]:
    meta = rows[0]
    if meta.get("type") != "meta":
        raise ValueError("First JSONL row must be meta")

    candidates = [row for row in rows[1:] if row.get("type") == "candidate_setup"]
    if not candidates:
        raise ValueError("No candidate_setup rows present")

    invalid_rows: list[dict[str, Any]] = []
    recommendation_rows: list[dict[str, Any]] = []
    for row in candidates:
        missing = [field for field in REQUIRED_LABEL_FIELDS if field not in row]
        if missing:
            invalid_rows.append({"record_id": row.get("record_id"), "error": f"missing_fields:{','.join(missing)}"})
            continue

        if not _bool_or_none(row.get("hit10_5d")) or not _bool_or_none(row.get("hit20_5d")):
            invalid_rows.append({"record_id": row.get("record_id"), "error": "invalid_boolean_label"})
            continue

        non_finite_fields = [
            field for field in ("mfe_5d_pct", "mae_5d_pct", "score") if not _is_finite_or_none(row.get(field))
        ]
        if non_finite_fields:
            invalid_rows.append(
                {"record_id": row.get("record_id"), "error": f"non_finite:{','.join(non_finite_fields)}"}
            )
            continue

        score = _finite_float(row.get("score"))
        mfe = _finite_float(row.get("mfe_5d_pct"))
        mae = _finite_float(row.get("mae_5d_pct"))
        if score is None or mfe is None or mae is None:
            continue

        if not isinstance(row.get("hit10_5d"), bool) or not isinstance(row.get("hit20_5d"), bool):
            continue

        recommendation_rows.append(
            {
                "setup_type": str(row.get("setup_type")),
                "score": score,
                "hit10_5d": row["hit10_5d"],
                "hit20_5d": row["hit20_5d"],
                "mfe_5d_pct": mfe,
                "mae_5d_pct": mae,
            }
        )

    evaluable = [
        row for row in candidates if isinstance(row.get("hit10_5d"), bool) and isinstance(row.get("hit20_5d"), bool)
    ]

    by_setup: dict[str, dict[str, int]] = {}
    for setup in sorted({str(row.get("setup_type")) for row in candidates}):
        rows_for_setup = [row for row in candidates if row.get("setup_type") == setup]
        by_setup[setup] = {
            "rows": len(rows_for_setup),
            "evaluable_rows": sum(
                1
                for row in rows_for_setup
                if isinstance(row.get("hit10_5d"), bool) and isinstance(row.get("hit20_5d"), bool)
            ),
        }

    shadow_recommendation = _derive_recommendation(
        recommendation_rows,
        min_samples_total=min_samples_total,
        min_samples_per_setup=min_samples_per_setup,
        target_hit10_rate=target_hit10_rate,
        target_hit20_rate=target_hit20_rate,
        min_rr_samples=min_rr_samples,
        rr_quantile=rr_quantile,
        invalid_rows=len(invalid_rows),
    )

    return {
        "type": "shadow_calibration_prep_report",
        "report_id": report_id,
        "generated_at_iso": _utc_iso(_utc_now()),
        "source_run_id": meta.get("run_id"),
        "source_dataset_schema_version": meta.get("dataset_schema_version"),
        "summary": {
            "candidate_rows": len(candidates),
            "evaluable_rows": len(evaluable),
            "not_evaluable_rows": len(candidates) - len(evaluable),
            "invalid_rows": len(invalid_rows),
            "invalid_ratio": round(len(invalid_rows) / len(candidates), 6),
        },
        "setup_type_summary": by_setup,
        "invalid_examples": sorted(invalid_rows, key=lambda row: (str(row.get("record_id")), str(row.get("error"))))[:20],
        "shadow_recommendation": shadow_recommendation,
        "calibration_state": {
            "active": False,
            "threshold_adjustment": None,
            "notes": "Preparation only. No productive threshold changes are applied.",
        },
    }


def _write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build a shadow-calibration preparation report from evaluation JSONL")
    parser.add_argument("--eval-dataset", required=True, help="Path to eval_*.jsonl")
    parser.add_argument("--output-dir", default="artifacts/shadow_calibration", help="Report output directory")
    parser.add_argument("--report-id", default=None, help="Optional deterministic report id")
    parser.add_argument("--strict", action="store_true", help="Fail if invalid rows are detected; no output is written")
    parser.add_argument("--min-samples-total", type=int, default=30)
    parser.add_argument("--min-samples-per-setup", type=int, default=10)
    parser.add_argument("--target-hit10-rate", type=float, default=0.55)
    parser.add_argument("--target-hit20-rate", type=float, default=0.20)
    parser.add_argument("--min-rr-samples", type=int, default=20)
    parser.add_argument("--rr-quantile", type=float, default=0.6)
    return parser


def run(args: argparse.Namespace) -> Path:
    rows = _load_jsonl(Path(args.eval_dataset))
    generated_at = _utc_now()
    report_id = args.report_id or generated_at.strftime("%Y-%m-%d_%H%M%SZ")

    report = build_shadow_calibration_prep_report(
        rows,
        report_id=report_id,
        min_samples_total=int(args.min_samples_total),
        min_samples_per_setup=int(args.min_samples_per_setup),
        target_hit10_rate=float(args.target_hit10_rate),
        target_hit20_rate=float(args.target_hit20_rate),
        min_rr_samples=int(args.min_rr_samples),
        rr_quantile=float(args.rr_quantile),
    )
    if args.strict and int(report["summary"]["invalid_rows"]) > 0:
        raise ValueError("Invalid rows detected in strict mode")

    output_path = Path(args.output_dir) / f"shadow_calibration_prep_{report_id}.json"
    _write_json_atomic(output_path, report)
    return output_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        out = run(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(str(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
