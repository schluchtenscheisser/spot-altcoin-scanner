from __future__ import annotations

import argparse
import json
import re
import sys
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from scanner.config import ScannerConfig, load_config
from scanner.pipeline.snapshot import SnapshotManager

SYMBOL_CACHE_RE = re.compile(r"^mexc_klines_(?P<symbol>[A-Z0-9]+)_1d\.json$")


@dataclass(frozen=True)
class BackfillStats:
    scanned: int = 0
    created: int = 0
    skipped_existing: int = 0
    missing: int = 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _snapshot_base(now: datetime, run_date: str, features: dict[str, dict[str, dict[str, float]]], mode: str, source: str) -> dict[str, Any]:
    asof_ts_ms = int(now.timestamp() * 1000)
    asof_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "meta": {
            "date": run_date,
            "created_at": now.isoformat().replace("+00:00", "Z"),
            "version": "1.1",
            "asof_ts_ms": asof_ts_ms,
            "asof_iso": asof_iso,
            "backfill": True,
            "backfill_mode": mode,
            "backfill_source": source,
        },
        "pipeline": {
            "universe_count": 0,
            "filtered_count": 0,
            "shortlist_count": 0,
            "features_count": len(features),
        },
        "data": {
            "universe": [],
            "filtered": [],
            "shortlist": [],
            "features": features,
        },
        "scoring": {
            "reversals": [],
            "breakouts": [],
            "pullbacks": [],
        },
    }


def _extract_ohlcv_row(path: Path, target_date: str) -> tuple[str, dict[str, float]] | None:
    match = SYMBOL_CACHE_RE.match(path.name)
    if not match:
        return None

    with path.open("r", encoding="utf-8") as fh:
        candles = json.load(fh)

    if not isinstance(candles, list):
        raise ValueError(f"Invalid OHLCV cache format: {path}")

    for row in candles:
        if not isinstance(row, list) or len(row) < 5:
            continue
        try:
            open_time_ms = int(float(row[0]))
            row_date = datetime.fromtimestamp(open_time_ms / 1000, tz=timezone.utc).date().isoformat()
            if row_date != target_date:
                continue
            high = float(row[2])
            low = float(row[3])
            close = float(row[4])
        except (TypeError, ValueError):
            continue
        symbol = match.group("symbol")
        return symbol, {"1d": {"close": close, "high": high, "low": low}}

    return None


def _build_minimal_features(ohlcv_cache_dir: Path, target_date: str) -> dict[str, dict[str, dict[str, float]]]:
    date_dir = ohlcv_cache_dir / target_date
    if not date_dir.exists():
        raise FileNotFoundError(
            f"No local OHLCV cache files found for {target_date} in {date_dir}. "
            "Expected source: data/raw/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json"
        )

    files = sorted(path for path in date_dir.iterdir() if path.is_file() and SYMBOL_CACHE_RE.match(path.name))
    if not files:
        raise FileNotFoundError(
            f"No local OHLCV cache files found for {target_date} in {date_dir}. "
            "Expected source: data/raw/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json"
        )

    features: dict[str, dict[str, dict[str, float]]] = {}
    for file_path in files:
        extracted = _extract_ohlcv_row(file_path, target_date)
        if extracted is None:
            continue
        symbol, payload = extracted
        features[symbol] = payload

    if not features:
        raise FileNotFoundError(
            f"No OHLCV candles for {target_date} found in local cache files under {date_dir}. "
            "Tool requires local 1d candles for that date; no API fallback is allowed."
        )

    return dict(sorted(features.items(), key=lambda item: item[0]))


def _run_full_mode(target_day: date, config_path: str, snapshots_dir: Path, dry_run: bool) -> None:
    if dry_run:
        return

    from scanner.pipeline import run_pipeline

    config = load_config(config_path)
    raw_copy = dict(config.raw)
    snapshots_cfg = dict(raw_copy.get("snapshots", {}))
    snapshots_cfg["history_dir"] = str(snapshots_dir)
    raw_copy["snapshots"] = snapshots_cfg
    patched_config = ScannerConfig(raw=raw_copy)

    with _patched_full_mode_time_sources(target_day):
        run_pipeline(patched_config)


def _mark_full_backfill(snapshot_path: Path) -> None:
    with snapshot_path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)

    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure in full mode output: {snapshot_path}")

    meta = payload.setdefault("meta", {})
    if not isinstance(meta, dict):
        raise ValueError(f"Invalid snapshot.meta structure in full mode output: {snapshot_path}")

    meta["backfill"] = True
    meta["backfill_mode"] = "full"
    meta["backfill_source"] = "pipeline"

    with snapshot_path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def _resolve_snapshots_dir(args: argparse.Namespace) -> Path:
    if args.snapshots_dir:
        return Path(args.snapshots_dir)
    return SnapshotManager.resolve_history_dir(load_config(args.config))


def _preflight_requirements(args: argparse.Namespace, start: date, end: date, snapshots_dir: Path, ohlcv_cache_dir: Path) -> None:
    errors: list[str] = []
    for day in _daterange(start, end):
        run_date = day.isoformat()
        snapshot_path = snapshots_dir / f"{run_date}.json"
        if snapshot_path.exists():
            if args.strict_existing:
                errors.append(f"Snapshot already exists for {run_date}: {snapshot_path}")
            continue

        if args.mode == "minimal":
            try:
                _build_minimal_features(ohlcv_cache_dir=ohlcv_cache_dir, target_date=run_date)
            except Exception as exc:  # preflight aggregation
                errors.append(f"{run_date}: {exc}")

    if errors:
        raise FileNotFoundError("Strict preflight failed: " + " | ".join(errors))


