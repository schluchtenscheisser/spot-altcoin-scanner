#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
import re
import zipfile
from pathlib import Path
from statistics import median
from typing import Any, Iterable

OUTPUT_DIR_DEFAULT = "reports/aux/entry_location_analysis"
FORBIDDEN_OUTPUT_ROOTS = [
    "reports/runs",
    "reports/daily",
    "reports/index",
    "snapshots/runs",
    "reports/analysis",
]

PROXY_FIELDS = [
    "expansion_progress_structural",
    "freshness_distance_structural",
    "reclaim_progress",
    "reacceleration_strength_simplified",
    "volume_regime_shift",
    "pullback_quality_simplified",
]

PATTERN_BREAKDOWN_FIELDS = [
    "expansion_progress_structural",
    "freshness_distance_structural",
    "reclaim_progress",
    "reacceleration_strength_simplified",
]

STEP_B_FIELDS = [
    "close_vs_ema20_4h_pct",
    "bars_above_ema20_4h",
    "dist_to_ema20_4h_pct_abs",
]

NAMED_CANDIDATES = ["RENDERUSDT", "DOTUSDT", "AVAXUSDT", "DOGEUSDT", "PEPEUSDT"]
PATTERN_ORDER = [
    "early_reversal_break",
    "resume_reclaim",
    "ema_reclaim",
    "shallow_pullback",
    "continuation_breakout",
]


def _normalize(p: Path, repo_root: Path) -> Path | None:
    try:
        return p.resolve().relative_to(repo_root)
    except ValueError:
        return None


def _validate_output_dir(out: Path, repo_root: Path) -> None:
    rel = _normalize(out, repo_root)
    if rel is None:
        return
    r = rel.as_posix()
    for bad in FORBIDDEN_OUTPUT_ROOTS:
        if r == bad or r.startswith(f"{bad}/"):
            raise ValueError(f"Forbidden output path: {out} (normalized: {rel})")


def _block(rec: dict[str, Any], name: str) -> dict[str, Any]:
    value = rec.get(name)
    return value if isinstance(value, dict) else {}


def _axes(rec: dict[str, Any]) -> dict[str, Any]:
    return _block(rec, "axes")


def _decision(rec: dict[str, Any]) -> dict[str, Any]:
    return _block(rec, "decision")


def _pattern(rec: dict[str, Any]) -> dict[str, Any]:
    return _block(rec, "pattern")


def _phase(rec: dict[str, Any]) -> dict[str, Any]:
    return _block(rec, "phase")


def _state(rec: dict[str, Any]) -> dict[str, Any]:
    return _block(rec, "state")


def _finite_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(float(value))


def _numeric_values(records: Iterable[dict[str, Any]], field: str) -> list[float]:
    values = []
    for rec in records:
        value = _axes(rec).get(field)
        if _finite_number(value):
            values.append(float(value))
    return values


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    rank = (len(ordered) - 1) * pct
    lo = math.floor(rank)
    hi = math.ceil(rank)
    if lo == hi:
        return ordered[lo]
    frac = rank - lo
    return ordered[lo] * (1.0 - frac) + ordered[hi] * frac


def _fmt(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, float):
        if math.isfinite(value):
            return f"{value:.2f}"
        return "null"
    return str(value)


def _null_count(records: Iterable[dict[str, Any]], field: str) -> int:
    return sum(1 for rec in records if _axes(rec).get(field) is None)


