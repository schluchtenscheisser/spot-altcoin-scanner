from __future__ import annotations

import logging
import math
from dataclasses import asdict, dataclass, field
from datetime import timezone
from types import SimpleNamespace
from typing import Any, Protocol

import pandas as pd

from scanner.axes.tier1 import compute_tier1_axes
from scanner.axes.tier2 import compute_tier2_axes
from scanner.config import ScannerConfig, load_config
from scanner.entry.patterns import resolve_entry_pattern
from scanner.features.bundle import build_feature_bundle
from scanner.phase.interpreter import compute_phase_interpretation
from scanner.state.invalidation import compute_invalidation_and_cycle
from scanner.state.machine import compute_state_machine
from scanner.state.models import PersistedStateCycleContext, PersistedStateMachineContext, StateRuntimeContext

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ReplayProductionOutput:
    disposition_status: str
    disposition_reason: str
    market_phase: str
    market_phase_confidence: float
    state_machine_state: str | None
    state_confidence: float | None
    state_transition_reason: str | None
    setup_cycle_id: str | None
    entry_pattern: str
    entry_pattern_score: float
    signal_daily_close: float | None
    transition_event_types: list[str] = field(default_factory=list)
    updated_state_patch: dict[str, Any] = field(default_factory=dict)
    production_modules_used: list[str] = field(default_factory=list)


class ReplayProductionAdapterProtocol(Protocol):
    def __call__(self, *, symbol: str, as_of_daily_bar_id: str, closed_1d_bars: pd.DataFrame, closed_4h_bars: pd.DataFrame, persisted_state: dict[str, Any], scanner_config: dict[str, Any]) -> ReplayProductionOutput: ...


def _finite_float(value: Any, field: str) -> float:
    val = float(value)
    if not math.isfinite(val):
        raise ValueError(f"{field} must be finite")
    return val


def _bars_from_df(df: pd.DataFrame) -> list[SimpleNamespace]:
    required = ["close", "high", "low", "volume", "quote_volume"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"missing required OHLCV columns: {missing}")

    if "close_time_utc_ms" not in df.columns and "close_time_utc" not in df.columns:
        raise ValueError("missing required OHLCV close time column: close_time_utc_ms or close_time_utc")

    sort_col = "close_time_utc_ms" if "close_time_utc_ms" in df.columns else "close_time_utc"
    sorted_df = df.sort_values(sort_col, ascending=True)

    bars: list[SimpleNamespace] = []
    for rec in sorted_df.to_dict("records"):
        if rec.get("close_time_utc_ms") is not None:
            close_time_utc_ms = int(rec["close_time_utc_ms"])
        else:
            close_time_utc_ms = int(pd.Timestamp(rec["close_time_utc"]).timestamp() * 1000)

        bars.append(SimpleNamespace(
            close_time_utc_ms=close_time_utc_ms,
            close=_finite_float(rec["close"], "close"),
            high=_finite_float(rec["high"], "high"),
            low=_finite_float(rec["low"], "low"),
            base_volume=_finite_float(rec["volume"], "volume"),
            quote_volume=_finite_float(rec["quote_volume"], "quote_volume"),
        ))

    return bars


def _build_bar_clock_context(as_of_daily_bar_id: str, current_daily_bar: dict[str, Any]) -> dict[str, Any]:
    if "close_time_utc_ms" in current_daily_bar and current_daily_bar["close_time_utc_ms"] is not None:
        daily_close_time_utc_ms = int(current_daily_bar["close_time_utc_ms"])
    else:
        ts = pd.Timestamp(current_daily_bar["close_time_utc"])
        if ts.tzinfo is None:
            ts = ts.tz_localize(timezone.utc)
        else:
            ts = ts.tz_convert(timezone.utc)
        daily_close_time_utc_ms = int(ts.timestamp() * 1000)
    return {
        "daily_bar_id": as_of_daily_bar_id,
        "daily_close_time_utc_ms": daily_close_time_utc_ms,
    }


def _state_ctx(symbol: str, persisted_state: dict[str, Any]) -> PersistedStateMachineContext:
    s = persisted_state or {}
    return PersistedStateMachineContext(
        symbol=symbol,
        current_setup_cycle_id=s.get("setup_cycle_id"),
        previous_setup_cycle_id=s.get("previous_setup_cycle_id"),
        state_recorded_in_cycle_id=s.get("state_recorded_in_cycle_id"),
        prev_state_machine_state=s.get("state_machine_state"),
        freshness_distance_state_early=s.get("freshness_distance_state_early"),
        freshness_distance_state_confirmed=s.get("freshness_distance_state_confirmed"),
        bars_since_state_entered=s.get("bars_since_state_entered"),
        bars_since_early_entered=s.get("bars_since_early_entered"),
        bars_since_confirmed_entered=s.get("bars_since_confirmed_entered"),
        bars_since_cycle_end=s.get("bars_since_cycle_end"),
        reclaim_below_reset_floor_seen_since_cycle_end=s.get("reclaim_below_reset_floor_seen_since_cycle_end"),
        close_at_early_entry_bar=s.get("close_at_early_entry_bar"),
        close_at_confirmed_entry_bar=s.get("close_at_confirmed_entry_bar"),
        distance_from_ideal_entry_after_early=s.get("distance_from_ideal_entry_after_early"),
        distance_from_ideal_entry_after_confirmed=s.get("distance_from_ideal_entry_after_confirmed"),
        cycle_end_bar_index=s.get("cycle_end_bar_index"),
        cycle_end_timestamp=s.get("cycle_end_timestamp"),
        last_aging_daily_bar_id=s.get("last_aging_daily_bar_id"),
    )


