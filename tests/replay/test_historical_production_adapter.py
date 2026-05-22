from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import pytest

from scanner.evaluation.historical_replay.production_adapter import HistoricalProductionAdapter, _build_bar_clock_context, _state_ctx


def _bars() -> pd.DataFrame:
    return pd.DataFrame([
        {"close_time_utc_ms": 1, "close": 10.0, "high": 11.0, "low": 9.0, "volume": 1.0, "quote_volume": 10.0},
        {"close_time_utc_ms": 2, "close": 10.5, "high": 11.5, "low": 9.5, "volume": 1.1, "quote_volume": 11.0},
    ])


def test_bar_clock_context_daily_only() -> None:
    ctx = _build_bar_clock_context("2025-01-01", {"close_time_utc": "2025-01-01T23:59:59Z"})
    assert ctx["daily_bar_id"] == "2025-01-01"
    assert isinstance(ctx["daily_close_time_utc_ms"], int)
    assert "intraday_bar_id" not in ctx

    ctx_ms = _build_bar_clock_context("2025-01-01", {"close_time_utc_ms": 123, "close_time_utc": "2025-01-01T23:59:59Z"})
    assert ctx_ms["daily_close_time_utc_ms"] == 123


def test_state_ctx_bootstrap_and_validation() -> None:
    assert _state_ctx("AAAUSDT", {}).symbol == "AAAUSDT"
    with pytest.raises(ValueError):
        _state_ctx("AAAUSDT", {"state_machine_state": "bad_state"})
    with pytest.raises(ValueError):
        _state_ctx("AAAUSDT", {"bars_since_state_entered": -1})
    with pytest.raises(ValueError):
        _state_ctx("AAAUSDT", {"last_aging_daily_bar_id": "20250101"})


def test_adapter_mapping_with_stubs(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    adapter = HistoricalProductionAdapter()

    @dataclass
    class StubPhase:
        market_phase: str = "trend_resume"
        market_phase_confidence: float = 80.0

    @dataclass
    class Disp:
        admitted: bool = True
        disposition_reason: str | None = "OK"

    @dataclass
    class Patch:
        setup_cycle_id: int = 5

    class State:
        disposition = Disp()
        state_machine_state = "confirmed_ready"
        state_confidence = 90.0
        state_transition_reason = "PROMOTE"
        persistence_patch = Patch()

    @dataclass
    class Entry:
        entry_pattern: str = "range_reclaim"
        entry_pattern_score: float = 77.0

    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.load_config", lambda *_: object())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.build_feature_bundle", lambda **_: object())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.compute_tier1_axes", lambda *_: object())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.compute_tier2_axes", lambda *_: object())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.compute_phase_interpretation", lambda *_: StubPhase())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.compute_invalidation_and_cycle", lambda *_: object())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.compute_state_machine", lambda *_: State())
    monkeypatch.setattr("scanner.evaluation.historical_replay.production_adapter.resolve_entry_pattern", lambda *_: Entry())

    out = adapter(symbol="AAAUSDT", as_of_daily_bar_id="2025-01-01", closed_1d_bars=_bars(), closed_4h_bars=_bars(), persisted_state={"state_machine_state": "early_ready"}, scanner_config={"ref": (tmp_path / "config.yml").as_posix()})
    assert out.market_phase == "trend_resume"
    assert out.state_machine_state == "confirmed_ready"
    assert out.entry_pattern == "range_reclaim"
    assert out.signal_daily_close == 10.5
    assert out.transition_event_types == ["first_confirmed_ready", "first_confirmed_with_entry_pattern"]
