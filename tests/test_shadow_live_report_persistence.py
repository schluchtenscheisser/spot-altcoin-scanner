from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/persist_shadow_live_reports.py").resolve()
WORKFLOW = Path(".github/workflows/independence-shadow-live.yml")


def _run(
    args: list[str],
    cwd: Path,
    check: bool = True,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        env=env,
    )


def _init_repo(path: Path) -> None:
    _run(["git", "init"], cwd=path)
    _run(["git", "config", "user.name", "Test User"], cwd=path)
    _run(["git", "config", "user.email", "test@example.invalid"], cwd=path)
    (path / "README.md").write_text("test repo\n", encoding="utf-8")
    _run(["git", "add", "README.md"], cwd=path)
    _run(["git", "commit", "-m", "initial"], cwd=path)


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def _latest_daily(run_id: str = "daily-2026-05-12") -> dict[str, object]:
    return {
        "run_id": run_id,
        "scan_mode": "daily",
        "as_of_utc": "2026-05-12T01:30:00Z",
        "daily_bar_id": "2026-05-12",
        "intraday_bar_id": None,
        "counts_by_bucket": {},
        "symbol_lists": {"confirmed_candidates": ["AAAUSDT"], "watchlist": ["BBBUSDT"]},
        "manifest_path": f"snapshots/runs/2026/05/12/{run_id}/run.manifest.json",
    }


def _manifest(run_id: str) -> dict[str, object]:
    return {"run_id": run_id, "schema_version": "1.0", "artifact_paths": []}


def _populate_source(source: Path, *, include_manifests: bool = True) -> None:
    daily = _latest_daily()
    intraday_run_id = "intraday-2026-05-12T04"
    intraday = {
        **daily,
        "run_id": intraday_run_id,
        "scan_mode": "intraday",
        "intraday_bar_id": "2026-05-12T04:00:00Z",
        "manifest_path": f"snapshots/runs/2026/05/12/{intraday_run_id}/run.manifest.json",
    }
    (source / "reports" / "index").mkdir(parents=True, exist_ok=True)
    (source / "reports" / "index" / "latest_run.txt").write_text("intraday-2026-05-12T04\n", encoding="utf-8")
    _write_json(source / "reports" / "index" / "latest_daily.json", daily)
    _write_json(source / "reports" / "index" / "latest.json", intraday)
    _write_json(source / "reports" / "index" / "latest_intraday.json", intraday)
    _write_json(source / "reports" / "index" / "latest_confirmed_candidates.json", ["AAAUSDT"])
    _write_json(source / "reports" / "index" / "latest_watchlist.json", ["BBBUSDT"])
    _write_json(source / "reports" / "index" / "latest_paths.json", {"report_path": f"reports/runs/2026/05/12/{intraday_run_id}/report.json"})
    _write_json(source / "reports" / "index" / "recent_runs.json", [intraday, daily])
    _write_json(source / "reports" / "daily" / "2026" / "05" / "12" / "report.json", daily)
    _write_json(source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.json", daily)
    _write_json(source / "reports" / "runs" / "2026" / "05" / "12" / intraday_run_id / "report.json", intraday)
    if include_manifests:
        _write_json(source / "snapshots" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "run.manifest.json", _manifest("daily-2026-05-12"))
        _write_json(source / "snapshots" / "runs" / "2026" / "05" / "12" / intraday_run_id / "run.manifest.json", _manifest(intraday_run_id))
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "symbol_diagnostics.jsonl.gz").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.xlsx").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "debug.parquet").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "archive.zip").write_bytes(b"not allowed")
    snapshot_payload_dir = source / "snapshots" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12"
    snapshot_payload_dir.mkdir(parents=True, exist_ok=True)
    (snapshot_payload_dir / "run.snapshot.json").write_text("{}\n", encoding="utf-8")
    (snapshot_payload_dir / "symbols.jsonl.gz").write_bytes(b"not allowed")
    (snapshot_payload_dir / "anything.parquet").write_bytes(b"not allowed")


def _run_persist(repo: Path, source: Path, output_path: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {**os.environ}
    if output_path is not None:
        env["GITHUB_OUTPUT"] = str(output_path)
    return _run([sys.executable, str(SCRIPT), "--repo-root", str(repo), "--source-root", str(source)], cwd=repo, env=env, check=check)


def test_persistence_commits_only_allowlisted_report_and_manifest_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)

    github_output = tmp_path / "github-output.txt"
    result = _run_persist(repo, source, github_output)

    assert "Persisted shadow-live reports for daily-2026-05-12." in result.stdout
    assert "created_commit=true" in github_output.read_text(encoding="utf-8")
    show = _run(["git", "show", "--name-only", "--format="], cwd=repo).stdout.splitlines()
    changed = {line for line in show if line}
    assert changed == {
        "reports/index/latest_run.txt",
        "reports/index/latest.json",
        "reports/index/latest_daily.json",
        "reports/index/latest_intraday.json",
        "reports/index/latest_confirmed_candidates.json",
        "reports/index/latest_watchlist.json",
        "reports/index/latest_paths.json",
        "reports/index/recent_runs.json",
        "reports/daily/2026/05/12/report.json",
        "reports/runs/2026/05/12/daily-2026-05-12/report.json",
        "reports/runs/2026/05/12/intraday-2026-05-12T04/report.json",
        "snapshots/runs/2026/05/12/daily-2026-05-12/run.manifest.json",
        "snapshots/runs/2026/05/12/intraday-2026-05-12T04/run.manifest.json",
    }
    tree = _run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo).stdout
    assert "symbol_diagnostics.jsonl.gz" not in tree
    assert "run.snapshot.json" not in tree
    assert ".xlsx" not in tree
    assert ".parquet" not in tree
    assert ".zip" not in tree
    assert _run(["git", "log", "-1", "--pretty=%s"], cwd=repo).stdout.strip() == "Persist shadow-live reports for daily-2026-05-12"


