import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

SCRIPT = Path("scripts/backtest/analyze_replay_event_dataset.py")


def _base_df():
    return pd.DataFrame([
        {"scenario_id":"s1","replay_id":"r1","symbol":"A","as_of_daily_bar_id":"2026-01-01","included_in_primary_analysis":True,"included_in_signal_analysis":True,"historical_signal_bucket":"high","analysis_event_type":"first_confirmed_ready","event_type":"first_confirmed_ready","entry_pattern":"breakout","market_phase":"trend","quote_volume_bucket":"qv_1m_10m","btc_regime_label":"bull","forward_close_return_1d":0.1,"has_forward_1d":True,"forward_close_return_3d":0.2,"has_forward_3d":True,"forward_close_return_5d":np.nan,"has_forward_5d":True,"forward_close_return_10d":0.3,"has_forward_10d":True,"forward_close_return_20d":0.5,"has_forward_20d":True},
        {"scenario_id":"s1","replay_id":"r1","symbol":"B","as_of_daily_bar_id":"2026-01-02","included_in_primary_analysis":True,"included_in_signal_analysis":False,"historical_signal_bucket":"low","analysis_event_type":"first_late","event_type":"first_late","entry_pattern":"pullback","market_phase":"range","quote_volume_bucket":"qv_100k_1m","btc_regime_label":"bear","forward_close_return_1d":-0.1,"has_forward_1d":True,"forward_close_return_3d":np.inf,"has_forward_3d":True,"forward_close_return_5d":0.0,"has_forward_5d":True,"forward_close_return_10d":-0.2,"has_forward_10d":True,"forward_close_return_20d":-0.4,"has_forward_20d":True},
        {"scenario_id":"s1","replay_id":"r1","symbol":"C","as_of_daily_bar_id":"2026-01-03","included_in_primary_analysis":False,"included_in_signal_analysis":True,"historical_signal_bucket":"high","analysis_event_type":"first_early_ready","event_type":"first_early_ready","entry_pattern":"breakout","market_phase":"trend","quote_volume_bucket":"qv_10m_100m","btc_regime_label":"bull","forward_close_return_1d":0.0,"has_forward_1d":False,"forward_close_return_3d":0.1,"has_forward_3d":True,"forward_close_return_5d":0.2,"has_forward_5d":True,"forward_close_return_10d":0.2,"has_forward_10d":True,"forward_close_return_20d":0.1,"has_forward_20d":True},
    ])


def _run(tmp_path, df, *extra):
    ds = tmp_path / "d.parquet"
    df.to_parquet(ds, index=False)
    out = tmp_path / "out"
    cmd = [sys.executable, str(SCRIPT), "--dataset", str(ds), "--output-root", str(out), *extra]
    return subprocess.run(cmd, capture_output=True, text=True)


def test_missing_dataset_fails(tmp_path):
    out = subprocess.run([sys.executable, str(SCRIPT), "--dataset", str(tmp_path/"x.parquet"), "--output-root", str(tmp_path)], capture_output=True, text=True)
    assert out.returncode != 0

def test_missing_flag_fails(tmp_path):
    df = _base_df().drop(columns=["included_in_signal_analysis"])
    r = _run(tmp_path, df)
    assert r.returncode != 0

def test_missing_horizon_column_fails(tmp_path):
    df = _base_df().drop(columns=["forward_close_return_3d"])
    r = _run(tmp_path, df)
    assert r.returncode != 0

def test_scopes_and_outputs(tmp_path):
    df = _base_df()
    r = _run(tmp_path, df, "--analysis-scope", "primary_signal")
    assert r.returncode == 0
    out_dir = tmp_path / "out" / "s1" / "r1"
    seg = pd.read_csv(out_dir / "segment_returns.csv")
    assert (seg["scope"] == "primary_signal").all()
    assert "ALL" in set(seg["segment_group"])
    assert (out_dir / "backtest_summary.json").exists()
    assert (out_dir / "backtest_summary.md").exists()

    s = json.loads((out_dir / "backtest_summary.json").read_text())
    assert s["selected_row_count"] == 1

    assert "labels" in (out_dir / "backtest_summary.md").read_text()

@pytest.mark.parametrize("scope,expected", [("primary_raw",2),("full_signal",2),("full_raw",3)])
def test_scope_counts(tmp_path, scope, expected):
    r = _run(tmp_path, _base_df(), "--analysis-scope", scope)
    assert r.returncode == 0
    s = json.loads((tmp_path / "out" / "s1" / "r1" / "backtest_summary.json").read_text())
    assert s["selected_row_count"] == expected


def test_metrics_nonfinite_missing_and_min_count(tmp_path):
    r = _run(tmp_path, _base_df(), "--analysis-scope", "full_raw", "--min-count", "10")
    assert r.returncode == 0
    seg = pd.read_csv(tmp_path / "out" / "s1" / "r1" / "segment_returns.csv")
    all_row = seg[seg["segment_group"] == "ALL"].iloc[0]
    assert all_row["available_count_3d"] == 2
    assert all_row["missing_count_3d"] == 1
    assert bool(all_row["passes_min_count"]) is False
    assert "|" in str(seg[seg["segment_group"] == "historical_signal_bucket__x__entry_pattern"].iloc[0]["segment_key"])
