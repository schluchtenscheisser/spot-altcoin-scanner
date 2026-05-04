from __future__ import annotations
import gzip, json, subprocess, sys, zipfile
from pathlib import Path

DATES=["2026-04-26","2026-04-27","2026-04-28","2026-04-29","2026-04-30","2026-05-01","2026-05-02","2026-05-03"]

def _zip_for_day(base:Path, d:str, rows:list[dict]):
    zp=base/f"run_{d}.zip"
    inner=f"reports/runs/{d.replace('-', '/')}/rid/symbol_diagnostics.jsonl.gz"
    payload="\n".join(json.dumps(r) for r in rows).encode()
    with zipfile.ZipFile(zp,"w") as z: z.writestr(inner,gzip.compress(payload))

def _row(sym,status,bucket="early_candidates",state="early_ready",sc=70.0,ep="breakout",ps=50.0):
    return {"symbol":sym,"execution_status_raw":status,"decision_bucket":bucket,"state_machine_state":state,"market_phase":"bull","market_phase_confidence":80.0,"state_confidence":sc,"entry_pattern":ep,"entry_pattern_score":60.0,"priority_score":ps,"available_depth_usdt":500.0,"depth_threshold_1pct_usdt":1000.0}

def _run(inp:Path,out:Path):
    subprocess.run([sys.executable,"scripts/analyze_execution_depth_shadow_live.py","--input-dir",str(inp),"--output-dir",str(out)],check=True)

def test_replay_gates_and_watch_preserved_and_ranking_population(tmp_path:Path):
    inp=tmp_path/"in"; inp.mkdir(); out=tmp_path/"out"
    base_rows=[
      _row("FAIL_EARLY_OK","fail",bucket="watchlist",state="early_ready",sc=70,ep="breakout"),
      _row("FAIL_EARLY_NONE","fail",bucket="watchlist",state="early_ready",sc=70,ep="none"),
      _row("FAIL_EARLY_LOW","fail",bucket="watchlist",state="early_ready",sc=50,ep="breakout"),
      _row("FAIL_CONF_OK","fail",bucket="confirmed_candidates",state="confirmed_ready",sc=70,ep="breakout"),
      _row("FAIL_CONF_LOW","fail",bucket="confirmed_candidates",state="confirmed_ready",sc=60,ep="breakout"),
      _row("FAIL_WATCH","fail",bucket="watchlist",state="watch",sc=60,ep="none"),
      _row("MARG","marginal",bucket="early_candidates",state="early_ready",ps=40),
      _row("DIRECT1","direct_ok",bucket="early_candidates",state="early_ready",ps=60),
      _row("TRANCHE1","tranche_ok",bucket="early_candidates",state="early_ready",ps=50),
      _row("MARG2","marginal",bucket="early_candidates",state="early_ready",ps=40),
    ]
    for d in DATES: _zip_for_day(inp,d,base_rows)
    _run(inp,out)

    fails=[json.loads(x) for x in (out/"fail_cases_full.jsonl").read_text().splitlines() if x.strip()]
    b={r["symbol"]:r["decision_bucket_without_execution_block"] for r in fails}
    assert b["FAIL_EARLY_OK"]=="early_candidates"
    assert b["FAIL_EARLY_NONE"]!="early_candidates"
    assert b["FAIL_EARLY_LOW"]!="early_candidates"
    assert b["FAIL_CONF_OK"]=="confirmed_candidates"
    assert b["FAIL_CONF_LOW"]!="confirmed_candidates"
    assert b["FAIL_WATCH"]=="watchlist"

    marg=[json.loads(x) for x in (out/"marginal_candidate_cases_full.jsonl").read_text().splitlines() if x.strip()]
    m=[r for r in marg if r["symbol"]=="MARG"][0]
    assert m["rank_actual"]==3  # direct1(60), tranche1(50), marg(40) tie->MARG before MARG2
    assert m["rank_cf_100"]==1
    m2=[r for r in marg if r["symbol"]=="MARG2"][0]
    assert m2["rank_actual"]==4

def test_output_path_safety_and_missing_date(tmp_path:Path):
    inp=tmp_path/"in"; inp.mkdir()
    for d in DATES[:-1]: _zip_for_day(inp,d,[_row("A","fail")])
    p=subprocess.run([sys.executable,"scripts/analyze_execution_depth_shadow_live.py","--input-dir",str(inp),"--output-dir","reports/runs/bad"],capture_output=True,text=True)
    assert p.returncode!=0 and "Forbidden output path" in (p.stdout+p.stderr)
    assert not Path("reports/runs/bad/fail_cases_full.jsonl").exists()

    # traversal normalized rejection
    p2=subprocess.run([sys.executable,"scripts/analyze_execution_depth_shadow_live.py","--input-dir",str(inp),"--output-dir","reports/aux/../runs/evil"],capture_output=True,text=True)
    assert p2.returncode!=0 and "Forbidden output path" in (p2.stdout+p2.stderr)
