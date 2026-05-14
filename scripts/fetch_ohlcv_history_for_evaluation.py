#!/usr/bin/env python3
"""Build candidate-scoped 1d OHLCV history for T30 evaluation.

The generated Parquet history is intentionally artifact-only. It is written
under snapshots/history/ohlcv/... so T18 forward-return replay can consume it,
but .gitignore keeps the market-data files out of repository commits.
"""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
from pathlib import Path

PROJECT_ROOT_FOR_IMPORTS = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT_FOR_IMPORTS) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT_FOR_IMPORTS))

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Any, Iterable

import pandas as pd

from scanner.clients.mexc_client import MEXCClient
from scanner.data.bar_clock import daily_bar_id

UTC = timezone.utc
DEFAULT_START_DATE = "2026-05-03"
DEFAULT_INCLUDE_BUCKETS = ("confirmed_candidates", "early_candidates")
DEFAULT_HORIZONS = (1, 3, 5, 10)
SOURCE = "mexc_spot_klines"
TIMEFRAME = "1d"
OUTPUT_COLUMNS = [
    "symbol",
    "timeframe",
    "daily_bar_id",
    "open_time_utc_ms",
    "close_time_utc_ms",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "source",
    "fetched_at_utc",
]
ALLOWED_SYMBOL_SOURCES = {"auto", "reports", "diagnostics"}
ALLOWED_STATUSES = {"fetched", "refreshed_existing", "no_valid_bars", "fetch_failed", "skipped_existing_complete"}


@dataclass
class RunSourceResult:
    symbols: set[str] = field(default_factory=set)
    source_used: str | None = None
    skipped_reason: str | None = None


@dataclass
class UniverseResult:
    symbols: list[str]
    skipped_runs: list[dict[str, str]]
    runs_considered: int
    runs_used: int
    source_counts: dict[str, int]


@dataclass(frozen=True)
class OhlcvWriteResult:
    partition_paths: list[str]
    new_row_count: int
    replaced_row_count: int
    existing_duplicate_row_count: int
    valid_input_row_count: int
    bars_written: int
    first_daily_bar_id: str | None
    last_daily_bar_id: str | None

    def to_summary(self) -> dict[str, Any]:
        return {
            "bars_written": self.bars_written,
            "first_daily_bar_id": self.first_daily_bar_id,
            "last_daily_bar_id": self.last_daily_bar_id,
            "partition_paths": self.partition_paths,
            "new_row_count": self.new_row_count,
            "replaced_row_count": self.replaced_row_count,
            "existing_duplicate_row_count": self.existing_duplicate_row_count,
            "valid_input_row_count": self.valid_input_row_count,
        }

    def __getitem__(self, key: str) -> Any:
        return self.to_summary()[key]


def _now_utc() -> datetime:
    return datetime.now(tz=UTC)


def iso_now() -> str:
    return _now_utc().replace(microsecond=0).isoformat().replace("+00:00", "Z")


def latest_closed_daily_bar_date(now: datetime | None = None) -> str:
    return daily_bar_id(now or _now_utc())


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def parse_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def parse_horizons(value: str) -> list[int]:
    horizons = [int(item) for item in parse_csv(value)]
    if not horizons or any(h <= 0 for h in horizons):
        raise argparse.ArgumentTypeError("--horizons must contain positive integers")
    return horizons


def _project_path(project_root: Path, configured_path: str | Path) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else project_root / path


def _load_json_object(path: Path) -> dict[str, Any] | None:
    try:
        if not path.is_file() or path.stat().st_size == 0:
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _extract_symbol_from_item(item: Any) -> str | None:
    if isinstance(item, str):
        symbol = item.strip()
        return symbol or None
    if isinstance(item, dict):
        symbol = item.get("symbol")
        if isinstance(symbol, str) and symbol.strip():
            return symbol.strip()
    return None


def extract_symbols_from_report(report: dict[str, Any], include_buckets: Iterable[str]) -> set[str]:
    symbols: set[str] = set()
    candidate_containers: list[Any] = []
    if isinstance(report.get("symbol_lists"), dict):
        candidate_containers.append(report["symbol_lists"])
    # Compatibility for older/additive report-level segment containers that may
    # carry bucket arrays with either strings or objects containing `symbol`.
    for key in ("candidate_segments", "entry_location_candidate_segments", "execution_aware_candidate_segments"):
        if isinstance(report.get(key), dict):
            candidate_containers.append(report[key])

    for container in candidate_containers:
        for bucket in include_buckets:
            items = container.get(bucket)
            if not isinstance(items, list):
                continue
            for item in items:
                symbol = _extract_symbol_from_item(item)
                if symbol:
                    symbols.add(symbol)
    return symbols


