#!/usr/bin/env python3
"""Risk/Reward diagnosis with sensitivity ladder for reversal max_stop_distance.

Improvements over v1:
- Sensitivity ladder: tests multiple max_stop thresholds (15/18/20/22/25/30%)
- Fixed ATR extraction: reads atr_value from multiple JSON paths
- Shows which symbols unlock at each threshold step
- Cross-checks ATR counterfactual summary vs row-level data

Output: reports/aux/diagnose_rr_<date>.json + .md
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

REPORTS_DIR = Path("reports")
OUTPUT_DIR = Path("reports/aux")
MAX_RUNS = 7

CURRENT_RISK_CONFIG = {
    "min_stop_distance_pct": 4.0,
    "max_stop_distance_pct": 12.0,
    "min_rr_to_target_2": 1.3,
    "atr_multiple": 2.0,
}

REVERSAL_LADDER = [15.0, 18.0, 20.0, 22.0, 25.0, 30.0]

def load_reports(reports_dir, max_runs):
    files = sorted(reports_dir.glob("2026-*.json"), reverse=True)[:max_runs]
    files.reverse()
    reports = []
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["_source_file"] = f.name
        reports.append(data)
    return reports

def _to_float(value):
    if value is None: return None
    try:
        f = float(value)
        return f if math.isfinite(f) else None
    except (TypeError, ValueError): return None

def _round_opt(v, d):
    return round(v, d) if v is not None else None

def _pct(count, total):
    return f"{100.0 * count / total:.1f}" if total else "0.0"

def _percentile(values, pct):
    if not values: return None
    s = sorted(values)
    idx = (len(s) - 1) * pct / 100.0
    lo = int(idx)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (idx - lo) * (s[hi] - s[lo])

def resolve_setup_bucket(candidate):
    setup_type = (candidate.get("best_setup_type") or "").lower().strip()
    setup_subtype = (candidate.get("setup_subtype") or "").lower().strip()
    if setup_type == "pullback" or "pullback" in setup_subtype: return "pullback"
    if setup_type == "reversal" or "reversal" in setup_subtype: return "reversal"
    if setup_type == "breakout" or "breakout" in setup_subtype: return "breakout"
    return "other"

def _extract_trade_levels(candidate):
    analysis = candidate.get("analysis")
    if isinstance(analysis, dict):
        tl = analysis.get("trade_levels")
        if isinstance(tl, dict): return tl
    tl = candidate.get("trade_levels")
    if isinstance(tl, dict): return tl
    return {}

def _extract_atr_value(candidate, trade_levels):
    for src in [
        trade_levels.get("atr_value"),
        candidate.get("atr_value"),
        candidate.get("atr_1d"),
        candidate.get("atr_14_1d"),
    ]:
        atr = _to_float(src)
        if atr is not None and atr > 0: return atr
    return None

def _extract_invalidation(candidate, trade_levels):
    for src in [
        trade_levels.get("invalidation"),
        candidate.get("invalidation"),
        candidate.get("invalidation_anchor_price"),
    ]:
        inv = _to_float(src)
        if inv is not None and inv > 0: return inv
    return None

def _extract_entry_price(candidate, trade_levels, setup_bucket):
    ep = _to_float(candidate.get("entry_price_usdt"))
    if ep and ep > 0: return ep
    if setup_bucket == "pullback":
        zone = trade_levels.get("entry_zone")
        if isinstance(zone, dict):
            ep = _to_float(zone.get("center"))
            if ep and ep > 0: return ep
    ep = _to_float(trade_levels.get("entry_trigger"))
    if ep and ep > 0: return ep
    return None

def _classify_risk_failure(risk_pct, rr_t2, risk_acceptable):
    if risk_acceptable is True: return "PASS"
    if risk_acceptable is None: return "NOT_EVALUABLE"
    if risk_pct is None: return "MISSING_RISK_PCT"
    cfg = CURRENT_RISK_CONFIG
    reasons = []
    if risk_pct < cfg["min_stop_distance_pct"]: reasons.append("STOP_TOO_TIGHT")
    if risk_pct > cfg["max_stop_distance_pct"]: reasons.append("STOP_TOO_WIDE")
    if rr_t2 is None: reasons.append("MISSING_RR")
    elif rr_t2 < cfg["min_rr_to_target_2"]: reasons.append("RR_TOO_LOW")
    return "+".join(reasons) if reasons else "UNKNOWN_FAILURE"

def _check_risk_at_threshold(risk_pct, rr_t2, max_stop):
    if risk_pct is None: return None
    min_stop = CURRENT_RISK_CONFIG["min_stop_distance_pct"]
    min_rr = CURRENT_RISK_CONFIG["min_rr_to_target_2"]
    return (min_stop <= risk_pct <= max_stop) and (rr_t2 is not None and rr_t2 >= min_rr)

def _counterfactual_atr_stop(entry_price, atr_value):
    atr_mult = CURRENT_RISK_CONFIG["atr_multiple"]
    atr_stop = entry_price - (atr_mult * atr_value)
    if atr_stop >= entry_price or atr_stop <= 0:
        return {"viable": False, "reason": "atr_stop_not_below_entry"}
    risk_pct = ((entry_price - atr_stop) / entry_price) * 100.0
    rr_t2 = 2.0
    min_stop = CURRENT_RISK_CONFIG["min_stop_distance_pct"]
    max_stop = CURRENT_RISK_CONFIG["max_stop_distance_pct"]
    min_rr = CURRENT_RISK_CONFIG["min_rr_to_target_2"]
    risk_acceptable = min_stop <= risk_pct <= max_stop and rr_t2 >= min_rr
    return {
        "viable": True,
        "atr_stop_price": round(atr_stop, 6),
        "risk_pct_to_stop": round(risk_pct, 2),
        "rr_to_target_2": rr_t2,
        "risk_acceptable": risk_acceptable,
        "failure_mode": "PASS" if risk_acceptable else (
            "STOP_TOO_TIGHT" if risk_pct < min_stop else
            "STOP_TOO_WIDE" if risk_pct > max_stop else "RR_TOO_LOW"),
    }

def analyze_risk(candidate, source):
    symbol = candidate.get("symbol", "?")
    report_date = candidate.get("_report_date", "?")
    setup_bucket = candidate.get("_inferred_bucket") or resolve_setup_bucket(candidate)
    trade_levels = _extract_trade_levels(candidate)
    risk_acceptable = candidate.get("risk_acceptable")
    stop_price = _to_float(candidate.get("stop_price_initial"))
    stop_source = candidate.get("stop_source")
    risk_pct = _to_float(candidate.get("risk_pct_to_stop"))
    rr_t1 = _to_float(candidate.get("rr_to_target_1"))
    rr_t2 = _to_float(candidate.get("rr_to_target_2"))
    entry_price = _extract_entry_price(candidate, trade_levels, setup_bucket)
    current_price = _to_float(candidate.get("price_usdt") or candidate.get("current_price_usdt"))
    atr_value = _extract_atr_value(candidate, trade_levels)
    invalidation = _extract_invalidation(candidate, trade_levels)
    failure_mode = _classify_risk_failure(risk_pct, rr_t2, risk_acceptable)
    ladder_results = None
    if setup_bucket == "reversal":
        ladder_results = {str(t): _check_risk_at_threshold(risk_pct, rr_t2, t) for t in REVERSAL_LADDER}
    cf_atr = None
    if setup_bucket == "reversal" and stop_source == "invalidation" and entry_price and atr_value and atr_value > 0:
        cf_atr = _counterfactual_atr_stop(entry_price, atr_value)
    return {
        "report_date": report_date, "symbol": symbol, "setup_bucket": setup_bucket,
        "setup_subtype": candidate.get("setup_subtype"), "source": source,
        "decision": candidate.get("decision"), "risk_acceptable": risk_acceptable,
        "stop_price_initial": _round_opt(stop_price, 6), "stop_source": stop_source,
        "risk_pct_to_stop": _round_opt(risk_pct, 2),
        "rr_to_target_1": _round_opt(rr_t1, 2), "rr_to_target_2": _round_opt(rr_t2, 2),
        "entry_price": _round_opt(entry_price, 6), "current_price": _round_opt(current_price, 6),
        "atr_value": _round_opt(atr_value, 6), "invalidation": _round_opt(invalidation, 6),
        "failure_mode": failure_mode, "reversal_ladder": ladder_results, "cf_atr_fallback": cf_atr,
    }

def aggregate(analyses, source_filter):
    rows = [a for a in analyses if a["source"] == source_filter]
    total = len(rows)
    ra_counts = Counter(a["risk_acceptable"] for a in rows)
    fail_modes = Counter(a["failure_mode"] for a in rows)
    setup_stats = {}
    for bucket in ["reversal", "pullback", "breakout", "other"]:
        subset = [a for a in rows if a["setup_bucket"] == bucket]
        if not subset: continue
        risk_pcts = [a["risk_pct_to_stop"] for a in subset if a["risk_pct_to_stop"] is not None]
        rr2s = [a["rr_to_target_2"] for a in subset if a["rr_to_target_2"] is not None]
        cf_atr_stats = None
        if bucket == "reversal":
            cf_atr_viable = [a for a in subset if a.get("cf_atr_fallback") and a["cf_atr_fallback"].get("viable")]
            cf_atr_pass = [a for a in cf_atr_viable if a["cf_atr_fallback"].get("risk_acceptable")]
            cf_atr_stats = {
                "viable_count": len(cf_atr_viable), "would_pass_count": len(cf_atr_pass),
                "viable_symbols": [
                    {"symbol": a["symbol"], "date": a["report_date"],
                     "current_stop_pct": a["risk_pct_to_stop"],
                     "atr_stop_pct": a["cf_atr_fallback"]["risk_pct_to_stop"],
                     "atr_pass": a["cf_atr_fallback"]["risk_acceptable"],
                     "atr_failure": a["cf_atr_fallback"]["failure_mode"]}
                    for a in cf_atr_viable],
            }
        setup_stats[bucket] = {
            "total": len(subset),
            "risk_acceptable_true": sum(1 for a in subset if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in subset if a["risk_acceptable"] is False),
            "risk_acceptable_null": sum(1 for a in subset if a["risk_acceptable"] is None),
            "failure_modes": dict(Counter(a["failure_mode"] for a in subset).most_common()),
            "stop_source_counts": dict(Counter(a["stop_source"] for a in subset).most_common()),
            "risk_pct_to_stop": {
                "min": _round_opt(min(risk_pcts) if risk_pcts else None, 2),
                "p25": _round_opt(_percentile(risk_pcts, 25), 2),
                "median": _round_opt(_percentile(risk_pcts, 50), 2),
                "p75": _round_opt(_percentile(risk_pcts, 75), 2),
                "p90": _round_opt(_percentile(risk_pcts, 90), 2),
                "max": _round_opt(max(risk_pcts) if risk_pcts else None, 2),
            },
            "rr_to_target_2": {
                "min": _round_opt(min(rr2s) if rr2s else None, 2),
                "median": _round_opt(_percentile(rr2s, 50), 2),
                "max": _round_opt(max(rr2s) if rr2s else None, 2),
            },
            "cf_atr_fallback": cf_atr_stats,
        }
    # Sensitivity ladder
    reversal_rows = [a for a in rows if a["setup_bucket"] == "reversal"]
    ladder_summary = {}
    current_pass = sum(1 for a in reversal_rows if a["risk_acceptable"] is True)
    prev_pass = current_pass
    for threshold in REVERSAL_LADDER:
        t_key = str(threshold)
        would_pass = sum(1 for a in reversal_rows if a.get("reversal_ladder", {}).get(t_key) is True)
        newly_unlocked = [
            {"symbol": a["symbol"], "date": a["report_date"], "stop_pct": a["risk_pct_to_stop"]}
            for a in reversal_rows
            if a.get("reversal_ladder", {}).get(t_key) is True and a["risk_acceptable"] is not True
        ]
        unique_symbols = sorted(set(n["symbol"] for n in newly_unlocked))
        ladder_summary[t_key] = {
            "threshold_pct": threshold, "would_pass": would_pass,
            "delta_vs_current": would_pass - current_pass,
            "delta_vs_previous_step": would_pass - prev_pass,
            "newly_unlocked_symbols": unique_symbols,
            "newly_unlocked_details": sorted(newly_unlocked, key=lambda x: x.get("stop_pct") or 999),
        }
        prev_pass = would_pass
    # Per-run
    per_run = []
    for d in sorted(set(a["report_date"] for a in rows)):
        rr = [a for a in rows if a["report_date"] == d]
        per_run.append({
            "date": d, "candidates": len(rr),
            "risk_acceptable_true": sum(1 for a in rr if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in rr if a["risk_acceptable"] is False),
            "failure_stop_too_wide": sum(1 for a in rr if "STOP_TOO_WIDE" in a["failure_mode"]),
            "failure_stop_too_tight": sum(1 for a in rr if "STOP_TOO_TIGHT" in a["failure_mode"]),
        })
    # Setup list stats
    sl_rows = [a for a in analyses if a["source"] != source_filter]
    setup_list_stats = {}
    for bucket in ["reversal", "pullback", "breakout"]:
        subset = [a for a in sl_rows if a["setup_bucket"] == bucket]
        if not subset: continue
        risk_pcts = [a["risk_pct_to_stop"] for a in subset if a["risk_pct_to_stop"] is not None]
        setup_list_stats[bucket] = {
            "total_scored": len(subset),
            "risk_acceptable_true": sum(1 for a in subset if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in subset if a["risk_acceptable"] is False),
            "failure_modes": dict(Counter(a["failure_mode"] for a in subset).most_common()),
            "risk_pct_to_stop": {
                "median": _round_opt(_percentile(risk_pcts, 50), 2),
                "p75": _round_opt(_percentile(risk_pcts, 75), 2),
                "p90": _round_opt(_percentile(risk_pcts, 90), 2),
                "max": _round_opt(max(risk_pcts) if risk_pcts else None, 2),
            },
        }
    return {
        "total_candidates": total,
        "risk_acceptable_counts": {"true": ra_counts.get(True, 0), "false": ra_counts.get(False, 0), "null": ra_counts.get(None, 0)},
        "failure_mode_counts": dict(fail_modes.most_common()),
        "setup_stats": setup_stats,
        "reversal_sensitivity_ladder": ladder_summary,
        "setup_list_stats": setup_list_stats,
        "per_run": per_run,
    }

def generate_markdown(summary, analyses):
    lines = []
    w = lines.append
    w("# Risk/Reward Diagnosis (v2 — Sensitivity Ladder)")
    w("")
    w(f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    w(f"- Candidates: {summary['total_candidates']}")
    w(f"- Config: min_stop={CURRENT_RISK_CONFIG['min_stop_distance_pct']}%, max_stop={CURRENT_RISK_CONFIG['max_stop_distance_pct']}%, min_rr_t2={CURRENT_RISK_CONFIG['min_rr_to_target_2']}")
    w("")
    ra = summary["risk_acceptable_counts"]
    w("## Headline")
    w("")
    w(f"- risk_acceptable=true: **{ra['true']}** ({_pct(ra['true'], summary['total_candidates'])}%)")
    w(f"- risk_acceptable=false: **{ra['false']}** ({_pct(ra['false'], summary['total_candidates'])}%)")
    w("")
    w("## Failure Modes")
    w("")
    w("| Mode | Count |")
    w("|---|---:|")
    for mode, count in summary["failure_mode_counts"].items():
        w(f"| {mode} | {count} |")
    w("")
    for bucket in ["reversal", "pullback", "breakout", "other"]:
        stats = summary["setup_stats"].get(bucket)
        if not stats: continue
        w(f"## {bucket.title()} ({stats['total']})")
        w("")
        w(f"- Pass/Fail/Null: {stats['risk_acceptable_true']}/{stats['risk_acceptable_false']}/{stats['risk_acceptable_null']}")
        w(f"- Stop sources: {stats['stop_source_counts']}")
        rp = stats["risk_pct_to_stop"]
        w(f"- Stop distance: min={rp['min']}% | P25={rp['p25']}% | median={rp['median']}% | P75={rp['p75']}% | P90={rp['p90']}% | max={rp['max']}%")
        w(f"- Failure modes: {stats['failure_modes']}")
        w("")
        cf_atr = stats.get("cf_atr_fallback")
        if cf_atr:
            w("### ATR-Fallback Counterfactual")
            w("")
            w(f"- Viable: {cf_atr['viable_count']}, Would pass: {cf_atr['would_pass_count']}")
            if cf_atr["viable_symbols"]:
                w("")
                w("| Symbol | Date | Current Stop % | ATR Stop % | ATR Pass? | ATR Failure |")
                w("|---|---|---:|---:|---|---|")
                for vs in cf_atr["viable_symbols"]:
                    w(f"| {vs['symbol']} | {vs['date']} | {vs['current_stop_pct']}% | {vs['atr_stop_pct']}% | {vs['atr_pass']} | {vs['atr_failure']} |")
            w("")
    w("## Reversal Sensitivity Ladder")
    w("")
    w("| Threshold | Would Pass | +vs Current | +vs Prev Step | New Symbols |")
    w("|---:|---:|---:|---:|---|")
    rev_stats = summary["setup_stats"].get("reversal", {})
    current_pass = rev_stats.get("risk_acceptable_true", 0)
    w(f"| **{CURRENT_RISK_CONFIG['max_stop_distance_pct']}% (current)** | **{current_pass}** | — | — | — |")
    for threshold in REVERSAL_LADDER:
        step = summary["reversal_sensitivity_ladder"].get(str(threshold), {})
        syms = ", ".join(step.get("newly_unlocked_symbols", [])[:10])
        extra = len(step.get("newly_unlocked_symbols", [])) - 10
        if extra > 0: syms += f" (+{extra})"
        w(f"| {threshold}% | {step.get('would_pass', '?')} | +{step.get('delta_vs_current', '?')} | +{step.get('delta_vs_previous_step', '?')} | {syms} |")
    w("")
    w("## Per-Run Timeline")
    w("")
    w("| Date | Candidates | RA=true | RA=false | Stop Wide | Stop Tight |")
    w("|---|---:|---:|---:|---:|---:|")
    for r in summary["per_run"]:
        w(f"| {r['date']} | {r['candidates']} | {r['risk_acceptable_true']} | {r['risk_acceptable_false']} | {r['failure_stop_too_wide']} | {r['failure_stop_too_tight']} |")
    w("")
    if summary["setup_list_stats"]:
        w("## Full Scored Universe")
        w("")
        for bucket in ["reversal", "pullback", "breakout"]:
            sls = summary["setup_list_stats"].get(bucket)
            if not sls: continue
            rp = sls["risk_pct_to_stop"]
            w(f"**{bucket.title()}** ({sls['total_scored']}): pass={sls['risk_acceptable_true']}, fail={sls['risk_acceptable_false']} | median={rp['median']}%, P90={rp['p90']}%, max={rp['max']}%")
            w("")
    rev_fail = sorted(
        [a for a in analyses if a["setup_bucket"] == "reversal" and a["risk_acceptable"] is False and a["source"] == "trade_candidates"],
        key=lambda a: a.get("risk_pct_to_stop") or 999, reverse=True)
    if rev_fail:
        w("## Worst Reversal Stop Profiles")
        w("")
        w("| Date | Symbol | Stop % | Entry | Stop | Invalidation | ATR | ATR CF |")
        w("|---|---|---:|---:|---:|---:|---:|---|")
        for a in rev_fail[:20]:
            cf = a.get("cf_atr_fallback") or {}
            cf_str = f"pass@{cf['risk_pct_to_stop']}%" if cf.get("risk_acceptable") else (f"fail@{cf['risk_pct_to_stop']}%" if cf.get("viable") else "n/a")
            w(f"| {a['report_date']} | {a['symbol']} | {a['risk_pct_to_stop']}% | {a['entry_price']} | {a['stop_price_initial']} | {a['invalidation']} | {a['atr_value']} | {cf_str} |")
        w("")
    return "\n".join(lines)

def extract_candidates(report):
    report_date = report.get("meta", {}).get("date", "unknown")
    source_file = report.get("_source_file", "unknown")
    tc = []
    for c in report.get("trade_candidates", []):
        row = dict(c); row["_report_date"] = report_date; row["_source_file"] = source_file; row["_source"] = "trade_candidates"; tc.append(row)
    sr = []
    for key, lst in report.get("setups", {}).items():
        if not isinstance(lst, list): continue
        for entry in lst:
            if not isinstance(entry, dict): continue
            row = dict(entry); row["_report_date"] = report_date; row["_source_file"] = source_file; row["_source"] = f"setups.{key}"
            if "reversal" in key: row["_inferred_bucket"] = "reversal"
            elif "pullback" in key: row["_inferred_bucket"] = "pullback"
            elif "breakout" in key: row["_inferred_bucket"] = "breakout"
            sr.append(row)
    return tc, sr

def main():
    print(f"Loading reports from {REPORTS_DIR}...")
    reports = load_reports(REPORTS_DIR, MAX_RUNS)
    if not reports:
        print(f"ERROR: No reports in {REPORTS_DIR}", file=sys.stderr); return 1
    print(f"Loaded {len(reports)} reports")
    all_tc, all_sr, reports_used = [], [], []
    for report in reports:
        tc, sr = extract_candidates(report)
        all_tc.extend(tc); all_sr.extend(sr); reports_used.append(report.get("_source_file", "?"))
        print(f"  {report.get('_source_file')}: {len(tc)} trade_candidates, {len(sr)} setup rows")
    if not all_tc:
        print("ERROR: No trade_candidates", file=sys.stderr); return 1
    analyses_tc = [analyze_risk(c, "trade_candidates") for c in all_tc]
    analyses_sr = [analyze_risk(c, c.get("_source", "setups")) for c in all_sr]
    summary = aggregate(analyses_tc + analyses_sr, "trade_candidates")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    json_path = OUTPUT_DIR / f"diagnose_rr_{today}.json"
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump({"generated_at_utc": datetime.now(timezone.utc).isoformat(), "reports_used": reports_used, "config": CURRENT_RISK_CONFIG, "reversal_ladder": REVERSAL_LADDER, "summary": summary, "trade_candidate_rows": analyses_tc, "setup_list_sample": analyses_sr[:50]}, fh, indent=2, ensure_ascii=False)
    print(f"\nJSON: {json_path}")
    md_path = OUTPUT_DIR / f"diagnose_rr_{today}.md"
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write(generate_markdown(summary, analyses_tc + analyses_sr))
    print(f"MD: {md_path}")
    print("\n" + "=" * 60)
    print("SENSITIVITY LADDER (Reversal max_stop_distance)")
    print("=" * 60)
    rev = summary["setup_stats"].get("reversal", {})
    print(f"Current (12%): {rev.get('risk_acceptable_true', 0)}/{rev.get('total', 0)} pass")
    for t in REVERSAL_LADDER:
        step = summary["reversal_sensitivity_ladder"].get(str(t), {})
        print(f"  {t:5.1f}%: {step.get('would_pass', '?')} pass (+{step.get('delta_vs_current', '?')} vs current, +{step.get('delta_vs_previous_step', '?')} marginal)")
    cf_atr = rev.get("cf_atr_fallback")
    if cf_atr:
        print(f"\nATR-Fallback: {cf_atr['viable_count']} viable, {cf_atr['would_pass_count']} would pass")
        for vs in cf_atr.get("viable_symbols", []):
            print(f"  {vs['symbol']} ({vs['date']}): {vs['current_stop_pct']}% -> {vs['atr_stop_pct']}% {'PASS' if vs['atr_pass'] else vs['atr_failure']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
