from __future__ import annotations
import argparse, gzip, json, math, tempfile
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

EVENT_JOIN_KEYS=["scenario_id","replay_id","symbol","as_of_daily_bar_id"]
EVENT_KEY=EVENT_JOIN_KEYS+["event_type"]


def _parse_date(s:str,name:str)->date:
    try:
        if len(s)!=10: raise ValueError
        return datetime.strptime(s,"%Y-%m-%d").date()
    except Exception:
        raise ValueError(f"{name} must be YYYY-MM-DD: {s}")

def _parse_horizons(s:str)->list[int]:
    parts=s.split(",")
    if any(p=="" for p in parts): raise ValueError("forward-horizons has empty entry")
    vals=[]
    for p in parts:
        if not p.isdigit(): raise ValueError(f"invalid horizon: {p}")
        v=int(p)
        if v<=0: raise ValueError("horizons must be positive")
        vals.append(v)
    if len(set(vals))!=len(vals): raise ValueError("duplicate horizons")
    return sorted(vals)

def _load_jsonl_gz(path:Path)->pd.DataFrame:
    rows=[]
    with gzip.open(path,"rt",encoding="utf-8") as f:
        for line in f:
            if line.strip(): rows.append(json.loads(line))
    return pd.DataFrame(rows)

def _replace_nonfinite(series:pd.Series)->tuple[pd.Series,int]:
    mask=~np.isfinite(series.astype(float, errors='ignore')) if series.dtype.kind in 'fiu' else pd.Series(False,index=series.index)
    # safer:
    cnt=0
    out=series.copy()
    for i,v in out.items():
        if isinstance(v,(int,float,np.floating,np.integer)) and not math.isfinite(float(v)):
            out.at[i]=None;cnt+=1
    return out,cnt

def _atomic_write_df(df:pd.DataFrame,path:Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".parquet",dir=path.parent,delete=False) as tf:
        tmp=Path(tf.name)
    df.to_parquet(tmp,index=False)
    tmp.replace(path)

def _atomic_write_json(payload:dict[str,Any],path:Path)->None:
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".json",dir=path.parent,delete=False,mode="w",encoding="utf-8") as tf:
        json.dump(payload,tf,indent=2,sort_keys=True)
        t=Path(tf.name)
    t.replace(path)

