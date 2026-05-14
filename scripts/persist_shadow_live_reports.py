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
    "latest_intraday.json",
    "latest_confirmed_candidates.json",
    "latest_watchlist.json",
    "latest_paths.json",
    "recent_runs.json",
)

JSON_TYPE_ALLOWLIST: dict[str, tuple[type, ...]] = {
    "reports/index/latest.json": (dict,),
    "reports/index/latest_daily.json": (dict,),
    "reports/index/latest_intraday.json": (dict,),
    "reports/index/latest_paths.json": (dict,),
    "reports/index/latest_confirmed_candidates.json": (list,),
    "reports/index/latest_watchlist.json": (list,),
    "reports/index/recent_runs.json": (list,),
}

BOT_NAME = "github-actions[bot]"
BOT_EMAIL = "41898282+github-actions[bot]@users.noreply.github.com"
SKIP_MESSAGE = "report persistence skipped because complete allowlist is already valid and current."
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


def _date_parts(daily_bar_id: str) -> tuple[str, str, str]:
    parts = daily_bar_id.split("-")
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"invalid daily_bar_id in latest_daily.json: {daily_bar_id!r}")
    return parts[0], parts[1], parts[2]


def _source_reports_root(source_root: Path) -> Path:
    if (source_root / "reports").is_dir():
        return source_root / "reports"
    return source_root


def _source_snapshots_root(source_root: Path) -> Path:
    if (source_root / "snapshots").is_dir():
        return source_root / "snapshots"
    return source_root / "snapshots" if (source_root / "snapshots" / "runs").is_dir() else source_root


def _source_for_rel_path(source_root: Path, rel_path: Path) -> Path:
    if rel_path.parts and rel_path.parts[0] == "reports":
        return _source_reports_root(source_root).joinpath(*rel_path.parts[1:])
    if rel_path.parts and rel_path.parts[0] == "snapshots":
        return _source_snapshots_root(source_root).joinpath(*rel_path.parts[1:])
    return source_root / rel_path


def _validate_text_file(path: Path, *, label: str) -> str:
    if not path.exists():
        raise FileNotFoundError(f"{label} missing: {path}")
    if not path.is_file():
        raise ValueError(f"{label} is not a regular file: {path}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"{label} must be non-empty: {path}")
    return content


def _validate_json_file(path: Path, *, expected_types: tuple[type, ...], label: str) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"{label} missing: {path}")
    if not path.is_file():
        raise ValueError(f"{label} is not a regular file: {path}")
    if path.stat().st_size <= 0:
        raise ValueError(f"{label} must be non-empty JSON: {path}")
    content = path.read_text(encoding="utf-8")
    if not content.strip():
        raise ValueError(f"{label} must be non-empty JSON: {path}")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} contains invalid JSON at {path}: {exc.msg}") from exc
    if expected_types != (object,) and not isinstance(payload, expected_types):
        expected = " or ".join(t.__name__ for t in expected_types)
        raise ValueError(f"{label} must contain JSON {expected}: {path}")
    return payload


def _expected_json_types(rel_path: Path) -> tuple[type, ...]:
    rel = rel_path.as_posix()
    if rel in JSON_TYPE_ALLOWLIST:
        return JSON_TYPE_ALLOWLIST[rel]
    if rel.endswith("/report.json"):
        return (dict,)
    if rel.endswith("/run.manifest.json"):
        return (dict,)
    raise ValueError(f"no JSON validation contract for allowed path: {rel}")


def _validate_allowed_path(path: Path, *, rel_path: Path, label_prefix: str) -> Any:
    label = f"{label_prefix} {rel_path.as_posix()}"
    if rel_path.name == "latest_run.txt":
        return _validate_text_file(path, label=label)
    payload = _validate_json_file(path, expected_types=_expected_json_types(rel_path), label=label)
    if rel_path.name == "run.manifest.json" and not str(payload.get("run_id") or "").strip():
        raise ValueError(f"{label} is missing required run_id: {path}")
    return payload


def _daily_anchor_from_source(source_root: Path) -> tuple[str, Path]:
    reports_root = _source_reports_root(source_root)
    latest_daily_path = reports_root / "index" / "latest_daily.json"
    if not latest_daily_path.exists():
        raise FileNotFoundError(
            "reports/index/latest_daily.json missing from report persistence artifact"
        )
    payload = _validate_json_file(
        latest_daily_path,
        expected_types=(dict,),
        label="source reports/index/latest_daily.json",
    )
    run_id = str(payload.get("run_id") or "")
    daily_bar_id = str(payload.get("daily_bar_id") or "")
    if not run_id:
        raise ValueError("reports/index/latest_daily.json is missing run_id")
    year, month, day = _date_parts(daily_bar_id)
    return run_id, Path("reports") / "runs" / year / month / day / run_id / "report.json"


