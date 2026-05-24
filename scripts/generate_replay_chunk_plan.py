from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from scanner.evaluation.historical_replay.scenario import load_scenario


def _month_end(d: date) -> date:
    first_next = (d.replace(day=1) + timedelta(days=32)).replace(day=1)
    return first_next - timedelta(days=1)


def _iter_monthly_chunks(start: date, end: date) -> list[tuple[date, date]]:
    chunks: list[tuple[date, date]] = []
    current = start
    while current <= end:
        chunk_end = min(_month_end(current), end)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)
    return chunks


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Generate chunk plan for historical replay workflow")
    p.add_argument("--scenario", required=True)
    p.add_argument("--run-mode", choices=["full_chunked", "single_chunk"], required=True)
    p.add_argument("--chunk-start", default="")
    p.add_argument("--chunk-end", default="")
    p.add_argument("--resume-from-artifact", default="")
    p.add_argument("--replay-id", default="")
    p.add_argument("--output-plan", required=True)
    return p


def main() -> int:
    args = _build_parser().parse_args()
    scenario_path = Path(args.scenario)
    scenario = load_scenario(scenario_path)

    eval_start = scenario.evaluation.start_date
    eval_end = scenario.evaluation.end_date

    replay_id = args.replay_id.strip() or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    chunks: list[dict[str, object]] = []
    if args.run_mode == "full_chunked":
        ranges = _iter_monthly_chunks(eval_start, eval_end)
    else:
        if not args.chunk_start or not args.chunk_end:
            raise SystemExit("chunk_start and chunk_end are required for single_chunk mode")
        chunk_start = date.fromisoformat(args.chunk_start)
        chunk_end = date.fromisoformat(args.chunk_end)
        if chunk_start < eval_start or chunk_end > eval_end or chunk_start > chunk_end:
            raise SystemExit("single_chunk boundaries must be within scenario evaluation window")
        if chunk_start > eval_start and not args.resume_from_artifact.strip():
            raise SystemExit(
                "ERROR: resume_from_artifact is required for single_chunk mode when chunk_start > evaluation.start_date"
            )
        ranges = [(chunk_start, chunk_end)]

    for idx, (chunk_start, chunk_end) in enumerate(ranges):
        chunks.append(
            {
                "chunk_id": f"{chunk_start.isoformat()}_to_{chunk_end.isoformat()}",
                "chunk_start": chunk_start.isoformat(),
                "chunk_end": chunk_end.isoformat(),
                "is_first": idx == 0,
            }
        )

    if not chunks:
        raise SystemExit("chunk plan is empty")

    plan = {
        "scenario_id": scenario.scenario_id,
        "replay_id": replay_id,
        "scenario_path": scenario_path.as_posix(),
        "run_mode": args.run_mode,
        "evaluation_start_date": eval_start.isoformat(),
        "evaluation_end_date": eval_end.isoformat(),
        "chunks": chunks,
    }

    output = Path(args.output_plan)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
