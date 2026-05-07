from __future__ import annotations

from pathlib import Path
import sqlite3

from scripts import shadow_live_state as state


def _create_state_db(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    try:
        conn.execute("CREATE TABLE state_machine_context (symbol TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO state_machine_context(symbol) VALUES ('SOLUSDT')")
        conn.commit()
    finally:
        conn.close()


def test_sqlite_state_validation_requires_integrity_and_state_table(tmp_path: Path) -> None:
    valid = tmp_path / "valid.sqlite"
    _create_state_db(valid)
    assert state._sqlite_state_is_valid(valid) is True

    missing_table = tmp_path / "missing-table.sqlite"
    conn = sqlite3.connect(missing_table)
    try:
        conn.execute("CREATE TABLE other_table (id INTEGER PRIMARY KEY)")
        conn.commit()
    finally:
        conn.close()
    assert state._sqlite_state_is_valid(missing_table) is False

    empty = tmp_path / "empty.sqlite"
    empty.write_bytes(b"")
    assert state._sqlite_state_is_valid(empty) is False


def test_restore_state_excludes_current_run_and_reports_cold_start(tmp_path: Path, monkeypatch) -> None:
    def fake_gh_json(args):
        if args[:2] == ["run", "list"]:
            return [{"databaseId": 123, "conclusion": "success"}]
        raise AssertionError(f"artifact lookup should not run for current run: {args}")

    monkeypatch.setattr(state, "_run_gh_json", fake_gh_json)

    status = state.restore_state(
        workdir=tmp_path / "workdir",
        repo="owner/repo",
        workflow="independence-shadow-live.yml",
        branch="main",
        current_run_id="123",
        limit=20,
        restore_dir=tmp_path / "restore",
    )

    assert status == "cold_start"
    assert not (tmp_path / "workdir" / "data" / "independence_release.sqlite").exists()


def test_restore_state_copies_valid_artifact_to_data_db(tmp_path: Path, monkeypatch) -> None:
    restored_db = tmp_path / "restore" / "independence_release.sqlite"

    def fake_gh_json(args):
        if args[:2] == ["run", "list"]:
            return [{"databaseId": 456, "conclusion": "success"}]
        if args[:1] == ["api"]:
            return {"artifacts": [{"name": "shadow-live-state", "expired": False}]}
        raise AssertionError(f"unexpected gh json args: {args}")

    def fake_run_command(args, *, cwd=None):
        _ = cwd
        assert args[:3] == ["gh", "run", "download"]
        _create_state_db(restored_db)
        return type("Result", (), {"returncode": 0, "stdout": "", "stderr": ""})()

    monkeypatch.setattr(state, "_run_gh_json", fake_gh_json)
    monkeypatch.setattr(state, "_run_command", fake_run_command)

    workdir = tmp_path / "workdir"
    status = state.restore_state(
        workdir=workdir,
        repo="owner/repo",
        workflow="independence-shadow-live.yml",
        branch="main",
        current_run_id="123",
        limit=20,
        restore_dir=tmp_path / "restore",
    )

    target = workdir / "data" / "independence_release.sqlite"
    assert status == "restored"
    assert state._sqlite_state_is_valid(target) is True


def test_checkpoint_and_stage_state_uploads_single_root_db_file(tmp_path: Path) -> None:
    workdir = tmp_path / "workdir"
    db_path = workdir / "data" / "independence_release.sqlite"
    _create_state_db(db_path)
    wal = workdir / "data" / "independence_release.sqlite-wal"
    shm = workdir / "data" / "independence_release.sqlite-shm"
    wal.write_text("do-not-upload", encoding="utf-8")
    shm.write_text("do-not-upload", encoding="utf-8")

    staged = state.checkpoint_and_stage_state(workdir=workdir, upload_dir=tmp_path / "upload")

    assert staged == tmp_path / "upload" / "independence_release.sqlite"
    assert staged.is_file()
    assert sorted(path.name for path in staged.parent.iterdir()) == ["independence_release.sqlite"]
