from __future__ import annotations

from datetime import datetime, timezone

import pytest

from scanner.config import ScannerConfig, resolve_independence_intraday_config
from scanner.data.bar_clock import get_last_closed_intraday_bar_id, has_new_intraday_bar
import scanner.runners.intraday as intraday_runner
from scanner.runners.intraday import run_intraday_scan
from scanner.storage import init_db


def _cfg(raw: dict | None = None) -> ScannerConfig:
    merged = {"independence_release": {}}
    if raw:
        merged["independence_release"].update(raw.get("independence_release", {}))
    return ScannerConfig(raw=merged)


def test_intraday_bar_clock_helpers() -> None:
    now = datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc)
    assert get_last_closed_intraday_bar_id(now) == "2026-04-24T08:00:00Z"
    assert has_new_intraday_bar(None, "2026-04-24T08:00:00Z") is True
    assert has_new_intraday_bar("2026-04-24T08:00:00Z", "2026-04-24T08:00:00Z") is False
    assert has_new_intraday_bar("2026-04-24T04:00:00Z", "2026-04-24T08:00:00Z") is True


def test_intraday_bar_clock_rejects_invalid_previous_id() -> None:
    with pytest.raises(ValueError, match="previous_bar_id"):
        has_new_intraday_bar("2026-04-24T09:00:00Z", "2026-04-24T12:00:00Z")


def test_intraday_config_defaults_and_partial_merge() -> None:
    cfg = resolve_independence_intraday_config({"independence_release": {"intraday": {"frequency_hours": 6}}})
    assert cfg == {
        "frequency_hours": 6,
        "min_phase_confidence_for_monitoring": 55.0,
        "enable_reset_check": False,
        "max_execution_subset_size": None,
    }


@pytest.mark.parametrize("value", [5, "4", True, 0])
def test_intraday_frequency_validation(value) -> None:
    with pytest.raises(ValueError, match="frequency_hours"):
        resolve_independence_intraday_config({"independence_release": {"intraday": {"frequency_hours": value}}})


def test_intraday_runner_no_new_bar_noop_when_no_refresh_required(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
        }
    ]

    conn = init_db("data/independence_release.sqlite")
    conn.execute(
        "INSERT INTO run_metadata(run_id, scan_mode, started_at_utc, finished_at_utc, daily_bar_id, intraday_bar_id, schema_version, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("r1", "intraday", "2026-04-24T09:00:00Z", "2026-04-24T09:01:00Z", "2026-04-23", "2026-04-24T08:00:00Z", 4, "completed"),
    )
    conn.commit()
    conn.close()

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))


def test_intraday_runner_safety_limit_hard_fails(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg({"independence_release": {"intraday": {"max_execution_subset_size": 1}}})
    daily_id = "2026-04-23"
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "early_ready",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 70.0,
            "priority_score": 80.0,
            "daily_cache_bar_id": daily_id,
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
        },
        {
            "symbol": "BBBUSDT",
            "state_machine_state": "confirmed_ready",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 80.0,
            "priority_score": 70.0,
            "daily_cache_bar_id": daily_id,
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
        },
    ]

    with pytest.raises(RuntimeError, match="max_execution_subset_size"):
        run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))


def test_intraday_noop_report_uses_active_config(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg({"independence_release": {"reports": {"recent_runs_limit": 7}}})
    cfg.intraday_context_provider = lambda _cfg, _daily: []  # type: ignore[attr-defined]

    seen: dict[str, object] = {}

    class _DummyBuilder:
        def write_run_report(self, **kwargs):
            seen["called"] = True
            seen["kwargs"] = kwargs
            return {}

    def _fake_make_report_builder(*, project_root, config):
        seen["project_root"] = project_root
        seen["config"] = config
        return _DummyBuilder()

    monkeypatch.setattr(intraday_runner, "make_report_builder", _fake_make_report_builder)
    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))

    assert seen["called"] is True
    cfg_used = seen["config"]
    assert isinstance(cfg_used, dict)
    assert cfg_used["independence_release"]["reports"]["recent_runs_limit"] == 7
    kwargs = seen["kwargs"]
    assert isinstance(kwargs, dict)
    manifest_path = kwargs["manifest_path"]
    assert manifest_path.endswith("/run.manifest.json")
    assert manifest_path.startswith("snapshots/runs/")
    assert "reports/runs" not in manifest_path


def test_intraday_context_rejects_non_legacy_non_canonical_cache_bar_ids(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "NOT_A_CANONICAL_BAR_ID",
        }
    ]

    with pytest.raises(ValueError, match="current_bar_id"):
        run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))


def test_intraday_runner_accepts_legacy_digit_string_previous_bar_id(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
        }
    ]

    conn = init_db("data/independence_release.sqlite")
    conn.execute(
        "INSERT INTO run_metadata(run_id, scan_mode, started_at_utc, finished_at_utc, daily_bar_id, intraday_bar_id, schema_version, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("r1", "intraday", "2026-04-24T09:00:00Z", "2026-04-24T09:01:00Z", "2026-04-23", "1774324800000", 4, "completed"),
    )
    conn.commit()
    conn.close()

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))


def test_intraday_runner_rejects_legacy_integer_cache_bar_id(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": 1774324800000,
        }
    ]

    with pytest.raises(TypeError, match="intraday_cache_bar_id"):
        run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))


def test_intraday_runner_rejects_legacy_digit_string_cache_bar_id(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "market_phase_confidence": 40.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "1774324800000",
        }
    ]

    with pytest.raises(ValueError, match="current_bar_id"):
        run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))