class HistoricalProductionAdapter:
    def __call__(self, *, symbol: str, as_of_daily_bar_id: str, closed_1d_bars: pd.DataFrame, closed_4h_bars: pd.DataFrame, persisted_state: dict[str, Any], scanner_config: dict[str, Any]) -> ReplayProductionOutput:
        try:
            cfg: ScannerConfig = load_config(scanner_config.get("ref"))
            current_daily_bar = closed_1d_bars.iloc[-1].to_dict()
            bar_clock_context = _build_bar_clock_context(as_of_daily_bar_id, current_daily_bar)
            d1 = _bars_from_df(closed_1d_bars)
            h4 = _bars_from_df(closed_4h_bars)
            bundle = build_feature_bundle(symbol=symbol, bar_clock_context=bar_clock_context, ohlcv_1d=d1, ohlcv_4h=h4, cfg=cfg)
            t1 = compute_tier1_axes(bundle, cfg)
            t2 = compute_tier2_axes(bundle, cfg)
            phase = compute_phase_interpretation(t1, t2, cfg)
            persisted_machine = _state_ctx(symbol, persisted_state)
            bootstrap = persisted_machine.current_setup_cycle_id is None
            cycle_ctx = PersistedStateCycleContext(
                symbol=symbol,
                current_setup_cycle_id=persisted_machine.current_setup_cycle_id,
                previous_setup_cycle_id=None if bootstrap else persisted_machine.previous_setup_cycle_id,
                state_recorded_in_cycle_id=None if bootstrap else persisted_machine.state_recorded_in_cycle_id,
                prev_state_machine_state=None if bootstrap else persisted_machine.prev_state_machine_state,
                freshness_distance_state_early=None if bootstrap else persisted_machine.freshness_distance_state_early,
                freshness_distance_state_confirmed=None if bootstrap else persisted_machine.freshness_distance_state_confirmed,
                bars_since_state_entered=persisted_machine.bars_since_state_entered,
                bars_since_early_entered=persisted_machine.bars_since_early_entered,
                bars_since_confirmed_entered=persisted_machine.bars_since_confirmed_entered,
                bars_since_cycle_end=None if bootstrap else persisted_machine.bars_since_cycle_end,
                reclaim_below_reset_floor_seen_since_cycle_end=persisted_machine.reclaim_below_reset_floor_seen_since_cycle_end,
            )
            invalidation = compute_invalidation_and_cycle(phase, t1, t2, cycle_ctx, cfg)
            runtime = StateRuntimeContext(current_close=float(current_daily_bar["close"]), current_bar_index=max(0, len(d1)-1), delta_closed_bars_relevant=1)
            state = compute_state_machine(phase, t1, t2, invalidation, persisted_machine, runtime, cfg)
            entry = resolve_entry_pattern(phase, t1, t2, cfg)
            prev_state = persisted_machine.prev_state_machine_state
            new_state = state.state_machine_state
            events: list[str] = []
            mapping = {"early_ready": "first_early_ready", "confirmed_ready": "first_confirmed_ready", "late": "first_late", "chased": "first_chased", "rejected": "first_rejected"}
            if new_state in mapping and prev_state != new_state:
                events.append(mapping[new_state])
            if new_state == "confirmed_ready" and entry.entry_pattern != "none" and prev_state != "confirmed_ready":
                events.append("first_confirmed_with_entry_pattern")
            patch = asdict(state.persistence_patch) if state.persistence_patch is not None else {}
            return ReplayProductionOutput(
                disposition_status="admitted" if state.disposition.admitted else "untracked",
                disposition_reason=state.disposition.disposition_reason or "NONE",
                market_phase=phase.market_phase,
                market_phase_confidence=phase.market_phase_confidence,
                state_machine_state=state.state_machine_state,
                state_confidence=state.state_confidence,
                state_transition_reason=state.state_transition_reason,
                setup_cycle_id=str(state.persistence_patch.setup_cycle_id) if state.persistence_patch is not None else None,
                entry_pattern=entry.entry_pattern,
                entry_pattern_score=entry.entry_pattern_score,
                signal_daily_close=float(current_daily_bar["close"]),
                transition_event_types=events,
                updated_state_patch=patch,
                production_modules_used=[
                    "scanner.features.bundle",
                    "scanner.axes.tier1",
                    "scanner.axes.tier2",
                    "scanner.phase.interpreter",
                    "scanner.state.invalidation",
                    "scanner.state.machine",
                    "scanner.entry.patterns",
                ],
            )
        except Exception:
            logger.exception("HistoricalProductionAdapter failed symbol=%s as_of_daily_bar_id=%s", symbol, as_of_daily_bar_id)
            raise
