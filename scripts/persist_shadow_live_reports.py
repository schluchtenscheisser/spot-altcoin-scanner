#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

INDEX_ALLOWLIST = (
    "latest_run.txt",
    "latest.json",
    "latest_daily.json",
    "latest_confirmed_candidates.json",
    "latest_watchlist.json",
    "latest_paths.json",
    "recent_runs.json",
)

BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
SKIP_MESSAGE = "report persistence skipped because daily run report already exists."
NO_CHANGES_MESSAGE = "No report persistence changes to commit."


def _emit_created_commit(created_commit: bool) -> None:
    github_output = os.environ.get("GITHUB_OUTPUT")
    if not github_output:
        return
    with open(github_output, "a", encoding="utf-8") as handle:
        handle.write(f"created_commit={'true' if created_commit else 'false'}\n")


def _run_git(repo_root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _date_parts(daily_bar_id: str) -> tuple[str, str, str]:
    parts = daily_bar_id.split("-")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"invalid daily_bar_id in latest_daily.json: {daily_bar_id!r}")
    return parts[0], parts[1], parts[2]


def _source_reports_root(source_root: Path) -> Path:
    if (source_root / "reports").is_dir():
        return source_root / "reports"
    return source_root


def _daily_anchor_from_source(source_root: Path) -> tuple[str, Path]:
    reports_root = _source_reports_root(source_root)
    latest_daily_path = reports_root / "index" / "latest_daily.json"
    if not latest_daily_path.exists():
        raise FileNotFoundError(
            "reports/index/latest_daily.json missing from report persistence artifact"
        )
    payload = _read_json(latest_daily_path)
    if not isinstance(payload, dict):
        raise ValueError("reports/index/latest_daily.json must contain a JSON object")
    run_id = str(payload.get("run_id") or "")
    daily_bar_id = str(payload.get("daily_bar_id") or "")
    if not run_id:
        raise ValueError("reports/index/latest_daily.json is missing run_id")
    year, month, day = _date_parts(daily_bar_id)
    return run_id, Path("reports") / "runs" / year / month / day / run_id / "report.json"


def _copy_if_exists(source_root: Path, repo_root: Path, rel_path: Path) -> bool:
    src = source_root / rel_path
    if not src.exists() and rel_path.parts and rel_path.parts[0] == "reports":
        src = _source_reports_root(source_root).joinpath(*rel_path.parts[1:])
    if not src.exists() or not src.is_file():
        return False
    dst = repo_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def _allowed_paths(source_root: Path) -> list[Path]:
    reports_root = _source_reports_root(source_root)
    paths: list[Path] = []
    for name in INDEX_ALLOWLIST:
        rel = Path("reports") / "index" / name
        if (reports_root / "index" / name).is_file():
            paths.append(rel)

    daily_root = reports_root / "daily"
    if daily_root.exists():
        paths.extend(
            Path("reports") / "daily" / path.relative_to(daily_root)
            for path in sorted(daily_root.glob("*/*/*/report.json"))
            if path.is_file()
        )

    runs_root = reports_root / "runs"
    if runs_root.exists():
        paths.extend(
            Path("reports") / "runs" / path.relative_to(runs_root)
            for path in sorted(runs_root.glob("*/*/*/*/report.json"))
            if path.is_file()
        )
    return paths


def persist_reports(repo_root: Path, source_root: Path, push: bool = False) -> int:
    repo_root = repo_root.resolve()
    source_root = source_root.resolve()
    daily_run_id, daily_anchor = _daily_anchor_from_source(source_root)

    if (repo_root / daily_anchor).exists():
        _emit_created_commit(False)
        print(SKIP_MESSAGE)
        return 0

    copied: list[Path] = []
    for rel_path in _allowed_paths(source_root):
        if _copy_if_exists(source_root, repo_root, rel_path):
            copied.append(rel_path)

    if not copied:
        _emit_created_commit(False)
        print(NO_CHANGES_MESSAGE)
        return 0

    _run_git(repo_root, ["config", "user.name", BOT_NAME])
    _run_git(repo_root, ["config", "user.email", BOT_EMAIL])
    _run_git(repo_root, ["add", "--", *(path.as_posix() for path in copied)])

    diff = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", *(path.as_posix() for path in copied)],
        cwd=repo_root,
        check=False,
    )
    if diff.returncode == 0:
        _emit_created_commit(False)
        print(NO_CHANGES_MESSAGE)
        return 0
    if diff.returncode != 1:
        raise RuntimeError(f"git diff --cached --quiet failed with exit code {diff.returncode}")

    _run_git(repo_root, ["commit", "-m", f"Persist shadow-live reports for {daily_run_id}"])
    _emit_created_commit(True)
    if push:
        _run_git(repo_root, ["push"])
    print(f"Persisted shadow-live reports for {daily_run_id}.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Persist allowed Shadow-Live reports into git.")
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    return persist_reports(repo_root=args.repo_root, source_root=args.source_root, push=args.push)


if __name__ == "__main__":
    raise SystemExit(main())
