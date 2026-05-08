from __future__ import annotations

import gzip
import json
from pathlib import Path

import pytest

import scanner.runners.daily as daily_runner_module
from scripts import run_independence_shadow_live as shadow


@pytest.fixture(autouse=True)
def _set_required_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CMC_API_KEY", "dummy")


def _write_gz_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def test_shadow_live_main_writes_summary_with_non_blocking_intraday_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fake_run_daily_scan(_cfg, as_of_date: str | None = None) -> None:
        assert as_of_date == "2026-04-24"
        run_id = "daily-2026-04-24-fake"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        diag = run_dir / "symbol_diagnostics.jsonl.gz"
        _write_gz_jsonl(diag, [{"symbol": "SOLUSDT", "daily_bar_id": "2026-04-24"}])
        manifest = tmp_path / "shadow-workdir" / "snapshots" / "runs" / "2026" / "04" / "24" / run_id / "run.manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("{}\n", encoding="utf-8")
        (run_dir / "report.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "scan_mode": "daily",
                    "daily_bar_id": "2026-04-24",
                    "diagnostics_path": "reports/runs/2026/04/24/daily-2026-04-24-fake/symbol_diagnostics.jsonl.gz",
                    "manifest_path": "snapshots/runs/2026/04/24/daily-2026-04-24-fake/run.manifest.json",
                    "counts_by_bucket": {"watchlist": 1, "early_candidates": 0, "confirmed_candidates": 0, "late_monitor": 0, "discarded": 0},
                    "symbol_lists": {"watchlist": ["SOLUSDT"], "early_candidates": [], "confirmed_candidates": [], "late_monitor": []},
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def fake_run_intraday_scan(_cfg, now_utc=None) -> None:
        _ = now_utc
        run_id = "intraday-2026-04-24-fake"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        _write_gz_jsonl(
            run_dir / "symbol_diagnostics.jsonl.gz",
            [{"execution_attempted": False, "reasons": {"intraday_skip_reason": "missing_intraday_cycle_context"}}],
        )
        (run_dir / "report.json").write_text(
            json.dumps({"diagnostics_path": f"reports/runs/2026/04/24/{run_id}/symbol_diagnostics.jsonl.gz"}) + "\n",
            encoding="utf-8",
        )

    def fake_run_eval(*, project_root: Path, config: dict[str, object] | None = None) -> dict[str, object]:
        _ = config
        replay = project_root / "evaluation" / "replay"
        exports = project_root / "evaluation" / "exports"
        replay.mkdir(parents=True, exist_ok=True)
        exports.mkdir(parents=True, exist_ok=True)
        (replay / "event_timeline.jsonl").write_text("{}\n", encoding="utf-8")
        (exports / "evaluation_summary.json").write_text(json.dumps({"cycle_count": 0}) + "\n", encoding="utf-8")
        return {"cycle_count": 0}

    def fake_build_real_daily_providers(*, cfg, now_utc):
        _ = (cfg, now_utc)
        return (
            ["SOLUSDT"],
            lambda _cfg, _daily_id: ["SOLUSDT"],
            lambda _symbol, _tf: [],
        )

    monkeypatch.setattr(shadow, "_build_real_daily_providers", fake_build_real_daily_providers)
    monkeypatch.setattr(shadow, "run_daily_scan", fake_run_daily_scan)
    monkeypatch.setattr(shadow, "run_intraday_scan", fake_run_intraday_scan)
    monkeypatch.setattr(shadow, "run_evaluation_export", fake_run_eval)
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_shadow_live.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-24T20:00:00Z",
        ],
    )

    monkeypatch.setenv("STATE_RESTORE_STATUS", "restored")

    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))
    manifest_payload = json.loads(
        (workdir / "snapshots" / "runs" / "2026" / "04" / "24" / "daily-2026-04-24-fake" / "run.manifest.json").read_text(
            encoding="utf-8"
        )
    )

    assert rc == 0
    assert payload["status"] == "pass"
    assert payload["daily"]["status"] == "pass"
    assert payload["evaluation_replay"]["status"] == "pass"
    assert payload["intraday"]["status"] == "non_blocking_warning"
    assert payload["intraday"]["known_state"] == "missing_intraday_cycle_context"
    assert payload["state_restore_status"] == "restored"
    assert manifest_payload["state_restore_status"] == "restored"


