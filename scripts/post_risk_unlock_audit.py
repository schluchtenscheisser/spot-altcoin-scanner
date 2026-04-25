#!/usr/bin/env python3
"""
Post-risk-unlock blocker audit for Spot Altcoin Scanner.

Purpose
-------
Diagnose the next real blocker layer AFTER risk unlock, without changing config.

Questions answered
------------------
1) Among trade_candidates, how many are risk_acceptable=true?
2) Of those, how many are still blocked by tradeability?
3) Of those with entry-eligible tradeability, how many are blocked by entry_ready=false?
4) Of the "otherwise clean" cohort, what still blocks ENTER?
5) How often is the remaining blocker timing-only vs confirmation/tradeability/other?
6) How does this differ by setup_type across the latest N runs?

Outputs
-------
Writes both:
- reports/aux/post_risk_unlock_audit_<date>.json
- reports/aux/post_risk_unlock_audit_<date>.md

Design notes
------------
- Reads canonical trade_candidates JSON run files only.
- Auto-discovers run JSON files in the repo and ignores manifests / analysis outputs.
- Uses stdlib only.
- Does not modify scanner behavior.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


ENTRY_ELIGIBLE_TRADEABILITY = {"DIRECT_OK", "TRANCHE_OK"}
TIMING_REASONS = {"entry_chased", "entry_late", "entry_too_early"}
CONFIRMATION_REASONS = {"entry_not_confirmed", "retest_not_reclaimed"}
TRADEABILITY_REASONS = {"tradeability_marginal"}
HARD_LATE_ENTRY_REASONS = {"price_past_target_1", "effective_rr_insufficient"}
RISK_REASONS = {
    "risk_unacceptable",
    "risk_reward_unattractive",
    "stop_too_wide",
    "stop_too_tight",
    "STOP_TOO_WIDE",
    "STOP_TOO_TIGHT",
}
UNKNOWN_SENTINEL = "UNKNOWN"


@dataclass(frozen=True)
class RunRecord:
    path: Path
    run_id: str
    timestamp_utc: str
    canonical_schema_version: Optional[str]
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
    ignored_parts = {
        ".git",
        ".venv",
        "venv",
        "__pycache__",
    }

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
        trade_candidates=trade_candidates,
    )


def sort_runs_desc(runs: List[RunRecord]) -> List[RunRecord]:
    def key(run: RunRecord) -> Tuple[str, str]:
        return (run.timestamp_utc or "", run.run_id or "")
    return sorted(runs, key=key, reverse=True)


def normalize_reasons(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(x) for x in value if x is not None]
    if isinstance(value, str):
        return [value]
    return [str(value)]


def bool_true(value: Any) -> bool:
    return value is True


def get_setup_type(row: Dict[str, Any]) -> str:
    value = row.get("best_setup_type")
    return str(value) if value not in (None, "") else UNKNOWN_SENTINEL


def get_tradeability_class(row: Dict[str, Any]) -> str:
    value = row.get("tradeability_class")
    return str(value) if value not in (None, "") else UNKNOWN_SENTINEL


def get_entry_state(row: Dict[str, Any]) -> str:
    value = row.get("entry_state")
    return str(value) if value not in (None, "") else UNKNOWN_SENTINEL


def get_decision(row: Dict[str, Any]) -> str:
    value = row.get("decision")
    return str(value) if value not in (None, "") else UNKNOWN_SENTINEL


def symbol_of(row: Dict[str, Any]) -> str:
    value = row.get("symbol")
    return str(value) if value not in (None, "") else "UNKNOWN_SYMBOL"


def reasons_of(row: Dict[str, Any]) -> List[str]:
    return normalize_reasons(row.get("decision_reasons"))


def readiness_reasons_of(row: Dict[str, Any]) -> List[str]:
    return normalize_reasons(row.get("entry_readiness_reasons"))


def risk_ok(row: Dict[str, Any]) -> bool:
    return bool_true(row.get("risk_acceptable"))


def entry_ready(row: Dict[str, Any]) -> bool:
    return bool_true(row.get("entry_ready"))


def entry_eligible_tradeability(row: Dict[str, Any]) -> bool:
    return get_tradeability_class(row) in ENTRY_ELIGIBLE_TRADEABILITY


def direct_ok(row: Dict[str, Any]) -> bool:
    return get_tradeability_class(row) == "DIRECT_OK"


def tranche_ok(row: Dict[str, Any]) -> bool:
    return get_tradeability_class(row) == "TRANCHE_OK"


def non_enter(row: Dict[str, Any]) -> bool:
    return get_decision(row) != "ENTER"


def only_timing_reasons(row: Dict[str, Any]) -> bool:
    reasons = set(reasons_of(row))
    return bool(reasons) and reasons.issubset(TIMING_REASONS)


def reasons_counter(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter.update(reasons_of(row))
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def bucket_counter(rows: Iterable[Dict[str, Any]]) -> Dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        reasons = set(reasons_of(row))
        if reasons & TRADEABILITY_REASONS:
            counter["tradeability"] += 1
        if reasons & CONFIRMATION_REASONS:
            counter["confirmation"] += 1
        if reasons & TIMING_REASONS:
            counter["timing"] += 1
        if reasons & {"btc_regime_caution"}:
            counter["btc_regime"] += 1
        if reasons & HARD_LATE_ENTRY_REASONS:
            counter["late_entry_guard"] += 1
        if reasons & RISK_REASONS:
            counter["risk"] += 1
        other = reasons - (
            TRADEABILITY_REASONS
            | CONFIRMATION_REASONS
            | TIMING_REASONS
            | {"btc_regime_caution"}
            | HARD_LATE_ENTRY_REASONS
            | RISK_REASONS
        )
        if other:
            counter["other"] += 1
    return dict(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def setup_breakdown(rows: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    grouped: Dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        grouped[get_setup_type(row)]["rows"] += 1
        grouped[get_setup_type(row)][f"decision::{get_decision(row)}"] += 1
        grouped[get_setup_type(row)][f"tradeability::{get_tradeability_class(row)}"] += 1
        grouped[get_setup_type(row)][f"entry_state::{get_entry_state(row)}"] += 1
        grouped[get_setup_type(row)][f"risk_ok::{risk_ok(row)}"] += 1
        grouped[get_setup_type(row)][f"entry_ready::{entry_ready(row)}"] += 1
    return {
        setup: dict(sorted(counter.items(), key=lambda kv: kv[0]))
        for setup, counter in sorted(grouped.items(), key=lambda kv: kv[0])
    }


def row_brief(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "symbol": symbol_of(row),
        "decision": get_decision(row),
        "decision_reasons": reasons_of(row),
        "best_setup_type": get_setup_type(row),
        "tradeability_class": get_tradeability_class(row),
        "entry_ready": row.get("entry_ready"),
        "entry_readiness_reasons": readiness_reasons_of(row),
        "entry_state": get_entry_state(row),
        "risk_acceptable": row.get("risk_acceptable"),
        "setup_score": row.get("setup_score"),
        "global_score": row.get("global_score"),
        "distance_to_entry_pct": row.get("distance_to_entry_pct"),
        "risk_pct_to_stop": row.get("risk_pct_to_stop"),
        "rr_to_target_2": row.get("rr_to_target_2"),
    }


def summarize_run(run: RunRecord) -> Dict[str, Any]:
    rows = list(run.trade_candidates)

    risk_ok_rows = [r for r in rows if risk_ok(r)]
    risk_ok_non_enter = [r for r in risk_ok_rows if non_enter(r)]

    risk_ok_direct_ok = [r for r in risk_ok_rows if direct_ok(r)]
    risk_ok_tranche_ok = [r for r in risk_ok_rows if tranche_ok(r)]
    risk_ok_entry_eligible = [r for r in risk_ok_rows if entry_eligible_tradeability(r)]
    risk_ok_marginal = [r for r in risk_ok_rows if get_tradeability_class(r) == "MARGINAL"]
    risk_ok_fail = [r for r in risk_ok_rows if get_tradeability_class(r) == "FAIL"]
    risk_ok_unknown = [r for r in risk_ok_rows if get_tradeability_class(r) == "UNKNOWN"]

    risk_ok_entry_eligible_non_enter = [r for r in risk_ok_entry_eligible if non_enter(r)]
    risk_ok_entry_eligible_entry_ready = [
        r for r in risk_ok_entry_eligible if entry_ready(r)
    ]
    risk_ok_entry_eligible_entry_ready_non_enter = [
        r for r in risk_ok_entry_eligible_entry_ready if non_enter(r)
    ]
    timing_only_rows = [
        r for r in risk_ok_entry_eligible_entry_ready_non_enter if only_timing_reasons(r)
    ]

    result = {
        "run_id": run.run_id,
        "timestamp_utc": run.timestamp_utc,
        "canonical_schema_version": run.canonical_schema_version,
        "source_file": str(run.path.relative_to(repo_root())),
        "waterfall": {
            "top_candidates": len(rows),
            "risk_acceptable_true": len(risk_ok_rows),
            "risk_acceptable_true_direct_ok": len(risk_ok_direct_ok),
            "risk_acceptable_true_tranche_ok": len(risk_ok_tranche_ok),
            "risk_acceptable_true_entry_eligible_tradeability": len(risk_ok_entry_eligible),
            "risk_acceptable_true_marginal": len(risk_ok_marginal),
            "risk_acceptable_true_fail": len(risk_ok_fail),
            "risk_acceptable_true_unknown": len(risk_ok_unknown),
            "risk_ok_plus_entry_eligible_plus_entry_ready": len(risk_ok_entry_eligible_entry_ready),
            "risk_ok_plus_entry_eligible_plus_entry_ready_non_enter": len(
                risk_ok_entry_eligible_entry_ready_non_enter
            ),
            "timing_only_after_risk_tradeability_readiness": len(timing_only_rows),
        },
        "distributions": {
            "decision": dict(
                sorted(Counter(get_decision(r) for r in rows).items(), key=lambda kv: kv[0])
            ),
            "tradeability_class": dict(
                sorted(Counter(get_tradeability_class(r) for r in rows).items(), key=lambda kv: kv[0])
            ),
            "entry_ready": dict(
                sorted(Counter(str(r.get("entry_ready")) for r in rows).items(), key=lambda kv: kv[0])
            ),
            "entry_state": dict(
                sorted(Counter(get_entry_state(r) for r in rows).items(), key=lambda kv: kv[0])
            ),
            "best_setup_type": dict(
                sorted(Counter(get_setup_type(r) for r in rows).items(), key=lambda kv: kv[0])
            ),
        },
        "post_risk_blockers": {
            "all_risk_ok_non_enter_reason_counts": reasons_counter(risk_ok_non_enter),
            "all_risk_ok_non_enter_bucket_counts": bucket_counter(risk_ok_non_enter),
            "risk_ok_entry_eligible_non_enter_reason_counts": reasons_counter(
                risk_ok_entry_eligible_non_enter
            ),
            "risk_ok_entry_eligible_non_enter_bucket_counts": bucket_counter(
                risk_ok_entry_eligible_non_enter
            ),
            "risk_ok_entry_eligible_entry_ready_non_enter_reason_counts": reasons_counter(
                risk_ok_entry_eligible_entry_ready_non_enter
            ),
            "risk_ok_entry_eligible_entry_ready_non_enter_bucket_counts": bucket_counter(
                risk_ok_entry_eligible_entry_ready_non_enter
            ),
        },
        "setup_breakdown_all_rows": setup_breakdown(rows),
        "setup_breakdown_risk_ok_rows": setup_breakdown(risk_ok_rows),
        "timing_only_rows": [row_brief(r) for r in timing_only_rows],
        "risk_ok_entry_eligible_entry_ready_non_enter_rows": [
            row_brief(r) for r in risk_ok_entry_eligible_entry_ready_non_enter
        ],
    }
    return result


def aggregate_runs(run_summaries: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg_waterfall: Counter[str] = Counter()
    agg_reason_counts_risk_ok: Counter[str] = Counter()
    agg_reason_counts_entry_eligible: Counter[str] = Counter()
    agg_reason_counts_clean_non_enter: Counter[str] = Counter()
    agg_bucket_counts_risk_ok: Counter[str] = Counter()
    agg_bucket_counts_entry_eligible: Counter[str] = Counter()
    agg_bucket_counts_clean_non_enter: Counter[str] = Counter()
    agg_decision: Counter[str] = Counter()
    agg_tradeability: Counter[str] = Counter()
    agg_entry_ready: Counter[str] = Counter()
    agg_entry_state: Counter[str] = Counter()
    agg_setup_type: Counter[str] = Counter()

    per_setup: Dict[str, Counter[str]] = defaultdict(Counter)

    for summary in run_summaries:
        agg_waterfall.update(summary["waterfall"])
        agg_reason_counts_risk_ok.update(
            summary["post_risk_blockers"]["all_risk_ok_non_enter_reason_counts"]
        )
        agg_reason_counts_entry_eligible.update(
            summary["post_risk_blockers"]["risk_ok_entry_eligible_non_enter_reason_counts"]
        )
        agg_reason_counts_clean_non_enter.update(
            summary["post_risk_blockers"][
                "risk_ok_entry_eligible_entry_ready_non_enter_reason_counts"
            ]
        )
        agg_bucket_counts_risk_ok.update(
            summary["post_risk_blockers"]["all_risk_ok_non_enter_bucket_counts"]
        )
        agg_bucket_counts_entry_eligible.update(
            summary["post_risk_blockers"]["risk_ok_entry_eligible_non_enter_bucket_counts"]
        )
        agg_bucket_counts_clean_non_enter.update(
            summary["post_risk_blockers"][
                "risk_ok_entry_eligible_entry_ready_non_enter_bucket_counts"
            ]
        )
        agg_decision.update(summary["distributions"]["decision"])
        agg_tradeability.update(summary["distributions"]["tradeability_class"])
        agg_entry_ready.update(summary["distributions"]["entry_ready"])
        agg_entry_state.update(summary["distributions"]["entry_state"])
        agg_setup_type.update(summary["distributions"]["best_setup_type"])

        for setup, counters in summary["setup_breakdown_risk_ok_rows"].items():
            per_setup[setup].update(counters)

    return {
        "runs_analyzed": len(run_summaries),
        "waterfall_sums": dict(sorted(agg_waterfall.items(), key=lambda kv: kv[0])),
        "distribution_sums": {
            "decision": dict(sorted(agg_decision.items(), key=lambda kv: kv[0])),
            "tradeability_class": dict(sorted(agg_tradeability.items(), key=lambda kv: kv[0])),
            "entry_ready": dict(sorted(agg_entry_ready.items(), key=lambda kv: kv[0])),
            "entry_state": dict(sorted(agg_entry_state.items(), key=lambda kv: kv[0])),
            "best_setup_type": dict(sorted(agg_setup_type.items(), key=lambda kv: kv[0])),
        },
        "post_risk_blockers": {
            "all_risk_ok_non_enter_reason_counts": dict(
                sorted(agg_reason_counts_risk_ok.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "all_risk_ok_non_enter_bucket_counts": dict(
                sorted(agg_bucket_counts_risk_ok.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "risk_ok_entry_eligible_non_enter_reason_counts": dict(
                sorted(agg_reason_counts_entry_eligible.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "risk_ok_entry_eligible_non_enter_bucket_counts": dict(
                sorted(agg_bucket_counts_entry_eligible.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "risk_ok_entry_eligible_entry_ready_non_enter_reason_counts": dict(
                sorted(agg_reason_counts_clean_non_enter.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
            "risk_ok_entry_eligible_entry_ready_non_enter_bucket_counts": dict(
                sorted(agg_bucket_counts_clean_non_enter.items(), key=lambda kv: (-kv[1], kv[0]))
            ),
        },
        "setup_breakdown_risk_ok_rows_sum": {
            setup: dict(sorted(counter.items(), key=lambda kv: kv[0]))
            for setup, counter in sorted(per_setup.items(), key=lambda kv: kv[0])
        },
    }


def fmt_counter(counter: Dict[str, int]) -> str:
    if not counter:
        return "- none"
    return "\n".join(f"- `{k}`: {v}" for k, v in counter.items())


def fmt_row_table(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "_none_"

    header = (
        "| symbol | decision | setup | tradeability | entry_ready | entry_state | reasons |\n"
        "|---|---|---|---|---:|---|---|"
    )
    body = []
    for row in rows:
        reasons = ", ".join(row.get("decision_reasons", []))
        body.append(
            "| {symbol} | {decision} | {best_setup_type} | {tradeability_class} | {entry_ready} | {entry_state} | {reasons} |".format(
                symbol=row.get("symbol"),
                decision=row.get("decision"),
                best_setup_type=row.get("best_setup_type"),
                tradeability_class=row.get("tradeability_class"),
                entry_ready=row.get("entry_ready"),
                entry_state=row.get("entry_state"),
                reasons=reasons,
            )
        )
    return header + "\n" + "\n".join(body)


def render_markdown(
    run_summaries: List[Dict[str, Any]],
    aggregate: Dict[str, Any],
    generated_at_utc: str,
    selected_count: int,
) -> str:
    lines: List[str] = []
    lines.append("# Post-Risk-Unlock Blocker Audit")
    lines.append("")
    lines.append(f"- Generated at UTC: `{generated_at_utc}`")
    lines.append(f"- Runs analyzed: `{selected_count}`")
    lines.append("")
    lines.append("## Aggregate summary")
    lines.append("")
    lines.append("### Waterfall sums")
    lines.append(fmt_counter(aggregate["waterfall_sums"]))
    lines.append("")
    lines.append("### Aggregate blocker buckets")
    lines.append("")
    lines.append("#### All risk_ok non-ENTER")
    lines.append(fmt_counter(aggregate["post_risk_blockers"]["all_risk_ok_non_enter_bucket_counts"]))
    lines.append("")
    lines.append("#### risk_ok + entry-eligible non-ENTER")
    lines.append(
        fmt_counter(aggregate["post_risk_blockers"]["risk_ok_entry_eligible_non_enter_bucket_counts"])
    )
    lines.append("")
    lines.append("#### risk_ok + entry-eligible + entry_ready non-ENTER")
    lines.append(
        fmt_counter(
            aggregate["post_risk_blockers"][
                "risk_ok_entry_eligible_entry_ready_non_enter_bucket_counts"
            ]
        )
    )
    lines.append("")
    lines.append("### Aggregate blocker reasons")
    lines.append("")
    lines.append("#### All risk_ok non-ENTER")
    lines.append(fmt_counter(aggregate["post_risk_blockers"]["all_risk_ok_non_enter_reason_counts"]))
    lines.append("")
    lines.append("#### risk_ok + entry-eligible non-ENTER")
    lines.append(
        fmt_counter(aggregate["post_risk_blockers"]["risk_ok_entry_eligible_non_enter_reason_counts"])
    )
    lines.append("")
    lines.append("#### risk_ok + entry-eligible + entry_ready non-ENTER")
    lines.append(
        fmt_counter(
            aggregate["post_risk_blockers"][
                "risk_ok_entry_eligible_entry_ready_non_enter_reason_counts"
            ]
        )
    )
    lines.append("")

    for summary in run_summaries:
        lines.append(f"## Run `{summary['run_id']}`")
        lines.append("")
        lines.append(f"- Timestamp UTC: `{summary['timestamp_utc']}`")
        lines.append(f"- Schema: `{summary['canonical_schema_version']}`")
        lines.append(f"- Source file: `{summary['source_file']}`")
        lines.append("")
        lines.append("### Waterfall")
        lines.append(fmt_counter(summary["waterfall"]))
        lines.append("")
        lines.append("### Distributions")
        lines.append("")
        for section_name, counter in summary["distributions"].items():
            lines.append(f"#### {section_name}")
            lines.append(fmt_counter(counter))
            lines.append("")
        lines.append("### Post-risk blocker buckets")
        lines.append("")
        for section_name, counter in summary["post_risk_blockers"].items():
            if not section_name.endswith("_bucket_counts"):
                continue
            lines.append(f"#### {section_name}")
            lines.append(fmt_counter(counter))
            lines.append("")
        lines.append("### Post-risk blocker reasons")
        lines.append("")
        for section_name, counter in summary["post_risk_blockers"].items():
            if not section_name.endswith("_reason_counts"):
                continue
            lines.append(f"#### {section_name}")
            lines.append(fmt_counter(counter))
            lines.append("")
        lines.append("### Timing-only rows")
        lines.append(fmt_row_table(summary["timing_only_rows"]))
        lines.append("")
        lines.append("### Clean-but-not-ENTER rows")
        lines.append(fmt_row_table(summary["risk_ok_entry_eligible_entry_ready_non_enter_rows"]))
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_output(run_summaries: List[Dict[str, Any]], selected_count: int) -> Dict[str, Any]:
    generated_at_utc = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    aggregate = aggregate_runs(run_summaries)
    return {
        "analysis_name": "post_risk_unlock_audit",
        "generated_at_utc": generated_at_utc,
        "runs_analyzed": selected_count,
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
    payload = build_output(run_summaries, selected_count=len(selected_runs))

    slug = utc_now_slug()
    out_dir = analysis_dir()
    json_path = out_dir / f"post_risk_unlock_audit_{slug}.json"
    md_path = out_dir / f"post_risk_unlock_audit_{slug}.md"

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    md_content = render_markdown(
        run_summaries=run_summaries,
        aggregate=payload["aggregate"],
        generated_at_utc=payload["generated_at_utc"],
        selected_count=payload["runs_analyzed"],
    )
    with md_path.open("w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
