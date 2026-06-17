#!/usr/bin/env python3
"""Stage-1b term-structure, turnover, persistence, and survivorship diagnostics."""
from __future__ import annotations

import argparse
import json
import math
import socket
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.rotation.btc_relative_edge_probe import (
    ProbeError,
    add_returns,
    available_history_symbols,
    bootstrap_ci_by_week,
    load_close_series,
    map_tiers,
    resolve_history_symbols,
    symbol_column,
)

HORIZONS_DEFAULT = [1, 3, 5, 10, 20]
REQUIRED_STAGE1_FILES = [
    "segment_relative_returns.parquet",
    "btc_relative_edge_probe.json",
    "probe_manifest.json",
]
FORBIDDEN_MACHINE_TOKENS = {
    "approved",
    "green_light",
    "stage2_green_light",
    "stage2_approved",
    "deploy",
    "rotation_recommendation",
    "trade_recommendation",
    "live_trade",
    "execute_trade",
}
ASSESSMENTS = {
    "compatible_evidence_absent",
    "compatible_evidence_weak",
    "compatible_evidence_inconclusive",
    "compatible_evidence_promising_but_oos_required",
}
NON_GOALS = [
    "No mechanical rotation backtest yet.",
    "No TAO/BTC strategy validation yet.",
    "No change of the pre-registered Stage-1 result (10d primary remains FAILED).",
    "No decision-bearing switch from 10d to 1d/3d on the same dataset.",
    "Stage 2 remains blocked until this ticket's central question is answered.",
]
TURNOVER_CAVEAT = (
    "This is not a position simulation and must not annualize P&L. It is only a\n"
    "turnover-cost magnitude diagnostic. implied_max_rotations_per_year is an upper\n"
    "bound on rotation frequency for an edge whose horizon is h, not a realized\n"
    "trade count."
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--stage1-root", default="evaluation/rotation/stage1/2026-05-24T21-27-31Z")
    p.add_argument("--events", default="evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-31Z/enriched_replay_events.parquet")
    p.add_argument("--history-root", default="snapshots/history/ohlcv")
    p.add_argument("--output-root", default="evaluation/rotation/stage1b")
    p.add_argument("--replay-id", default="2026-05-24T21-27-31Z")
    p.add_argument("--horizons", default=",".join(map(str, HORIZONS_DEFAULT)))
    p.add_argument("--primary-reference-horizon-days", type=int, default=10)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--min-count", type=int, default=30)
    p.add_argument("--tail-contributor-count", type=int, default=5)
    p.add_argument("--benchmark-symbol", default="BTCUSDT")
    p.add_argument("--n-bootstrap", type=int, default=2000)
    return p.parse_args(argv)


def horizons_from_arg(raw: str) -> list[int]:
    hs = [int(x) for x in str(raw).split(",") if x.strip()]
    if not hs or any(h <= 0 for h in hs):
        raise ProbeError("horizons must be positive integers")
    return hs


def load_stage1(stage1_root: Path) -> tuple[pd.DataFrame, dict[str, Any], dict[str, Any]]:
    missing = [name for name in REQUIRED_STAGE1_FILES if not (stage1_root / name).exists()]
    if missing:
        raise ProbeError(f"missing required Stage-1 files: {missing}")
    seg = pd.read_parquet(stage1_root / "segment_relative_returns.parquet")
    probe = json.loads((stage1_root / "btc_relative_edge_probe.json").read_text())
    manifest = json.loads((stage1_root / "probe_manifest.json").read_text())
    cc = probe.get("cost_context") or {}
    if "cost_log_low" not in cc or "cost_log_high" not in cc:
        raise ProbeError("Stage-1 cost_context.cost_log_low/high absent")
    return seg, probe, manifest


def load_events(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        raise ProbeError(f"enriched replay events missing/empty: {path}")
    df = pd.read_parquet(path)
    if df.empty:
        raise ProbeError("enriched replay events is empty")
    return df


def static_scope(df: pd.DataFrame, sym_col: str, benchmark: str) -> pd.DataFrame:
    base = df["history_symbol"].fillna(df[sym_col].astype(str)).astype(str).str.replace(r"USDT$", "", regex=True)
    deny = base.isin(["USDC", "USDT", "FDUSD", "DAI", "TUSD", "USDE"])
    cat = df.get("universe_category", pd.Series("", index=df.index)).astype(str).str.lower()
    cat_deny = cat.str.contains("stable|tokenized|stock|cash", regex=True, na=False)
    return df[(df["history_symbol"].notna()) & (df["history_symbol"] != benchmark) & ~deny & ~cat_deny].copy()


def metric_row(frame: pd.DataFrame, group: str, key: str, h: int, min_count: int, seed: int, n_boot: int) -> dict[str, Any]:
    col = f"relative_log_return_{h}d"
    vals = frame[col].dropna() if col in frame else pd.Series(dtype=float)
    ci = (None, None) if len(vals) < min_count else bootstrap_ci_by_week(frame.dropna(subset=[col]), col, np.median, n_boot, seed)
    return {
        "analysis_role": "diagnostic",
        "analysis_name": "term_structure_bucket_ladder",
        "segment_group": group,
        "segment_key": str(key),
        "horizon_days": h,
        "event_count": int(len(vals)),
        "mean_relative_log_return": float(vals.mean()) if len(vals) else None,
        "median_relative_log_return": float(vals.median()) if len(vals) else None,
        "hit_rate_vs_btc": float((vals > 0).mean()) if len(vals) else None,
        "bootstrap_ci_low": ci[0],
        "bootstrap_ci_high": ci[1],
    }


def term_structure(scope: pd.DataFrame, tier_col: str, horizons: list[int], min_count: int, seed: int, n_boot: int) -> pd.DataFrame:
    rows = []
    for tier, g in scope.groupby(tier_col, dropna=False):
        for h in horizons:
            rows.append(metric_row(g, "tier", str(tier), h, min_count, seed, n_boot))
    for field in ["btc_regime_label", "quote_volume_bucket"]:
        if field in scope.columns:
            for key, g in scope.groupby(field, dropna=False):
                for h in horizons:
                    r = metric_row(g, field, str(key), h, min_count, seed, n_boot)
                    r["analysis_name"] = "regime_liquidity_stratification"
                    rows.append(r)
    return pd.DataFrame(rows)


def persistence(scope: pd.DataFrame, tier_col: str, confirmed: str) -> pd.DataFrame:
    d = scope[scope[tier_col] == confirmed].copy()
    rows = []
    for src, dst in [(1, 10), (3, 10), (10, 20)]:
        a, b = f"relative_log_return_{src}d", f"relative_log_return_{dst}d"
        e = d.dropna(subset=[a, b])
        pos = e[e[a] > 0]
        for sk, dk in [("positive", "positive"), ("positive", "non_positive"), ("non_positive", "positive"), ("non_positive", "non_positive")]:
            mask_src = e[a] > 0 if sk == "positive" else e[a] <= 0
            mask_dst = e[b] > 0 if dk == "positive" else e[b] <= 0
            denom = int(mask_src.sum())
            rows.append({"analysis_role": "diagnostic", "analysis_name": "persistence_sign_transition", "transition": f"{src}d_to_{dst}d", "source_sign": sk, "destination_sign": dk, "event_count": int((mask_src & mask_dst).sum()), "source_count": denom, "rate": float(((mask_src & mask_dst).sum() / denom)) if denom else None})
        rows.append({"analysis_role": "diagnostic", "analysis_name": "persistence_positive_carry", "transition": f"{src}d_to_{dst}d", "source_sign": "positive", "destination_sign": "positive", "event_count": int(((pos[b] > 0)).sum()), "source_count": int(len(pos)), "rate": float((pos[b] > 0).mean()) if len(pos) else None})
    return pd.DataFrame(rows)


def cost_break_even(scope: pd.DataFrame, tier_col: str, confirmed: str, horizons: list[int], low: float, high: float) -> pd.DataFrame:
    d = scope[scope[tier_col] == confirmed]
    rows = []
    for h in horizons:
        vals = d[f"relative_log_return_{h}d"].dropna()
        gross = float(vals.median()) if len(vals) else None
        rows.append({"analysis_role": "diagnostic", "analysis_name": "cost_break_even", "horizon_days": h, "gross_edge_log": gross, "one_roundtrip_net_low": gross - low if gross is not None else None, "one_roundtrip_net_high": gross - high if gross is not None else None, "implied_max_rotations_per_year": 365 / h, "annualized_cost_drag_low": (365 / h) * low, "annualized_cost_drag_high": (365 / h) * high})
    return pd.DataFrame(rows)


def turnover(scope: pd.DataFrame, tier_col: str, confirmed: str) -> pd.DataFrame:
    d = scope[scope[tier_col] == confirmed].copy()
    d["week"] = pd.to_datetime(d["as_of_daily_bar_id"]).dt.strftime("%G-%V")
    by_sym_week = d.groupby(["history_symbol", "week"]).size()
    by_week = d.groupby("week").size()
    gaps = []
    for _, g in d.sort_values("as_of_daily_bar_id").groupby("history_symbol"):
        days = pd.to_datetime(g["as_of_daily_bar_id"]).sort_values()
        gaps += [float(x) for x in days.diff().dt.days.dropna().tolist()]
    return pd.DataFrame([{"analysis_role": "diagnostic", "analysis_name": "turnover_signal_frequency_proxy", "events_per_symbol_week_median": float(by_sym_week.median()) if len(by_sym_week) else None, "events_per_symbol_week_p75": float(by_sym_week.quantile(.75)) if len(by_sym_week) else None, "universe_events_per_week_median": float(by_week.median()) if len(by_week) else None, "median_inter_signal_gap_days": float(np.median(gaps)) if gaps else None}])


def same_date(scope: pd.DataFrame, tier_col: str, confirmed: str, watch: str) -> pd.DataFrame:
    watch_count = int((scope[tier_col] == watch).sum())
    co = 0
    for _, g in scope.groupby("as_of_daily_bar_id"):
        if (g[tier_col] == confirmed).any() and (g[tier_col] == watch).any():
            co += 1
    return pd.DataFrame([{"analysis_role": "diagnostic", "analysis_name": "same_date_coverage", "watchlist_event_count": watch_count, "confirmed_watch_same_date_cooccurrence_count": int(co), "explanation": "same-date comparator structurally underpowered"}])


def first_history_dates(root: Path) -> dict[str, str]:
    out = {}
    base = root / "timeframe=1d"
    for d in base.glob("symbol=*") if base.exists() else []:
        sym = d.name.split("=", 1)[1]
        try:
            s = load_close_series(root, sym)
            if len(s):
                out[sym] = str(s.index.min())
        except Exception:
            pass
    return out


def assign_age(scope: pd.DataFrame, root: Path) -> tuple[pd.DataFrame, bool, list[float]]:
    d = scope.copy()
    if "available_history_days_1d_at_event" in d.columns and pd.to_numeric(d["available_history_days_1d_at_event"], errors="coerce").notna().any():
        d["survivorship_age_proxy_days"] = pd.to_numeric(d["available_history_days_1d_at_event"], errors="coerce")
        available = True
    else:
        firsts = first_history_dates(root)
        if not firsts:
            d["survivorship_age_proxy_days"] = np.nan
            return d, False, []
        first = d["history_symbol"].map(firsts)
        d["survivorship_age_proxy_days"] = (pd.to_datetime(d["as_of_daily_bar_id"]) - pd.to_datetime(first)).dt.days
        available = d["survivorship_age_proxy_days"].notna().any()
    if not available:
        return d, False, []
    ordered = d.reset_index(names="_orig").sort_values(["survivorship_age_proxy_days", "history_symbol", "as_of_daily_bar_id", "_orig"], na_position="last")
    valid = ordered[ordered["survivorship_age_proxy_days"].notna()].copy()
    labels = ["youngest", "middle", "oldest"]
    valid["age_cohort"] = pd.qcut(np.arange(len(valid)), q=3, labels=labels, duplicates="drop") if len(valid) >= 3 else "middle"
    d["age_cohort"] = valid.set_index("_orig")["age_cohort"]
    edges = [float(valid["survivorship_age_proxy_days"].min()), float(valid["survivorship_age_proxy_days"].quantile(1/3)), float(valid["survivorship_age_proxy_days"].quantile(2/3)), float(valid["survivorship_age_proxy_days"].max())] if len(valid) else []
    return d, True, edges


def survivorship(scope: pd.DataFrame, tier_col: str, confirmed: str, horizons: list[int], tail_n: int, root: Path) -> tuple[pd.DataFrame, dict[str, Any]]:
    d, avail, edges = assign_age(scope, root)
    rows = []
    if avail:
        for cohort, g in d[(d[tier_col] == confirmed)].groupby("age_cohort", dropna=False):
            for h in horizons:
                r = metric_row(g, "age_cohort", str(cohort), h, 1, 12345, 20); r["analysis_name"] = "survivorship_age_stratification"; rows.append(r)
    h = 10 if 10 in horizons else horizons[0]
    col = f"relative_log_return_{h}d"
    confirmed_df = d[d[tier_col] == confirmed]
    contributors = confirmed_df.dropna(subset=[col]).groupby("history_symbol")[col].sum().sort_values(ascending=False)
    top = list(contributors.head(tail_n).index)
    for key, g in [(f"exclude_top_{tail_n}_contributors", confirmed_df[~confirmed_df["history_symbol"].isin(top)]), ("exclude_youngest_cohort", confirmed_df[confirmed_df.get("age_cohort") != "youngest"] if avail else confirmed_df.iloc[0:0])]:
        for hh in horizons:
            r = metric_row(g, "survivorship_recomputed", key, hh, 1, 12345, 20); r["analysis_name"] = "survivorship_recomputed_edge"; rows.append(r)
    meta = {"survivorship_age_proxy_available": bool(avail), "age_cohort_edges_days": edges, "tail_contributor_symbols": top, "delisting_status_available": False}
    return pd.DataFrame(rows), meta


def validate_machine_output(obj: Any) -> None:
    def walk(x: Any, key: str | None = None):
        if key and key in FORBIDDEN_MACHINE_TOKENS:
            raise ProbeError(f"forbidden machine-readable key emitted: {key}")
        if isinstance(x, str) and x in FORBIDDEN_MACHINE_TOKENS:
            raise ProbeError(f"forbidden machine-readable value emitted: {x}")
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, str(k))
        elif isinstance(x, list):
            for v in x: walk(v)
    walk(obj)


def diagnostic_assessment(cost_df: pd.DataFrame, turn_df: pd.DataFrame) -> str:
    one = cost_df[cost_df["horizon_days"].isin([1, 3])]["one_roundtrip_net_high"].dropna()
    ten = cost_df[cost_df["horizon_days"] == 10]["one_roundtrip_net_high"].dropna()
    low_turnover_gap = turn_df["median_inter_signal_gap_days"].iloc[0]
    if len(ten) and (ten > 0).any() and (pd.isna(low_turnover_gap) or low_turnover_gap >= 10):
        return "compatible_evidence_promising_but_oos_required"
    if len(one) and (one > 0).any():
        return "compatible_evidence_weak"
    return "compatible_evidence_absent"


def write_outputs(out: Path, tables: dict[str, pd.DataFrame], summary: dict[str, Any]) -> None:
    out.mkdir(parents=True, exist_ok=True)
    for name, df in tables.items():
        df.to_parquet(out / f"{name}.parquet", index=False)
        df.to_csv(out / f"{name}.csv", index=False)
    validate_machine_output(summary)
    (out / "term_structure_turnover_diagnostics.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    non_goals = "\n".join(f"- {x}" for x in NON_GOALS)
    (out / "term_structure_turnover_diagnostics.md").write_text(
        f"# Stage-1b Term-Structure & Turnover Diagnostics\n\n## Non-goals\n\n{non_goals}\n\n## Diagnostic assessment\n\n`{summary['diagnostic_assessment']}`\n\n## Turnover-cost caveat\n\n{TURNOVER_CAVEAT}\n\n## Central question answer\n\nThe machine-readable assessment above is diagnostic only. Stage 2 remains blocked until this question is answered out of sample.\n\n## OOS requirement specification\n\nA future Stage-1c should pre-register a held-out validation design using existing split manifest infrastructure, with either a later time-window holdout, symbol holdout, or both. Any horizon or comparator found here is exposed to data-snooping risk and must not become decision-bearing on this dataset.\n",
        encoding="utf-8",
    )


def run(argv: list[str] | None = None) -> int:
    a = parse_args(argv)
    # No network: fail if code under test tries direct socket use after this point.
    socket.create_connection = lambda *args, **kwargs: (_ for _ in ()).throw(ProbeError("network access disabled for Stage-1b"))  # type: ignore[assignment]
    horizons = horizons_from_arg(a.horizons)
    if a.primary_reference_horizon_days != 10:
        raise ProbeError("primary reference horizon is fixed at 10 days")
    _, probe, manifest = load_stage1(Path(a.stage1_root))
    low, high = float(probe["cost_context"]["cost_log_low"]), float(probe["cost_context"]["cost_log_high"])
    events = load_events(Path(a.events))
    sym_col = symbol_column(events.columns)
    for c in ["as_of_daily_bar_id", "event_type", "historical_signal_bucket"]:
        if c not in events.columns: raise ProbeError(f"required column missing: {c}")
    symbols = available_history_symbols(Path(a.history_root))
    if a.benchmark_symbol not in symbols: raise ProbeError(f"benchmark symbol {a.benchmark_symbol} not resolvable")
    tier = map_tiers(events)
    df = events.copy()
    df["as_of_daily_bar_id"] = pd.to_datetime(df["as_of_daily_bar_id"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["history_symbol"], df["history_symbol_resolution_source"] = resolve_history_symbols(df, sym_col, symbols)
    df, unavailable, missing_hist = add_returns(df, Path(a.history_root), horizons, a.benchmark_symbol)
    scope = static_scope(df, sym_col, a.benchmark_symbol)
    tier_col, conf, watch = tier["source"], tier["confirmed_tier"], tier["watch_tier"]
    tables = {
        "term_structure": term_structure(scope, tier_col, horizons, a.min_count, a.seed, a.n_bootstrap),
        "persistence": persistence(scope, tier_col, conf),
        "cost_break_even": cost_break_even(scope, tier_col, conf, horizons, low, high),
        "turnover_signal_frequency": turnover(scope, tier_col, conf),
        "same_date_coverage": same_date(scope, tier_col, conf, watch),
    }
    surv, surv_meta = survivorship(scope, tier_col, conf, horizons, a.tail_contributor_count, Path(a.history_root)); tables["survivorship"] = surv
    for name, table in tables.items():
        if not table.empty and "analysis_role" in table.columns and not (table["analysis_role"] == "diagnostic").all():
            raise ProbeError(f"non-diagnostic analysis_role in {name}")
    assess = diagnostic_assessment(tables["cost_break_even"], tables["turnover_signal_frequency"])
    if assess not in ASSESSMENTS: raise ProbeError("invalid diagnostic assessment")
    summary = {"analysis_role": "diagnostic", "diagnostic_assessment": assess, "created_at_utc": datetime.now(timezone.utc).isoformat(), "inputs": {"stage1_root": str(a.stage1_root), "events": str(a.events), "history_root": str(a.history_root), "stage1_manifest_run_id": manifest.get("run_id")}, "cost_context": {"cost_log_low": low, "cost_log_high": high}, "validation": {"relative_return_unavailable_by_horizon": unavailable, "missing_price_history_count": missing_hist}, "survivorship": surv_meta, "non_goals": NON_GOALS, "oos_requirement_specified_not_executed": True}
    write_outputs(Path(a.output_root) / a.replay_id, tables, summary)
    print(f"wrote {Path(a.output_root) / a.replay_id}")
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except ProbeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    main()
