from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd

from scanner.evaluation.historical_replay.production_adapter import ReplayProductionOutput
from scanner.evaluation.historical_replay.replay_runner import run_replay
from scanner.evaluation.historical_replay.scenario import load_scenario


def _write_hist(root: Path, symbol: str) -> None:
    d1_dir = root / "timeframe=1d" / f"symbol={symbol}"
    h4_dir = root / "timeframe=4h" / f"symbol={symbol}"
    d1_dir.mkdir(parents=True, exist_ok=True)
    h4_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"close_time_utc": "2025-01-01T23:59:59Z", "close": 10.0},
    ]).to_parquet(d1_dir / "data.parquet", index=False)
    pd.DataFrame([
        {"close_time_utc": "2025-01-01T04:00:00Z", "close": 9.0},
    ]).to_parquet(h4_dir / "data.parquet", index=False)


def _scenario(tmp: Path, history: Path) -> Path:
    p = tmp / "scenario.yml"
    p.write_text(f"""
scenario_id: s1
history_dataset_ref: {history.as_posix()}
history_manifest_ref: hm
universe_manifest_ref: um
evaluation: {{start_date: 2025-01-01, end_date: 2025-01-01}}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {{mode: disabled_historical_ohlcv_only}}
scanner_config: {{ref: config/config.yml, hash: abc}}
regime_labels: {{method_ref: x}}
daily_replay_time_policy: {{settlement_delay_seconds: 0}}
warmup: {{warm_up_1d_bars: 1, warm_up_4h_bars: 1}}
""")
    return p


def _rows(path: Path) -> list[dict]:
    out: list[dict] = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def test_runner_uses_adapter_outputs_and_emits_events(tmp_path: Path) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT")
    scenario = load_scenario(_scenario(tmp_path, hist))

    def _stub_adapter(**kwargs: object) -> ReplayProductionOutput:
        return ReplayProductionOutput(
            disposition_status="admitted",
            disposition_reason="STUB_OK",
            market_phase="impulse",
            market_phase_confidence=88.0,
            state_machine_state="confirmed_ready",
            state_confidence=91.0,
            state_transition_reason="STUB_TRANSITION",
            setup_cycle_id="cycle-1",
            entry_pattern="range_reclaim",
            entry_pattern_score=77.0,
            signal_daily_close=10.0,
            transition_event_types=["first_confirmed_with_entry_pattern"],
            updated_state_patch={"state_machine_state": "confirmed_ready", "state_confidence": 91.0},
            production_modules_used=["scanner.phase.interpreter", "scanner.state.machine", "scanner.entry.patterns"],
        )

    manifest = run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay", production_adapter=_stub_adapter)
    run_dir = tmp_path / "evaluation/replay" / "runs" / "s1" / manifest["replay_id"]

    rows = _rows(run_dir / "replay_symbol_diagnostics.jsonl.gz")
    assert len(rows) == 1
    row = rows[0]
    assert row["market_phase"] == "impulse"
    assert row["state_machine_state"] == "confirmed_ready"
    assert row["entry_pattern"] == "range_reclaim"
    assert row["historical_signal_bucket"] == "confirmed_candidates"
    assert "decision_bucket" not in row
    assert "next_daily_open" not in row
    assert "forward_return_1d" not in row

    events = pd.read_parquet(run_dir / "replay_event_candidates.parquet")
    assert len(events) == 1
    assert events.iloc[0]["event_type"] == "first_confirmed_with_entry_pattern"
    assert events.iloc[0]["historical_signal_bucket"] == "confirmed_candidates"

    assert manifest["production_modules_used"] == [
        "scanner.entry.patterns",
        "scanner.phase.interpreter",
        "scanner.state.machine",
    ]
