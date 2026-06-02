from __future__ import annotations
import gzip, json, math, zipfile
from pathlib import Path
import pytest
from scripts.analyze_t30_v2_segment_selection import analyze, apply_slippage, basket_filters, classify_run, extract_record, segments, validate_thresholds, write_json

def rec(**kw):
 d={"symbol":"AAAUSDT","schema_version":"ir1.5","is_operational_trade_candidate":True,"candidate_excluded":False,"execution_size_class":"full","execution_status_raw":"direct_ok","estimated_slippage_bps":31,"decision":{"decision_bucket":"confirmed_candidates","priority_score":70},"entry_location":{"entry_location_status":"fresh_entry","entry_action_hint":"acceptable_if_strategy_allows"}}
 d.update(kw); return d

def test_schema_detection_semantic_and_fallback():
 assert classify_run([rec(schema_version="ir1.5")])[0]
 assert classify_run([rec(schema_version="ir1.4")])[:2] == (False,"schema_pre_ir1.5")
 assert classify_run([rec(schema_version="ir1.6")])[0]
 assert classify_run([{"schema_version":"ir1.6"}])[:2] == (False,"missing_required_fields")
 assert classify_run([{"is_operational_trade_candidate":False}])[:2] == (True,"operational_field_fallback")
 assert not classify_run([{}])[0]

def test_nested_entry_location_ignores_root():
 x=extract_record(rec(entry_location_status="WRONG"),"r")
 assert x["entry_location_status"] == "fresh_entry"
 x=extract_record(rec(entry_location=None,entry_location_status="WRONG"),"r")
 assert (x["entry_location_status"],x["entry_action_hint"]) == ("not_evaluable","not_evaluable")

def test_tranche_visibility_segment_and_baskets():
 tranche=extract_record(rec(execution_status_raw="tranche_ok"),"r")
 assert not segments()["S1"](tranche) and not segments()["S2"](tranche) and not segments()["S7"](tranche)
 assert segments()["S8"](tranche)
 assert all(f(tranche) for f in basket_filters({"A":65,"B":60,"C":55}).values())

def test_s6_excludes_buy_now_but_s9_includes_and_basket_c_outside_segments():
 buy=extract_record(rec(decision={"decision_bucket":"early_candidates","priority_score":70},entry_location={"entry_location_status":"fresh_entry","entry_action_hint":"buy_now_candidate"}),"r")
 assert not segments()["S6"](buy) and segments()["S9"](buy)
 outside=extract_record(rec(decision={"decision_bucket":"early_candidates","priority_score":70},execution_size_class="reduced_50"),"r")
 assert basket_filters({"A":65,"B":60,"C":55})["C"](outside)
 assert not any(segments()[s](outside) for s in ["S1","S2","S3","S4","S5","S6","S7"])

def test_slippage_and_validation_and_json_finiteness(tmp_path):
 assert apply_slippage(10,31)==pytest.approx((9.69,True)); assert apply_slippage(10,None)==(10,False)
 with pytest.raises(ValueError): validate_thresholds({"A":math.nan})
 with pytest.raises(ValueError): validate_thresholds({"A":101})
 p=tmp_path/"x.json"; write_json(p,{"bad":[math.nan,math.inf,-math.inf]}); assert json.loads(p.read_text())=={"bad":[None,None,None]}

def write_zip(path:Path, run_id:str, records:list[dict]):
 raw=gzip.compress("\n".join(json.dumps(x) for x in records).encode())
 with zipfile.ZipFile(path,"w") as z:
  base=f"reports/runs/2026/06/01/{run_id}"; z.writestr(f"{base}/symbol_diagnostics.jsonl.gz",raw); z.writestr(f"{base}/report.json",json.dumps({"counts_by_bucket":{"confirmed_candidates":len(records),"early_candidates":0}}))

def test_synthetic_zip_missing_ohlcv_outputs_and_minimum_gate(tmp_path):
 z=tmp_path/".local_data/shadow_live_runs"; z.mkdir(parents=True)
 write_zip(z/"runs.zip","r0",[rec(execution_status_raw="tranche_ok")])
 with pytest.raises(RuntimeError,match="T30-v2 requires at least 20 ir1.5\\+ runs. Found: 1"):
  analyze(tmp_path,input_zip_dir=Path(".local_data/shadow_live_runs"))
 for n in range(1,20): write_zip(z/f"r{n}.zip",f"r{n}",[rec(symbol=f"A{n}USDT",execution_status_raw="tranche_ok")])
 artifacts=analyze(tmp_path,input_zip_dir=Path(".local_data/shadow_live_runs"))
 assert artifacts["segment_summary.json"]["S8"]["n_total_records"]==20
 assert artifacts["basket_summary.json"]["applied_config"]["PRIORITY_THRESHOLD_A"]==65
 assert artifacts["basket_summary.json"]["baskets"]["A"]["execution_status_raw_distribution"]=={"tranche_ok":20}
 assert artifacts["mfe_mae_summary.json"]=={"mfe_mae_available":False}
 assert "OHLCV history absent or incomplete" in (tmp_path/"reports/aux/t30_v2/decision_support.md").read_text()
 assert "OHLCV history absent or incomplete" in (tmp_path/"reports/aux/t30_v2/run_coverage.md").read_text()
