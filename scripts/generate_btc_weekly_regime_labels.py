from __future__ import annotations

import argparse
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from scanner.evaluation.history.parquet_store import load_symbol_timeframe

SCHEMA_VERSION = "regime_labels_btc_weekly_30d_return_vol_v1"
METHOD_ID = "btc_weekly_30d_return_vol_v1"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate frozen BTC weekly regime labels from local Pre-1 OHLCV history")
    parser.add_argument("--history-root", default="snapshots/history/ohlcv")
    parser.add_argument("--history-manifest", default="snapshots/history/manifests/history_manifest.json")
    parser.add_argument("--symbol-completeness", default="snapshots/history/manifests/symbol_completeness.json")
    parser.add_argument(
        "--output",
        default="snapshots/history/regime_labels/regime_labels_btc_weekly_30d_return_vol_v1.json",
    )
    return parser


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"Invalid JSON object at {path}")
    return payload


def _load_btc_daily(history_root: Path) -> pd.DataFrame:
    frame = load_symbol_timeframe(history_root, symbol="BTCUSDT", timeframe="1d")
    if frame.empty:
        raise ValueError("Missing BTCUSDT 1d history in Pre-1 dataset")
    frame = frame.copy()
    frame = frame[frame["is_closed"].eq(True)].copy()
    if frame.shape[0] < 31:
        raise ValueError("BTCUSDT 1d history must contain at least 31 usable closed bars")

    close = pd.to_numeric(frame["close"], errors="coerce")
    if close.isna().any() or not close.map(lambda v: math.isfinite(float(v))).all():
        raise ValueError("BTCUSDT 1d history contains non-finite close values")

    frame["close"] = close.astype(float)
    frame["open_time"] = pd.to_datetime(frame["open_time_utc"], utc=True)
    frame = frame.sort_values("open_time").reset_index(drop=True)
    frame["bar_date"] = frame["open_time"].dt.date
    frame["btc_30d_return_pct"] = (frame["close"] / frame["close"].shift(30) - 1.0) * 100.0

    log_returns = (frame["close"] / frame["close"].shift(1)).map(math.log)
    frame["btc_30d_realized_vol_annualized_pct"] = log_returns.rolling(window=30).std() * math.sqrt(365.0) * 100.0
    frame = frame.dropna(subset=["btc_30d_return_pct", "btc_30d_realized_vol_annualized_pct"]).copy()
    if frame.empty:
        raise ValueError("BTCUSDT 1d history does not have enough bars after 30-day lookback")
    return frame


def _label_regime(ret: float, vol: float) -> str:
    if ret < -15.0:
        return "Bear/Crash"
    if ret > 15.0 and vol < 60.0:
        return "Bull"
    return "Sideways"


def _derive_weekly_labels(frame: pd.DataFrame) -> list[dict[str, Any]]:
    iso = frame["open_time"].dt.isocalendar()
    tmp = frame.copy()
    tmp["iso_year"] = iso.year
    tmp["iso_week"] = iso.week

    by_week = tmp.groupby(["iso_year", "iso_week"], sort=True, as_index=False)
    rows: list[dict[str, Any]] = []
    for _, week in by_week:
        distinct_dates = set(week["bar_date"].tolist())
        if len(distinct_dates) != 7:
            continue

        week_start = week["bar_date"].min()
        week_end = week["bar_date"].max()
        expected_week_dates = pd.date_range(start=week_start, periods=7, freq="D").date
        expected_dates_set = set(expected_week_dates)
        if distinct_dates != expected_dates_set:
            continue

        week_end_dt = pd.Timestamp(week_end)
        if week_end_dt.dayofweek != 6:
            continue

        week_end_rows = week[week["bar_date"] == week_end]
        if week_end_rows.empty:
            continue
        week_end_row = week_end_rows.iloc[-1]
        rows.append(
            {
                "week_start_date": week_start.isoformat(),
                "week_end_date": week_end.isoformat(),
                "as_of_daily_bar_id": f"BTCUSDT:1d:{week_end_row['open_time_utc']}",
                "btc_30d_return_pct": float(week_end_row["btc_30d_return_pct"]),
                "btc_30d_realized_vol_annualized_pct": float(week_end_row["btc_30d_realized_vol_annualized_pct"]),
                "regime_label": _label_regime(
                    float(week_end_row["btc_30d_return_pct"]),
                    float(week_end_row["btc_30d_realized_vol_annualized_pct"]),
                ),
            }
        )

    return sorted(rows, key=lambda row: row["week_start_date"])


def generate_payload(
    *,
    history_root: Path,
    history_manifest_path: Path,
    symbol_completeness_path: Path,
) -> dict[str, Any]:
    history_manifest = _load_json(history_manifest_path)
    symbol_completeness = _load_json(symbol_completeness_path)
    frame = _load_btc_daily(history_root)
    labels = _derive_weekly_labels(frame)

    return {
        "schema_version": SCHEMA_VERSION,
        "status": "frozen",
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": {
            "history_root": str(history_root),
            "symbol": "BTCUSDT",
            "timeframe": "1d",
            "history_manifest": {
                "fetch_run_id": history_manifest.get("fetch_run_id"),
                "created_at_utc": history_manifest.get("created_at_utc"),
                "fetch_start_date": history_manifest.get("fetch_start_date"),
                "effective_fetch_end_date": history_manifest.get("effective_fetch_end_date"),
                "closed_bar_only": history_manifest.get("closed_bar_only"),
            },
            "symbol_completeness": {
                "fetch_run_id": symbol_completeness.get("fetch_run_id"),
                "created_at_utc": symbol_completeness.get("created_at_utc"),
            },
        },
        "method": {
            "method_id": METHOD_ID,
            "return_window_bars": 30,
            "vol_window_returns": 30,
            "vol_annualization_basis_days": 365,
            "rules": {
                "bear_crash": "btc_30d_return_pct < -15",
                "bull": "btc_30d_return_pct > 15 and btc_30d_realized_vol_annualized_pct < 60",
                "sideways": "all other complete weeks",
            },
        },
        "labels": labels,
    }


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = generate_payload(
        history_root=Path(args.history_root),
        history_manifest_path=Path(args.history_manifest),
        symbol_completeness_path=Path(args.symbol_completeness),
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote={output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
