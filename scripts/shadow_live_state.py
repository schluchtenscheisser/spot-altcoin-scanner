from __future__ import annotations

import argparse
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
from typing import Any, Sequence

STATE_ARTIFACT_NAME = "shadow-live-state"
STATE_DB_NAME = "independence_release.sqlite"
STATE_DB_RELATIVE_PATH = Path("data") / STATE_DB_NAME
VALID_RESTORE_STATUSES = {"cold_start", "cold_start_reset", "restored", "restore_failed"}


def _run_command(args: Sequence[str], *, cwd: Path | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=cwd, check=False, text=True, capture_output=True)


def _run_gh_json(args: Sequence[str]) -> Any:
    result = _run_command(["gh", *args])
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"gh {' '.join(args)} failed")
    payload = result.stdout.strip()
    return json.loads(payload) if payload else None


def _sqlite_state_is_valid(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    try:
        connection = sqlite3.connect(path)
        try:
            integrity = connection.execute("PRAGMA integrity_check;").fetchone()
            if integrity is None or integrity[0] != "ok":
                return False
            table = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='state_machine_context';"
            ).fetchone()
            return table is not None and table[0] == "state_machine_context"
        finally:
            connection.close()
    except sqlite3.Error:
        return False


def _candidate_run_ids(*, repo: str, workflow: str, branch: str, current_run_id: str | None, limit: int) -> list[str]:
    runs = _run_gh_json(
        [
            "run",
            "list",
            "--repo",
            repo,
            "--workflow",
            workflow,
            "--branch",
            branch,
            "--status",
            "success",
            "--limit",
            str(limit),
            "--json",
            "databaseId,conclusion",
        ]
    )
    if not isinstance(runs, list):
        return []
    candidates: list[str] = []
    for run in runs:
        if not isinstance(run, dict) or run.get("conclusion") != "success":
            continue
        run_id = str(run.get("databaseId") or "").strip()
        if not run_id or run_id == str(current_run_id or "").strip():
            continue
        candidates.append(run_id)
    return candidates


def _run_has_state_artifact(*, repo: str, run_id: str) -> bool:
    payload = _run_gh_json(["api", f"repos/{repo}/actions/runs/{run_id}/artifacts"])
    artifacts = payload.get("artifacts") if isinstance(payload, dict) else None
    if not isinstance(artifacts, list):
        return False
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            continue
        if artifact.get("name") == STATE_ARTIFACT_NAME and artifact.get("expired") is not True:
            return True
    return False


def restore_state(
    *,
    workdir: Path,
    repo: str,
    workflow: str,
    branch: str,
    current_run_id: str | None,
    limit: int,
    restore_dir: Path,
) -> str:
    target = workdir / STATE_DB_RELATIVE_PATH
    partial = target.with_suffix(target.suffix + ".partial")
    shutil.rmtree(restore_dir, ignore_errors=True)
    restore_dir.mkdir(parents=True, exist_ok=True)
    target.parent.mkdir(parents=True, exist_ok=True)

    partial.unlink(missing_ok=True)
    target.unlink(missing_ok=True)

    try:
        candidates = _candidate_run_ids(
            repo=repo,
            workflow=workflow,
            branch=branch,
            current_run_id=current_run_id,
            limit=limit,
        )
        selected_run_id = next((run_id for run_id in candidates if _run_has_state_artifact(repo=repo, run_id=run_id)), None)
        if selected_run_id is None:
            print("INFO: no previous shadow-live-state artifact found; starting cold", file=sys.stderr)
            return "cold_start"

        download = _run_command(
            [
                "gh",
                "run",
                "download",
                selected_run_id,
                "--repo",
                repo,
                "--name",
                STATE_ARTIFACT_NAME,
                "--dir",
                restore_dir.as_posix(),
            ]
        )
        if download.returncode != 0:
            print(download.stderr.strip() or download.stdout.strip(), file=sys.stderr)
            target.unlink(missing_ok=True)
            return "restore_failed"

        restored_file = restore_dir / STATE_DB_NAME
        if not _sqlite_state_is_valid(restored_file):
            print(f"WARN: restored artifact is not a valid state DB: {restored_file}", file=sys.stderr)
            target.unlink(missing_ok=True)
            return "restore_failed"

        shutil.copy2(restored_file, partial)
        partial.replace(target)
        print(f"INFO: restored shadow-live SQLite state from run {selected_run_id}", file=sys.stderr)
        return "restored"
    except Exception as exc:
        print(f"WARN: shadow-live state restore failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        return "restore_failed"
    finally:
        shutil.rmtree(restore_dir, ignore_errors=True)


def checkpoint_and_stage_state(*, workdir: Path, upload_dir: Path) -> Path:
    db_path = workdir / STATE_DB_RELATIVE_PATH
    if not db_path.is_file() or db_path.stat().st_size <= 0:
        raise FileNotFoundError(f"missing non-empty SQLite state database: {db_path}")
    connection = sqlite3.connect(db_path)
    try:
        connection.execute("PRAGMA wal_checkpoint(TRUNCATE);").fetchall()
    finally:
        connection.close()
    if not _sqlite_state_is_valid(db_path):
        raise RuntimeError(f"SQLite state database failed post-checkpoint validation: {db_path}")
    shutil.rmtree(upload_dir, ignore_errors=True)
    upload_dir.mkdir(parents=True, exist_ok=True)
    staged = upload_dir / STATE_DB_NAME
    shutil.copy2(db_path, staged)
    return staged


def _write_github_output(path: str | None, *, name: str, value: str) -> None:
    if not path:
        return
    with Path(path).open("a", encoding="utf-8") as fh:
        fh.write(f"{name}={value}\n")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore or stage Shadow-Live SQLite state")
    subparsers = parser.add_subparsers(dest="command", required=True)

    restore = subparsers.add_parser("restore", help="Restore prior shadow-live SQLite state from GitHub Actions artifacts")
    restore.add_argument("--workdir", required=True)
    restore.add_argument("--repo", required=True)
    restore.add_argument("--workflow", default="independence-shadow-live.yml")
    restore.add_argument("--branch", default="main")
    restore.add_argument("--current-run-id", default=None)
    restore.add_argument("--limit", type=int, default=20)
    restore.add_argument("--restore-dir", default=".state-restore")
    restore.add_argument("--github-output", default=None)

    checkpoint = subparsers.add_parser("checkpoint-stage", help="Checkpoint and stage shadow-live SQLite state for upload")
    checkpoint.add_argument("--workdir", required=True)
    checkpoint.add_argument("--upload-dir", default=".state-upload")

    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    if args.command == "restore":
        status = restore_state(
            workdir=Path(args.workdir).resolve(),
            repo=args.repo,
            workflow=args.workflow,
            branch=args.branch,
            current_run_id=args.current_run_id,
            limit=args.limit,
            restore_dir=Path(args.restore_dir).resolve(),
        )
        _write_github_output(args.github_output, name="state_restore_status", value=status)
        print(status)
        return 0

    staged = checkpoint_and_stage_state(
        workdir=Path(args.workdir).resolve(),
        upload_dir=Path(args.upload_dir).resolve(),
    )
    print(staged.as_posix())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
