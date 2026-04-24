from __future__ import annotations

import pytest

import scanner.main as main_module
from scanner.config import ScannerConfig


def _cfg(run_mode: str) -> ScannerConfig:
    return ScannerConfig(raw={"general": {"run_mode": run_mode}})


def test_dispatch_uses_config_run_mode_when_no_cli_override(monkeypatch) -> None:
    calls: list[str] = []
    monkeypatch.setattr(main_module, "load_config", lambda: _cfg("intraday_promotion"))
    monkeypatch.setattr(main_module, "run_intraday_scan", lambda _cfg: calls.append("intraday"))
    monkeypatch.setattr(main_module, "run_daily_scan", lambda _cfg: calls.append("daily"))

    rc = main_module.main([])
    assert rc == 0
    assert calls == ["intraday"]


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
