import gzip, json
from pathlib import Path
import pandas as pd
import pytest
from scripts.backtest.build_replay_event_dataset import build_dataset


def _write_jsonl_gz(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")


def _fixture(tmp_path: Path):
    run=tmp_path/"run"; (run/"chunks"/"2025-05").mkdir(parents=True); (run/"chunks"/"2025-06").mkdir(parents=True)
    ev1=pd.DataFrame([{"scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-05-20","event_type":"E","signal_daily_close":1.0}])
    ev2=pd.DataFrame([{"scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-20","event_type":"E","signal_daily_close":1.2}])
    ev1.to_parquet(run/"chunks"/"2025-05"/"replay_event_candidates.parquet",index=False)
    ev2.to_parquet(run/"chunks"/"2025-06"/"replay_event_candidates.parquet",index=False)
    (run/"chunks"/"2025-05"/"chunk_manifest.json").write_text("{}")
    (run/"chunks"/"2025-06"/"chunk_manifest.json").write_text("{}")
    d1={"scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-05-20","execution_evaluation_status":"not_evaluated_historical_ohlcv_only"}
    d2={"scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-20","execution_evaluation_status":"not_evaluated_historical_ohlcv_only"}
    _write_jsonl_gz(run/"chunks"/"2025-05"/"replay_symbol_diagnostics.jsonl.gz",[d1])
    _write_jsonl_gz(run/"chunks"/"2025-06"/"replay_symbol_diagnostics.jsonl.gz",[d2])
    manifest={"is_complete":True,"replay_days_completed":2,"replay_days_total":2,"chunks_completed":["2025-05","2025-06"],"signal_events_so_far":2,"signal_events_total":1,"diagnostics_so_far":2,"scenario_id":"s","replay_id":"r","evaluation_end_date":"2025-06-30"}
    (run/"replay_manifest.json").write_text(json.dumps(manifest))
    hist=tmp_path/"hist"; hist.mkdir()
    regime=tmp_path/"reg.json"; regime.write_text(json.dumps([{"iso_week":"2025-W21","regime_label":"neutral"}]))
    out=tmp_path/"out"
    return run,hist,regime,out


def test_merge_and_analysis_flags(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    build_dataset(run,hist,regime,out,analysis_start_date="2025-06-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    assert len(enr)==2
    assert enr.iloc[0]["as_of_daily_bar_id"]=="2025-05-20"
    assert enr["included_in_primary_analysis"].tolist()==[False,True]


def test_invalid_horizons_fail(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    with pytest.raises(ValueError):
        build_dataset(run,hist,regime,out,forward_horizons="1,0,3")
