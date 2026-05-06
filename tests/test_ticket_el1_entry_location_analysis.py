from __future__ import annotations

import gzip
import json
import subprocess
import sys
import zipfile
from pathlib import Path


def _zip_for_day(base: Path, day: str, rows: list[dict]) -> Path:
    zip_path = base / f"run_{day}.zip"
    inner = f"reports/runs/{day.replace('-', '/')}/daily-{day}-abc123/symbol_diagnostics.jsonl.gz"
    payload = "\n".join(json.dumps(row) for row in rows).encode("utf-8")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(inner, gzip.compress(payload))
    return zip_path


def _row(
    symbol: str,
    *,
    bucket: str = "confirmed_candidates",
    bars_confirmed: int | None = 0,
    bars_early: int | None = None,
    bars_state: int | None = None,
    data_4h_available: bool = True,
    execution_status_raw: str = "direct_ok",
    pattern: str = "early_reversal_break",
    phase: str = "transition_reclaim",
    proxies: dict | None = None,
    direct_4h: dict | None = None,
) -> dict:
    axes = {
        "expansion_progress_structural": 80.0,
        "freshness_distance_structural": 60.0,
        "reclaim_progress": 70.0,
        "reacceleration_strength_simplified": 90.0,
        "volume_regime_shift": 50.0,
        "pullback_quality_simplified": None,
    }
    if proxies:
        axes.update(proxies)
    row = {
        "schema_version": "ir1.0",
        "run_id": f"run-{symbol}",
        "scan_mode": "daily",
        "symbol": symbol,
        "data_4h_available": data_4h_available,
        "axes": axes,
        "decision": {"decision_bucket": bucket, "priority_score": 75.0},
        "pattern": {"entry_pattern": pattern, "entry_pattern_score": 65.0},
        "phase": {"market_phase": phase, "market_phase_confidence": 80.0},
        "state": {
            "state_machine_state": "confirmed_ready" if bucket == "confirmed_candidates" else "early_ready",
            "bars_since_confirmed_entered": bars_confirmed,
            "bars_since_early_entered": bars_early,
            "bars_since_state_entered": bars_confirmed if bucket == "confirmed_candidates" else (bars_early if bars_state is None else bars_state),
            "close_at_confirmed_entry_bar": 1.0 if bars_confirmed is not None else None,
            "distance_from_ideal_entry_after_confirmed": None,
            "freshness_distance_state_confirmed": None,
        },
        "execution_status_raw": execution_status_raw,
    }
    if direct_4h:
        row.update(direct_4h)
    return row


def _run(input_dir: Path, output_dir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/analyze_entry_location_shadow_live.py", "--input-dir", str(input_dir), "--output-dir", str(output_dir)],
        check=True,
        capture_output=True,
        text=True,
    )


def test_step_a_outputs_preserve_nulls_nested_fields_and_skip_step_b(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "reports" / "aux" / "entry_location_analysis"
    input_dir.mkdir()
    _zip_for_day(
        input_dir,
        "2026-05-01",
        [
            _row("RENDERUSDT", proxies={"pullback_quality_simplified": None}),
            _row("DOTUSDT", bars_confirmed=2, execution_status_raw="marginal"),
            _row("AVAXUSDT", bucket="early_candidates", bars_confirmed=None, bars_early=0),
            _row("PEPEUSDT", bucket="early_candidates", bars_confirmed=None, bars_early=3, bars_state=0),
            _row("NO4H", data_4h_available=False),
            {
                **_row("TOPLEVEL_TRAP"),
                "decision_bucket": "confirmed_candidates",
                "entry_pattern": "wrong_top_level_pattern",
                "market_phase": "wrong_top_level_phase",
                "priority_score": 99.0,
            },
        ],
    )

    result = _run(input_dir, output_dir)

    assert "[T_EL1 Step B] Required 4h fields not found in diagnostics. Step B skipped." in result.stdout
    assert (output_dir / "step_a_population_distributions.md").exists()
    assert (output_dir / "step_a_named_candidates.md").exists()
    assert (output_dir / "step_a_day0_volume_summary.md").exists()
    assert (output_dir / "step_a_findings_and_field_requirements.md").exists()
    assert not (output_dir / "step_b_threshold_candidates.md").exists()

    distributions = (output_dir / "step_a_population_distributions.md").read_text()
    assert "Excluded records with `data_4h_available == False`: 1" in distributions
    assert "Null proxy values are counted separately" in distributions
    assert "| `early_reversal_break` | 2 |" in distributions
    assert "wrong_top_level_pattern" not in distributions

    named = (output_dir / "step_a_named_candidates.md").read_text()
    assert "RENDERUSDT" in named
    assert "DOTUSDT" not in named  # Day-1+ confirmed is not Population 1.

    summary = (output_dir / "step_a_day0_volume_summary.md").read_text()
    assert "| 2026-05-01 | 3 | 2 | 1 | 66.67% | 2 | 0 |" in summary

    findings = (output_dir / "step_a_findings_and_field_requirements.md").read_text()
    assert "`close_vs_ema20_4h_pct`" in findings
    assert "`distance_to_last_structural_anchor_pct_abs`" in findings
    assert "`distance_to_range_high_pct_abs`" in findings
    assert "`bars_since_last_structural_break_4h`" in findings
    assert "Population 3 (Day-0 early) contains 2 records." in findings


def test_step_b_runs_when_direct_fields_are_present(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "out"
    input_dir.mkdir()
    _zip_for_day(
        input_dir,
        "2026-05-02",
        [
            _row(
                "PEPEUSDT",
                pattern="early_reversal_break",
                direct_4h={"close_vs_ema20_4h_pct": 2.0, "bars_above_ema20_4h": 3, "dist_to_ema20_4h_pct_abs": 2.0},
            ),
            _row(
                "DOGEUSDT",
                pattern="shallow_pullback",
                direct_4h={"close_vs_ema20_4h_pct": 7.0, "bars_above_ema20_4h": 5, "dist_to_ema20_4h_pct_abs": 7.0},
            ),
        ],
    )

    _run(input_dir, output_dir)

    thresholds = (output_dir / "step_b_threshold_candidates.md").read_text()
    assert "`ideal`" in thresholds
    assert "Pattern-specific thresholds justified: True" in thresholds
    extended = (output_dir / "step_b_named_candidates_extended.md").read_text()
    assert "PEPEUSDT" in extended
    assert "DOGEUSDT" in extended


def test_output_path_safety(tmp_path: Path) -> None:
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    _zip_for_day(input_dir, "2026-05-03", [_row("RENDERUSDT")])

    result = subprocess.run(
        [
            sys.executable,
            "scripts/analyze_entry_location_shadow_live.py",
            "--input-dir",
            str(input_dir),
            "--output-dir",
            "reports/runs/bad-entry-location",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode != 0
    assert "Forbidden output path" in (result.stdout + result.stderr)