def test_persistence_rejects_empty_json_source(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)
    (source / "reports" / "index" / "latest_daily.json").write_text("   \n", encoding="utf-8")

    result = _run_persist(repo, source, check=False)

    assert result.returncode != 0
    assert "latest_daily.json" in result.stdout
    assert "non-empty JSON" in result.stdout
    assert _run(["git", "log", "--oneline"], cwd=repo).stdout.count("\n") == 1


def test_persistence_rejects_invalid_json_source(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)
    (source / "reports" / "index" / "latest_paths.json").write_text("{invalid\n", encoding="utf-8")

    result = _run_persist(repo, source, check=False)

    assert result.returncode != 0
    assert "latest_paths.json" in result.stdout
    assert "invalid JSON" in result.stdout
    assert _run(["git", "status", "--short"], cwd=repo).stdout == ""


def test_existing_empty_repo_anchor_is_replaced_instead_of_skipped(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)
    anchor = repo / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.json"
    anchor.parent.mkdir(parents=True, exist_ok=True)
    anchor.write_text("", encoding="utf-8")
    _run(["git", "add", anchor.relative_to(repo).as_posix()], cwd=repo)
    _run(["git", "commit", "-m", "persist empty anchor"], cwd=repo)

    result = _run_persist(repo, source, tmp_path / "github-output-repair.txt")

    assert "report persistence skipped" not in result.stdout
    assert json.loads(anchor.read_text(encoding="utf-8"))["run_id"] == "daily-2026-05-12"
    assert _run(["git", "log", "-1", "--pretty=%s"], cwd=repo).stdout.strip() == "Persist shadow-live reports for daily-2026-05-12"


def test_persistence_skips_when_daily_anchor_already_exists_and_is_valid(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)
    _write_json(repo / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.json", {"already": True})
    _run(["git", "add", "reports/runs/2026/05/12/daily-2026-05-12/report.json"], cwd=repo)
    _run(["git", "commit", "-m", "persisted already"], cwd=repo)
    before = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    github_output = tmp_path / "github-output-skip.txt"
    result = _run_persist(repo, source, github_output)

    assert "report persistence skipped because daily run report already exists." in result.stdout
    assert "created_commit=false" in github_output.read_text(encoding="utf-8")
    after = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    assert after == before
    assert _run(["git", "status", "--short"], cwd=repo).stdout == ""


def test_persistence_exits_without_commit_when_allowed_files_have_no_diff(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    latest_daily = _latest_daily()
    _write_json(source / "reports" / "index" / "latest_daily.json", latest_daily)
    _write_json(repo / "reports" / "index" / "latest_daily.json", latest_daily)
    _run(["git", "add", "reports/index/latest_daily.json"], cwd=repo)
    _run(["git", "commit", "-m", "existing index"], cwd=repo)
    before = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()

    github_output = tmp_path / "github-output-no-diff.txt"
    result = _run_persist(repo, source, github_output)

    assert "No report persistence changes to commit." in result.stdout
    assert "created_commit=false" in github_output.read_text(encoding="utf-8")
    after = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    assert after == before


def test_persistence_fails_when_run_report_manifest_is_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source, include_manifests=False)

    result = _run_persist(repo, source, check=False)

    assert result.returncode != 0
    assert "missing replay manifest" in result.stdout
    assert "snapshots/runs/2026/05/12/daily-2026-05-12/run.manifest.json" in result.stdout
    assert _run(["git", "status", "--short"], cwd=repo).stdout == ""


def test_gitignore_blocks_large_report_and_snapshot_artifacts() -> None:
    text = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in [
        "reports/**/*.jsonl.gz",
        "reports/**/*.xlsx",
        "reports/**/*.parquet",
        "reports/**/*.zip",
        "reports/**/symbol_diagnostics.jsonl.gz",
        "snapshots/**/*.parquet",
        "snapshots/**/*.jsonl.gz",
    ]:
        assert pattern in text
    lines = set(text.splitlines())
    assert "reports/**/*.json" not in lines
    assert "reports/**/*.md" not in lines


def test_workflow_report_persistence_artifact_transfers_replay_manifests() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "${{ runner.temp }}/ir-shadow-live-workdir/snapshots/runs/**/run.manifest.json" in text
    assert "if: steps.persist_reports.outputs.created_commit == 'true'" in text
