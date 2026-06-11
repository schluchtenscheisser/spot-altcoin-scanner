from __future__ import annotations

import pytest

import scanner.main as main_module
from scanner.config import ScannerConfig
from scanner.run_modes import (
    resolve_cli_mode_to_run_metadata_scan_mode,
    resolve_cli_mode_to_runner,
    resolve_run_metadata_scan_mode_to_report_scan_mode,
)


def _cfg(run_mode: str) -> ScannerConfig:
    return ScannerConfig(raw={"general": {"run_mode": run_mode}})


@pytest.mark.parametrize(
    ("input_mode", "runner_target", "metadata_scan_mode", "report_scan_mode"),
    [
        ("daily_discovery", "daily", "daily_discovery", "daily"),
        ("intraday_promotion", "intraday", "intraday_promotion", "intraday"),
        ("standard", "daily", "daily_discovery", "daily"),
        ("fast", "daily", "daily_discovery", "daily"),
        ("offline", "daily", "daily_discovery", "daily"),
        ("backtest", "daily", "daily_discovery", "daily"),
    ],
)
def test_canonical_run_mode_mapping_table(
    input_mode: str,
    runner_target: str,
    metadata_scan_mode: str,
    report_scan_mode: str,
) -> None:
    assert resolve_cli_mode_to_runner(input_mode) == runner_target
    assert resolve_cli_mode_to_run_metadata_scan_mode(input_mode) == metadata_scan_mode
    assert resolve_run_metadata_scan_mode_to_report_scan_mode(metadata_scan_mode) == report_scan_mode


def test_dispatch_uses_config_run_mode_when_no_cli_override(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg("intraday_promotion"))
    monkeypatch.setattr(main_module, "run_intraday_scan", lambda _cfg: calls.append("intraday"))
    monkeypatch.setattr(main_module, "run_daily_scan", lambda _cfg: calls.append("daily"))

    rc = main_module.main([])
    assert rc == 0
    assert calls == ["intraday"]


@pytest.mark.parametrize("alias", ["standard", "fast", "offline", "backtest"])
def test_compatibility_aliases_dispatch_to_daily_runner(monkeypatch, alias: str) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg(alias))
    monkeypatch.setattr(main_module, "run_intraday_scan", lambda _cfg: calls.append("intraday"))
    monkeypatch.setattr(main_module, "run_daily_scan", lambda _cfg: calls.append("daily"))

    rc = main_module.main([])
    assert rc == 0
    assert calls == ["daily"]


def test_cli_override_wins_daily_to_intraday(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg("daily_discovery"))
    monkeypatch.setattr(main_module, "run_intraday_scan", lambda _cfg: calls.append("intraday"))
    monkeypatch.setattr(main_module, "run_daily_scan", lambda _cfg: calls.append("daily"))

    rc = main_module.main(["--mode", "intraday_promotion"])
    assert rc == 0
    assert calls == ["intraday"]


def test_cli_override_wins_intraday_to_daily(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg("intraday_promotion"))
    monkeypatch.setattr(main_module, "run_intraday_scan", lambda _cfg: calls.append("intraday"))
    monkeypatch.setattr(main_module, "run_daily_scan", lambda _cfg: calls.append("daily"))

    rc = main_module.main(["--mode", "daily_discovery"])
    assert rc == 0
    assert calls == ["daily"]


def test_invalid_effective_run_mode_fails_fast(monkeypatch) -> None:
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg("not_a_real_mode"))
    with pytest.raises(ValueError, match="invalid run_mode"):
        main_module.main([])
