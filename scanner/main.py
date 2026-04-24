from __future__ import annotations

import argparse
import sys

from .config import load_config
from .runners import run_daily_scan, run_intraday_scan

_DAILY_RUN_MODES = {"daily_discovery", "standard", "fast", "offline", "backtest"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Spot Altcoin Scanner – daily pipeline runner"
    )
    parser.add_argument(
        "--mode",
        choices=["daily_discovery", "standard", "fast", "offline", "backtest", "intraday_promotion"],
        help="Override run_mode from config.yml",
    )
    return parser.parse_args(argv)


def _resolve_effective_run_mode(cfg, cli_override: str | None) -> str:
    if cli_override:
        cfg.raw.setdefault("general", {})["run_mode"] = cli_override
    mode = str(cfg.run_mode)
    if mode in _DAILY_RUN_MODES or mode == "intraday_promotion":
        return mode
    raise ValueError(
        f"invalid run_mode {mode!r}: expected one of "
        f"{sorted(_DAILY_RUN_MODES | {'intraday_promotion'})}"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    cfg = load_config()
    effective_mode = _resolve_effective_run_mode(cfg, args.mode)
    if effective_mode == "intraday_promotion":
        run_intraday_scan(cfg)
    else:
        run_daily_scan(cfg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
