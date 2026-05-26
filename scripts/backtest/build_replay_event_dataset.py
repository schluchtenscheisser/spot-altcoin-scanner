from __future__ import annotations
import argparse, gzip, json, math, tempfile, glob
from dataclasses import dataclass
from datetime import datetime, date
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd

EVENT_JOIN_KEYS=["scenario_id","replay_id","symbol","as_of_daily_bar_id"]
EVENT_KEY=EVENT_JOIN_KEYS+["event_type"]
SIGNAL_ANALYSIS_DEDUP_KEY_FIELDS=["scenario_id","replay_id","symbol","as_of_daily_bar_id","historical_signal_bucket"]
ANALYSIS_EVENT_PRIORITY_ORDER={"first_confirmed_with_entry_pattern":1,"first_early_ready":2,"first_late":3,"first_chased":4,"first_rejected":5,"first_confirmed_ready":6}

def _first_present(mapping: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None

def _nonempty_str(value: Any) -> str | None:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return None


def _derive_regime_week_key(row: dict[str, Any]) -> str | None:
    for key in ("iso_week", "week", "btc_regime_week"):
        val = _nonempty_str(row.get(key))
        if val is not None:
            return val
    week_start = _nonempty_str(row.get("week_start_date"))
    if week_start is None:
        return None
    try:
        iso = date.fromisoformat(week_start).isocalendar()
    except ValueError:
        return None
    return f"{iso.year}-W{iso.week:02d}"


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


def _is_finite_number(value: Any) -> bool:
    return isinstance(value, (int, float, np.floating, np.integer)) and math.isfinite(float(value))


def _sanitize_numeric(value: Any) -> float | None:
    if _is_finite_number(value):
        return float(value)
    return None


def _bucket_quote_volume(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "qv_unknown"
    if value < 100_000:
        return "qv_lt_100k"
    if value < 1_000_000:
        return "qv_100k_1m"
    if value < 10_000_000:
        return "qv_1m_10m"
    if value < 100_000_000:
        return "qv_10m_100m"
    return "qv_ge_100m"


@dataclass
class SymbolHistory:
    dates: np.ndarray
    close: np.ndarray
    quote_volume: np.ndarray
    date_to_index: dict[str, int]


class OhlcvHistoryStore:
    def __init__(self, history_root: Path) -> None:
        self._root = history_root
        self._cache: dict[str, SymbolHistory | None] = {}

    def get(self, symbol: str) -> SymbolHistory | None:
        if symbol not in self._cache:
            self._cache[symbol] = self._load_symbol(symbol)
        return self._cache[symbol]

    def _load_symbol(self, symbol: str) -> SymbolHistory | None:
        pattern = str(self._root / f"timeframe=1d/symbol={symbol}/year=*/month=*/part-*.parquet")
        files = sorted(glob.glob(pattern))
        if not files:
            return None
        df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
        if df.empty or "close_time_utc" not in df.columns:
            return None
        if "is_closed" in df.columns:
            df = df[df["is_closed"] == True]
        if df.empty:
            return None
        df["close_time_utc"] = pd.to_datetime(df["close_time_utc"], errors="coerce", utc=True)
        df = df.dropna(subset=["close_time_utc"]).sort_values("close_time_utc").reset_index(drop=True)
        if df.empty:
            return None
        df["bar_date"] = df["close_time_utc"].dt.strftime("%Y-%m-%d")
        df = df.drop_duplicates(subset=["bar_date"], keep="last").reset_index(drop=True)
        close = df["close"].map(_sanitize_numeric).to_numpy(dtype=object) if "close" in df.columns else np.array([None]*len(df), dtype=object)
        qv = df["quote_volume"].map(_sanitize_numeric).to_numpy(dtype=object) if "quote_volume" in df.columns else np.array([None]*len(df), dtype=object)
        dates = df["bar_date"].to_numpy()
        return SymbolHistory(dates=dates, close=close, quote_volume=qv, date_to_index={d:i for i,d in enumerate(dates)})

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

_NULLABLE_STRING_COLUMNS = [
    "setup_cycle_id",
    "state_machine_state",
    "state_transition_reason",
    "entry_pattern",
    "historical_signal_bucket",
    "market_phase",
    "disposition_status",
    "disposition_reason",
    "execution_evaluation_status",
    "data_resolution_class",
    "event_type",
    "scenario_id",
    "replay_id",
    "symbol",
    "as_of_daily_bar_id",
    "event_timestamp_utc",
    "btc_regime_week",
    "btc_regime_label",
    "quote_volume_bucket",
    "dedup_group_key",
    "analysis_event_type",
    "dedup_reason",
]


def _normalize_nullable_string_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    if column not in df.columns:
        return df
    out = df.copy()
    out[column] = out[column].map(lambda v: None if pd.isna(v) else str(v))
    return out


def _normalize_nullable_string_columns(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df
    for column in columns:
        out = _normalize_nullable_string_column(out, column)
    return out



def _apply_signal_analysis_dedup_fields(enriched: pd.DataFrame) -> pd.DataFrame:
    out = enriched.copy()
    out["dedup_group_key"] = out[SIGNAL_ANALYSIS_DEDUP_KEY_FIELDS].map(lambda c: "" if pd.isna(c) else str(c)).agg("|".join, axis=1)
    out["analysis_event_rank"] = out["event_type"].map(lambda e: ANALYSIS_EVENT_PRIORITY_ORDER.get(str(e), 99)).astype(int)
    ranked = out.sort_values(["dedup_group_key", "analysis_event_rank", "event_type", "symbol", "as_of_daily_bar_id"], kind="mergesort")
    selected_index = set(ranked.groupby("dedup_group_key", sort=False).head(1).index.tolist())
    out["included_in_signal_analysis"] = out.index.to_series().map(lambda i: i in selected_index).astype(bool)
    out["analysis_event_type"] = np.where(out["included_in_signal_analysis"], out["event_type"], None)
    out["dedup_reason"] = np.where(out["included_in_signal_analysis"], "selected_primary_event", "duplicate_lower_priority_event")
    return out

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

    enriched=events.merge(
        diagnostics,
        on=EVENT_JOIN_KEYS,
        how="left",
        suffixes=("","_diag"),
        validate="many_to_one",
        indicator=True,
    )
    if len(enriched)!=len(events): raise ValueError("join mismatch")
    missing = enriched["_merge"] != "both"
    if missing.any():
        sample = enriched.loc[missing, EVENT_KEY].head(20).to_dict("records")
        raise ValueError(
            f"events without matching diagnostics rows: count={int(missing.sum())}, sample={sample}"
        )
    enriched = enriched.drop(columns=["_merge"])
    if "event_timestamp_utc" not in enriched:
        enriched["event_timestamp_utc"]=enriched["as_of_daily_bar_id"].astype(str)+"T23:59:59Z"

    d=pd.to_datetime(enriched["as_of_daily_bar_id"]).dt.date
    enriched["included_in_primary_analysis"]=(d>=sd)&(d<=ed)
    enriched["analysis_start_date"]=analysis_start_date; enriched["analysis_end_date"]=ed.isoformat()

    regime=json.loads(regime_labels.read_text())
    if isinstance(regime, list):
        rows = regime
    elif isinstance(regime, dict):
        rows = regime.get("rows") or regime.get("labels") or []
    else:
        rows = []
    week_map={}
    for r in rows:
        key = _derive_regime_week_key(r)
        if key is None:
            continue
        if key in week_map:
            raise ValueError(f"duplicate regime week key: {key}")
        week_map[key]=r
    if not week_map: raise ValueError("cannot interpret regime schema: expected top-level list, rows, or labels with non-empty iso_week/week/btc_regime_week or valid week_start_date")
    miss_reg=0
    weeks=[]; labels=[]; rets=[]; vols=[]
    for dtv in pd.to_datetime(enriched["as_of_daily_bar_id"]):
        y,w,_=dtv.isocalendar(); key=f"{y}-W{int(w):02d}"; row=week_map.get(key)
        weeks.append(key)
        if row is None:
            miss_reg+=1; labels.append(None); rets.append(None); vols.append(None)
        else:
            labels.append(_first_present(row, "regime_label", "btc_regime_label")); rets.append(_first_present(row, "btc_30d_return_pct", "ret_30d", "btc_30d_return")); vols.append(_first_present(row, "btc_30d_realized_vol_annualized_pct", "realized_vol_30d", "btc_30d_realized_vol"))
    if miss_reg==len(enriched): raise ValueError("all regime joins missing")
    enriched["btc_regime_week"]=weeks; enriched["btc_regime_label"]=labels; enriched["btc_30d_return"]=rets; enriched["btc_30d_realized_vol"]=vols

    history_store = OhlcvHistoryStore(history_root)
    symbol_missing_history: set[str] = set()
    event_missing_history_count = 0
    nonfinite_replaced = 0

    for c in ["signal_day_quote_volume","median_quote_volume_30d","median_quote_volume_90d","available_history_days_1d_at_event"]:
        enriched[c]=None
    enriched["quote_volume_bucket"]="qv_unknown"
    for h in hs:
        enriched[f"forward_close_return_{h}d"]=None
        enriched[f"has_forward_{h}d"]=False

    for idx, row in enriched.iterrows():
        symbol = row["symbol"]
        event_day = str(row["as_of_daily_bar_id"])
        history = history_store.get(symbol)
        if history is None:
            symbol_missing_history.add(symbol)
            event_missing_history_count += 1
            continue
        pos = history.date_to_index.get(event_day)
        if pos is None:
            prior_count = int(np.searchsorted(history.dates, event_day, side="right"))
            enriched.at[idx, "available_history_days_1d_at_event"] = prior_count
            continue

        enriched.at[idx, "available_history_days_1d_at_event"] = pos + 1
        signal_qv = history.quote_volume[pos]
        enriched.at[idx, "signal_day_quote_volume"] = signal_qv

        last30 = [v for v in history.quote_volume[max(0, pos - 29): pos + 1] if v is not None]
        last90 = [v for v in history.quote_volume[max(0, pos - 89): pos + 1] if v is not None]
        if last30:
            enriched.at[idx, "median_quote_volume_30d"] = float(np.median(last30))
        if last90:
            enriched.at[idx, "median_quote_volume_90d"] = float(np.median(last90))

        qv_ref = _sanitize_numeric(enriched.at[idx, "median_quote_volume_30d"])
        if qv_ref is None:
            qv_ref = signal_qv
        enriched.at[idx, "quote_volume_bucket"] = _bucket_quote_volume(qv_ref)

        signal_close = _sanitize_numeric(row.get("signal_daily_close"))
        for h in hs:
            future_idx = pos + h
            has_col = f"has_forward_{h}d"
            ret_col = f"forward_close_return_{h}d"
            if future_idx < len(history.close):
                future_close = history.close[future_idx]
                if future_close is not None and signal_close is not None and signal_close > 0:
                    enriched.at[idx, has_col] = True
                    enriched.at[idx, ret_col] = float(future_close / signal_close - 1.0)
                else:
                    enriched.at[idx, has_col] = False
                    enriched.at[idx, ret_col] = None
            else:
                enriched.at[idx, has_col] = False
                enriched.at[idx, ret_col] = None

    for col in ["signal_day_quote_volume", "median_quote_volume_30d", "median_quote_volume_90d"] + [f"forward_close_return_{h}d" for h in hs]:
        if col in enriched.columns:
            before = enriched[col].isna().sum()
            enriched[col] = pd.to_numeric(enriched[col], errors="coerce")
            after = enriched[col].isna().sum()
            nonfinite_replaced += int(after - before)

    # required columns may come from diag/event; ensure exists
    req_cols=["state_machine_state","historical_signal_bucket","market_phase","market_phase_confidence","state_confidence","state_transition_reason","entry_pattern","entry_pattern_score","setup_cycle_id","signal_daily_close","consecutive_missing_1d_bars_at_event","consecutive_missing_4h_bars_at_event","data_4h_available","data_resolution_class","disposition_status","disposition_reason","execution_evaluation_status","is_tradeable_candidate"]
    for c in req_cols:
        if c not in enriched.columns: enriched[c]=None

    enriched=_apply_signal_analysis_dedup_fields(enriched)

    events_for_write = _normalize_nullable_string_columns(events, _NULLABLE_STRING_COLUMNS)
    diagnostics_for_write = _normalize_nullable_string_columns(diagnostics, _NULLABLE_STRING_COLUMNS)
    enriched_for_write = _normalize_nullable_string_columns(
        enriched.sort_values(EVENT_KEY).reset_index(drop=True),
        _NULLABLE_STRING_COLUMNS,
    )

    _atomic_write_df(events_for_write,out_dir/"all_replay_event_candidates.parquet")
    _atomic_write_df(diagnostics_for_write,out_dir/"all_replay_symbol_diagnostics.parquet")
    _atomic_write_df(enriched_for_write,out_dir/"enriched_replay_events.parquet")
    missing_forward = {str(h): int((~enriched[f"has_forward_{h}d"].fillna(False)).sum()) for h in hs}
    quote_bucket_counts = {k: int(v) for k, v in enriched["quote_volume_bucket"].value_counts(dropna=False).items()}
    primary = enriched[enriched["included_in_primary_analysis"]]
    primary_quote_bucket_counts = {k: int(v) for k, v in primary["quote_volume_bucket"].value_counts(dropna=False).items()}
    raw_event_count=int(len(enriched)); signal_analysis_event_count=int(enriched["included_in_signal_analysis"].sum()); primary_signal_analysis_event_count=int((enriched["included_in_signal_analysis"]&enriched["included_in_primary_analysis"]).sum()); duplicate_signal_event_count=int(raw_event_count-signal_analysis_event_count); duplicate_signal_event_count_by_event_type={str(k):int(v) for k,v in enriched.loc[~enriched["included_in_signal_analysis"],"event_type"].value_counts(dropna=False).items()}
    m={"scenario_id":scenario_id,"replay_id":replay_id,"replay_run_dir":str(replay_run_dir),"history_root":str(history_root),"regime_labels_path":str(regime_labels),"created_at_utc":datetime.utcnow().replace(microsecond=0).isoformat()+"Z","analysis_start_date":analysis_start_date,"analysis_end_date":ed.isoformat(),"forward_horizons":hs,"full_event_count":int(len(events)),"primary_analysis_event_count":int(enriched["included_in_primary_analysis"].sum()),"diagnostics_count":int(len(diagnostics)),"chunk_count":len(chunks),"chunks_completed":sorted(chunks),"missing_regime_label_count":miss_reg,"missing_signal_daily_close_count":int(enriched["signal_daily_close"].isna().sum()),"missing_quote_volume_count":int(enriched["signal_day_quote_volume"].isna().sum()),"missing_median_quote_volume_30d_count":int(enriched["median_quote_volume_30d"].isna().sum()),"missing_median_quote_volume_90d_count":int(enriched["median_quote_volume_90d"].isna().sum()),"quote_volume_bucket_counts":quote_bucket_counts,"primary_quote_volume_bucket_counts":primary_quote_bucket_counts,"missing_forward_return_counts_by_horizon":missing_forward,"symbols_missing_1d_history_count":int(len(symbol_missing_history)),"events_missing_1d_history_count":int(event_missing_history_count),"negative_quote_volume_count":int((pd.to_numeric(enriched["signal_day_quote_volume"], errors="coerce") < 0).fillna(False).sum()),"nonfinite_numeric_values_replaced_with_null_count":int(nonfinite_replaced),"market_cap_available":False,"market_cap_reason":"not_available_point_in_time","liquidity_proxy_fields":["signal_day_quote_volume","median_quote_volume_30d","median_quote_volume_90d","quote_volume_bucket"],"forward_returns_are_labels_only":True,"no_lookahead_signal_inputs":True,"raw_event_count":raw_event_count,"signal_analysis_event_count":signal_analysis_event_count,"primary_signal_analysis_event_count":primary_signal_analysis_event_count,"duplicate_signal_event_count":duplicate_signal_event_count,"duplicate_signal_event_count_by_event_type":duplicate_signal_event_count_by_event_type,"analysis_event_priority_order":ANALYSIS_EVENT_PRIORITY_ORDER,"signal_analysis_dedup_key_fields":SIGNAL_ANALYSIS_DEDUP_KEY_FIELDS,"validation_status":"passed","validation_errors":[]}
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
