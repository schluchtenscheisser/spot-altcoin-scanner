# analyze_chased_entries.py

```python
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


@dataclass
class CandidateRow:
    report_date: str
    symbol: str
    decision: str | None
    setup_id: str | None
    setup_bucket: str
    entry_state: str | None
    distance_to_entry_pct: float | None
    current_price: float | None
    planned_entry_price: float | None
    decision_reasons: list[str]
    source_path: str


@dataclass
class SymbolContext:
    setup_ids: list[str]
    buckets: list[str]


SETUP_KEY_CANDIDATES = [
    "setup_id",
    "setup_type",
    "setup_name",
    "setup",
    "selected_setup_id",
    "selected_setup_type",
    "primary_setup_id",
    "primary_setup_type",
    "strategy",
    "strategy_id",
    "strategy_type",
]

ENTRY_KEY_CANDIDATES = [
    "entry_price",
    "entry",
    "planned_entry_price",
    "entry_trigger",
    "trigger_price",
    "buy_price",
]

CURRENT_PRICE_KEY_CANDIDATES = [
    "current_price",
    "price",
    "market_price",
    "last_price",
    "close",
    "last",
]

DISTANCE_KEY_CANDIDATES = [
    "distance_to_entry_pct",
    "entry_distance_pct",
    "distance_from_entry_pct",
]

SYMBOL_KEY_CANDIDATES = [
    "symbol",
    "market",
    "pair",
]


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
        default="reports/analysis",
        help="Directory for generated analysis artifacts (default: reports/analysis)",
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


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def normalize_symbol(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    return s.upper()


def is_symbol_like(value: str | None) -> bool:
    if not value:
        return False
    if "USDT" in value or "USD" in value:
        return True
    return value.isupper() and 3 <= len(value) <= 20


def iter_dict_nodes(obj: Any, path: str = "$") -> Iterable[tuple[dict[str, Any], str]]:
    if isinstance(obj, dict):
        yield obj, path
        for key, value in obj.items():
            yield from iter_dict_nodes(value, f"{path}.{key}")
    elif isinstance(obj, list):
        for idx, value in enumerate(obj):
            yield from iter_dict_nodes(value, f"{path}[{idx}]")


def iter_values(obj: Any) -> Iterable[Any]:
    if isinstance(obj, dict):
        for value in obj.values():
            yield value
            yield from iter_values(value)
    elif isinstance(obj, list):
        for value in obj:
            yield value
            yield from iter_values(value)


def find_first_value(obj: Any, key_candidates: list[str]) -> Any:
    def _walk(x: Any) -> Any:
        if isinstance(x, dict):
            for key in key_candidates:
                if key in x and x[key] is not None:
                    return x[key]
            for _, value in x.items():
                found = _walk(value)
                if found is not None:
                    return found
        elif isinstance(x, list):
            for value in x:
                found = _walk(value)
                if found is not None:
                    return found
        return None

    return _walk(obj)


def find_all_values_for_keys(obj: Any, key_candidates: list[str]) -> list[Any]:
    results: list[Any] = []

    def _walk(x: Any) -> None:
        if isinstance(x, dict):
            for key, value in x.items():
                if key in key_candidates and value is not None:
                    results.append(value)
                _walk(value)
        elif isinstance(x, list):
            for value in x:
                _walk(value)

    _walk(obj)
    return results


def extract_setup_strings_from_node(node: dict[str, Any]) -> list[str]:
    raw_values = find_all_values_for_keys(node, SETUP_KEY_CANDIDATES)
    setup_strings: list[str] = []

    for value in raw_values:
        if isinstance(value, str):
            setup_strings.append(value)
        elif isinstance(value, dict):
            nested = find_first_value(value, ["id", "type", "name"])
            if isinstance(nested, str):
                setup_strings.append(nested)

    return [s for s in setup_strings if s and len(s) < 200]


def normalize_setup_bucket(setup_id: str | None, source_path: str = "") -> str:
    haystack = f"{setup_id or ''} {source_path}".lower()
    if "pullback" in haystack:
        return "pullback"
    if "reversal" in haystack:
        return "reversal"
    if "breakout" in haystack:
        return "breakout"
    return "other"


def choose_best_setup_id(setup_ids: list[str], fallback_path: str = "") -> str | None:
    if not setup_ids:
        bucket = normalize_setup_bucket(None, fallback_path)
        return None if bucket == "other" else bucket

    ranked = sorted(
        set(setup_ids),
        key=lambda s: (
            0 if any(tag in s.lower() for tag in ["pullback", "reversal", "breakout"]) else 1,
            len(s),
            s,
        ),
    )
    return ranked[0]


def first_non_null_float_from_obj(obj: Any, keys: list[str]) -> float | None:
    value = find_first_value(obj, keys)
    return coerce_float(value)


def first_non_null_str_from_obj(obj: Any, keys: list[str]) -> str | None:
    value = find_first_value(obj, keys)
    if value is None:
        return None
    if isinstance(value, str):
        s = value.strip()
        return s or None
    return str(value)


def looks_like_candidate(node: dict[str, Any], path: str) -> bool:
    has_decision = find_first_value(node, ["decision"]) is not None
    has_entry_state = find_first_value(node, ["entry_state"]) is not None
    symbol = first_non_null_str_from_obj(node, SYMBOL_KEY_CANDIDATES)
    if has_decision and has_entry_state and is_symbol_like(normalize_symbol(symbol)):
        return True
    if path.startswith("$.trade_candidates[") and is_symbol_like(normalize_symbol(symbol)):
        return True
    return False


def build_symbol_context_map(report_data: Any) -> dict[str, SymbolContext]:
    symbol_to_setup_ids: dict[str, Counter[str]] = defaultdict(Counter)
    symbol_to_buckets: dict[str, Counter[str]] = defaultdict(Counter)

    for node, path in iter_dict_nodes(report_data):
        symbol = normalize_symbol(first_non_null_str_from_obj(node, SYMBOL_KEY_CANDIDATES))
        if not is_symbol_like(symbol):
            continue

        setup_strings = extract_setup_strings_from_node(node)
        for setup_str in setup_strings:
            symbol_to_setup_ids[symbol][setup_str] += 1

        bucket = normalize_setup_bucket(choose_best_setup_id(setup_strings, path), path)
        if bucket != "other":
            symbol_to_buckets[symbol][bucket] += 1

    result: dict[str, SymbolContext] = {}
    for symbol in set(symbol_to_setup_ids) | set(symbol_to_buckets):
        setup_ids = [s for s, _ in symbol_to_setup_ids[symbol].most_common()]
        buckets = [b for b, _ in symbol_to_buckets[symbol].most_common()]
        result[symbol] = SymbolContext(setup_ids=setup_ids, buckets=buckets)

    return result


def enrich_setup_from_context(
    symbol: str,
    direct_setup_id: str | None,
    direct_bucket: str,
    symbol_context_map: dict[str, SymbolContext],
    source_path: str,
) -> tuple[str | None, str]:
    if direct_setup_id:
        return direct_setup_id, direct_bucket

    context = symbol_context_map.get(symbol)
    if context:
        setup_id = context.setup_ids[0] if context.setup_ids else None
        if setup_id:
            return setup_id, normalize_setup_bucket(setup_id, source_path)
        if context.buckets:
            return None, context.buckets[0]

    return None, direct_bucket


def extract_candidates(
    report_data: Any,
    report_date: str,
    symbol_context_map: dict[str, SymbolContext],
) -> list[CandidateRow]:
    seen: set[tuple[str, str, str | None, str | None, str]] = set()
    rows: list[CandidateRow] = []

    for node, source_path in iter_dict_nodes(report_data):
        if not looks_like_candidate(node, source_path):
            continue

        symbol = normalize_symbol(first_non_null_str_from_obj(node, SYMBOL_KEY_CANDIDATES))
        if not is_symbol_like(symbol):
            continue

        decision = first_non_null_str_from_obj(node, ["decision"])
        entry_state = first_non_null_str_from_obj(node, ["entry_state"])

        direct_setup_candidates = extract_setup_strings_from_node(node)
        direct_setup_id = choose_best_setup_id(direct_setup_candidates, source_path)
        direct_bucket = normalize_setup_bucket(direct_setup_id, source_path)

        setup_id, setup_bucket = enrich_setup_from_context(
            symbol=symbol,
            direct_setup_id=direct_setup_id,
            direct_bucket=direct_bucket,
            symbol_context_map=symbol_context_map,
            source_path=source_path,
        )

        planned_entry_price = first_non_null_float_from_obj(node, ENTRY_KEY_CANDIDATES)
        current_price = first_non_null_float_from_obj(node, CURRENT_PRICE_KEY_CANDIDATES)
        distance_to_entry_pct = first_non_null_float_from_obj(node, DISTANCE_KEY_CANDIDATES)
        decision_reasons = coerce_list_of_str(find_first_value(node, ["decision_reasons"]))

        dedupe_key = (report_date, symbol, decision, entry_state, source_path)
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        rows.append(
            CandidateRow(
                report_date=report_date,
                symbol=symbol,
                decision=decision,
                setup_id=setup_id,
                setup_bucket=setup_bucket,
                entry_state=entry_state,
                distance_to_entry_pct=distance_to_entry_pct,
                current_price=current_price,
                planned_entry_price=planned_entry_price,
                decision_reasons=decision_reasons,
                source_path=source_path,
            )
        )

    return rows


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
            }
        )

    chased_examples = sorted(
        [r for r in rows if r.entry_state == "chased"],
        key=lambda r: (r.report_date, -(r.distance_to_entry_pct or -1.0), r.symbol),
    )[:20]

    return {
        "label": label,
        "candidate_count": len(rows),
        "decision_counts": dict(decision_counter),
        "entry_state_counts": dict(entry_state_counter),
        "reason_counts": dict(reason_counter.most_common()),
        "per_run": per_run,
        "sample_chased_candidates": [asdict(r) for r in chased_examples],
    }


def build_summary(rows: list[CandidateRow]) -> dict[str, Any]:
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

        setup_key = row.setup_id or f"bucket:{row.setup_bucket}"
        setup_counts[setup_key][row.entry_state or "null"] += 1

        if row.distance_to_entry_pct is not None:
            setup_distances[setup_key].append(row.distance_to_entry_pct)

        for reason in row.decision_reasons:
            reason_counter[reason] += 1

        bucket_rows[row.setup_bucket].append(row)

    per_run: list[dict[str, Any]] = []
    for report_date in sorted(rows_by_date):
        day_rows = rows_by_date[report_date]
        chased_rows = [r for r in day_rows if r.entry_state == "chased"]
        distances = [
            r.distance_to_entry_pct
            for r in chased_rows
            if r.distance_to_entry_pct is not None
        ]
        bucket_counts = Counter(r.setup_bucket for r in day_rows)
        chased_bucket_counts = Counter(r.setup_bucket for r in chased_rows)

        per_run.append(
            {
                "report_date": report_date,
                "candidate_count": len(day_rows),
                "decision_counts": dict(Counter((r.decision or "null") for r in day_rows)),
                "entry_state_counts": dict(Counter((r.entry_state or "null") for r in day_rows)),
                "setup_bucket_counts": dict(bucket_counts),
                "chased_bucket_counts": dict(chased_bucket_counts),
                "chased_count": len(chased_rows),
                "chased_pct": safe_pct(len(chased_rows), len(day_rows)),
                "median_chased_distance_to_entry_pct": median_or_none(distances),
                "p75_chased_distance_to_entry_pct": p75_or_none(distances),
            }
        )

    setup_breakdown: list[dict[str, Any]] = []
    for setup_id in sorted(setup_counts):
        counter = setup_counts[setup_id]
        total = sum(counter.values())
        chased_count = counter.get("chased", 0)
        bucket = (
            setup_id.replace("bucket:", "")
            if setup_id.startswith("bucket:")
            else normalize_setup_bucket(setup_id)
        )

        setup_breakdown.append(
            {
                "setup_id": None if setup_id.startswith("bucket:") else setup_id,
                "setup_bucket": bucket,
                "candidate_count": total,
                "entry_state_counts": dict(counter),
                "chased_count": chased_count,
                "chased_pct": safe_pct(chased_count, total),
                "median_distance_to_entry_pct": median_or_none(setup_distances[setup_id]),
                "p75_distance_to_entry_pct": p75_or_none(setup_distances[setup_id]),
            }
        )

    top_chased_examples = sorted(
        [r for r in rows if r.entry_state == "chased"],
        key=lambda r: (r.report_date, -(r.distance_to_entry_pct or -1.0), r.symbol),
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
        "per_run": per_run,
        "setup_breakdown": setup_breakdown,
        "setup_bucket_summaries": setup_bucket_summaries,
        "top_chased_examples": [asdict(r) for r in top_chased_examples],
    }


def format_float(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.2f}"


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

    lines.append("### Per-run summary")
    lines.append("")
    lines.append("| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in subset["per_run"]:
        lines.append(
            "| {report_date} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} |".format(
                report_date=row["report_date"],
                candidate_count=row["candidate_count"],
                chased_count=row["chased_count"],
                chased_pct=format_float(row["chased_pct"]),
                median=format_float(row["median_chased_distance_to_entry_pct"]),
                p75=format_float(row["p75_chased_distance_to_entry_pct"]),
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
    lines.append("| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |")
    lines.append("|---|---|---|---|---|---:|---|")
    for row in subset["sample_chased_candidates"][:10]:
        lines.append(
            "| {report_date} | {symbol} | {decision} | {setup_id} | {setup_bucket} | {distance} | {reasons} |".format(
                report_date=row["report_date"],
                symbol=row["symbol"],
                decision=row["decision"] or "",
                setup_id=row["setup_id"] or "",
                setup_bucket=row["setup_bucket"] or "",
                distance=format_float(row["distance_to_entry_pct"]),
                reasons=", ".join(row["decision_reasons"]),
            )
        )
    lines.append("")
    return lines


def render_markdown(summary: dict[str, Any], source_files: list[Path]) -> str:
    lines: list[str] = []
    lines.append("# Chased Entry Analysis")
    lines.append("")
    lines.append(f"- Generated: {summary['generated_at_utc']}")
    lines.append(f"- Runs analyzed: {summary['runs_analyzed']}")
    lines.append(f"- Total candidates: {summary['total_candidates']}")
    lines.append(f"- Source files: {', '.join(p.name for p in source_files)}")
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

    lines.append("## Per-run chased summary")
    lines.append("")
    lines.append("| Date | Candidates | Chased | Chased % | Median chased distance % | P75 chased distance % | Pullback count | Reversal count | Breakout count | Other count |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in summary["per_run"]:
        bucket_counts = row.get("setup_bucket_counts", {})
        lines.append(
            "| {report_date} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} | {pullback} | {reversal} | {breakout} | {other} |".format(
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
            )
        )
    lines.append("")

    lines.append("## Setup breakdown")
    lines.append("")
    lines.append("| Setup | Bucket | Candidates | Chased | Chased % | Median distance % | P75 distance % |")
    lines.append("|---|---|---:|---:|---:|---:|---:|")
    for row in summary["setup_breakdown"]:
        lines.append(
            "| {setup_id} | {setup_bucket} | {candidate_count} | {chased_count} | {chased_pct} | {median} | {p75} |".format(
                setup_id=row["setup_id"] or "",
                setup_bucket=row["setup_bucket"],
                candidate_count=row["candidate_count"],
                chased_count=row["chased_count"],
                chased_pct=format_float(row["chased_pct"]),
                median=format_float(row["median_distance_to_entry_pct"]),
                p75=format_float(row["p75_distance_to_entry_pct"]),
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
    lines.append("| Date | Symbol | Decision | Setup | Bucket | Distance % | Reasons |")
    lines.append("|---|---|---|---|---|---:|---|")
    for row in summary["top_chased_examples"][:20]:
        lines.append(
            "| {report_date} | {symbol} | {decision} | {setup_id} | {setup_bucket} | {distance} | {reasons} |".format(
                report_date=row["report_date"],
                symbol=row["symbol"],
                decision=row["decision"] or "",
                setup_id=row["setup_id"] or "",
                setup_bucket=row["setup_bucket"] or "",
                distance=format_float(row["distance_to_entry_pct"]),
                reasons=", ".join(row["decision_reasons"]),
            )
        )
    lines.append("")

    for bucket in ["pullback", "reversal", "breakout", "other"]:
        lines.extend(render_subset_markdown(summary["setup_bucket_summaries"][bucket]))

    return "\n".join(lines)


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
    for report_file in report_files:
        report_data = load_json(report_file)
        report_date = parse_report_date(report_file)
        symbol_context_map = build_symbol_context_map(report_data)
        all_rows.extend(extract_candidates(report_data, report_date, symbol_context_map))

    if not all_rows:
        raise SystemExit("No candidate rows found in selected reports.")

    summary = build_summary(all_rows)

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
```