def _report_has_candidate_lists(report: dict[str, Any], include_buckets: Iterable[str]) -> bool:
    symbol_lists = report.get("symbol_lists")
    return isinstance(symbol_lists, dict) and any(isinstance(symbol_lists.get(bucket), list) for bucket in include_buckets)


def extract_symbols_from_diagnostics(path: Path, include_buckets: Iterable[str]) -> set[str] | None:
    allowed = set(include_buckets)
    symbols: set[str] = set()
    records_seen = 0
    try:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                record = json.loads(raw)
                if not isinstance(record, dict):
                    continue
                records_seen += 1
                decision = record.get("decision")
                bucket = decision.get("decision_bucket") if isinstance(decision, dict) else None
                if bucket not in allowed:
                    continue
                symbol = record.get("symbol")
                if isinstance(symbol, str) and symbol.strip():
                    symbols.add(symbol.strip())
    except (OSError, EOFError, json.JSONDecodeError):
        return None
    return symbols if records_seen > 0 else None


def _iter_run_report_paths(reports_root: Path, start: date, end: date) -> list[Path]:
    paths: list[Path] = []
    runs_root = reports_root
    for path in sorted(runs_root.glob("*/*/*/*/report.json")):
        try:
            rel = path.relative_to(runs_root)
            run_date = date(int(rel.parts[0]), int(rel.parts[1]), int(rel.parts[2]))
        except (ValueError, IndexError):
            continue
        if start <= run_date <= end:
            paths.append(path)
    return paths


def _extract_run_symbols(report_path: Path, include_buckets: list[str], symbol_source: str) -> RunSourceResult:
    diagnostics_path = report_path.with_name("symbol_diagnostics.jsonl.gz")
    report = _load_json_object(report_path)

    if symbol_source in {"auto", "diagnostics"} and diagnostics_path.is_file():
        diagnostic_symbols = extract_symbols_from_diagnostics(diagnostics_path, include_buckets)
        if diagnostic_symbols is not None:
            return RunSourceResult(symbols=diagnostic_symbols, source_used="diagnostics")
        if symbol_source == "diagnostics":
            return RunSourceResult(skipped_reason="invalid_diagnostics")

    if symbol_source == "diagnostics":
        return RunSourceResult(skipped_reason="missing_diagnostics")

    if report is None:
        return RunSourceResult(skipped_reason="missing_or_invalid_report")
    if not _report_has_candidate_lists(report, include_buckets):
        return RunSourceResult(skipped_reason="missing_report_candidate_lists")
    return RunSourceResult(symbols=extract_symbols_from_report(report, include_buckets), source_used="reports")


def collect_symbol_universe(
    *,
    reports_root: Path,
    start_date: str,
    end_date: str,
    include_buckets: list[str],
    symbol_source: str,
) -> UniverseResult:
    if symbol_source not in ALLOWED_SYMBOL_SOURCES:
        raise ValueError(f"invalid symbol_source: {symbol_source}")
    start = parse_date(start_date)
    end = parse_date(end_date)
    symbols: set[str] = set()
    skipped_runs: list[dict[str, str]] = []
    source_counts = {"reports": 0, "diagnostics": 0}
    runs_used = 0
    run_paths = _iter_run_report_paths(reports_root, start, end)
    for report_path in run_paths:
        result = _extract_run_symbols(report_path, include_buckets, symbol_source)
        if result.source_used:
            runs_used += 1
            source_counts[result.source_used] += 1
            symbols.update(result.symbols)
        else:
            skipped_runs.append({"path": report_path.as_posix(), "reason": result.skipped_reason or "unusable_run"})
    return UniverseResult(
        symbols=sorted(symbols),
        skipped_runs=skipped_runs,
        runs_considered=len(run_paths),
        runs_used=runs_used,
        source_counts=source_counts,
    )


def _to_int_or_none(value: Any) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return int(numeric)


