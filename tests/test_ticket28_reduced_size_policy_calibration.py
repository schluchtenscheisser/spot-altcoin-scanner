from __future__ import annotations

import gzip
import json
import subprocess
import sys
import zipfile
from pathlib import Path

from scripts import analyze_reduced_size_policy_calibration as t28

DATES = ["2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06", "2026-05-07"]


def _zip_for_day(base: Path, day: str, rows: list[dict], *, daily: bool = True, intraday: bool = False) -> None:
    zp = base / f"run_{day}.zip"
    mode = "a" if zp.exists() else "w"
    with zipfile.ZipFile(zp, mode) as zf:
        if daily:
            inner = f"reports/runs/{day.replace('-', '/')}/daily-{day}-abc/symbol_diagnostics.jsonl.gz"
            payload = "\n".join(json.dumps(r) for r in rows).encode()
            zf.writestr(inner, gzip.compress(payload))
        if intraday:
            inner = f"reports/runs/{day.replace('-', '/')}/intraday-{day}-abc/symbol_diagnostics.jsonl.gz"
            payload = "\n".join(json.dumps(r) for r in rows).encode()
            zf.writestr(inner, gzip.compress(payload))


def _row(symbol: str, status: str, *, bucket: str = "confirmed_candidates", depth: float | None = 50_000.0, spread: float | None = 0.1, slippage: float | None = None, score: float = 50.0) -> dict:
    return {
        "symbol": symbol,
        "execution_attempted": True,
        "execution_status_raw": status,
        "execution_reason_raw": "fixture",
        "execution_pass": status == "direct_ok",
        "execution_grade_t16": 40.0 if status == "marginal" else 0.0,
        "available_depth_1pct_usdt": depth,
        "depth_threshold_1pct_usdt": 200_000.0,
        "available_depth_ratio": None if depth is None else depth / 200_000.0,
        "depth_ratio_band": "fixture",
        "recommended_position_factor_preview": None,
        "execution_limiting_metric": "depth",
        "spread_pct": spread,
        "estimated_slippage_bps": slippage,
        "orderbook_snapshot_age_ms": 1000,
        "bid_depth_1pct_usdt": depth,
        "ask_depth_1pct_usdt": depth,
        "depth_side_used": "ask",
        "decision": {
            "decision_bucket": bucket,
            "priority_score": score,
            "entry_pattern": "breakout",
            "entry_pattern_score": 60.0,
        },
        "state": {"state_machine_state": "confirmed_ready", "state_confidence": 70.0},
        "phase": {"market_phase": "bull", "market_phase_confidence": 80.0},
    }


def _run(inp: Path, out: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/analyze_reduced_size_policy_calibration.py", "--input-dir", str(inp), "--output-dir", str(out)],
        check=False,
        capture_output=True,
        text=True,
    )


def _complete_input(base: Path, rows: list[dict] | None = None) -> None:
    for day in DATES:
        _zip_for_day(base, day, rows or [_row("MARG", "marginal"), _row("DIRECT", "direct_ok"), _row("UNK", "unknown", bucket="watchlist")], intraday=True)


def test_archive_selection_daily_manifest_and_errors(tmp_path: Path) -> None:
    inp = tmp_path / "in"
    inp.mkdir()
    out = tmp_path / "reports" / "aux" / "out"
    _complete_input(inp)
    proc = _run(inp, out)
    assert proc.returncode == 0, proc.stderr
    manifest = (out / "run_input_manifest.md").read_text()
    assert "daily-2026-05-03" in manifest
    assert "intraday" not in manifest
    assert "unknown_count" in manifest

    missing = tmp_path / "missing"
    missing.mkdir()
    for day in DATES[:-1]:
        _zip_for_day(missing, day, [_row("A", "marginal")])
    proc_missing = _run(missing, tmp_path / "reports" / "aux" / "missing-out")
    assert proc_missing.returncode != 0
    assert "Missing expected dates" in (proc_missing.stdout + proc_missing.stderr)

    zero = tmp_path / "zero"
    zero.mkdir()
    for day in DATES:
        _zip_for_day(zero, day, [] if day == DATES[0] else [_row("A", "marginal")])
    proc_zero = _run(zero, tmp_path / "reports" / "aux" / "zero-out")
    assert proc_zero.returncode != 0
    assert "zero records" in (proc_zero.stdout + proc_zero.stderr)


