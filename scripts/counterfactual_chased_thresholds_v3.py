#!/usr/bin/env python3
"""Counterfactual analysis for setup-specific chased thresholds.

This script answers:
1. How many candidates would be reclassified from "chased" to "late"?
2. Would any decision actually change in the CURRENT architecture?
3. Which candidates only change labels vs which remain blocked by non-timing reasons?
4. Where do report-state and recomputed-state diverge?

Important architectural note:
- In the current repo state, entry_state is computed in scanner/pipeline/output.py
  during report generation, after the decision layer has already assigned
  decision + decision_reasons.
- Therefore, changing chased thresholds alone should not change decisions in
  production, unless the pipeline architecture itself changes.

This script makes that explicit by reporting:
- reported decision
- reason-implied floor (approximation from non-timing reasons)
- label-only reclassifications
- report-vs-recomputed entry_state mismatches
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_REPORTS_DIR = Path("reports")
DEFAULT_OUTPUT_DIR = Path("reports/aux")
DEFAULT_MAX_RUNS = 7

CURRENT_THRESHOLD_PCT = 3.0
AT_TRIGGER_TOLERANCE_PCT = 0.25

DEFAULT_HYPOTHETICAL_THRESHOLDS = {
    "pullback": 8.0,
    "reversal": 12.0,
    "breakout": 5.0,
    "default": 3.0,
}

NO_TRADE_HARD_BLOCKERS = {
    "tradeability_fail",
    "risk_flag_blocked",
    "stop_distance_too_wide",
    "risk_reward_unattractive",
    "risk_data_insufficient",
    "price_past_target_1",
    "insufficient_edge",
}

WAIT_LEVEL_BLOCKERS = {
    "tradeability_marginal",
    "btc_regime_caution",
    "entry_not_confirmed",
    "breakout_not_confirmed",
    "retest_not_reclaimed",
    "rebound_not_confirmed",
    "effective_rr_insufficient",
}

TIMING_REASONS = {
    "entry_chased",
    "entry_late",
    "entry_too_early",
}


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Counterfactual analysis for setup-specific chased thresholds."
    )
    parser.add_argument(
        "--reports-dir",
        default=str(DEFAULT_REPORTS_DIR),
        help="Directory containing daily report JSON files (default: reports)",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_OUTPUT_DIR),
        help="Directory for generated analysis artifacts (default: reports/aux)",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=DEFAULT_MAX_RUNS,
        help="Number of most recent daily reports to analyze (default: 7)",
    )
    parser.add_argument(
        "--start-date",
        default=None,
        help="Optional lower bound date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--end-date",
        default=None,
        help="Optional upper bound date in YYYY-MM-DD",
    )
    parser.add_argument(
        "--pullback-threshold",
        type=float,
        default=DEFAULT_HYPOTHETICAL_THRESHOLDS["pullback"],
        help="Hypothetical chased threshold for pullback setups",
    )
    parser.add_argument(
        "--reversal-threshold",
        type=float,
        default=DEFAULT_HYPOTHETICAL_THRESHOLDS["reversal"],
        help="Hypothetical chased threshold for reversal setups",
    )
    parser.add_argument(
        "--breakout-threshold",
        type=float,
        default=DEFAULT_HYPOTHETICAL_THRESHOLDS["breakout"],
        help="Hypothetical chased threshold for breakout setups",
    )
    parser.add_argument(
        "--default-threshold",
        type=float,
        default=DEFAULT_HYPOTHETICAL_THRESHOLDS["default"],
        help="Fallback hypothetical chased threshold for unresolved setups",
    )
    parser.add_argument(
        "--focus-symbol",
        default=None,
        help="Optional symbol to highlight as case study, e.g. TAOUSDT",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: Optional[str]) -> Optional[datetime]:
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d")


def _is_daily_report_json(path: Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    if "_" in path.name:
        return False
    try:
        datetime.strptime(path.stem, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _to_optional_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric


def _round_opt(value: Optional[float], digits: int = 2) -> Optional[float]:
    if value is None:
        return None
    return round(value, digits)


def load_reports(
    reports_dir: Path,
    max_runs: int,
    start_date: Optional[str],
    end_date: Optional[str],
) -> list[dict[str, Any]]:
    """Load the most recent N daily report JSON files."""
    files = sorted(
        [p for p in reports_dir.iterdir() if p.is_file() and _is_daily_report_json(p)],
        key=lambda p: p.name,
    )
    start_dt = _parse_date(start_date)
    end_dt = _parse_date(end_date)

    filtered: list[Path] = []
    for path in files:
        report_dt = _parse_date(path.stem)
        if report_dt is None:
            continue
        if start_dt and report_dt < start_dt:
            continue
        if end_dt and report_dt > end_dt:
            continue
        filtered.append(path)

    selected = filtered[-max_runs:]
    reports: list[dict[str, Any]] = []
    for f in selected:
        with f.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        data["_source_file"] = f.name
        reports.append(data)
    return reports


def extract_candidates(report: dict[str, Any]) -> list[dict[str, Any]]:
    candidates = report.get("trade_candidates", [])
    report_date = report.get("meta", {}).get("date", "unknown")
    source_file = report.get("_source_file", "unknown")

    out: list[dict[str, Any]] = []
    for c in candidates:
        row = deepcopy(c)
        row["_report_date"] = report_date
        row["_source_file"] = source_file
        out.append(row)
    return out


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


def classify_entry_state(
    distance_pct: Optional[float],
    threshold_pct: float,
) -> Optional[str]:
    if distance_pct is None:
        return None
    if distance_pct < -AT_TRIGGER_TOLERANCE_PCT:
        return "early"
    if abs(distance_pct) <= AT_TRIGGER_TOLERANCE_PCT:
        return "at_trigger"
    if distance_pct <= threshold_pct:
        return "late"
    return "chased"


def get_threshold_for_setup(
    setup_bucket: str,
    hypothetical_thresholds: dict[str, float],
) -> float:
    return hypothetical_thresholds.get(setup_bucket, hypothetical_thresholds["default"])


def strip_timing_reasons(reasons: list[str]) -> list[str]:
    return [r for r in reasons if r not in TIMING_REASONS]


def categorize_blockers(reasons: list[str]) -> dict[str, list[str]]:
    hard = [r for r in reasons if r in NO_TRADE_HARD_BLOCKERS]
    wait = [r for r in reasons if r in WAIT_LEVEL_BLOCKERS]
    other = [r for r in reasons if r not in NO_TRADE_HARD_BLOCKERS and r not in WAIT_LEVEL_BLOCKERS]
    return {"hard": hard, "wait": wait, "other": other}


def infer_reason_implied_floor(non_timing_reasons: list[str]) -> str:
    """Approximate floor implied by reasons, not a full decision replay."""
    blocker_cats = categorize_blockers(non_timing_reasons)
    if blocker_cats["hard"]:
        return "NO_TRADE"
    if blocker_cats["wait"]:
        return "WAIT"
    if not non_timing_reasons:
        return "UNBLOCKED_BY_REASONS"
    return "UNKNOWN"


def _compute_unlock_path(candidate: dict[str, Any], blocker_cats: dict[str, list[str]]) -> str:
    if blocker_cats["hard"]:
        return f"remove_hard_blocker:{blocker_cats['hard'][0]}"
    if blocker_cats["wait"]:
        return f"remove_wait_blocker:{blocker_cats['wait'][0]}"
    if candidate.get("entry_state_current") == "chased":
        return "reclassify_chased"
    return "already_unblocked_by_reasons"


def analyze_candidate(
    candidate: dict[str, Any],
    hypothetical_thresholds: dict[str, float],
) -> dict[str, Any]:
    report_date = candidate.get("_report_date")
    symbol = candidate.get("symbol")
    setup_bucket = resolve_setup_bucket(candidate)
    decision = candidate.get("decision")
    reasons = list(candidate.get("decision_reasons") or [])

    distance_pct = _to_optional_float(candidate.get("distance_to_entry_pct"))
    entry_state_reported = candidate.get("entry_state")

    hypothetical_threshold = get_threshold_for_setup(setup_bucket, hypothetical_thresholds)
    current_state_recomputed = classify_entry_state(distance_pct, CURRENT_THRESHOLD_PCT)
    hypothetical_state = classify_entry_state(distance_pct, hypothetical_threshold)

    report_state_matches_recomputed = entry_state_reported == current_state_recomputed
    reclassified_from_reported = (
        entry_state_reported == "chased" and hypothetical_state != "chased"
    )
    reclassified_from_recomputed = (
        current_state_recomputed == "chased" and hypothetical_state != "chased"
    )

    non_timing_reasons = strip_timing_reasons(reasons)
    blocker_cats = categorize_blockers(non_timing_reasons)
    reason_implied_floor = infer_reason_implied_floor(non_timing_reasons)

    # Under the CURRENT architecture this should stay unchanged, because timing is
    # appended after the decision layer. We keep this explicit.
    decision_would_change_in_current_architecture = False

    unlock_path = _compute_unlock_path(
        {
            "entry_state_current": entry_state_reported,
        },
        blocker_cats,
    )

    return {
        "report_date": report_date,
        "symbol": symbol,
        "setup_bucket": setup_bucket,
        "setup_subtype": candidate.get("setup_subtype"),
        "decision_current": decision,
        "decision_reasons": reasons,
        "non_timing_reasons": non_timing_reasons,
        "distance_to_entry_pct": _round_opt(distance_pct),
        "entry_state_reported": entry_state_reported,
        "entry_state_recomputed_current": current_state_recomputed,
        "entry_state_hypothetical": hypothetical_state,
        "report_state_matches_recomputed": report_state_matches_recomputed,
        "reclassified_from_reported": reclassified_from_reported,
        "reclassified_from_recomputed": reclassified_from_recomputed,
        "reason_implied_floor": reason_implied_floor,
        "hard_blockers": blocker_cats["hard"],
        "wait_blockers": blocker_cats["wait"],
        "other_non_timing_reasons": blocker_cats["other"],
        "decision_would_change_in_current_architecture": decision_would_change_in_current_architecture,
        "unlock_path": unlock_path,
        "source_file": candidate.get("_source_file"),
    }


def aggregate_results(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_setup: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_date: dict[str, list[dict[str, Any]]] = defaultdict(list)

    mismatch_rows: list[dict[str, Any]] = []
    reclassified_rows: list[dict[str, Any]] = []
    label_only_rows: list[dict[str, Any]] = []

    decision_counts = Counter()
    reported_entry_state_counts = Counter()
    recomputed_entry_state_counts = Counter()
    hypothetical_entry_state_counts = Counter()
    reason_floor_counts = Counter()
    hard_blocker_counts = Counter()
    wait_blocker_counts = Counter()

    for row in rows:
        setup = row["setup_bucket"]
        date = row["report_date"]
        by_setup[setup].append(row)
        by_date[date].append(row)

        decision_counts[row["decision_current"] or "null"] += 1
        reported_entry_state_counts[row["entry_state_reported"] or "null"] += 1
        recomputed_entry_state_counts[row["entry_state_recomputed_current"] or "null"] += 1
        hypothetical_entry_state_counts[row["entry_state_hypothetical"] or "null"] += 1
        reason_floor_counts[row["reason_implied_floor"]] += 1

        for b in row["hard_blockers"]:
            hard_blocker_counts[b] += 1
        for b in row["wait_blockers"]:
            wait_blocker_counts[b] += 1

        if not row["report_state_matches_recomputed"]:
            mismatch_rows.append(row)
        if row["reclassified_from_reported"]:
            reclassified_rows.append(row)
            if row["decision_would_change_in_current_architecture"] is False:
                label_only_rows.append(row)

    def summarize_subset(subset: list[dict[str, Any]], label: str) -> dict[str, Any]:
        distances = [
            r["distance_to_entry_pct"]
            for r in subset
            if r["distance_to_entry_pct"] is not None and r["entry_state_reported"] == "chased"
        ]
        chased = sum(1 for r in subset if r["entry_state_reported"] == "chased")
        return {
            "label": label,
            "candidate_count": len(subset),
            "reported_entry_state_counts": dict(Counter(r["entry_state_reported"] or "null" for r in subset)),
            "recomputed_entry_state_counts": dict(Counter(r["entry_state_recomputed_current"] or "null" for r in subset)),
            "hypothetical_entry_state_counts": dict(Counter(r["entry_state_hypothetical"] or "null" for r in subset)),
            "decision_counts": dict(Counter(r["decision_current"] or "null" for r in subset)),
            "reason_implied_floor_counts": dict(Counter(r["reason_implied_floor"] for r in subset)),
            "reported_chased_count": chased,
            "reported_chased_pct": _round_opt((chased / len(subset) * 100.0) if subset else None),
            "median_reported_chased_distance_pct": _round_opt(
                None if not distances else sorted(distances)[len(distances) // 2]
            ),
            "reclassified_from_reported_count": sum(1 for r in subset if r["reclassified_from_reported"]),
            "report_state_mismatch_count": sum(1 for r in subset if not r["report_state_matches_recomputed"]),
        }

    return {
        "total_candidates": len(rows),
        "decision_counts": dict(decision_counts),
        "reported_entry_state_counts": dict(reported_entry_state_counts),
        "recomputed_entry_state_counts": dict(recomputed_entry_state_counts),
        "hypothetical_entry_state_counts": dict(hypothetical_entry_state_counts),
        "reason_implied_floor_counts": dict(reason_floor_counts),
        "hard_blocker_counts": dict(hard_blocker_counts.most_common()),
        "wait_blocker_counts": dict(wait_blocker_counts.most_common()),
        "reclassified_from_reported_count": len(reclassified_rows),
        "label_only_reclassification_count": len(label_only_rows),
        "report_state_mismatch_count": len(mismatch_rows),
        "report_state_mismatch_examples": mismatch_rows[:25],
        "reclassified_examples": reclassified_rows[:50],
        "setup_breakdown": {
            setup: summarize_subset(subset, setup)
            for setup, subset in sorted(by_setup.items())
        },
        "per_run_breakdown": {
            date: summarize_subset(subset, date)
            for date, subset in sorted(by_date.items())
        },
    }

def build_focus_symbol_summary(rows: list[dict[str, Any]], focus_symbol: str | None) -> dict[str, Any] | None:
    if not focus_symbol:
        return None

    normalized = focus_symbol.strip().upper()
    if not normalized:
        return None

    focus_rows = [row for row in rows if str(row.get("symbol") or "").upper() == normalized]
    if not focus_rows:
        return {
            "focus_symbol": normalized,
            "match_count": 0,
            "rows": [],
            "summary": {},
        }

    focus_rows = sorted(
        focus_rows,
        key=lambda r: (
            str(r.get("report_date") or ""),
            str(r.get("symbol") or ""),
            str(r.get("setup_bucket") or ""),
            str(r.get("setup_subtype") or ""),
        ),
    )

    summary = {
        "focus_symbol": normalized,
        "match_count": len(focus_rows),
        "decision_counts": dict(Counter(r.get("decision_current") or "null" for r in focus_rows)),
        "reported_entry_state_counts": dict(Counter(r.get("entry_state_reported") or "null" for r in focus_rows)),
        "hypothetical_entry_state_counts": dict(Counter(r.get("entry_state_hypothetical") or "null" for r in focus_rows)),
        "reason_implied_floor_counts": dict(Counter(r.get("reason_implied_floor") or "null" for r in focus_rows)),
        "reclassified_from_reported_count": sum(1 for r in focus_rows if r.get("reclassified_from_reported")),
        "report_state_mismatch_count": sum(1 for r in focus_rows if not r.get("report_state_matches_recomputed")),
    }

    return {
        "focus_symbol": normalized,
        "match_count": len(focus_rows),
        "rows": focus_rows,
        "summary": summary,
    }



def generate_json_output(
    analyzed_rows: list[dict[str, Any]],
    summary: dict[str, Any],
    hypothetical_thresholds: dict[str, float],
    focus_symbol_analysis: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis_type": "counterfactual_chased_thresholds",
        "architecture_note": (
            "entry_state is appended in output.py after the decision layer. "
            "Therefore threshold changes are label-only in the current architecture."
        ),
        "current_threshold_pct": CURRENT_THRESHOLD_PCT,
        "at_trigger_tolerance_pct": AT_TRIGGER_TOLERANCE_PCT,
        "hypothetical_thresholds": hypothetical_thresholds,
        "summary": summary,
        "focus_symbol_analysis": focus_symbol_analysis,
        "rows": analyzed_rows,
    }


def generate_markdown_output(
    json_output: dict[str, Any],
) -> str:
    summary = json_output["summary"]
    thresholds = json_output["hypothetical_thresholds"]

    lines: list[str] = []
    lines.append("# Counterfactual Chased Threshold Analysis")
    lines.append("")
    lines.append(f"- Generated: {json_output['generated_at_utc']}")
    lines.append(f"- Current threshold: {json_output['current_threshold_pct']}%")
    lines.append(
        "- Hypothetical thresholds: "
        f"pullback={thresholds['pullback']}%, "
        f"reversal={thresholds['reversal']}%, "
        f"breakout={thresholds['breakout']}%, "
        f"default={thresholds['default']}%"
    )
    lines.append("")
    lines.append("## Headline findings")
    lines.append("")
    lines.append(f"- Total candidates: {summary['total_candidates']}")
    lines.append(f"- Reclassified from reported chased: {summary['reclassified_from_reported_count']}")
    lines.append(f"- Label-only reclassifications in current architecture: {summary['label_only_reclassification_count']}")
    lines.append(f"- Report vs recomputed entry_state mismatches: {summary['report_state_mismatch_count']}")
    lines.append("")
    lines.append("## Decision counts")
    lines.append("")
    for key, value in summary["decision_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Entry-state counts")
    lines.append("")
    lines.append("### Reported")
    lines.append("")
    for key, value in summary["reported_entry_state_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("### Recomputed with current threshold")
    lines.append("")
    for key, value in summary["recomputed_entry_state_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("### Hypothetical")
    lines.append("")
    for key, value in summary["hypothetical_entry_state_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Reason-implied floor counts")
    lines.append("")
    for key, value in summary["reason_implied_floor_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Most common hard blockers")
    lines.append("")
    for key, value in list(summary["hard_blocker_counts"].items())[:15]:
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Most common wait-level blockers")
    lines.append("")
    for key, value in list(summary["wait_blocker_counts"].items())[:15]:
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Setup breakdown")
    lines.append("")
    lines.append("| Setup | Candidates | Reported chased | Reclassified | State mismatches | Reason floor: NO_TRADE | Reason floor: WAIT | Reason floor: UNBLOCKED |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for setup, row in summary["setup_breakdown"].items():
        floor_counts = row["reason_implied_floor_counts"]
        lines.append(
            f"| {setup} | {row['candidate_count']} | {row['reported_chased_count']} | "
            f"{row['reclassified_from_reported_count']} | {row['report_state_mismatch_count']} | "
            f"{floor_counts.get('NO_TRADE', 0)} | {floor_counts.get('WAIT', 0)} | "
            f"{floor_counts.get('UNBLOCKED_BY_REASONS', 0)} |"
        )
    lines.append("")
    lines.append("## Per-run breakdown")
    lines.append("")
    lines.append("| Date | Candidates | Reported chased | Reclassified | State mismatches |")
    lines.append("|---|---:|---:|---:|---:|")
    for date, row in summary["per_run_breakdown"].items():
        lines.append(
            f"| {date} | {row['candidate_count']} | {row['reported_chased_count']} | "
            f"{row['reclassified_from_reported_count']} | {row['report_state_mismatch_count']} |"
        )
    lines.append("")
    if summary["report_state_mismatch_examples"]:
        lines.append("## Report vs recomputed mismatch examples")
        lines.append("")
        lines.append("| Date | Symbol | Setup | Distance % | Reported state | Recomputed state |")
        lines.append("|---|---|---|---:|---|---|")
        for row in summary["report_state_mismatch_examples"][:15]:
            lines.append(
                f"| {row['report_date']} | {row['symbol']} | {row['setup_bucket']} | "
                f"{row['distance_to_entry_pct'] if row['distance_to_entry_pct'] is not None else ''} | "
                f"{row['entry_state_reported'] or ''} | {row['entry_state_recomputed_current'] or ''} |"
            )
        lines.append("")
    if summary["reclassified_examples"]:
        lines.append("## Reclassified examples")
        lines.append("")
        lines.append("| Date | Symbol | Setup | Decision | Distance % | Reported state | Hypothetical state | Reason-implied floor |")
        lines.append("|---|---|---|---|---:|---|---|---|")
        for row in summary["reclassified_examples"][:20]:
            lines.append(
                f"| {row['report_date']} | {row['symbol']} | {row['setup_bucket']} | "
                f"{row['decision_current']} | "
                f"{row['distance_to_entry_pct'] if row['distance_to_entry_pct'] is not None else ''} | "
                f"{row['entry_state_reported'] or ''} | {row['entry_state_hypothetical'] or ''} | "
                f"{row['reason_implied_floor']} |"
            )
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    hypothetical_thresholds = {
        "pullback": float(args.pullback_threshold),
        "reversal": float(args.reversal_threshold),
        "breakout": float(args.breakout_threshold),
        "default": float(args.default_threshold),
    }

    reports = load_reports(
        reports_dir=reports_dir,
        max_runs=args.max_runs,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if not reports:
        raise SystemExit("No matching daily report JSON files found.")

    candidates: list[dict[str, Any]] = []
    for report in reports:
        candidates.extend(extract_candidates(report))

    analyzed_rows = [analyze_candidate(c, hypothetical_thresholds) for c in candidates]
    summary = aggregate_results(analyzed_rows)
    focus_symbol_analysis = build_focus_symbol_summary(analyzed_rows, args.focus_symbol)
    json_output = generate_json_output(
        analyzed_rows,
        summary,
        hypothetical_thresholds,
        focus_symbol_analysis=focus_symbol_analysis,
    )
    markdown_output = generate_markdown_output(json_output)

    latest_date = reports[-1].get("meta", {}).get("date") or Path(reports[-1]["_source_file"]).stem
    stem = f"counterfactual_chased_{latest_date}"

    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(json_output, f, indent=2, ensure_ascii=False)

    with md_path.open("w", encoding="utf-8") as f:
        f.write(markdown_output + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
