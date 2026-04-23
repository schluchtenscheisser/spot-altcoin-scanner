from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Tier1AxisBundle:
    symbol: str
    daily_bar_id: str
    intraday_bar_id: int | None
    data_4h_available: bool

    trend_strength: float | None
    trend_strength_not_evaluable: bool
    trend_strength_reduced_resolution: bool
    trend_strength_effective_weight_ratio: float | None

    reclaim_progress: float | None
    reclaim_progress_not_evaluable: bool
    reclaim_progress_reduced_resolution: bool
    reclaim_progress_effective_weight_ratio: float | None

    compression_strength: float | None
    compression_strength_not_evaluable: bool
    compression_strength_reduced_resolution: bool
    compression_strength_effective_weight_ratio: float | None

    expansion_progress_structural: float | None
    expansion_progress_structural_not_evaluable: bool
    expansion_progress_structural_reduced_resolution: bool
    expansion_progress_structural_effective_weight_ratio: float | None

    volume_regime_shift: float | None
    volume_regime_shift_not_evaluable: bool
    volume_regime_shift_reduced_resolution: bool
    volume_regime_shift_effective_weight_ratio: float | None

    freshness_distance_structural: float | None
    freshness_distance_structural_not_evaluable: bool
    freshness_distance_structural_reduced_resolution: bool
    freshness_distance_structural_effective_weight_ratio: float | None


@dataclass(frozen=True)
class Tier2AxisBundle:
    symbol: str
    daily_bar_id: str
    intraday_bar_id: int | None
    data_4h_available: bool

    base_integrity_simplified: float | None
    base_integrity_simplified_not_evaluable: bool
    base_integrity_simplified_reduced_resolution: bool
    base_integrity_simplified_effective_weight_ratio: float | None

    pullback_quality_simplified: float | None
    pullback_quality_simplified_not_evaluable: bool
    pullback_quality_simplified_reduced_resolution: bool
    pullback_quality_simplified_effective_weight_ratio: float | None

    reacceleration_strength_simplified: float | None
    reacceleration_strength_simplified_not_evaluable: bool
    reacceleration_strength_simplified_reduced_resolution: bool
    reacceleration_strength_simplified_effective_weight_ratio: float | None
