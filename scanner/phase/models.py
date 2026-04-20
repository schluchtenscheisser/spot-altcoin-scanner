from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PhaseInterpretationBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    market_phase: str
    market_phase_confidence: float
    market_phase_runner_up: str
    market_phase_gap: float
    market_phase_blended: bool

    phase_score_pressure_build: float
    phase_score_trend_resume: float
    phase_score_transition_reclaim: float

    phase_floor_margin_pressure_build: float | None
    phase_floor_margin_trend_resume: float | None
    phase_floor_margin_transition_reclaim: float | None

    phase_floor_failed_pressure_build: bool
    phase_floor_failed_trend_resume: bool
    phase_floor_failed_transition_reclaim: bool

    phase_eval_status_pressure_build: str
    phase_eval_status_trend_resume: str
    phase_eval_status_transition_reclaim: str

    freshness_distance_structural: float | None
    freshness_distance_structural_not_evaluable: bool
    freshness_distance_structural_reduced_resolution: bool
