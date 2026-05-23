from __future__ import annotations
import json
import sqlite3
from datetime import date
from pathlib import Path
import pandas as pd
import pytest

from scanner.evaluation.historical_replay.replay_runner import run_replay
from scanner.evaluation.historical_replay.scenario import load_scenario
from tests.replay.test_historical_replay_runner import _write_hist, _scenario


def _scenario_long(tmp: Path, history: Path) -> Path:
    p = tmp / "scenario_long.yml"
    p.write_text(f"""
scenario_id: s1
history_dataset_ref: {history.as_posix()}
history_manifest_ref: hm
universe_manifest_ref: um
evaluation: {{start_date: 2025-01-01, end_date: 2025-01-31}}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {{mode: disabled_historical_ohlcv_only}}
scanner_config: {{ref: config/config.yml, hash: abc}}
regime_labels: {{method_ref: x}}
daily_replay_time_policy: {{settlement_delay_seconds: 0}}
warmup: {{warm_up_1d_bars: 1, warm_up_4h_bars: 1}}
""")
    return p


def test_chunk_requires_both_dates(tmp_path: Path):
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    s = load_scenario(_scenario(tmp_path, hist))
    with pytest.raises(ValueError, match="Both --chunk-start and --chunk-end are required"):
        run_replay(s, tmp_path / "evaluation/replay", chunk_start=date(2025,1,1))


def test_first_chunk_and_resume_chunk_flow(tmp_path: Path):
    hist = tmp_path / "hist"
    d1=[{"close_time_utc": f"2025-01-{i:02d}T23:59:59Z", "close": float(i)} for i in range(1,32)]
    h4=[{"close_time_utc": f"2025-01-{i:02d}T04:00:00Z", "close": float(i)} for i in range(1,32)]
    _write_hist(hist,"AAAUSDT",d1,h4)
    s=load_scenario(_scenario_long(tmp_path,hist))
    m1=run_replay(s,tmp_path/"evaluation/replay",chunk_start=date(2025,1,1),chunk_end=date(2025,1,15),replay_id="2026-01-01T00:00:00Z",chunk_id="2025-01a")
    run_dir=tmp_path/"evaluation/replay"/"runs"/"s1"/"2026-01-01T00:00:00Z"
    resume=run_dir/"chunks"/"2025-01a"/"state_final.sqlite"
    before=resume.read_bytes()
    m2=run_replay(s,tmp_path/"evaluation/replay",chunk_start=date(2025,1,16),chunk_end=date(2025,1,31),resume_from_state=resume,replay_id="2026-01-01T00:00:00Z",chunk_id="2025-01b")
    assert before==resume.read_bytes()
    manifest=json.loads((run_dir/"replay_manifest.json").read_text())
    assert manifest["chunks_completed"]==["2025-01a","2025-01b"]
    assert manifest["chunks_total"] is None
    assert manifest["replay_days_completed"]==31
    assert (run_dir/"state_latest.sqlite").exists()
    assert (run_dir/"chunks"/"2025-01b"/"state_working.sqlite").exists()


def test_mid_period_without_resume_fails(tmp_path: Path):
    hist=tmp_path/"hist"; _write_hist(hist,"AAAUSDT",[{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    s=load_scenario(_scenario(tmp_path,hist))
    with pytest.raises(ValueError, match="resume_from_state is required"):
        run_replay(s,tmp_path/"evaluation/replay",chunk_start=date(2025,1,2),chunk_end=date(2025,1,2))