def test_scenario_mapping_boundaries() -> None:
    assert t28.scenario_band(100_000.0, "target_10k") == (1.0, "full", 1.0, "full")
    assert t28.scenario_band(75_000.0, "target_10k") == (0.75, "reduced_75", 0.75, "reduced_75")
    assert t28.scenario_band(50_000.0, "target_10k") == (0.5, "reduced_50", 0.5, "reduced_50")
    assert t28.scenario_band(25_000.0, "target_10k") == (0.25, "reduced_25", 0.25, "reduced_25")
    assert t28.scenario_band(24_999.0, "target_10k")[1:] == ("below_min", 0.0, "observe_only")
    assert t28.scenario_band(None, "target_10k") == (None, "not_evaluable", None, "not_evaluable")


def test_fail_sanity_manual_review_threshold(tmp_path: Path) -> None:
    inp = tmp_path / "in"
    inp.mkdir()
    _complete_input(inp, [_row("FAIL_LOW", "fail", depth=24_999.0), _row("FAIL_EDGE", "fail", depth=25_000.0)])
    out = tmp_path / "reports" / "aux" / "out"
    proc = _run(inp, out)
    assert proc.returncode == 0, proc.stderr
    report = (out / "fail_sanity_check.md").read_text()
    policy = (out / "recommended_policy.md").read_text()
    assert "fail_count_reaching_reduced_25_target_10k: 5" in report
    assert "Manual review required" in report
    assert "Fail policy status: manual-review-required" in policy


def test_marginal_unknown_spread_slippage_and_ranking(tmp_path: Path) -> None:
    inp = tmp_path / "in"
    inp.mkdir()
    rows = [
        _row("DIRECT", "direct_ok", score=70),
        _row("MARG_ELIG", "marginal", depth=25_000, spread=0.10, score=40),
        _row("MARG_OBS", "marginal", depth=24_999, spread=None, score=30),
        _row("MARG_NE", "marginal", depth=None, spread=0.01, score=20),
        _row("MARG_OTHER_BUCKET", "marginal", bucket="watchlist", depth=50_000, score=90),
        _row("UNK", "unknown", bucket="confirmed_candidates", depth=100_000, score=100),
    ]
    _complete_input(inp, rows)
    out = tmp_path / "reports" / "aux" / "out"
    proc = _run(inp, out)
    assert proc.returncode == 0, proc.stderr
    marginal = [json.loads(line) for line in (out / "marginal_candidates_full.jsonl").read_text().splitlines()]
    target = [r for r in marginal if r["scenario_id"] == "target_10k"]
    by_symbol = {r["symbol"]: r for r in target}
    assert by_symbol["MARG_ELIG"]["scenario_tradeability_class"] == "reduced_25"
    assert by_symbol["MARG_ELIG"]["reduced_size_eligible"] is True
    assert by_symbol["MARG_OBS"]["scenario_tradeability_class"] == "observe_only"
    assert by_symbol["MARG_OBS"]["reduced_size_eligible"] is False
    assert by_symbol["MARG_NE"]["scenario_tradeability_class"] == "not_evaluable"
    assert "MARG_OTHER_BUCKET" not in by_symbol
    assert "UNK" not in by_symbol
    spread = (out / "spread_slippage_by_band.md").read_text()
    assert "Slippage data is only partially available" in spread
    assert "eligible_remaining_derivable_spread_only" in spread
    grade = (out / "grade_mapping_sensitivity.md").read_text()
    assert "strict_tradeable_only" in grade
    availability = (out / "candidate_availability_by_day.md").read_text()
    assert "unknown_bucket_distribution" in availability


def test_output_path_safety(tmp_path: Path) -> None:
    inp = tmp_path / "in"
    inp.mkdir()
    _complete_input(inp)
    proc = subprocess.run(
        [sys.executable, "scripts/analyze_reduced_size_policy_calibration.py", "--input-dir", str(inp), "--output-dir", "reports/runs/bad"],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "Forbidden output path" in (proc.stdout + proc.stderr)
    assert not Path("reports/runs/bad").exists()

    proc2 = subprocess.run(
        [sys.executable, "scripts/analyze_reduced_size_policy_calibration.py", "--input-dir", str(inp), "--output-dir", "reports/aux/../analysis/evil"],
        capture_output=True,
        text=True,
    )
    assert proc2.returncode != 0
    assert "Forbidden output path" in (proc2.stdout + proc2.stderr)