def _stats(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = _numeric_values(records, field)
    return {
        "count": len(records),
        "numeric_count": len(values),
        "null_count": _null_count(records, field),
        "median": median(values) if values else None,
        "p25": _percentile(values, 0.25),
        "p75": _percentile(values, 0.75),
        "p90": _percentile(values, 0.90),
        "p95": _percentile(values, 0.95),
    }


def _histogram(values: list[float]) -> list[tuple[str, int]]:
    buckets = [(f"{i * 10}-{i * 10 + 10}", 0) for i in range(10)]
    counts = [0] * 10
    for value in values:
        clamped = min(100.0, max(0.0, value))
        idx = min(9, int(clamped // 10))
        counts[idx] += 1
    return [(label, counts[i]) for i, (label, _) in enumerate(buckets)]


def _group_by(records: list[dict[str, Any]], key_func) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = key_func(rec)
        grouped[str(key if key is not None else "null")].append(rec)
    return dict(grouped)


def _read_diagnostics_member(zip_path: Path, member: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        raw = zf.read(member)
    return [json.loads(line) for line in gzip.decompress(raw).decode("utf-8").splitlines() if line.strip()]


def _read_diagnostics_file(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in gzip.decompress(path.read_bytes()).decode("utf-8").splitlines() if line.strip()]


def _date_from_member(member: str) -> str:
    match = re.search(r"reports/runs/(\d{4})/(\d{2})/(\d{2})/", member)
    if match:
        return "-".join(match.groups())
    match = re.search(r"(\d{4}-\d{2}-\d{2})", member)
    return match.group(1) if match else "unknown"


def _iter_diagnostics_sources(input_dir: Path) -> list[tuple[Path, str | None, str]]:
    sources: list[tuple[Path, str | None, str]] = []
    if input_dir.is_file() and input_dir.suffix == ".zip":
        zips = [input_dir]
    else:
        zips = sorted(input_dir.glob("*.zip"))
    for zip_path in zips:
        with zipfile.ZipFile(zip_path) as zf:
            for member in sorted(zf.namelist()):
                if member.endswith("symbol_diagnostics.jsonl.gz") and "/daily-" in member:
                    sources.append((zip_path, member, _date_from_member(member)))
    if input_dir.is_dir():
        for diag in sorted(input_dir.glob("**/symbol_diagnostics.jsonl.gz")):
            if any(part.startswith("daily-") for part in diag.parts):
                sources.append((diag, None, _date_from_member(diag.as_posix())))
    return sources


def _load_records(input_dir: Path) -> tuple[list[dict[str, Any]], Counter[str]]:
    records: list[dict[str, Any]] = []
    loaded_by_date: Counter[str] = Counter()
    for source, member, run_date in _iter_diagnostics_sources(input_dir):
        recs = _read_diagnostics_member(source, member) if member else _read_diagnostics_file(source)
        source_name = f"{source}:{member}" if member else str(source)
        print(f"[T_EL1] {run_date}: loaded {len(recs)} records from {source_name}", flush=True)
        loaded_by_date[run_date] += len(recs)
        for rec in recs:
            row = dict(rec)
            row["_run_date"] = run_date
            row["_source"] = source_name
            records.append(row)
    return records, loaded_by_date


def _eligible(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    excluded = [rec for rec in records if rec.get("data_4h_available") is False]
    return [rec for rec in records if rec.get("data_4h_available") is not False], len(excluded)


def _populations(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    return {
        "Population 1 — Day-0 confirmed": [
            rec
            for rec in records
            if _decision(rec).get("decision_bucket") == "confirmed_candidates"
            and _state(rec).get("bars_since_confirmed_entered") == 0
        ],
        "Population 2 — Day-1+ confirmed": [
            rec
            for rec in records
            if _decision(rec).get("decision_bucket") == "confirmed_candidates"
            and _finite_number(_state(rec).get("bars_since_confirmed_entered"))
            and float(_state(rec).get("bars_since_confirmed_entered")) >= 1.0
        ],
        "Population 3 — Day-0 early": [
            rec
            for rec in records
            if _decision(rec).get("decision_bucket") == "early_candidates"
            and _state(rec).get("bars_since_early_entered") == 0
        ],
    }


def _distribution_section(title: str, records: list[dict[str, Any]]) -> list[str]:
    lines = [f"## {title}", "", f"Record count: {len(records)}", ""]
    for field in PROXY_FIELDS:
        stats = _stats(records, field)
        lines.extend([
            f"### `{field}`",
            "",
            "| Count | Numeric | Null | Median | P25 | P75 | P90 | P95 |",
            "|---:|---:|---:|---:|---:|---:|---:|---:|",
            "| " + " | ".join(_fmt(stats[key]) for key in ["count", "numeric_count", "null_count", "median", "p25", "p75", "p90", "p95"]) + " |",
            "",
            "Histogram (10 buckets, values clamped to 0–100):",
            "",
            "| Bucket | Count |",
            "|---|---:|",
        ])
        for label, count in _histogram(_numeric_values(records, field)):
            lines.append(f"| {label} | {count} |")
        lines.extend(["", "Top 5 `entry_pattern` breakdown:", "", "| Entry pattern | Count | Median | P25 | P75 | Null |", "|---|---:|---:|---:|---:|---:|"])
        pattern_groups = _group_by(records, lambda rec: _pattern(rec).get("entry_pattern"))
        for pattern, group in sorted(pattern_groups.items(), key=lambda item: (-len(item[1]), item[0]))[:5]:
            s = _stats(group, field)
            lines.append(f"| {pattern} | {len(group)} | {_fmt(s['median'])} | {_fmt(s['p25'])} | {_fmt(s['p75'])} | {_fmt(s['null_count'])} |")
        lines.extend(["", "`market_phase` breakdown:", "", "| Market phase | Count | Median | P25 | P75 | Null |", "|---|---:|---:|---:|---:|---:|"])
        phase_groups = _group_by(records, lambda rec: _phase(rec).get("market_phase"))
        for phase, group in sorted(phase_groups.items(), key=lambda item: (-len(item[1]), item[0])):
            s = _stats(group, field)
            lines.append(f"| {phase} | {len(group)} | {_fmt(s['median'])} | {_fmt(s['p25'])} | {_fmt(s['p75'])} | {_fmt(s['null_count'])} |")
        lines.append("")
    return lines


def _write_population_distributions(out: Path, populations: dict[str, list[dict[str, Any]]], total_loaded: int, data_4h_excluded: int) -> None:
    lines = [
        "# T_EL1 Step A — Population Proxy Distributions",
        "",
        f"Loaded diagnostic records: {total_loaded}",
        f"Excluded records with `data_4h_available == False`: {data_4h_excluded}",
        "",
        "Null proxy values are counted separately and are not coerced to zero.",
        "",
    ]
    for title, records in populations.items():
        lines.extend(_distribution_section(title, records))
    lines.extend(_pattern_specific_breakdown(populations["Population 1 — Day-0 confirmed"]))
    (out / "step_a_population_distributions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pattern_specific_breakdown(records: list[dict[str, Any]]) -> list[str]:
    lines = [
        "## Population 1 pattern-specific breakdown",
        "",
        "| Pattern | Count | median(expansion_progress) | median(freshness_dist_struct) | median(reclaim_progress) | median(reaccel_strength) |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    grouped = _group_by(records, lambda rec: _pattern(rec).get("entry_pattern"))
    used = set()
    for pattern in PATTERN_ORDER:
        group = grouped.get(pattern, [])
        used.add(pattern)
        values = [_stats(group, field)["median"] for field in PATTERN_BREAKDOWN_FIELDS]
        lines.append(f"| `{pattern}` | {len(group)} | " + " | ".join(_fmt(v) for v in values) + " |")
    other = [rec for pattern, group in grouped.items() if pattern not in used for rec in group]
    values = [_stats(other, field)["median"] for field in PATTERN_BREAKDOWN_FIELDS]
    lines.append(f"| _(other)_ | {len(other)} | " + " | ".join(_fmt(v) for v in values) + " |")
    lines.append("")
    return lines


def _write_named_candidates(out: Path, population_1: list[dict[str, Any]]) -> None:
    lines = [
        "# T_EL1 Step A — Named Candidate Profiles",
        "",
        "Population: Day-0 `confirmed_candidates` with 4h data available.",
        "",
        "| Run date | Symbol | Priority score | Entry pattern | Market phase | Execution status raw | expansion_progress_structural | freshness_distance_structural | reclaim_progress | reacceleration_strength_simplified | volume_regime_shift | pullback_quality_simplified |",
        "|---|---|---:|---|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    by_symbol = {symbol: [] for symbol in NAMED_CANDIDATES}
    for rec in population_1:
        symbol = str(rec.get("symbol") or "")
        if symbol in by_symbol:
            by_symbol[symbol].append(rec)
    wrote = False
    for symbol in NAMED_CANDIDATES:
        for rec in sorted(by_symbol[symbol], key=lambda r: (r.get("_run_date"), str(r.get("symbol")))):
            axes = _axes(rec)
            values = [axes.get(field) for field in PROXY_FIELDS]
            lines.append(
                f"| {rec.get('_run_date')} | {symbol} | {_fmt(_decision(rec).get('priority_score'))} | "
                f"{_fmt(_pattern(rec).get('entry_pattern'))} | {_fmt(_phase(rec).get('market_phase'))} | {_fmt(rec.get('execution_status_raw'))} | "
                + " | ".join(_fmt(v) for v in values)
                + " |"
            )
            wrote = True
    if not wrote:
        lines.append("| _none_ | _No named candidates found in Population 1_ | null | null | null | null | null | null | null | null | null | null |")
    (out / "step_a_named_candidates.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_day0_summary(out: Path, eligible_records: list[dict[str, Any]], data_4h_excluded: int) -> None:
    dates = sorted({str(rec.get("_run_date")) for rec in eligible_records})
    lines = [
        "# T_EL1 Step A — Day-0 Volume Summary",
        "",
        f"Records excluded from all populations because `data_4h_available == False`: {data_4h_excluded}",
        "",
        "| Run date | Total confirmed | Day-0 confirmed | Day-1+ confirmed | Day-0 fraction | Day-0 direct_ok | Day-0 marginal |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for run_date in dates:
        recs = [rec for rec in eligible_records if rec.get("_run_date") == run_date]
        confirmed = [rec for rec in recs if _decision(rec).get("decision_bucket") == "confirmed_candidates"]
        day0 = [rec for rec in confirmed if _state(rec).get("bars_since_confirmed_entered") == 0]
        day1p = [
            rec for rec in confirmed
            if _finite_number(_state(rec).get("bars_since_confirmed_entered")) and float(_state(rec).get("bars_since_confirmed_entered")) >= 1.0
        ]
        direct = sum(1 for rec in day0 if rec.get("execution_status_raw") == "direct_ok")
        marginal = sum(1 for rec in day0 if rec.get("execution_status_raw") == "marginal")
        frac = (len(day0) / len(confirmed)) if confirmed else 0.0
        lines.append(f"| {run_date} | {len(confirmed)} | {len(day0)} | {len(day1p)} | {frac:.2%} | {direct} | {marginal} |")
    (out / "step_a_day0_volume_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_findings(out: Path, populations: dict[str, list[dict[str, Any]]], data_4h_excluded: int) -> None:
    p1 = populations["Population 1 — Day-0 confirmed"]
    p2 = populations["Population 2 — Day-1+ confirmed"]
    p3 = populations["Population 3 — Day-0 early"]
    lines = [
        "# T_EL1 Step A — Findings and Field Requirements",
        "",
        "## Key findings",
        "",
        f"- Population 1 (Day-0 confirmed) contains {len(p1)} records.",
        f"- Population 2 (Day-1+ confirmed) contains {len(p2)} records.",
        f"- Population 3 (Day-0 early) contains {len(p3)} records.",
        f"- Records excluded because `data_4h_available == False`: {data_4h_excluded}.",
        "- Existing structural proxy fields can describe directional overextension risk, but calibrated entry-location thresholds require direct 4h distance fields in diagnostics.",
        "- `None` proxy values are preserved as null and reported separately in the distribution output.",
        "",
        "## Field requirements for diagnostics extension",
        "",
        "The structural anchor fields below were verified by code inspection in `scanner/features/models.py`, `scanner/features/raw_4h.py`, and `scanner/axes/tier1.py`. The spec field `bars_since_last_structural_break_event` is implemented as `bars_since_last_structural_break_4h`.",
        "",
        "| Field name | Source module (T-ticket) | Reason needed | Priority |",
        "|---|---|---|---|",
        "| `close_vs_ema20_4h_pct` | T5 raw features | Primary overextension indicator | Must-have |",
        "| `bars_above_ema20_4h` | T5 raw features | 4h velocity proxy | Must-have |",
        "| `dist_to_ema20_4h_pct_abs` | T5 raw features | Absolute distance variant | Must-have |",
        "| `distance_to_last_structural_anchor_pct_abs` | T5 raw features (confirmed present) | Direct structural anchor distance useful for directional warning support | Should-have |",
        "| `distance_to_range_high_pct_abs` | T5.1 raw features (confirmed present) | Range-high proximity helps separate clean retests from extended breaks | Should-have |",
        "| `bars_since_last_structural_break_4h` | T5 raw features (implementation name for `bars_since_last_structural_break_event`, confirmed present) | Structural-break age supports trigger freshness analysis | Should-have |",
        "",
    ]
    (out / "step_a_findings_and_field_requirements.md").write_text("\n".join(lines), encoding="utf-8")


def _direct_field(rec: dict[str, Any], field: str) -> Any:
    for block_name in ("features", "raw_features", "raw_features_4h", "raw_4h"):
        block = rec.get(block_name)
        if isinstance(block, dict) and field in block:
            return block.get(field)
    return rec.get(field)


def _has_step_b_data(records: list[dict[str, Any]]) -> bool:
    for field in STEP_B_FIELDS:
        if not any(_direct_field(rec, field) is not None for rec in records):
            return False
    return True


def _direct_stats(records: list[dict[str, Any]], field: str) -> dict[str, Any]:
    values = [float(_direct_field(rec, field)) for rec in records if _finite_number(_direct_field(rec, field))]
    return {
        "numeric_count": len(values),
        "p25": _percentile(values, 0.25),
        "p50": median(values) if values else None,
        "p75": _percentile(values, 0.75),
        "p90": _percentile(values, 0.90),
    }


def _thresholds_from_distribution(values: list[float]) -> tuple[float | None, float | None, float | None]:
    if not values:
        return None, None, None
    return _percentile(values, 0.25), _percentile(values, 0.50), _percentile(values, 0.75)


def _run_step_b(out: Path, population_1: list[dict[str, Any]]) -> None:
    grouped = _group_by(population_1, lambda rec: _pattern(rec).get("entry_pattern"))
    lines = [
        "# T_EL1 Step B — Direct 4h Distributions",
        "",
        "| Entry pattern | Count | Metric | Numeric | P25 | P50 | P75 | P90 |",
        "|---|---:|---|---:|---:|---:|---:|---:|",
    ]
    for pattern, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        for field in STEP_B_FIELDS:
            s = _direct_stats(group, field)
            lines.append(f"| {pattern} | {len(group)} | `{field}` | {s['numeric_count']} | {_fmt(s['p25'])} | {_fmt(s['p50'])} | {_fmt(s['p75'])} | {_fmt(s['p90'])} |")
    (out / "step_b_4h_distributions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    values = [float(_direct_field(rec, "close_vs_ema20_4h_pct")) for rec in population_1 if _finite_number(_direct_field(rec, "close_vs_ema20_4h_pct"))]
    t_ideal, t_acceptable, t_extended = _thresholds_from_distribution(values)
    p75s = {pattern: _direct_stats(group, "close_vs_ema20_4h_pct")["p75"] for pattern, group in grouped.items()}
    finite_p75s = [v for v in p75s.values() if v is not None]
    pattern_specific = bool(finite_p75s and (max(finite_p75s) - min(finite_p75s) > 2.0))
    threshold_lines = [
        "# T_EL1 Step B — Threshold Candidates",
        "",
        f"Pattern-specific thresholds justified: {pattern_specific}",
        "",
        "| close_vs_ema20_4h_pct range | Proposed entry_location_status | Justification |",
        "|---|---|---|",
        f"| [0, {_fmt(t_ideal)}) | `ideal` | Lower quartile of observed Day-0 confirmed distribution |",
        f"| [{_fmt(t_ideal)}, {_fmt(t_acceptable)}) | `acceptable` | Between P25 and P50 of observed distribution |",
        f"| [{_fmt(t_acceptable)}, {_fmt(t_extended)}) | `extended` | Between P50 and P75 of observed distribution |",
        f"| [{_fmt(t_extended)}, ∞) | `chase` | Above P75 of observed distribution |",
        "",
        "| Pattern | Count | P25 | P50 | P75 | P90 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for pattern, group in sorted(grouped.items(), key=lambda item: (-len(item[1]), item[0])):
        s = _direct_stats(group, "close_vs_ema20_4h_pct")
        threshold_lines.append(f"| {pattern} | {len(group)} | {_fmt(s['p25'])} | {_fmt(s['p50'])} | {_fmt(s['p75'])} | {_fmt(s['p90'])} |")
    (out / "step_b_threshold_candidates.md").write_text("\n".join(threshold_lines) + "\n", encoding="utf-8")

    named_lines = [
        "# T_EL1 Step B — Named Candidates Extended",
        "",
        "| Run date | Symbol | close_vs_ema20_4h_pct | bars_above_ema20_4h | dist_to_ema20_4h_pct_abs |",
        "|---|---|---:|---:|---:|",
    ]
    for rec in sorted(population_1, key=lambda r: (str(r.get("_run_date")), str(r.get("symbol")))):
        if rec.get("symbol") in NAMED_CANDIDATES:
            named_lines.append(
                f"| {rec.get('_run_date')} | {rec.get('symbol')} | "
                f"{_fmt(_direct_field(rec, 'close_vs_ema20_4h_pct'))} | {_fmt(_direct_field(rec, 'bars_above_ema20_4h'))} | {_fmt(_direct_field(rec, 'dist_to_ema20_4h_pct_abs'))} |"
            )
    (out / "step_b_named_candidates_extended.md").write_text("\n".join(named_lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze T_EL1 entry-location / Day-0 overextension diagnostics.")
    parser.add_argument("--input-dir", default="data/shadow-live-zips", help="Directory with Shadow-Live ZIP artifacts or extracted reports.")
    parser.add_argument("--output-dir", default=OUTPUT_DIR_DEFAULT, help="Output directory under reports/aux.")
    args = parser.parse_args()

    repo_root = Path.cwd().resolve()
    out = Path(args.output_dir)
    _validate_output_dir(out, repo_root)
    out.mkdir(parents=True, exist_ok=True)

    records, loaded_by_date = _load_records(Path(args.input_dir))
    if not records:
        raise SystemExit("[T_EL1] No daily symbol_diagnostics.jsonl.gz records found.")
    eligible_records, data_4h_excluded = _eligible(records)
    populations = _populations(eligible_records)

    _write_population_distributions(out, populations, len(records), data_4h_excluded)
    _write_named_candidates(out, populations["Population 1 — Day-0 confirmed"])
    _write_day0_summary(out, eligible_records, data_4h_excluded)
    _write_findings(out, populations, data_4h_excluded)

    if not _has_step_b_data(records):
        print("[T_EL1 Step B] Required 4h fields not found in diagnostics. Step B skipped.", flush=True)
        print("Step A completed successfully. Re-run after diagnostics extension and new artifact collection.", flush=True)
        return

    _run_step_b(out, populations["Population 1 — Day-0 confirmed"])
    print(f"[T_EL1] Loaded records by date: {dict(loaded_by_date)}", flush=True)
    print(f"[T_EL1] Wrote analysis outputs to {out}", flush=True)


if __name__ == "__main__":
    main()
