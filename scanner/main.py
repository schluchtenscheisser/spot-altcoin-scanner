from __future__ import annotations

import argparse
import sys

from .config import load_config
from .run_modes import ACCEPTED_CLI_RUN_MODES, resolve_cli_mode_to_runner
from .runners import run_daily_scan, run_intraday_scan


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spot Altcoin Scanner – daily pipeline runner"
    )
    parser.add_argument(
        "--mode",
        choices=list(ACCEPTED_CLI_RUN_MODES),
        help="Override run_mode from config.yml",
    )
    return parser.parse_args(argv)


def _resolve_effective_run_mode(cfg, cli_override: str | None) -> str:
    if cli_override:
        cfg.raw.setdefault("general", {})["run_mode"] = cli_override
    return resolve_cli_mode_to_runner(str(cfg.run_mode))


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config()
    effective_mode = _resolve_effective_run_mode(cfg, args.mode)
    if effective_mode == "intraday":
        run_intraday_scan(cfg)
    else:
        run_daily_scan(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