def _copy_validated(source_root: Path, repo_root: Path, rel_path: Path) -> None:
    src = _source_for_rel_path(source_root, rel_path)
    _validate_allowed_path(src, rel_path=rel_path, label_prefix="source")
    dst = repo_root / rel_path
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    _validate_allowed_path(dst, rel_path=rel_path, label_prefix="destination")


def _allowed_report_paths(source_root: Path) -> list[Path]:
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
    return sorted(paths, key=lambda path: path.as_posix())


def _allowed_manifest_paths(source_root: Path) -> list[Path]:
    snapshots_root = _source_snapshots_root(source_root)
    runs_root = snapshots_root / "runs"
    if not runs_root.exists():
        return []
    return sorted(
        (
            Path("snapshots") / "runs" / path.relative_to(runs_root)
            for path in runs_root.glob("*/*/*/*/run.manifest.json")
            if path.is_file()
        ),
        key=lambda path: path.as_posix(),
    )


def _validate_source_paths(source_root: Path, rel_paths: list[Path]) -> None:
    for rel_path in rel_paths:
        _validate_allowed_path(
            _source_for_rel_path(source_root, rel_path),
            rel_path=rel_path,
            label_prefix="source",
        )


def _matching_manifest_path(run_report_path: Path) -> Path:
    parts = run_report_path.parts
    # reports/runs/YYYY/MM/DD/<run_id>/report.json
    return Path("snapshots") / "runs" / parts[2] / parts[3] / parts[4] / parts[5] / "run.manifest.json"


def _validate_manifest_coverage(source_root: Path, report_paths: list[Path], manifest_paths: list[Path]) -> None:
    manifest_set = {path.as_posix() for path in manifest_paths}
    for report_path in report_paths:
        if not report_path.as_posix().startswith("reports/runs/"):
            continue
        expected = _matching_manifest_path(report_path)
        if expected.as_posix() not in manifest_set:
            raise FileNotFoundError(
                f"missing replay manifest for persisted run report {report_path.as_posix()}: "
                f"expected source artifact path {expected.as_posix()}"
            )

        report_payload = _validate_json_file(
            _source_for_rel_path(source_root, report_path),
            expected_types=(dict,),
            label=f"source {report_path.as_posix()}",
        )
        manifest_path = report_payload.get("manifest_path")
        if isinstance(manifest_path, str) and manifest_path.strip():
            manifest_rel = Path(manifest_path.strip())
            if manifest_rel.is_absolute() or any(part == ".." for part in manifest_rel.parts):
                raise ValueError(f"invalid manifest_path in {report_path.as_posix()}: {manifest_path!r}")
            if manifest_rel.as_posix() not in manifest_set:
                raise FileNotFoundError(
                    f"manifest_path referenced by {report_path.as_posix()} is absent from source artifact: "
                    f"{manifest_rel.as_posix()}"
                )


def _target_needs_copy(source_root: Path, repo_root: Path, rel_path: Path) -> bool:
    src = _source_for_rel_path(source_root, rel_path)
    dst = repo_root / rel_path
    if not dst.exists():
        return True
    try:
        _validate_allowed_path(dst, rel_path=rel_path, label_prefix="destination")
    except (OSError, UnicodeDecodeError, ValueError):
        return True
    return src.read_bytes() != dst.read_bytes()


def persist_reports(repo_root: Path, source_root: Path, push: bool = False) -> int:
    repo_root = repo_root.resolve()
    source_root = source_root.resolve()
    daily_run_id, _daily_anchor = _daily_anchor_from_source(source_root)

    report_paths = _allowed_report_paths(source_root)
    manifest_paths = _allowed_manifest_paths(source_root)
    allowed_paths = sorted([*report_paths, *manifest_paths], key=lambda path: path.as_posix())

    # Idempotency is intentionally evaluated over the complete persisted
    # allowlist. A valid daily report alone is not enough: same-day retries must
    # be able to repair missing, corrupt, or stale index/report/manifest siblings.
    _validate_source_paths(source_root, allowed_paths)
    _validate_manifest_coverage(source_root, report_paths, manifest_paths)

    copied = [
        rel_path
        for rel_path in allowed_paths
        if _target_needs_copy(source_root, repo_root, rel_path)
    ]
    for rel_path in copied:
        _copy_validated(source_root, repo_root, rel_path)

    if not copied:
        _emit_created_commit(False)
        print(SKIP_MESSAGE)
        return 0

    _run_git(repo_root, ["config", "user.name", BOT_NAME])
    _run_git(repo_root, ["config", "user.email", BOT_EMAIL])
    _run_git(repo_root, ["add", "-f", "--", *(path.as_posix() for path in copied)])

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
    parser = argparse.ArgumentParser(description="Persist allowed Shadow-Live reports and replay manifests into git.")
    parser.add_argument("--repo-root", default=".", type=Path)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--push", action="store_true")
    args = parser.parse_args()
    return persist_reports(repo_root=args.repo_root, source_root=args.source_root, push=args.push)


if __name__ == "__main__":
    raise SystemExit(main())
