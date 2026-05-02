#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

BUCKETS = ["confirmed_candidates", "early_candidates", "watchlist", "late_monitor"]
OUTCOMES = ["direct_ok", "tranche_ok", "marginal", "failed", "unknown_execution", "unexpected_execution_state", "not_attempted"]
TOP_SYMBOL_OUTCOMES = ["failed", "marginal", "unknown_execution", "direct_ok", "tranche_ok", "unexpected_execution_state"]
COUNT_KEYS = ["structural", "execution_attempted", "executable", "direct_ok", "tranche_ok", "marginal", "failed", "unknown_execution", "unexpected_execution_state", "not_attempted"]


def _counts() -> dict[str, int]:
    return {k: 0 for k in COUNT_KEYS}


def _with_rates(c: dict[str, int]) -> dict[str, Any]:
    d = dict(c)
    denom = c["structural"]
    for k in ["executable", "direct_ok", "tranche_ok", "marginal", "failed", "unknown_execution", "unexpected_execution_state", "not_attempted"]:
        d[f"{k}_rate"] = None if denom == 0 else c[k] / denom
    return d


def _require_count_block(block: dict[str, Any], where: str) -> dict[str, int]:
    out = {}
    for k in COUNT_KEYS:
        v = block.get(k)
        if type(v) is not int or v < 0:
            raise ValueError(f"Invalid count {k} in {where}")
        out[k] = v
    return out


def _check_output_path(path: Path) -> None:
    p = path.as_posix()
    for bad in ("reports/analysis", "reports/runs", "snapshots/runs"):
        if p == bad or p.startswith(f"{bad}/"):
            raise ValueError(f"Forbidden output path: {path}")


def _discover_reports(reports_root: Path) -> list[Path]:
    return sorted(reports_root.glob("**/report.json"))


def _segment_to_outcome(segment_name: str) -> str | None:
    for outcome in TOP_SYMBOL_OUTCOMES:
        if segment_name.endswith(f"_{outcome}"):
            return outcome
    return None


