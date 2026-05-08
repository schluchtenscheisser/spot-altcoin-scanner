#!/usr/bin/env python3
from __future__ import annotations

import argparse
import gzip
import json
import math
import statistics
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

DATES = ["2026-05-03", "2026-05-04", "2026-05-05", "2026-05-06", "2026-05-07"]
TOP_BUCKETS = {"confirmed_candidates", "early_candidates"}
CANONICAL_OUTPUT_DIR = Path("reports/aux/reduced_size_policy_calibration/2026-05-03_to_2026-05-07")
FORBIDDEN_OUTPUT_ROOTS = ["reports/runs", "reports/daily", "reports/index", "snapshots/runs", "reports/analysis"]
SCENARIOS = {
    "current_20k": {"notional_total_usdt": 20_000.0, "notional_chunk_usdt": 5_000.0, "max_tranches": 4, "depth_buffer_multiple": 10.0},
    "target_10k": {"notional_total_usdt": 10_000.0, "notional_chunk_usdt": 5_000.0, "max_tranches": 2, "depth_buffer_multiple": 10.0},
}
GRADE_MAPPINGS = {
    "conservative": {"full": 75.0, "reduced_75": 70.0, "reduced_50": 60.0, "reduced_25": 45.0, "observe_only": 20.0, "not_evaluable": 0.0},
    "balanced": {"full": 85.0, "reduced_75": 75.0, "reduced_50": 60.0, "reduced_25": 40.0, "observe_only": 20.0, "not_evaluable": 0.0},
    "strict_tradeable_only": {"full": 85.0, "reduced_75": 75.0, "reduced_50": 60.0, "reduced_25": 40.0, "observe_only": 0.0, "not_evaluable": 0.0},
}
SPREAD_THRESHOLDS = [0.05, 0.10, 0.15, 0.20, 0.30]
BAND_ORDER = {"not_evaluable": 0, "below_min": 1, "reduced_25": 2, "reduced_50": 3, "reduced_75": 4, "full": 5}


def finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def num(value: Any) -> float | None:
    if finite(value):
        return float(value)
    return None


def q(values: Iterable[float], pct: float) -> float | None:
    vals = sorted(float(v) for v in values if finite(v))
    if not vals:
        return None
    if len(vals) == 1:
        return vals[0]
    pos = (len(vals) - 1) * pct
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return vals[lo]
    return vals[lo] + (vals[hi] - vals[lo]) * (pos - lo)


def stats(values: Iterable[Any], prefix: str = "") -> dict[str, Any]:
    vals = [float(v) for v in values if finite(v)]
    missing = sum(1 for v in values if not finite(v)) if not isinstance(values, list) else len(values) - len(vals)
    p = f"{prefix}_" if prefix else ""
    return {
        f"{p}count_derivable": len(vals),
        f"{p}missing_count": missing,
        f"{p}min": min(vals) if vals else None,
        f"{p}median": statistics.median(vals) if vals else None,
        f"{p}p75": q(vals, 0.75),
        f"{p}p90": q(vals, 0.90),
        f"{p}max": max(vals) if vals else None,
    }


def nested(record: dict[str, Any], section: str, key: str) -> Any:
    section_value = record.get(section)
    if isinstance(section_value, dict) and key in section_value:
        return section_value.get(key)
    return record.get(key)


def get_field(record: dict[str, Any], field: str) -> Any:
    if field in {"decision_bucket", "priority_score"}:
        return nested(record, "decision", field)
    if field in {"state_machine_state", "state_confidence"}:
        return nested(record, "state", field)
    if field in {"market_phase", "market_phase_confidence"}:
        return nested(record, "phase", field)
    if field in {"entry_pattern", "entry_pattern_score"}:
        decision = record.get("decision")
        if isinstance(decision, dict) and field in decision:
            return decision.get(field)
        pattern = record.get("pattern")
        if isinstance(pattern, dict) and field in pattern:
            return pattern.get(field)
        return record.get(field)
    return record.get(field)


def priority_score(mpc: float, sc: float, eps: float, grade: float) -> float:
    return 0.30 * mpc + 0.35 * sc + 0.20 * eps + 0.15 * grade


