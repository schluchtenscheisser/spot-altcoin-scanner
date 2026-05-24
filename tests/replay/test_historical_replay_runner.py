from __future__ import annotations

import gzip
import json
from pathlib import Path
import sqlite3
import re

import pandas as pd
import pytest

from scanner.evaluation.historical_replay.bar_loader import HistoricalBarLoader
from scanner.evaluation.historical_replay.replay_runner import run_replay
from scanner.evaluation.historical_replay.scenario import load_scenario


def _with_ohlcv_defaults(rows: list[dict]) -> list[dict]:
    out: list[dict] = []
    for row in rows:
        r = dict(row)
        c = float(r.get("close", 0.0))
        r.setdefault("high", c)
        r.setdefault("low", c)
        r.setdefault("volume", 1.0)
        r.setdefault("quote_volume", c)
        out.append(r)
    return out


def _write_hist(root: Path, symbol: str, d1_rows: list[dict], h4_rows: list[dict]) -> None:
    d1_dir = root / "timeframe=1d" / f"symbol={symbol}"
    h4_dir = root / "timeframe=4h" / f"symbol={symbol}"
    d1_dir.mkdir(parents=True, exist_ok=True)
    h4_dir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(_with_ohlcv_defaults(d1_rows)).to_parquet(d1_dir / "data.parquet", index=False)
    pd.DataFrame(_with_ohlcv_defaults(h4_rows)).to_parquet(h4_dir / "data.parquet", index=False)


def _scenario(tmp: Path, history: Path, warm4h: int = 1) -> Path:
    p = tmp / "scenario.yml"
    p.write_text(f"""
scenario_id: s1
history_dataset_ref: {history.as_posix()}
history_manifest_ref: hm
universe_manifest_ref: um
evaluation: {{start_date: 2025-01-01, end_date: 2025-01-03}}
timeframes: [1d, 4h]
universe_mode: fixed
execution: {{mode: disabled_historical_ohlcv_only}}
scanner_config: {{ref: config/config.yml, hash: abc}}
regime_labels: {{method_ref: x}}
daily_replay_time_policy: {{settlement_delay_seconds: 0}}
warmup: {{warm_up_1d_bars: 1, warm_up_4h_bars: {warm4h}}}
""")
    return p


def _rows(path: Path) -> list[dict]:
    out = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def test_point_in_time_slice_excludes_future(tmp_path: Path) -> None:
    _write_hist(tmp_path, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}, {"close_time_utc": "2025-01-02T23:59:59Z", "close": 2.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    loader = HistoricalBarLoader(tmp_path.as_posix())
    bars = loader.closed_bars_as_of("AAAUSDT", "1d", pd.Timestamp("2025-01-01T23:59:59Z").to_pydatetime()).bars
    assert len(bars) == 1


def test_missing_current_1d_after_warmup_is_missing_data_and_no_stale_price(tmp_path: Path) -> None:
    hist = tmp_path / "hist"
    _write_hist(
        hist,
        "AAAUSDT",
        [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 100.0}],
        [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}, {"close_time_utc": "2025-01-02T04:00:00Z", "close": 1.1}],
    )
    scenario = load_scenario(_scenario(tmp_path, hist))
    manifest = run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    run_dir = tmp_path / "evaluation/replay" / "runs" / "s1" / manifest["replay_id"]
    rows = _rows(run_dir / "replay_symbol_diagnostics.jsonl.gz")
    missing_day = [r for r in rows if r["as_of_daily_bar_id"] == "2025-01-02"][0]
    assert missing_day["disposition_status"] == "not_evaluable_missing_data"
    assert missing_day["disposition_reason"] == "MISSING_1D_BAR"
    assert missing_day["historical_signal_bucket"] == "not_evaluable_missing_data"
    assert missing_day["signal_daily_close"] is None
    assert missing_day["state_machine_state"] is None
    con = sqlite3.connect(run_dir / "state.sqlite")
    state = con.execute("SELECT last_aging_daily_bar_id, bars_since_state_entered, consecutive_missing_1d_bars FROM replay_state WHERE symbol='AAAUSDT'").fetchone()
    assert state[0] == "2025-01-01"
    assert state[1] == 1
    assert state[2] >= 1
    assert pd.read_parquet(run_dir / "replay_event_candidates.parquet").empty


