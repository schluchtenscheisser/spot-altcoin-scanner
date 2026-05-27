from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

HORIZONS = [1, 3, 5, 10, 20]
FORWARD_RETURN_COLUMN_BY_HORIZON = {h: f"forward_close_return_{h}d" for h in HORIZONS}
REQUIRED_COLUMNS = [
    "included_in_primary_analysis",
    "included_in_signal_analysis",
    "historical_signal_bucket",
    "entry_pattern",
    "btc_regime_label",
    "quote_volume_bucket",
]
OPTIONAL_LIQUIDITY_COLUMNS = ["median_quote_volume_30d", "median_quote_volume_90d"]

CLASSIFICATION_SORT_ORDER = {"Tier A": 1, "Tier B": 2, "Exclude": 3, "Diagnostic": 4, "Unclassified": 5}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-events-parquet", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser.parse_args()


def _normalize_entry_pattern(series: pd.Series) -> pd.Series:
    out = series.astype("string")
    out = out.fillna("none").str.strip()
    out = out.mask(out == "", "none")
    return out


def _to_finite(series: pd.Series) -> pd.Series:
    n = pd.to_numeric(series, errors="coerce")
    return n[np.isfinite(n)]


def _metric_block(frame: pd.DataFrame) -> dict[str, Any]:
    result: dict[str, Any] = {"count": int(len(frame))}
    for h in HORIZONS:
        vals = _to_finite(frame[FORWARD_RETURN_COLUMN_BY_HORIZON[h]])
        denom = int(len(vals))
        result[f"forward_return_{h}d_non_null_count"] = denom
        result[f"forward_return_{h}d_mean_pct"] = None if denom == 0 else float(vals.mean())
        result[f"forward_return_{h}d_median_pct"] = None if denom == 0 else float(vals.median())
        result[f"forward_return_{h}d_win_rate_pct"] = None if denom == 0 else float(100.0 * (vals > 0).sum() / denom)

    for col in OPTIONAL_LIQUIDITY_COLUMNS:
        if col in frame.columns:
            vals = _to_finite(frame[col])
            result[col] = None if vals.empty else float(vals.median())
        else:
            result[col] = None
    return result


def _classify(row: dict[str, Any]) -> str:
    bucket = row["historical_signal_bucket"]
    entry = row["entry_pattern"]
    c = row["count"]
    med1 = row["forward_return_1d_median_pct"]
    med3 = row["forward_return_3d_median_pct"]
    med5 = row["forward_return_5d_median_pct"]
    wr1 = row["forward_return_1d_win_rate_pct"]
    wr3 = row["forward_return_3d_win_rate_pct"]

    if bucket in {"late_monitor", "watchlist", "discarded"}:
        return "Diagnostic"
    if bucket in {"early_candidates", "confirmed_candidates"} and entry != "none":
        if c >= 15 and med1 is not None and med1 > 0 and med3 is not None and med3 > 0 and wr1 is not None and wr1 >= 60 and wr3 is not None and wr3 >= 55 and med5 is not None and med5 > -2.0:
            return "Tier A"
        if c >= 10 and med1 is not None and med1 > 0 and ((med3 is not None and med3 >= 0) or (wr3 is not None and wr3 >= 55)):
            return "Tier B"
    if bucket in {"early_candidates", "confirmed_candidates"}:
        return "Exclude"
    return "Unclassified"


def _warnings(row: dict[str, Any]) -> dict[str, Any]:
    med5 = row["forward_return_5d_median_pct"]
    w5_weak = None if med5 is None else bool(med5 <= -2.0)
    w5_severe = None if med5 is None else bool(med5 <= -5.0)
    return {
        "low_sample": bool(row["count"] < 15),
        "sample_warning": bool(row["count"] < 20),
        "warning_5d_weak": w5_weak,
        "warning_5d_severe": w5_severe,
    }


