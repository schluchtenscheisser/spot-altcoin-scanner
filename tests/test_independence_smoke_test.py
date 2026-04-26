from __future__ import annotations

import gzip
import json
import os
from pathlib import Path

import pytest

from scripts import run_independence_smoke_test as smoke


def _write_gz_jsonl(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, sort_keys=True) + "\n")


def _install_fake_pipeline(monkeypatch: pytest.MonkeyPatch, capture: dict[str, str]) -> None:
    class _FakeMexcClient:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        def get_exchange_info(self, use_cache: bool = False) -> dict[str, object]:
            return {"use_cache": use_cache, "symbols": []}

    def fake_fetch_closed_bars(*, symbol: str, timeframe: str, now: object, lookback_bars: int | None = None):
        _ = (symbol, timeframe, now, lookback_bars)
        capture["provider_seen_scanner_config_path"] = str(Path(os.environ["SCANNER_CONFIG_PATH"]).resolve())
        capture["provider_seen_cwd"] = Path.cwd().as_posix()

        class _Result:
            bars: list[object] = []
            last_fetch_status = "error_transport"
            last_error_code = "transport"

        return _Result()

    def fake_run_daily_scan(cfg, as_of_date: str | None = None) -> None:
        daily = str(as_of_date)
        y, m, d = daily.split("-")
        run_id = f"daily-{daily}-fake"

        # trigger provider call after chdir(workdir)
        cfg.daily_ohlcv_provider("SOLUSDT", "1d")

        manifest = Path("snapshots") / "runs" / y / m / d / run_id / "run.manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"run_id": run_id, "daily_bar_id": daily}) + "\n", encoding="utf-8")

        diagnostics = Path("reports") / "runs" / y / m / d / run_id / "symbol_diagnostics.jsonl.gz"
        _write_gz_jsonl(
            diagnostics,
            [
                {
                    "symbol": "SOLUSDT",
                    "daily_bar_id": daily,
                    "intraday_bar_id": None,
                    "as_of_utc": "2026-04-25T00:00:00Z",
                }
            ],
        )

        report = Path("reports") / "runs" / y / m / d / run_id / "report.json"
        report.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "daily_bar_id": daily,
                    "diagnostics_path": diagnostics.as_posix(),
                    "scan_mode": "daily",
                    "intraday_bar_id": None,
                }
            )
            + "\n",
            encoding="utf-8",
        )

    def fake_run_intraday_scan(cfg, now_utc=None) -> None:
        _ = (cfg, now_utc)
        run_id = "intraday-2026-04-24-fake"
        manifest = Path("snapshots") / "runs" / "2026" / "04" / "24" / run_id / "run.manifest.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"run_id": run_id}) + "\n", encoding="utf-8")
        report = Path("reports") / "runs" / "2026" / "04" / "24" / run_id / "report.json"
        report.parent.mkdir(parents=True, exist_ok=True)
        report.write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "intraday_bar_id": "2026-04-25T12:00:00Z",
                    "scan_mode": "intraday",
                    "daily_bar_id": "2026-04-24",
                    "manifest_path": manifest.as_posix(),
                }
            )
            + "\n",
            encoding="utf-8",
        )
        _write_gz_jsonl(report.parent / "symbol_diagnostics.jsonl.gz", [])

    def fake_run_evaluation_export(*, project_root: Path, config: dict[str, object] | None = None) -> dict[str, object]:
        _ = config
        out = project_root / "evaluation" / "exports" / "evaluation_summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"cycle_count": 0}) + "\n", encoding="utf-8")
        return {"cycle_count": 0}

    monkeypatch.setattr(smoke, "MEXCClient", _FakeMexcClient)
    monkeypatch.setattr(smoke, "fetch_closed_bars", fake_fetch_closed_bars)
    monkeypatch.setattr(smoke, "run_daily_scan", fake_run_daily_scan)
    monkeypatch.setattr(smoke, "run_intraday_scan", fake_run_intraday_scan)
    monkeypatch.setattr(smoke, "run_evaluation_export", fake_run_evaluation_export)


def test_smoke_main_exports_absolute_config_path_when_env_unset(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("SCANNER_CONFIG_PATH", raising=False)
    monkeypatch.delenv("GITHUB_WORKSPACE", raising=False)

    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )

    rc = smoke.main()
    assert rc == 0

    expected = (smoke.REPO_ROOT / "config" / "config.yml").resolve()
    exported = Path(os.environ["SCANNER_CONFIG_PATH"]).resolve()

    assert exported.is_absolute()
    assert exported == expected
    assert capture["provider_seen_scanner_config_path"] == expected.as_posix()
    assert capture["provider_seen_cwd"] == workdir.resolve().as_posix()
    assert capture["provider_seen_scanner_config_path"] != str((workdir / "config" / "config.yml").resolve())


