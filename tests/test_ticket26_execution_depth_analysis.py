from __future__ import annotations
import gzip, json, subprocess, sys, zipfile
from pathlib import Path

DATES=["2026-04-26","2026-04-27","2026-04-28","2026-04-29","2026-04-30","2026-05-01","2026-05-02","2026-05-03"]

def _mk_row(symbol:str,status:str,bucket:str="confirmed_candidates"):
    return {"symbol":symbol,"execution_status_raw":status,"execution_reason_raw":"depth_1pct_insufficient" if status=="fail" else None,"decision_bucket":bucket,"state_machine_state":"confirmed_ready","market_phase":"bull","market_phase_confidence":80.0,"state_confidence":70.0,"entry_pattern":"x","entry_pattern_score":60.0,"priority_score":50.0,"available_depth_usdt":500.0,"depth_threshold_1pct_usdt":1000.0}

def _write_zip(base:Path,d:str):
    zp=base/f"run_{d}.zip"
    inner=f"reports/runs/{d.replace('-','/')}/rid/symbol_diagnostics.jsonl.gz"
    payload="\n".join([json.dumps(_mk_row("AAAUSDT","fail","watchlist")),json.dumps(_mk_row("BBBUSDT","marginal","early_candidates"))]).encode()
    gz=gzip.compress(payload)
    with zipfile.ZipFile(zp,"w") as z: z.writestr(inner,gz)

def test_t26_outputs(tmp_path:Path)->None:
    inp=tmp_path/"in"; inp.mkdir()
    for d in DATES: _write_zip(inp,d)
    out=tmp_path/"out"
    subprocess.run([sys.executable,"scripts/analyze_execution_depth_shadow_live.py","--input-dir",str(inp),"--output-dir",str(out)],check=True)
    assert (out/"fail_cases_full.jsonl").exists()
    assert (out/"analysis_report.md").exists()
    fails=[json.loads(x) for x in (out/"fail_cases_full.jsonl").read_text().splitlines() if x.strip()]
    assert len(fails)==8
    assert fails[0]["recommended_position_factor"]==0.5

def test_missing_date_fails(tmp_path:Path)->None:
    inp=tmp_path/"in"; inp.mkdir()
    for d in DATES[:-1]: _write_zip(inp,d)
    p=subprocess.run([sys.executable,"scripts/analyze_execution_depth_shadow_live.py","--input-dir",str(inp)],capture_output=True,text=True)
    assert p.returncode!=0
    assert "Missing expected dates" in (p.stdout+p.stderr)
