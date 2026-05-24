from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path


def _find_single_state_file(resume_state_dir: Path) -> Path:
    matches = list(resume_state_dir.rglob("state_final.sqlite"))
    if len(matches) == 0:
        raise SystemExit("ERROR: resume_state_dir contains zero state_final.sqlite files")
    if len(matches) > 1:
        raise SystemExit("ERROR: resume_state_dir contains multiple state_final.sqlite files")
    return matches[0]


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run replay chunks sequentially")
    p.add_argument("--scenario", required=True)
    p.add_argument("--chunk-plan", required=True)
    p.add_argument("--output-root", required=True)
    p.add_argument("--resume-state-dir", default="")
    return p


def main() -> int:
    args = _build_parser().parse_args()
    plan = json.loads(Path(args.chunk_plan).read_text(encoding="utf-8"))
    scenario_id = plan["scenario_id"]
    replay_id = plan["replay_id"]
    scenario_path = plan["scenario_path"]
    chunks = plan["chunks"]

    run_dir = Path(args.output_root) / "runs" / scenario_id / replay_id

    total_start = time.time()
    for idx, chunk in enumerate(chunks):
        chunk_id = chunk["chunk_id"]
        chunk_start = chunk["chunk_start"]
        chunk_end = chunk["chunk_end"]
        chunk_timer = time.time()

        cmd = [
            sys.executable,
            "scanner/tools/run_historical_daily_replay.py",
            "--scenario",
            scenario_path,
            "--output-root",
            args.output_root,
            "--replay-id",
            replay_id,
            "--chunk-start",
            chunk_start,
            "--chunk-end",
            chunk_end,
            "--chunk-id",
            chunk_id,
        ]

        if idx == 0 and args.resume_state_dir:
            cmd.extend(["--resume-from-state", str(_find_single_state_file(Path(args.resume_state_dir)))])
        elif idx > 0:
            prev_chunk_id = chunks[idx - 1]["chunk_id"]
            prev_state = run_dir / "chunks" / prev_chunk_id / "state_final.sqlite"
            cmd.extend(["--resume-from-state", str(prev_state)])

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            print(f"ERROR: chunk {chunk_id} failed with exit code {result.returncode}", file=sys.stderr)
            return result.returncode

        current_state = run_dir / "chunks" / chunk_id / "state_final.sqlite"
        if not current_state.exists():
            print(f"ERROR: expected state file missing after chunk {chunk_id}: {current_state}", file=sys.stderr)
            return 1

        print(f"chunk {chunk_id} completed in {time.time() - chunk_timer:.2f}s")

    manifest_path = run_dir / "replay_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        print(f"all chunks complete in {time.time() - total_start:.2f}s; final_event_count={manifest.get('final_event_count')}")
    else:
        print(f"all chunks complete in {time.time() - total_start:.2f}s; replay_manifest.json not found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
