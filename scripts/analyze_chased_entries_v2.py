#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


DISTANCE_BUCKETS: list[tuple[str, float | None, float | None]] = [
    ("0-3%", 0.0, 3.0),
    ("3-7%", 3.0, 7.0),
    ("7-15%", 7.0, 15.0),
    (">15%", 15.0, None),
]


@dataclass
class CandidateRow:
    report_date: str
    symbol: str
    decision: str | None
    setup_id: str | None
    entry_state: str | None
    distance_to_entry_pct: float | None
    current_price: float | None
    planned_entry_price: float | None
    decision_reasons: list[str]
    source_path: str


@dataclass
class SetupHint:
    report_date: str
    symbol: str
    setup_id: str | None
    source_path: str
    inferred_from_path: bool


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze chased-entry behavior across recent Spot Altcoin Scanner reports."
    )
    parser.add_argument(
        "--reports-dir",
        default="reports",
        help="Directory containing YYYY-MM-DD.json report files (default: reports)",
    )
    parser.add_argument(
        "--output-dir",
        default="reports/aux",
        help="Directory for generated analysis artifacts (default: reports/aux)",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=7,
        help="Number of most recent daily report JSON files to analyze (default: 7)",
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
    return parser.parse_args()


def is_daily_report_json(path: Path) -> bool:
    if path.suffix.lower() != ".json":
        return False
    name = path.name
    if "_" in name:
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


def coerce_list_of_str(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, str):
        return [part.strip() for part in value.split(",") if part.strip()]
    return [str(value)]


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


def first_non_null_float(node: dict[str, Any], keys: list[str]) -> float | None:
    for key in keys:
        value = coerce_float(node.get(key))
        if value is not None:
            return value
    return None


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


def infer_setup_id_from_path(path: str) -> str | None:
    p = path.lower()
    if "pullback" in p:
        return "pullback"
    if "reversal" in p:
        return "reversal"
    if "breakout" in p:
        return "breakout"
    return None


def canonicalize_setup_id(raw: str | None, source_path: str = "") -> str | None:
    if raw:
        value = str(raw).strip()
        if value:
            return value
    return infer_setup_id_from_path(source_path)


def looks_like_trade_candidate(node: dict[str, Any], path: str) -> bool:
    if "symbol" not in node or "decision" not in node or "entry_state" not in node:
        return False
    # We prefer actual trade_candidates, but keep fallback for schema drift.
    return ".trade_candidates[" in path or True


def looks_like_setup_hint(node: dict[str, Any], path: str) -> bool:
    if "symbol" not in node:
        return False
    if "setup_id" in node or "setup_type" in node:
        return True
    inferred = infer_setup_id_from_path(path)
    return inferred is not None


def extract_trade_candidates(report_data: Any, report_date: str) -> list[CandidateRow]:
    rows: list[CandidateRow] = []

    for node, source_path in iter_dict_nodes(report_data):
        if not looks_like_trade_candidate(node, source_path):
            continue

        symbol = str(node.get("symbol") or "").strip()
        if not symbol:
            continue

        decision = str(node.get("decision")) if node.get("decision") is not None else None
        entry_state = (
            str(node.get("entry_state")) if node.get("entry_state") is not None else None
        )
        setup_id = canonicalize_setup_id(
            node.get("setup_id") or node.get("setup_type"),
            source_path,
        )

        planned_entry_price = first_non_null_float(
            node,
            ["entry_price", "entry", "planned_entry_price", "entry_trigger", "trigger_price"],
        )
        current_price = first_non_null_float(
            node,
            ["current_price", "price", "market_price", "last_price", "close"],
        )
        distance_to_entry_pct = first_non_null_float(
            node,
            ["distance_to_entry_pct", "entry_distance_pct", "distance_from_entry_pct"],
        )

        rows.append(
            CandidateRow(
                report_date=report_date,
                symbol=symbol,
                decision=decision,
                setup_id=setup_id,
                entry_state=entry_state,
                distance_to_entry_pct=distance_to_entry_pct,
                current_price=current_price,
                planned_entry_price=planned_entry_price,
                decision_reasons=coerce_list_of_str(node.get("decision_reasons")),
                source_path=source_path,
            )
        )

    return rows


def extract_setup_hints(report_data: Any, report_date: str) -> list[SetupHint]:
    hints: list[SetupHint] = []

    for node, source_path in iter_dict_nodes(report_data):
        if not looks_like_setup_hint(node, source_path):
            continue

        symbol = str(node.get("symbol") or "").strip()
        if not symbol:
            continue

        explicit = node.get("setup_id") or node.get("setup_type")
        setup_id = canonicalize_setup_id(explicit, source_path)
        if not setup_id:
            continue

        hints.append(
            SetupHint(
                report_date=report_date,
                symbol=symbol,
                setup_id=setup_id,
                source_path=source_path,
                inferred_from_path=explicit is None,
            )
        )

    return deduplicate_setup_hints(hints)


def deduplicate_setup_hints(hints: list[SetupHint]) -> list[SetupHint]:
    chosen: dict[tuple[str, str, str], SetupHint] = {}
    for hint in hints:
        key = (hint.report_date, hint.symbol, hint.setup_id or "")
        existing = chosen.get(key)
        if existing is None:
            chosen[key] = hint
            continue

        existing_score = setup_hint_quality(existing)
        hint_score = setup_hint_quality(hint)
        if hint_score > existing_score:
            chosen[key] = hint

    return list(chosen.values())


def setup_hint_quality(hint: SetupHint) -> tuple[int, int]:
    explicit_bonus = 1 if not hint.inferred_from_path else 0
    trade_path_bonus = 1 if ".trade_candidates[" in hint.source_path else 0
    return (explicit_bonus, trade_path_bonus)


def build_setup_index(hints: list[SetupHint]) -> dict[tuple[str, str], list[SetupHint]]:
    index: dict[tuple[str, str], list[SetupHint]] = defaultdict(list)
    for hint in hints:
        index[(hint.report_date, hint.symbol)].append(hint)

    for key in index:
        index[key] = sorted(index[key], key=setup_hint_quality, reverse=True)

    return index


def resolve_candidate_setup(
    candidate: CandidateRow,
    setup_index: dict[tuple[str, str], list[SetupHint]],
) -> tuple[CandidateRow, str]:
    if candidate.setup_id:
        return candidate, "already_present"

    matches = setup_index.get((candidate.report_date, candidate.symbol), [])
    if not matches:
        return candidate, "unresolved"

    if len(matches) == 1:
        candidate.setup_id = matches[0].setup_id
        return candidate, "joined_unique"

    preferred = choose_best_setup_match(matches, candidate)
    candidate.setup_id = preferred.setup_id
    return candidate, "joined_multi"


def choose_best_setup_match(matches: list[SetupHint], candidate: CandidateRow) -> SetupHint:
    # For now prefer the richest / most explicit hint.
    # This keeps behavior deterministic and debuggable.
    return sorted(matches, key=setup_hint_quality, reverse=True)[0]


def dedup_key(row: CandidateRow) -> tuple[Any, ...]:
    distance = None if row.distance_to_entry_pct is None else round(row.distance_to_entry_pct, 6)
    planned = None if row.planned_entry_price is None else round(row.planned_entry_price, 12)
    current = None if row.current_price is None else round(row.current_price, 12)

    return (
        row.report_date,
        row.symbol,
        row.decision,
        row.entry_state,
        distance,
        planned,
        current,
        row.setup_id or "",
    )


def is_better_string(current: str | None, candidate: str | None) -> bool:
    if not candidate:
        return False
    if not current:
        return True
    return len(candidate) > len(current)


def choose_preferred_source_path(current: str, candidate: str) -> str:
    current_trade = ".trade_candidates[" in current
    candidate_trade = ".trade_candidates[" in candidate

    if candidate_trade and not current_trade:
        return candidate
    if current_trade and not candidate_trade:
        return current
    return candidate if len(candidate) > len(current) else current


def merge_rows(base: CandidateRow, incoming: CandidateRow) -> CandidateRow:
    merged = CandidateRow(
        report_date=base.report_date,
        symbol=base.symbol,
        decision=base.decision,
        setup_id=base.setup_id,
        entry_state=base.entry_state,
        distance_to_entry_pct=base.distance_to_entry_pct,
        current_price=base.current_price,
        planned_entry_price=base.planned_entry_price,
        decision_reasons=list(base.decision_reasons),
        source_path=base.source_path,
    )

    if is_better_string(merged.setup_id, incoming.setup_id):
        merged.setup_id = incoming.setup_id

    if merged.distance_to_entry_pct is None and incoming.distance_to_entry_pct is not None:
        merged.distance_to_entry_pct = incoming.distance_to_entry_pct

    if merged.current_price is None and incoming.current_price is not None:
        merged.current_price = incoming.current_price

    if merged.planned_entry_price is None and incoming.planned_entry_price is not None:
        merged.planned_entry_price = incoming.planned_entry_price

    if is_better_string(merged.decision, incoming.decision):
        merged.decision = incoming.decision

    if is_better_string(merged.entry_state, incoming.entry_state):
        merged.entry_state = incoming.entry_state

    merged.source_path = choose_preferred_source_path(merged.source_path, incoming.source_path)

    merged_reasons: list[str] = []
    seen = set()
    for reason in list(merged.decision_reasons) + list(incoming.decision_reasons):
        if reason not in seen:
            seen.add(reason)
            merged_reasons.append(reason)
    merged.decision_reasons = merged_reasons

    return merged


def deduplicate_rows(rows: list[CandidateRow]) -> list[CandidateRow]:
    merged_rows: dict[tuple[Any, ...], CandidateRow] = {}

    for row in rows:
        key = dedup_key(row)
        existing = merged_rows.get(key)
        if existing is None:
            merged_rows[key] = row
        else:
            merged_rows[key] = merge_rows(existing, row)

    return list(merged_rows.values())


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


def median_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    return float(statistics.median(values))


def p75_or_none(values: list[float]) -> float | None:
    if not values:
        return None
    if len(values) == 1:
        return float(values[0])
    return float(statistics.quantiles(values, n=4, method="inclusive")[2])


def safe_pct(numerator: int, denominator: int) -> float | None:
    if denominator == 0:
        return None
    return (numerator / denominator) * 100.0


def classify_distance_bucket(distance: float | None) -> str:
    if distance is None:
        return "unknown"
    for label, lower, upper in DISTANCE_BUCKETS:
        if lower is not None and distance < lower:
            continue
        if upper is None and lower is not None and distance >= lower:
            return label
        if lower is not None and upper is not None and lower <= distance < upper:
            return label
    return "unknown"


def bucket_counter(rows: list[CandidateRow], chased_only: bool = False) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        if chased_only and row.entry_state != "chased":
            continue
        counter[classify_distance_bucket(row.distance_to_entry_pct)] += 1

    ordered = {label: counter.get(label, 0) for label, _, _ in DISTANCE_BUCKETS}
    if counter.get("unknown", 0):
        ordered["unknown"] = counter["unknown"]
    return ordered


def summarize_subset(rows: list[CandidateRow], label: str) -> dict[str, Any]:
    rows_by_date: dict[str, list[CandidateRow]] = defaultdict(list)
    for row in rows:
        rows_by_date[row.report_date].append(row)

    decision_counter: Counter[str] = Counter()
    entry_state_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()

    for row in rows:
        decision_counter[row.decision or "null"] += 1
        entry_state_counter[row.entry_state or "null"] += 1
        for reason in row.decision_reasons:
            reason_counter[reason] += 1

    per_run: list[dict[str, Any]] = []
    for report_date in sorted(rows_by_date):
        day_rows = rows_by_date[report_date]
        chased_rows = [r for r in day_rows if r.entry_state == "chased"]
        distances = [
            r.distance_to_entry_pct
            for r in chased_rows
            if r.distance_to_entry_pct is not None
        ]
        per_run.append(
            {
                "report_date": report_date,
                "candidate_count": len(day_rows),
                "decision_counts": dict(Counter((r.decision or "null") for r in day_rows)),
                "entry_state_counts": dict(Counter((r.entry_state or "null") for r in day_rows)),
                "chased_count": len(chased_rows),
                "chased_pct": safe_pct(len(chased_rows), len(day_rows)),
                "median_chased_distance_to_entry_pct": median_or_none(distances),
                "p75_chased_distance_to_entry_pct": p75_or_none(distances),
                "distance_buckets_all": bucket_counter(day_rows, chased_only=False),
                "distance_buckets_chased": bucket_counter(day_rows, chased_only=True),
            }
        )

    chased_examples = sorted(
        [r for r in rows if r.entry_state == "chased"],
        key=lambda r: (r.report_date, -(r.distance_to_entry_pct or -1.0), r.symbol, r.setup_id or ""),
    )[:20]

    return {
        "label": label,
        "candidate_count": len(rows),
        "decision_counts": dict(decision_counter),
        "entry_state_counts": dict(entry_state_counter),
        "reason_counts": dict(reason_counter.most_common()),
        "distance_buckets_all": bucket_counter(rows, chased_only=False),
        "distance_buckets_chased": bucket_counter(rows, chased_only=True),
        "per_run": per_run,
        "sample_chased_candidates": [asdict(r) for r in chased_examples],
    }


def build_summary(rows: list[CandidateRow], join_stats: dict[str, Any]) -> dict[str, Any]:
    rows_by_date: dict[str, list[CandidateRow]] = defaultdict(list)
    for row in rows:
        rows_by_date[row.report_date].append(row)

    setup_counts: dict[str, Counter[str]] = defaultdict(Counter)
    setup_distances: dict[str, list[float]] = defaultdict(list)
    reason_counter: Counter[str] = Counter()
    decision_counter: Counter[str] = Counter()
    entry_state_counter: Counter[str] = Counter()
    bucket_rows: dict[str, list[CandidateRow]] = defaultdict(list)

    for row in rows:
        decision_counter[row.decision or "null"] += 1
        entry_state_counter[row.entry_state or "null"] += 1
        setup_key = row.setup_id or ""
        setup_counts[setup_key][row.entry_state or "null"] += 1
        if row.distance_to_entry_pct is not None:
            setup_distances[setup_key].append(row.distance_to_entry_pct)
        for reason in row.decision_reasons:
            reason_counter[reason] += 1
        bucket_rows[normalize_setup_bucket(row.setup_id)].append(row)

    per_run: list[dict[str, Any]] = []
    for report_date in sorted(rows_by_date):
        day_rows = rows_by_date[report_date]
        chased_rows = [r for r in day_rows if r.entry_state == "chased"]
        distances = [
            r.distance_to_entry_pct
            for r in chased_rows
            if r.distance_to_entry_pct is not None
        ]
        bucket_counts = Counter(normalize_setup_bucket(r.setup_id) for r in day_rows)

        per_run.append(
            {
                "report_date": report_date,
                "candidate_count": len(day_rows),
                "decision_counts": dict(Counter((r.decision or "null") for r in day_rows)),
                "entry_state_counts": dict(Counter((r.entry_state or "null") for r in day_rows)),
                "setup_bucket_counts": dict(bucket_counts),
                "chased_count": len(chased_rows),
                "chased_pct": safe_pct(len(chased_rows), len(day_rows)),
                "median_chased_distance_to_entry_pct": median_or_none(distances),
                "p75_chased_distance_to_entry_pct": p75_or_none(distances),
                "distance_buckets_all": bucket_counter(day_rows, chased_only=False),
                "distance_buckets_chased": bucket_counter(day_rows, chased_only=True),
            }
        )

    setup_breakdown: list[dict[str, Any]] = []
    for setup_id in sorted(setup_counts):
        counter = setup_counts[setup_id]
        total = sum(counter.values())
        chased_count = counter.get("chased", 0)
        setup_rows = [r for r in rows if (r.setup_id or "") == setup_id]
        setup_breakdown.append(
            {
                "setup_id": setup_id,
                "setup_bucket": normalize_setup_bucket(setup_id or None),
                "candidate_count": total,
                "entry_state_counts": dict(counter),
                "chased_count": chased_count,
                "chased_pct": safe_pct(chased_count, total),
                "median_distance_to_entry_pct": median_or_none(setup_distances[setup_id]),
                "p75_distance_to_entry_pct": p75_or_none(setup_distances[setup_id]),
                "distance_buckets_all": bucket_counter(setup_rows, chased_only=False),
                "distance_buckets_chased": bucket_counter(setup_rows, chased_only=True),
            }
        )

    top_chased_examples = sorted(
        [r for r in rows if r.entry_state == "chased"],
        key=lambda r: (r.report_date, -(r.distance_to_entry_pct or -1.0), r.symbol, r.setup_id or ""),
    )[:50]

    setup_bucket_summaries = {
        bucket: summarize_subset(bucket_rows.get(bucket, []), bucket)
        for bucket in ["pullback", "reversal", "breakout", "other"]
    }

    return {
        "generated_at_utc": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "runs_analyzed": len(rows_by_date),
        "total_candidates": len(rows),
        "decision_counts": dict(decision_counter),
        "entry_state_counts": dict(entry_state_counter),
        "reason_counts": dict(reason_counter.most_common()),
        "distance_buckets_all": bucket_counter(rows, chased_only=False),
        "distance_buckets_chased": bucket_counter(rows, chased_only=True),
        "join_stats": join_stats,
        "per_run": per_run,
        "setup_breakdown": setup_breakdown,
        "setup_bucket_summaries": setup_bucket_summaries,
        "top_chased_examples": [asdict(r) for r in top_chased_examples],
    }


def format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


def render_distance_bucket_table(title: str, bucket_counts: dict[str, int]) -> list[str]:
    lines: list[str] = []
    lines.append(title)
    lines.append("")
    lines.append("| Bucket | Count |")
    lines.append("|---|---:|")
    for label, _, _ in DISTANCE_BUCKETS:
        lines.append(f"| {label} | {bucket_counts.get(label, 0)} |")
    if "unknown" in bucket_counts:
        lines.append(f"| unknown | {bucket_counts.get('unknown', 0)} |")
    lines.append("")
    return lines


def render_subset_markdown(subset: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    label = subset["label"]

    lines.append(f"## {label.title()} only")
    lines.append("")
    lines.append(f"- Candidates: {subset['candidate_count']}")
    lines.append("")

    lines.append("### Entry-state counts")
    lines.append("")
    for key, value in subset["entry_state_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("### Decision counts")
    lines.append("")
    for key, value in subset["decision_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.extend(render_distance_bucket_table("### Distance buckets (all)", subset["distance_buckets_all"]))
    lines.extend(
        render_distance_bucket_table(
            "### Distance buckets (chased only)",
            subset["distance_buckets_chased"],
        )
    )

    lines.append("### Per-run summary")
    lines.append("")
    lines.append("| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % | 0-3% | 3-7% | 7-15% | >15% |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in subset["per_run"]:
        buckets = row["distance_buckets_chased"]
        lines.append(
            "| {report_date} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} | {b0} | {b1} | {b2} | {b3} |".format(
                report_date=row["report_date"],
                candidate_count=row["candidate_count"],
                chased_count=row["chased_count"],
                chased_pct=format_float(row["chased_pct"]),
                median=format_float(row["median_chased_distance_to_entry_pct"]),
                p75=format_float(row["p75_chased_distance_to_entry_pct"]),
                b0=buckets.get("0-3%", 0),
                b1=buckets.get("3-7%", 0),
                b2=buckets.get("7-15%", 0),
                b3=buckets.get(">15%", 0),
            )
        )
    lines.append("")

    lines.append("### Most common decision reasons")
    lines.append("")
    for reason, count in list(subset["reason_counts"].items())[:10]:
        lines.append(f"- {reason}: {count}")
    lines.append("")

    lines.append("### Sample chased candidates")
    lines.append("")
    lines.append("| Date | Symbol | Decision | Setup | Distance % | Reasons |")
    lines.append("|---|---|---|---|---:|---|")
    for row in subset["sample_chased_candidates"][:10]:
        lines.append(
            "| {report_date} | {symbol} | {decision} | {setup_id} | {distance} | {reasons} |".format(
                report_date=row["report_date"],
                symbol=row["symbol"],
                decision=row["decision"] or "",
                setup_id=row["setup_id"] or "",
                distance=format_float(row["distance_to_entry_pct"]),
                reasons=", ".join(row["decision_reasons"]),
            )
        )
    lines.append("")
    return lines


def render_markdown(summary: dict[str, Any], source_files: list[Path]) -> str:
    join_stats = summary["join_stats"]

    lines: list[str] = []
    lines.append("# Chased Entry Analysis")
    lines.append("")
    lines.append(f"- Generated: {summary['generated_at_utc']}")
    lines.append(f"- Runs analyzed: {summary['runs_analyzed']}")
    lines.append(f"- Total candidates: {summary['total_candidates']}")
    lines.append(f"- Source files: {', '.join(p.name for p in source_files)}")
    lines.append("")

    lines.append("## Setup join diagnostics")
    lines.append("")
    lines.append(f"- Candidates with setup already present: {join_stats['already_present']}")
    lines.append(f"- Candidates joined via unique symbol match: {join_stats['joined_unique']}")
    lines.append(f"- Candidates joined via multi-match heuristic: {join_stats['joined_multi']}")
    lines.append(f"- Candidates unresolved after join: {join_stats['unresolved']}")
    if join_stats["unresolved_symbols"]:
        lines.append(f"- Unresolved symbols: {', '.join(join_stats['unresolved_symbols'][:25])}")
    lines.append("")

    lines.append("## Overall entry-state counts")
    lines.append("")
    for key, value in summary["entry_state_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.append("## Overall decision counts")
    lines.append("")
    for key, value in summary["decision_counts"].items():
        lines.append(f"- {key}: {value}")
    lines.append("")

    lines.extend(render_distance_bucket_table("## Overall distance buckets (all)", summary["distance_buckets_all"]))
    lines.extend(
        render_distance_bucket_table(
            "## Overall distance buckets (chased only)",
            summary["distance_buckets_chased"],
        )
    )

    lines.append("## Per-run chased summary")
    lines.append("")
    lines.append("| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % | Pullback | Reversal | Breakout | Other | 0-3% | 3-7% | 7-15% | >15% |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in summary["per_run"]:
        bucket_counts = row.get("setup_bucket_counts", {})
        distance_buckets = row.get("distance_buckets_chased", {})
        lines.append(
            "| {report_date} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} | {pullback} | {reversal} | {breakout} | {other} | {b0} | {b1} | {b2} | {b3} |".format(
                report_date=row["report_date"],
                candidate_count=row["candidate_count"],
                chased_count=row["chased_count"],
                chased_pct=format_float(row["chased_pct"]),
                median=format_float(row["median_chased_distance_to_entry_pct"]),
                p75=format_float(row["p75_chased_distance_to_entry_pct"]),
                pullback=bucket_counts.get("pullback", 0),
                reversal=bucket_counts.get("reversal", 0),
                breakout=bucket_counts.get("breakout", 0),
                other=bucket_counts.get("other", 0),
                b0=distance_buckets.get("0-3%", 0),
                b1=distance_buckets.get("3-7%", 0),
                b2=distance_buckets.get("7-15%", 0),
                b3=distance_buckets.get(">15%", 0),
            )
        )
    lines.append("")

    lines.append("## Setup breakdown")
    lines.append("")
    lines.append("| Setup | Bucket | Candidates | Chased | Chased % | Median distance % | P75 distance % | 0-3% | 3-7% | 7-15% | >15% |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in summary["setup_breakdown"]:
        dist = row["distance_buckets_chased"]
        lines.append(
            "| {setup_id} | {setup_bucket} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} | {b0} | {b1} | {b2} | {b3} |".format(
                setup_id=row["setup_id"],
                setup_bucket=row["setup_bucket"],
                candidate_count=row["candidate_count"],
                chased_count=row["chased_count"],
                chased_pct=format_float(row["chased_pct"]),
                median=format_float(row["median_distance_to_entry_pct"]),
                p75=format_float(row["p75_distance_to_entry_pct"]),
                b0=dist.get("0-3%", 0),
                b1=dist.get("3-7%", 0),
                b2=dist.get("7-15%", 0),
                b3=dist.get(">15%", 0),
            )
        )
    lines.append("")

    lines.append("## Most common decision reasons")
    lines.append("")
    for reason, count in list(summary["reason_counts"].items())[:15]:
        lines.append(f"- {reason}: {count}")
    lines.append("")

    lines.append("## Sample chased candidates (overall)")
    lines.append("")
    lines.append("| Date | Symbol | Decision | Setup | Distance % | Reasons |")
    lines.append("|---|---|---|---|---:|---|")
    for row in summary["top_chased_examples"][:20]:
        lines.append(
            "| {report_date} | {symbol} | {decision} | {setup_id} | {distance} | {reasons} |".format(
                report_date=row["report_date"],
                symbol=row["symbol"],
                decision=row["decision"] or "",
                setup_id=row["setup_id"] or "",
                distance=format_float(row["distance_to_entry_pct"]),
                reasons=", ".join(row["decision_reasons"]),
            )
        )
    lines.append("")

    for bucket in ["pullback", "reversal", "breakout", "other"]:
        lines.extend(render_subset_markdown(summary["setup_bucket_summaries"][bucket]))

    return "\n".join(lines)


def analyze_report(report_data: Any, report_date: str) -> tuple[list[CandidateRow], dict[str, int]]:
    trade_candidates = extract_trade_candidates(report_data, report_date)
    setup_hints = extract_setup_hints(report_data, report_date)
    setup_index = build_setup_index(setup_hints)

    join_counter: Counter[str] = Counter()
    resolved_rows: list[CandidateRow] = []

    for candidate in trade_candidates:
        resolved, mode = resolve_candidate_setup(candidate, setup_index)
        join_counter[mode] += 1
        resolved_rows.append(resolved)

    deduped = deduplicate_rows(resolved_rows)
    return deduped, dict(join_counter)


def main() -> int:
    args = parse_args()

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
        raise SystemExit("No matching daily report JSON files found.")

    all_rows: list[CandidateRow] = []
    total_join_counter: Counter[str] = Counter()

    for report_file in report_files:
        report_data = load_json(report_file)
        report_date = parse_report_date(report_file)
        rows, join_counter = analyze_report(report_data, report_date)
        all_rows.extend(rows)
        total_join_counter.update(join_counter)

    if not all_rows:
        raise SystemExit("No candidate rows found in selected reports.")

    unresolved_symbols = sorted(
        {
            row.symbol
            for row in all_rows
            if not row.setup_id
        }
    )

    join_stats = {
        "already_present": total_join_counter.get("already_present", 0),
        "joined_unique": total_join_counter.get("joined_unique", 0),
        "joined_multi": total_join_counter.get("joined_multi", 0),
        "unresolved": total_join_counter.get("unresolved", 0),
        "unresolved_symbols": unresolved_symbols,
    }

    summary = build_summary(all_rows, join_stats)

    latest_date = parse_report_date(report_files[-1])
    stem = f"chased_entry_analysis_{latest_date}"

    json_path = output_dir / f"{stem}.json"
    md_path = output_dir / f"{stem}.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    with md_path.open("w", encoding="utf-8") as f:
        f.write(render_markdown(summary, report_files) + "\n")

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
