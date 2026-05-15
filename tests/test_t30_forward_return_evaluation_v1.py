from __future__ import annotations

import gzip
import json
from pathlib import Path

import pandas as pd
import pytest

from scripts import run_t30_evaluation as t30


def _write_manifest(project_root: Path, run_id: str = "daily-test") -> Path:
    path = project_root / "snapshots" / "runs" / "2026" / "05" / "03" / run_id / "run.manifest.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"run_id": run_id, "scan_mode": "daily"}, sort_keys=True), encoding="utf-8")
    return path


def _write_diag(project_root: Path, rows: list[dict], run_id: str = "daily-test") -> Path:
    path = project_root / "reports" / "runs" / "2026" / "05" / "03" / run_id / "symbol_diagnostics.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")
    return path


def _write_ohlcv(
    project_root: Path,
    symbol: str = "AAAUSDT",
    rows: list[dict] | None = None,
    history_root: Path | None = None,
) -> Path:
    if rows is None:
        rows = [
            {"daily_bar_id": f"2026-05-{day:02d}", "close": 100.0 + day, "high": 101.0 + day, "low": 99.0 + day}
            for day in range(3, 15)
        ]
    base_history_root = history_root if history_root is not None else project_root / "snapshots" / "history"
    path = (
        base_history_root
        / "ohlcv"
        / "timeframe=1d"
        / f"symbol={symbol}"
        / "year=2026"
        / "month=05"
        / "part-000.parquet"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)
    return path


def _valid_diag_rows() -> list[dict]:
    return [
        {
            "symbol": "AAAUSDT",
            "setup_cycle_id": 1,
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "as_of_utc": "2026-05-03T00:00:00Z",
            "daily_bar_id": "2026-05-03",
        },
        {
            "symbol": "AAAUSDT",
            "setup_cycle_id": 1,
            "state_machine_state": "late",
            "decision_bucket": "late_monitor",
            "as_of_utc": "2026-05-06T00:00:00Z",
            "daily_bar_id": "2026-05-06",
        },
        {
            "symbol": "BBBUSDT",
            "setup_cycle_id": 2,
            "state_machine_state": "early_ready",
            "decision_bucket": "early_candidates",
            "as_of_utc": "2026-05-04T08:10:00Z",
            "intraday_bar_id": "2026-05-04T08:00:00Z",
        },
    ]


def _prepare_valid_fixture(project_root: Path) -> None:
    _write_manifest(project_root)
    _write_diag(project_root, _valid_diag_rows())
    _write_ohlcv(project_root, "AAAUSDT")


def test_t30_script_runs_t18_export_and_writes_note_and_summary(tmp_path: Path) -> None:
    _prepare_valid_fixture(tmp_path)

    exit_code = t30.main(["--project-root", str(tmp_path)])

    assert exit_code == 0
    required = [
        "evaluation/exports/signal_event_metrics.parquet",
        "evaluation/exports/terminal_event_timeline.parquet",
        "evaluation/exports/transition_lead_times.parquet",
        "evaluation/exports/evaluation_summary.json",
        "evaluation/replay/event_timeline.jsonl",
        "evaluation/replay/replay_manifest.json",
        "evaluation/replay/replay_diagnostics.json",
        "evaluation/replay/t30_run_summary.json",
        "evaluation/notes/T30_forward_return_evaluation_v1.md",
    ]
    for rel in required:
        assert (tmp_path / rel).exists(), rel
        assert (tmp_path / rel).stat().st_size > 0, rel

    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    watch = signal.loc[signal["event_type"] == "first_watch"].iloc[0]
    assert watch["metric_status_1d"] == "ok"
    assert watch["forward_return_1d_pct"] == pytest.approx(((104.0 - 103.0) / 103.0) * 100.0)

    summary = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    assert summary["schema"] == "t30_run_summary_v1"
    assert summary["input_counts"]["manifest_count"] == 1
    assert summary["input_counts"]["ohlcv_symbol_count"] == 1
    assert summary["history_root"] == (tmp_path / "snapshots" / "history").as_posix()
    assert summary["event_counts_by_type"]["first_watch"] == 1
    assert summary["metric_status_counts_by_horizon"]["1d"]["ok"] == 1
    assert summary["metric_status_counts_by_horizon"]["1d"]["missing_ohlcv_history"] == 1

    note = (tmp_path / "evaluation" / "notes" / "T30_forward_return_evaluation_v1.md").read_text(encoding="utf-8")
    for heading in [
        "## Status",
        "## Input data",
        "## Evaluation outputs",
        "## Event coverage",
        "## Forward-return metric coverage",
        "## Primary cohort: ir1.5+",
        "## Exploratory historical cohort: pre-ir1.5",
        "## Segment observations",
        "## Known limitations",
        "## Next recommended steps",
    ]:
        assert heading in note
    assert "Not a final performance conclusion" in note
    assert "Effective OHLCV history root" in note
    assert "reference_price_not_evaluable" in note


def test_t30_alternate_history_root_is_used_for_export(tmp_path: Path) -> None:
    _write_manifest(tmp_path)
    _write_diag(tmp_path, _valid_diag_rows())
    alternate_history = tmp_path / "prefetched-history"
    _write_ohlcv(tmp_path, "AAAUSDT", history_root=alternate_history)

    exit_code = t30.main(["--project-root", str(tmp_path), "--history-root", str(alternate_history)])

    assert exit_code == 0
    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    watch = signal.loc[signal["event_type"] == "first_watch"].iloc[0]
    assert watch["metric_status_1d"] == "ok"
    assert watch["metric_status_1d"] != "missing_ohlcv_history"
    summary = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    assert summary["history_root"] == alternate_history.as_posix()


