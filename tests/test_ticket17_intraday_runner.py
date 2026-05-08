from __future__ import annotations

from datetime import datetime, timezone
import gzip
import json
from pathlib import Path

import pytest

from scanner.config import ScannerConfig, resolve_independence_intraday_config
from scanner.data.bar_clock import get_last_closed_intraday_bar_id, has_new_intraday_bar
import scanner.runners.intraday as intraday_runner
from scanner.runners.intraday import run_intraday_scan
from scanner.storage import SCHEMA_VERSION, init_db


def _cfg(raw: dict | None = None) -> ScannerConfig:
    merged = {"independence_release": {}}
    if raw:
        merged["independence_release"].update(raw.get("independence_release", {}))
    return ScannerConfig(raw=merged)


def _load_intraday_diagnostics(tmp_path: Path) -> list[dict]:
    diag_paths = sorted((tmp_path / "reports" / "runs").glob("**/symbol_diagnostics.jsonl.gz"))
    assert len(diag_paths) == 1
    with gzip.open(diag_paths[0], "rt", encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


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


def test_intraday_run_metadata_schema_version_uses_storage_schema_version(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: []  # type: ignore[attr-defined]

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))

    conn = init_db("data/independence_release.sqlite")
    row = conn.execute(
        "SELECT schema_version FROM run_metadata WHERE scan_mode='intraday' ORDER BY started_at_utc DESC LIMIT 1"
    ).fetchone()
    conn.close()
    assert row is not None
    assert row[0] == SCHEMA_VERSION


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
            "market_phase": "pressure_build",
            "market_phase_confidence": 70.0,
            "priority_score": 80.0,
            "daily_cache_bar_id": daily_id,
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "resolved_setup_cycle_id": 1,
        },
        {
            "symbol": "BBBUSDT",
            "state_machine_state": "confirmed_ready",
            "decision_bucket": "watchlist",
            "market_phase": "pressure_build",
            "market_phase_confidence": 80.0,
            "priority_score": 70.0,
            "daily_cache_bar_id": daily_id,
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "resolved_setup_cycle_id": 2,
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
    manifest_file = tmp_path / manifest_path
    assert manifest_file.exists()
    reports_manifests = list((tmp_path / "reports" / "runs").glob("**/*.manifest.json"))
    assert reports_manifests == []


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


def test_intraday_report_manifest_path_points_to_existing_snapshot_manifest(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: []  # type: ignore[attr-defined]

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))
    report_paths = sorted((tmp_path / "reports" / "runs").glob("**/intraday-*/report.json"))
    assert len(report_paths) == 1
    report = json.loads(report_paths[0].read_text(encoding="utf-8"))
    manifest_path = report["manifest_path"]
    assert isinstance(manifest_path, str) and manifest_path
    assert manifest_path.startswith("snapshots/runs/")
    assert "reports/runs" not in manifest_path
    assert (tmp_path / manifest_path).exists()


def test_intraday_missing_cycle_context_is_not_executed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "priority_score": 55.0,
            "market_phase": "pressure_build",
            "market_phase_confidence": 60.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "setup_cycle_id": None,
            "current_setup_cycle_id": None,
            "resolved_setup_cycle_id": None,
        }
    ]
    seen_subset_symbols: list[str] = []
    monkeypatch.setattr(intraday_runner, "select_execution_subset", lambda rows, _execution: rows)
    monkeypatch.setattr(
        intraday_runner,
        "evaluate_execution_subset",
        lambda subset, _execution: (
            seen_subset_symbols.extend(str(getattr(r, "symbol", "")) for r in subset) or type("E", (), {"contracts": {}, "diagnostics": {}})()
        ),
    )

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))
    diagnostics = _load_intraday_diagnostics(tmp_path)
    assert len(diagnostics) == 1
    assert diagnostics[0]["execution_attempted"] is False
    assert diagnostics[0]["reasons"]["intraday_skip_reason"] == "missing_intraday_cycle_context"
    assert seen_subset_symbols == []


