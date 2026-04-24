from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd
import pytest

from scanner.config import resolve_independence_evaluation_config
from scanner.evaluation.dataset_export import run_evaluation_export
from scanner.evaluation.replay import reconstruct_event_timeline


def _write_diag(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row) + "\n")


def _write_manifest(path: Path, run_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run_id": run_id}, sort_keys=True), encoding="utf-8")


def _write_daily_ohlcv(root: Path, symbol: str, rows: list[dict]) -> None:
    out = root / "snapshots" / "history" / "ohlcv" / "timeframe=1d" / f"symbol={symbol}" / "year=2026" / "month=04"
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(out / "part-000.parquet", index=False)


def test_evaluation_config_defaults_merge_and_guardrails() -> None:
    assert resolve_independence_evaluation_config({}) == {
        "horizons_days": [1, 3, 5, 10],
        "include_first_watch_metrics": True,
        "include_terminal_event_return_metrics": False,
    }
    assert resolve_independence_evaluation_config({"independence_release": {"evaluation": {"include_first_watch_metrics": False}}})[
        "include_first_watch_metrics"
    ] is False

    with pytest.raises(ValueError, match="terminal-event return metrics"):
        resolve_independence_evaluation_config(
            {"independence_release": {"evaluation": {"include_terminal_event_return_metrics": True}}}
        )


def test_replay_uses_snapshots_runs_and_picks_earliest_event(tmp_path: Path) -> None:
    run1 = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r1"
    run2 = tmp_path / "snapshots" / "runs" / "2026" / "04" / "02" / "r2"
    _write_manifest(run1 / "run.manifest.json", "r1")
    _write_manifest(run2 / "run.manifest.json", "r2")
    report_run1 = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r1"
    report_run2 = tmp_path / "reports" / "runs" / "2026" / "04" / "02" / "r2"
    _write_diag(
        report_run1 / "symbol_diagnostics.jsonl.gz",
        [
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "watch",
                "decision_bucket": "watchlist",
                "as_of_utc": "2026-04-01T00:00:00Z",
                "daily_bar_id": "2026-04-01",
            }
        ],
    )
    _write_diag(
        report_run2 / "symbol_diagnostics.jsonl.gz",
        [
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "watch",
                "decision_bucket": "watchlist",
                "as_of_utc": "2026-04-02T00:00:00Z",
                "daily_bar_id": "2026-04-02",
            }
        ],
    )

    events, diag = reconstruct_event_timeline(project_root=tmp_path)
    assert len(events) == 1
    assert events[0]["event_timestamp_utc"] == "2026-04-01T00:00:00Z"
    assert events[0]["source_snapshot_path"].startswith((tmp_path / "snapshots" / "runs").as_posix())
    assert diag["run_count"] == 2
    assert diag["missing_diagnostics_run_count"] == 0


def test_replay_missing_diagnostics_is_explicit(tmp_path: Path) -> None:
    run1 = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r1"
    _write_manifest(run1 / "run.manifest.json", "r1")
    events, diag = reconstruct_event_timeline(project_root=tmp_path)
    assert events == []
    assert diag["missing_diagnostics_run_count"] == 1
    assert diag["missing_diagnostics_run_ids"] == ["r1"]


def test_evaluation_export_intraday_mapping_and_terminal_scope(tmp_path: Path) -> None:
    run = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r1"
    _write_manifest(run / "run.manifest.json", "r1")
    report = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r1"
    _write_diag(
        report / "symbol_diagnostics.jsonl.gz",
        [
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "early_ready",
                "decision_bucket": "watchlist",
                "as_of_utc": "2026-04-01T08:10:00Z",
                "intraday_bar_id": "2026-04-01T08:00:00Z",
                "close_at_early_entry_bar": 90.0,
                "market_phase_confidence": 0,
                "state_confidence": 0,
                "priority_score": 0.0,
            },
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "late",
                "decision_bucket": "late_monitor",
                "as_of_utc": "2026-04-03T00:00:00Z",
                "daily_bar_id": "2026-04-03",
            },
        ],
    )
    _write_daily_ohlcv(
        tmp_path,
        "AAAUSDT",
        [
            {"daily_bar_id": "2026-04-01", "close": 100.0, "high": 105.0, "low": 95.0},
            {"daily_bar_id": "2026-04-02", "close": 99.0, "high": 120.0, "low": 80.0},
            {"daily_bar_id": "2026-04-03", "close": 110.0, "high": 112.0, "low": 90.0},
        ],
    )

    run_evaluation_export(project_root=tmp_path)
    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    terminal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "terminal_event_timeline.parquet")

    row = signal.iloc[0].to_dict()
    assert row["reference_price"] == 90.0
    assert row["market_phase_confidence"] == 0
    assert row["state_confidence"] == 0
    assert row["priority_score"] == 0.0
    assert row["metric_status_1d"] == "ok"
    assert row["forward_return_1d_pct"] == pytest.approx(10.0)
    assert row["metric_status_3d"] == "insufficient_future_data"

    assert terminal.iloc[0]["event_type"] == "first_late"
    assert terminal.iloc[0]["return_metrics_status"] == "terminal_event_returns_out_of_scope"


