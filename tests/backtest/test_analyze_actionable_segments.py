import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

SCRIPT = Path("scripts/backtest/analyze_actionable_segments.py")


def _run(tmp_path, df):
    ds = tmp_path / "in.parquet"
    df.to_parquet(ds, index=False)
    out = tmp_path / "o"
    r = subprocess.run([sys.executable, str(SCRIPT), "--input-events-parquet", str(ds), "--output-dir", str(out)], capture_output=True, text=True)
    return r, out


def _base_row():
    return {
        "included_in_primary_analysis": True,
        "included_in_signal_analysis": True,
        "historical_signal_bucket": "early_candidates",
        "entry_pattern": "base_reclaim",
        "btc_regime_label": "bull",
        "quote_volume_bucket": "qv_hi",
        "forward_close_return_1d": 1.0,
        "forward_close_return_3d": 1.0,
        "forward_close_return_5d": 0.0,
        "forward_close_return_10d": 0.0,
        "forward_close_return_20d": 0.0,
        "median_quote_volume_30d": 10.0,
        "median_quote_volume_90d": 20.0,
    }


def test_outputs_and_classification(tmp_path):
    rows = [_base_row() for _ in range(16)]
    rows.append({**_base_row(), "entry_pattern": "", "forward_close_return_1d": -1.0, "forward_close_return_3d": -1.0, "forward_close_return_5d": -3.0})
    rows.append({**_base_row(), "historical_signal_bucket": "late_monitor", "entry_pattern": "ema_reclaim", "forward_close_return_1d": 5.0, "forward_close_return_3d": 5.0, "forward_close_return_5d": 5.0})

    r, out = _run(tmp_path, pd.DataFrame(rows))
    assert r.returncode == 0, r.stderr
    seg = pd.read_csv(out / "actionable_segments.csv")
    assert set(seg["classification"]) >= {"Tier A", "Exclude", "Diagnostic"}
    s = json.loads((out / "actionable_segment_report.json").read_text())
    assert s["classification_counts"]["Tier A"] == 1


def test_zero_scope_writes_all_outputs_and_empty_sections(tmp_path):
    rows = [{**_base_row(), "included_in_primary_analysis": False, "included_in_signal_analysis": False, "historical_signal_bucket": "other"} for _ in range(3)]
    r, out = _run(tmp_path, pd.DataFrame(rows))
    assert r.returncode == 0, r.stderr

    expected = [
        "actionable_segment_report.md",
        "actionable_segment_report.json",
        "actionable_segments.csv",
        "actionable_segments.parquet",
        "actionable_segment_splits.csv",
        "actionable_segment_splits.parquet",
    ]
    for name in expected:
        assert (out / name).exists(), name

    seg = pd.read_csv(out / "actionable_segments.csv")
    splits = pd.read_csv(out / "actionable_segment_splits.csv")
    assert list(seg.columns) == [
        "historical_signal_bucket", "entry_pattern", "segment_label", "classification", "classification_warning", "classification_sort_order", "count",
        "forward_return_1d_mean_pct", "forward_return_1d_median_pct", "forward_return_1d_win_rate_pct", "forward_return_1d_non_null_count",
        "forward_return_3d_mean_pct", "forward_return_3d_median_pct", "forward_return_3d_win_rate_pct", "forward_return_3d_non_null_count",
        "forward_return_5d_mean_pct", "forward_return_5d_median_pct", "forward_return_5d_win_rate_pct", "forward_return_5d_non_null_count",
        "forward_return_10d_mean_pct", "forward_return_10d_median_pct", "forward_return_10d_win_rate_pct", "forward_return_10d_non_null_count",
        "forward_return_20d_mean_pct", "forward_return_20d_median_pct", "forward_return_20d_win_rate_pct", "forward_return_20d_non_null_count",
        "median_quote_volume_30d", "median_quote_volume_90d", "low_sample", "sample_warning", "warning_5d_weak", "warning_5d_severe",
    ]
    assert len(seg) == 0
    assert len(splits) == 0

    md = (out / "actionable_segment_report.md").read_text()
    assert "No Tier A segments found under the current thresholds." in md
    assert "No Tier B segments found under the current thresholds." in md
    assert "No Diagnostic segments found under the current scope." in md


def test_non_evaluable_segment_is_unclassified(tmp_path):
    rows = []
    for _ in range(12):
        rows.append({**_base_row(), "forward_close_return_1d": np.nan, "forward_close_return_3d": np.inf, "forward_close_return_5d": 0.0})
    r, out = _run(tmp_path, pd.DataFrame(rows))
    assert r.returncode == 0, r.stderr
    seg = pd.read_csv(out / "actionable_segments.csv")
    assert len(seg) == 1
    assert seg.iloc[0]["classification"] == "Unclassified"
    assert seg.iloc[0]["classification_warning"] == "non_evaluable_return_metrics"


def test_missing_required_column_fails(tmp_path):
    r, _ = _run(tmp_path, pd.DataFrame([{k: v for k, v in _base_row().items() if k != "btc_regime_label"}]))
    assert r.returncode != 0


def test_missing_optional_liquidity_column_warns(tmp_path):
    df = pd.DataFrame([{k: v for k, v in _base_row().items() if k not in {"median_quote_volume_30d", "median_quote_volume_90d"}} for _ in range(16)])
    r, out = _run(tmp_path, df)
    assert r.returncode == 0
    s = json.loads((out / "actionable_segment_report.json").read_text())
    assert any("missing optional column" in w for w in s["warnings"])
