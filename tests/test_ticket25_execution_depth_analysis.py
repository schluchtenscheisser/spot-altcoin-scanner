from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def _report(run_id: str, day: str, as_of: str, mode: str = "daily") -> dict:
    c = {"structural": 2, "execution_attempted": 2, "executable": 1, "direct_ok": 1, "tranche_ok": 0, "marginal": 0, "failed": 1, "unknown_execution": 0, "unexpected_execution_state": 0, "not_attempted": 0}
    return {
        "run_id": run_id,
        "scan_mode": mode,
        "daily_bar_id": day,
        "as_of_utc": as_of,
        "execution_aware_summary": c,
        "execution_counts_by_bucket": {"confirmed_candidates": c, "early_candidates": {k: 0 for k in c}, "watchlist": {k: 0 for k in c}, "late_monitor": {k: 0 for k in c}},
        "execution_counts_by_universe_category": {"classic_crypto": c},
        "execution_counts_by_bucket_and_category": {"confirmed_candidates": {"classic_crypto": c}, "early_candidates": {}, "watchlist": {}, "late_monitor": {}},
        "execution_aware_candidate_segments": {
            "confirmed_failed": [{"symbol": "AAAUSDT", "bucket": "confirmed_candidates", "universe_category": "classic_crypto", "execution_reason_raw": "depth_1pct_insufficient"}],
            "confirmed_direct_ok": [{"symbol": "BBBUSDT", "bucket": "confirmed_candidates", "universe_category": "classic_crypto", "execution_reason_raw": None}],
        },
    }


def test_script_aggregates_and_writes(tmp_path: Path) -> None:
    runs = tmp_path / "reports" / "runs" / "2026" / "05" / "01"
    r1 = runs / "r1"
    r2 = runs / "r2"
    r1.mkdir(parents=True)
    r2.mkdir(parents=True)
    (r1 / "report.json").write_text(json.dumps(_report("r1", "2026-05-01", "2026-05-01T01:00:00Z")), encoding="utf-8")
    (r2 / "report.json").write_text(json.dumps(_report("r2", "2026-05-02", "2026-05-02T01:00:00Z")), encoding="utf-8")
    out_json = tmp_path / "reports" / "aux" / "out.json"
    out_md = tmp_path / "reports" / "aux" / "out.md"

    subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--reports-root",
        str(tmp_path / "reports" / "runs"),
        "--output-json",
        str(out_json),
        "--output-md",
        str(out_md),
        "--top-n",
        "5",
    ], check=True)

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["schema_version"] == "t25_execution_depth_analysis_v1"
    assert data["summary"]["total_structural"] == 4
    assert data["by_bucket"]["confirmed_candidates"]["failed"] == 2
    assert data["execution_reason_counts"]["depth_1pct_insufficient"] == 2
    assert out_md.exists()


def test_missing_t24_block_fails(tmp_path: Path) -> None:
    rd = tmp_path / "rd"
    rd.mkdir()
    (rd / "report.json").write_text(json.dumps({"run_id": "x", "scan_mode": "daily", "daily_bar_id": "2026-05-01", "as_of_utc": "2026-05-01T00:00:00Z"}), encoding="utf-8")
    proc = subprocess.run([sys.executable, "scripts/analyze_execution_depth_shadow_live.py", "--run-dir", str(rd)], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "T25 requires T24 execution-aware report fields" in (proc.stderr + proc.stdout)


def test_empty_reports_root_fails_without_outputs(tmp_path: Path) -> None:
    out_json = tmp_path / "reports" / "aux" / "none.json"
    out_md = tmp_path / "reports" / "aux" / "none.md"
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--reports-root",
        str(tmp_path / "reports" / "runs"),
        "--output-json",
        str(out_json),
        "--output-md",
        str(out_md),
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "No analyzable T24 execution-aware reports were found." in (proc.stderr + proc.stdout)
    assert not out_json.exists()
    assert not out_md.exists()


def test_discovery_only_non_daily_fails(tmp_path: Path) -> None:
    run_dir = tmp_path / "reports" / "runs" / "2026" / "05" / "02" / "r1"
    run_dir.mkdir(parents=True)
    (run_dir / "report.json").write_text(json.dumps(_report("r1", "2026-05-02", "2026-05-02T00:00:00Z", mode="intraday")), encoding="utf-8")
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--reports-root",
        str(tmp_path / "reports" / "runs"),
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "No analyzable T24 execution-aware reports were found." in (proc.stderr + proc.stdout)
