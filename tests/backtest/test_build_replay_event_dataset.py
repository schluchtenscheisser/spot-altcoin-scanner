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

def test_missing_diagnostics_match_fails(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    # break one diagnostics key while keeping diagnostics row count plausible
    _write_jsonl_gz(run/"chunks"/"2025-06"/"replay_symbol_diagnostics.jsonl.gz", [{
        "scenario_id":"s","replay_id":"r","symbol":"OTHERUSDT","as_of_daily_bar_id":"2025-06-20",
        "execution_evaluation_status":"not_evaluated_historical_ohlcv_only"
    }])
    with pytest.raises(ValueError, match="events without matching diagnostics rows"):
        build_dataset(run,hist,regime,out,analysis_start_date="2025-06-01")


def test_regime_zero_values_and_secondary_fallback(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps([
        {"iso_week":"2025-W21","regime_label":"neutral","ret_30d":0.0,"realized_vol_30d":0.0,"btc_30d_return":None,"btc_30d_realized_vol":None},
        {"iso_week":"2025-W25","regime_label":"risk_on","ret_30d":None,"realized_vol_30d":None,"btc_30d_return":0.0,"btc_30d_realized_vol":0.0},
    ]))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    may = enr.loc[enr["as_of_daily_bar_id"]=="2025-05-20"].iloc[0]
    jun = enr.loc[enr["as_of_daily_bar_id"]=="2025-06-20"].iloc[0]
    assert may["btc_30d_return"] == 0.0
    assert may["btc_30d_realized_vol"] == 0.0
    assert jun["btc_30d_return"] == 0.0
    assert jun["btc_30d_realized_vol"] == 0.0


def test_regime_labels_schema_week_start_date_and_metrics(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({
        "created_at_utc": "2026-01-01T00:00:00Z",
        "labels": [
            {"week_start_date":"2025-05-19","regime_label":"Sideways","btc_30d_return_pct":1.25,"btc_30d_realized_vol_annualized_pct":12.5},
            {"week_start_date":"2025-06-16","regime_label":"RiskOn","btc_30d_return_pct":2.5,"btc_30d_realized_vol_annualized_pct":22.5},
        ],
        "status": "frozen",
    }))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    may = enr.loc[enr["as_of_daily_bar_id"]=="2025-05-20"].iloc[0]
    jun = enr.loc[enr["as_of_daily_bar_id"]=="2025-06-20"].iloc[0]
    assert may["btc_regime_week"] == "2025-W21"
    assert may["btc_30d_return"] == 1.25
    assert may["btc_30d_realized_vol"] == 12.5
    assert jun["btc_regime_week"] == "2025-W25"
    assert jun["btc_30d_return"] == 2.5
    assert jun["btc_30d_realized_vol"] == 22.5


def test_regime_labels_schema_preserves_zero_values(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"week_start_date":"2025-05-19","regime_label":"Sideways","btc_30d_return_pct":0.0,"btc_30d_realized_vol_annualized_pct":0.0},
        {"week_start_date":"2025-06-16","regime_label":"RiskOn","btc_30d_return_pct":0.0,"btc_30d_realized_vol_annualized_pct":0.0},
    ]}))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    assert enr["btc_30d_return"].tolist() == [0.0, 0.0]
    assert enr["btc_30d_realized_vol"].tolist() == [0.0, 0.0]


def test_regime_duplicate_derived_iso_week_fails_fast(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"week_start_date":"2025-05-19","regime_label":"A"},
        {"week_start_date":"2025-05-20","regime_label":"B"},
    ]}))
    with pytest.raises(ValueError, match="duplicate regime week key"):
        build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")


def test_regime_does_not_use_as_of_daily_bar_id_as_week_key(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"as_of_daily_bar_id":"BTCUSDT:1d:2025-02-09T00:00:00Z","regime_label":"Sideways"}
    ]}))
    with pytest.raises(ValueError, match="cannot interpret regime schema: expected top-level list, rows, or labels with non-empty iso_week/week/btc_regime_week or valid week_start_date"):
        build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")


def test_regime_empty_iso_week_falls_back_to_week_start_date(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"iso_week":"","week_start_date":"2025-05-19","regime_label":"Sideways"},
        {"week_start_date":"2025-06-16","regime_label":"RiskOn"},
    ]}))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    assert enr.loc[enr["as_of_daily_bar_id"]=="2025-05-20","btc_regime_label"].iloc[0] == "Sideways"


def test_regime_whitespace_week_falls_back_to_week_start_date(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"week":"   ","week_start_date":"2025-05-19","regime_label":"Sideways"},
        {"week_start_date":"2025-06-16","regime_label":"RiskOn"},
    ]}))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    assert enr.loc[enr["as_of_daily_bar_id"]=="2025-05-20","btc_regime_label"].iloc[0] == "Sideways"


