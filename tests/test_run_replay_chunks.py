from __future__ import annotations

import json
from pathlib import Path

import importlib.util

SPEC = importlib.util.spec_from_file_location("run_replay_chunks", "scripts/run_replay_chunks.py")
run_replay_chunks = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(run_replay_chunks)


def _write_plan(tmp_path: Path, chunks: list[dict]) -> Path:
    plan = {
        "scenario_id": "scenario_x",
        "replay_id": "2026-05-24T08:00:00Z",
        "scenario_path": "configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml",
        "chunks": chunks,
    }
    p = tmp_path / "chunk_plan.json"
    p.write_text(json.dumps(plan), encoding="utf-8")
    return p


def test_sequential_state_handoff(monkeypatch, tmp_path):
    chunks = [
        {"chunk_id": "2025-05-01_to_2025-05-31", "chunk_start": "2025-05-01", "chunk_end": "2025-05-31"},
        {"chunk_id": "2025-06-01_to_2025-06-30", "chunk_start": "2025-06-01", "chunk_end": "2025-06-30"},
    ]
    plan = _write_plan(tmp_path, chunks)
    output_root = tmp_path / "evaluation" / "replay"
    calls = []

    def fake_run(cmd, check=False):
        calls.append(cmd)
        chunk_id = cmd[cmd.index("--chunk-id") + 1]
        state = output_root / "runs" / "scenario_x" / "2026-05-24T08:00:00Z" / "chunks" / chunk_id / "state_final.sqlite"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("ok", encoding="utf-8")
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(run_replay_chunks.subprocess, "run", fake_run)
    argv = ["x", "--scenario", "s", "--chunk-plan", str(plan), "--output-root", str(output_root)]
    monkeypatch.setattr("sys.argv", argv)
    assert run_replay_chunks.main() == 0
    assert "--resume-from-state" not in calls[0]
    assert "--resume-from-state" in calls[1]


def test_resume_state_dir_rules(monkeypatch, tmp_path):
    resume = tmp_path / "resume"
    resume.mkdir()
    with open(resume / "state_final.sqlite", "w", encoding="utf-8") as f:
        f.write("x")
    chunks = [{"chunk_id": "a", "chunk_start": "2025-05-01", "chunk_end": "2025-05-31"}]
    plan = _write_plan(tmp_path, chunks)
    output_root = tmp_path / "evaluation" / "replay"

    def fake_run(cmd, check=False):
        state = output_root / "runs" / "scenario_x" / "2026-05-24T08:00:00Z" / "chunks" / "a" / "state_final.sqlite"
        state.parent.mkdir(parents=True, exist_ok=True)
        state.write_text("ok", encoding="utf-8")
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(run_replay_chunks.subprocess, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["x", "--scenario", "s", "--chunk-plan", str(plan), "--output-root", str(output_root), "--resume-state-dir", str(resume)])
    assert run_replay_chunks.main() == 0


def test_resume_state_dir_zero_or_multiple_fail(tmp_path):
    zero = tmp_path / "z"
    zero.mkdir()
    try:
        run_replay_chunks._find_single_state_file(zero)
        assert False
    except SystemExit:
        pass
    multi = tmp_path / "m"
    (multi / "a").mkdir(parents=True)
    (multi / "b").mkdir(parents=True)
    (multi / "a" / "state_final.sqlite").write_text("1", encoding="utf-8")
    (multi / "b" / "state_final.sqlite").write_text("2", encoding="utf-8")
    try:
        run_replay_chunks._find_single_state_file(multi)
        assert False
    except SystemExit:
        pass


def test_missing_state_aborts_next_chunk(monkeypatch, tmp_path):
    chunks = [
        {"chunk_id": "c1", "chunk_start": "2025-05-01", "chunk_end": "2025-05-31"},
        {"chunk_id": "c2", "chunk_start": "2025-06-01", "chunk_end": "2025-06-30"},
    ]
    plan = _write_plan(tmp_path, chunks)
    output_root = tmp_path / "evaluation" / "replay"
    calls = []

    def fake_run(cmd, check=False):
        calls.append(cmd)
        return type("R", (), {"returncode": 0})()

    monkeypatch.setattr(run_replay_chunks.subprocess, "run", fake_run)
    monkeypatch.setattr("sys.argv", ["x", "--scenario", "s", "--chunk-plan", str(plan), "--output-root", str(output_root)])
    assert run_replay_chunks.main() == 1
    assert len(calls) == 1
