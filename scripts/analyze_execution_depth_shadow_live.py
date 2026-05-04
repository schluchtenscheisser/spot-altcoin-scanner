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


def _replay_bucket(record: dict[str, Any], cfg: dict[str, float]) -> str:
    state = str(record.get("state_machine_state") or "")
    phase = str(record.get("market_phase") or "")
    entry = str(record.get("entry_pattern") or "none")
    sc = record.get("state_confidence")
    exec_status = "marginal"
    if state in {"", "rejected"}:
        return "discarded"
    if phase == "none":
        return "discarded"
    c_gate = _finite(sc) and float(sc) >= cfg["confirmed"]
    e_gate = _finite(sc) and float(sc) >= cfg["early"]
    w_gate = _finite(sc) and float(sc) >= cfg["watchlist"]
    if state == "confirmed_ready" and entry != "none" and c_gate and exec_status != "fail":
        return "confirmed_candidates"
    if state == "confirmed_ready" and entry == "none":
        return "late_monitor"
    if state == "early_ready" and entry != "none" and e_gate and exec_status != "fail":
        return "early_candidates"
    if state == "early_ready" and entry == "none":
        return "watchlist"
    if state == "watch" and w_gate:
        return "watchlist"
    if state in {"late", "chased"} and phase != "none":
        return "late_monitor"
    return "discarded"


def _find_archives(inp: Path) -> dict[str, tuple[Path, str]]:
    found = {}
    for zp in sorted(inp.glob("*.zip")):
        with zipfile.ZipFile(zp) as zf:
            for name in zf.namelist():
                if not name.endswith("symbol_diagnostics.jsonl.gz"):
                    continue
                for d in DATES:
                    if f"/{d.replace('-', '/')}/" in name:
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
    ranked = sorted(items, key=lambda r: (-(score_overrides.get(r.get("symbol"), r.get("priority_score", float("-inf")))), str(r.get("symbol") or "")))
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
        for rec in _read_diag(zp, member):
            rec = dict(rec)
            rec["_date"] = d
            all_records.append(rec)
            for k in rec:
                lk = k.lower()
                if "spread" in lk or "slippage" in lk:
                    spread_fields.add(k)

    bucket_pop: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for r in all_records:
        b = r.get("decision_bucket")
        if b in TOP_BUCKETS:
            bucket_pop.setdefault((r["_date"], b), []).append(r)

    fail_rows = []
    marg_rows = []
    for r in all_records:
        st = r.get("execution_status_raw")
        if st == "fail":
            mpc, sc, eps = r.get("market_phase_confidence"), r.get("state_confidence"), r.get("entry_pattern_score")
            replay_derivable = all(_finite(v) for v in (mpc, sc, eps))
            ratio = None
            if _finite(r.get("available_depth_usdt")) and _finite(r.get("depth_threshold_1pct_usdt")) and r.get("depth_threshold_1pct_usdt"):
                ratio = float(r["available_depth_usdt"]) / float(r["depth_threshold_1pct_usdt"])
            rec = None if ratio is None else (1.0 if ratio >= 1.0 else 0.75 if ratio >= 0.75 else 0.5 if ratio >= 0.5 else 0.25 if ratio >= 0.25 else 0.0)
            bcf = _replay_bucket(r, DEFAULT_BUCKET_CFG) if replay_derivable else None
            fail_rows.append({"symbol": r.get("symbol"), "date": r["_date"], "replay_derivable": replay_derivable, "decision_bucket_actual": r.get("decision_bucket"), "decision_bucket_without_execution_block": bcf, "structurally_actionable": bcf in TOP_BUCKETS if bcf else False, "state_machine_state": r.get("state_machine_state"), "market_phase": r.get("market_phase"), "market_phase_confidence": mpc, "entry_pattern": r.get("entry_pattern"), "entry_pattern_score": eps, "priority_score_actual": r.get("priority_score"), "priority_score_counterfactual_marginal": _priority(float(mpc), float(sc), float(eps), 40.0) if replay_derivable else None, "execution_status_raw": "fail", "execution_reason_raw": r.get("execution_reason_raw"), "available_depth_usdt": r.get("available_depth_usdt"), "depth_threshold_1pct_usdt": r.get("depth_threshold_1pct_usdt"), "available_depth_ratio": ratio, "clearing_notional_fraction": ratio, "recommended_position_factor": rec, "tradable_at_75pct": None if ratio is None else ratio >= 0.75, "tradable_at_50pct": None if ratio is None else ratio >= 0.50, "tradable_at_25pct": None if ratio is None else ratio >= 0.25, "depth_ratio_derivable": ratio is not None})
        elif st == "marginal" and r.get("decision_bucket") in TOP_BUCKETS:
            mpc, sc, eps = r.get("market_phase_confidence"), r.get("state_confidence"), r.get("entry_pattern_score")
            if not all(_finite(v) for v in (mpc, sc, eps)):
                continue
            symbol = r.get("symbol")
            pop = bucket_pop[(r["_date"], r.get("decision_bucket"))]
            cf = {50.0: _priority(float(mpc), float(sc), float(eps), 50.0), 60.0: _priority(float(mpc), float(sc), float(eps), 60.0), 75.0: _priority(float(mpc), float(sc), float(eps), 75.0), 100.0: _priority(float(mpc), float(sc), float(eps), 100.0)}
            row = {"symbol": symbol, "date": r["_date"], "decision_bucket": r.get("decision_bucket"), "state_machine_state": r.get("state_machine_state"), "market_phase": r.get("market_phase"), "market_phase_confidence": mpc, "state_confidence": sc, "entry_pattern": r.get("entry_pattern"), "entry_pattern_score": eps, "priority_score_actual": r.get("priority_score"), "priority_score_cf_50": cf[50.0], "priority_score_cf_60": cf[60.0], "priority_score_cf_75": cf[75.0], "priority_score_cf_100": cf[100.0], "rank_actual": _rank(symbol, pop), "rank_cf_50": _rank(symbol, pop, {symbol: cf[50.0]}), "rank_cf_60": _rank(symbol, pop, {symbol: cf[60.0]}), "rank_cf_75": _rank(symbol, pop, {symbol: cf[75.0]}), "rank_cf_100": _rank(symbol, pop, {symbol: cf[100.0]})}
            row["rank_displacement_cf_100"] = row["rank_cf_100"] - row["rank_actual"]
            marg_rows.append(row)

    out.mkdir(parents=True, exist_ok=True)
    (out / "fail_cases_full.jsonl").write_text("\n".join(json.dumps(x) for x in fail_rows) + "\n", encoding="utf-8")
    (out / "marginal_candidate_cases_full.jsonl").write_text("\n".join(json.dumps(x) for x in marg_rows) + "\n", encoding="utf-8")
    (out / "summary_fail_depth_counterfactual.md").write_text(f"# Summary Fail\n\nTotal fail: {len(fail_rows)}\n", encoding="utf-8")
    (out / "summary_marginal_priority_impact.md").write_text(f"# Summary Marginal\n\nTotal marginal top buckets: {len(marg_rows)}\n", encoding="utf-8")
    (out / "analysis_report.md").write_text("# T26 Analysis Report\n\n## Replay logic\n\nAnalysis-only replay mirrors scanner/decision/buckets.py gating (entry pattern + confidence gates + fail-only execution block).\n\n## Spread/slippage availability\n\nFields found: " + (", ".join(sorted(spread_fields)) if spread_fields else "none") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
