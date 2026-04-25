#!/usr/bin/env python3
"""
Top20 formation audit for Spot Altcoin Scanner.

Purpose
-------
Diagnose whether the visible Top20 composition is plausibly aligned with the
canonical global ranking intent, or whether downstream analysis may be happening
on a structurally weak candidate set.

This script intentionally does NOT modify pipeline behavior.

What it audits
--------------
1) Visible Top20 composition from canonical trade_candidates
2) Decision / setup / tradeability composition of the published Top20
3) Ordering sanity within the published Top20:
   - decision priority ENTER > WAIT > NO_TRADE
   - within ENTER/WAIT: global_score descending
4) Concentration diagnostics:
   - setup-type concentration
   - tradeability concentration
   - risk-ok vs entry-eligible concentration
5) Optional upstream inclusion audit if the run JSON contains a larger candidate
   array beyond trade_candidates (best-effort auto-detection)

Outputs
-------
Writes both:
- reports/aux/top20_formation_audit_<date>.json
- reports/aux/top20_formation_audit_<date>.md

Design notes
------------
- Stdlib only.
- Auto-discovers canonical run JSON files.
- Gracefully degrades when no upstream "pre-top20" array is present.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


DECISION_PRIORITY = {"ENTER": 0, "WAIT": 1, "NO_TRADE": 2}
ENTRY_ELIGIBLE_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK"}
UNKNOWN_SENTINEL = "UNKNOWN"


@dataclass(frozen=True)
class RunRecord:
    path: Path
    run_id: str
    timestamp_utc: str
    canonical_schema_version: Optional[str]
    raw_data: Dict[str, Any]
    trade_candidates: List[Dict[str, Any]]


def utc_now_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d_%H%M%S")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def analysis_dir() -> Path:
    out = repo_root() / "reports" / "aux"
    out.mkdir(parents=True, exist_ok=True)
    return out


def safe_load_json(path: Path) -> Optional[Dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def looks_like_run_json(data: Dict[str, Any]) -> bool:
    tc = data.get("trade_candidates")
    rm = data.get("run_manifest")
    return isinstance(tc, list) and isinstance(rm, dict)


def discover_run_files(root: Path) -> List[Path]:
    candidates: List[Path] = []
    ignored_parts = {".git", ".venv", "venv", "__pycache__"}

    for path in root.rglob("*.json"):
        if any(part in ignored_parts for part in path.parts):
            continue

        name = path.name.lower()
        path_str = str(path).lower().replace("\\", "/")

        if "/reports/analysis/" in path_str:
            continue
        if name.endswith(".manifest.json"):
            continue
        if name.startswith("backtest_"):
            continue
        if "counterfactual" in name:
            continue
        if "chased_entry_analysis" in name:
            continue
        if "diagnose_rr" in name:
            continue
        if "post_risk_unlock_audit" in name:
            continue
        if "top20_formation_audit" in name:
            continue

        data = safe_load_json(path)
        if data and looks_like_run_json(data):
            candidates.append(path)

    return sorted(candidates)


def parse_run(path: Path) -> Optional[RunRecord]:
    data = safe_load_json(path)
    if not data or not looks_like_run_json(data):
        return None

    run_manifest = data.get("run_manifest", {})
    trade_candidates = data.get("trade_candidates", [])

    timestamp_utc = str(run_manifest.get("timestamp_utc") or "")
    run_id = str(run_manifest.get("run_id") or path.stem)
    canonical_schema_version = run_manifest.get("canonical_schema_version")

    if not isinstance(trade_candidates, list):
        return None

    return RunRecord(
        path=path,
        run_id=run_id,
        timestamp_utc=timestamp_utc,
        canonical_schema_version=canonical_schema_version,
        raw_data=data,
        trade_candidates=trade_candidates,
    )


def sort_runs_desc(runs: List[RunRecord]) -> List[RunRecord]:
    def key(run: RunRecord) -> Tuple[str, str]:
        return (run.timestamp_utc or "", run.run_id or "")
    return sorted(runs, key=key, reverse=True)


def is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(value)


def normalize_str(value: Any, default: str = UNKNOWN_SENTINEL) -> str:
    if value in (None, ""):
        return default
    return str(value)


def normalize_list_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str):
        return [value]
    return [str(value)]


def bool_true(value: Any) -> bool:
    return value is True


def symbol_of(row: Dict[str, Any]) -> str:
    return normalize_str(row.get("symbol"), "UNKNOWN_SYMBOL")


def setup_type_of(row: Dict[str, Any]) -> str:
    return normalize_str(row.get("best_setup_type"))


def decision_of(row: Dict[str, Any]) -> str:
    return normalize_str(row.get("decision"))


def tradeability_of(row: Dict[str, Any]) -> str:
    return normalize_str(row.get("tradeability_class"))


def entry_state_of(row: Dict[str, Any]) -> str:
    return normalize_str(row.get("entry_state"))


def score_of(row: Dict[str, Any], key: str) -> Optional[float]:
    value = row.get(key)
    return float(value) if is_finite_number(value) else None


def decision_reasons_of(row: Dict[str, Any]) -> List[str]:
    return normalize_list_str(row.get("decision_reasons"))


def entry_eligible_tradeability(row: Dict[str, Any]) -> bool:
    return tradeability_of(row) in ENTRY_ELIGIBLE_TRADEABILITY


def row_brief(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "rank": row.get("rank"),
        "symbol": symbol_of(row),
        "decision": decision_of(row),
        "best_setup_type": setup_type_of(row),
        "tradeability_class": tradeability_of(row),
        "entry_ready": row.get("entry_ready"),
        "risk_acceptable": row.get("risk_acceptable"),
        "entry_state": entry_state_of(row),
        "global_score": row.get("global_score"),
        "setup_score": row.get("setup_score"),
        "decision_reasons": decision_reasons_of(row),
    }


def summarize_numeric(rows: Iterable[Dict[str, Any]], key: str) -> Dict[str, Optional[float]]:
    clean = [score_of(r, key) for r in rows]
    clean = [v for v in clean if v is not None]
    if not clean:
        return {"count": 0, "min": None, "median": None, "max": None, "mean": None}
    clean_sorted = sorted(clean)
    n = len(clean_sorted)
    if n % 2 == 1:
        median = clean_sorted[n // 2]
    else:
        median = (clean_sorted[n // 2 - 1] + clean_sorted[n // 2]) / 2.0
    mean = sum(clean_sorted) / n
    return {
        "count": n,
        "min": round(clean_sorted[0], 6),
        "median": round(median, 6),
        "max": round(clean_sorted[-1], 6),
        "mean": round(mean, 6),
    }


def find_ordering_violations(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    for idx in range(len(rows) - 1):
        a = rows[idx]
        b = rows[idx + 1]

        a_dec = decision_of(a)
        b_dec = decision_of(b)
        a_pri = DECISION_PRIORITY.get(a_dec, 999)
        b_pri = DECISION_PRIORITY.get(b_dec, 999)

        if a_pri > b_pri:
            violations.append(
                {
                    "type": "decision_priority",
                    "index_left": idx,
                    "index_right": idx + 1,
                    "left_symbol": symbol_of(a),
                    "right_symbol": symbol_of(b),
                    "left_decision": a_dec,
                    "right_decision": b_dec,
                }
            )
            continue

        if a_dec in {"ENTER", "WAIT"} and b_dec == a_dec:
            a_gs = score_of(a, "global_score")
            b_gs = score_of(b, "global_score")
            if a_gs is not None and b_gs is not None and a_gs < b_gs:
                violations.append(
                    {
                        "type": "global_score_desc_within_decision",
                        "index_left": idx,
                        "index_right": idx + 1,
                        "left_symbol": symbol_of(a),
                        "right_symbol": symbol_of(b),
                        "decision": a_dec,
                        "left_global_score": a_gs,
                        "right_global_score": b_gs,
                    }
                )
    return violations


def setup_concentration(counter: Counter[str], total: int) -> Dict[str, Any]:
    if total <= 0:
        return {"top_share_pct": None, "effective_unique_setups": None}

    top_count = max(counter.values()) if counter else 0
    top_share_pct = round((top_count / total) * 100.0, 2)

    probs = []
    for count in counter.values():
        p = count / total
        if p > 0:
            probs.append(p)

    hhi = sum(p * p for p in probs)
    effective_unique = round(1.0 / hhi, 4) if hhi > 0 else None

    return {
        "top_share_pct": top_share_pct,
        "effective_unique_setups": effective_unique,
    }


def find_optional_upstream_arrays(data: Dict[str, Any], trade_candidates_len: int) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []

    for key, value in data.items():
        if key == "trade_candidates":
            continue
        if not isinstance(value, list) or len(value) <= trade_candidates_len:
            continue
        if not value or not isinstance(value[0], dict):
            continue

        keys = set(value[0].keys())
        score_like = {"global_score", "setup_score", "final_score", "weighted_score", "symbol"}
        if len(keys & score_like) < 2:
            continue

        findings.append(
            {
                "key": key,
                "length": len(value),
                "sample_keys": sorted(list(keys))[:20],
            }
        )

    return sorted(findings, key=lambda x: (-x["length"], x["key"]))


def choose_best_upstream_array(data: Dict[str, Any], trade_candidates_len: int) -> Optional[Tuple[str, List[Dict[str, Any]]]]:
    candidates: List[Tuple[int, str, List[Dict[str, Any]]]] = []

    for key, value in data.items():
        if key == "trade_candidates":
            continue
        if not isinstance(value, list) or len(value) <= trade_candidates_len:
            continue
        if not value or not isinstance(value[0], dict):
            continue

        keys = set(value[0].keys())
        quality = 0
        for wanted in ("symbol", "global_score", "final_score", "weighted_score", "setup_score", "setup_id"):
            if wanted in keys:
                quality += 1

        if quality >= 2:
            candidates.append((quality, key, value))

    if not candidates:
        return None

    candidates.sort(key=lambda x: (-x[0], -len(x[2]), x[1]))
    _, key, value = candidates[0]
    return key, value


def upstream_inclusion_audit(
    upstream_key: str,
    upstream_rows: List[Dict[str, Any]],
    trade_candidates: List[Dict[str, Any]],
) -> Dict[str, Any]:
    visible_symbols = {symbol_of(r) for r in trade_candidates}

    dedup_best: Dict[str, Dict[str, Any]] = {}
    for row in upstream_rows:
        symbol = symbol_of(row)
        weighted = score_of(row, "weighted_score")
        global_score = score_of(row, "global_score")
        final_score = score_of(row, "final_score")
        proxy = weighted if weighted is not None else global_score
        if proxy is None:
            proxy = final_score
        if proxy is None:
            continue

        prev = dedup_best.get(symbol)
        if prev is None:
            dedup_best[symbol] = row
            continue

        prev_proxy = score_of(prev, "weighted_score")
        if prev_proxy is None:
            prev_proxy = score_of(prev, "global_score")
        if prev_proxy is None:
            prev_proxy = score_of(prev, "final_score")

        if prev_proxy is None or proxy > prev_proxy:
            dedup_best[symbol] = row
        elif proxy == prev_proxy:
            prev_setup = normalize_str(prev.get("setup_id"))
            curr_setup = normalize_str(row.get("setup_id"))
            if curr_setup < prev_setup:
                dedup_best[symbol] = row

    dedup_rows = list(dedup_best.values())

    def sort_key(row: Dict[str, Any]) -> Tuple[float, str, str]:
        gs = score_of(row, "global_score")
        ws = score_of(row, "weighted_score")
        fs = score_of(row, "final_score")
        top = gs if gs is not None else ws
        if top is None:
            top = fs
        return (-(top if top is not None else -1e18), normalize_str(row.get("setup_id")), symbol_of(row))

    ranked = sorted(dedup_rows, key=sort_key)
    reconstructed_top20 = ranked[:20]
    reconstructed_symbols = [symbol_of(r) for r in reconstructed_top20]
    reconstructed_symbol_set = set(reconstructed_symbols)

    published_not_in_reconstructed = sorted(list(visible_symbols - reconstructed_symbol_set))
    reconstructed_not_in_published = sorted(list(reconstructed_symbol_set - visible_symbols))

    cutoff_row = ranked[19] if len(ranked) >= 20 else None
    cutoff_score = None
    if cutoff_row is not None:
        cutoff_score = score_of(cutoff_row, "global_score")
        if cutoff_score is None:
            cutoff_score = score_of(cutoff_row, "weighted_score")
        if cutoff_score is None:
            cutoff_score = score_of(cutoff_row, "final_score")

    near_misses = []
    if cutoff_score is not None:
        for row in ranked[20:40]:
            proxy = score_of(row, "global_score")
            if proxy is None:
                proxy = score_of(row, "weighted_score")
            if proxy is None:
                proxy = score_of(row, "final_score")
            if proxy is None:
                continue
            near_misses.append(
                {
                    "symbol": symbol_of(row),
                    "setup_id": normalize_str(row.get("setup_id")),
                    "score_proxy": proxy,
                    "gap_to_cutoff": round(cutoff_score - proxy, 6),
                }
            )

    return {
        "upstream_key_used": upstream_key,
        "upstream_rows_total": len(upstream_rows),
        "dedup_symbols_total": len(dedup_rows),
        "reconstructed_top20_symbols": reconstructed_symbols,
        "published_top20_symbols": sorted(list(visible_symbols)),
        "published_not_in_reconstructed_top20": published_not_in_reconstructed,
        "reconstructed_not_in_published_top20": reconstructed_not_in_published,
        "cutoff_score_proxy": cutoff_score,
        "near_misses_21_to_40": near_misses[:20],
    }


def summarize_run(run: RunRecord) -> Dict[str, Any]:
    rows = list(run.trade_candidates)

    decision_counts = Counter(decision_of(r) for r in rows)
    setup_counts = Counter(setup_type_of(r) for r in rows)
    tradeability_counts = Counter(tradeability_of(r) for r in rows)
    entry_state_counts = Counter(entry_state_of(r) for r in rows)

    risk_ok_rows = [r for r in rows if bool_true(r.get("risk_acceptable"))]
    entry_eligible_rows = [r for r in rows if entry_eligible_tradeability(r)]
    risk_ok_entry_eligible_rows = [
        r for r in rows if bool_true(r.get("risk_acceptable")) and entry_eligible_tradeability(r)
    ]

    ordering_violations = find_ordering_violations(rows)
    setup_conc = setup_concentration(setup_counts, len(rows))

    by_setup_score = {
        setup: summarize_numeric([r for r in rows if setup_type_of(r) == setup], "global_score")
        for setup in sorted(setup_counts.keys())
    }

    visible_signals = {
        "top20_size": len(rows),
        "decision_counts": dict(sorted(decision_counts.items(), key=lambda kv: kv[0])),
        "setup_type_counts": dict(sorted(setup_counts.items(), key=lambda kv: kv[0])),
        "tradeability_class_counts": dict(sorted(tradeability_counts.items(), key=lambda kv: kv[0])),
        "entry_state_counts": dict(sorted(entry_state_counts.items(), key=lambda kv: kv[0])),
        "risk_acceptable_true": len(risk_ok_rows),
        "entry_eligible_tradeability": len(entry_eligible_rows),
        "risk_ok_and_entry_eligible": len(risk_ok_entry_eligible_rows),
        "global_score_all": summarize_numeric(rows, "global_score"),
        "setup_score_all": summarize_numeric(rows, "setup_score"),
        "global_score_by_setup_type": by_setup_score,
        "setup_concentration": setup_conc,
        "marginal_share_pct": round((tradeability_counts.get("MARGINAL", 0) / len(rows)) * 100.0, 2) if rows else None,
        "risk_ok_share_pct": round((len(risk_ok_rows) / len(rows)) * 100.0, 2) if rows else None,
        "entry_eligible_share_pct": round((len(entry_eligible_rows) / len(rows)) * 100.0, 2) if rows else None,
        "risk_ok_entry_eligible_share_pct": round((len(risk_ok_entry_eligible_rows) / len(rows)) * 100.0, 2) if rows else None,
    }

    optional_arrays = find_optional_upstream_arrays(run.raw_data, len(rows))
    upstream_best = choose_best_upstream_array(run.raw_data, len(rows))
    upstream_audit = None
    if upstream_best is not None:
        upstream_key, upstream_rows = upstream_best
        upstream_audit = upstream_inclusion_audit(upstream_key, upstream_rows, rows)

    return {
        "run_id": run.run_id,
        "timestamp_utc": run.timestamp_utc,
        "canonical_schema_version": run.canonical_schema_version,
        "source_file": str(run.path.relative_to(repo_root())),
        "visible_top20": visible_signals,
        "ordering_violations": ordering_violations,
        "top20_rows": [row_brief(r) for r in rows],
        "optional_upstream_arrays_found": optional_arrays,
        "upstream_inclusion_audit": upstream_audit,
    }


def aggregate_runs(run_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    decision_counts: Counter[str] = Counter()
    setup_counts: Counter[str] = Counter()
    tradeability_counts: Counter[str] = Counter()
    entry_state_counts: Counter[str] = Counter()

    total_top20_slots = 0
    risk_ok_total = 0
    entry_eligible_total = 0
    risk_ok_entry_eligible_total = 0
    ordering_violations_total = 0
    runs_with_upstream_data = 0

    for summary in run_summaries:
        visible = summary["visible_top20"]
        total_top20_slots += visible["top20_size"]
        risk_ok_total += visible["risk_acceptable_true"]
        entry_eligible_total += visible["entry_eligible_tradeability"]
        risk_ok_entry_eligible_total += visible["risk_ok_and_entry_eligible"]
        ordering_violations_total += len(summary["ordering_violations"])

        decision_counts.update(visible["decision_counts"])
        setup_counts.update(visible["setup_type_counts"])
        tradeability_counts.update(visible["tradeability_class_counts"])
        entry_state_counts.update(visible["entry_state_counts"])

        if summary["upstream_inclusion_audit"] is not None:
            runs_with_upstream_data += 1

    return {
        "runs_analyzed": len(run_summaries),
        "total_top20_slots": total_top20_slots,
        "decision_counts": dict(sorted(decision_counts.items(), key=lambda kv: kv[0])),
        "setup_type_counts": dict(sorted(setup_counts.items(), key=lambda kv: kv[0])),
        "tradeability_class_counts": dict(sorted(tradeability_counts.items(), key=lambda kv: kv[0])),
        "entry_state_counts": dict(sorted(entry_state_counts.items(), key=lambda kv: kv[0])),
        "risk_acceptable_true_total": risk_ok_total,
        "entry_eligible_tradeability_total": entry_eligible_total,
        "risk_ok_and_entry_eligible_total": risk_ok_entry_eligible_total,
        "marginal_share_pct": round((tradeability_counts.get("MARGINAL", 0) / total_top20_slots) * 100.0, 2) if total_top20_slots else None,
        "risk_ok_share_pct": round((risk_ok_total / total_top20_slots) * 100.0, 2) if total_top20_slots else None,
        "entry_eligible_share_pct": round((entry_eligible_total / total_top20_slots) * 100.0, 2) if total_top20_slots else None,
        "risk_ok_entry_eligible_share_pct": round((risk_ok_entry_eligible_total / total_top20_slots) * 100.0, 2) if total_top20_slots else None,
        "ordering_violations_total": ordering_violations_total,
        "runs_with_optional_upstream_data": runs_with_upstream_data,
    }


def fmt_counter(counter: Dict[str, Any]) -> str:
    if not counter:
        return "- none"
    return "\n".join(f"- `{k}`: {v}" for k, v in counter.items())


def fmt_rows(rows: List[Dict[str, Any]], limit: int = 20) -> str:
    if not rows:
        return "_none_"
    show = rows[:limit]
    header = (
        "| rank | symbol | decision | setup | tradeability | risk_ok | entry_ready | entry_state | global_score | reasons |\n"
        "|---:|---|---|---|---|---:|---:|---|---:|---|"
    )
    body = []
    for row in show:
        reasons = ", ".join(row.get("decision_reasons", []))
        body.append(
            "| {rank} | {symbol} | {decision} | {best_setup_type} | {tradeability_class} | {risk_acceptable} | {entry_ready} | {entry_state} | {global_score} | {reasons} |".format(
                rank=row.get("rank"),
                symbol=row.get("symbol"),
                decision=row.get("decision"),
                best_setup_type=row.get("best_setup_type"),
                tradeability_class=row.get("tradeability_class"),
                risk_acceptable=row.get("risk_acceptable"),
                entry_ready=row.get("entry_ready"),
                entry_state=row.get("entry_state"),
                global_score=row.get("global_score"),
                reasons=reasons,
            )
        )
    return header + "\n" + "\n".join(body)


def render_markdown(
    run_summaries: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    generated_at_utc: str,
) -> str:
    lines: List[str] = []
    lines.append("# Top20 Formation Audit")
    lines.append("")
    lines.append(f"- Generated at UTC: `{generated_at_utc}`")
    lines.append(f"- Runs analyzed: `{aggregate['runs_analyzed']}`")
    lines.append("")
    lines.append("## Aggregate summary")
    lines.append("")
    lines.append(fmt_counter(aggregate))
    lines.append("")

    for summary in run_summaries:
        lines.append(f"## Run `{summary['run_id']}`")
        lines.append("")
        lines.append(f"- Timestamp UTC: `{summary['timestamp_utc']}`")
        lines.append(f"- Schema: `{summary['canonical_schema_version']}`")
        lines.append(f"- Source file: `{summary['source_file']}`")
        lines.append("")
        lines.append("### Visible Top20 signals")
        lines.append(fmt_counter(summary["visible_top20"]))
        lines.append("")
        lines.append("### Ordering violations")
        if summary["ordering_violations"]:
            for item in summary["ordering_violations"]:
                lines.append(f"- `{item}`")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("### Optional upstream arrays found")
        if summary["optional_upstream_arrays_found"]:
            for item in summary["optional_upstream_arrays_found"]:
                lines.append(f"- `{item['key']}` length={item['length']} sample_keys={item['sample_keys']}")
        else:
            lines.append("- none")
        lines.append("")
        lines.append("### Upstream inclusion audit")
        if summary["upstream_inclusion_audit"] is None:
            lines.append("_No larger upstream candidate array found in this run JSON. Full inclusion audit not possible from this artifact alone._")
        else:
            lines.append(fmt_counter(summary["upstream_inclusion_audit"]))
        lines.append("")
        lines.append("### Published Top20 rows")
        lines.append(fmt_rows(summary["top20_rows"]))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_output(run_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    generated_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    aggregate = aggregate_runs(run_summaries)
    return {
        "analysis_name": "top20_formation_audit",
        "generated_at_utc": generated_at_utc,
        "aggregate": aggregate,
        "runs": run_summaries,
    }


def main() -> int:
    root = repo_root()
    all_run_paths = discover_run_files(root)
    all_runs = [parse_run(p) for p in all_run_paths]
    runs = [r for r in all_runs if r is not None]
    runs = sort_runs_desc(runs)

    selected_runs = runs[:5]
    if not selected_runs:
        raise SystemExit("No canonical run JSON files with trade_candidates were found.")

    run_summaries = [summarize_run(run) for run in selected_runs]
    payload = build_output(run_summaries)

    slug = utc_now_slug()
    out_dir = analysis_dir()
    json_path = out_dir / f"top20_formation_audit_{slug}.json"
    md_path = out_dir / f"top20_formation_audit_{slug}.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    md_content = render_markdown(
        run_summaries=run_summaries,
        aggregate=payload["aggregate"],
        generated_at_utc=payload["generated_at_utc"],
    )
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
