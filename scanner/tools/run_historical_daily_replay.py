from __future__ import annotations

from argparse import ArgumentParser
from datetime import date
import logging
import sys
import time
from pathlib import Path

from scanner.evaluation.historical_replay.scenario import ScenarioValidationError, load_scenario, scenario_config_hash
from scanner.evaluation.historical_replay.scenario_registry import ensure_scenario_hash
from scanner.evaluation.historical_replay.replay_runner import run_replay


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Validate and register historical daily replay scenario")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output-root", default="evaluation/replay")
    parser.add_argument("--dry-run-validate-scenario", action="store_true")
    parser.add_argument("--chunk-start")
    parser.add_argument("--chunk-end")
    parser.add_argument("--resume-from-state")
    parser.add_argument("--replay-id")
    parser.add_argument("--chunk-id")
    return parser


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%SZ",
    )
    logging.Formatter.converter = time.gmtime
    args = build_parser().parse_args()
    scenario_path = Path(args.scenario)
    try:
        scenario = load_scenario(scenario_path)
    except (ScenarioValidationError, ValueError) as exc:
        print(f"Scenario validation failed: {exc}", file=sys.stderr)
        return 2
    if args.dry_run_validate_scenario:
        return 0
    registry_path = Path(args.output_root) / "scenario_registry.sqlite"
    ensure_scenario_hash(
        registry_path=registry_path,
        scenario_id=scenario.scenario_id,
        scenario_hash=scenario_config_hash(scenario),
        scenario_path=scenario_path.as_posix(),
    )
    chunk_start = date.fromisoformat(args.chunk_start) if args.chunk_start else None
    chunk_end = date.fromisoformat(args.chunk_end) if args.chunk_end else None
    run_replay(
        scenario=scenario,
        output_root=Path(args.output_root),
        chunk_start=chunk_start,
        chunk_end=chunk_end,
        resume_from_state=Path(args.resume_from_state) if args.resume_from_state else None,
        replay_id=args.replay_id,
        chunk_id=args.chunk_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
