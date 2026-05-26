from __future__ import annotations

from datetime import date
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

import scripts.diagnostics.may_2025_cold_start_diagnostic as diag


class _DummyLoader:
    def __init__(self, _ref: str) -> None:
        pass

    def closed_bars_as_of(self, _symbol: str, timeframe: str, _as_of) -> SimpleNamespace:
        ts = pd.Timestamp("2025-05-01T23:59:59Z")
        bars = pd.DataFrame([{"close_time_utc": ts, "close": 1.0}])
        if timeframe == "4h":
            bars = pd.DataFrame([{"close_time_utc": ts}])
        return SimpleNamespace(bars=bars)


class _DummyAdapter:
    def __call__(self, **kwargs):
        persisted = kwargs["persisted_state"]
        first = "seen" not in persisted
        return SimpleNamespace(
            updated_state_patch={"seen": True},
            transition_event_types=["first_watch"] if first else [],
        )


def _scenario(dataset_root: Path) -> SimpleNamespace:
    return SimpleNamespace(
        history_dataset_ref=str(dataset_root),
        settlement_delay_seconds=0,
        warm_up_1d_bars=1,
        warm_up_4h_bars=1,
        scanner_config_ref="x",
        scanner_config_hash="y",
        evaluation=SimpleNamespace(start_date=date(2025, 5, 1), end_date=date(2025, 6, 2)),
    )


def _prepare_dataset(tmp_path: Path) -> Path:
    root = tmp_path / "hist"
    (root / "timeframe=1d" / "symbol=AAA").mkdir(parents=True)
    return root


def test_reset_sqlite_state_removes_db_and_sidecars(tmp_path: Path) -> None:
    p = tmp_path / "state.sqlite"
    for suffix in ["", "-wal", "-shm", "-journal"]:
        (tmp_path / f"state.sqlite{suffix}").write_text("x", encoding="utf-8")
    diag._reset_sqlite_state(p)
    for suffix in ["", "-wal", "-shm", "-journal"]:
        assert not (tmp_path / f"state.sqlite{suffix}").exists()


def test_running_twice_same_workdir_is_deterministic(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(diag, "HistoricalBarLoader", _DummyLoader)
    monkeypatch.setattr(diag, "HistoricalProductionAdapter", _DummyAdapter)
    dataset = _prepare_dataset(tmp_path)
    scenario = _scenario(dataset)
    out = tmp_path / "out"
    out.mkdir()

    r1 = diag._collect_events(scenario, scenario.evaluation.start_date, scenario.evaluation.start_date, scenario.evaluation.start_date, "cold_start", out)
    r2 = diag._collect_events(scenario, scenario.evaluation.start_date, scenario.evaluation.start_date, scenario.evaluation.start_date, "cold_start", out)
    assert r1.total_events == r2.total_events == 1


def test_stale_state_file_does_not_affect_cold_start_or_preroll(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(diag, "HistoricalBarLoader", _DummyLoader)
    monkeypatch.setattr(diag, "HistoricalProductionAdapter", _DummyAdapter)
    dataset = _prepare_dataset(tmp_path)
    scenario = _scenario(dataset)
    out = tmp_path / "out"
    out.mkdir()

    for mode in ["cold_start", "state_preroll"]:
        stale = out / f"{mode}_state.sqlite"
        stale.write_text("stale", encoding="utf-8")
        (out / f"{mode}_state.sqlite-wal").write_text("stale", encoding="utf-8")
        result = diag._collect_events(scenario, scenario.evaluation.start_date, scenario.evaluation.start_date, scenario.evaluation.start_date, mode, out)
        assert result.total_events == 1


def test_collect_events_respects_diagnostic_end_date(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(diag, "HistoricalBarLoader", _DummyLoader)
    monkeypatch.setattr(diag, "HistoricalProductionAdapter", _DummyAdapter)
    dataset = _prepare_dataset(tmp_path)
    scenario = _scenario(dataset)
    out = tmp_path / "out"
    out.mkdir()
    result = diag._collect_events(
        scenario,
        scenario.evaluation.start_date,
        scenario.evaluation.start_date,
        date(2025, 5, 31),
        "cold_start",
        out,
    )
    assert result.events_by_month == {"2025-05": 1}


def test_month_and_event_type_grouping_rendered() -> None:
    cold = diag.ReplayModeResult("cold", 3, {"2025-05": 3}, {"first_watch": 2, "first_early": 1}, [("AAA", 2)], [("2025-05-01", 2)])
    pre = diag.ReplayModeResult("pre", 1, {"2025-05": 1}, {"first_early": 1}, [("AAA", 1)], [("2025-05-01", 1)])

    class S:
        scenario_id = "s1"
        evaluation = type("E", (), {"start_date": date(2025, 5, 1), "end_date": date(2025, 5, 10)})

    report = diag._render_report(
        scenario_path=type("P", (), {"as_posix": lambda self: "scenario.yml"})(),
        scenario=S(),
        preroll_start_date=date(2025, 1, 1),
        diagnostic_end_date=date(2025, 5, 31),
        cold=cold,
        preroll=pre,
        command="python ...",
    )
    assert "| 2025-05 | 3 | 1 |" in report
    assert "first_watch" in report
    assert "Diagnostic end date: `2025-05-31`" in report


def test_main_rejects_diagnostic_end_date_before_eval_start(tmp_path: Path, monkeypatch) -> None:
    dataset = _prepare_dataset(tmp_path)
    scenario = _scenario(dataset)
    monkeypatch.setattr(diag, "load_scenario", lambda _p: scenario)
    monkeypatch.setattr(diag, "_collect_events", lambda *args, **kwargs: None)
    monkeypatch.setattr(diag, "_render_report", lambda *args, **kwargs: "x")
    monkeypatch.setattr("sys.argv", ["diag", "--scenario", "s.yml", "--diagnostic-end-date", "2025-04-30"])
    try:
        diag.main()
        assert False, "Expected SystemExit"
    except SystemExit as exc:
        assert "diagnostic_end_date must be on or after evaluation_start_date" in str(exc)


def test_main_rejects_diagnostic_end_date_after_eval_end(tmp_path: Path, monkeypatch) -> None:
    dataset = _prepare_dataset(tmp_path)
    scenario = _scenario(dataset)
    monkeypatch.setattr(diag, "load_scenario", lambda _p: scenario)
    monkeypatch.setattr(diag, "_collect_events", lambda *args, **kwargs: None)
    monkeypatch.setattr(diag, "_render_report", lambda *args, **kwargs: "x")
    monkeypatch.setattr("sys.argv", ["diag", "--scenario", "s.yml", "--diagnostic-end-date", "2025-06-03"])
    try:
        diag.main()
        assert False, "Expected SystemExit"
    except SystemExit as exc:
        assert "diagnostic_end_date must be on or before scenario.evaluation.end_date" in str(exc)
