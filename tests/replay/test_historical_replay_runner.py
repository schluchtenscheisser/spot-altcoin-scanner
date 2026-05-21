from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

from scanner.evaluation.historical_replay.bar_loader import HistoricalBarLoader
from scanner.evaluation.historical_replay.replay_runner import run_replay
from scanner.evaluation.historical_replay.scenario import load_scenario


def _mk_history(root: Path, symbol: str = "AAAUSDT") -> None:
    (root / "1d").mkdir(parents=True)
    (root / "4h").mkdir(parents=True)
    d1 = pd.DataFrame([
        {"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0},
        {"close_time_utc": "2025-01-02T23:59:59Z", "close": 2.0},
    ])
    h4 = pd.DataFrame([
        {"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0},
        {"close_time_utc": "2025-01-01T08:00:00Z", "close": 1.1},
        {"close_time_utc": "2025-01-01T12:00:00Z", "close": 1.2},
    ])
    d1.to_parquet(root / "1d" / f"{symbol}.parquet", index=False)
    h4.to_parquet(root / "4h" / f"{symbol}.parquet", index=False)


def _scenario(tmp: Path, history: Path, warm4h: int = 1) -> Path:
    p = tmp / "scenario.yml"
    p.write_text(f"""
scenario_id: s1
history_dataset_ref: {history.as_posix()}
history_manifest_ref: hm
universe_manifest_ref: um
evaluation: {{start_date: 2025-01-01, end_date: 2025-01-02}}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {{mode: disabled_historical_ohlcv_only}}
scanner_config: {{ref: config/config.yml, hash: abc}}
regime_labels: {{method_ref: x}}
daily_replay_time_policy: {{settlement_delay_seconds: 0}}
warmup: {{warm_up_1d_bars: 1, warm_up_4h_bars: {warm4h}}}
""")
    return p


def test_point_in_time_slice_excludes_future(tmp_path: Path) -> None:
    _mk_history(tmp_path)
    loader = HistoricalBarLoader(tmp_path.as_posix())
    bars = loader.closed_bars_as_of("AAAUSDT", "1d", pd.Timestamp("2025-01-01T23:59:59Z").to_pydatetime()).bars
    assert len(bars) == 1


def test_runner_manifest_and_diagnostics_constraints(tmp_path: Path) -> None:
    history = tmp_path / "hist"
    _mk_history(history)
    scenario = load_scenario(_scenario(tmp_path, history))
    out = tmp_path / "evaluation/replay"
    manifest = run_replay(scenario=scenario, output_root=out)
    run_dir = out / "runs" / "s1" / manifest["replay_id"]
    assert (run_dir / "state.sqlite").exists()
    assert manifest["scenario_config_hash_excludes_splits"] is True
    rows = []
    with gzip.open(run_dir / "replay_symbol_diagnostics.jsonl.gz", "rt", encoding="utf-8") as f:
        for line in f:
            rows.append(json.loads(line))
    assert rows
    assert all("decision_bucket" not in r for r in rows)
    assert all(r["execution_mode"] == "disabled_historical_ohlcv_only" for r in rows)


def test_warmup_skips_diag_rows(tmp_path: Path) -> None:
    history = tmp_path / "hist"
    _mk_history(history)
    scenario = load_scenario(_scenario(tmp_path, history, warm4h=999))
    out = tmp_path / "evaluation/replay"
    manifest = run_replay(scenario=scenario, output_root=out)
    run_dir = out / "runs" / "s1" / manifest["replay_id"]
    with gzip.open(run_dir / "replay_symbol_diagnostics.jsonl.gz", "rt", encoding="utf-8") as f:
        assert f.read() == ""
    assert manifest["warmup_summary_by_symbol"]["AAAUSDT"]["warmup_days_skipped"] == 2
