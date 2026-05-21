from __future__ import annotations

from argparse import ArgumentParser
import sys
from pathlib import Path

from scanner.evaluation.historical_replay.scenario import ScenarioValidationError, load_scenario, scenario_config_hash
from scanner.evaluation.historical_replay.scenario_registry import ensure_scenario_hash
from scanner.evaluation.historical_replay.replay_runner import run_replay


def build_parser() -> ArgumentParser:
    parser = ArgumentParser(description="Validate and register historical daily replay scenario")
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--output-root", default="evaluation/replay")
    parser.add_argument("--dry-run-validate-scenario", action="store_true")
    return parser


def main() -> int:
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
    run_replay(scenario=scenario, output_root=Path(args.output_root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