def test_regime_malformed_week_start_date_is_skipped(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"week_start_date":"not-a-date","regime_label":"BadRow"},
        {"week_start_date":"2025-06-16","regime_label":"RiskOn"},
    ]}))
    build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")
    enr=pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    jun = enr.loc[enr["as_of_daily_bar_id"]=="2025-06-20"].iloc[0]
    assert jun["btc_regime_label"] == "RiskOn"


def test_regime_all_non_interpretable_rows_fail_with_clear_error(tmp_path: Path):
    run,hist,regime,out=_fixture(tmp_path)
    regime.write_text(json.dumps({"labels":[
        {"iso_week":" ","week_start_date":"not-a-date","regime_label":"A"},
        {"week":"", "regime_label":"B"},
        {"btc_regime_week":"   ", "week_start_date":"", "regime_label":"C"},
    ]}))
    with pytest.raises(ValueError, match="cannot interpret regime schema: expected top-level list, rows, or labels with non-empty iso_week/week/btc_regime_week or valid week_start_date"):
        build_dataset(run,hist,regime,out,analysis_start_date="2025-05-01")


def test_mixed_setup_cycle_id_normalized_for_parquet_write(tmp_path: Path):
    run, hist, regime, out = _fixture(tmp_path)
    ev1 = pd.DataFrame([{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-05-20",
        "event_type":"E","signal_daily_close":1.0,"market_phase_confidence":0.8,"entry_pattern_score":0.5,
        "forward_close_return_1d":0.01,
    }])
    ev2 = pd.DataFrame([{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-20",
        "event_type":"E","signal_daily_close":1.2,"market_phase_confidence":0.6,"entry_pattern_score":0.7,
        "forward_close_return_1d":0.02,
    }])
    ev3 = pd.DataFrame([{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-21",
        "event_type":"E","signal_daily_close":1.4,"market_phase_confidence":0.9,"entry_pattern_score":0.2,
        "forward_close_return_1d":0.03,
    }])
    (run/"chunks"/"2025-07").mkdir(parents=True)
    ev1.to_parquet(run/"chunks"/"2025-05"/"replay_event_candidates.parquet",index=False)
    ev2.to_parquet(run/"chunks"/"2025-06"/"replay_event_candidates.parquet",index=False)
    ev3.to_parquet(run/"chunks"/"2025-07"/"replay_event_candidates.parquet",index=False)
    (run/"chunks"/"2025-07"/"chunk_manifest.json").write_text("{}")
    _write_jsonl_gz(run/"chunks"/"2025-05"/"replay_symbol_diagnostics.jsonl.gz",[{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-05-20",
        "setup_cycle_id":5,"execution_evaluation_status":"not_evaluated_historical_ohlcv_only"
    }])
    _write_jsonl_gz(run/"chunks"/"2025-06"/"replay_symbol_diagnostics.jsonl.gz",[{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-20",
        "setup_cycle_id":"6","execution_evaluation_status":"not_evaluated_historical_ohlcv_only"
    }])
    _write_jsonl_gz(run/"chunks"/"2025-07"/"replay_symbol_diagnostics.jsonl.gz",[{
        "scenario_id":"s","replay_id":"r","symbol":"AAAUSDT","as_of_daily_bar_id":"2025-06-21",
        "setup_cycle_id":None,"execution_evaluation_status":"not_evaluated_historical_ohlcv_only"
    }])
    manifest={"is_complete":True,"replay_days_completed":3,"replay_days_total":3,"chunks_completed":["2025-05","2025-06","2025-07"],"signal_events_so_far":3,"signal_events_total":1,"diagnostics_so_far":3,"scenario_id":"s","replay_id":"r","evaluation_end_date":"2025-06-30"}
    (run/"replay_manifest.json").write_text(json.dumps(manifest))
    regime.write_text(json.dumps([{"iso_week":"2025-W21","regime_label":"neutral"}, {"iso_week":"2025-W25","regime_label":"risk_on"}]))

    build_dataset(run, hist, regime, out, analysis_start_date="2025-05-01")

    diag = pd.read_parquet(out/"s"/"r"/"all_replay_symbol_diagnostics.parquet")
    assert diag["setup_cycle_id"].iloc[0] == "5"
    assert diag["setup_cycle_id"].iloc[1] == "6"
    assert pd.isna(diag["setup_cycle_id"].iloc[2])
    assert "None" not in diag["setup_cycle_id"].dropna().tolist()
    assert "nan" not in diag["setup_cycle_id"].dropna().tolist()

    enr = pd.read_parquet(out/"s"/"r"/"enriched_replay_events.parquet")
    assert pd.api.types.is_numeric_dtype(enr["signal_daily_close"])
    assert pd.api.types.is_numeric_dtype(enr["market_phase_confidence"])
    assert pd.api.types.is_numeric_dtype(enr["entry_pattern_score"])
    events = pd.read_parquet(out/"s"/"r"/"all_replay_event_candidates.parquet")
    if "forward_close_return_1d" in events.columns:
        assert pd.api.types.is_numeric_dtype(events["forward_close_return_1d"])
