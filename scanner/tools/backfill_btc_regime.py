from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable

from scanner.config import load_config
from scanner.pipeline.regime import compute_btc_regime_from_1d_features
from scanner.pipeline.snapshot import SnapshotManager


@dataclass(frozen=True)
class BackfillStats:
    scanned: int = 0
    updated: int = 0
    skipped_existing: int = 0
    missing: int = 0


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure: {path}")
    return payload


def _ensure_minimum_version(meta: dict[str, Any]) -> bool:
    version = meta.get("version")
    if version in (None, "", "1.0"):
        meta["version"] = "1.1"
        return True
    return False


def _extract_btc_features_1d(snapshot: dict[str, Any]) -> dict[str, Any]:
    features = snapshot.get("data", {}).get("features", {})
    btc_features_1d = {}
    if isinstance(features, dict):
        btc = features.get("BTCUSDT", {})
        if isinstance(btc, dict):
            maybe_1d = btc.get("1d", {})
            if isinstance(maybe_1d, dict):
                btc_features_1d = maybe_1d
    return btc_features_1d


def _compute_regime(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    btc_features_1d = _extract_btc_features_1d(snapshot)
    if not btc_features_1d:
        return None
    return compute_btc_regime_from_1d_features(btc_features_1d)


def _resolve_snapshots_dir(args: argparse.Namespace) -> Path:
    if args.snapshots_dir:
        return Path(args.snapshots_dir)
    return SnapshotManager.resolve_history_dir(load_config(args.config))


def _preflight_missing_paths(start: date, end: date, snapshots_dir: Path) -> list[Path]:
    return [snapshots_dir / f"{day.isoformat()}.json" for day in _daterange(start, end) if not (snapshots_dir / f"{day.isoformat()}.json").exists()]


def backfill(args: argparse.Namespace) -> BackfillStats:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    snapshots_dir = _resolve_snapshots_dir(args)

    stats = BackfillStats()
    missing_paths: list[Path] = []

    if args.strict_missing:
        missing_paths = _preflight_missing_paths(start, end, snapshots_dir)
        if missing_paths:
            msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
            raise FileNotFoundError(msg)

    for day in _daterange(start, end):
        stats = BackfillStats(
            scanned=stats.scanned + 1,
            updated=stats.updated,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )
        path = snapshots_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing_paths.append(path)
            stats = BackfillStats(
                scanned=stats.scanned,
                updated=stats.updated,
                skipped_existing=stats.skipped_existing,
                missing=stats.missing + 1,
            )
            continue

        snapshot = _load_snapshot(path)
        meta = snapshot.setdefault("meta", {})
        if not isinstance(meta, dict):
            raise ValueError(f"Invalid snapshot.meta structure: {path}")

        if meta.get("btc_regime") is not None:
            changed = _ensure_minimum_version(meta)
            if changed and not args.dry_run:
                with path.open("w", encoding="utf-8") as fh:
                    json.dump(snapshot, fh, indent=2, ensure_ascii=False)
                    fh.write("\n")
            stats = BackfillStats(
                scanned=stats.scanned,
                updated=stats.updated + (1 if changed else 0),
                skipped_existing=stats.skipped_existing + (0 if changed else 1),
                missing=stats.missing,
            )
            continue

        regime = _compute_regime(snapshot)
        if regime is None:
            meta["btc_regime"] = None
            meta["btc_regime_status"] = "missing_btc_features"
        else:
            meta["btc_regime"] = regime
            if meta.get("btc_regime_status") == "missing_btc_features":
                meta.pop("btc_regime_status", None)
        _ensure_minimum_version(meta)

        if not args.dry_run:
            with path.open("w", encoding="utf-8") as fh:
                json.dump(snapshot, fh, indent=2, ensure_ascii=False)
                fh.write("\n")

        stats = BackfillStats(
            scanned=stats.scanned,
            updated=stats.updated + 1,
            skipped_existing=stats.skipped_existing,
            missing=stats.missing,
        )

    if missing_paths:
        msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
        if args.strict_missing:
            raise FileNotFoundError(msg)
        print(f"WARN: {msg}", file=sys.stderr)

    return stats


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill meta.btc_regime in snapshot history (missing BTC features => btc_regime=null)")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Do not modify files")
    parser.add_argument("--strict-missing", action="store_true", help="Fail if any snapshot is missing")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        stats = backfill(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(
        f"scanned={stats.scanned} updated={stats.updated} "
        f"skipped_existing={stats.skipped_existing} missing={stats.missing}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