def test_missing_current_day_4h_is_missing_context(tmp_path: Path) -> None:
    hist = tmp_path / "hist"
    _write_hist(
        hist,
        "AAAUSDT",
        [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}, {"close_time_utc": "2025-01-02T23:59:59Z", "close": 2.0}],
        [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}],
    )
    scenario = load_scenario(_scenario(tmp_path, hist))
    manifest = run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    rows = _rows(tmp_path / "evaluation/replay" / "runs" / "s1" / manifest["replay_id"] / "replay_symbol_diagnostics.jsonl.gz")
    d2 = [r for r in rows if r["as_of_daily_bar_id"] == "2025-01-02"][0]
    assert d2["data_4h_available"] is False
    assert d2["disposition_reason"] == "MISSING_4H_CONTEXT"
    assert d2["historical_signal_bucket"] == "not_evaluable_missing_data"


def test_manifest_evaluable_counts_warmup_only_and_mixed(tmp_path: Path) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    _write_hist(hist, "BBBUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    scenario = load_scenario(_scenario(tmp_path, hist, warm4h=999))
    m1 = run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    assert m1["symbols_total"] == 2
    assert m1["symbols_evaluable"] == 0
    assert m1["symbols_excluded_warmup"] == 2
    assert all(v["first_evaluable_date"] is None for v in m1["warmup_summary_by_symbol"].values())

    hist2 = tmp_path / "hist2"
    _write_hist(hist2, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}, {"close_time_utc": "2025-01-02T23:59:59Z", "close": 2.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}, {"close_time_utc": "2025-01-02T04:00:00Z", "close": 1.1}])
    _write_hist(hist2, "BBBUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    m2 = run_replay(scenario=load_scenario(_scenario(tmp_path, hist2, warm4h=2)), output_root=tmp_path / "evaluation/replay2")
    assert m2["symbols_total"] == 2
    assert m2["symbols_evaluable"] == 1
    assert m2["symbols_excluded_warmup"] == 1


def test_replay_runner_logs_start_and_day_progress(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    scenario = load_scenario(_scenario(tmp_path, hist))
    with caplog.at_level("INFO"):
        run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    messages = [r.message for r in caplog.records]
    assert any("Starting replay scenario_id=s1" in m for m in messages)
    assert any("Replaying day 2025-01-01 (1/3) symbols=1" in m for m in messages)
    assert any("Day 2025-01-01 done:" in m for m in messages)
    assert any("Replay complete replay_id=" in m for m in messages)


def test_symbol_exception_logs_context_and_reraises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    scenario = load_scenario(_scenario(tmp_path, hist))

    original = HistoricalBarLoader.closed_bars_as_of

    def _boom(self: HistoricalBarLoader, symbol: str, timeframe: str, as_of: object) -> object:
        if symbol == "AAAUSDT" and timeframe == "1d":
            raise RuntimeError("boom")
        return original(self, symbol, timeframe, as_of)

    monkeypatch.setattr(HistoricalBarLoader, "closed_bars_as_of", _boom)
    with caplog.at_level("INFO"), pytest.raises(RuntimeError, match="boom"):
        run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    assert any("Symbol AAAUSDT day 2025-01-01 failed: boom" in r.message for r in caplog.records)


def test_abort_exception_logs_context_and_reraises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    scenario = load_scenario(_scenario(tmp_path, hist))

    def _boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("fatal")

    monkeypatch.setattr(HistoricalBarLoader, "closed_bars_as_of", _boom)
    with caplog.at_level("INFO"), pytest.raises(RuntimeError, match="fatal"):
        run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    assert any("Replay aborted after 0/3 days: fatal" in r.message for r in caplog.records)


def test_auto_generated_replay_id_is_filesystem_safe(tmp_path: Path) -> None:
    hist = tmp_path / "hist"
    _write_hist(hist, "AAAUSDT", [{"close_time_utc": "2025-01-01T23:59:59Z", "close": 1.0}], [{"close_time_utc": "2025-01-01T04:00:00Z", "close": 1.0}])
    scenario = load_scenario(_scenario(tmp_path, hist))
    manifest = run_replay(scenario=scenario, output_root=tmp_path / "evaluation/replay")
    replay_id = manifest["replay_id"]
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}Z", replay_id)
    assert not any(ch in replay_id for ch in ':\"<>|*?\\\\/\\r\\n')
