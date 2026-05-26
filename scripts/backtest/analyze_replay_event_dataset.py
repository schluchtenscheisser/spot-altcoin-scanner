from __future__ import annotations

import argparse
import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REQUIRED_IDENTITY_COLUMNS = ["scenario_id", "replay_id", "symbol", "as_of_daily_bar_id"]
REQUIRED_FLAG_COLUMNS = ["included_in_primary_analysis", "included_in_signal_analysis"]
REQUIRED_GROUPING_FIELDS = [
    "historical_signal_bucket",
    "analysis_event_type",
    "event_type",
    "entry_pattern",
    "market_phase",
    "quote_volume_bucket",
    "btc_regime_label",
]

SINGLE_GROUPS = REQUIRED_GROUPING_FIELDS.copy()
DOUBLE_GROUPS: list[tuple[str, str]] = [
    ("historical_signal_bucket", "entry_pattern"),
    ("historical_signal_bucket", "analysis_event_type"),
    ("market_phase", "entry_pattern"),
    ("btc_regime_label", "historical_signal_bucket"),
    ("quote_volume_bucket", "historical_signal_bucket"),
    ("quote_volume_bucket", "entry_pattern"),
]


def _parse_horizons(raw: str) -> list[int]:
    vals = [int(x.strip()) for x in raw.split(",") if x.strip()]
    if not vals or any(v <= 0 for v in vals) or len(set(vals)) != len(vals):
        raise ValueError("--horizons must be unique positive integers")
    return vals


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--min-count", type=int, default=10)
    parser.add_argument("--horizons", default="1,3,5,10,20")
    parser.add_argument("--analysis-scope", choices=["primary_signal", "primary_raw", "full_signal", "full_raw"], default="primary_signal")
    parser.add_argument("--sort-horizon", type=int, default=3)
    parser.add_argument("--include-appendix", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--output-dir")
    return parser.parse_args()


def _validate(df: pd.DataFrame, dataset: Path, horizons: list[int], min_count: int, sort_horizon: int) -> None:
    if not dataset.exists():
        raise ValueError("dataset does not exist")
    if df.empty:
        raise ValueError("dataset is empty")
    missing = [c for c in REQUIRED_IDENTITY_COLUMNS + REQUIRED_FLAG_COLUMNS + REQUIRED_GROUPING_FIELDS if c not in df.columns]
    if missing:
        raise ValueError(f"missing required columns: {missing}")
    for h in horizons:
        for col in (f"forward_close_return_{h}d", f"has_forward_{h}d"):
            if col not in df.columns:
                raise ValueError(f"missing required horizon column: {col}")
    if min_count <= 0:
        raise ValueError("--min-count must be > 0")
    if sort_horizon not in horizons:
        raise ValueError("--sort-horizon must be included in --horizons")


def _select_scope(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    if scope == "primary_signal":
        return df[(df["included_in_primary_analysis"] == True) & (df["included_in_signal_analysis"] == True)].copy()
    if scope == "primary_raw":
        return df[df["included_in_primary_analysis"] == True].copy()
    if scope == "full_signal":
        return df[df["included_in_signal_analysis"] == True].copy()
    return df.copy()


def _metrics_for_series(series: pd.Series) -> dict[str, float | int | None]:
    if series.empty:
        return {"mean": None, "median": None, "win_rate": None, "positive": None, "negative": None, "flat": None, "min": None, "max": None, "p25": None, "p75": None}
    pos = int((series > 0).sum())
    neg = int((series < 0).sum())
    flat = int((series == 0).sum())
    return {
        "mean": float(series.mean()), "median": float(series.median()), "win_rate": float(pos / len(series)), "positive": pos,
        "negative": neg, "flat": flat, "min": float(series.min()), "max": float(series.max()), "p25": float(series.quantile(0.25)), "p75": float(series.quantile(0.75))
    }


def _build_segment_row(frame: pd.DataFrame, scope: str, group: str, k1: Any, k2: Any, horizons: list[int], min_count: int, sort_horizon: int) -> dict[str, Any]:
    count = int(len(frame))
    row = {
        "scope": scope, "segment_group": group,
        "segment_key": "ALL" if group == "ALL" else (str(k1) if k2 is None else f"{k1} | {k2}"),
        "segment_key_1": "ALL" if group == "ALL" else k1,
        "segment_key_2": None if group in SINGLE_GROUPS or group == "ALL" else k2,
        "count": count,
        "distinct_symbols": int(frame["symbol"].nunique(dropna=True)),
        "distinct_days": int(frame["as_of_daily_bar_id"].nunique(dropna=True)),
    }
    for h in horizons:
        ret_col = f"forward_close_return_{h}d"
        has_col = f"has_forward_{h}d"
        vals = pd.to_numeric(frame.loc[frame[has_col] == True, ret_col], errors="coerce")
        vals = vals[np.isfinite(vals)]
        avail = int(len(vals))
        row[f"available_count_{h}d"] = avail
        row[f"missing_count_{h}d"] = int(count - avail)
        m = _metrics_for_series(vals)
        row[f"mean_return_{h}d"] = m["mean"]
        row[f"median_return_{h}d"] = m["median"]
        row[f"win_rate_{h}d"] = m["win_rate"]
        row[f"positive_count_{h}d"] = m["positive"]
        row[f"negative_count_{h}d"] = m["negative"]
        row[f"flat_count_{h}d"] = m["flat"]
        row[f"min_return_{h}d"] = m["min"]
        row[f"max_return_{h}d"] = m["max"]
        row[f"p25_return_{h}d"] = m["p25"]
        row[f"p75_return_{h}d"] = m["p75"]
    row["passes_min_count"] = bool(count >= min_count)
    row["sort_metric"] = row.get(f"mean_return_{sort_horizon}d")
    row["sort_horizon"] = sort_horizon
    return row


def analyze(df: pd.DataFrame, scope: str, horizons: list[int], min_count: int, sort_horizon: int) -> pd.DataFrame:
    scoped = _select_scope(df, scope)
    rows: list[dict[str, Any]] = []
    rows.append(_build_segment_row(scoped, scope, "ALL", "ALL", None, horizons, min_count, sort_horizon))
    for col in SINGLE_GROUPS:
        for key, sub in scoped.groupby(col, dropna=False, sort=True):
            rows.append(_build_segment_row(sub, scope, col, key, None, horizons, min_count, sort_horizon))
    for c1, c2 in DOUBLE_GROUPS:
        group_name = f"{c1}__x__{c2}"
        for (k1, k2), sub in scoped.groupby([c1, c2], dropna=False, sort=True):
            rows.append(_build_segment_row(sub, scope, group_name, k1, k2, horizons, min_count, sort_horizon))
    out = pd.DataFrame(rows)
    out = out.sort_values(["scope", "segment_group", "passes_min_count", "sort_metric", "count", "segment_key"], ascending=[True, True, False, False, False, True], na_position="last", kind="mergesort")
    return out


def main() -> None:
    args = _parse_args()
    dataset_path = Path(args.dataset)
    horizons = _parse_horizons(args.horizons)
    df = pd.read_parquet(dataset_path) if dataset_path.exists() else pd.DataFrame()
    _validate(df, dataset_path, horizons, args.min_count, args.sort_horizon)

    scenario_id = str(df.iloc[0]["scenario_id"])
    replay_id = str(df.iloc[0]["replay_id"])
    out_dir = Path(args.output_dir) if args.output_dir else Path(args.output_root) / scenario_id / replay_id
    out_dir.mkdir(parents=True, exist_ok=True)

    segment_df = analyze(df, args.analysis_scope, horizons, args.min_count, args.sort_horizon)
    segment_df.to_parquet(out_dir / "segment_returns.parquet", index=False)
    segment_df.to_csv(out_dir / "segment_returns.csv", index=False)

    lines = [
        "# Backtest-1 Segment Summary",
        "",
        f"- Scope: `{args.analysis_scope}` (default `primary_signal`)",
        "- Forward returns are labels, not signal inputs.",
        "- MarketCap is unavailable point-in-time and not used.",
        "- Quote-volume buckets are OHLCV-derived proxies, not execution/liquidity guarantees.",
        "- No orderbook, MEXC depth, slippage, or execution filters are applied in this backtest.",
        "- This is descriptive segment analysis, not a trading-strategy P&L simulation.",
    ]
    (out_dir / "backtest_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    selected_count = int(len(_select_scope(df, args.analysis_scope)))
    summary = {
        "scenario_id": scenario_id, "replay_id": replay_id, "dataset_path": str(dataset_path),
        "created_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"), "analysis_scope": args.analysis_scope,
        "min_count": args.min_count, "horizons": horizons, "sort_horizon": args.sort_horizon,
        "input_row_count": int(len(df)), "selected_row_count": selected_count,
        "raw_event_count": int(len(df)),
        "signal_analysis_event_count": int((df["included_in_signal_analysis"] == True).sum()),
        "primary_analysis_event_count": int((df["included_in_primary_analysis"] == True).sum()),
        "primary_signal_analysis_event_count": int(((df["included_in_primary_analysis"] == True) & (df["included_in_signal_analysis"] == True)).sum()),
        "segment_row_count": int(len(segment_df)),
        "segment_row_count_passing_min_count": int((segment_df["passes_min_count"] == True).sum()),
        "top_segments_by_mean_return": {
            f"{h}d": (
                segment_df.assign(**{f"_m_{h}": pd.to_numeric(segment_df[f"mean_return_{h}d"], errors="coerce")})
                .sort_values([f"_m_{h}", "count"], ascending=[False, False], na_position="last")
                .head(5)[["segment_group", "segment_key", f"mean_return_{h}d"]]
                .to_dict(orient="records")
            )
            for h in horizons
        },
        "scope_definitions": {
            "primary_signal": "included_in_primary_analysis == true AND included_in_signal_analysis == true",
            "primary_raw": "included_in_primary_analysis == true",
            "full_signal": "included_in_signal_analysis == true",
            "full_raw": "no filter",
        },
        "warnings": [], "validation_status": "passed", "validation_errors": [],
    }
    (out_dir / "backtest_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
