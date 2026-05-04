#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
import zipfile
from pathlib import Path
from typing import Any

DATES = ["2026-04-26", "2026-04-27", "2026-04-28", "2026-04-29", "2026-04-30", "2026-05-01", "2026-05-02", "2026-05-03"]
TOP_BUCKETS = {"confirmed_candidates", "early_candidates"}
FORBIDDEN_OUTPUT_ROOTS = ["reports/runs", "reports/daily", "reports/index", "snapshots/runs", "reports/analysis"]
DEFAULT_BUCKET_CFG = {"watchlist": 50.0, "early": 60.0, "confirmed": 65.0}


def _finite(v: Any) -> bool:
    return isinstance(v, (int, float)) and math.isfinite(float(v))


def _priority(mpc: float, sc: float, eps: float, grade: float) -> float:
    return 0.30 * mpc + 0.35 * sc + 0.20 * eps + 0.15 * grade


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


# ---------------------------------------------------------------------------
# Field accessors — all fields are in nested sub-dicts in the diagnostic schema
# ---------------------------------------------------------------------------

def _decision(r: dict) -> dict:
    out = dict(r.get("decision") or {})
    for key in ("decision_bucket", "entry_pattern", "entry_pattern_score", "priority_score"):
        if key not in out and key in r:
            out[key] = r.get(key)
    return out

def _phase(r: dict) -> dict:
    out = dict(r.get("phase") or {})
    for key in ("market_phase", "market_phase_confidence"):
        if key not in out and key in r:
            out[key] = r.get(key)
    return out

def _state(r: dict) -> dict:
    out = dict(r.get("state") or {})
    for key in ("state_machine_state", "state_confidence"):
        if key not in out and key in r:
            out[key] = r.get(key)
    return out

def _pattern(r: dict) -> dict:
    return r.get("pattern") or {}


def _replay_bucket(r: dict[str, Any], cfg: dict[str, float]) -> str:
    """Replay T12 bucket assignment with execution_status forced to marginal."""
    state_val = str(_state(r).get("state_machine_state") or "")
    phase_val = str(_phase(r).get("market_phase") or "")
    entry = str(_decision(r).get("entry_pattern") or "none")
    sc = _state(r).get("state_confidence")

    if state_val in {"", "rejected"}:
        return "discarded"
    if phase_val == "none":
        return "discarded"

    c_gate = _finite(sc) and float(sc) >= cfg["confirmed"]
    e_gate = _finite(sc) and float(sc) >= cfg["early"]
    w_gate = _finite(sc) and float(sc) >= cfg["watchlist"]

    # execution_status forced to marginal — only "fail" blocks top buckets
    exec_status = "marginal"

    if state_val == "confirmed_ready" and entry != "none" and c_gate and exec_status != "fail":
        return "confirmed_candidates"
    if state_val == "confirmed_ready" and entry == "none":
        return "late_monitor"
    if state_val == "early_ready" and entry != "none" and e_gate and exec_status != "fail":
        return "early_candidates"
    if state_val == "early_ready" and entry == "none":
        return "watchlist"
    if state_val == "watch" and w_gate:
        return "watchlist"
    if state_val in {"late", "chased"} and phase_val != "none":
        return "late_monitor"
    return "discarded"


def _find_archives(inp: Path) -> dict[str, tuple[Path, str]]:
    found = {}
    zip_files = sorted(inp.glob("*.zip"))
    print(f"[T26] Found {len(zip_files)} ZIP file(s) in {inp}", flush=True)
    for zp in zip_files:
        with zipfile.ZipFile(zp) as zf:
            for name in zf.namelist():
                if not name.endswith("symbol_diagnostics.jsonl.gz"):
                    continue
                if "/daily-" not in name:
                    continue
                for d in DATES:
                    if f"/{d.replace('-', '/')}/" in name:
                        print(f"[T26]   {d} -> {zp.name} :: {name}", flush=True)
                        found[d] = (zp, name)
    missing = [d for d in DATES if d not in found]
    if missing:
        raise ValueError(f"Missing expected dates: {', '.join(missing)}")
    return found


