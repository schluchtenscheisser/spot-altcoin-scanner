#!/usr/bin/env python3
"""Risk/Reward diagnosis across recent runs.

Answers:
1. Why do 79% of candidates fail risk_acceptable?
2. Which gate fails: min_stop_distance, max_stop_distance, or RR threshold?
3. How does the failure mode differ by setup type (reversal vs pullback)?
4. Counterfactual: what if max_stop_distance_pct were setup-specific?
5. Counterfactual: what if reversals used ATR-fallback instead of base_low?

Output: reports/aux/diagnose_rr_<date>.json + .md
"""

from __future__ import annotations

import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

REPORTS_DIR = Path("reports")
OUTPUT_DIR = Path("reports/aux")
MAX_RUNS = 7

# Current production risk config
CURRENT_RISK_CONFIG = {
    "min_stop_distance_pct": 4.0,
    "max_stop_distance_pct": 12.0,
    "min_rr_to_target_2": 1.3,  # config key is min_rr_to_tp10, evaluated on target_2
    "atr_multiple": 2.0,
}

# Hypothetical setup-specific max_stop_distance_pct
HYPOTHETICAL_MAX_STOP = {
    "reversal": 25.0,
    "pullback": 12.0,   # unchanged
    "breakout": 12.0,   # unchanged
    "default": 12.0,
}

