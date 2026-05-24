from __future__ import annotations

import json
import os
import subprocess
import sys


def _run(*args: str):
    env=os.environ.copy(); env["PYTHONPATH"]=os.getcwd(); return subprocess.run([sys.executable, "scripts/generate_replay_chunk_plan.py", *args], capture_output=True, text=True, env=env)


def test_full_chunk_generation(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run(
        "--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
        "--run-mode", "full_chunked",
        "--output-plan", str(out),
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(out.read_text(encoding="utf-8"))
    chunks = plan["chunks"]
    assert len(chunks) == 13
    assert chunks[0]["chunk_start"] == "2025-05-01"
    assert chunks[-1]["chunk_end"] == "2026-05-17"
    assert plan["scenario_id"] == "hsq_replay_2025_05_to_2026_05_v1"
    assert "T" in plan["replay_id"]


def test_full_chunk_has_no_gaps(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run("--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml", "--run-mode", "full_chunked", "--output-plan", str(out))
    assert result.returncode == 0, result.stderr
    plan = json.loads(out.read_text(encoding="utf-8"))
    chunks = plan["chunks"]
    for i in range(1, len(chunks)):
        assert chunks[i - 1]["chunk_end"] < chunks[i]["chunk_start"]


def test_replay_id_pass_through(tmp_path):
    out = tmp_path / "chunk_plan.json"
    rid = "2026-05-24T08:00:00Z"
    result = _run("--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml", "--run-mode", "full_chunked", "--replay-id", rid, "--output-plan", str(out))
    assert result.returncode == 0
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert plan["replay_id"] == rid


def test_single_chunk_valid_first_chunk(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run(
        "--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
        "--run-mode", "single_chunk",
        "--chunk-start", "2025-05-01",
        "--chunk-end", "2025-05-31",
        "--output-plan", str(out),
    )
    assert result.returncode == 0, result.stderr
    plan = json.loads(out.read_text(encoding="utf-8"))
    assert len(plan["chunks"]) == 1


def test_single_chunk_missing_start_fails(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run("--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml", "--run-mode", "single_chunk", "--chunk-end", "2025-05-31", "--output-plan", str(out))
    assert result.returncode != 0
    assert "chunk_start and chunk_end are required for single_chunk mode" in (result.stderr + result.stdout)


def test_single_chunk_mid_period_without_resume_fails_before_write(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run(
        "--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
        "--run-mode", "single_chunk",
        "--chunk-start", "2025-06-01",
        "--chunk-end", "2025-06-30",
        "--output-plan", str(out),
    )
    assert result.returncode != 0
    assert "resume_from_artifact is required" in (result.stderr + result.stdout)
    assert not out.exists()


def test_single_chunk_outside_window_fails(tmp_path):
    out = tmp_path / "chunk_plan.json"
    result = _run(
        "--scenario", "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
        "--run-mode", "single_chunk",
        "--chunk-start", "2025-04-30",
        "--chunk-end", "2025-05-31",
        "--resume-from-artifact", "x",
        "--output-plan", str(out),
    )
    assert result.returncode != 0
