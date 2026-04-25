from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

import pytest

from scanner.config import ScannerConfig
import scanner.runners.daily as daily_runner
from scanner.runners.daily import run_daily_scan
from scanner.state.models import (
    InvalidationCycleBundle,
    PersistedStateMachineContext,
    StateEvaluationDisposition,
    StateFreshnessBundle,
    StateMachineBundle,
    StatePersistencePatch,
)
from scanner.storage import init_db


@dataclass(frozen=True)
class _Bar:
    close_time_utc_ms: int
    close: float
    high: float = 1.0
    low: float = 1.0
    base_volume: float = 1.0
    quote_volume: float = 1.0


def _cfg() -> ScannerConfig:
    return ScannerConfig(raw={"independence_release": {}, "runner": {}})


def test_as_of_date_invalid_format_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        run_daily_scan(_cfg(), as_of_date="2026/01/01")


def test_as_of_date_future_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ValueError, match="past date"):
        run_daily_scan(_cfg(), as_of_date="2999-01-01")


def test_empty_universe_non_publishable_minimal_artifacts(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg()
    cfg.daily_universe_provider = lambda *_: []

    run_daily_scan(cfg, as_of_date="2026-01-01")

    conn = init_db("data/independence_release.sqlite")
    row = conn.execute("SELECT status, daily_bar_id, scan_mode FROM run_metadata ORDER BY started_at_utc DESC LIMIT 1").fetchone()
    assert row is not None
    assert row[0] == "completed"
    assert row[1] == "2026-01-01"
    assert row[2] == "daily"

    run_reports = list((tmp_path / "reports" / "runs" / "2026" / "01" / "01").glob("*/report.json"))
    assert len(run_reports) == 1
    report = json.loads(run_reports[0].read_text(encoding="utf-8"))
    assert report["candidate_count"] == 0

    assert not (tmp_path / "reports" / "index").exists()
    assert not (tmp_path / "reports" / "daily").exists()


def test_runtime_context_uses_real_bar_data(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg()
    cfg.daily_universe_provider = lambda *_: ["BTCUSDT"]

    bars_1d = [_Bar(close_time_utc_ms=100, close=10.0), _Bar(close_time_utc_ms=200, close=11.0)]
    bars_4h = [_Bar(close_time_utc_ms=500, close=20.0), _Bar(close_time_utc_ms=600, close=21.0)]
    cfg.daily_ohlcv_provider = lambda _symbol, tf: bars_4h if tf == "4h" else bars_1d

    monkeypatch.setattr(daily_runner, "build_feature_bundle", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier1_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier2_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_phase_interpretation", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_invalidation_and_cycle", lambda *_args, **_kwargs: InvalidationCycleBundle(
        symbol="BTCUSDT",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=True,
        structural_invalidation=False,
        structural_invalidation_reason=None,
        timing_invalidation=False,
        timing_invalidation_reason=None,
        new_cycle_detected=False,
        cycle_reason_code="FIRST_CYCLE_INITIALIZED",
        resolved_setup_cycle_id=1,
        phase_floor_recovered_since_cycle_end=False,
        expansion_reset_condition_met=None,
        reclaim_reset_condition_met=None,
    ))
    monkeypatch.setattr(daily_runner, "load_persisted_state_machine_context", lambda *_args, **_kwargs: PersistedStateMachineContext(
        symbol="BTCUSDT",
        current_setup_cycle_id=None,
        previous_setup_cycle_id=None,
        state_recorded_in_cycle_id=None,
        prev_state_machine_state=None,
        freshness_distance_state_early=None,
        freshness_distance_state_confirmed=None,
        bars_since_state_entered=None,
        bars_since_early_entered=None,
        bars_since_confirmed_entered=None,
        bars_since_cycle_end=None,
        reclaim_below_reset_floor_seen_since_cycle_end=None,
        close_at_early_entry_bar=None,
        close_at_confirmed_entry_bar=None,
        distance_from_ideal_entry_after_early=None,
        distance_from_ideal_entry_after_confirmed=None,
        cycle_end_bar_index=None,
        cycle_end_timestamp=None,
    ))

    seen = {}
    def _fake_state_machine(_p, _t1, _t2, _inv, _persisted, runtime_context, _cfg):
        seen["close"] = runtime_context.current_close
        seen["bar_index"] = runtime_context.current_bar_index
        seen["delta"] = runtime_context.delta_closed_bars_relevant
        return StateMachineBundle(
            symbol="BTCUSDT",
            daily_bar_id="2026-01-01",
            intraday_bar_id=None,
            data_4h_available=True,
            disposition=StateEvaluationDisposition(admitted=True, disposition_reason=None),
            state_machine_state="watch",
            state_confidence=50.0,
            state_transition_reason="STATE_HOLD",
            data_resolution_class="full_1d_4h",
            freshness=StateFreshnessBundle(None, None, None, None),
            persistence_patch=None,
        )

    monkeypatch.setattr(daily_runner, "compute_state_machine", _fake_state_machine)
    monkeypatch.setattr(daily_runner, "resolve_entry_pattern", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "assign_bucket", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "rank_coins", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(daily_runner, "make_report_builder", lambda *_args, **_kwargs: type("B", (), {"write_run_report": lambda *_a, **_k: {"daily_bar_id":"2026-01-01"}, "write_daily_report": lambda *_a, **_k: None})())
    monkeypatch.setattr(daily_runner, "_persist_run_manifest", lambda *_args, **_kwargs: "snapshots/runs/x/run.manifest.json")

    run_daily_scan(cfg, as_of_date="2026-01-01")
    assert seen == {"close": 21.0, "bar_index": 600, "delta": 6}


def test_no_state_persist_when_symbol_fails_after_t10(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg()
    cfg.daily_universe_provider = lambda *_: ["BTCUSDT"]
    cfg.daily_ohlcv_provider = lambda *_: [_Bar(close_time_utc_ms=100, close=10.0)]

    monkeypatch.setattr(daily_runner, "build_feature_bundle", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier1_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier2_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_phase_interpretation", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_invalidation_and_cycle", lambda *_args, **_kwargs: InvalidationCycleBundle(
        symbol="BTCUSDT",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=True,
        structural_invalidation=False,
        structural_invalidation_reason=None,
        timing_invalidation=False,
        timing_invalidation_reason=None,
        new_cycle_detected=False,
        cycle_reason_code="FIRST_CYCLE_INITIALIZED",
        resolved_setup_cycle_id=1,
        phase_floor_recovered_since_cycle_end=False,
        expansion_reset_condition_met=None,
        reclaim_reset_condition_met=None,
    ))
    monkeypatch.setattr(daily_runner, "load_persisted_state_machine_context", lambda *_args, **_kwargs: PersistedStateMachineContext(
        symbol="BTCUSDT",
        current_setup_cycle_id=None,
        previous_setup_cycle_id=None,
        state_recorded_in_cycle_id=None,
        prev_state_machine_state=None,
        freshness_distance_state_early=None,
        freshness_distance_state_confirmed=None,
        bars_since_state_entered=None,
        bars_since_early_entered=None,
        bars_since_confirmed_entered=None,
        bars_since_cycle_end=None,
        reclaim_below_reset_floor_seen_since_cycle_end=None,
        close_at_early_entry_bar=None,
        close_at_confirmed_entry_bar=None,
        distance_from_ideal_entry_after_early=None,
        distance_from_ideal_entry_after_confirmed=None,
        cycle_end_bar_index=None,
        cycle_end_timestamp=None,
    ))
    patch = StatePersistencePatch(
        symbol="BTCUSDT",
        setup_cycle_id=1,
        previous_setup_cycle_id=None,
        state_recorded_in_cycle_id=1,
        state_machine_state="watch",
        state_confidence=50.0,
        state_transition_reason="STATE_HOLD",
        bars_since_state_entered=0,
        bars_since_early_entered=None,
        bars_since_confirmed_entered=None,
        bars_since_cycle_end=None,
        close_at_early_entry_bar=None,
        close_at_confirmed_entry_bar=None,
        distance_from_ideal_entry_after_early=None,
        distance_from_ideal_entry_after_confirmed=None,
        freshness_distance_state_early=None,
        freshness_distance_state_confirmed=None,
        cycle_end_bar_index=None,
        cycle_end_timestamp=None,
        reclaim_below_reset_floor_seen_since_cycle_end=None,
        data_resolution_class="full_1d_4h",
    )
    monkeypatch.setattr(daily_runner, "compute_state_machine", lambda *_args, **_kwargs: StateMachineBundle(
        symbol="BTCUSDT",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=True,
        disposition=StateEvaluationDisposition(admitted=True, disposition_reason=None),
        state_machine_state="watch",
        state_confidence=50.0,
        state_transition_reason="STATE_HOLD",
        data_resolution_class="full_1d_4h",
        freshness=StateFreshnessBundle(None, None, None, None),
        persistence_patch=patch,
    ))

    monkeypatch.setattr(daily_runner, "resolve_entry_pattern", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("entry fail")))
    apply_calls: list[str] = []
    monkeypatch.setattr(daily_runner, "apply_state_persistence_patch", lambda *_args, **_kwargs: apply_calls.append("called"))
    monkeypatch.setattr(daily_runner, "rank_coins", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(daily_runner, "make_report_builder", lambda *_args, **_kwargs: type("B", (), {"write_run_report": lambda *_a, **_k: {"daily_bar_id":"2026-01-01"}, "write_daily_report": lambda *_a, **_k: None})())
    monkeypatch.setattr(daily_runner, "_persist_run_manifest", lambda *_args, **_kwargs: "snapshots/runs/x/run.manifest.json")

    run_daily_scan(cfg, as_of_date="2026-01-01")
    assert apply_calls == []


def test_daily_diagnostics_use_real_data_4h_available_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg()
    cfg.daily_universe_provider = lambda *_: ["AUSDT", "BUSDT"]
    bars_1d = [_Bar(close_time_utc_ms=100, close=10.0)]
    bars_4h = [_Bar(close_time_utc_ms=200, close=20.0)]
    cfg.daily_ohlcv_provider = lambda symbol, tf: ([] if (symbol == "AUSDT" and tf == "4h") else (bars_4h if tf == "4h" else bars_1d))

    monkeypatch.setattr(daily_runner, "compute_tier1_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier2_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_phase_interpretation", lambda *_args, **_kwargs: type("P", (), {"market_phase_confidence": 70.0})())
    monkeypatch.setattr(daily_runner, "compute_invalidation_and_cycle", lambda *_args, **_kwargs: InvalidationCycleBundle(
        symbol="X",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=True,
        structural_invalidation=False,
        structural_invalidation_reason=None,
        timing_invalidation=False,
        timing_invalidation_reason=None,
        new_cycle_detected=False,
        cycle_reason_code="FIRST_CYCLE_INITIALIZED",
        resolved_setup_cycle_id=1,
        phase_floor_recovered_since_cycle_end=False,
        expansion_reset_condition_met=None,
        reclaim_reset_condition_met=None,
    ))
    monkeypatch.setattr(daily_runner, "load_persisted_state_machine_context", lambda *_args, **_kwargs: PersistedStateMachineContext(
        symbol="X",
        current_setup_cycle_id=None,
        previous_setup_cycle_id=None,
        state_recorded_in_cycle_id=None,
        prev_state_machine_state=None,
        freshness_distance_state_early=None,
        freshness_distance_state_confirmed=None,
        bars_since_state_entered=None,
        bars_since_early_entered=None,
        bars_since_confirmed_entered=None,
        bars_since_cycle_end=None,
        reclaim_below_reset_floor_seen_since_cycle_end=None,
        close_at_early_entry_bar=None,
        close_at_confirmed_entry_bar=None,
        distance_from_ideal_entry_after_early=None,
        distance_from_ideal_entry_after_confirmed=None,
        cycle_end_bar_index=None,
        cycle_end_timestamp=None,
    ))
    monkeypatch.setattr(daily_runner, "compute_state_machine", lambda *_args, **_kwargs: StateMachineBundle(
        symbol="X",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=True,
        disposition=StateEvaluationDisposition(admitted=True, disposition_reason=None),
        state_machine_state="watch",
        state_confidence=60.0,
        state_transition_reason="STATE_HOLD",
        data_resolution_class="full_1d_4h",
        freshness=StateFreshnessBundle(None, None, None, None),
        persistence_patch=None,
    ))
    monkeypatch.setattr(daily_runner, "resolve_entry_pattern", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "assign_bucket", lambda *_args, **_kwargs: type("D", (), {"priority_score": 10.0, "decision_bucket": type("B", (), {"value": "watchlist"})()})())
    monkeypatch.setattr(daily_runner, "select_execution_subset", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(daily_runner, "evaluate_execution_subset", lambda *_args, **_kwargs: type("E", (), {"contracts": {}, "diagnostics": {}})())
    monkeypatch.setattr(daily_runner, "rank_coins", lambda records, *_args, **_kwargs: records)
    monkeypatch.setattr(daily_runner, "_persist_run_manifest", lambda *_args, **_kwargs: "snapshots/runs/x/run.manifest.json")

    seen: dict[str, list[dict]] = {}

    class _Builder:
        def write_run_report(self, **kwargs):
            seen["records"] = list(kwargs["diagnostics_records"])
            return {"daily_bar_id": "2026-01-01"}

        def write_daily_report(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(daily_runner, "make_report_builder", lambda *_args, **_kwargs: _Builder())
    monkeypatch.setattr(
        daily_runner,
        "build_feature_bundle",
        lambda symbol, *_args, **_kwargs: type("FB", (), {"data_4h_available": symbol != "AUSDT"})(),
    )

    run_daily_scan(cfg, as_of_date="2026-01-01")
    by_symbol = {r["symbol"]: r for r in seen["records"]}
    assert by_symbol["AUSDT"]["data_4h_available"] is False
    assert by_symbol["BUSDT"]["data_4h_available"] is True


def test_daily_runner_writes_canonical_daily_scan_mode(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    cfg = _cfg()
    cfg.daily_universe_provider = lambda *_: ["BTCUSDT"]
    cfg.daily_ohlcv_provider = lambda *_: [_Bar(close_time_utc_ms=100, close=10.0)]

    monkeypatch.setattr(daily_runner, "build_feature_bundle", lambda *_args, **_kwargs: type("FB", (), {"data_4h_available": False})())
    monkeypatch.setattr(daily_runner, "compute_tier1_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_tier2_axes", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "compute_phase_interpretation", lambda *_args, **_kwargs: type("P", (), {"market_phase_confidence": 70.0})())
    monkeypatch.setattr(daily_runner, "compute_invalidation_and_cycle", lambda *_args, **_kwargs: InvalidationCycleBundle(
        symbol="BTCUSDT",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=False,
        structural_invalidation=False,
        structural_invalidation_reason=None,
        timing_invalidation=False,
        timing_invalidation_reason=None,
        new_cycle_detected=False,
        cycle_reason_code="FIRST_CYCLE_INITIALIZED",
        resolved_setup_cycle_id=1,
        phase_floor_recovered_since_cycle_end=False,
        expansion_reset_condition_met=None,
        reclaim_reset_condition_met=None,
    ))
    monkeypatch.setattr(daily_runner, "load_persisted_state_machine_context", lambda *_args, **_kwargs: PersistedStateMachineContext(
        symbol="BTCUSDT",
        current_setup_cycle_id=None,
        previous_setup_cycle_id=None,
        state_recorded_in_cycle_id=None,
        prev_state_machine_state=None,
        freshness_distance_state_early=None,
        freshness_distance_state_confirmed=None,
        bars_since_state_entered=None,
        bars_since_early_entered=None,
        bars_since_confirmed_entered=None,
        bars_since_cycle_end=None,
        reclaim_below_reset_floor_seen_since_cycle_end=None,
        close_at_early_entry_bar=None,
        close_at_confirmed_entry_bar=None,
        distance_from_ideal_entry_after_early=None,
        distance_from_ideal_entry_after_confirmed=None,
        cycle_end_bar_index=None,
        cycle_end_timestamp=None,
    ))
    monkeypatch.setattr(daily_runner, "compute_state_machine", lambda *_args, **_kwargs: StateMachineBundle(
        symbol="BTCUSDT",
        daily_bar_id="2026-01-01",
        intraday_bar_id=None,
        data_4h_available=False,
        disposition=StateEvaluationDisposition(admitted=True, disposition_reason=None),
        state_machine_state="watch",
        state_confidence=60.0,
        state_transition_reason="STATE_HOLD",
        data_resolution_class="full_1d",
        freshness=StateFreshnessBundle(None, None, None, None),
        persistence_patch=None,
    ))
    monkeypatch.setattr(daily_runner, "resolve_entry_pattern", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(daily_runner, "assign_bucket", lambda *_args, **_kwargs: type("D", (), {"priority_score": 1.0, "decision_bucket": type("B", (), {"value": "watchlist"})()})())
    monkeypatch.setattr(daily_runner, "select_execution_subset", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(daily_runner, "evaluate_execution_subset", lambda *_args, **_kwargs: type("E", (), {"contracts": {}, "diagnostics": {}})())
    monkeypatch.setattr(daily_runner, "rank_coins", lambda records, *_args, **_kwargs: records)
    monkeypatch.setattr(daily_runner, "_persist_run_manifest", lambda *_args, **_kwargs: "snapshots/runs/x/run.manifest.json")

    captured: dict[str, str] = {}

    class _Builder:
        def write_run_report(self, **kwargs):
            captured["scan_mode"] = str(kwargs["scan_mode"])
            return {"daily_bar_id": "2026-01-01"}

        def write_daily_report(self, *_args, **_kwargs):
            return None

    monkeypatch.setattr(daily_runner, "make_report_builder", lambda *_args, **_kwargs: _Builder())

    run_daily_scan(cfg, as_of_date="2026-01-01")
    assert captured["scan_mode"] == "daily"
