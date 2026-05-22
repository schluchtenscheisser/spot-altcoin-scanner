from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

import pandas as pd


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
    def __call__(
        self,
        *,
        symbol: str,
        as_of_daily_bar_id: str,
        closed_1d_bars: pd.DataFrame,
        closed_4h_bars: pd.DataFrame,
        persisted_state: dict[str, Any],
        scanner_config: dict[str, Any],
    ) -> ReplayProductionOutput: ...


class HistoricalProductionAdapter:
    """Placeholder adapter boundary until T5–T12 production wiring is completed."""

    def __call__(
        self,
        *,
        symbol: str,
        as_of_daily_bar_id: str,
        closed_1d_bars: pd.DataFrame,
        closed_4h_bars: pd.DataFrame,
        persisted_state: dict[str, Any],
        scanner_config: dict[str, Any],
    ) -> ReplayProductionOutput:
        return ReplayProductionOutput(
            disposition_status="admitted",
            disposition_reason="PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE",
            market_phase="none",
            market_phase_confidence=0.0,
            state_machine_state="watch",
            state_confidence=persisted_state.get("state_confidence"),
            state_transition_reason=persisted_state.get("state_transition_reason"),
            setup_cycle_id=persisted_state.get("setup_cycle_id"),
            entry_pattern="none",
            entry_pattern_score=0.0,
            signal_daily_close=float(closed_1d_bars.iloc[-1].get("close", 0.0)) if not closed_1d_bars.empty else None,
            transition_event_types=[],
            updated_state_patch={},
            production_modules_used=[],
        )