def _resolve_cache_date(target_day: date) -> str:
    return target_day.isoformat()


@contextmanager
def _patched_full_mode_time_sources(target_day: date):
    from scanner import pipeline as pipeline_module
    from scanner.utils import io_utils, time_utils

    fake_now = datetime(target_day.year, target_day.month, target_day.day, 0, 0, 0, tzinfo=timezone.utc)

    original_pipeline_utc_now = pipeline_module.utc_now
    original_pipeline_timestamp_to_ms = pipeline_module.timestamp_to_ms
    original_time_utils_utc_now = time_utils.utc_now
    original_time_utils_utc_date = time_utils.utc_date
    original_time_utils_utc_timestamp = time_utils.utc_timestamp
    original_io_get_cache_path = io_utils.get_cache_path

    def _fake_utc_now() -> datetime:
        return fake_now

    def _fake_utc_date() -> str:
        return _resolve_cache_date(target_day)

    def _fake_utc_timestamp() -> str:
        return fake_now.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _fake_timestamp_to_ms(dt: datetime) -> int:
        return int(dt.timestamp() * 1000)

    def _fake_get_cache_path(cache_type: str, date: str | None = None) -> Path:
        return original_io_get_cache_path(cache_type, date or _resolve_cache_date(target_day))

    pipeline_module.utc_now = _fake_utc_now
    pipeline_module.timestamp_to_ms = _fake_timestamp_to_ms
    time_utils.utc_now = _fake_utc_now
    time_utils.utc_date = _fake_utc_date
    time_utils.utc_timestamp = _fake_utc_timestamp
    io_utils.get_cache_path = _fake_get_cache_path
    try:
        yield
    finally:
        pipeline_module.utc_now = original_pipeline_utc_now
        pipeline_module.timestamp_to_ms = original_pipeline_timestamp_to_ms
        time_utils.utc_now = original_time_utils_utc_now
        time_utils.utc_date = original_time_utils_utc_date
        time_utils.utc_timestamp = original_time_utils_utc_timestamp
        io_utils.get_cache_path = original_io_get_cache_path


def backfill(args: argparse.Namespace) -> BackfillStats:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    snapshots_dir = _resolve_snapshots_dir(args)
    snapshots_dir.mkdir(parents=True, exist_ok=True)

    ohlcv_cache_dir = Path(args.ohlcv_cache_dir)

    stats = BackfillStats()

    if args.strict_missing:
        _preflight_requirements(args=args, start=start, end=end, snapshots_dir=snapshots_dir, ohlcv_cache_dir=ohlcv_cache_dir)

    for day in _daterange(start, end):
        run_date = day.isoformat()
        snapshot_path = snapshots_dir / f"{run_date}.json"

        stats = BackfillStats(
            scanned=stats.scanned + 1,
            created=stats.created,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

        if snapshot_path.exists():
            if args.strict_existing:
                raise FileExistsError(f"Snapshot already exists for {run_date}: {snapshot_path}")
            stats = BackfillStats(
                scanned=stats.scanned,
                created=stats.created,
                skipped_existing=stats.skipped_existing + 1,
                missing=stats.missing,
            )
            continue


        if args.mode == "minimal":
            features = _build_minimal_features(ohlcv_cache_dir=ohlcv_cache_dir, target_date=run_date)
            payload = _snapshot_base(
                now=datetime.now(timezone.utc),
                run_date=run_date,
                features=features,
                mode="minimal",
                source="ohlcv_only",
            )
            if not args.dry_run:
                with snapshot_path.open("w", encoding="utf-8") as fh:
                    json.dump(payload, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
        else:
            _run_full_mode(target_day=day, config_path=args.config, snapshots_dir=snapshots_dir, dry_run=args.dry_run)
            if not args.dry_run:
                if not snapshot_path.exists():
                    raise FileNotFoundError(
                        f"Full mode did not produce expected snapshot for {run_date} at {snapshot_path}. "
                        "Historical as-of backfill is best effort and may require local caches/config."
                    )
                _mark_full_backfill(snapshot_path)

        stats = BackfillStats(
            scanned=stats.scanned,
            created=stats.created + 1,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill missing snapshot files by date range")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--mode", choices=["minimal", "full"], default="minimal")
    parser.add_argument("--dry-run", action="store_true", help="Do not write files")
    parser.add_argument("--strict-existing", action="store_true", help="Fail if any target date already has a snapshot")
    parser.add_argument("--strict-missing", action="store_true", help="Preflight dates and fail atomically before writes if any target snapshot is missing")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config (used for snapshots dir and full mode)")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    parser.add_argument(
        "--ohlcv-cache-dir",
        default="data/raw",
        help="Root directory for local OHLCV cache (expected: <root>/<YYYY-MM-DD>/mexc_klines_<SYMBOL>_1d.json)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        stats = backfill(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"mode={args.mode} scanned={stats.scanned} created={stats.created} skipped_existing={stats.skipped_existing} missing={stats.missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
