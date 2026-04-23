from __future__ import annotations

import json
from pathlib import Path

import pytest

from scanner.config import ScannerConfig
from scanner.runners.daily import run_daily_scan
from scanner.storage import init_db


def _cfg(tmp_path: Path) -> ScannerConfig:
    return ScannerConfig(raw={"independence_release": {}, "runner": {}})


def test_as_of_date_invalid_format_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        run_daily_scan(_cfg(tmp_path), as_of_date="2026/01/01")


def test_as_of_date_future_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="past date"):
        run_daily_scan(_cfg(tmp_path), as_of_date="2999-01-01")


def test_empty_universe_non_publishable_minimal_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg(tmp_path)
    cfg.daily_universe_provider = lambda *_: []

    run_daily_scan(cfg, as_of_date="2026-01-01")

    conn = init_db("data/independence_release.sqlite")
    row = conn.execute("SELECT status, daily_bar_id, scan_mode FROM run_metadata ORDER BY started_at_utc DESC LIMIT 1").fetchone()
    assert row is not None
    assert row[0] == "completed"
    assert row[1] == "2026-01-01"
    assert row[2] == "daily_discovery"

    run_reports = list((tmp_path / "reports" / "runs" / "2026" / "01" / "01").glob("*/report.json"))
    assert len(run_reports) == 1
    report = json.loads(run_reports[0].read_text(encoding="utf-8"))
    assert report["candidate_count"] == 0

    assert not (tmp_path / "reports" / "index").exists()
    assert not (tmp_path / "reports" / "daily").exists()
