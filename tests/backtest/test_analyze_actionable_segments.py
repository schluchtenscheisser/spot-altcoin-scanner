import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path("scripts/backtest/analyze_actionable_segments.py")


def _df():
    rows = []
    for i in range(16):
        rows.append({"included_in_primary_analysis": True, "included_in_signal_analysis": True, "historical_signal_bucket": "early_candidates", "entry_pattern": "base_reclaim", "btc_regime_label": "bull", "quote_volume_bucket": "qv_hi", "forward_close_return_1d": 1.0, "forward_close_return_3d": 1.0, "forward_close_return_5d": 0.0, "forward_close_return_10d": 0.0, "forward_close_return_20d": 0.0, "median_quote_volume_30d": 10.0, "median_quote_volume_90d": 20.0})
    rows.append({"included_in_primary_analysis": True, "included_in_signal_analysis": True, "historical_signal_bucket": "early_candidates", "entry_pattern": "", "btc_regime_label": "bear", "quote_volume_bucket": "qv_lo", "forward_close_return_1d": -1.0, "forward_close_return_3d": -1.0, "forward_close_return_5d": -3.0, "forward_close_return_10d": 0.0, "forward_close_return_20d": 0.0})
    rows.append({"included_in_primary_analysis": True, "included_in_signal_analysis": True, "historical_signal_bucket": "late_monitor", "entry_pattern": "ema_reclaim", "btc_regime_label": "bull", "quote_volume_bucket": "qv_hi", "forward_close_return_1d": 5.0, "forward_close_return_3d": 5.0, "forward_close_return_5d": 5.0, "forward_close_return_10d": 5.0, "forward_close_return_20d": 5.0})
    return pd.DataFrame(rows)


def test_outputs_and_classification(tmp_path):
    ds = tmp_path / "in.parquet"
    _df().to_parquet(ds, index=False)
    out = tmp_path / "o"
    r = subprocess.run([sys.executable, str(SCRIPT), "--input-events-parquet", str(ds), "--output-dir", str(out)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    seg = pd.read_csv(out / "actionable_segments.csv")
    assert (out / "actionable_segment_report.md").exists()
    assert (out / "actionable_segment_report.json").exists()
    assert set(seg["classification"]) >= {"Tier A", "Exclude", "Diagnostic"}

    s = json.loads((out / "actionable_segment_report.json").read_text())
    assert s["row_counts"]["primary_actionable_rows"] == 16
    assert s["classification_counts"]["Tier A"] == 1


def test_missing_required_column_fails(tmp_path):
    df = _df().drop(columns=["btc_regime_label"])
    ds = tmp_path / "in.parquet"
    df.to_parquet(ds, index=False)
    out = tmp_path / "o"
    r = subprocess.run([sys.executable, str(SCRIPT), "--input-events-parquet", str(ds), "--output-dir", str(out)], capture_output=True, text=True)
    assert r.returncode != 0


def test_missing_optional_liquidity_column_warns(tmp_path):
    df = _df().drop(columns=["median_quote_volume_30d", "median_quote_volume_90d"])
    ds = tmp_path / "in.parquet"
    df.to_parquet(ds, index=False)
    out = tmp_path / "o"
    r = subprocess.run([sys.executable, str(SCRIPT), "--input-events-parquet", str(ds), "--output-dir", str(out)], capture_output=True, text=True)
    assert r.returncode == 0
    s = json.loads((out / "actionable_segment_report.json").read_text())
    assert any("missing optional column" in w for w in s["warnings"])
    seg = pd.read_csv(out / "actionable_segments.csv")
    assert seg["median_quote_volume_30d"].isna().all()
