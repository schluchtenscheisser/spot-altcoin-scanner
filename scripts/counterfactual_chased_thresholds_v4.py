#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


ENTRY_AT_TRIGGER_TOLERANCE_PCT = 0.25
DEFAULT_CURRENT_THRESHOLD_PCT = 3.0
DEFAULT_THRESHOLDS = {
    "pullback": 8.0,
    "reversal": 12.0,
    "breakout": 5.0,
    "other": DEFAULT_CURRENT_THRESHOLD_PCT,
}

TIMING_REASONS = {"entry_too_early", "entry_late", "entry_chased"}
HARD_NO_TRADE_REASONS = {
    "tradeability_fail",
    "risk_flag_blocked",
    "stop_distance_too_wide",
    "risk_reward_unattractive",
    "risk_data_insufficient",
    "price_past_target_1",
    "insufficient_edge",
}
WAIT_BLOCKING_REASONS = HARD_NO_TRADE_REASONS | {
    "effective_rr_insufficient",
    "entry_not_confirmed",
    "breakout_not_confirmed",
    "retest_not_reclaimed",
    "rebound_not_confirmed",
    "btc_regime_caution",
}


@dataclass
class CandidateRow:
    report_date: str
    symbol: str
    setup_id: str | None
    setup_bucket: str
    decision_current: str | None
    decision_reasons: list[str]
    non_timing_reasons: list[str]
    reported_entry_state: str | None
    recomputed_entry_state: str | None
    current_price_usdt: float | None
    entry_price_usdt: float | None
    distance_to_entry_pct: float | None
    rr_to_target_2: float | None
    stop_price_initial: float | None
    entry_ready: bool | None
    tradeability_class: str | None
    btc_regime_state: str | None
    risk_acceptable: bool | None
    hypothetical_entry_state: str | None = None
    reclassified: bool = False
    reason_implied_floor: str | None = None
    unlock_path: str | None = None
    report_state_matches_recomputed: bool | None = None
    source_path: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Counterfactual analysis for setup-specific chased thresholds."
    )
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--output-dir", default="reports/aux")
    parser.add_argument("--runs", type=int, default=7)
    parser.add_argument("--start-date", default=None)
    parser.add_argument("--end-date", default=None)
    parser.add_argument("--pullback-threshold", type=float, default=8.0)
    parser.add_argument("--reversal-threshold", type=float, default=12.0)
    parser.add_argument("--breakout-threshold", type=float, default=5.0)
    parser.add_argument("--other-threshold", type=float, default=DEFAULT_CURRENT_THRESHOLD_PCT)
    parser.add_argument("--focus-symbol", default=None)
    return parser.parse_args()