def _to_float_or_none(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    return numeric if math.isfinite(numeric) else None


def _positive_required(value: Any) -> float | None:
    numeric = _to_float_or_none(value)
    if numeric is None or numeric <= 0:
        return None
    return numeric


def _nonnegative_optional(value: Any) -> float | None:
    numeric = _to_float_or_none(value)
    if numeric is None:
        return None
    return numeric if numeric >= 0 else None


def normalize_klines(
    symbol: str,
    klines: Iterable[Any],
    *,
    start_date: str,
    fetch_end_date: str,
    fetched_at_utc: str,
    now_utc: object | None = None,
) -> tuple[pd.DataFrame, int]:
    start = parse_date(start_date)
    latest_closed = parse_date(latest_closed_daily_bar_date(now_utc if now_utc is not None else _now_utc()))
    end = min(parse_date(fetch_end_date), latest_closed)
    rows: list[dict[str, Any]] = []
    invalid_count = 0
    for kline in klines or []:
        if not isinstance(kline, (list, tuple)) or len(kline) < 6:
            invalid_count += 1
            continue
        open_time = _to_int_or_none(kline[0])
        close_time = _to_int_or_none(kline[6]) if len(kline) > 6 else None
        open_price = _positive_required(kline[1])
        high = _positive_required(kline[2])
        low = _positive_required(kline[3])
        close = _positive_required(kline[4])
        volume_raw = _to_float_or_none(kline[5])
        quote_raw = _to_float_or_none(kline[7]) if len(kline) > 7 else None
        if None in (open_time, open_price, high, low, close):
            invalid_count += 1
            continue
        if volume_raw is not None and volume_raw < 0:
            invalid_count += 1
            continue
        if quote_raw is not None and quote_raw < 0:
            invalid_count += 1
            continue
        # MEXC daily klines open at 00:00 UTC and close just before the next
        # boundary. T18 indexes rows by the calendar session date, so derive the
        # `daily_bar_id` from open time rather than the near-midnight close time.
        bar_date = datetime.fromtimestamp(open_time / 1000.0, tz=UTC).date()
        if not (start <= bar_date <= end):
            continue
        rows.append(
            {
                "symbol": symbol,
                "timeframe": TIMEFRAME,
                "daily_bar_id": bar_date.isoformat(),
                "open_time_utc_ms": open_time,
                "close_time_utc_ms": close_time,
                "open": float(open_price),
                "high": float(high),
                "low": float(low),
                "close": float(close),
                "volume": _nonnegative_optional(kline[5]),
                "quote_volume": _nonnegative_optional(kline[7]) if len(kline) > 7 else None,
                "source": SOURCE,
                "fetched_at_utc": fetched_at_utc,
            }
        )
    df = pd.DataFrame(rows, columns=OUTPUT_COLUMNS)
    if not df.empty:
        df = df.drop_duplicates(subset=["daily_bar_id"], keep="last").sort_values("daily_bar_id").reset_index(drop=True)
    return df, invalid_count


def _partition_path(history_root: Path, symbol: str, year: str, month: str) -> Path:
    return history_root / "ohlcv" / "timeframe=1d" / f"symbol={symbol}" / f"year={year}" / f"month={month}" / "part-000.parquet"


def write_ohlcv_partitions(history_root: Path, symbol: str, bars: pd.DataFrame, *, force_refetch: bool = False) -> OhlcvWriteResult:
    if bars.empty:
        return OhlcvWriteResult([], 0, 0, 0, 0, 0, None, None)

    partition_paths: list[str] = []
    new_row_count = 0
    replaced_row_count = 0
    existing_duplicate_row_count = 0
    work = bars.copy()
    work["year"] = work["daily_bar_id"].str.slice(0, 4)
    work["month"] = work["daily_bar_id"].str.slice(5, 7)
    for (year, month), group in work.groupby(["year", "month"], sort=True):
        path = _partition_path(history_root, symbol, str(year), str(month))
        new_rows = group[OUTPUT_COLUMNS].copy()
        if path.exists():
            existing = pd.read_parquet(path).reindex(columns=OUTPUT_COLUMNS)
        else:
            existing = pd.DataFrame(columns=OUTPUT_COLUMNS)

        existing_ids = set(existing["daily_bar_id"].dropna().astype(str).tolist()) if not existing.empty else set()
        fetched_ids = set(new_rows["daily_bar_id"].dropna().astype(str).tolist())
        duplicate_ids = fetched_ids & existing_ids
        added_ids = fetched_ids - existing_ids
        existing_duplicate_row_count += len(duplicate_ids)
        new_row_count += len(added_ids)
        if force_refetch:
            replaced_row_count += len(duplicate_ids)

        should_write = bool(added_ids) or bool(force_refetch and duplicate_ids) or not path.exists()
        if not should_write:
            continue

        if force_refetch:
            merged = pd.concat([existing, new_rows], ignore_index=True).drop_duplicates(
                subset=["daily_bar_id"], keep="last"
            )
        else:
            merged = pd.concat([existing, new_rows], ignore_index=True).drop_duplicates(
                subset=["daily_bar_id"], keep="first"
            )
        merged = merged.sort_values("daily_bar_id").reset_index(drop=True)
        if merged.empty:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        merged.to_parquet(path, index=False)
        partition_paths.append(path.as_posix())

    return OhlcvWriteResult(
        partition_paths=partition_paths,
        new_row_count=int(new_row_count),
        replaced_row_count=int(replaced_row_count),
        existing_duplicate_row_count=int(existing_duplicate_row_count),
        valid_input_row_count=int(len(bars)),
        bars_written=int(new_row_count + replaced_row_count),
        first_daily_bar_id=str(bars["daily_bar_id"].min()),
        last_daily_bar_id=str(bars["daily_bar_id"].max()),
    )


def _symbol_has_history(history_root: Path, symbol: str) -> bool:
    base = history_root / "ohlcv" / "timeframe=1d" / f"symbol={symbol}"
    return any(base.glob("year=*/month=*/*.parquet")) if base.exists() else False


def build_symbols_manifest(*, generated_at: str, start_date: str, end_date: str, include_buckets: list[str], symbol_source: str, symbols: list[str]) -> dict[str, Any]:
    return {
        "generated_at_utc": generated_at,
        "start_date": start_date,
        "end_date": end_date,
        "include_buckets": include_buckets,
        "symbol_source": symbol_source,
        "symbol_count": len(symbols),
        "symbols": symbols,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_and_write_history(
    args: argparse.Namespace,
    *,
    client: MEXCClient | None = None,
    now_utc: object | None = None,
) -> tuple[int, dict[str, Any], dict[str, Any]]:
    project_root = Path(args.project_root).resolve()
    reports_root = _project_path(project_root, args.reports_root)
    history_root = _project_path(project_root, args.history_root)
    output_summary = _project_path(project_root, args.output_summary)
    output_symbols = _project_path(project_root, args.output_symbols)
    end_date = args.end_date or latest_closed_daily_bar_date()
    include_buckets = parse_csv(args.include_buckets) if isinstance(args.include_buckets, str) else list(args.include_buckets)
    horizons = parse_horizons(args.horizons) if isinstance(args.horizons, str) else list(args.horizons)
    generated_at = iso_now()

    universe = collect_symbol_universe(
        reports_root=reports_root,
        start_date=args.start_date,
        end_date=end_date,
        include_buckets=include_buckets,
        symbol_source=args.symbol_source,
    )
    symbols = universe.symbols[: args.max_symbols] if args.max_symbols else universe.symbols
    symbols_manifest = build_symbols_manifest(
        generated_at=generated_at,
        start_date=args.start_date,
        end_date=end_date,
        include_buckets=include_buckets,
        symbol_source=args.symbol_source,
        symbols=symbols,
    )

    summary: dict[str, Any] = {
        "generated_at_utc": generated_at,
        "start_date": args.start_date,
        "end_date": end_date,
        "horizons_days": horizons,
        "symbol_source": args.symbol_source,
        "symbol_count": len(symbols),
        "symbols_fetched": 0,
        "symbols_with_existing_history": 0,
        "symbols_with_new_history": 0,
        "symbols_refreshed_existing": 0,
        "symbols_without_valid_bars": 0,
        "invalid_bar_count": 0,
        "written_partition_count": 0,
        "skipped_run_count": len(universe.skipped_runs),
        "skipped_runs": universe.skipped_runs,
        "runs_considered": universe.runs_considered,
        "runs_used": universe.runs_used,
        "source_counts": universe.source_counts,
        "dry_run": bool(args.dry_run),
        "per_symbol": {},
    }

    _write_json(output_symbols, symbols_manifest)

    if not symbols:
        _write_json(output_summary, summary)
        if args.fail_on_empty_universe:
            return 2, summary, symbols_manifest
        return 0, summary, symbols_manifest

    if args.dry_run:
        for symbol in symbols:
            summary["per_symbol"][symbol] = {
                "status": "skipped_existing_complete",
                "bars_written": 0,
                "first_daily_bar_id": None,
                "last_daily_bar_id": None,
                "partition_paths": [],
            }
        _write_json(output_summary, summary)
        return 0, summary, symbols_manifest

    mexc = client or MEXCClient()
    fetch_end = (parse_date(end_date) + timedelta(days=max(horizons))).isoformat()
    limit = min(max(int(args.mexc_limit), 1), 1000)
    for symbol in symbols:
        had_existing = _symbol_has_history(history_root, symbol)
        if had_existing:
            summary["symbols_with_existing_history"] += 1
        try:
            klines = mexc.get_klines(symbol, interval=TIMEFRAME, limit=limit, use_cache=bool(args.use_cache))
            summary["symbols_fetched"] += 1
        except Exception as exc:  # noqa: BLE001 - summary must record per-symbol API failures.
            summary["per_symbol"][symbol] = {
                "status": "fetch_failed",
                "error": str(exc),
                "bars_written": 0,
                "first_daily_bar_id": None,
                "last_daily_bar_id": None,
                "partition_paths": [],
            }
            continue
        bars, invalid_count = normalize_klines(
            symbol,
            klines,
            start_date=args.start_date,
            fetch_end_date=fetch_end,
            fetched_at_utc=generated_at,
            now_utc=now_utc,
        )
        summary["invalid_bar_count"] += invalid_count
        if bars.empty:
            summary["symbols_without_valid_bars"] += 1
            summary["per_symbol"][symbol] = {
                "status": "no_valid_bars",
                "bars_written": 0,
                "first_daily_bar_id": None,
                "last_daily_bar_id": None,
                "partition_paths": [],
            }
            continue
        write_result = write_ohlcv_partitions(history_root, symbol, bars, force_refetch=bool(args.force_refetch))
        if write_result.new_row_count > 0:
            status = "fetched"
            summary["symbols_with_new_history"] += 1
        elif write_result.replaced_row_count > 0:
            status = "refreshed_existing"
            summary["symbols_refreshed_existing"] += 1
        else:
            status = "skipped_existing_complete"
        summary["written_partition_count"] += len(write_result.partition_paths)
        summary["per_symbol"][symbol] = {"status": status, **write_result.to_summary()}

    _write_json(output_summary, summary)
    return 0, summary, symbols_manifest


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch candidate-scoped 1d OHLCV history for T30 evaluation.")
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--reports-root", default="reports/runs")
    parser.add_argument("--snapshots-runs-root", default="snapshots/runs")
    parser.add_argument("--history-root", default="snapshots/history")
    parser.add_argument("--start-date", default=DEFAULT_START_DATE)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--horizons", default=",".join(str(h) for h in DEFAULT_HORIZONS))
    parser.add_argument("--include-buckets", default=",".join(DEFAULT_INCLUDE_BUCKETS))
    parser.add_argument("--symbol-source", choices=sorted(ALLOWED_SYMBOL_SOURCES), default="auto")
    parser.add_argument("--output-summary", default="evaluation/replay/ohlcv_history_fetch_summary.json")
    parser.add_argument("--output-symbols", default="evaluation/replay/ohlcv_history_symbols.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--use-cache", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--max-symbols", type=int, default=None)
    parser.add_argument("--force-refetch", action="store_true")
    parser.add_argument("--fail-on-empty-universe", action="store_true")
    parser.add_argument("--mexc-limit", type=int, default=1000)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    if args.max_symbols is not None and args.max_symbols < 1:
        parser.error("--max-symbols must be positive when provided")
    if not (1 <= int(args.mexc_limit) <= 1000):
        parser.error("--mexc-limit must be between 1 and 1000")
    try:
        exit_code, _, _ = fetch_and_write_history(args)
    except Exception as exc:  # noqa: BLE001 - CLI should fail with a concise message.
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