def test_include_first_watch_metrics_respected(tmp_path: Path) -> None:
    run = tmp_path / "snapshots" / "runs" / "2026" / "04" / "01" / "r1"
    _write_manifest(run / "run.manifest.json", "r1")
    report = tmp_path / "reports" / "runs" / "2026" / "04" / "01" / "r1"
    _write_diag(
        report / "symbol_diagnostics.jsonl.gz",
        [
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "watch",
                "decision_bucket": "watchlist",
                "as_of_utc": "2026-04-01T00:00:00Z",
                "daily_bar_id": "2026-04-01",
            },
            {
                "symbol": "AAAUSDT",
                "setup_cycle_id": 1,
                "state_machine_state": "early_ready",
                "decision_bucket": "watchlist",
                "as_of_utc": "2026-04-01T08:10:00Z",
                "intraday_bar_id": "2026-04-01T08:00:00Z",
                "close_at_early_entry_bar": 90.0,
            },
        ],
    )
    _write_daily_ohlcv(
        tmp_path,
        "AAAUSDT",
        [
            {"daily_bar_id": "2026-04-01", "close": 100.0, "high": 105.0, "low": 95.0},
            {"daily_bar_id": "2026-04-02", "close": 99.0, "high": 120.0, "low": 80.0},
            {"daily_bar_id": "2026-04-03", "close": 110.0, "high": 112.0, "low": 90.0},
            {"daily_bar_id": "2026-04-04", "close": 111.0, "high": 115.0, "low": 90.0},
            {"daily_bar_id": "2026-04-05", "close": 112.0, "high": 118.0, "low": 90.0},
            {"daily_bar_id": "2026-04-06", "close": 113.0, "high": 119.0, "low": 90.0},
            {"daily_bar_id": "2026-04-07", "close": 114.0, "high": 120.0, "low": 90.0},
            {"daily_bar_id": "2026-04-08", "close": 115.0, "high": 121.0, "low": 90.0},
            {"daily_bar_id": "2026-04-09", "close": 116.0, "high": 122.0, "low": 90.0},
            {"daily_bar_id": "2026-04-10", "close": 117.0, "high": 123.0, "low": 90.0},
            {"daily_bar_id": "2026-04-11", "close": 118.0, "high": 124.0, "low": 90.0},
        ],
    )

    run_evaluation_export(project_root=tmp_path, config={"independence_release": {"evaluation": {"include_first_watch_metrics": True}}})
    signal_true = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    assert "first_watch" in set(signal_true["event_type"].tolist())

    run_evaluation_export(project_root=tmp_path, config={"independence_release": {"evaluation": {"include_first_watch_metrics": False}}})
    signal_false = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    assert "first_watch" not in set(signal_false["event_type"].tolist())
    assert "first_early_ready" in set(signal_false["event_type"].tolist())


def test_ticket18_docs_updated() -> None:
    open_questions = Path("docs/canonical/open_questions.md").read_text(encoding="utf-8")
    enhancements = Path("docs/canonical/feature_enhancements.md").read_text(encoding="utf-8")
    assert "resolved by Ticket 14" in open_questions
    assert "Canonical OHLCV long-term storage" in open_questions
    assert "Terminal-event forward returns for decay / invalidation states" in enhancements
