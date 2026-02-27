from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from scanner.backtest.e2_model import (
    DEFAULT_T_HOLD,
    DEFAULT_T_TRIGGER_MAX,
    DEFAULT_THRESHOLDS_PCT,
    evaluate_e2_candidate,
)
from scanner.config import load_config
from scanner.pipeline.global_ranking import compute_global_top20

DATASET_SCHEMA_VERSION = "1.0"


def _parse_date(value: str) -> date:
    return date.fromisoformat(value)


def _daterange(start: date, end: date) -> Iterable[date]:
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _run_id_from_asof(asof_iso: str) -> str:
    dt = datetime.strptime(asof_iso, "%Y-%m-%dT%H:%M:%SZ")
    return dt.strftime("%Y-%m-%d_%H%MZ")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _score_from_entry(entry: dict[str, Any]) -> float:
    score = entry.get("score")
    if score is None:
        raise ValueError("Missing non-nullable scoring_entry.score")
    return float(score)


def _load_snapshot(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid snapshot structure: {path}")
    return payload


def _build_price_series_by_symbol(snapshots: list[dict[str, Any]]) -> dict[str, dict[str, dict[str, Any]]]:
    result: dict[str, dict[str, dict[str, Any]]] = {}
    for snapshot in snapshots:
        meta = snapshot.get("meta", {})
        t_date = meta.get("date")
        if not t_date:
            continue
        features = snapshot.get("data", {}).get("features", {})
        if not isinstance(features, dict):
            continue
        for symbol, feature in features.items():
            one_day = feature.get("1d") if isinstance(feature, dict) else None
            candle = {
                "close": one_day.get("close") if isinstance(one_day, dict) else None,
                "high": one_day.get("high") if isinstance(one_day, dict) else None,
                "low": one_day.get("low") if isinstance(one_day, dict) else None,
            }
            result.setdefault(symbol, {})[t_date] = candle
    return result


def export_dataset(args: argparse.Namespace) -> Path:
    start = _parse_date(args.from_date)
    end = _parse_date(args.to_date)
    if end < start:
        raise ValueError("--to must be >= --from")

    config = load_config(args.config)
    config_root = config.raw
    backtest_cfg = config_root.get("backtest", {})

    t_hold = int(args.t_hold if args.t_hold is not None else backtest_cfg.get("t_hold", DEFAULT_T_HOLD))
    t_trigger_max = int(
        args.t_trigger_max
        if args.t_trigger_max is not None
        else backtest_cfg.get("t_trigger_max", DEFAULT_T_TRIGGER_MAX)
    )
    thresholds_pct = [float(x) for x in (args.thresholds_pct or backtest_cfg.get("thresholds_pct", list(DEFAULT_THRESHOLDS_PCT)))]
    thresholds_pct = sorted(set(thresholds_pct + [10.0, 20.0]))

    snapshots_dir = Path(args.snapshots_dir or config_root.get("snapshots", {}).get("history_dir", "snapshots/history"))
    output_dir = Path(args.output_dir)

    snapshots: list[dict[str, Any]] = []
    missing_paths: list[Path] = []
    for day in _daterange(start, end):
        path = snapshots_dir / f"{day.isoformat()}.json"
        if not path.exists():
            missing_paths.append(path)
            continue
        snapshots.append(_load_snapshot(path))

    if missing_paths:
        msg = f"Missing {len(missing_paths)} snapshot file(s): " + ", ".join(str(p) for p in missing_paths)
        if args.strict_missing:
            raise FileNotFoundError(msg)
        print(f"WARN: {msg}", file=sys.stderr)

    if not snapshots:
        raise ValueError("No snapshots loaded for requested range")

    run_id = args.run_id
    if not run_id:
        run_id = _run_id_from_asof(snapshots[-1].get("meta", {}).get("asof_iso"))

    price_series_by_symbol = _build_price_series_by_symbol(snapshots)

    rows: list[dict[str, Any]] = []
    setup_map = (("reversal", "reversals"), ("breakout", "breakouts"), ("pullback", "pullbacks"))

    for snapshot in snapshots:
        meta = snapshot.get("meta", {})
        scoring = snapshot.get("scoring", {})
        features = snapshot.get("data", {}).get("features", {})

        t0_date = meta.get("date")
        if not t0_date:
            raise ValueError("Missing non-nullable snapshot.meta.date")

        global_top20 = compute_global_top20(
            list(scoring.get("reversals", []) or []),
            list(scoring.get("breakouts", []) or []),
            list(scoring.get("pullbacks", []) or []),
            config,
        )
        global_rank_by_symbol = {entry.get("symbol"): idx for idx, entry in enumerate(global_top20, start=1)}

        for setup_type, key in setup_map:
            entries = list(scoring.get(key, []) or [])
            for idx, entry in enumerate(entries, start=1):
                symbol = entry.get("symbol")
                if not symbol:
                    raise ValueError("Missing non-nullable scoring_entry.symbol")

                setup_id = entry.get("setup_id") or setup_type
                feat = features.get(symbol, {}) if isinstance(features, dict) else {}

                e2 = evaluate_e2_candidate(
                    t0_date=t0_date,
                    setup_type=setup_type,
                    trade_levels=entry.get("trade_levels", {}) if isinstance(entry, dict) else {},
                    price_series=price_series_by_symbol.get(symbol, {}),
                    params={
                        "T_hold": t_hold,
                        "T_trigger_max": t_trigger_max,
                        "thresholds_pct": thresholds_pct,
                    },
                )

                row = {
                    "type": "candidate_setup",
                    "record_id": f"{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}",
                    "run_id": run_id,
                    "t0_date": t0_date,
                    "symbol": symbol,
                    "setup_type": setup_type,
                    "setup_id": setup_id,
                    "snapshot_version": meta.get("version"),
                    "asof_ts_ms": meta.get("asof_ts_ms"),
                    "asof_iso": meta.get("asof_iso"),
                    "market_cap_usd": feat.get("market_cap") if isinstance(feat, dict) else None,
                    "quote_volume_24h_usd": feat.get("quote_volume_24h") if isinstance(feat, dict) else None,
                    "liquidity_grade": feat.get("liquidity_grade") if isinstance(feat, dict) else None,
                    "btc_regime": meta.get("btc_regime"),
                    "score": _score_from_entry(entry),
                    "setup_rank": idx,
                    "global_rank": global_rank_by_symbol.get(symbol),
                    "reason": e2.get("reason"),
                    "t_trigger_date": e2.get("t_trigger_date"),
                    "t_trigger_day_offset": e2.get("t_trigger_day_offset"),
                    "entry_price": e2.get("entry_price"),
                    "hit_10": bool(e2.get("hit_10")),
                    "hit_20": bool(e2.get("hit_20")),
                    "hits": {k: bool(v) for k, v in (e2.get("hits") or {}).items()},
                    "mfe_pct": e2.get("mfe_pct"),
                    "mae_pct": e2.get("mae_pct"),
                }

                required_non_nullable = [
                    "snapshot_version",
                    "asof_ts_ms",
                    "asof_iso",
                    "score",
                    "reason",
                    "hit_10",
                    "hit_20",
                    "hits",
                ]
                for required in required_non_nullable:
                    if row.get(required) is None:
                        raise ValueError(f"Missing non-nullable field: {required}")

                rows.append(row)

    rows.sort(key=lambda row: (row["t0_date"], row["setup_type"], row["setup_rank"], row["symbol"]))

    meta_record = {
        "type": "meta",
        "run_id": run_id,
        "from_date": start.isoformat(),
        "to_date": end.isoformat(),
        "exported_at_iso": _utc_now_iso(),
        "source_snapshot_count": len(snapshots),
        "thresholds_pct": thresholds_pct,
        "T_hold": t_hold,
        "T_trigger_max": t_trigger_max,
        "dataset_schema_version": DATASET_SCHEMA_VERSION,
        "notes": None,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"eval_{run_id}.jsonl"

    with output_path.open("w", encoding="utf-8") as fh:
        fh.write(json.dumps(meta_record, ensure_ascii=False, separators=(",", ":")) + "\n")
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")

    return output_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export E2 evaluation dataset JSONL from snapshot history")
    parser.add_argument("--from", dest="from_date", required=True, help="Start date YYYY-MM-DD")
    parser.add_argument("--to", dest="to_date", required=True, help="End date YYYY-MM-DD")
    parser.add_argument("--run-id", dest="run_id", default=None, help="Optional run_id override")
    parser.add_argument("--strict-missing", action="store_true", help="Fail on missing snapshot files")
    parser.add_argument("--config", default="config/config.yml", help="Path to scanner config")
    parser.add_argument("--snapshots-dir", default=None, help="Override snapshots history directory")
    parser.add_argument("--output-dir", default="datasets/eval", help="Output directory")
    parser.add_argument("--thresholds-pct", nargs="*", type=float, default=None, help="Optional threshold list")
    parser.add_argument("--t-hold", type=int, default=None)
    parser.add_argument("--t-trigger-max", type=int, default=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        out_path = export_dataset(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(str(out_path))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
