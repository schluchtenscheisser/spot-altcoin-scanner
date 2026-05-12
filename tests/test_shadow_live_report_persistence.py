from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path("scripts/persist_shadow_live_reports.py").resolve()


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
    }


def _populate_source(source: Path) -> None:
    daily = _latest_daily()
    intraday = {**daily, "run_id": "intraday-2026-05-12T04", "scan_mode": "intraday", "intraday_bar_id": "2026-05-12T04:00:00Z"}
    (source / "reports" / "index").mkdir(parents=True, exist_ok=True)
    (source / "reports" / "index" / "latest_run.txt").write_text("intraday-2026-05-12T04\n", encoding="utf-8")
    _write_json(source / "reports" / "index" / "latest_daily.json", daily)
    _write_json(source / "reports" / "index" / "latest.json", intraday)
    _write_json(source / "reports" / "index" / "latest_confirmed_candidates.json", ["AAAUSDT"])
    _write_json(source / "reports" / "index" / "latest_watchlist.json", ["BBBUSDT"])
    _write_json(source / "reports" / "index" / "latest_paths.json", {"report_path": "reports/runs/2026/05/12/intraday-2026-05-12T04/report.json"})
    _write_json(source / "reports" / "index" / "recent_runs.json", [intraday, daily])
    _write_json(source / "reports" / "index" / "latest_intraday.json", intraday)
    _write_json(source / "reports" / "daily" / "2026" / "05" / "12" / "report.json", daily)
    _write_json(source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.json", daily)
    _write_json(source / "reports" / "runs" / "2026" / "05" / "12" / "intraday-2026-05-12T04" / "report.json", intraday)
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "symbol_diagnostics.jsonl.gz").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "report.xlsx").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "debug.parquet").write_bytes(b"not allowed")
    (source / "reports" / "runs" / "2026" / "05" / "12" / "daily-2026-05-12" / "archive.zip").write_bytes(b"not allowed")


def test_persistence_commits_only_allowlisted_report_files(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    source = tmp_path / "source"
    repo.mkdir()
    _init_repo(repo)
    _populate_source(source)

    github_output = tmp_path / "github-output.txt"
    env = {**os.environ, "GITHUB_OUTPUT": str(github_output)}
    result = _run([sys.executable, str(SCRIPT), "--repo-root", str(repo), "--source-root", str(source)], cwd=repo, env=env)

    assert "Persisted shadow-live reports for daily-2026-05-12." in result.stdout
    assert "created_commit=true" in github_output.read_text(encoding="utf-8")
    show = _run(["git", "show", "--name-only", "--format="], cwd=repo).stdout.splitlines()
    changed = {line for line in show if line}
    assert changed == {
        "reports/index/latest_run.txt",
        "reports/index/latest.json",
        "reports/index/latest_daily.json",
        "reports/index/latest_confirmed_candidates.json",
        "reports/index/latest_watchlist.json",
        "reports/index/latest_paths.json",
        "reports/index/recent_runs.json",
        "reports/daily/2026/05/12/report.json",
        "reports/runs/2026/05/12/daily-2026-05-12/report.json",
        "reports/runs/2026/05/12/intraday-2026-05-12T04/report.json",
    }
    tree = _run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo).stdout
    assert "reports/index/latest_intraday.json" not in tree
    assert "symbol_diagnostics.jsonl.gz" not in tree
    assert ".xlsx" not in tree
    assert ".parquet" not in tree
    assert ".zip" not in tree
    assert _run(["git", "log", "-1", "--pretty=%s"], cwd=repo).stdout.strip() == "Persist shadow-live reports for daily-2026-05-12"


def test_persistence_skips_when_daily_anchor_already_exists(tmp_path: Path) -> None:
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
    env = {**os.environ, "GITHUB_OUTPUT": str(github_output)}
    result = _run([sys.executable, str(SCRIPT), "--repo-root", str(repo), "--source-root", str(source)], cwd=repo, env=env)

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
    env = {**os.environ, "GITHUB_OUTPUT": str(github_output)}
    result = _run([sys.executable, str(SCRIPT), "--repo-root", str(repo), "--source-root", str(source)], cwd=repo, env=env)

    assert "No report persistence changes to commit." in result.stdout
    assert "created_commit=false" in github_output.read_text(encoding="utf-8")
    after = _run(["git", "rev-parse", "HEAD"], cwd=repo).stdout.strip()
    assert after == before


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