def scenario_threshold(cfg: dict[str, Any]) -> float:
    return float(cfg["notional_total_usdt"]) * float(cfg["depth_buffer_multiple"])


def scenario_band(available_depth: Any, scenario_id: str) -> tuple[float | None, str, float | None, str]:
    threshold = scenario_threshold(SCENARIOS[scenario_id])
    available = num(available_depth)
    if available is None or threshold <= 0 or not math.isfinite(threshold):
        return None, "not_evaluable", None, "not_evaluable"
    ratio = available / threshold
    if ratio >= 1.0:
        band, factor = "full", 1.0
    elif ratio >= 0.75:
        band, factor = "reduced_75", 0.75
    elif ratio >= 0.50:
        band, factor = "reduced_50", 0.50
    elif ratio >= 0.25:
        band, factor = "reduced_25", 0.25
    else:
        band, factor = "below_min", 0.0
    tradeability = "observe_only" if band == "below_min" else band
    return ratio, band, factor, tradeability


def eligible(cls: str) -> bool:
    return cls in {"full", "reduced_75", "reduced_50", "reduced_25"}


def best_band(bands: Iterable[Any]) -> str:
    return max((str(b) for b in bands), key=lambda b: (BAND_ORDER.get(b, -1), b), default="not_evaluable")


def joined_seen(values: Iterable[Any]) -> str:
    return ", ".join(sorted({str(v) for v in values if v is not None}))


def recurrence_bucket(day_count: int) -> str:
    return f"{min(day_count, 5)}_day"


def normalize_path(path: Path, repo_root: Path) -> Path | None:
    try:
        return path.resolve().relative_to(repo_root)
    except ValueError:
        return None


def validate_output_dir(out: Path, repo_root: Path) -> None:
    resolved = out.resolve()
    rel = normalize_path(out, repo_root)
    rel_posix = rel.as_posix() if rel is not None else resolved.as_posix()
    for bad in FORBIDDEN_OUTPUT_ROOTS:
        if rel_posix == bad or rel_posix.startswith(f"{bad}/") or f"/{bad}/" in rel_posix:
            raise ValueError(f"Forbidden output path: {out} (normalized: {rel_posix})")
    if rel is None:
        # Test and ad-hoc calibration runs may write to temporary directories outside
        # the repo; canonical production output remains the default.
        return
    canonical = CANONICAL_OUTPUT_DIR.as_posix()
    if rel_posix != canonical and not rel_posix.startswith("reports/aux/"):
        raise ValueError(f"Output path must be under reports/aux: {out} (normalized: {rel})")


def find_archives(input_dir: Path) -> dict[str, tuple[Path, str]]:
    found: dict[str, list[tuple[Path, str]]] = {d: [] for d in DATES}
    for zip_path in sorted(input_dir.glob("*.zip")):
        with zipfile.ZipFile(zip_path) as zf:
            for name in sorted(zf.namelist()):
                if not name.endswith("symbol_diagnostics.jsonl.gz") or "/daily-" not in name:
                    continue
                for day in DATES:
                    if f"/{day.replace('-', '/')}/" in name:
                        found[day].append((zip_path, name))
    missing = [d for d, matches in found.items() if not matches]
    if missing:
        raise ValueError(f"Missing expected dates: {', '.join(missing)}")
    multiples = {d: matches for d, matches in found.items() if len(matches) > 1}
    if multiples:
        detail = "; ".join(f"{d}: {len(matches)}" for d, matches in multiples.items())
        raise ValueError(f"Multiple Daily diagnostics files found without selection rule: {detail}")
    return {d: matches[0] for d, matches in found.items()}


def read_diag(zip_path: Path, member: str) -> list[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as zf:
        raw = zf.read(member)
    rows = [json.loads(line) for line in gzip.decompress(raw).decode("utf-8").splitlines() if line.strip()]
    if not rows:
        raise ValueError(f"Selected diagnostics has zero records: {zip_path.name}::{member}")
    return rows


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    def fmt(v: Any) -> str:
        if v is None:
            return "null"
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v)
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    out += ["| " + " | ".join(fmt(v) for v in row) + " |" for row in rows]
    return "\n".join(out) + "\n"