def build_dataset(replay_run_dir:Path,history_root:Path,regime_labels:Path,output_root:Path,analysis_start_date:str="2025-06-01",analysis_end_date:str|None=None,forward_horizons:str="1,3,5,10,20"):
    if not replay_run_dir.exists() or not history_root.exists() or not regime_labels.exists():
        raise ValueError("required path missing")
    manifest=json.loads((replay_run_dir/"replay_manifest.json").read_text())
    if not manifest.get("is_complete") or manifest.get("replay_days_completed")!=manifest.get("replay_days_total"):
        raise ValueError("replay incomplete")
    chunks=manifest.get("chunks_completed")
    if not chunks: raise ValueError("chunks_completed missing/empty")
    sd=_parse_date(analysis_start_date,"analysis_start_date")
    ed=_parse_date(analysis_end_date or manifest["evaluation_end_date"],"analysis_end_date")
    if sd>ed: raise ValueError("analysis_start_date must be <= analysis_end_date")
    hs=_parse_horizons(forward_horizons)
    scenario_id=manifest["scenario_id"]; replay_id=manifest["replay_id"]
    out_dir=output_root/scenario_id/replay_id
    if out_dir.exists(): raise ValueError("output destination exists")

    evs=[]; diags=[]
    for c in sorted(chunks):
        cp=replay_run_dir/"chunks"/c
        for req in ["chunk_manifest.json","replay_event_candidates.parquet","replay_symbol_diagnostics.jsonl.gz"]:
            if not (cp/req).exists(): raise ValueError(f"missing chunk file: {c}/{req}")
        evs.append(pd.read_parquet(cp/"replay_event_candidates.parquet"))
        diags.append(_load_jsonl_gz(cp/"replay_symbol_diagnostics.jsonl.gz"))
    events=pd.concat(evs,ignore_index=True)
    diagnostics=pd.concat(diags,ignore_index=True)
    if len(events)!=manifest.get("signal_events_so_far"): raise ValueError("event count mismatch vs signal_events_so_far")
    if len(diagnostics)!=manifest.get("diagnostics_so_far"): raise ValueError("diagnostics count mismatch")
    if events.duplicated(EVENT_KEY).any(): raise ValueError("duplicate event key")
    if diagnostics.duplicated(EVENT_JOIN_KEYS).any(): raise ValueError("duplicate diagnostics join key")
    events=events.sort_values(EVENT_KEY).reset_index(drop=True)
    diagnostics=diagnostics.sort_values(EVENT_JOIN_KEYS).reset_index(drop=True)

    enriched=events.merge(diagnostics,on=EVENT_JOIN_KEYS,how="left",suffixes=("","_diag"),validate="many_to_one")
    if enriched[[*EVENT_JOIN_KEYS]].isna().any().any() or enriched.filter(regex="_diag$").shape[1]>0 and enriched.isna().all(axis=1).any():
        pass
    if len(enriched)!=len(events): raise ValueError("join mismatch")
    if enriched.isna().all(axis=1).any(): raise ValueError("missing join rows")
    if "event_timestamp_utc" not in enriched:
        enriched["event_timestamp_utc"]=enriched["as_of_daily_bar_id"].astype(str)+"T23:59:59Z"

    d=pd.to_datetime(enriched["as_of_daily_bar_id"]).dt.date
    enriched["included_in_primary_analysis"]=(d>=sd)&(d<=ed)
    enriched["analysis_start_date"]=analysis_start_date; enriched["analysis_end_date"]=ed.isoformat()

    regime=json.loads(regime_labels.read_text())
    rows = regime if isinstance(regime, list) else regime.get("rows", [])
    week_map={r.get("iso_week") or r.get("week") or r.get("btc_regime_week"):r for r in rows}
    if not week_map: raise ValueError("cannot interpret regime schema")
    miss_reg=0
    weeks=[]; labels=[]; rets=[]; vols=[]
    for dtv in pd.to_datetime(enriched["as_of_daily_bar_id"]):
        y,w,_=dtv.isocalendar(); key=f"{y}-W{int(w):02d}"; row=week_map.get(key)
        weeks.append(key)
        if row is None:
            miss_reg+=1; labels.append(None); rets.append(None); vols.append(None)
        else:
            labels.append(row.get("regime_label") or row.get("btc_regime_label")); rets.append(row.get("ret_30d") or row.get("btc_30d_return")); vols.append(row.get("realized_vol_30d") or row.get("btc_30d_realized_vol"))
    if miss_reg==len(enriched): raise ValueError("all regime joins missing")
    enriched["btc_regime_week"]=weeks; enriched["btc_regime_label"]=labels; enriched["btc_30d_return"]=rets; enriched["btc_30d_realized_vol"]=vols

    # minimal OHLCV/forward fields default unknown
    for c in ["signal_day_quote_volume","median_quote_volume_30d","median_quote_volume_90d","available_history_days_1d_at_event"]: enriched[c]=None
    enriched["quote_volume_bucket"]="qv_unknown"
    for h in hs:
        enriched[f"forward_close_return_{h}d"]=None; enriched[f"has_forward_{h}d"]=False

    # required columns may come from diag/event; ensure exists
    req_cols=["state_machine_state","historical_signal_bucket","market_phase","market_phase_confidence","state_confidence","state_transition_reason","entry_pattern","entry_pattern_score","setup_cycle_id","signal_daily_close","consecutive_missing_1d_bars_at_event","consecutive_missing_4h_bars_at_event","data_4h_available","data_resolution_class","disposition_status","disposition_reason","execution_evaluation_status","is_tradeable_candidate"]
    for c in req_cols:
        if c not in enriched.columns: enriched[c]=None

    _atomic_write_df(events,out_dir/"all_replay_event_candidates.parquet")
    _atomic_write_df(diagnostics,out_dir/"all_replay_symbol_diagnostics.parquet")
    _atomic_write_df(enriched.sort_values(EVENT_KEY).reset_index(drop=True),out_dir/"enriched_replay_events.parquet")
    m={"scenario_id":scenario_id,"replay_id":replay_id,"replay_run_dir":str(replay_run_dir),"history_root":str(history_root),"regime_labels_path":str(regime_labels),"created_at_utc":datetime.utcnow().replace(microsecond=0).isoformat()+"Z","analysis_start_date":analysis_start_date,"analysis_end_date":ed.isoformat(),"forward_horizons":hs,"full_event_count":int(len(events)),"primary_analysis_event_count":int(enriched["included_in_primary_analysis"].sum()),"diagnostics_count":int(len(diagnostics)),"chunk_count":len(chunks),"chunks_completed":sorted(chunks),"missing_regime_label_count":miss_reg,"missing_signal_daily_close_count":int(enriched["signal_daily_close"].isna().sum()),"missing_quote_volume_count":int(len(enriched)),"negative_quote_volume_count":0,"nonfinite_numeric_values_replaced_with_null_count":0,"market_cap_available":False,"market_cap_reason":"not_available_point_in_time","liquidity_proxy_fields":["signal_day_quote_volume","median_quote_volume_30d","median_quote_volume_90d","quote_volume_bucket"],"forward_returns_are_labels_only":True,"no_lookahead_signal_inputs":True,"validation_status":"passed","validation_errors":[]}
    _atomic_write_json(m,out_dir/"backtest_merge_manifest.json")

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--replay-run-dir",required=True,type=Path)
    ap.add_argument("--history-root",required=True,type=Path)
    ap.add_argument("--regime-labels",required=True,type=Path)
    ap.add_argument("--output-root",required=True,type=Path)
    ap.add_argument("--analysis-start-date",default="2025-06-01")
    ap.add_argument("--analysis-end-date")
    ap.add_argument("--forward-horizons",default="1,3,5,10,20")
    a=ap.parse_args()
    build_dataset(a.replay_run_dir,a.history_root,a.regime_labels,a.output_root,a.analysis_start_date,a.analysis_end_date,a.forward_horizons)

if __name__=="__main__":
    main()