def main() -> None:
    args = _parse_args()
    in_path = Path(args.input_events_parquet)
    out_dir = Path(args.output_dir)

    if not in_path.exists() or not in_path.is_file():
        raise ValueError(f"input parquet does not exist or is not a file: {in_path}")
    try:
        df = pd.read_parquet(in_path)
    except Exception as exc:
        raise ValueError(f"unable to read parquet: {in_path}") from exc

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    missing_h = [FORWARD_RETURN_COLUMN_BY_HORIZON[h] for h in HORIZONS if FORWARD_RETURN_COLUMN_BY_HORIZON[h] not in df.columns]
    if missing or missing_h:
        raise ValueError(f"schema error. missing={missing + missing_h}. available={list(df.columns)} expected_horizons={FORWARD_RETURN_COLUMN_BY_HORIZON}")

    df = df.copy()
    df["entry_pattern"] = _normalize_entry_pattern(df["entry_pattern"])

    actionable_base = df[(df["included_in_primary_analysis"] == True) & (df["included_in_signal_analysis"] == True) & (df["historical_signal_bucket"].isin(["early_candidates", "confirmed_candidates"]))]
    primary_actionable = actionable_base[actionable_base["entry_pattern"] != "none"]
    diagnostic_scope = df[(df["included_in_primary_analysis"] == True) & (df["included_in_signal_analysis"] == True) & (df["historical_signal_bucket"].isin(["late_monitor", "watchlist", "discarded"]))]
    analysis_df = pd.concat([actionable_base, diagnostic_scope], ignore_index=True)

    rows = []
    for (bucket, entry), sub in analysis_df.groupby(["historical_signal_bucket", "entry_pattern"], sort=True, dropna=False):
        row = {"historical_signal_bucket": str(bucket), "entry_pattern": str(entry), "segment_label": f"{bucket} × {entry}"}
        row.update(_metric_block(sub))
        row["classification"] = _classify(row)
        row["classification_sort_order"] = CLASSIFICATION_SORT_ORDER[row["classification"]]
        row.update(_warnings(row))
        rows.append(row)

    seg = pd.DataFrame(rows)
    if seg.empty:
        seg = pd.DataFrame(columns=["historical_signal_bucket", "entry_pattern", "segment_label", "classification", "classification_sort_order", "count"])

    seg = seg.sort_values([
        "classification_sort_order", "forward_return_3d_median_pct", "forward_return_1d_median_pct", "count", "historical_signal_bucket", "entry_pattern"
    ], ascending=[True, False, False, False, True, True], na_position="last", kind="mergesort")

    split_rows = []
    for _, srow in seg.iterrows():
        mask = (analysis_df["historical_signal_bucket"] == srow["historical_signal_bucket"]) & (analysis_df["entry_pattern"] == srow["entry_pattern"])
        base = analysis_df[mask]
        dims = [
            ("overall", [("ALL", "ALL", base)]),
            ("btc_regime", [((reg[0] if isinstance(reg, tuple) else reg), "ALL", sub) for reg, sub in base.groupby(["btc_regime_label"], sort=True, dropna=False)]),
            ("quote_volume_bucket", [("ALL", (qv[0] if isinstance(qv, tuple) else qv), sub) for qv, sub in base.groupby(["quote_volume_bucket"], sort=True, dropna=False)]),
            ("btc_regime_x_quote_volume_bucket", [(reg, qv, sub) for (reg, qv), sub in base.groupby(["btc_regime_label", "quote_volume_bucket"], sort=True, dropna=False)]),
        ]
        for split_type, groups in dims:
            for reg, qv, sub in groups:
                rec = {
                    "historical_signal_bucket": srow["historical_signal_bucket"], "entry_pattern": srow["entry_pattern"], "segment_label": srow["segment_label"],
                    "split_type": split_type, "btc_regime_label": reg, "quote_volume_bucket": qv, "overall_classification": srow["classification"],
                }
                rec.update(_metric_block(sub))
                rec.update(_warnings(rec))
                split_rows.append(rec)
    splits = pd.DataFrame(split_rows)

    out_dir.mkdir(parents=True, exist_ok=True)
    seg.to_csv(out_dir / "actionable_segments.csv", index=False)
    seg.to_parquet(out_dir / "actionable_segments.parquet", index=False)
    splits.to_csv(out_dir / "actionable_segment_splits.csv", index=False)
    splits.to_parquet(out_dir / "actionable_segment_splits.parquet", index=False)

    warnings: list[str] = []
    for col in OPTIONAL_LIQUIDITY_COLUMNS:
        if col not in df.columns:
            warnings.append(f"missing optional column: {col}; metric set to null")
    if (seg["classification"] == "Unclassified").any():
        warnings.append("Unclassified segments present")

    report = {
        "analysis_id": "BACKTEST-2_ACTIONABLE_SEGMENT_REPORT",
        "input_events_parquet": str(in_path),
        "output_dir": str(out_dir),
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "row_counts": {
            "input_rows": int(len(df)), "primary_actionable_rows": int(len(primary_actionable)), "actionable_candidate_rows": int(len(actionable_base)),
            "diagnostic_rows": int(len(diagnostic_scope)), "overall_segment_rows": int(len(seg)), "split_rows": int(len(splits)),
        },
        "thresholds": {
            "tier_a_min_count": 15, "tier_b_min_count": 10, "sample_warning_count_lt": 20, "low_sample_count_lt": 15,
            "tier_a_5d_median_floor_pct": -2.0, "warning_5d_weak_median_lte_pct": -2.0, "warning_5d_severe_median_lte_pct": -5.0,
        },
        "classification_counts": {k: int((seg["classification"] == k).sum()) for k in ["Tier A", "Tier B", "Exclude", "Diagnostic", "Unclassified"]},
        "warnings": warnings,
        "segments": seg.replace({np.nan: None}).to_dict(orient="records"),
    }
    (out_dir / "actionable_segment_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    def _section(df_sec: pd.DataFrame, label: str, empty_text: str) -> list[str]:
        lines = [f"## {label}"]
        if df_sec.empty:
            lines += ["", empty_text, ""]
            return lines
        cols = ["segment_label", "count", "forward_return_1d_median_pct", "forward_return_3d_median_pct", "forward_return_5d_median_pct"]
        lines += ["", "| segment | count | 1d med % | 3d med % | 5d med % |", "|---|---:|---:|---:|---:|"]
        for _, r in df_sec.iterrows():
            vals = [r[c] for c in cols]
            def fm(x):
                if isinstance(x, (int, np.integer)): return str(int(x))
                if isinstance(x, (float, np.floating)): return f"{x:.2f}"
                if x is None or (isinstance(x, float) and np.isnan(x)): return "n/a"
                return str(x)
            lines.append(f"| {fm(vals[0])} | {fm(vals[1])} | {fm(vals[2])} | {fm(vals[3])} | {fm(vals[4])} |")
        lines.append("")
        return lines

    md = [
        "# BACKTEST-2 Actionable Segment Report", "",
        f"- Generated at (UTC): {report['generated_at_utc']}", f"- Input parquet: `{in_path}`", f"- Output dir: `{out_dir}`", "",
        "## Method Boundary", "- Not trading P&L.", "- No execution simulation.", "- Forward returns are labels, not signal inputs.", "- Quote-volume is only a liquidity proxy.",
        "", "## Scope Definitions", "- Primary actionable: primary && signal && bucket in {confirmed, early} && entry_pattern != none", "- Candidate actionable: primary && signal && bucket in {confirmed, early}", "- Diagnostic: primary && signal && bucket in {late_monitor, watchlist, discarded}",
        "", "## Thresholds", "- Tier A min count: 15", "- Tier B min count: 10", "- Sample warning: count < 20", "- Low sample: count < 15", "",
    ]
    md += _section(seg[seg["classification"] == "Tier A"], "Tier A", "No Tier A segments found under the current thresholds.")
    md += _section(seg[seg["classification"] == "Tier B"], "Tier B", "No Tier B segments found under the current thresholds.")
    md += _section(seg[seg["classification"] == "Exclude"], "Exclude", "No Exclude segments found under the current thresholds.")
    md += _section(seg[seg["classification"] == "Diagnostic"], "Diagnostic", "No Diagnostic segments found under the current scope.")
    md += ["## Split Summaries", "- BTC regime annotation", "- quote-volume bucket annotation", "- combined BTC regime × quote-volume annotation", "", "## Warnings"]
    if warnings:
        md += [f"- {w}" for w in warnings]
    else:
        md += ["- none"]
    (out_dir / "actionable_segment_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
