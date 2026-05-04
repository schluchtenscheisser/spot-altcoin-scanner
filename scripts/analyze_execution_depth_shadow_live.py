#!/usr/bin/env python3
from __future__ import annotations
import argparse, gzip, json, math, zipfile
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Any

DATES=["2026-04-26","2026-04-27","2026-04-28","2026-04-29","2026-04-30","2026-05-01","2026-05-02","2026-05-03"]
TOP_BUCKETS={"confirmed_candidates","early_candidates"}


def _finite(v: Any)->bool:
    return isinstance(v,(int,float)) and math.isfinite(float(v))

def _pf(phase:float,state:float,entry:float,grade:float)->float:
    return 0.30*phase+0.35*state+0.20*entry+0.15*grade

def _bucket(state: str, exec_status:str)->str:
    if state=="confirmed_ready":
        return "confirmed_candidates" if exec_status!="fail" else "late_monitor"
    if state=="early_ready":
        return "early_candidates" if exec_status!="fail" else "watchlist"
    if state=="watch":
        return "watchlist"
    return "late_monitor"

def _find_archives(inp:Path)->dict[str,tuple[Path,str]]:
    found={}
    for zp in sorted(inp.glob("*.zip")):
        with zipfile.ZipFile(zp) as z:
            for name in z.namelist():
                if not name.endswith("symbol_diagnostics.jsonl.gz"): continue
                for d in DATES:
                    if f"/{d.replace('-','/')}/" in name:
                        found[d]=(zp,name)
    miss=[d for d in DATES if d not in found]
    if miss: raise ValueError(f"Missing expected dates: {', '.join(miss)}")
    return found

def _read_diag(zip_path:Path, member:str)->list[dict[str,Any]]:
    with zipfile.ZipFile(zip_path) as z:
        b=z.read(member)
    lines=gzip.decompress(b).decode("utf-8").splitlines()
    return [json.loads(x) for x in lines if x.strip()]

def main()->None:
    ap=argparse.ArgumentParser()
    ap.add_argument("--input-dir", required=True)
    ap.add_argument("--output-dir", default="reports/aux/execution_depth_analysis/2026-04-26_to_2026-05-03")
    a=ap.parse_args()
    mapping=_find_archives(Path(a.input_dir))
    out=Path(a.output_dir); out.mkdir(parents=True,exist_ok=True)
    fail=[]; marg=[]; spread_fields=set()
    for d,(zp,member) in mapping.items():
        for r in _read_diag(zp,member):
            for k in r.keys():
                if "spread" in k.lower() or "slippage" in k.lower(): spread_fields.add(k)
            st=r.get("execution_status_raw")
            if st=="fail":
                p,m,e=r.get("market_phase_confidence"),r.get("state_confidence"),r.get("entry_pattern_score")
                replay=all(_finite(x) for x in (p,m,e))
                ratio=r.get("available_depth_usdt")/r.get("depth_threshold_1pct_usdt") if _finite(r.get("available_depth_usdt")) and _finite(r.get("depth_threshold_1pct_usdt")) and r.get("depth_threshold_1pct_usdt") else None
                rec=None
                if ratio is not None:
                    rec=1.0 if ratio>=1 else 0.75 if ratio>=0.75 else 0.5 if ratio>=0.5 else 0.25 if ratio>=0.25 else 0.0
                bcf=_bucket(r.get("state_machine_state",""),"marginal") if replay else None
                row={"symbol":r.get("symbol"),"date":d,"replay_derivable":replay,"decision_bucket_actual":r.get("decision_bucket"),"decision_bucket_without_execution_block":bcf,"structurally_actionable":bcf in TOP_BUCKETS if bcf else False,"state_machine_state":r.get("state_machine_state"),"market_phase":r.get("market_phase"),"market_phase_confidence":p,"entry_pattern":r.get("entry_pattern"),"entry_pattern_score":e,"priority_score_actual":r.get("priority_score"),"priority_score_counterfactual_marginal":_pf(p,m,e,40.0) if replay else None,"execution_status_raw":"fail","execution_reason_raw":r.get("execution_reason_raw"),"available_depth_usdt":r.get("available_depth_usdt"),"depth_threshold_1pct_usdt":r.get("depth_threshold_1pct_usdt"),"available_depth_ratio":ratio,"clearing_notional_fraction":ratio,"recommended_position_factor":rec,"tradable_at_75pct": None if ratio is None else ratio>=0.75,"tradable_at_50pct": None if ratio is None else ratio>=0.5,"tradable_at_25pct": None if ratio is None else ratio>=0.25,"depth_ratio_derivable": ratio is not None}
                fail.append(row)
            elif st=="marginal" and r.get("decision_bucket") in TOP_BUCKETS:
                p,s,e=r.get("market_phase_confidence"),r.get("state_confidence"),r.get("entry_pattern_score")
                if not all(_finite(x) for x in (p,s,e)): continue
                row={"symbol":r.get("symbol"),"date":d,"decision_bucket":r.get("decision_bucket"),"state_machine_state":r.get("state_machine_state"),"market_phase":r.get("market_phase"),"market_phase_confidence":p,"state_confidence":s,"entry_pattern":r.get("entry_pattern"),"entry_pattern_score":e}
                scores={40:_pf(p,s,e,40),50:_pf(p,s,e,50),60:_pf(p,s,e,60),75:_pf(p,s,e,75),100:_pf(p,s,e,100)}
                row.update({"priority_score_actual":scores[40],"priority_score_cf_50":scores[50],"priority_score_cf_60":scores[60],"priority_score_cf_75":scores[75],"priority_score_cf_100":scores[100]})
                marg.append(row)
    # ranks
    by_day_bucket=defaultdict(list)
    for r in marg: by_day_bucket[(r["date"],r["decision_bucket"])].append(r)
    for grp in by_day_bucket.values():
        for g,skey in (("actual","priority_score_actual"),("cf_50","priority_score_cf_50"),("cf_60","priority_score_cf_60"),("cf_75","priority_score_cf_75"),("cf_100","priority_score_cf_100")):
            sorted_grp=sorted(grp,key=lambda x:(-x[skey],x["symbol"] or ""))
            for i,r in enumerate(sorted_grp,1): r[f"rank_{g}"]=i
        for r in grp: r["rank_displacement_cf_100"]=r["rank_cf_100"]-r["rank_actual"]

    (out/"fail_cases_full.jsonl").write_text("\n".join(json.dumps(x) for x in fail)+"\n",encoding="utf-8")
    (out/"marginal_candidate_cases_full.jsonl").write_text("\n".join(json.dumps(x) for x in marg)+"\n",encoding="utf-8")
    (out/"summary_fail_depth_counterfactual.md").write_text(f"# Summary Fail\n\nTotal fail: {len(fail)}\n",encoding="utf-8")
    (out/"summary_marginal_priority_impact.md").write_text(f"# Summary Marginal\n\nTotal marginal top buckets: {len(marg)}\n",encoding="utf-8")
    (out/"analysis_report.md").write_text("# T26 Analysis Report\n\n## Spread/slippage availability\n\nFields found: "+(", ".join(sorted(spread_fields)) if spread_fields else "none")+"\n\n## Limitations\n\n- Profitability is not assessed.\n- Depth-to-notional scaling assumption is linear.\n- Single-metric counterfactual holds other metrics constant.\n- Pre-T24 data.\n- Preliminary summary stats are superseded by this output.\n",encoding="utf-8")

if __name__=="__main__":
    main()
