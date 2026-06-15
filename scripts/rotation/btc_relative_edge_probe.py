#!/usr/bin/env python3
"""BTC-relative edge probe for historical replay events.

Standalone analysis script: reads enriched replay events plus local 1d OHLCV history,
computes BTC-relative forward log returns, and writes Stage-1 probe artifacts.
"""
from __future__ import annotations

import argparse, json, math, re, sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

HORIZONS_DEFAULT = [1,3,5,10,20]
SYMBOL_CANDIDATES = ["symbol", "pair", "pair_symbol"]
OPTIONAL_FIELDS = ["btc_regime_label","signal_day_quote_volume","median_quote_volume_30d","median_quote_volume_90d","quote_volume_bucket","available_history_days_1d_at_event","is_tradeable_candidate","universe_category"]
DENYLIST_DEFAULT = ["USDC","USDT","FDUSD","DAI","TUSD","USDE"]
CAVEATS = [
"This is an exploratory edge-existence probe, NOT a trading backtest.",
"This is NOT a TAO/BTC-specific strategy validation.",
"No live trading rule is derived from this stage.",
"Results are conditional on the available historical universe and surviving listings\n(survivorship bias present).",
"Tradeability here is a historical liquidity/exclusion proxy only, NOT real MEXC order-book tradeability.",
"Costs are shown as break-even context only; no rotation, turnover, or execution is\nsimulated.",
"Forward windows overlap and same-date events are correlated; effective sample size\nis far below the row count.",
"Results reflect a single historical regime path (2025-05 to 2026-05); one realization,\nnot a distribution.",
"Only the single pre-registered primary test (and the dual-gate rule) is decision-bearing;\nall other cuts are exploratory.",
]

class ProbeError(RuntimeError): pass

def norm_label(x: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(x).lower()).strip("_")

def finite_pos(x: Any) -> bool:
    try: return math.isfinite(float(x)) and float(x) > 0
    except Exception: return False