def is_daily_report_json(path: Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    if "_" in path.name:
        return False
    try:
        datetime.strptime(path.stem, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def parse_report_date(path: Path) -> str:
    return path.stem


def parse_iso_date(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d")


def coerce_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def coerce_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    return None


def coerce_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def coerce_list_of_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return []


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def iter_dict_nodes(obj: Any, path: str = "$") -> Iterable[tuple[dict[str, Any], str]]:
    if isinstance(obj, dict):
        yield obj, path
        for key, value in obj.items():
            yield from iter_dict_nodes(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from iter_dict_nodes(value, f"{path}[{idx}]")


def looks_like_candidate(node: dict[str, Any]) -> bool:
    return "symbol" in node and "decision" in node and "entry_state" in node


def normalize_setup_bucket(setup_id: str | None) -> str:
    if not setup_id:
        return "other"
    s = setup_id.lower()
    if "pullback" in s:
        return "pullback"
    if "reversal" in s:
        return "reversal"
    if "breakout" in s:
        return "breakout"
    return "other"


def first_non_null_float(node: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = coerce_float(node.get(key))
        if value is not None:
            return value
    return None


def classify_entry_state(distance_to_entry_pct: float | None, chased_threshold_pct: float) -> str | None:
    if distance_to_entry_pct is None:
        return None
    if distance_to_entry_pct < -ENTRY_AT_TRIGGER_TOLERANCE_PCT:
        return "early"
    if abs(distance_to_entry_pct) <= ENTRY_AT_TRIGGER_TOLERANCE_PCT:
        return "at_trigger"
    if distance_to_entry_pct <= chased_threshold_pct:
        return "late"
    return "chased"


def implied_decision_floor(non_timing_reasons: list[str]) -> str:
    if any(reason in HARD_NO_TRADE_REASONS for reason in non_timing_reasons):
        return "NO_TRADE"
    if any(reason in WAIT_BLOCKING_REASONS for reason in non_timing_reasons):
        return "WAIT"
    if non_timing_reasons:
        return "WAIT"
    return "UNBLOCKED_BY_REASONS"


def focus_row_sort_key(row: CandidateRow) -> tuple[Any, ...]:
    return (
        row.report_date,
        row.setup_bucket,
        row.setup_id or "",
        row.symbol,
    )


def extract_trade_candidates(report_data: Any) -> list[dict[str, Any]]:
    if not isinstance(report_data, dict):
        return []
    trade_candidates = report_data.get("trade_candidates")
    if isinstance(trade_candidates, list):
        return [row for row in trade_candidates if isinstance(row, dict)]
    return []


def select_report_files(
    reports_dir: Path,
    runs: int,
    start_date: str | None,
    end_date: str | None,
) -> list[Path]:
    files = sorted(
        [p for p in reports_dir.iterdir() if p.is_file() and is_daily_report_json(p)],
        key=lambda p: p.name,
    )
    start_dt = parse_iso_date(start_date)
    end_dt = parse_iso_date(end_date)

    filtered: list[Path] = []
    for path in files:
        report_dt = parse_iso_date(parse_report_date(path))
        if report_dt is None:
            continue
        if start_dt and report_dt < start_dt:
            continue
        if end_dt and report_dt > end_dt:
            continue
        filtered.append(path)
    return filtered[-runs:]


def extract_rows_from_report(report_data: Any, report_date: str) -> list[CandidateRow]:
    trade_candidates = extract_trade_candidates(report_data)
    rows: list[CandidateRow] = []

    for idx, node in enumerate(trade_candidates):
        if not looks_like_candidate(node):
            continue

        setup_id = coerce_str(node.get("setup_id")) or coerce_str(node.get("best_setup_type"))
        setup_bucket = normalize_setup_bucket(setup_id)
        decision_reasons = coerce_list_of_str(node.get("decision_reasons"))
        non_timing_reasons = [reason for reason in decision_reasons if reason not in TIMING_REASONS]

        reported_entry_state = coerce_str(node.get("entry_state"))
        distance_to_entry_pct = first_non_null_float(
            node,
            ["distance_to_entry_pct", "entry_distance_pct", "distance_from_entry_pct"],
        )
        recomputed_entry_state = classify_entry_state(
            distance_to_entry_pct,
            DEFAULT_CURRENT_THRESHOLD_PCT,
        )

        rows.append(
            CandidateRow(
                report_date=report_date,
                symbol=str(node.get("symbol") or "").strip(),
                setup_id=setup_id,
                setup_bucket=setup_bucket,
                decision_current=coerce_str(node.get("decision")),
                decision_reasons=decision_reasons,
                non_timing_reasons=non_timing_reasons,
                reported_entry_state=reported_entry_state,
                recomputed_entry_state=recomputed_entry_state,
                current_price_usdt=first_non_null_float(node, ["current_price_usdt", "price_usdt", "current_price", "price"]),
                entry_price_usdt=first_non_null_float(node, ["entry_price_usdt", "entry_price", "planned_entry_price", "entry_trigger", "entry"]),
                distance_to_entry_pct=distance_to_entry_pct,
                rr_to_target_2=first_non_null_float(node, ["rr_to_target_2"]),
                stop_price_initial=first_non_null_float(node, ["stop_price_initial"]),
                entry_ready=coerce_bool(node.get("entry_ready")),
                tradeability_class=coerce_str(node.get("tradeability_class")),
                btc_regime_state=coerce_str(node.get("btc_regime_state")) or coerce_str(node.get("btc_regime")),
                risk_acceptable=coerce_bool(node.get("risk_acceptable")),
                report_state_matches_recomputed=(reported_entry_state == recomputed_entry_state),
                source_path=f"$.trade_candidates[{idx}]",
            )
        )
    return rows


def apply_counterfactual(rows: list[CandidateRow], thresholds: dict[str, float]) -> list[CandidateRow]:
    out: list[CandidateRow] = []
    for row in rows:
        threshold = thresholds.get(row.setup_bucket, thresholds["other"])
        hypothetical_state = classify_entry_state(row.distance_to_entry_pct, threshold)
        reclassified = (
            row.reported_entry_state == "chased"
            and hypothetical_state is not None
            and hypothetical_state != "chased"
        )

        unlock_path = None
        if reclassified and not row.non_timing_reasons:
            unlock_path = "reclassify_chased"
        elif reclassified:
            unlock_path = "blocked_by_non_timing_reasons"

        reason_floor = implied_decision_floor(row.non_timing_reasons)

        out.append(
            CandidateRow(
                **{
                    **asdict(row),
                    "hypothetical_entry_state": hypothetical_state,
                    "reclassified": reclassified,
                    "reason_implied_floor": reason_floor,
                    "unlock_path": unlock_path,
                }
            )
        )
    return out


def summarize(rows: list[CandidateRow], thresholds: dict[str, float], focus_symbol: str | None) -> dict[str, Any]:
    total_candidates = len(rows)
    reported_chased = [r for r in rows if r.reported_entry_state == "chased"]
    reclassified = [r for r in rows if r.reclassified]
    label_only = [
        r for r in reclassified
        if r.reason_implied_floor in {"NO_TRADE", "WAIT", "UNBLOCKED_BY_REASONS"}
    ]
    mismatches = [r for r in rows if r.report_state_matches_recomputed is False]

    reason_counter: Counter[str] = Counter()
    for row in rows:
        for reason in row.non_timing_reasons:
            reason_counter[reason] += 1

    setup_breakdown: dict[str, dict[str, Any]] = {}
    grouped: dict[str, list[CandidateRow]] = defaultdict(list)
    for row in rows:
        grouped[row.setup_bucket].append(row)

    for setup_bucket, bucket_rows in grouped.items():
        setup_breakdown[setup_bucket] = {
            "candidates": len(bucket_rows),
            "reported_chased": sum(r.reported_entry_state == "chased" for r in bucket_rows),
            "reclassified": sum(r.reclassified for r in bucket_rows),
            "threshold_used": thresholds.get(setup_bucket, thresholds["other"]),
        }

    focus_symbol_analysis = None
    if focus_symbol:
        focus_rows = [r for r in rows if r.symbol.upper() == focus_symbol.upper()]
        focus_rows = sorted(focus_rows, key=focus_row_sort_key)
        focus_symbol_analysis = {
            "symbol": focus_symbol.upper(),
            "count": len(focus_rows),
            "rows": [asdict(r) for r in focus_rows],
            "summary": {
                "reported_chased": sum(r.reported_entry_state == "chased" for r in focus_rows),
                "reclassified": sum(r.reclassified for r in focus_rows),
                "by_setup_bucket": dict(Counter(r.setup_bucket for r in focus_rows)),
                "reason_implied_floor_counts": dict(Counter(r.reason_implied_floor for r in focus_rows)),
            },
        }

    return {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "thresholds": thresholds,
        "total_candidates": total_candidates,
        "reported_chased": len(reported_chased),
        "reclassified_from_reported_chased": len(reclassified),
        "label_only_reclassifications": len(label_only),
        "report_vs_recomputed_entry_state_mismatches": len(mismatches),
        "reason_counts_non_timing": dict(reason_counter.most_common()),
        "setup_breakdown": setup_breakdown,
        "focus_symbol_analysis": focus_symbol_analysis,
        "unblocked_examples": [asdict(r) for r in rows if r.reason_implied_floor == "UNBLOCKED_BY_REASONS"][:20],
        "report_state_mismatch_examples": [asdict(r) for r in mismatches[:20]],
    }


def format_float(value: float | None, digits: int = 2) -> str:
    if value is None:
        return ""
    return f"{value:.{digits}f}"


def render_focus_symbol_markdown(focus_symbol_analysis: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    symbol = focus_symbol_analysis["symbol"]
    summary = focus_symbol_analysis["summary"]
    rows = focus_symbol_analysis["rows"]

    lines.append(f"## Focus Symbol: {symbol}")
    lines.append("")
    lines.append(f"- Rows: {focus_symbol_analysis['count']}")
    lines.append(f"- Reported chased: {summary['reported_chased']}")
    lines.append(f"- Reclassified: {summary['reclassified']}")
    lines.append(f"- By setup bucket: {json.dumps(summary['by_setup_bucket'], ensure_ascii=False)}")
    lines.append(f"- Reason-implied floors: {json.dumps(summary['reason_implied_floor_counts'], ensure_ascii=False)}")
    lines.append("")

    lines.append("| Date | Setup | Decision | Dist % | Reported | Hypothetical | RR2 | Stop | Entry ready | Tradeability | BTC regime | Floor | Non-timing reasons |")
    lines.append("|---|---|---|---:|---|---|---:|---:|---|---|---|---|---|")
    for row in rows:
        lines.append(
            "| {date} | {setup} | {decision} | {dist} | {reported} | {hypo} | {rr2} | {stop} | {entry_ready} | {tradeability} | {btc} | {floor} | {reasons} |".format(
                date=row["report_date"],
                setup=row["setup_id"] or row["setup_bucket"],
                decision=row["decision_current"] or "",
                dist=format_float(row["distance_to_entry_pct"]),
                reported=row["reported_entry_state"] or "",
                hypo=row["hypothetical_entry_state"] or "",
                rr2=format_float(row["rr_to_target_2"]),
                stop=format_float(row["stop_price_initial"], digits=4),
                entry_ready=("true" if row["entry_ready"] is True else "false" if row["entry_ready"] is False else ""),
                tradeability=row["tradeability_class"] or "",
                btc=row["btc_regime_state"] or "",
                floor=row["reason_implied_floor"] or "",
                reasons=", ".join(row["non_timing_reasons"]),
            )
        )
    lines.append("")
    return lines


def render_markdown(summary: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append("# Counterfactual Chased Threshold Analysis")
    lines.append("")
    lines.append(f"- Generated: {summary['generated_at_utc']}")
    lines.append(f"- Total candidates: {summary['total_candidates']}")
    lines.append(f"- Reported chased: {summary['reported_chased']}")
    lines.append(f"- Reclassified from reported chased: {summary['reclassified_from_reported_chased']}")
    lines.append(f"- Label-only reclassifications: {summary['label_only_reclassifications']}")
    lines.append(f"- Report vs recomputed entry_state mismatches: {summary['report_vs_recomputed_entry_state_mismatches']}")
    lines.append("")
    lines.append("## Thresholds used")
    lines.append("")
    for key, value in summary["thresholds"].items():
        lines.append(f"- {key}: {value:.2f}%")
    lines.append("")
    lines.append("## Non-timing blocker counts")
    lines.append("")
    for key, value in summary["reason_counts_non_timing"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")
    lines.append("## Setup breakdown")
    lines.append("")
    lines.append("| Setup | Candidates | Reported chased | Reclassified | Threshold |")
    lines.append("|---|---:|---:|---:|---:|")
    for setup, row in sorted(summary["setup_breakdown"].items()):
        lines.append(
            f"| {setup} | {row['candidates']} | {row['reported_chased']} | {row['reclassified']} | {row['threshold_used']:.2f}% |"
        )
    lines.append("")

    if summary.get("focus_symbol_analysis"):
        lines.extend(render_focus_symbol_markdown(summary["focus_symbol_analysis"]))

    return "\n".join(lines)


def main() -> int:
    args = parse_args()

    thresholds = {
        "pullback": args.pullback_threshold,
        "reversal": args.reversal_threshold,
        "breakout": args.breakout_threshold,
        "other": args.other_threshold,
    }

    reports_dir = Path(args.reports_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report_files = select_report_files(
        reports_dir=reports_dir,
        runs=args.runs,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    if not report_files:
        raise SystemExit("No matching report JSON files found.")

    rows: list[CandidateRow] = []
    for report_file in report_files:
        report_date = parse_report_date(report_file)
        report_data = load_json(report_file)
        rows.extend(extract_rows_from_report(report_data, report_date))

    rows = apply_counterfactual(rows, thresholds)
    summary = summarize(rows, thresholds, args.focus_symbol)

    latest_date = parse_report_date(report_files[-1])
    stem = f"counterfactual_chased_{latest_date}"

    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with md_path.open("w", encoding="utf-8") as f:
        f.write(render_markdown(summary) + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