def test_smoke_main_preserves_absolute_scanner_config_path_env(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    custom_cfg = (tmp_path / "custom-config.yml").resolve()
    custom_cfg.write_text("general:\n  run_mode: fast\n", encoding="utf-8")
    monkeypatch.setenv("SCANNER_CONFIG_PATH", custom_cfg.as_posix())

    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            (tmp_path / "smoke-workdir").as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )

    rc = smoke.main()
    assert rc == 0
    assert Path(os.environ["SCANNER_CONFIG_PATH"]).resolve() == custom_cfg
    assert capture["provider_seen_scanner_config_path"] == custom_cfg.as_posix()


def test_resolve_config_path_uses_github_workspace_when_present(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("SCANNER_CONFIG_PATH", raising=False)
    monkeypatch.setenv("GITHUB_WORKSPACE", tmp_path.as_posix())

    resolved = Path(smoke._resolve_config_path())
    assert resolved == (tmp_path / "config" / "config.yml").resolve()
    assert resolved.is_absolute()


def test_daily_stage_exception_is_fail_not_skip(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)
    monkeypatch.setattr(smoke, "run_daily_scan", lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("boom")))

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )
    rc = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["steps"]["daily_runner"] == "FAIL"
    assert any("ValueError: boom" in err for err in payload["errors"])


def test_evaluation_stage_skip_only_when_no_run_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)
    monkeypatch.setattr(smoke, "run_daily_scan", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(smoke, "run_intraday_scan", lambda *_args, **_kwargs: None)

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )
    rc = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert payload["steps"]["evaluation_replay"] == "SKIP"


def test_smoke_summary_contains_per_symbol_skip_details(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )

    _ = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    symbol_diag = payload["per_symbol_diagnostics"]
    assert "SOLUSDT" in symbol_diag
    assert symbol_diag["SOLUSDT"]["1d_bar_count"] == 0
    assert symbol_diag["SOLUSDT"]["1d_fetch_status"] == "error_transport"
    assert symbol_diag["SOLUSDT"]["1d_error_code"] == "transport"
    assert isinstance(symbol_diag["AVAXUSDT"]["skip_reason"], str)


def test_smoke_summary_path_write_classification(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)
    workdir = tmp_path / "smoke-workdir"

    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )
    _ = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    assert "uploaded_artifact_candidates" in payload
    assert "allowed_workspace_log_writes" in payload
    assert "forbidden_path_writes" in payload
    assert payload["forbidden_path_writes"] == []


def test_workspace_logs_churn_is_allowed_not_forbidden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)
    workspace = tmp_path / "workspace"
    (workspace / "logs").mkdir(parents=True, exist_ok=True)
    log_file = workspace / "logs" / "scanner_2026-04-26.log"
    log_file.write_text("before\n", encoding="utf-8")
    monkeypatch.setenv("GITHUB_WORKSPACE", workspace.as_posix())
    monkeypatch.setenv("SCANNER_CONFIG_PATH", (smoke.REPO_ROOT / "config" / "config.yml").as_posix())

    original_daily = smoke.run_daily_scan

    def _daily_with_log_churn(cfg, as_of_date=None):
        original_daily(cfg, as_of_date=as_of_date)
        log_file.write_text("before\nafter\n", encoding="utf-8")

    monkeypatch.setattr(smoke, "run_daily_scan", _daily_with_log_churn)

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )
    rc = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    assert rc == 0
    assert "logs/scanner_2026-04-26.log" in payload["allowed_workspace_log_writes"]
    assert payload["forbidden_path_writes"] == []


def test_workspace_run_output_write_is_forbidden(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    capture: dict[str, str] = {}
    _install_fake_pipeline(monkeypatch, capture)
    workspace = tmp_path / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("GITHUB_WORKSPACE", workspace.as_posix())
    monkeypatch.setenv("SCANNER_CONFIG_PATH", (smoke.REPO_ROOT / "config" / "config.yml").as_posix())

    original_daily = smoke.run_daily_scan

    def _daily_with_forbidden_workspace_write(cfg, as_of_date=None):
        original_daily(cfg, as_of_date=as_of_date)
        forbidden = workspace / "reports" / "runs" / "oops.txt"
        forbidden.parent.mkdir(parents=True, exist_ok=True)
        forbidden.write_text("bad\n", encoding="utf-8")

    monkeypatch.setattr(smoke, "run_daily_scan", _daily_with_forbidden_workspace_write)

    workdir = tmp_path / "smoke-workdir"
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_independence_smoke_test.py",
            "--workdir",
            workdir.as_posix(),
            "--daily-bar-id",
            "2026-04-24",
            "--intraday-bar-id",
            "2026-04-25T12:00:00Z",
        ],
    )
    rc = smoke.main()
    payload = json.loads((workdir / "artifacts" / "smoke-test-report.json").read_text(encoding="utf-8"))
    assert rc == 1
    assert "reports/runs/oops.txt" in payload["forbidden_path_writes"]