def _read_diag(zip_path: Path, member: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        raw = zf.read(member)
    return [json.loads(x) for x in gzip.decompress(raw).decode("utf-8").splitlines() if x.strip()]


def _rank(symbol: str, items: list[dict[str, Any]], score_overrides: dict[str, float] | None = None) -> int:
    score_overrides = score_overrides or {}
    ranked = sorted(
        items,
        key=lambda r: (
            -(score_overrides.get(r.get("symbol"), _decision(r).get("priority_score", float("-inf")))),
            str(r.get("symbol") or ""),
        ),
    )
    for i, r in enumerate(ranked, 1):
        if r.get("symbol") == symbol:
            return i
    return -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="data/shadow-live-zips")
    ap.add_argument("--output-dir", default="reports/aux/execution_depth_analysis/2026-04-26_to_2026-05-03")
    args = ap.parse_args()

    repo_root = Path.cwd().resolve()
    out = Path(args.output_dir)
    _validate_output_dir(out, repo_root)

    mapping = _find_archives(Path(args.input_dir))

    all_records: list[dict[str, Any]] = []
    spread_fields: set[str] = set()

    for d, (zp, member) in mapping.items():
        recs = _read_diag(zp, member)
        print(f"[T26] {d}: loaded {len(recs)} records", flush=True)
        for rec in recs:
            rec = dict(rec)
            rec["_date"] = d
            all_records.append(rec)
            for k in rec:
                lk = k.lower()
                if "spread" in lk or "slippage" in lk:
                    spread_fields.add(k)

    # Count execution status distribution for debug
    from collections import Counter
    status_counts = Counter(r.get("execution_status_raw") for r in all_records)
    print(f"[T26] execution_status_raw distribution: {dict(status_counts)}", flush=True)

    # Build per-(date, bucket) population index for ranking — uses nested decision.decision_bucket
    bucket_pop: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in all_records:
        b = _decision(r).get("decision_bucket")
        if b in TOP_BUCKETS:
            bucket_pop.setdefault((r["_date"], b), []).append(r)

    fail_rows = []
    marg_rows = []

    for r in all_records:
        st = r.get("execution_status_raw")

        if st == "fail":
            mpc = _phase(r).get("market_phase_confidence")
            sc  = _state(r).get("state_confidence")
            eps = _decision(r).get("entry_pattern_score")

            replay_derivable = all(_finite(v) for v in (mpc, sc, eps))

            # Depth ratio — these fields don't exist in pre-T24 diagnostics; will be None
            avail = r.get("available_depth_1pct_usdt")
            if avail is None:
                avail = r.get("available_depth_usdt")
            thresh = r.get("depth_threshold_1pct_usdt")
            depth_ratio_derivable = _finite(avail) and _finite(thresh) and thresh
            ratio = (float(avail) / float(thresh)) if depth_ratio_derivable else None

            if ratio is None:
                rec_factor  = None
                t75 = t50 = t25 = None
            elif ratio >= 1.0:
                rec_factor = 1.00; t75 = t50 = t25 = True
            elif ratio >= 0.75:
                rec_factor = 0.75; t75 = True;  t50 = True;  t25 = True
            elif ratio >= 0.50:
                rec_factor = 0.50; t75 = False; t50 = True;  t25 = True
            elif ratio >= 0.25:
                rec_factor = 0.25; t75 = False; t50 = False; t25 = True
            else:
                rec_factor = 0.00; t75 = False; t50 = False; t25 = False

            bcf = _replay_bucket(r, DEFAULT_BUCKET_CFG) if replay_derivable else None
            actual_bucket = _decision(r).get("decision_bucket")

            fail_rows.append({
                "symbol":                              r.get("symbol"),
                "date":                                r["_date"],
                "replay_derivable":                    replay_derivable,
                "decision_bucket_actual":              actual_bucket,
                "decision_bucket_without_execution_block": bcf,
                "structurally_actionable":             bcf in TOP_BUCKETS if bcf else False,
                "state_machine_state":                 _state(r).get("state_machine_state"),
                "market_phase":                        _phase(r).get("market_phase"),
                "market_phase_confidence":             mpc,
                "entry_pattern":                       _decision(r).get("entry_pattern"),
                "entry_pattern_score":                 eps,
                "priority_score_actual":               _decision(r).get("priority_score"),
                "priority_score_counterfactual_marginal": (
                    _priority(float(mpc), float(sc), float(eps), 40.0) if replay_derivable else None
                ),
                "execution_status_raw":                "fail",
                "execution_reason_raw":                r.get("execution_reason_raw"),
                "available_depth_usdt":                avail,
                "depth_threshold_1pct_usdt":           thresh,
                "available_depth_ratio":               ratio,
                "clearing_notional_fraction":          ratio,
                "recommended_position_factor":         rec_factor,
                "tradable_at_75pct":                   t75,
                "tradable_at_50pct":                   t50,
                "tradable_at_25pct":                   t25,
                "depth_ratio_derivable":               bool(depth_ratio_derivable),
            })

        elif st == "marginal" and _decision(r).get("decision_bucket") in TOP_BUCKETS:
            mpc = _phase(r).get("market_phase_confidence")
            sc  = _state(r).get("state_confidence")
            eps = _decision(r).get("entry_pattern_score")

            if not all(_finite(v) for v in (mpc, sc, eps)):
                continue

            symbol = r.get("symbol")
            bucket = _decision(r).get("decision_bucket")
            pop    = bucket_pop.get((r["_date"], bucket), [])

            cf = {
                50.0:  _priority(float(mpc), float(sc), float(eps), 50.0),
                60.0:  _priority(float(mpc), float(sc), float(eps), 60.0),
                75.0:  _priority(float(mpc), float(sc), float(eps), 75.0),
                100.0: _priority(float(mpc), float(sc), float(eps), 100.0),
            }

            rank_actual   = _rank(symbol, pop)
            rank_cf_50    = _rank(symbol, pop, {symbol: cf[50.0]})
            rank_cf_60    = _rank(symbol, pop, {symbol: cf[60.0]})
            rank_cf_75    = _rank(symbol, pop, {symbol: cf[75.0]})
            rank_cf_100   = _rank(symbol, pop, {symbol: cf[100.0]})

            marg_rows.append({
                "symbol":                       symbol,
                "date":                         r["_date"],
                "decision_bucket":              bucket,
                "state_machine_state":          _state(r).get("state_machine_state"),
                "market_phase":                 _phase(r).get("market_phase"),
                "market_phase_confidence":      mpc,
                "state_confidence":             sc,
                "entry_pattern":                _decision(r).get("entry_pattern"),
                "entry_pattern_score":          eps,
                "priority_score_actual":        _decision(r).get("priority_score"),
                "priority_score_cf_50":         cf[50.0],
                "priority_score_cf_60":         cf[60.0],
                "priority_score_cf_75":         cf[75.0],
                "priority_score_cf_100":        cf[100.0],
                "rank_actual":                  rank_actual,
                "rank_cf_50":                   rank_cf_50,
                "rank_cf_60":                   rank_cf_60,
                "rank_cf_75":                   rank_cf_75,
                "rank_cf_100":                  rank_cf_100,
                "rank_displacement_cf_100":     rank_cf_100 - rank_actual,
            })

    print(f"[T26] fail_rows: {len(fail_rows)}, marg_rows: {len(marg_rows)}", flush=True)

    # Aggregate summaries
    actionable     = [x for x in fail_rows if x["structurally_actionable"]]
    depth_derivable = [x for x in fail_rows if x["depth_ratio_derivable"]]

    fail_summary_lines = [
        "# T26 Summary — Fail-Class Depth Counterfactual\n",
        f"Total fail cases (all days):          {len(fail_rows)}",
        f"replay_derivable = True:              {sum(1 for x in fail_rows if x['replay_derivable'])}",
        f"depth_ratio_derivable = True:         {len(depth_derivable)}  (expected 0 for pre-T24 data)",
        f"structurally_actionable (True):       {len(actionable)}",
        "",
        "## Structurally actionable by counterfactual bucket",
    ]
    from collections import Counter
    sa_bucket = Counter(x["decision_bucket_without_execution_block"] for x in actionable)
    for bkt, cnt in sa_bucket.most_common():
        fail_summary_lines.append(f"  {bkt}: {cnt}")

    fail_summary_lines += [
        "",
        "## By actual decision bucket (all fail cases)",
    ]
    actual_bucket_counts = Counter(x["decision_bucket_actual"] for x in fail_rows)
    for bkt, cnt in actual_bucket_counts.most_common():
        fail_summary_lines.append(f"  {bkt}: {cnt}")

    fail_summary_lines += [
        "",
        "## Per-day fail counts",
    ]
    day_counts = Counter(x["date"] for x in fail_rows)
    for day in DATES:
        fail_summary_lines.append(f"  {day}: {day_counts.get(day, 0)}")

    marg_summary_lines = [
        "# T26 Summary — Marginal-Class Priority Impact\n",
        f"Total marginal in confirmed/early (all days): {len(marg_rows)}",
        "",
        "## Per-day counts",
    ]
    marg_day_counts = Counter(x["date"] for x in marg_rows)
    for day in DATES:
        marg_summary_lines.append(f"  {day}: {marg_day_counts.get(day, 0)}")

    if marg_rows:
        deltas = [x["priority_score_cf_100"] - x["priority_score_actual"] for x in marg_rows]
        displacements = [x["rank_displacement_cf_100"] for x in marg_rows]
        marg_summary_lines += [
            "",
            f"## Priority score delta (cf_100 - actual)",
            f"  mean:   {sum(deltas)/len(deltas):.2f}",
            f"  min:    {min(deltas):.2f}",
            f"  max:    {max(deltas):.2f}",
            "",
            f"## Rank displacement (cf_100 vs actual, negative = better rank)",
            f"  mean:   {sum(displacements)/len(displacements):.2f}",
            f"  improved >= 5 ranks: {sum(1 for d in displacements if d <= -5)}",
            f"  no change (0):       {sum(1 for d in displacements if d == 0)}",
            f"  worsened:            {sum(1 for d in displacements if d > 0)}",
            "",
            "## By bucket",
        ]
        marg_bucket = Counter(x["decision_bucket"] for x in marg_rows)
        for bkt, cnt in marg_bucket.most_common():
            marg_summary_lines.append(f"  {bkt}: {cnt}")

    report_lines = [
        "# T26 Analysis Report\n",
        "## Data source",
        f"8 Shadow-Live Daily runs: {DATES[0]} through {DATES[-1]}",
        "Primary source: symbol_diagnostics.jsonl.gz (pre-T24 data; T24 report fields not present)",
        "",
        "## Replay logic",
        "Analysis-only replay mirrors scanner/decision/buckets.py gating:",
        "entry_pattern + confidence gates + fail-only execution block.",
        "Bucket fields read from nested sub-dicts: decision, phase, state, pattern.",
        "",
        "## Spread/slippage availability",
        "Fields found: " + (", ".join(sorted(spread_fields)) if spread_fields else "none"),
        "",
        "## Key findings",
        f"- Total fail cases:                  {len(fail_rows)}",
        f"- Total marginal in top buckets:     {len(marg_rows)}",
        f"- Structurally actionable fail cases: {len(actionable)}",
        f"- depth_ratio_derivable:             {len(depth_derivable)} (0 expected — available_depth_1pct_usdt absent in pre-T27 diagnostics)",
        "",
        "## Limitations",
        "1. Profitability not assessed — T26 quantifies bottleneck size only.",
        "2. Depth-to-notional scaling assumed linear (unverifiable without raw depth data).",
        "3. depth_ratio_derivable = False for all fail records: available_depth_usdt and",
        "   depth_threshold_1pct_usdt are absent from pre-T24 diagnostic schema.",
        "   The follow-on Spec-Ticket must add these fields to symbol_diagnostics.jsonl.gz.",
        "4. Spread/slippage fields absent — depth is the only measurable execution bottleneck.",
        "5. Pre-T24 data — T24 execution-aware report fields absent (not an error).",
    ]

    out.mkdir(parents=True, exist_ok=True)
    (out / "fail_cases_full.jsonl").write_text(
        "\n".join(json.dumps(x) for x in fail_rows) + "\n", encoding="utf-8"
    )
    (out / "marginal_candidate_cases_full.jsonl").write_text(
        "\n".join(json.dumps(x) for x in marg_rows) + "\n", encoding="utf-8"
    )
    (out / "summary_fail_depth_counterfactual.md").write_text(
        "\n".join(fail_summary_lines) + "\n", encoding="utf-8"
    )
    (out / "summary_marginal_priority_impact.md").write_text(
        "\n".join(marg_summary_lines) + "\n", encoding="utf-8"
    )
    (out / "analysis_report.md").write_text(
        "\n".join(report_lines) + "\n", encoding="utf-8"
    )
    print("[T26] Done.", flush=True)


if __name__ == "__main__":
    main()
    