def test_shadow_live_attaches_daily_providers_before_daily_scan(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_build_real_daily_providers(*, cfg, now_utc):
        _ = now_utc
        return (
            ["SOLUSDT"],
            lambda _cfg, _daily_id: ["SOLUSDT"],
            lambda _symbol, _tf: [],
        )

    def fake_run_daily_scan(cfg, as_of_date: str | None = None) -> None:
        _ = as_of_date
        assert getattr(cfg, "daily_universe_provider", None) is not None
        assert getattr(cfg, "daily_ohlcv_provider", None) is not None
        assert getattr(cfg, "daily_universe_provider") is not daily_runner_module._default_universe
        assert getattr(cfg, "daily_ohlcv_provider") is not daily_runner_module._default_ohlcv
        run_id = "daily-2026-04-24-fake"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        diag = run_dir / "symbol_diagnostics.jsonl.gz"
        _write_gz_jsonl(diag, [{"symbol": "SOLUSDT"}])
        manifest = tmp_path / "shadow-workdir" / "snapshots" / "runs" / "2026" / "04" / "24" / run_id / "run.manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text("{}\n", encoding="utf-8")
        (run_dir / "report.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "diagnostics_path": "reports/runs/2026/04/24/daily-2026-04-24-fake/symbol_diagnostics.jsonl.gz",
                    "manifest_path": "snapshots/runs/2026/04/24/daily-2026-04-24-fake/run.manifest.json",
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def fake_eval(*, project_root: Path, config=None):
        _ = config
        (project_root / "evaluation" / "replay").mkdir(parents=True, exist_ok=True)
        (project_root / "evaluation" / "exports").mkdir(parents=True, exist_ok=True)
        (project_root / "evaluation" / "replay" / "event_timeline.jsonl").write_text("{}\n", encoding="utf-8")
        (project_root / "evaluation" / "exports" / "evaluation_summary.json").write_text(json.dumps({"cycle_count": 1}) + "\n", encoding="utf-8")
        return {"cycle_count": 1}

    monkeypatch.setattr(shadow, "_build_real_daily_providers", fake_build_real_daily_providers)
    monkeypatch.setattr(shadow, "run_daily_scan", fake_run_daily_scan)
    monkeypatch.setattr(shadow, "run_intraday_scan", lambda *args, **kwargs: None)
    monkeypatch.setattr(shadow, "run_evaluation_export", fake_eval)
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr("sys.argv", ["run_independence_shadow_live.py", "--workdir", workdir.as_posix(), "--daily-bar-id", "2026-04-24", "--skip-intraday"])
    rc = shadow.main()
    assert rc == 0


def test_shadow_live_fails_preflight_without_provider_wiring(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shadow, "_build_real_daily_providers", lambda **kwargs: ([], daily_runner_module._default_universe, daily_runner_module._default_ohlcv))
    monkeypatch.setattr(shadow, "run_daily_scan", lambda *_args, **_kwargs: pytest.fail("run_daily_scan should not be called when preflight fails"))
    monkeypatch.setattr(shadow, "run_intraday_scan", lambda *args, **kwargs: None)
    monkeypatch.setattr(shadow, "run_evaluation_export", lambda **kwargs: {})
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr("sys.argv", ["run_independence_shadow_live.py", "--workdir", workdir.as_posix(), "--daily-bar-id", "2026-04-24", "--skip-intraday"])
    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert any("EMPTY_REAL_DAILY_UNIVERSE" in err for err in payload["errors"])


@pytest.mark.parametrize(
    ("diag_value", "manifest_value"),
    [
        (None, "snapshots/runs/2026/04/24/daily-x/run.manifest.json"),
        ("", "snapshots/runs/2026/04/24/daily-x/run.manifest.json"),
        ("   ", "snapshots/runs/2026/04/24/daily-x/run.manifest.json"),
        ("reports/runs/../../evil.json", "snapshots/runs/2026/04/24/daily-x/run.manifest.json"),
        ("/tmp/absolute.json", "snapshots/runs/2026/04/24/daily-x/run.manifest.json"),
        ("reports/runs/2026/04/24/daily-x/symbol_diagnostics.jsonl.gz", ""),
    ],
)
def test_shadow_live_daily_report_path_validation_is_blocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, diag_value, manifest_value
) -> None:
    def fake_build_real_daily_providers(*, cfg, now_utc):
        _ = (cfg, now_utc)
        return (["SOLUSDT"], lambda _cfg, _daily_id: ["SOLUSDT"], lambda _symbol, _tf: [])

    def fake_daily(_cfg, as_of_date: str | None = None) -> None:
        _ = as_of_date
        run_id = "daily-x"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        report = {"run_id": run_id}
        if diag_value is not None:
            report["diagnostics_path"] = diag_value
        if manifest_value is not None:
            report["manifest_path"] = manifest_value
        (run_dir / "report.json").write_text(json.dumps(report) + "\n", encoding="utf-8")

    monkeypatch.setattr(shadow, "_build_real_daily_providers", fake_build_real_daily_providers)
    monkeypatch.setattr(shadow, "run_daily_scan", fake_daily)
    monkeypatch.setattr(shadow, "run_intraday_scan", lambda *args, **kwargs: None)
    monkeypatch.setattr(shadow, "run_evaluation_export", lambda **kwargs: (_ for _ in ()).throw(AssertionError("evaluation should not run on blocking daily failure")))
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr("sys.argv", ["run_independence_shadow_live.py", "--workdir", workdir.as_posix(), "--daily-bar-id", "2026-04-24", "--skip-intraday"])
    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["daily"]["status"] == "fail"


def test_shadow_live_daily_report_paths_must_point_to_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_build_real_daily_providers(*, cfg, now_utc):
        _ = (cfg, now_utc)
        return (["SOLUSDT"], lambda _cfg, _daily_id: ["SOLUSDT"], lambda _symbol, _tf: [])

    def fake_daily(_cfg, as_of_date: str | None = None) -> None:
        _ = as_of_date
        run_id = "daily-x"
        run_dir = tmp_path / "shadow-workdir" / "reports" / "runs" / "2026" / "04" / "24" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        diagnostics_rel = "reports/runs/2026/04/24/daily-x"
        manifest_rel = "snapshots/runs/2026/04/24/daily-x"
        (tmp_path / "shadow-workdir" / diagnostics_rel).mkdir(parents=True, exist_ok=True)
        (tmp_path / "shadow-workdir" / manifest_rel).mkdir(parents=True, exist_ok=True)
        (run_dir / "report.json").write_text(
            json.dumps({"run_id": run_id, "diagnostics_path": diagnostics_rel, "manifest_path": manifest_rel}) + "\n",
            encoding="utf-8",
        )

    monkeypatch.setattr(shadow, "_build_real_daily_providers", fake_build_real_daily_providers)
    monkeypatch.setattr(shadow, "run_daily_scan", fake_daily)
    monkeypatch.setattr(shadow, "run_intraday_scan", lambda *args, **kwargs: None)
    monkeypatch.setattr(shadow, "run_evaluation_export", lambda **kwargs: (_ for _ in ()).throw(AssertionError("evaluation should not run on blocking daily failure")))
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr("sys.argv", ["run_independence_shadow_live.py", "--workdir", workdir.as_posix(), "--daily-bar-id", "2026-04-24", "--skip-intraday"])
    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["daily"]["status"] == "fail"


def test_shadow_live_empty_real_universe_is_blocking(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shadow, "_build_real_daily_providers", lambda **kwargs: ([], lambda *_a, **_k: [], lambda *_a, **_k: []))
    monkeypatch.setattr(shadow, "run_daily_scan", lambda *_args, **_kwargs: pytest.fail("daily should not run on empty universe"))
    monkeypatch.setattr(shadow, "run_intraday_scan", lambda *args, **kwargs: None)
    monkeypatch.setattr(shadow, "run_evaluation_export", lambda **kwargs: {})
    monkeypatch.setattr(shadow, "MEXCClient", lambda *args, **kwargs: type("C", (), {"get_exchange_info": lambda self, **kw: {}})())

    workdir = tmp_path / "shadow-workdir"
    monkeypatch.setattr("sys.argv", ["run_independence_shadow_live.py", "--workdir", workdir.as_posix(), "--daily-bar-id", "2026-04-24", "--skip-intraday"])
    rc = shadow.main()
    payload = json.loads((workdir / "shadow-live-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert any("EMPTY_REAL_DAILY_UNIVERSE" in err for err in payload["errors"])


def test_shadow_live_workdir_disallows_reports_analysis(tmp_path: Path) -> None:
    workdir = tmp_path / "shadow"
    target = workdir / "reports" / "analysis" / "x.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("{}\n", encoding="utf-8")

    forbidden = shadow._collect_forbidden_writes(workdir)
    assert "reports/analysis/x.json" in forbidden


def test_shadow_live_accepts_cold_start_reset_restore_status(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STATE_RESTORE_STATUS", "cold_start_reset")
    assert shadow._state_restore_status_from_env() == "cold_start_reset"

    manifest = tmp_path / "run.manifest.json"
    manifest.write_text("{}\n", encoding="utf-8")
    shadow._annotate_manifest_state_restore_status(manifest, "cold_start_reset")
    assert json.loads(manifest.read_text(encoding="utf-8"))["state_restore_status"] == "cold_start_reset"