def _load_reports(report_paths: list[Path], explicit: bool) -> list[dict[str, Any]]:
    required = ["execution_aware_summary", "execution_counts_by_bucket", "execution_counts_by_universe_category", "execution_counts_by_bucket_and_category", "execution_aware_candidate_segments"]
    rows = []
    for p in report_paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        for k in required:
            if k not in data:
                raise ValueError(f"T25 requires T24 execution-aware report fields. Missing {k} in {p}.")
        if data.get("scan_mode") != "daily":
            if explicit:
                raise ValueError(f"Non-daily report passed via --run-dir: {p}")
            continue
        rows.append({"path": p, "data": data})
    return rows


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports-root", default="reports/runs")
    ap.add_argument("--run-dir", action="append", default=[])
    ap.add_argument("--output-json", default="reports/aux/execution_depth_analysis.json")
    ap.add_argument("--output-md", default="reports/aux/execution_depth_analysis.md")
    ap.add_argument("--max-runs", type=int)
    ap.add_argument("--top-n", type=int, default=20)
    args = ap.parse_args()
    if args.top_n < 1:
        raise ValueError("--top-n must be >= 1")
    if args.max_runs is not None and args.max_runs < 1:
        raise ValueError("--max-runs must be >= 1")

    out_json = Path(args.output_json)
    out_md = Path(args.output_md)
    _check_output_path(out_json)
    _check_output_path(out_md)

    explicit = bool(args.run_dir)
    report_paths = [Path(d) / "report.json" for d in args.run_dir] if explicit else _discover_reports(Path(args.reports_root))
    rows = _load_reports(report_paths, explicit=explicit)

    rows.sort(key=lambda r: (r["data"]["daily_bar_id"], r["data"]["as_of_utc"], r["data"]["run_id"]))
    if args.max_runs is not None:
        rows = list(reversed(rows))[: args.max_runs]
        rows.sort(key=lambda r: (r["data"]["daily_bar_id"], r["data"]["as_of_utc"], r["data"]["run_id"]))

    summary = _counts()
    by_run: dict[str, Any] = {}
    by_bucket = {b: _counts() for b in BUCKETS}
    by_cat: dict[str, dict[str, int]] = defaultdict(_counts)
    by_bucket_cat: dict[str, dict[str, dict[str, int]]] = {b: defaultdict(_counts) for b in BUCKETS}
    reason_counts: dict[str, int] = defaultdict(int)
    reason_by_bucket: dict[str, dict[str, int]] = {b: defaultdict(int) for b in BUCKETS}
    reason_by_cat: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    symbol_runs = {o: defaultdict(list) for o in TOP_SYMBOL_OUTCOMES}

    for row in rows:
        d = row["data"]
        rid = d["run_id"]
        rcounts = _require_count_block(d["execution_aware_summary"], f"{row['path']}::execution_aware_summary")
        for k in COUNT_KEYS:
            summary[k] += rcounts[k]
        by_run[rid] = {
            "daily_bar_id": d["daily_bar_id"], "as_of_utc": d["as_of_utc"], "report_path": row["path"].as_posix(), **_with_rates(rcounts)
        }
        for b in BUCKETS:
            bc = _require_count_block(d["execution_counts_by_bucket"][b], f"{row['path']}::{b}")
            for k in COUNT_KEYS:
                by_bucket[b][k] += bc[k]

            for cat, vals in d["execution_counts_by_bucket_and_category"].get(b, {}).items():
                cc = _require_count_block(vals, f"{row['path']}::{b}::{cat}")
                for k in COUNT_KEYS:
                    by_bucket_cat[b][cat][k] += cc[k]
        for cat, vals in d["execution_counts_by_universe_category"].items():
            cc = _require_count_block(vals, f"{row['path']}::{cat}")
            for k in COUNT_KEYS:
                by_cat[cat][k] += cc[k]

        for seg, items in d["execution_aware_candidate_segments"].items():
            outcome = _segment_to_outcome(seg)
            if not outcome:
                continue
            for it in items:
                reason = it.get("execution_reason_raw")
                rk = "__null__" if reason is None else str(reason)
                reason_counts[rk] += 1
                bucket = it.get("bucket")
                if bucket in BUCKETS:
                    reason_by_bucket[bucket][rk] += 1
                cat = it.get("universe_category")
                if cat is not None:
                    reason_by_cat[str(cat)][rk] += 1
                symbol = it.get("symbol")
                if symbol:
                    symbol_runs[outcome][symbol].append({"run_id": rid, "daily_bar_id": d["daily_bar_id"], "bucket": bucket, "universe_category": cat, "execution_reason_raw": reason})

    over = {"confirmed_structural_vs_executable": [], "early_structural_vs_executable": []}
    sorted_runs = sorted(rows, key=lambda r: (r["data"]["daily_bar_id"], r["data"]["as_of_utc"], r["data"]["run_id"]))
    for r in sorted_runs:
        d = r["data"]
        for bucket, key in (("confirmed_candidates", "confirmed_structural_vs_executable"), ("early_candidates", "early_structural_vs_executable")):
            c = _require_count_block(d["execution_counts_by_bucket"][bucket], "over_time")
            over[key].append({"run_id": d["run_id"], "daily_bar_id": d["daily_bar_id"], "as_of_utc": d["as_of_utc"], **c, "executable_rate": None if c["structural"] == 0 else c["executable"] / c["structural"]})

    top = {}
    for outcome in TOP_SYMBOL_OUTCOMES:
        entries = []
        for symbol, runs in symbol_runs[outcome].items():
            distinct = sorted({r["run_id"] for r in runs})
            entries.append({"symbol": symbol, "run_count": len(distinct), "runs": sorted(runs, key=lambda x: (x["daily_bar_id"], x["run_id"], str(x.get("bucket") or "")))})
        entries.sort(key=lambda x: (-x["run_count"], x["symbol"]))
        top[outcome] = entries[: args.top_n]

    result = {
        "schema_version": "t25_execution_depth_analysis_v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input": {
            "reports_root": args.reports_root,
            "run_count": len(rows),
            "run_ids": [r["data"]["run_id"] for r in sorted_runs],
            "report_paths": [r["path"].as_posix() for r in sorted_runs],
            "top_n": args.top_n,
            "max_runs": args.max_runs,
        },
        "summary": {f"total_{k}": v for k, v in summary.items()} | {f"overall_{k}_rate": (None if summary['structural']==0 else summary[k]/summary['structural']) for k in ["executable","direct_ok","tranche_ok","marginal","failed","unknown_execution","unexpected_execution_state","not_attempted"]},
        "by_run": {k: _with_rates({ck: by_run[k][ck] for ck in COUNT_KEYS}) | {"daily_bar_id": by_run[k]["daily_bar_id"], "as_of_utc": by_run[k]["as_of_utc"], "report_path": by_run[k]["report_path"]} for k in sorted(by_run, key=lambda x:(by_run[x]["daily_bar_id"],by_run[x]["as_of_utc"],x))},
        "by_bucket": {b: _with_rates(by_bucket[b]) for b in BUCKETS},
        "by_universe_category": {k: _with_rates(by_cat[k]) for k in sorted(by_cat)},
        "by_bucket_and_category": {b: {k: _with_rates(v) for k, v in sorted(by_bucket_cat[b].items())} for b in BUCKETS},
        "execution_reason_counts": {k: reason_counts[k] for k in sorted(reason_counts)},
        "execution_reason_counts_by_bucket": {b: {k: reason_by_bucket[b][k] for k in sorted(reason_by_bucket[b])} for b in BUCKETS},
        "execution_reason_counts_by_universe_category": {c: {k: reason_by_cat[c][k] for k in sorted(reason_by_cat[c])} for c in sorted(reason_by_cat)},
        "over_time": over,
        "top_repeated_symbols": top,
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(result, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    out_md.write_text(f"# T25 Execution Depth Analysis\n\nAnalyzed runs: {len(rows)}\n", encoding="utf-8")


if __name__ == "__main__":
    main()
