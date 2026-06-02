#!/usr/bin/env python3
"""T30-v2 offline segment-selection evidence report.

Consumes persisted Shadow-Live diagnostics (or manually uploaded ZIP artifacts).
It deliberately does not call live APIs and does not select a trading basket.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any, Callable, Iterable
import zipfile

import pandas as pd

# T30-v2 config — all thresholds are preliminary placeholders.
# Override after reviewing priority_score_distributions in output.
PRIORITY_THRESHOLD_A = 65
PRIORITY_THRESHOLD_B = 60
PRIORITY_THRESHOLD_C = 55
MINIMUM_RUN_COUNT = 20
FETCH_COMMAND = "python scripts/fetch_ohlcv_history_for_evaluation.py --project-root ."
HORIZONS = (1, 3, 7)
TRADEABLE = {"full", "reduced_75", "reduced_50", "reduced_25"}


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def validate_thresholds(values: dict[str, Any]) -> dict[str, float]:
    for name, value in values.items():
        if not finite(value) or not 0 <= float(value) <= 100:
            raise ValueError(f"{name} must be a finite numeric value in [0, 100]")
    return {name: float(value) for name, value in values.items()}


def pct(values: Iterable[Any], quantile: float) -> float | None:
    nums = sorted(float(v) for v in values if finite(v))
    if not nums:
        return None
    if len(nums) == 1:
        return nums[0]
    rank = (len(nums) - 1) * quantile
    lo, hi = math.floor(rank), math.ceil(rank)
    return nums[lo] if lo == hi else nums[lo] + (nums[hi] - nums[lo]) * (rank - lo)


def block(record: dict[str, Any], name: str) -> dict[str, Any]:
    value = record.get(name)
    return value if isinstance(value, dict) else {}


def nested(record: dict[str, Any], first: str, *fallbacks: tuple[str, str] | str) -> Any:
    parent, key = first.split(".", 1)
    if key in block(record, parent):
        return block(record, parent)[key]
    for fallback in fallbacks:
        if isinstance(fallback, tuple):
            p, k = fallback
            if k in block(record, p):
                return block(record, p)[k]
        elif fallback in record:
            return record[fallback]
    return None


def extract_record(record: dict[str, Any], run_id: str) -> dict[str, Any]:
    entry = block(record, "entry_location")
    return {
        **record,
        "run_id": run_id,
        "decision_bucket": nested(record, "decision.decision_bucket", "decision_bucket"),
        "priority_score": nested(record, "decision.priority_score", "priority_score"),
        "entry_pattern": nested(record, "decision.entry_pattern", ("pattern", "entry_pattern"), "entry_pattern"),
        "entry_pattern_score": nested(record, "decision.entry_pattern_score", ("pattern", "entry_pattern_score"), "entry_pattern_score"),
        "market_phase": nested(record, "phase.market_phase", "market_phase"),
        "market_phase_confidence": nested(record, "phase.market_phase_confidence", "market_phase_confidence"),
        "state_machine_state": nested(record, "state.state_machine_state", "state_machine_state"),
        "state_confidence": nested(record, "state.state_confidence", "state_confidence"),
        # Intentionally ignore same-named root keys: ir1.5 entry-location data is nested.
        "entry_location_status": entry.get("entry_location_status", "not_evaluable"),
        "entry_action_hint": entry.get("entry_action_hint", "not_evaluable"),
    }


def schema_version(value: Any) -> tuple[int, int] | None:
    if not isinstance(value, str) or not value.startswith("ir"):
        return None
    pieces = value[2:].split(".")
    if len(pieces) != 2 or not all(piece.isdigit() for piece in pieces):
        return None
    return int(pieces[0]), int(pieces[1])


def classify_run(records: list[dict[str, Any]]) -> tuple[bool, str, list[str]]:
    warnings: list[str] = []
    raw_versions = [r.get("schema_version") for r in records if r.get("schema_version") is not None]
    versions = [v for value in raw_versions if (v := schema_version(value)) is not None]
    if raw_versions and not versions:
        warnings.append("unparseable_schema_version")
    if versions:
        highest = max(versions)
        if highest < (1, 5):
            return False, "schema_pre_ir1.5", warnings
        if highest > (1, 5):
            required = ("is_operational_trade_candidate", "execution_size_class", "execution_status_raw", "entry_location")
            if any(not any(field in r and r.get(field) is not None for r in records) for field in required):
                return False, "missing_required_fields", warnings
        return True, "schema_ir1.5_plus", warnings
    if any(r.get("is_operational_trade_candidate") is not None for r in records):
        return True, "operational_field_fallback", warnings
    return False, "schema_not_ir1.5_plus", warnings


def _read_gzip(raw: bytes) -> list[dict[str, Any]]:
    return [json.loads(line) for line in gzip.decompress(raw).decode("utf-8").splitlines() if line.strip()]


def _safe_member(name: str) -> bool:
    p = PurePosixPath(name)
    return bool(name) and not p.is_absolute() and ".." not in p.parts


def discover_runs(project_root: Path, input_zip_dir: Path | None) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if input_zip_dir is None:
        for diag in sorted((project_root / "reports/runs").glob("**/symbol_diagnostics.jsonl.gz")):
            report = diag.with_name("report.json")
            runs.append({"run_id": diag.parent.name, "source": diag.as_posix(), "records": _read_gzip(diag.read_bytes()), "report": json.loads(report.read_text()) if report.exists() else None})
        return runs
    zip_root = input_zip_dir if input_zip_dir.is_absolute() else project_root / input_zip_dir
    for archive in sorted(zip_root.glob("*.zip")):
        with zipfile.ZipFile(archive) as zf:
            names = [n for n in zf.namelist() if _safe_member(n)]
            diagnostics = [n for n in names if n.endswith("/symbol_diagnostics.jsonl.gz") or n == "symbol_diagnostics.jsonl.gz"]
            for diag_name in diagnostics:
                parent = str(PurePosixPath(diag_name).parent)
                report_name = f"{parent}/report.json" if parent != "." else "report.json"
                report = json.loads(zf.read(report_name)) if report_name in names else None
                run_id = PurePosixPath(parent).name if parent != "." else archive.stem
                runs.append({"run_id": run_id, "source": f"{archive.as_posix()}!{diag_name}", "records": _read_gzip(zf.read(diag_name)), "report": report})
    return runs


def baseline(r: dict[str, Any]) -> bool:
    return r.get("is_operational_trade_candidate") is True and r.get("candidate_excluded") is not True and r.get("execution_size_class") in TRADEABLE


def segments() -> dict[str, Callable[[dict[str, Any]], bool]]:
    def match(bucket: str, raw: set[str] | None = None, sizes: set[str] | None = None, hint: str | None = None):
        return lambda r: baseline(r) and r.get("decision_bucket") == bucket and (raw is None or r.get("execution_status_raw") in raw) and (sizes is None or r.get("execution_size_class") in sizes) and (hint is None or r.get("entry_action_hint") == hint)
    return {
        "S1": match("confirmed_candidates", {"direct_ok"}, {"full"}, "buy_now_candidate"),
        "S2": match("confirmed_candidates", {"direct_ok"}, {"full"}, "acceptable_if_strategy_allows"),
        "S3": match("confirmed_candidates", {"marginal"}, {"reduced_75"}, "acceptable_if_strategy_allows"),
        "S4": match("confirmed_candidates", {"marginal"}, {"reduced_50"}, "acceptable_if_strategy_allows"),
        "S5": match("confirmed_candidates", {"marginal"}, {"reduced_25"}, "acceptable_if_strategy_allows"),
        "S6": match("early_candidates", {"direct_ok", "marginal"}, {"full", "reduced_75"}, "acceptable_if_strategy_allows"),
        "S7": match("confirmed_candidates", {"marginal"}, {"full"}, "acceptable_if_strategy_allows"),
        "S8": match("confirmed_candidates"), "S9": match("early_candidates"),
    }


def basket_filters(thresholds: dict[str, float]) -> dict[str, Callable[[dict[str, Any]], bool]]:
    hints = {"buy_now_candidate", "acceptable_if_strategy_allows"}
    def score(r: dict[str, Any], floor: float) -> bool: return finite(r.get("priority_score")) and float(r["priority_score"]) >= floor
    def common(r: dict[str, Any]) -> bool: return r.get("is_operational_trade_candidate") is True and r.get("candidate_excluded") is not True and r.get("entry_action_hint") in hints
    return {
        "A": lambda r: common(r) and r.get("decision_bucket") == "confirmed_candidates" and r.get("execution_size_class") == "full" and r.get("entry_location_status") in {"fresh_entry", "acceptable_entry"} and score(r, thresholds["A"]),
        "B": lambda r: common(r) and r.get("decision_bucket") == "confirmed_candidates" and r.get("execution_size_class") in {"full", "reduced_75", "reduced_50"} and r.get("entry_location_status") in {"fresh_entry", "acceptable_entry"} and score(r, thresholds["B"]),
        "C": lambda r: common(r) and r.get("decision_bucket") in {"confirmed_candidates", "early_candidates"} and r.get("execution_size_class") in TRADEABLE and r.get("entry_location_status") in {"fresh_entry", "acceptable_entry", "extended_entry"} and score(r, thresholds["C"]),
    }


def apply_slippage(raw: Any, bps: Any) -> tuple[float | None, bool]:
    if not finite(raw): return None, finite(bps)
    if not finite(bps): return float(raw), False
    return float(raw) - float(bps) / 100.0, True


def attach_forward_returns(project_root: Path, records: list[dict[str, Any]]) -> set[str]:
    """Attach metrics from T18/T30 event export; never reconstruct readiness events."""
    path = project_root / "evaluation/exports/signal_event_metrics.parquet"
    missing: set[str] = set()
    if not path.exists():
        for r in records:
            r["forward_return_derivable"] = False
            missing.add(str(r.get("symbol")))
        return missing
    events = pd.read_parquet(path).to_dict("records")
    by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        by_key[(str(event.get("symbol")), str(event.get("event_type")))].append(event)
    for r in records:
        wanted = "first_confirmed_ready" if r.get("decision_bucket") == "confirmed_candidates" else "first_early_ready" if r.get("decision_bucket") == "early_candidates" else ""
        matches = by_key.get((str(r.get("symbol")), wanted), [])
        event = matches[-1] if matches else None
        r["forward_return_derivable"] = bool(event and event.get("reference_price_status") == "ok")
        if not r["forward_return_derivable"]:
            missing.add(str(r.get("symbol")))
        for h in HORIZONS:
            raw = event.get(f"forward_return_{h}d_pct") if event else None
            r[f"return_{h}d_pct"] = float(raw) if finite(raw) else None
            adj, available = apply_slippage(r[f"return_{h}d_pct"], r.get("estimated_slippage_bps"))
            r[f"return_{h}d_adj_pct"] = adj
            r["slippage_adjustment_available"] = available
            r[f"mae_{h}d_pct"] = event.get(f"mae_{h}d_pct") if event and finite(event.get(f"mae_{h}d_pct")) else None
            r[f"mfe_{h}d_pct"] = event.get(f"mfe_{h}d_pct") if event and finite(event.get(f"mfe_{h}d_pct")) else None
    return missing


def dist(records: list[dict[str, Any]], key: str) -> dict[str, int]: return dict(sorted(Counter(str(r.get(key)) for r in records).items()))
def num(records: list[dict[str, Any]], key: str) -> list[float]: return [float(r[key]) for r in records if finite(r.get(key))]
def cell(records: list[dict[str, Any]]) -> dict[str, Any]:
    return {"n": len(records), "execution_status_raw_distribution": dist(records, "execution_status_raw"), "median_return_1d_adj_pct": pct(num(records, "return_1d_adj_pct"), .5), "win_pct_adj": (100 * sum(v > 0 for v in num(records, "return_1d_adj_pct")) / len(num(records, "return_1d_adj_pct"))) if num(records, "return_1d_adj_pct") else None, "median_spread_pct": pct(num(records, "spread_pct"), .5)}


def summarize(records: list[dict[str, Any]], run_ids: list[str]) -> dict[str, Any]:
    counts = Counter(str(r["run_id"]) for r in records)
    result = {"n_total_records": len(records), "n_forward_return_derivable": sum(r.get("forward_return_derivable") is True for r in records), "n_per_run_median": pct([counts[x] for x in run_ids], .5), "n_per_run_p25": pct([counts[x] for x in run_ids], .25), "n_per_run_p75": pct([counts[x] for x in run_ids], .75), "n_zero_days": sum(counts[x] == 0 for x in run_ids), "execution_status_raw_distribution": dist(records, "execution_status_raw"), "depth_ratio_band_distribution": dist(records, "depth_ratio_band"), "median_spread_pct": pct(num(records, "spread_pct"), .5), "median_estimated_slippage_bps": pct(num(records, "estimated_slippage_bps"), .5), "median_available_depth_ratio": pct(num(records, "available_depth_ratio"), .5), "priority_score_p25": pct(num(records, "priority_score"), .25), "priority_score_median": pct(num(records, "priority_score"), .5), "priority_score_p75": pct(num(records, "priority_score"), .75)}
    for h in HORIZONS:
        raw, adj = num(records, f"return_{h}d_pct"), num(records, f"return_{h}d_adj_pct")
        result[f"return_{h}d"] = {"mean_return_pct": sum(raw)/len(raw) if raw else None, "median_return_pct": pct(raw,.5), "win_pct": 100*sum(v>0 for v in raw)/len(raw) if raw else None, "mean_return_adj_pct": sum(adj)/len(adj) if adj else None, "median_return_adj_pct": pct(adj,.5), "win_pct_adj": 100*sum(v>0 for v in adj)/len(adj) if adj else None, "p10_return_pct": pct(raw,.1), "p90_return_pct": pct(raw,.9)}
    return result


def grouped(records: list[dict[str, Any]], keys: tuple[str, ...], extra: Callable[[list[dict[str, Any]]], dict[str, Any]] = cell) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for r in records: groups[tuple(str(r.get(k)) for k in keys)].append(r)
    return [{**dict(zip(keys, key)), **extra(rows)} for key, rows in sorted(groups.items())]


def sanitize(value: Any) -> Any:
    if isinstance(value, dict): return {str(k): sanitize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [sanitize(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value): return None
    return value


def write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(sanitize(payload), indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def report_counts(report: dict[str, Any] | None) -> dict[str, int] | None:
    if not report: return None
    values = report.get("counts_by_bucket", report.get("execution_aware_segments"))
    return values if isinstance(values, dict) else None


def analyze(project_root: Path, *, input_zip_dir: Path | None = None, output_dir: Path | None = None, thresholds: dict[str, Any] | None = None, minimum_runs: int = MINIMUM_RUN_COUNT, cross_validation_tolerance: int = 0) -> dict[str, Any]:
    thresholds = validate_thresholds(thresholds or {"A": PRIORITY_THRESHOLD_A, "B": PRIORITY_THRESHOLD_B, "C": PRIORITY_THRESHOLD_C})
    discovered, included, excluded, mismatches = discover_runs(project_root, input_zip_dir), [], [], []
    for run in discovered:
        ok, reason, warnings = classify_run(run["records"])
        info = {"run_id": run["run_id"], "source": run["source"], "schema_result": reason, "warnings": warnings}
        if not ok: excluded.append(info); continue
        derived = Counter(str(extract_record(r, run["run_id"]).get("decision_bucket")) for r in run["records"] if r.get("candidate_excluded") is not True)
        expected = report_counts(run["report"])
        info["report_cross_validation_available"] = expected is not None
        if expected:
            for bucket in ("confirmed_candidates", "early_candidates"):
                if bucket in expected and abs(int(expected[bucket]) - derived[bucket]) > cross_validation_tolerance:
                    mismatches.append({"run_id": run["run_id"], "bucket": bucket, "diagnostics_count": derived[bucket], "report_count": expected[bucket]})
        included.append({**run, **info})
    if len(included) < minimum_runs:
        raise RuntimeError(f"T30-v2 requires at least 20 ir1.5+ runs. Found: {len(included)}. Accumulate more runs and retry.")
    records = [extract_record(r, run["run_id"]) for run in included for r in run["records"]]
    missing_symbols = attach_forward_returns(project_root, records)
    run_ids = [r["run_id"] for r in included]
    seg_filters, baskets = segments(), basket_filters(thresholds)
    seg_members = {k: [r for r in records if f(r)] for k, f in seg_filters.items()}
    basket_members = {k: [r for r in records if f(r)] for k, f in baskets.items()}
    seg_summary = {k: summarize(v, run_ids) for k, v in seg_members.items()}
    basket_summary = {"applied_config": {f"PRIORITY_THRESHOLD_{k}": v for k,v in thresholds.items()}, "baskets": {k: summarize(v, run_ids) for k,v in basket_members.items()}}
    basket_frequency = {k: {"basket_frequency_by_run": {rid: sum(r["run_id"] == rid for r in rows) for rid in run_ids}, "basket_n_median": pct([sum(r["run_id"] == rid for r in rows) for rid in run_ids],.5), "basket_n_p25": pct([sum(r["run_id"] == rid for r in rows) for rid in run_ids],.25), "basket_n_p75": pct([sum(r["run_id"] == rid for r in rows) for rid in run_ids],.75), "basket_zero_run_count": sum(not any(r["run_id"] == rid for r in rows) for rid in run_ids), "basket_one_plus_run_count": sum(any(r["run_id"] == rid for r in rows) for rid in run_ids), "basket_three_plus_run_count": sum(sum(r["run_id"] == rid for r in rows)>=3 for rid in run_ids)} for k,rows in basket_members.items()}
    primary_1_7 = set(id(r) for k, rows in seg_members.items() if k not in {"S8","S9"} for r in rows)
    out_of_segment = {k: sum(id(r) not in primary_1_7 for r in rows) for k, rows in basket_members.items()}
    broad = [r for r in records if r.get("candidate_excluded") is not True and r.get("decision_bucket") in {"confirmed_candidates","early_candidates"}]
    base = [r for r in records if baseline(r)]
    breakdowns = {
        "cross_breakdown_exec_bucket.json": grouped(broad, ("execution_size_class","decision_bucket")),
        "cross_breakdown_entry_location.json": {"cells": grouped([r for r in base if r["entry_location_status"] != "not_evaluable"], ("entry_location_status","entry_action_hint")), "not_evaluable_count": sum(r["entry_location_status"] == "not_evaluable" for r in base)},
        "cross_breakdown_pattern_bucket.json": grouped(base, ("entry_pattern","decision_bucket"), lambda rows: {**cell(rows), **({"caution_note":"high EMA distance risk — validate entry_location_status before inclusion"} if any(r.get("entry_pattern") == "continuation_breakout" for r in rows) else {})}),
        "cross_breakdown_phase_exec.json": grouped(base, ("market_phase","execution_size_class")),
    }
    priority = {bucket: {"p10": pct(num(rows,"priority_score"),.1), "p25":pct(num(rows,"priority_score"),.25), "median":pct(num(rows,"priority_score"),.5), "p75":pct(num(rows,"priority_score"),.75), "p90":pct(num(rows,"priority_score"),.9)} for bucket in ("confirmed_candidates","early_candidates") for rows in [[r for r in records if r.get("decision_bucket") == bucket]]}
    s6_excluded = sum(baseline(r) and r.get("decision_bucket") == "early_candidates" and r.get("entry_action_hint") == "buy_now_candidate" for r in records)
    coverage = {"included_runs": [{k:v for k,v in run.items() if k not in {"records","report"}} for run in included], "excluded_runs": excluded, "cross_validation_mismatches": mismatches, "missing_ohlcv_symbols": sorted(missing_symbols), "execution_status_raw_distribution": dist(records,"execution_status_raw"), "s6_buy_now_candidate_exclusion_count": s6_excluded, "basket_out_of_segment_member_counts": out_of_segment}
    mfe_rows = [r for r in records if any(finite(r.get(f"mfe_{h}d_pct")) and finite(r.get(f"mae_{h}d_pct")) for h in HORIZONS)]
    mfe = {"mfe_mae_available": bool(mfe_rows)}
    if mfe_rows:
        for h in HORIZONS: mfe.update({f"median_mae_{h}d_pct":pct(num(mfe_rows,f"mae_{h}d_pct"),.5), f"median_mfe_{h}d_pct":pct(num(mfe_rows,f"mfe_{h}d_pct"),.5)})
    out = output_dir or project_root / "reports/aux/t30_v2"; out.mkdir(parents=True, exist_ok=True)
    artifacts = {"segment_summary.json":seg_summary,"basket_summary.json":basket_summary,"basket_frequency.json":basket_frequency,"priority_score_distributions.json":priority,"run_coverage.json":coverage,"mfe_mae_summary.json":mfe,**breakdowns}
    for name,payload in artifacts.items(): write_json(out/name,payload)
    warning = f"WARNING: OHLCV history absent or incomplete for {len(missing_symbols)} symbols.\nForward-return metrics are unavailable or partial.\nRun {FETCH_COMMAND} before re-running this script.\n" if missing_symbols else ""
    if not mfe_rows:
        warning += "MFE/MAE computation skipped: insufficient OHLCV coverage for ir1.5+ run population.\n"
    mismatch_table = "| run_id | bucket | diagnostics_count | report_count |\n|---|---|---:|---:|\n" + "\n".join(f"| {m['run_id']} | {m['bucket']} | {m['diagnostics_count']} | {m['report_count']} |" for m in mismatches)
    if not mismatches:
        mismatch_table += "| _none_ | _none_ | 0 | 0 |"
    coverage_md = f"# T30-v2 Run Coverage\n\n{warning}\nIncluded runs: {len(included)}\n\nExcluded runs: {len(excluded)}\n\nS6 buy_now_candidate exclusion count: {s6_excluded}\n\nBasket out-of-segment member counts: {out_of_segment}\n\n## Cross-validation mismatches\n\n{mismatch_table}\n"
    decision_md = f"# T30-v2 Decision Support — Evidence Only\n\n{warning}\n## Applied Configuration\n\n{basket_summary['applied_config']}\n\n## Q1. Minimum execution_size_class\nSee cross_breakdown_exec_bucket.json.\n## Q2. Allowed entry_action_hints\nSee S1/S2 and entry-location breakdown.\n## Q3. confirmed_candidates only vs. including early_candidates\nSee S6/S9 and Basket C.\n## Q4. Priority score floor\nSee priority_score_distributions.json. Thresholds are preliminary pending manual review.\n## Q5. Pattern restrictions\nSee cross_breakdown_pattern_bucket.json.\n## Q6. Frequency / parallelism\nSee basket_frequency.json.\n\n## Limitations\nBull-market bias; small segment samples; no exit modeling; entry slippage only; MFE/MAE may be unavailable; buy-now comparisons may be unavailable. This report does not recommend or select a live trading basket.\n"
    (out/"run_coverage.md").write_text(coverage_md); (out/"decision_support.md").write_text(decision_md)
    segment_rows = "\n".join(f"| {name} | {summary['n_total_records']} | {summary['n_forward_return_derivable']} | {summary['n_per_run_median']} | {summary['execution_status_raw_distribution']} |" for name, summary in seg_summary.items())
    (out/"segment_report.md").write_text("# T30-v2 Segments\n\n| segment | total records | derivable returns | median per run | raw execution status distribution |\n|---|---:|---:|---:|---|\n" + segment_rows + "\n\nSee `segment_summary.json` for all required return, execution, and priority metrics.\n")
    basket_rows = "\n".join(f"| {name} | {basket_summary['baskets'][name]['n_total_records']} | {values['basket_n_median']} | {values['basket_one_plus_run_count']} | {values['basket_zero_run_count']} |" for name, values in basket_frequency.items())
    (out/"basket_report.md").write_text("# T30-v2 Basket Hypotheses\n\n| basket | total records | median per run | runs with one+ | zero-candidate runs |\n|---|---:|---:|---:|---:|\n" + basket_rows + "\n\nSee `basket_summary.json` and `basket_frequency.json` for full evidence. No basket is selected or recommended.\n")
    return artifacts


def main() -> int:
    parser=argparse.ArgumentParser(description="Produce T30-v2 offline segment-selection evidence")
    parser.add_argument("--project-root",type=Path,default=Path(".")); parser.add_argument("--input-zip-dir",type=Path); parser.add_argument("--output-dir",type=Path)
    args=parser.parse_args(); analyze(args.project_root.resolve(), input_zip_dir=args.input_zip_dir, output_dir=args.output_dir); return 0
if __name__ == "__main__": raise SystemExit(main())
