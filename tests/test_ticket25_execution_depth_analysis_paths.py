from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_forbidden_output_root_rejected() -> None:
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--output-json",
        "reports/runs/nope.json",
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "Forbidden output path" in (proc.stdout + proc.stderr)


def test_forbidden_output_root_rejected_absolute_path() -> None:
    absolute = (Path.cwd() / "reports" / "runs" / "abs.json").as_posix()
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--output-json",
        absolute,
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "Forbidden output path" in (proc.stdout + proc.stderr)


def test_forbidden_output_root_rejected_traversal() -> None:
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--output-json",
        "reports/aux/../runs/out.json",
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "Forbidden output path" in (proc.stdout + proc.stderr)


def test_invalid_top_n_rejected() -> None:
    proc = subprocess.run([
        sys.executable,
        "scripts/analyze_execution_depth_shadow_live.py",
        "--top-n",
        "0",
    ], capture_output=True, text=True)
    assert proc.returncode != 0
    assert "--top-n must be >= 1" in (proc.stdout + proc.stderr)
