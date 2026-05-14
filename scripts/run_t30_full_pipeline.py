#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], *, cwd: Path) -> None:
    print("\n$ " + " ".join(cmd), flush=True)
    subprocess.run(cmd, cwd=cwd, check=True)


def _count_paths(root: Path, pattern: str) -> int:
    if not root.exists():
        return 0
    return sum(1 for _ in root.rglob(pattern))


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run the complete T30 v1 pipeline in one GitHub Actions run: "
            "download Shadow-Live artifacts, prepare T30 inputs, fetch OHLCV history, "
            "and run forward-return evaluation."
        )
    )
    parser.add_argument("--project-root", default=".", type=Path)
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "schluchtenscheisser/spot-altcoin-scanner"))
    parser.add_argument("--since", default="2026-05-03")
    parser.add_argument(
        "--artifact-prefix",
        default="independence-shadow-live-",
        help="Artifact prefix to download. Default downloads only main Shadow-Live artifacts.",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=None,
        help="Optional max workflow runs to inspect. Omit for default downloader behavior.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip artifact download and use existing data/shadow-live-zips.",
    )
    parser.add_argument(
        "--skip-ohlcv-fetch",
        action="store_true",
        help="Skip OHLCV fetch and use existing snapshots/history/ohlcv.",
    )
    parser.add_argument(
        "--non-strict-prepare",
        action="store_true",
        help="Run prepare_t30_inputs without --strict.",
    )
    args = parser.parse_args()

    project_root = args.project_root.resolve()

    required_scripts = [
        "scripts/download_shadow_live_artifacts.py",
        "scripts/prepare_t30_inputs_from_shadow_live_zips.py",
        "scripts/fetch_ohlcv_history_for_evaluation.py",
        "scripts/run_t30_evaluation.py",
    ]
    missing = [p for p in required_scripts if not (project_root / p).is_file()]
    if missing:
        print("ERROR: Missing required scripts:", file=sys.stderr)
        for p in missing:
            print(f"  - {p}", file=sys.stderr)
        return 2

    if not args.skip_download:
        dl_cmd = [
            sys.executable,
            "scripts/download_shadow_live_artifacts.py",
            "--repo",
            args.repo,
            "--since",
            args.since,
            "--artifact-prefix",
            args.artifact_prefix,
        ]
        if args.max_runs is not None:
            dl_cmd.extend(["--max-runs", str(args.max_runs)])
        _run(dl_cmd, cwd=project_root)
    else:
        print("Skipping artifact download because --skip-download was set.", flush=True)

    prep_cmd = [
        sys.executable,
        "scripts/prepare_t30_inputs_from_shadow_live_zips.py",
        "--project-root",
        ".",
    ]
    if not args.non_strict_prepare:
        prep_cmd.append("--strict")
    _run(prep_cmd, cwd=project_root)

    manifest_count = _count_paths(project_root / "snapshots" / "runs", "run.manifest.json")
    diagnostics_count = _count_paths(project_root / "reports" / "runs", "symbol_diagnostics.jsonl.gz")
    report_count = _count_paths(project_root / "reports" / "runs", "report.json")

    print("\nPrepared T30 input counts:", flush=True)
    print(f"  run.manifest.json:           {manifest_count}", flush=True)
    print(f"  symbol_diagnostics.jsonl.gz: {diagnostics_count}", flush=True)
    print(f"  report.json:                 {report_count}", flush=True)

    if manifest_count == 0 or diagnostics_count == 0:
        print(
            "ERROR: T30 inputs are incomplete. Need both snapshots/runs/**/run.manifest.json "
            "and reports/runs/**/symbol_diagnostics.jsonl.gz.",
            file=sys.stderr,
        )
        return 3

    if not args.skip_ohlcv_fetch:
        _run(
            [
                sys.executable,
                "scripts/fetch_ohlcv_history_for_evaluation.py",
                "--project-root",
                ".",
            ],
            cwd=project_root,
        )
    else:
        print("Skipping OHLCV fetch because --skip-ohlcv-fetch was set.", flush=True)

    ohlcv_count = _count_paths(project_root / "snapshots" / "history" / "ohlcv", "*.parquet")
    print(f"\nOHLCV parquet files: {ohlcv_count}", flush=True)
    if ohlcv_count == 0:
        print(
            "ERROR: No OHLCV parquet files found under snapshots/history/ohlcv. "
            "T30 would produce missing_ohlcv_history.",
            file=sys.stderr,
        )
        return 4

    _run(
        [
            sys.executable,
            "scripts/run_t30_evaluation.py",
            "--project-root",
            ".",
        ],
        cwd=project_root,
    )

    expected_outputs = [
        "evaluation/notes/T30_forward_return_evaluation_v1.md",
        "evaluation/exports/evaluation_summary.json",
        "evaluation/exports/signal_event_metrics.parquet",
        "evaluation/exports/terminal_event_timeline.parquet",
        "evaluation/exports/transition_lead_times.parquet",
        "evaluation/replay/event_timeline.jsonl",
        "evaluation/replay/replay_diagnostics.json",
    ]

    print("\nT30 expected outputs:", flush=True)
    missing_outputs: list[str] = []
    for rel in expected_outputs:
        exists = (project_root / rel).exists()
        print(f"  {'OK     ' if exists else 'MISSING'} {rel}", flush=True)
        if not exists:
            missing_outputs.append(rel)

    if missing_outputs:
        print("ERROR: T30 completed but expected outputs are missing.", file=sys.stderr)
        return 5

    print("\nPASS: T30 full pipeline completed.", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
