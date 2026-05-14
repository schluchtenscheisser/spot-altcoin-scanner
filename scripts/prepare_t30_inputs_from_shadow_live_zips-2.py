#!/usr/bin/env python3
"""Prepare local T30 inputs from downloaded Shadow-Live ZIP artifacts.

Expected workflow:
1. Put all downloaded Shadow-Live ZIP artifacts into data/shadow-live-zips/.
2. Run this script from the repository root:

   python scripts/prepare_t30_inputs_from_shadow_live_zips.py --project-root .

3. Then run:

   python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .
   python scripts/run_t30_evaluation.py --project-root .

This script intentionally extracts only files needed for T30 replay/evaluation:
- snapshots/runs/**/run.manifest.json
- reports/runs/**/symbol_diagnostics.jsonl.gz
- reports/runs/**/report.json
- reports/index/**
- reports/daily/**/report.json

It ignores SQLite state, Parquet history, and unrelated payloads.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable

DEFAULT_ZIP_DIR = Path("data/shadow-live-zips")

ALLOWED_EXACT_SUFFIXES = (
    "run.manifest.json",
    "symbol_diagnostics.jsonl.gz",
    "report.json",
)

ALLOWED_PREFIXES = (
    "reports/index/",
    "reports/daily/",
)

REQUIRED_PATTERNS = {
    "manifests": "snapshots/runs/**/run.manifest.json",
    "diagnostics": "reports/runs/**/symbol_diagnostics.jsonl.gz",
    "run_reports": "reports/runs/**/report.json",
}


@dataclass
class ExtractStats:
    zip_count: int = 0
    extracted: int = 0
    skipped_existing: int = 0
    ignored: int = 0
    invalid_members: int = 0


def _iter_zip_files(zip_dir: Path) -> list[Path]:
    return sorted(p for p in zip_dir.glob("*.zip") if p.is_file())


def _safe_member_path(member_name: str) -> PurePosixPath | None:
    """Return normalized POSIX path or None for unsafe members."""
    if not member_name or member_name.endswith("/"):
        return None
    p = PurePosixPath(member_name)
    if p.is_absolute() or ".." in p.parts:
        return None
    return p


def _is_allowed_member(member: PurePosixPath) -> bool:
    s = member.as_posix()

    if s.startswith(ALLOWED_PREFIXES):
        return True

    # Required T30 replay payloads.
    if s.startswith("snapshots/runs/") and s.endswith("/run.manifest.json"):
        return True
    if s.startswith("reports/runs/") and s.endswith("/symbol_diagnostics.jsonl.gz"):
        return True
    if s.startswith("reports/runs/") and s.endswith("/report.json"):
        return True

    return False


def _extract_member(zf: zipfile.ZipFile, member: zipfile.ZipInfo, target: Path, *, overwrite: bool) -> str:
    dest = target / member.filename
    dest = target / PurePosixPath(member.filename).as_posix()

    # Re-normalize with pathlib to avoid odd separators on Windows.
    dest = target.joinpath(*PurePosixPath(member.filename).parts)

    if dest.exists() and not overwrite:
        return "skipped_existing"

    dest.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(member, "r") as src, dest.open("wb") as out:
        out.write(src.read())
    return "extracted"


def extract_shadow_live_zips(project_root: Path, zip_dir: Path, *, overwrite: bool) -> ExtractStats:
    stats = ExtractStats()
    zip_files = _iter_zip_files(zip_dir)
    stats.zip_count = len(zip_files)

    for zip_path in zip_files:
        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for info in zf.infolist():
                    safe = _safe_member_path(info.filename)
                    if safe is None:
                        stats.invalid_members += 1
                        continue
                    if not _is_allowed_member(safe):
                        stats.ignored += 1
                        continue

                    # Preserve normalized path in extraction destination.
                    info.filename = safe.as_posix()
                    result = _extract_member(zf, info, project_root, overwrite=overwrite)
                    if result == "extracted":
                        stats.extracted += 1
                    elif result == "skipped_existing":
                        stats.skipped_existing += 1
        except zipfile.BadZipFile as exc:
            raise RuntimeError(f"Invalid ZIP file: {zip_path}") from exc

    return stats


def _count(project_root: Path, pattern: str) -> int:
    return sum(1 for p in project_root.glob(pattern) if p.is_file())


def _validate_non_empty_json_files(project_root: Path) -> list[str]:
    """Return validation errors for extracted report/manifest JSON files."""
    errors: list[str] = []
    candidates: Iterable[Path] = list(project_root.glob("reports/**/*.json")) + list(
        project_root.glob("snapshots/runs/**/run.manifest.json")
    )
    for path in sorted(set(candidates)):
        try:
            if path.stat().st_size == 0:
                errors.append(f"empty JSON file: {path.relative_to(project_root).as_posix()}")
                continue
            with path.open("r", encoding="utf-8") as fh:
                json.load(fh)
        except json.JSONDecodeError as exc:
            errors.append(f"invalid JSON file: {path.relative_to(project_root).as_posix()} ({exc})")
    return errors


def preflight(project_root: Path) -> dict[str, int | list[str]]:
    counts = {name: _count(project_root, pattern) for name, pattern in REQUIRED_PATTERNS.items()}
    counts["latest_index_files"] = _count(project_root, "reports/index/*")
    errors = _validate_non_empty_json_files(project_root)
    return {**counts, "json_errors": errors}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract T30 replay inputs from downloaded Shadow-Live ZIP artifacts."
    )
    parser.add_argument("--project-root", type=Path, default=Path("."), help="Repository root. Default: current directory.")
    parser.add_argument(
        "--zip-dir",
        type=Path,
        default=DEFAULT_ZIP_DIR,
        help="Directory containing downloaded Shadow-Live ZIP artifacts. Default: data/shadow-live-zips",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite already extracted files. Default: keep existing files.",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero if required T30 inputs or JSON validity checks fail.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()
    zip_dir = args.zip_dir
    if not zip_dir.is_absolute():
        zip_dir = project_root / zip_dir
    zip_dir = zip_dir.resolve()

    if not project_root.exists():
        print(f"FAIL: project root does not exist: {project_root}", file=sys.stderr)
        return 2
    if not zip_dir.exists():
        print(f"FAIL: ZIP directory does not exist: {zip_dir}", file=sys.stderr)
        return 2

    zip_files = _iter_zip_files(zip_dir)
    if not zip_files:
        print(f"FAIL: no .zip files found in {zip_dir}", file=sys.stderr)
        return 2

    stats = extract_shadow_live_zips(project_root, zip_dir, overwrite=args.overwrite)
    checks = preflight(project_root)

    print("T30 input preparation complete")
    print(f"zip_dir={zip_dir}")
    print(f"zip_count={stats.zip_count}")
    print(f"extracted_files={stats.extracted}")
    print(f"skipped_existing_files={stats.skipped_existing}")
    print(f"ignored_zip_members={stats.ignored}")
    print(f"invalid_zip_members={stats.invalid_members}")
    print("Preflight counts:")
    for key in ("manifests", "diagnostics", "run_reports", "latest_index_files"):
        print(f"  {key}={checks[key]}")

    json_errors = checks["json_errors"]
    if json_errors:
        print("JSON validation errors:")
        for err in json_errors:
            print(f"  - {err}")

    missing = [key for key in ("manifests", "diagnostics") if int(checks[key]) <= 0]
    if missing:
        print("Missing required T30 inputs:")
        for key in missing:
            print(f"  - {key}: expected > 0")

    print("Next steps:")
    print("  python scripts/fetch_ohlcv_history_for_evaluation.py --project-root .")
    print("  python scripts/run_t30_evaluation.py --project-root .")

    if args.strict and (missing or json_errors):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
