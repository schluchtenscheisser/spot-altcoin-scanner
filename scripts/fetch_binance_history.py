#!/usr/bin/env python3
"""Fetch Binance Spot USDT OHLCV history for Historical Signal-Quality Replay Pre-1."""

from __future__ import annotations

import argparse
import sys

from scanner.evaluation.history.history_fetch_config import (
    DEFAULT_EVALUATION_END_DATE,
    DEFAULT_EVALUATION_START_DATE,
    DEFAULT_FETCH_END_DATE,
    DEFAULT_FETCH_START_DATE,
    HistoryFetchConfig,
)
from scanner.evaluation.history.ohlcv_history_fetch import run_history_fetch


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fetch-start-date", default=DEFAULT_FETCH_START_DATE)
    parser.add_argument("--fetch-end-date", default=DEFAULT_FETCH_END_DATE)
    parser.add_argument("--evaluation-start-date", default=DEFAULT_EVALUATION_START_DATE)
    parser.add_argument("--evaluation-end-date", default=DEFAULT_EVALUATION_END_DATE)
    parser.add_argument("--mexc-universe-path")
    parser.add_argument("--output-root", default="snapshots/history/ohlcv")
    parser.add_argument("--manifest-root", default="snapshots/history/manifests")
    parser.add_argument(
        "--universe-mode",
        choices=("fixed_current_mexc_binance_intersection", "binance_spot_usdt_all"),
        default="fixed_current_mexc_binance_intersection",
    )
    parser.add_argument("--force-repair", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = HistoryFetchConfig.resolve(
            fetch_start_date=args.fetch_start_date,
            fetch_end_date=args.fetch_end_date,
            evaluation_start_date=args.evaluation_start_date,
            evaluation_end_date=args.evaluation_end_date,
            output_root=args.output_root,
            manifest_root=args.manifest_root,
            mexc_universe_path=args.mexc_universe_path,
            universe_mode=args.universe_mode,
            force_repair=args.force_repair,
        )
        outcome = run_history_fetch(config, dry_run=args.dry_run)
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        f"fetch_run_id={outcome.history_manifest['fetch_run_id']} symbols={outcome.history_manifest['symbols_total']} "
        f"rows={sum(outcome.history_manifest['bar_counts_by_timeframe'].values())} dry_run={args.dry_run}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