def test_t30_default_history_root_still_works(tmp_path: Path) -> None:
    _prepare_valid_fixture(tmp_path)

    exit_code = t30.main(["--project-root", str(tmp_path)])

    assert exit_code == 0
    signal = pd.read_parquet(tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet")
    watch = signal.loc[signal["event_type"] == "first_watch"].iloc[0]
    assert watch["metric_status_1d"] == "ok"


def test_t30_missing_alternate_history_root_fails_preflight(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_manifest(tmp_path)
    _write_diag(tmp_path, _valid_diag_rows())
    missing_history = tmp_path / "does-not-exist"

    exit_code = t30.main(["--project-root", str(tmp_path), "--history-root", str(missing_history)])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "missing OHLCV history" in captured.err
    assert missing_history.as_posix() in captured.err
    assert not (tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet").exists()


def test_t30_missing_manifests_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_ohlcv(tmp_path)

    exit_code = t30.main(["--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "missing replay manifests" in captured.err
    assert not (tmp_path / "evaluation" / "notes" / "T30_forward_return_evaluation_v1.md").exists()


def test_t30_missing_ohlcv_history_fails_clearly(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _write_manifest(tmp_path)
    _write_diag(tmp_path, _valid_diag_rows())

    exit_code = t30.main(["--project-root", str(tmp_path)])

    captured = capsys.readouterr()
    assert exit_code != 0
    assert "missing OHLCV history" in captured.err
    assert "scripts/fetch_ohlcv_history_for_evaluation.py" in captured.err
    assert not (tmp_path / "evaluation" / "exports" / "signal_event_metrics.parquet").exists()


def test_t30_output_validation_catches_empty_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _prepare_valid_fixture(tmp_path)

    def fake_export(*, project_root: Path, config: dict | None = None, history_root: str | Path = "snapshots/history") -> dict:
        exports = project_root / "evaluation" / "exports"
        replay = project_root / "evaluation" / "replay"
        exports.mkdir(parents=True, exist_ok=True)
        replay.mkdir(parents=True, exist_ok=True)
        (exports / "signal_event_metrics.parquet").write_bytes(b"")
        pd.DataFrame([{"event_type": "first_late"}]).to_parquet(exports / "terminal_event_timeline.parquet", index=False)
        pd.DataFrame([{"transition_status": "ok"}]).to_parquet(exports / "transition_lead_times.parquet", index=False)
        (exports / "evaluation_summary.json").write_text("{}\n", encoding="utf-8")
        (replay / "event_timeline.jsonl").write_text('{"event_type":"first_watch"}\n', encoding="utf-8")
        (replay / "replay_manifest.json").write_text('{"event_count":1}\n', encoding="utf-8")
        (replay / "replay_diagnostics.json").write_text('{"event_count":1,"missing_diagnostics_run_count":0}\n', encoding="utf-8")
        return {}

    monkeypatch.setattr(t30, "run_evaluation_export", fake_export)

    exit_code = t30.main(["--project-root", str(tmp_path)])

    assert exit_code == 5
    summary = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    assert "evaluation/exports/signal_event_metrics.parquet" in summary["validation"]["unreadable_outputs"]


def test_t30_metric_status_counts_are_per_horizon_and_not_collapsed(tmp_path: Path) -> None:
    _prepare_valid_fixture(tmp_path)

    assert t30.main(["--project-root", str(tmp_path)]) == 0

    summary = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    counts = summary["metric_status_counts_by_horizon"]
    assert counts["1d"]["ok"] == 1
    assert counts["1d"]["missing_ohlcv_history"] == 1
    assert counts["10d"]["ok"] == 1
    assert "failed" not in counts["1d"]


def test_t30_summary_counts_are_deterministic(tmp_path: Path) -> None:
    _prepare_valid_fixture(tmp_path)

    assert t30.main(["--project-root", str(tmp_path)]) == 0
    first = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    first_counts = json.dumps(
        {
            "event_counts_by_type": first["event_counts_by_type"],
            "metric_status_counts_by_horizon": first["metric_status_counts_by_horizon"],
        },
        sort_keys=True,
    )

    assert t30.main(["--project-root", str(tmp_path)]) == 0
    second = json.loads((tmp_path / "evaluation" / "replay" / "t30_run_summary.json").read_text(encoding="utf-8"))
    second_counts = json.dumps(
        {
            "event_counts_by_type": second["event_counts_by_type"],
            "metric_status_counts_by_horizon": second["metric_status_counts_by_horizon"],
        },
        sort_keys=True,
    )
    assert second_counts == first_counts


def test_t30_does_not_integrate_with_shadow_live_workflow() -> None:
    workflow = Path(".github/workflows/independence-shadow-live.yml")
    if workflow.exists():
        content = workflow.read_text(encoding="utf-8")
        assert "run_t30_evaluation.py" not in content


def test_t30_generated_file_ignore_guardrails() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    assert "evaluation/exports/*.parquet" in gitignore
    assert "snapshots/history/ohlcv/**" in gitignore