def parse_args(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument("--dataset", required=True)
    p.add_argument("--history-root", default="snapshots/history/ohlcv")
    p.add_argument("--output-root", default="evaluation/rotation/stage1")
    p.add_argument("--replay-id")
    p.add_argument("--horizons", default=",".join(map(str,HORIZONS_DEFAULT)))
    p.add_argument("--primary-horizon", type=int, default=10)
    p.add_argument("--min-count", type=int, default=30)
    p.add_argument("--min-qualifying-dates", type=int, default=20)
    p.add_argument("--n-bootstrap", type=int, default=2000)
    p.add_argument("--seed", type=int, default=12345)
    p.add_argument("--cost-bps-low", type=float, default=30)
    p.add_argument("--cost-bps-high", type=float, default=80)
    p.add_argument("--min-quote-volume", type=float, default=0)
    p.add_argument("--benchmark-symbol", default="BTCUSDT")
    p.add_argument("--cross-check-tolerance", type=float, default=1e-8)
    return p.parse_args(argv)

def validate_config(a):
    hs=[int(x) for x in str(a.horizons).split(',') if str(x).strip()]
    if a.primary_horizon != 10: raise ProbeError("--primary-horizon is fixed by the Stage-1 contract and must be exactly 10")
    if not hs or any(h<=0 for h in hs) or a.primary_horizon not in hs or 10 not in hs: raise ProbeError("invalid horizon list; primary horizon 10 must be present")
    if a.min_count<=0 or a.n_bootstrap<=0: raise ProbeError("--min-count and --n-bootstrap must be > 0")
    if a.cost_bps_low<0 or a.cost_bps_high<a.cost_bps_low or a.min_quote_volume<0: raise ProbeError("invalid cost/liquidity config")
    if not isinstance(a.benchmark_symbol,str) or not a.benchmark_symbol.strip(): raise ProbeError("--benchmark-symbol must be non-empty")
    return hs

def load_events(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0: raise ProbeError(f"enriched replay events missing/empty: {path}")
    try: df=pd.read_parquet(path)
    except Exception as e: raise ProbeError(f"cannot read events parquet: {e}") from e
    if df.empty: raise ProbeError("enriched replay events is empty")
    return df

def symbol_column(cols: Iterable[str]) -> str:
    for c in SYMBOL_CANDIDATES:
        if c in cols: return c
    raise ProbeError(f"symbol identifier not found in {SYMBOL_CANDIDATES}")

def required_columns(df):
    sym=symbol_column(df.columns)
    missing=[c for c in ["as_of_daily_bar_id","event_type","historical_signal_bucket"] if c not in df.columns]
    if missing: raise ProbeError(f"required columns missing: {missing}")
    return sym

def history_dir(root: Path, symbol: str) -> Path: return root/"timeframe=1d"/f"symbol={symbol}"

def available_history_symbols(root: Path) -> set[str]:
    base=root/"timeframe=1d"
    if not base.exists(): raise ProbeError(f"history root missing: {base}")
    return {p.name.split('=',1)[1] for p in base.glob('symbol=*') if p.is_dir()}

def load_close_series(root: Path, symbol: str) -> pd.Series:
    d=history_dir(root,symbol)
    files=sorted(d.glob("year=*/month=*/*.parquet"))
    if not d.exists() or not files: raise ProbeError(f"{symbol} 1d closes absent/empty under {d}")
    frames=[]
    for f in files: frames.append(pd.read_parquet(f))
    df=pd.concat(frames, ignore_index=True)
    columns=list(df.columns)
    if "close" not in df.columns:
        raise ProbeError(f"history for {symbol} lacks supported date/close columns; columns={columns}")
    date_sources=["daily_bar_id", "open_time_utc", "date", "timestamp"]
    if not any(c in df.columns for c in date_sources):
        raise ProbeError(f"history for {symbol} lacks supported date/close columns; columns={columns}")
    date_series=pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns, UTC]")
    for column in date_sources:
        if column in df.columns:
            parsed=pd.to_datetime(df[column], utc=True, errors="coerce")
            date_series=date_series.fillna(parsed)
    if date_series.isna().all():
        raise ProbeError(f"history for {symbol} has supported date columns but all dates failed to parse; columns={columns}")
    dates=date_series.dt.strftime("%Y-%m-%d")
    s=pd.Series(pd.to_numeric(df["close"], errors="coerce").to_numpy(), index=dates).dropna()
    return s[~s.index.duplicated(keep="last")].sort_index()

def resolve_history_symbols(df, sym_col, symbols):
    resolved=[]; sources=[]
    for raw in df[sym_col].astype(str):
        if raw in symbols: resolved.append(raw); sources.append("exact")
        elif not raw.endswith("USDT") and raw+"USDT" in symbols: resolved.append(raw+"USDT"); sources.append("base_plus_usdt")
        else: resolved.append(None); sources.append("unavailable")
    return resolved, sources

def map_tiers(df):
    inv={"historical_signal_bucket": sorted(map(str, df["historical_signal_bucket"].dropna().unique())), "event_type": sorted(map(str, df["event_type"].dropna().unique()))}
    bmap={raw:norm_label(raw) for raw in inv["historical_signal_bucket"]}
    conf=[r for r,n in bmap.items() if "confirmed" in n]; watch=[r for r,n in bmap.items() if "watch" in n]
    if len(conf)==1 and len(watch)==1:
        return {"source":"historical_signal_bucket","confirmed_tier":conf[0],"watch_tier":watch[0],"inventory":inv}
    evnorm={raw:norm_label(raw) for raw in inv["event_type"]}
    rev={v:k for k,v in evnorm.items()}
    if "first_confirmed_ready" in rev and "first_watch" in rev:
        return {"source":"event_type","confirmed_tier":rev["first_confirmed_ready"],"watch_tier":rev["first_watch"],"inventory":inv}
    raise ProbeError(f"confirmed/watch tiers not identifiable; observed={inv}")

def add_returns(df, root, horizons, benchmark):
    cache={benchmark: load_close_series(root, benchmark)}; unavailable={str(h):0 for h in horizons}
    unresolved_count=int((df["history_symbol_resolution_source"]=="unavailable").sum()) if "history_symbol_resolution_source" in df.columns else int(df["history_symbol"].isna().sum())
    missing_hist=unresolved_count
    for sym in sorted(set(x for x in df["history_symbol"].dropna())):
        if sym not in cache:
            try: cache[sym]=load_close_series(root,sym)
            except ProbeError: missing_hist += int((df["history_symbol"]==sym).sum()); cache[sym]=pd.Series(dtype=float)
    alt_logs={str(h):[] for h in horizons}; rels={str(h):[] for h in horizons}
    for _,r in df.iterrows():
        sym=r["history_symbol"]; t=str(r["as_of_daily_bar_id"])[:10]
        for h in horizons:
            key=str(h); t2=(pd.Timestamp(t)+pd.Timedelta(days=h)).strftime("%Y-%m-%d")
            a=cache.get(sym,pd.Series(dtype=float)); b=cache[benchmark]
            vals=[a.get(t,np.nan), a.get(t2,np.nan), b.get(t,np.nan), b.get(t2,np.nan)]
            if not all(finite_pos(v) for v in vals): alt_logs[key].append(np.nan); rels[key].append(np.nan); unavailable[key]+=1
            else:
                al=math.log(vals[1]/vals[0]); bl=math.log(vals[3]/vals[2]); alt_logs[key].append(al); rels[key].append(al-bl)
    for h in horizons:
        df[f"alt_log_return_{h}d"]=alt_logs[str(h)]; df[f"relative_log_return_{h}d"]=rels[str(h)]
    return df, unavailable, missing_hist

def bootstrap_ci_by_week(df, value_col, stat_fn, n=2000, seed=12345):
    d=df[["as_of_daily_bar_id", value_col]].dropna().copy()
    if d.empty: return (None,None)
    d["week"]=pd.to_datetime(d["as_of_daily_bar_id"]).dt.strftime("%G-%V")
    weeks=sorted(d["week"].unique()); rng=np.random.default_rng(seed); stats=[]
    for _ in range(n):
        sample_weeks=rng.choice(weeks, size=len(weeks), replace=True)
        sample=pd.concat([d[d.week==w] for w in sample_weeks], ignore_index=True)
        try: stats.append(float(stat_fn(sample[value_col].dropna())))
        except Exception: pass
    if not stats: return (None,None)
    return tuple(float(x) for x in np.percentile(stats,[2.5,97.5]))

def bootstrap_raw_pooled_spread_ci(df, tier_col, conf, watch, value_col, n=2000, seed=12345):
    d=df[["as_of_daily_bar_id", tier_col, value_col]].dropna().copy()
    if d.empty: return (None,None)
    d["week"]=pd.to_datetime(d["as_of_daily_bar_id"]).dt.strftime("%G-%V")
    weeks=sorted(d["week"].unique()); rng=np.random.default_rng(seed); stats=[]
    for _ in range(n):
        sample_weeks=rng.choice(weeks, size=len(weeks), replace=True)
        sample=pd.concat([d[d.week==w] for w in sample_weeks], ignore_index=True)
        c=sample[sample[tier_col]==conf][value_col].dropna()
        w=sample[sample[tier_col]==watch][value_col].dropna()
        if len(c) and len(w): stats.append(float(c.median()-w.median()))
    if not stats: return (None,None)
    return tuple(float(x) for x in np.percentile(stats,[2.5,97.5]))

def segment_metrics(df, group, key, role, horizons, min_count, costs, n_boot, seed, primary_horizon=None):
    rows=[]
    for h in horizons:
        col=f"relative_log_return_{h}d"; vals=df[col].dropna(); cnt=int(vals.size); passn=cnt>=min_count
        ci=(None,None) if not passn else bootstrap_ci_by_week(df.dropna(subset=[col]), col, np.median, n_boot, seed)
        med=float(vals.median()) if cnt else None
        if med is None: net="unavailable"
        elif med < costs[0]: net="below_cost"
        elif med <= costs[1]: net="marginal"
        else: net="above_cost"
        row_role = role(h) if callable(role) else role
        rows.append({"analysis_role":row_role,"segment_group":group,"segment_key":str(key),"horizon":h,"event_count":cnt,"unique_symbol_count":int(df.loc[vals.index,"history_symbol"].nunique()) if cnt else 0,"mean_relative_log_return":float(vals.mean()) if cnt else None,"median_relative_log_return":med,"hit_rate_vs_btc":float((vals>0).mean()) if cnt else None,"bootstrap_ci_low":ci[0],"bootstrap_ci_high":ci[1],"passes_min_count":bool(passn),"trimmed_mean_10pct":float(vals[(vals>=vals.quantile(.1))&(vals<=vals.quantile(.9))].mean()) if cnt else None,"winsorized_mean_5pct":float(vals.clip(vals.quantile(.05), vals.quantile(.95)).mean()) if cnt else None,"p25":float(vals.quantile(.25)) if cnt else None,"p75":float(vals.quantile(.75)) if cnt else None,"net_indication":net})
    return rows

def primary_stats(scope, tier_col, conf, watch, ph, min_dates, n_boot, seed, cost_high):
    col=f"relative_log_return_{ph}d"; d=scope.dropna(subset=[col]).copy()
    spreads=[]
    for date,g in d.groupby("as_of_daily_bar_id"):
        c=g[g[tier_col]==conf][col]; w=g[g[tier_col]==watch][col]
        if len(c)>=1 and len(w)>=1: spreads.append({"as_of_daily_bar_id":date,"spread":float(c.median()-w.median())})
    sp=pd.DataFrame(spreads)
    if len(sp) >= min_dates:
        estimator="same_date_bucket_spread"; robustness="standard"; val=float(sp.spread.median()); ci=bootstrap_ci_by_week(sp,"spread",np.median,n_boot,seed)
    else:
        estimator="raw_pooled_fallback"; robustness="reduced"
        c=d[d[tier_col]==conf][col]; w=d[d[tier_col]==watch][col]
        val=float(c.median()-w.median()) if len(c) and len(w) else None
        ci=bootstrap_raw_pooled_spread_ci(d,tier_col,conf,watch,col,n_boot,seed) if val is not None else (None,None)
    demean=d.copy(); demean["resid"]=demean[col]-demean.groupby("as_of_daily_bar_id")[col].transform("mean")
    rc=demean[demean[tier_col]==conf].resid; rw=demean[demean[tier_col]==watch].resid
    resid_diff=float(rc.median()-rw.median()) if len(rc) and len(rw) else None
    confirmed=d[d[tier_col]==conf][col]
    confirmed_med=float(confirmed.median()) if len(confirmed) else None
    return {"primary_estimator":estimator,"robustness":robustness,"qualifying_date_count":int(len(sp)),"primary_spread_median":val,"primary_spread_ci_low":ci[0],"primary_spread_ci_high":ci[1],"date_demeaned_residual_diff_median":resid_diff,"raw_confirmed_median_relative_log_return":confirmed_med,"gate_a_pass":bool(val is not None and ci[0] is not None and val>0 and ci[0]>0),"gate_b_pass":bool(confirmed_med is not None and confirmed_med>cost_high)}

def write_outputs(out, seg, manifest, summary, md_extra):
    out.mkdir(parents=True, exist_ok=True)
    seg.to_parquet(out/"segment_relative_returns.parquet", index=False); seg.to_csv(out/"segment_relative_returns.csv", index=False)
    (out/"probe_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    (out/"btc_relative_edge_probe.json").write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    caveat_lines="\n".join(f"- {c}" for c in CAVEATS)
    (out/"btc_relative_edge_probe.md").write_text(f"# BTC Relative Edge Probe\n\n## Dual-gate result\n\n```json\n{json.dumps(summary.get('dual_gate_result',{}), indent=2)}\n```\n\n## Mandatory caveats\n\n{caveat_lines}\n\n## Notes\n\n{md_extra}\n", encoding="utf-8")

def run(argv=None):
    a=parse_args(argv); horizons=validate_config(a)
    dataset=Path(a.dataset); root=Path(a.history_root); df=load_events(dataset); source_columns=list(df.columns); sym=required_columns(df)
    symbols=available_history_symbols(root); benchmark=a.benchmark_symbol.strip()
    if benchmark not in symbols: raise ProbeError(f"benchmark symbol {benchmark} not resolvable in 1d history root")
    tier=map_tiers(df)
    df=df.copy(); df["as_of_daily_bar_id"]=pd.to_datetime(df["as_of_daily_bar_id"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["history_symbol"], df["history_symbol_resolution_source"] = resolve_history_symbols(df,sym,symbols)
    resolution_counts=df["history_symbol_resolution_source"].value_counts(dropna=False).to_dict()
    df, unavailable, missing_hist = add_returns(df, root, horizons, benchmark)
    benchmark_count=int((df["history_symbol"]==benchmark).sum())
    base=df["history_symbol"].fillna(df[sym].astype(str)).astype(str).str.replace(r"USDT$","",regex=True)
    excl_static=base.isin(DENYLIST_DEFAULT)
    if "universe_category" in df.columns:
        cat=df["universe_category"].astype(str).str.lower(); excl_cat=cat.str.contains("stable|tokenized|stock|cash", regex=True, na=False)
    else: excl_cat=pd.Series(False,index=df.index)
    metric_all=df[(df["history_symbol"].notna()) & (df["history_symbol"]!=benchmark)].copy()
    scope=metric_all[~excl_static.loc[metric_all.index] & ~excl_cat.loc[metric_all.index]].copy()
    if "median_quote_volume_30d" in scope.columns and a.min_quote_volume>0: scope=scope[pd.to_numeric(scope["median_quote_volume_30d"],errors="coerce")>=a.min_quote_volume]
    tier_col=tier["source"]; conf=tier["confirmed_tier"]; watch=tier["watch_tier"]
    costs=(math.log(1+a.cost_bps_low/10000), math.log(1+a.cost_bps_high/10000))
    rows=[]; rows+=segment_metrics(metric_all,"scope","all_events_system_view","secondary_exploratory",horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    primary_scope_role=lambda h: "primary" if h == a.primary_horizon else "secondary_exploratory"
    rows+=segment_metrics(scope,"scope","operational_proxy_filtered",primary_scope_role,horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    for val,g in scope.groupby(tier_col, dropna=False): rows+=segment_metrics(g,"tier",val,"secondary_exploratory",horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    for field in ["btc_regime_label","quote_volume_bucket"]:
        if field in scope.columns:
            for val,g in scope.groupby(field, dropna=False): rows+=segment_metrics(g,field,val,"secondary_exploratory",horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    if "btc_regime_label" in scope.columns:
        for (tv,rv),g in scope.groupby([tier_col,"btc_regime_label"], dropna=False): rows+=segment_metrics(g,"tier_x_btc_regime_label",f"{tv}|{rv}","secondary_exploratory",horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    for val,g in scope.groupby("history_symbol", dropna=False): rows+=segment_metrics(g,"symbol",val,"secondary_exploratory",horizons,a.min_count,costs,a.n_bootstrap,a.seed)
    seg=pd.DataFrame(rows).sort_values(["analysis_role","segment_group","horizon","passes_min_count","median_relative_log_return","segment_key"], ascending=[True,True,True,False,False,True], na_position="last")
    primary=primary_stats(scope,tier_col,conf,watch,a.primary_horizon,a.min_qualifying_dates,a.n_bootstrap,a.seed,costs[1])
    col=f"relative_log_return_{a.primary_horizon}d"; pos=scope.dropna(subset=[col]); contributors=pos[pos[col]>0].groupby("history_symbol")[col].sum().sort_values(ascending=False)
    if contributors.sum()>0:
        top5=list(contributors.head(5).index); conc=float(contributors.head(5).sum()/contributors.sum()); status="available"
    else: top5=[]; conc=None; status="not_applicable_no_positive_edge"
    top_detail=[{"symbol":s,"event_count":int((pos.history_symbol==s).sum()),"median_r_rel_10":float(pos[pos.history_symbol==s][col].median())} for s in top5]
    excl_primary=primary_stats(scope[~scope.history_symbol.isin(top5)],tier_col,conf,watch,a.primary_horizon,a.min_qualifying_dates,a.n_bootstrap,a.seed,costs[1]) if top5 else primary
    generated_columns=[c for c in df.columns if c not in source_columns]
    unresolved_history_symbol_count=int((df["history_symbol_resolution_source"]=="unavailable").sum())
    validation={"relative_return_unavailable_by_horizon":unavailable,"unresolved_history_symbol_count":unresolved_history_symbol_count,"missing_price_history_count":missing_hist,"cross_check":{}}
    for h in horizons:
        f=f"forward_close_return_{h}d"; has=f"has_forward_{h}d"
        if f in df.columns and has in df.columns:
            m=df[has].astype(bool) & df[f].notna() & df[f"alt_log_return_{h}d"].notna(); dev=(df.loc[m,f"alt_log_return_{h}d"]-np.log1p(pd.to_numeric(df.loc[m,f],errors="coerce"))).abs()
            validation["cross_check"][str(h)]={"available":True,"mismatch_count":int((dev>a.cross_check_tolerance).sum()),"max_abs_deviation":float(dev.max()) if len(dev) else None}
        else: validation["cross_check"][str(h)]={"available":False}
    manifest={"created_at_utc":datetime.now(timezone.utc).isoformat(),"dataset_path":str(dataset),"dataset_columns":source_columns,"generated_columns":generated_columns,"symbol_identifier_column_used":sym,"tier_mapping":tier,"history_symbol_resolution_counts":resolution_counts,"benchmark_symbol":benchmark,"benchmark_self_excluded_count":benchmark_count,"optional_field_availability":{f:f in source_columns for f in OPTIONAL_FIELDS},"config":vars(a),"validation":validation,"exclusions":{"static_denylist_count":int(excl_static.sum()),"category_exclusion_count":int(excl_cat.sum()),"exclusion_source":"universe_category_or_static_denylist" if "universe_category" in df.columns else "static_denylist"}}
    summary={"primary":primary,"dual_gate_result":{"gate_a_genuine_signal":primary["gate_a_pass"],"gate_b_cost_viability":primary["gate_b_pass"],"stage2_green_light":bool(primary["gate_a_pass"] and primary["gate_b_pass"])},"cost_context":{"cost_log_low":costs[0],"cost_log_high":costs[1]},"concentration_share_top_5_symbols":conc,"concentration_status":status,"edge_sign_stable_excluding_top5":bool(excl_primary.get("primary_spread_median") is not None and excl_primary["primary_spread_median"]>0),"top_contributor_symbols":top_detail,"output_schema_version":"rotation_stage1_v1"}
    replay_id=a.replay_id or dataset.parent.name; out=Path(a.output_root)/replay_id
    write_outputs(out,seg,manifest,summary,"Generated standalone from enriched replay events and 1d OHLCV history. No rotation, turnover, or execution is simulated.")
    print(f"wrote {out}")
    return 0

def main():
    try: raise SystemExit(run())
    except ProbeError as e:
        print(f"ERROR: {e}", file=sys.stderr); raise SystemExit(2)
if __name__ == "__main__": main()