def dump_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n")


def count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    return dict(sorted(Counter(str(r.get(key)) for r in rows).items()))


def rank(symbol: str, rows: list[dict[str, Any]], override: float | None = None) -> int | None:
    ranked = []
    for r in rows:
        ps = override if r.get("symbol") == symbol and override is not None else num(get_field(r, "priority_score"))
        ranked.append((ps if ps is not None else float("-inf"), str(r.get("symbol") or ""), r))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    for i, (_, _, r) in enumerate(ranked, 1):
        if r.get("symbol") == symbol:
            return i
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input-dir", default="data/shadow-live-zips")
    ap.add_argument("--output-dir", default=str(CANONICAL_OUTPUT_DIR))
    args = ap.parse_args()
    repo_root = Path.cwd().resolve()
    out = Path(args.output_dir)
    validate_output_dir(out, repo_root)

    mapping = find_archives(Path(args.input_dir))
    day_rows: dict[str, list[dict[str, Any]]] = {}
    manifest_rows = []
    all_rows: list[dict[str, Any]] = []
    for day in DATES:
        zip_path, member = mapping[day]
        rows = read_diag(zip_path, member)
        for r in rows:
            r["_date"] = day
        day_rows[day] = rows
        all_rows.extend(rows)
        status_counts = Counter(str(r.get("execution_status_raw") or "not_attempted") for r in rows)
        unknown_buckets = Counter(str(get_field(r, "decision_bucket")) for r in rows if r.get("execution_status_raw") == "unknown")
        manifest_rows.append([day, zip_path.name, member, len(rows), status_counts.get("unknown", 0), dict(sorted(unknown_buckets.items()))])

    fail_full: list[dict[str, Any]] = []
    marginal_full: list[dict[str, Any]] = []
    for r in sorted(all_rows, key=lambda x: (x["_date"], str(x.get("symbol") or ""))):
        status = r.get("execution_status_raw")
        bucket = get_field(r, "decision_bucket")
        if status == "fail":
            for scenario_id in SCENARIOS:
                ratio, band, factor, cls = scenario_band(r.get("available_depth_1pct_usdt"), scenario_id)
                fail_full.append({
                    "date": r["_date"], "symbol": r.get("symbol"), "scenario_id": scenario_id,
                    "available_depth_1pct_usdt": num(r.get("available_depth_1pct_usdt")),
                    "scenario_depth_threshold_1pct_usdt": scenario_threshold(SCENARIOS[scenario_id]),
                    "scenario_available_depth_ratio": ratio,
                    "scenario_depth_ratio_band": band,
                    "scenario_recommended_position_factor": factor,
                    "reaches_reduced_25": eligible(cls),
                    "execution_reason_raw": r.get("execution_reason_raw"),
                    "recorded_depth_ratio_band": r.get("depth_ratio_band"),
                })
        if status == "marginal" and bucket in TOP_BUCKETS:
            for scenario_id in SCENARIOS:
                ratio, band, factor, cls = scenario_band(r.get("available_depth_1pct_usdt"), scenario_id)
                mpc, sc, eps = num(get_field(r, "market_phase_confidence")), num(get_field(r, "state_confidence")), num(get_field(r, "entry_pattern_score"))
                score_replay_derivable = all(v is not None for v in (mpc, sc, eps))
                marginal_full.append({
                    "date": r["_date"], "symbol": r.get("symbol"), "scenario_id": scenario_id,
                    "decision_bucket": bucket,
                    "scenario_available_depth_ratio": ratio,
                    "scenario_depth_ratio_band": band,
                    "scenario_recommended_position_factor": factor,
                    "scenario_tradeability_class": cls,
                    "reduced_size_eligible": eligible(cls),
                    "market_phase": get_field(r, "market_phase"),
                    "market_phase_confidence": mpc,
                    "state_machine_state": get_field(r, "state_machine_state"),
                    "state_confidence": sc,
                    "entry_pattern": get_field(r, "entry_pattern"),
                    "entry_pattern_score": eps,
                    "depth_side_used": r.get("depth_side_used"),
                    "spread_pct": num(r.get("spread_pct")),
                    "estimated_slippage_bps": num(r.get("estimated_slippage_bps")),
                    "score_replay_derivable": score_replay_derivable,
                    "execution_grade_t16": num(r.get("execution_grade_t16")),
                    "priority_score_actual": num(get_field(r, "priority_score")),
                })

    fail_target_reachers = [r for r in fail_full if r["scenario_id"] == "target_10k" and r["reaches_reduced_25"]]
    fail_manual_review = bool(fail_target_reachers)

    # Rank sensitivity.
    rank_summary_rows = []
    for scenario_id in SCENARIOS:
        scenario_candidates = [r for r in marginal_full if r["scenario_id"] == scenario_id]
        index = {(r["date"], r["symbol"]): r for r in scenario_candidates}
        for mapping_name, grade_map in GRADE_MAPPINGS.items():
            displacements = []
            for (day, symbol), mr in sorted(index.items()):
                if not mr["score_replay_derivable"]:
                    continue
                bucket = mr["decision_bucket"]
                population = [r for r in day_rows[day] if get_field(r, "decision_bucket") == bucket]
                current_rank = rank(symbol, population)
                simulated_grade = grade_map[mr["scenario_tradeability_class"]]
                simulated_score = priority_score(mr["market_phase_confidence"], mr["state_confidence"], mr["entry_pattern_score"], simulated_grade)
                simulated_rank = rank(symbol, population, simulated_score)
                if current_rank is not None and simulated_rank is not None:
                    displacements.append(simulated_rank - current_rank)
            rank_summary_rows.append({
                "scenario_id": scenario_id,
                "mapping": mapping_name,
                "mean_rank_displacement": statistics.mean(displacements) if displacements else None,
                "median_rank_displacement": statistics.median(displacements) if displacements else None,
                "count_improved_5plus_ranks": sum(1 for d in displacements if d <= -5),
                "count_improved_10plus_ranks": sum(1 for d in displacements if d <= -10),
                "count_no_change": sum(1 for d in displacements if d == 0),
                "count_worse": sum(1 for d in displacements if d > 0),
                "derivable_count": len(displacements),
            })

    out.mkdir(parents=True, exist_ok=True)
    dump_jsonl(out / "marginal_candidates_full.jsonl", marginal_full)
    dump_jsonl(out / "fail_sanity_full.jsonl", fail_full)

    aggregate_status = Counter(str(r.get("execution_status_raw") or "not_attempted") for r in all_rows)
    attempted_count = sum(1 for r in all_rows if r.get("execution_attempted") is True)
    aggregate_rows = [[key, aggregate_status[key]] for key in sorted(aggregate_status)]
    (out / "run_input_manifest.md").write_text(
        "# T28 Run Input Manifest\n\n"
        + md_table(["date", "zip", "diagnostics_path", "record_count", "unknown_count", "unknown_bucket_distribution"], manifest_rows)
        + f"\nTotal records: {len(all_rows)}\n\nExecution attempted records: {attempted_count}\n\n"
        + "## Aggregate execution status counts\n\n"
        + md_table(["execution_status_raw", "count"], aggregate_rows),
        encoding="utf-8",
    )

    fail_ratios_target = [r["scenario_available_depth_ratio"] for r in fail_full if r["scenario_id"] == "target_10k"]
    fail_ratios_current = [r["scenario_available_depth_ratio"] for r in fail_full if r["scenario_id"] == "current_20k"]
    fail_count_by_day = Counter(r["date"] for r in fail_full if r["scenario_id"] == "target_10k")
    fail_report = [
        "# Fail Sanity Check", "",
        f"fail_count: {sum(fail_count_by_day.values())}",
        f"fail_count_by_day: {dict(sorted(fail_count_by_day.items()))}",
        f"fail_ratio_min_target_10k: {q(fail_ratios_target, 0.0)}",
        f"fail_ratio_median_target_10k: {q(fail_ratios_target, 0.5)}",
        f"fail_ratio_p75_target_10k: {q(fail_ratios_target, 0.75)}",
        f"fail_ratio_max_target_10k: {q(fail_ratios_target, 1.0)}",
        f"fail_ratio_max_current_20k: {q(fail_ratios_current, 1.0)}",
        f"fail_count_reaching_reduced_25_current_20k: {sum(1 for r in fail_full if r['scenario_id']=='current_20k' and r['reaches_reduced_25'])}",
        f"fail_count_reaching_reduced_25_target_10k: {len(fail_target_reachers)}", "",
    ]
    if fail_manual_review:
        fail_report += ["Manual review required because at least one fail record reaches reduced_25 under target 10k."]
    else:
        fail_report += ["Based on the five T27-capable runs, fail remains out of scope for reduced-size execution and should stay hard-blocked in the T29 policy proposal. This is because no fail record reaches reduced_25 under the target 10k scenario."]
    (out / "fail_sanity_check.md").write_text("\n".join(fail_report) + "\n", encoding="utf-8")

    dist_rows = []
    for scenario_id in SCENARIOS:
        rows = [r for r in marginal_full if r["scenario_id"] == scenario_id]
        for key in ["scenario_tradeability_class", "scenario_depth_ratio_band", "depth_side_used", "market_phase", "entry_pattern", "state_machine_state"]:
            for val, count in sorted(Counter(str(r.get(key)) for r in rows).items()):
                dist_rows.append([scenario_id, key, val, count])
    (out / "marginal_band_distribution.md").write_text("# Marginal Band Distribution\n\n" + md_table(["scenario", "dimension", "value", "count"], dist_rows), encoding="utf-8")

    scenario_rows = []
    for scenario_id in SCENARIOS:
        rows = [r for r in marginal_full if r["scenario_id"] == scenario_id]
        scenario_rows.append([scenario_id, len(rows), sum(1 for r in rows if r["reduced_size_eligible"]), sum(1 for r in rows if r["scenario_tradeability_class"] == "observe_only"), sum(1 for r in rows if r["scenario_tradeability_class"] == "not_evaluable")])
    (out / "scenario_20k_vs_10k_summary.md").write_text("# Scenario 20k vs 10k Summary\n\n" + md_table(["scenario", "marginal_top_bucket_count", "eligible_count", "observe_only_count", "not_evaluable_count"], scenario_rows), encoding="utf-8")

    spread_rows = []
    sens_rows = []
    slip_rows = []
    for scenario_id in SCENARIOS:
        for cls in ["full", "reduced_75", "reduced_50", "reduced_25", "observe_only", "not_evaluable"]:
            rows = [r for r in marginal_full if r["scenario_id"] == scenario_id and r["scenario_tradeability_class"] == cls]
            s = stats([r["spread_pct"] for r in rows], "spread")
            spread_rows.append([scenario_id, cls, s["spread_count_derivable"], s["spread_missing_count"], s["spread_min"], s["spread_median"], s["spread_p75"], s["spread_p90"], s["spread_max"]])
            slip = [r["estimated_slippage_bps"] for r in rows]
            sl = stats(slip, "slippage")
            denom = len(rows)
            slip_rows.append([scenario_id, cls, sl["slippage_count_derivable"], sl["slippage_missing_count"], (sl["slippage_count_derivable"] / denom if denom else None), sl["slippage_median"], sl["slippage_p75"]])
        elig_rows = [r for r in marginal_full if r["scenario_id"] == scenario_id and r["reduced_size_eligible"]]
        for threshold in SPREAD_THRESHOLDS:
            sens_rows.append([scenario_id, threshold, sum(1 for r in elig_rows if r["spread_pct"] is not None and r["spread_pct"] <= threshold)])
    (out / "spread_slippage_by_band.md").write_text(
        "# Spread and Slippage by Band\n\n## Spread\n\n" + md_table(["scenario", "class", "derivable", "missing", "min", "median", "p75", "p90", "max"], spread_rows)
        + "\n## Spread Threshold Sensitivity\n\n" + md_table(["scenario", "spread_threshold_pct", "eligible_remaining_derivable_spread_only"], sens_rows)
        + "\n## Slippage\n\n" + md_table(["scenario", "class", "derivable", "missing", "derivable_share", "median", "p75"], slip_rows)
        + "\nSlippage data is only partially available. T28 does not justify loosening slippage thresholds for reduced-size candidates.\n",
        encoding="utf-8",
    )

    (out / "grade_mapping_sensitivity.md").write_text("# Grade Mapping Sensitivity\n\n" + md_table(["scenario", "mapping", "mean_rank_displacement", "median_rank_displacement", "improved_5plus", "improved_10plus", "no_change", "worse", "derivable_count"], [[r[k] for k in ["scenario_id", "mapping", "mean_rank_displacement", "median_rank_displacement", "count_improved_5plus_ranks", "count_improved_10plus_ranks", "count_no_change", "count_worse", "derivable_count"]] for r in rank_summary_rows]), encoding="utf-8")

    availability_rows = []
    for day in DATES:
        top = [r for r in day_rows[day] if get_field(r, "decision_bucket") in TOP_BUCKETS]
        unknown = [r for r in day_rows[day] if r.get("execution_status_raw") == "unknown"]
        for scenario_id in SCENARIOS:
            marg = [r for r in marginal_full if r["date"] == day and r["scenario_id"] == scenario_id and r["reduced_size_eligible"]]
            direct = [r for r in top if r.get("execution_status_raw") == "direct_ok"]
            combined = len(direct) + len(marg)
            row = [day, scenario_id, len(direct), len(marg), combined]
            row += [sum(1 for r in marg if r["spread_pct"] is not None and r["spread_pct"] <= th) + len(direct) for th in SPREAD_THRESHOLDS]
            row += ["YES" if combined < 5 else "NO", len(unknown), dict(sorted(Counter(str(get_field(r, "decision_bucket")) for r in unknown).items()))]
            availability_rows.append(row)
    (out / "candidate_availability_by_day.md").write_text("# Candidate Availability by Day\n\n" + md_table(["date", "scenario", "direct_ok_top_bucket_count", "marginal_reduced_eligible_top_bucket_count", "combined_tradeable_top_bucket_count", "after_spread_0.05", "after_spread_0.10", "after_spread_0.15", "after_spread_0.20", "after_spread_0.30", "weak_day_lt5", "unknown_count", "unknown_bucket_distribution"], availability_rows), encoding="utf-8")

    recur_summary_rows = []
    recur_detail_rows = []
    for scenario_id in SCENARIOS:
        by_symbol: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for r in marginal_full:
            if r["scenario_id"] == scenario_id and r["reduced_size_eligible"]:
                by_symbol[str(r["symbol"])].append(r)

        recurring_day_counts: list[int] = []
        for sym in sorted(by_symbol):
            rows = by_symbol[sym]
            dates = sorted({str(r["date"]) for r in rows})
            eligible_days = len(dates)
            if eligible_days < 2:
                continue
            recurring_day_counts.append(eligible_days)
            depth_ratios = [r["scenario_available_depth_ratio"] for r in rows if r["scenario_available_depth_ratio"] is not None]
            spreads = [r["spread_pct"] for r in rows if r["spread_pct"] is not None]
            recur_detail_rows.append([
                scenario_id,
                sym,
                eligible_days,
                ", ".join(dates),
                joined_seen(r["decision_bucket"] for r in rows),
                statistics.median(depth_ratios) if depth_ratios else None,
                best_band(r["scenario_depth_ratio_band"] for r in rows),
                statistics.median(spreads) if spreads else None,
                joined_seen(r["market_phase"] for r in rows),
                joined_seen(r["entry_pattern"] for r in rows),
                recurrence_bucket(eligible_days),
            ])
        recur_summary_rows.append([
            scenario_id,
            sum(1 for day_count in recurring_day_counts if day_count >= 2),
            sum(1 for day_count in recurring_day_counts if day_count >= 3),
            sum(1 for day_count in recurring_day_counts if day_count >= 4),
            sum(1 for day_count in recurring_day_counts if day_count >= 5),
        ])

    (out / "recurring_symbols.md").write_text(
        "# Recurring Eligible Symbols\n\n"
        + "## Summary Counts\n\n"
        + md_table(["scenario", "symbols_recurring_2plus_days", "symbols_recurring_3plus_days", "symbols_recurring_4plus_days", "symbols_recurring_5_days"], recur_summary_rows)
        + "\n## Recurring Symbol Diagnostics\n\n"
        + md_table(["scenario", "symbol", "eligible_days", "dates", "buckets_seen", "median_scenario_depth_ratio", "best_scenario_depth_ratio_band", "median_spread_pct", "phases_seen", "patterns_seen", "recurrence_bucket"], recur_detail_rows),
        encoding="utf-8",
    )

    fail_policy_recommendation = (
        "Based on the five T27-capable runs, no fail record reaches reduced_25 under the target 10k scenario. "
        "Fail remains out of scope for reduced-size execution and should stay hard no-trade in the T29 policy proposal."
        if not fail_manual_review
        else (
            "At least one fail record reaches or exceeds the reduced_25 threshold under the target 10k scenario. "
            f"Fail policy is manual-review-required: {len(fail_target_reachers)} fail record(s) reach reduced_25 and "
            f"the maximum target_10k fail ratio is {q(fail_ratios_target, 1.0)}. "
            "T29 must not implement fail-based reduced-size eligibility until this exception is manually reviewed."
        )
    )
    fail_runtime_semantics = (
        "fail: hard no-trade."
        if not fail_manual_review
        else "fail: manual-review-required for T29; no fail-based reduced-size eligibility may be implemented until the exception evidence is manually reviewed."
    )
    fail_limitation = (
        "4. No fail policy generalization beyond current evidence. Fail remains hard-blocked for T29 based on current evidence; future materially different liquidity regimes may warrant re-analysis.\n"
        if not fail_manual_review
        else "4. No fail policy generalization beyond current evidence. The fail-policy exception evidence is manual-review-required before T29 may define any fail-based reduced-size eligibility.\n"
    )

    policy = "manual-review-required" if fail_manual_review else "recommended"
    (out / "recommended_policy.md").write_text(
        "# Recommended T29 Policy\n\n"
        f"Fail policy status: {policy}.\n\n"
        "## Target 10k config values\n\n"
        + md_table(["key", "value"], [["notional_total_usdt", 10000], ["notional_chunk_usdt", 5000], ["max_tranches", 2], ["depth_buffer_multiple", 10], ["derived_min_depth_1pct_usdt", 100000]])
        + "\n## Runtime status semantics\n\n"
        "direct_ok: full-size tradeable.\n\ntranche_ok: existing behavior unchanged; no order-splitting extension in T29.\n\nmarginal: split by execution_size_class / recommended_position_factor.\n\n"
        f"{fail_runtime_semantics}\n\n"
        "unknown: no trade / not safely evaluable.\n\n"
        "## Recommended fields\n\nexecution_size_class values: full, reduced_75, reduced_50, reduced_25, observe_only, blocked, not_evaluable.\n\n"
        "recommended_position_factor mapping: full=1.00, reduced_75=0.75, reduced_50=0.50, reduced_25=0.25, observe_only=0.00, blocked=0.00, not_evaluable=null.\n\n"
        "Do not remove marginal + below_min from structural buckets in T29. Keep them visible in reports, but clearly mark them as execution_size_class = observe_only and not tradeable.\n\n"
        "Use the existing full-trade slippage threshold for reduced-size candidates unless T29 has stronger evidence. Slippage data is only partially available. T28 does not justify loosening slippage thresholds for reduced-size candidates.\n\n"
        "Recommended grade mapping for T29: balanced, because it preserves tradeable-class differentiation while keeping reduced_25 conservative and observe_only penalized.\n\n"
        "## Fail policy evidence\n\n"
        f"{fail_policy_recommendation}\n\n"
        "## Limitations\n\n"
        "1. No profitability conclusion. T28 does not evaluate forward returns, MFE, MAE, or realized trade performance.\n"
        "2. Five-run sample. The analysis uses five T27-capable Shadow-Live Daily runs. It is sufficient for first policy calibration but should be revisited after more runs.\n"
        "3. Slippage partial availability. Slippage is not available for all records. Missing slippage must not be interpreted as good execution.\n"
        f"{fail_limitation}"
        "5. No order-splitting change. T28 does not evaluate or modify tranche_ok or order-splitting behavior.\n",
        encoding="utf-8",
    )

    print(f"Wrote T28 reduced-size policy calibration outputs to {out}")


if __name__ == "__main__":
    main()