def test_intraday_missing_state_context_is_not_executed_and_non_discarded_decision_not_serialized(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": None,
            "decision_bucket": "watchlist",
            "priority_score": 0.0,
            "market_phase": "pressure_build",
            "market_phase_confidence": 0.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "resolved_setup_cycle_id": 5,
        }
    ]
    seen_subset_symbols: list[str] = []
    monkeypatch.setattr(intraday_runner, "select_execution_subset", lambda rows, _execution: rows)
    monkeypatch.setattr(
        intraday_runner,
        "evaluate_execution_subset",
        lambda subset, _execution: (
            seen_subset_symbols.extend(str(getattr(r, "symbol", "")) for r in subset) or type("E", (), {"contracts": {}, "diagnostics": {}})()
        ),
    )

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))
    diagnostics = _load_intraday_diagnostics(tmp_path)
    assert diagnostics[0]["decision"]["decision_bucket"] is None
    assert diagnostics[0]["execution_attempted"] is False
    assert diagnostics[0]["reasons"]["intraday_skip_reason"] == "missing_intraday_state_context"
    assert seen_subset_symbols == []


def test_intraday_discarded_without_state_is_valid_but_not_executed(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": None,
            "decision_bucket": "discarded",
            "priority_score": 0.0,
            "market_phase": "none",
            "market_phase_confidence": 60.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "resolved_setup_cycle_id": 9,
        }
    ]
    seen_subset_symbols: list[str] = []
    monkeypatch.setattr(intraday_runner, "select_execution_subset", lambda rows, _execution: rows)
    monkeypatch.setattr(
        intraday_runner,
        "evaluate_execution_subset",
        lambda subset, _execution: (
            seen_subset_symbols.extend(str(getattr(r, "symbol", "")) for r in subset) or type("E", (), {"contracts": {}, "diagnostics": {}})()
        ),
    )

    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))
    diagnostics = _load_intraday_diagnostics(tmp_path)
    assert diagnostics[0]["decision"]["decision_bucket"] == "discarded"
    assert diagnostics[0]["state"]["state_machine_state"] is None
    assert diagnostics[0]["execution_attempted"] is False
    assert diagnostics[0]["reasons"]["intraday_skip_reason"] == "missing_intraday_state_context"
    assert seen_subset_symbols == []


def test_intraday_complete_context_executes_and_attaches_execution_diagnostics(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir(parents=True, exist_ok=True)
    cfg = _cfg()
    cfg.intraday_context_provider = lambda _cfg, _daily: [  # type: ignore[attr-defined]
        {
            "symbol": "AAAUSDT",
            "state_machine_state": "watch",
            "decision_bucket": "watchlist",
            "priority_score": 0.0,
            "market_phase": "pressure_build",
            "market_phase_confidence": 0.0,
            "daily_cache_bar_id": "2026-04-23",
            "intraday_cache_bar_id": "2026-04-24T08:00:00Z",
            "resolved_setup_cycle_id": 1,
        }
    ]
    seen_subset_symbols: list[str] = []
    monkeypatch.setattr(intraday_runner, "select_execution_subset", lambda rows, _execution: rows)

    def _fake_evaluate(subset, _execution):
        seen_subset_symbols.extend(str(getattr(r, "symbol", "")) for r in subset)
        return type(
            "E",
            (),
            {
                "contracts": {},
                "diagnostics": {
                    "AAAUSDT": {
                        "execution_attempted": True,
                        "execution_status_raw": "ok",
                        "execution_reason_raw": None,
                        "execution_pass": True,
                        "execution_grade_t16": None,
                        "execution_fetch_duration_ms": 1,
                    }
                },
            },
        )()

    monkeypatch.setattr(intraday_runner, "evaluate_execution_subset", _fake_evaluate)
    run_intraday_scan(cfg, now_utc=datetime(2026, 4, 24, 10, 59, tzinfo=timezone.utc))

    diagnostics = _load_intraday_diagnostics(tmp_path)
    assert seen_subset_symbols == ["AAAUSDT"]
    assert diagnostics[0]["execution_attempted"] is True
    assert diagnostics[0]["execution_status_raw"] == "ok"