# Hypothetical setup-specific min_rr
HYPOTHETICAL_MIN_RR = {
    "reversal": 1.0,
    "pullback": 1.3,   # unchanged
    "breakout": 1.3,   # unchanged
    "default": 1.3,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_reports(reports_dir: Path, max_runs: int) -> list[dict[str, Any]]:
    files = sorted(reports_dir.glob("2026-*.json"), reverse=True)[:max_runs]
    files.reverse()
    reports = []
    for f in files:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["_source_file"] = f.name
        reports.append(data)
    return reports


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        f = float(value)
        if not math.isfinite(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def _round_opt(value: Optional[float], decimals: int) -> Optional[float]:
    if value is None:
        return None
    return round(value, decimals)


def _pct(count: int, total: int) -> str:
    if total == 0:
        return "0.0"
    return f"{100.0 * count / total:.1f}"


def _percentile(values: list[float], pct: float) -> Optional[float]:
    if not values:
        return None
    s = sorted(values)
    idx = (len(s) - 1) * pct / 100.0
    lo = int(idx)
    hi = min(lo + 1, len(s) - 1)
    frac = idx - lo
    return s[lo] + frac * (s[hi] - s[lo])


def resolve_setup_bucket(candidate: dict[str, Any]) -> str:
    setup_type = (candidate.get("best_setup_type") or "").lower().strip()
    setup_subtype = (candidate.get("setup_subtype") or "").lower().strip()
    if setup_type == "pullback" or "pullback" in setup_subtype:
        return "pullback"
    if setup_type == "reversal" or "reversal" in setup_subtype:
        return "reversal"
    if setup_type == "breakout" or "breakout" in setup_subtype:
        return "breakout"
    return "other"


# ---------------------------------------------------------------------------
# Candidate extraction — from trade_candidates AND setup lists
# ---------------------------------------------------------------------------

def extract_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract candidates from trade_candidates (primary) + setup lists (supplementary)."""
    report_date = report.get("meta", {}).get("date", "unknown")
    source_file = report.get("_source_file", "unknown")

    # Primary: trade_candidates (Top 20 with decisions)
    trade_candidates = []
    for c in report.get("trade_candidates", []):
        row = dict(c)
        row["_report_date"] = report_date
        row["_source_file"] = source_file
        row["_source"] = "trade_candidates"
        trade_candidates.append(row)

    # Supplementary: setup lists (all scored, not just top 20)
    setup_rows = []
    setups = report.get("setups", {})
    for setup_key, setup_list in setups.items():
        if not isinstance(setup_list, list):
            continue
        for entry in setup_list:
            if not isinstance(entry, dict):
                continue
            row = dict(entry)
            row["_report_date"] = report_date
            row["_source_file"] = source_file
            row["_source"] = f"setups.{setup_key}"
            # Infer setup bucket from setup_key
            if "reversal" in setup_key:
                row["_inferred_bucket"] = "reversal"
            elif "pullback" in setup_key:
                row["_inferred_bucket"] = "pullback"
            elif "breakout" in setup_key:
                row["_inferred_bucket"] = "breakout"
            setup_rows.append(row)

    return trade_candidates, setup_rows


# ---------------------------------------------------------------------------
# Risk analysis per candidate
# ---------------------------------------------------------------------------

def analyze_risk(candidate: dict[str, Any], source: str) -> dict[str, Any]:
    """Analyze risk fields for a single candidate."""
    symbol = candidate.get("symbol", "?")
    report_date = candidate.get("_report_date", "?")

    setup_bucket = candidate.get("_inferred_bucket") or resolve_setup_bucket(candidate)

    # Extract risk fields
    risk_acceptable = candidate.get("risk_acceptable")
    stop_price = _to_float(candidate.get("stop_price_initial"))
    stop_source = candidate.get("stop_source")
    risk_pct = _to_float(candidate.get("risk_pct_to_stop"))
    rr_t1 = _to_float(candidate.get("rr_to_target_1"))
    rr_t2 = _to_float(candidate.get("rr_to_target_2"))

    # Entry price
    entry_price = _to_float(candidate.get("entry_price_usdt"))
    if entry_price is None:
        # Try analysis.trade_levels
        analysis = candidate.get("analysis", {})
        trade_levels = analysis.get("trade_levels", {}) if isinstance(analysis, dict) else {}
        if setup_bucket == "pullback":
            zone = trade_levels.get("entry_zone", {})
            if isinstance(zone, dict):
                entry_price = _to_float(zone.get("center"))
        else:
            entry_price = _to_float(trade_levels.get("entry_trigger"))

    current_price = _to_float(candidate.get("price_usdt") or candidate.get("current_price_usdt"))

    # ATR value for counterfactual
    atr_value = None
    analysis = candidate.get("analysis", {})
    if isinstance(analysis, dict):
        trade_levels = analysis.get("trade_levels", {})
        if isinstance(trade_levels, dict):
            atr_value = _to_float(trade_levels.get("atr_value"))

    # Invalidation anchor
    invalidation = None
    if isinstance(analysis, dict):
        trade_levels = analysis.get("trade_levels", {})
        if isinstance(trade_levels, dict):
            invalidation = _to_float(trade_levels.get("invalidation"))

    # Determine WHY risk_acceptable is false
    failure_mode = _classify_risk_failure(risk_pct, rr_t2, risk_acceptable)

    # Counterfactual 1: What if max_stop_distance were setup-specific?
    hyp_max_stop = HYPOTHETICAL_MAX_STOP.get(setup_bucket, HYPOTHETICAL_MAX_STOP["default"])
    hyp_min_rr = HYPOTHETICAL_MIN_RR.get(setup_bucket, HYPOTHETICAL_MIN_RR["default"])
    cf_max_stop_pass = _counterfactual_risk_check(risk_pct, rr_t2, hyp_max_stop, hyp_min_rr)

    # Counterfactual 2: What if reversal used ATR-fallback instead of invalidation?
    cf_atr_result = None
    if setup_bucket == "reversal" and stop_source == "invalidation" and entry_price and atr_value:
        cf_atr_result = _counterfactual_atr_stop(
            entry_price, atr_value, CURRENT_RISK_CONFIG["atr_multiple"],
            CURRENT_RISK_CONFIG["min_stop_distance_pct"],
            CURRENT_RISK_CONFIG["max_stop_distance_pct"],
            CURRENT_RISK_CONFIG["min_rr_to_target_2"],
        )

    return {
        "report_date": report_date,
        "symbol": symbol,
        "setup_bucket": setup_bucket,
        "setup_subtype": candidate.get("setup_subtype"),
        "source": source,
        "decision": candidate.get("decision"),
        "risk_acceptable": risk_acceptable,
        "stop_price_initial": _round_opt(stop_price, 6),
        "stop_source": stop_source,
        "risk_pct_to_stop": _round_opt(risk_pct, 2),
        "rr_to_target_1": _round_opt(rr_t1, 2),
        "rr_to_target_2": _round_opt(rr_t2, 2),
        "entry_price": _round_opt(entry_price, 6),
        "current_price": _round_opt(current_price, 6),
        "atr_value": _round_opt(atr_value, 6),
        "invalidation": _round_opt(invalidation, 6),
        "failure_mode": failure_mode,
        "cf_setup_specific_max_stop": {
            "max_stop_pct": hyp_max_stop,
            "min_rr": hyp_min_rr,
            "would_pass": cf_max_stop_pass,
        },
        "cf_atr_fallback": cf_atr_result,
    }


def _classify_risk_failure(
    risk_pct: Optional[float],
    rr_t2: Optional[float],
    risk_acceptable: Any,
) -> str:
    """Classify why risk_acceptable is false."""
    if risk_acceptable is True:
        return "PASS"
    if risk_acceptable is None:
        return "NOT_EVALUABLE"

    cfg = CURRENT_RISK_CONFIG
    reasons = []

    if risk_pct is None:
        return "MISSING_RISK_PCT"

    if risk_pct < cfg["min_stop_distance_pct"]:
        reasons.append("STOP_TOO_TIGHT")
    if risk_pct > cfg["max_stop_distance_pct"]:
        reasons.append("STOP_TOO_WIDE")

    if rr_t2 is None:
        reasons.append("MISSING_RR")
    elif rr_t2 < cfg["min_rr_to_target_2"]:
        reasons.append("RR_TOO_LOW")

    if not reasons:
        # risk_acceptable=false but we can't identify why from the fields
        return "UNKNOWN_FAILURE"

    return "+".join(reasons)


def _counterfactual_risk_check(
    risk_pct: Optional[float],
    rr_t2: Optional[float],
    max_stop_pct: float,
    min_rr: float,
) -> Optional[bool]:
    """Would this candidate pass risk_acceptable with different thresholds?"""
    if risk_pct is None:
        return None
    min_stop = CURRENT_RISK_CONFIG["min_stop_distance_pct"]
    stop_ok = min_stop <= risk_pct <= max_stop_pct
    rr_ok = rr_t2 is not None and rr_t2 >= min_rr
    return stop_ok and rr_ok


def _counterfactual_atr_stop(
    entry_price: float,
    atr_value: float,
    atr_multiple: float,
    min_stop_pct: float,
    max_stop_pct: float,
    min_rr: float,
) -> dict[str, Any]:
    """What if this reversal used ATR-fallback stop instead of invalidation?"""
    atr_stop = entry_price - (atr_multiple * atr_value)
    if atr_stop >= entry_price or atr_stop <= 0:
        return {"viable": False, "reason": "atr_stop_not_below_entry"}

    risk_abs = entry_price - atr_stop
    risk_pct = (risk_abs / entry_price) * 100.0

    target_1 = entry_price + risk_abs
    target_2 = entry_price + 2.0 * risk_abs
    rr_t2 = 2.0  # by construction: target_2 = entry + 2R → rr = 2.0

    stop_ok = min_stop_pct <= risk_pct <= max_stop_pct
    rr_ok = rr_t2 >= min_rr
    risk_acceptable = stop_ok and rr_ok

    return {
        "viable": True,
        "atr_stop_price": round(atr_stop, 6),
        "risk_pct_to_stop": round(risk_pct, 2),
        "rr_to_target_2": round(rr_t2, 2),
        "risk_acceptable": risk_acceptable,
        "failure_mode": "PASS" if risk_acceptable else (
            "STOP_TOO_TIGHT" if risk_pct < min_stop_pct else
            "STOP_TOO_WIDE" if risk_pct > max_stop_pct else
            "RR_TOO_LOW"
        ),
    }


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(analyses: list[dict[str, Any]], source_filter: str = "trade_candidates") -> dict[str, Any]:
    """Aggregate risk analysis results."""
    rows = [a for a in analyses if a["source"] == source_filter] if source_filter else analyses
    total = len(rows)

    # risk_acceptable distribution
    ra_counts = Counter(a["risk_acceptable"] for a in rows)

    # Failure mode distribution
    fail_modes = Counter(a["failure_mode"] for a in rows)

    # Per-setup breakdown
    setup_stats = {}
    for bucket in ["reversal", "pullback", "breakout", "other"]:
        subset = [a for a in rows if a["setup_bucket"] == bucket]
        if not subset:
            continue

        risk_pcts = [a["risk_pct_to_stop"] for a in subset if a["risk_pct_to_stop"] is not None]
        rr2s = [a["rr_to_target_2"] for a in subset if a["rr_to_target_2"] is not None]
        fail_sub = Counter(a["failure_mode"] for a in subset)
        stop_sources = Counter(a["stop_source"] for a in subset)

        # Counterfactual: setup-specific max_stop
        cf_pass = sum(1 for a in subset if a["cf_setup_specific_max_stop"]["would_pass"] is True)
        cf_fail = sum(1 for a in subset if a["cf_setup_specific_max_stop"]["would_pass"] is False)

        # Counterfactual: ATR fallback (reversal only)
        cf_atr_viable = 0
        cf_atr_pass = 0
        if bucket == "reversal":
            for a in subset:
                cfr = a.get("cf_atr_fallback")
                if cfr and cfr.get("viable"):
                    cf_atr_viable += 1
                    if cfr.get("risk_acceptable"):
                        cf_atr_pass += 1

        setup_stats[bucket] = {
            "total": len(subset),
            "risk_acceptable_true": sum(1 for a in subset if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in subset if a["risk_acceptable"] is False),
            "risk_acceptable_null": sum(1 for a in subset if a["risk_acceptable"] is None),
            "failure_modes": dict(fail_sub.most_common()),
            "stop_source_counts": dict(stop_sources.most_common()),
            "risk_pct_to_stop": {
                "min": _round_opt(min(risk_pcts) if risk_pcts else None, 2),
                "p25": _round_opt(_percentile(risk_pcts, 25), 2),
                "median": _round_opt(_percentile(risk_pcts, 50), 2),
                "p75": _round_opt(_percentile(risk_pcts, 75), 2),
                "max": _round_opt(max(risk_pcts) if risk_pcts else None, 2),
            },
            "rr_to_target_2": {
                "min": _round_opt(min(rr2s) if rr2s else None, 2),
                "median": _round_opt(_percentile(rr2s, 50), 2),
                "max": _round_opt(max(rr2s) if rr2s else None, 2),
            },
            "counterfactual_setup_specific_max_stop": {
                "threshold": HYPOTHETICAL_MAX_STOP.get(bucket, HYPOTHETICAL_MAX_STOP["default"]),
                "would_pass": cf_pass,
                "would_fail": cf_fail,
                "delta_vs_current": cf_pass - sum(1 for a in subset if a["risk_acceptable"] is True),
            },
            "counterfactual_atr_fallback": {
                "viable": cf_atr_viable,
                "would_pass": cf_atr_pass,
            } if bucket == "reversal" else None,
        }

    # Supplementary: full setup-list analysis (all scored candidates, not just top 20)
    setup_list_rows = [a for a in analyses if a["source"] != "trade_candidates"]
    setup_list_stats = {}
    for bucket in ["reversal", "pullback", "breakout"]:
        subset = [a for a in setup_list_rows if a["setup_bucket"] == bucket]
        if not subset:
            continue
        risk_pcts = [a["risk_pct_to_stop"] for a in subset if a["risk_pct_to_stop"] is not None]
        fail_sub = Counter(a["failure_mode"] for a in subset)
        stop_sources = Counter(a["stop_source"] for a in subset)

        setup_list_stats[bucket] = {
            "total_scored": len(subset),
            "risk_acceptable_true": sum(1 for a in subset if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in subset if a["risk_acceptable"] is False),
            "failure_modes": dict(fail_sub.most_common()),
            "stop_source_counts": dict(stop_sources.most_common()),
            "risk_pct_to_stop": {
                "median": _round_opt(_percentile(risk_pcts, 50), 2),
                "p75": _round_opt(_percentile(risk_pcts, 75), 2),
                "p90": _round_opt(_percentile(risk_pcts, 90), 2),
                "max": _round_opt(max(risk_pcts) if risk_pcts else None, 2),
            },
        }

    # Per-run summary
    per_run = []
    dates = sorted(set(a["report_date"] for a in rows))
    for d in dates:
        run_rows = [a for a in rows if a["report_date"] == d]
        per_run.append({
            "date": d,
            "candidates": len(run_rows),
            "risk_acceptable_true": sum(1 for a in run_rows if a["risk_acceptable"] is True),
            "risk_acceptable_false": sum(1 for a in run_rows if a["risk_acceptable"] is False),
            "risk_acceptable_null": sum(1 for a in run_rows if a["risk_acceptable"] is None),
            "failure_stop_too_wide": sum(1 for a in run_rows if "STOP_TOO_WIDE" in a["failure_mode"]),
            "failure_stop_too_tight": sum(1 for a in run_rows if "STOP_TOO_TIGHT" in a["failure_mode"]),
            "failure_rr_too_low": sum(1 for a in run_rows if "RR_TOO_LOW" in a["failure_mode"]),
        })

    return {
        "source_filter": source_filter,
        "total_candidates": total,
        "risk_acceptable_counts": {
            "true": ra_counts.get(True, 0),
            "false": ra_counts.get(False, 0),
            "null": ra_counts.get(None, 0),
        },
        "failure_mode_counts": dict(fail_modes.most_common()),
        "current_risk_config": CURRENT_RISK_CONFIG,
        "setup_stats": setup_stats,
        "setup_list_stats": setup_list_stats,
        "per_run": per_run,
    }


# ---------------------------------------------------------------------------
# Markdown output
# ---------------------------------------------------------------------------

def generate_markdown(summary: dict[str, Any], analyses: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    w = lines.append

    w("# Risk/Reward Diagnosis")
    w("")
    w(f"- Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    w(f"- Source: {summary['source_filter']} ({summary['total_candidates']} candidates)")
    w(f"- Current config: min_stop={CURRENT_RISK_CONFIG['min_stop_distance_pct']}%, "
      f"max_stop={CURRENT_RISK_CONFIG['max_stop_distance_pct']}%, "
      f"min_rr_t2={CURRENT_RISK_CONFIG['min_rr_to_target_2']}")
    w("")

    # Headline
    ra = summary["risk_acceptable_counts"]
    w("## Headline")
    w("")
    w(f"- risk_acceptable=true: **{ra['true']}** ({_pct(ra['true'], summary['total_candidates'])}%)")
    w(f"- risk_acceptable=false: **{ra['false']}** ({_pct(ra['false'], summary['total_candidates'])}%)")
    w(f"- risk_acceptable=null: {ra['null']}")
    w("")

    # Failure mode breakdown
    w("## Why risk_acceptable=false")
    w("")
    w("| Failure Mode | Count | Meaning |")
    w("|---|---:|---|")
    mode_desc = {
        "STOP_TOO_WIDE": f"risk_pct_to_stop > {CURRENT_RISK_CONFIG['max_stop_distance_pct']}% — stop too far from entry",
        "STOP_TOO_TIGHT": f"risk_pct_to_stop < {CURRENT_RISK_CONFIG['min_stop_distance_pct']}% — stop too close to entry",
        "RR_TOO_LOW": f"rr_to_target_2 < {CURRENT_RISK_CONFIG['min_rr_to_target_2']} — reward too small vs risk",
        "STOP_TOO_WIDE+RR_TOO_LOW": "Both: stop too wide AND RR too low",
        "STOP_TOO_TIGHT+RR_TOO_LOW": "Both: stop too tight AND RR too low",
        "PASS": "risk_acceptable=true",
        "NOT_EVALUABLE": "Missing data, risk could not be computed",
        "MISSING_RISK_PCT": "risk_pct_to_stop is null",
        "MISSING_RR": "rr_to_target_2 is null",
    }
    for mode, count in summary["failure_mode_counts"].items():
        desc = mode_desc.get(mode, "")
        w(f"| {mode} | {count} | {desc} |")
    w("")

    # Per setup type
    w("## Setup Type Breakdown")
    w("")
    for bucket in ["reversal", "pullback", "breakout", "other"]:
        stats = summary["setup_stats"].get(bucket)
        if not stats:
            continue

        w(f"### {bucket.title()} ({stats['total']} candidates)")
        w("")
        w(f"- risk_acceptable: true={stats['risk_acceptable_true']}, "
          f"false={stats['risk_acceptable_false']}, null={stats['risk_acceptable_null']}")
        w("")

        # Stop source
        w("**Stop source:**")
        w("")
        for src, cnt in stats["stop_source_counts"].items():
            w(f"- {src}: {cnt}")
        w("")

        # Risk pct distribution
        rp = stats["risk_pct_to_stop"]
        w(f"**risk_pct_to_stop distribution:** min={rp['min']}% | P25={rp['p25']}% | "
          f"median={rp['median']}% | P75={rp['p75']}% | max={rp['max']}%")
        w("")

        # RR distribution
        rr = stats["rr_to_target_2"]
        w(f"**rr_to_target_2 distribution:** min={rr['min']} | median={rr['median']} | max={rr['max']}")
        w("")

        # Failure modes
        w("**Failure modes:**")
        w("")
        w("| Mode | Count |")
        w("|---|---:|")
        for mode, count in stats["failure_modes"].items():
            w(f"| {mode} | {count} |")
        w("")

        # Counterfactual: setup-specific max stop
        cf = stats["counterfactual_setup_specific_max_stop"]
        w(f"**Counterfactual — max_stop_distance={cf['threshold']}%:**")
        w(f"- Would pass: {cf['would_pass']} (current: {stats['risk_acceptable_true']}, delta: **+{cf['delta_vs_current']}**)")
        w("")

        # Counterfactual: ATR fallback (reversal only)
        cf_atr = stats.get("counterfactual_atr_fallback")
        if cf_atr:
            w(f"**Counterfactual — ATR-fallback stop instead of base_low:**")
            w(f"- Viable ATR stops: {cf_atr['viable']}")
            w(f"- Would pass risk_acceptable: {cf_atr['would_pass']}")
            w("")

    # Full setup list analysis
    if summary["setup_list_stats"]:
        w("## Full Scored Universe (all setups, not just Top 20)")
        w("")
        for bucket in ["reversal", "pullback", "breakout"]:
            sls = summary["setup_list_stats"].get(bucket)
            if not sls:
                continue
            w(f"### {bucket.title()} ({sls['total_scored']} scored)")
            w("")
            w(f"- risk_acceptable: true={sls['risk_acceptable_true']}, false={sls['risk_acceptable_false']}")
            rp = sls["risk_pct_to_stop"]
            w(f"- risk_pct_to_stop: median={rp['median']}% | P75={rp['p75']}% | P90={rp['p90']}% | max={rp['max']}%")
            w(f"- Stop sources: {sls['stop_source_counts']}")
            w(f"- Failure modes: {sls['failure_modes']}")
            w("")

    # Per-run timeline
    w("## Per-Run Timeline")
    w("")
    w("| Date | Candidates | RA=true | RA=false | RA=null | Stop Wide | Stop Tight | RR Low |")
    w("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in summary["per_run"]:
        w(f"| {r['date']} | {r['candidates']} | {r['risk_acceptable_true']} | "
          f"{r['risk_acceptable_false']} | {r['risk_acceptable_null']} | "
          f"{r['failure_stop_too_wide']} | {r['failure_stop_too_tight']} | {r['failure_rr_too_low']} |")
    w("")

    # Sample: worst reversal RR cases
    reversals_failed = [
        a for a in analyses
        if a["setup_bucket"] == "reversal"
        and a["risk_acceptable"] is False
        and a["source"] == "trade_candidates"
    ]
    reversals_failed.sort(key=lambda a: a.get("risk_pct_to_stop") or 999, reverse=True)

    if reversals_failed:
        w("## Worst Reversal Risk Profiles (widest stops)")
        w("")
        w("| Date | Symbol | Stop Source | Stop % | RR2 | Entry | Stop | Invalidation | ATR | CF ATR Pass? |")
        w("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
        for a in reversals_failed[:20]:
            cf_atr = a.get("cf_atr_fallback", {})
            cf_pass = "yes" if cf_atr and cf_atr.get("risk_acceptable") else ("no" if cf_atr and cf_atr.get("viable") else "n/a")
            cf_rpct = cf_atr.get("risk_pct_to_stop", "") if cf_atr and cf_atr.get("viable") else ""
            w(f"| {a['report_date']} | {a['symbol']} | {a['stop_source']} | "
              f"{a['risk_pct_to_stop']}% | {a['rr_to_target_2']} | "
              f"{a['entry_price']} | {a['stop_price_initial']} | {a['invalidation']} | {a['atr_value']} | "
              f"{cf_pass} ({cf_rpct}%) |")
        w("")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    print(f"Loading reports from {REPORTS_DIR}...")
    reports = load_reports(REPORTS_DIR, MAX_RUNS)

    if not reports:
        print(f"ERROR: No report files found in {REPORTS_DIR}", file=sys.stderr)
        return 1

    print(f"Loaded {len(reports)} reports: {[r.get('_source_file') for r in reports]}")

    # Extract all candidates
    all_trade_candidates: list[dict[str, Any]] = []
    all_setup_rows: list[dict[str, Any]] = []
    reports_used: list[str] = []

    for report in reports:
        tc, sr = extract_candidates(report)
        all_trade_candidates.extend(tc)
        all_setup_rows.extend(sr)
        reports_used.append(report.get("_source_file", "?"))
        print(f"  {report.get('_source_file')}: {len(tc)} trade_candidates, {len(sr)} setup rows")

    if not all_trade_candidates:
        print("ERROR: No trade_candidates found", file=sys.stderr)
        return 1

    print(f"\nTotal trade_candidates: {len(all_trade_candidates)}")
    print(f"Total setup rows: {len(all_setup_rows)}")

    # Analyze
    analyses_tc = [analyze_risk(c, "trade_candidates") for c in all_trade_candidates]
    analyses_sr = [analyze_risk(c, c.get("_source", "setups")) for c in all_setup_rows]
    all_analyses = analyses_tc + analyses_sr

    # Aggregate (trade_candidates only for primary stats)
    summary = aggregate(all_analyses, source_filter="trade_candidates")

    # Output
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    json_path = OUTPUT_DIR / f"diagnose_rr_{today}.json"
    json_output = {
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reports_used": reports_used,
        "current_risk_config": CURRENT_RISK_CONFIG,
        "hypothetical_max_stop": HYPOTHETICAL_MAX_STOP,
        "hypothetical_min_rr": HYPOTHETICAL_MIN_RR,
        "summary": summary,
        "trade_candidate_rows": analyses_tc,
        "setup_list_sample": analyses_sr[:50],  # limit size
    }
    with json_path.open("w", encoding="utf-8") as fh:
        json.dump(json_output, fh, indent=2, ensure_ascii=False)
    print(f"\nJSON: {json_path}")

    md_path = OUTPUT_DIR / f"diagnose_rr_{today}.md"
    md_output = generate_markdown(summary, all_analyses)
    with md_path.open("w", encoding="utf-8") as fh:
        fh.write(md_output)
    print(f"Markdown: {md_path}")

    # Console summary
    print("\n" + "=" * 60)
    print("KEY FINDINGS")
    print("=" * 60)
    ra = summary["risk_acceptable_counts"]
    print(f"risk_acceptable true/false/null: {ra['true']}/{ra['false']}/{ra['null']}")
    print()
    print("Failure modes:")
    for mode, count in summary["failure_mode_counts"].items():
        print(f"  {mode:35s}: {count}")
    print()
    for bucket in ["reversal", "pullback"]:
        s = summary["setup_stats"].get(bucket, {})
        if not s:
            continue
        cf = s["counterfactual_setup_specific_max_stop"]
        print(f"{bucket.title()}:")
        print(f"  Current risk_acceptable=true: {s['risk_acceptable_true']}/{s['total']}")
        print(f"  Counterfactual (max_stop={cf['threshold']}%): {cf['would_pass']}/{s['total']} (+{cf['delta_vs_current']})")
        cf_atr = s.get("counterfactual_atr_fallback")
        if cf_atr:
            print(f"  Counterfactual ATR-fallback: {cf_atr['would_pass']}/{cf_atr['viable']} viable would pass")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
