from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

FeatureStatus = Literal[
    "ok",
    "insufficient_history",
    "gap_in_required_window",
    "upstream_dependency_null",
    "invalid_upstream_value",
]


@dataclass(frozen=True)
class RawFeatures1D:
    close_vs_ema20_1d_pct: float | None
    close_vs_ema20_1d_pct_status: FeatureStatus
    close_vs_ema50_1d_pct: float | None
    close_vs_ema50_1d_pct_status: FeatureStatus
    ema20_vs_ema50_1d_pct: float | None
    ema20_vs_ema50_1d_pct_status: FeatureStatus
    ema20_slope_1d_pct_per_bar: float | None
    ema20_slope_1d_pct_per_bar_status: FeatureStatus
    volume_1d_current_vs_median10: float | None
    volume_1d_current_vs_median10_status: FeatureStatus
    volume_quote_spike_1d: float | None
    volume_quote_spike_1d_status: FeatureStatus
    range_width_10bars_1d_pct: float | None
    range_width_10bars_1d_pct_status: FeatureStatus
    close_position_in_range_10bars_1d: float | None
    close_position_in_range_10bars_1d_status: FeatureStatus
    close_above_range_mid_ratio_10bars_1d: float | None
    close_above_range_mid_ratio_10bars_1d_status: FeatureStatus
    close_vs_rolling_high_5_1d_pct: float | None
    close_vs_rolling_high_5_1d_pct_status: FeatureStatus
    atr_pct_1d: float | None
    atr_pct_1d_status: FeatureStatus
    atr_pct_rank_120_1d: float | None
    atr_pct_rank_120_1d_status: FeatureStatus
    bb_width_pct_1d: float | None
    bb_width_pct_1d_status: FeatureStatus
    bb_width_rank_120_1d: float | None
    bb_width_rank_120_1d_status: FeatureStatus
    bars_above_ema20_1d: int | None
    bars_above_ema20_1d_status: FeatureStatus
    bars_above_ema50_1d: int | None
    bars_above_ema50_1d_status: FeatureStatus
    bars_since_last_new_low_1d: int | None
    bars_since_last_new_low_1d_status: FeatureStatus
    pullback_depth_vs_last_impulse_pct_1d: float | None
    pullback_depth_vs_last_impulse_pct_1d_status: FeatureStatus
    pullback_volume_ratio_1d: float | None
    pullback_volume_ratio_1d_status: FeatureStatus
    lowest_low_vs_ema20_1d_pct: float | None
    lowest_low_vs_ema20_1d_pct_status: FeatureStatus
    impulse_start_price_1d: float | None
    impulse_start_price_1d_status: FeatureStatus
    impulse_high_price_1d: float | None
    impulse_high_price_1d_status: FeatureStatus
    pullback_low_price_1d: float | None
    pullback_low_price_1d_status: FeatureStatus
    current_pullback_close_1d: float | None
    current_pullback_close_1d_status: FeatureStatus
    atr_1d: float | None
    atr_1d_status: FeatureStatus


@dataclass(frozen=True)
class RawFeatures4H:
    close_vs_ema20_4h_pct: float | None
    close_vs_ema20_4h_pct_status: FeatureStatus
    close_vs_ema50_4h_pct: float | None
    close_vs_ema50_4h_pct_status: FeatureStatus
    ema20_vs_ema50_4h_pct: float | None
    ema20_vs_ema50_4h_pct_status: FeatureStatus
    ema20_slope_4h_pct_per_bar: float | None
    ema20_slope_4h_pct_per_bar_status: FeatureStatus
    volume_4h_current_vs_median10: float | None
    volume_4h_current_vs_median10_status: FeatureStatus
    volume_quote_spike_4h: float | None
    volume_quote_spike_4h_status: FeatureStatus
    volume_spike_persistence_4h: float | None
    volume_spike_persistence_4h_status: FeatureStatus
    range_width_12bars_4h_pct: float | None
    range_width_12bars_4h_pct_status: FeatureStatus
    close_position_in_range_12bars_4h: float | None
    close_position_in_range_12bars_4h_status: FeatureStatus
    close_above_range_mid_ratio_12bars_4h: float | None
    close_above_range_mid_ratio_12bars_4h_status: FeatureStatus
    close_vs_rolling_high_5_4h_pct: float | None
    close_vs_rolling_high_5_4h_pct_status: FeatureStatus
    atr_pct_4h: float | None
    atr_pct_4h_status: FeatureStatus
    atr_pct_rank_120_4h: float | None
    atr_pct_rank_120_4h_status: FeatureStatus
    bb_width_pct_4h: float | None
    bb_width_pct_4h_status: FeatureStatus
    bb_width_rank_120_4h: float | None
    bb_width_rank_120_4h_status: FeatureStatus
    std_return_rank_12bars_4h_pct: float | None
    std_return_rank_12bars_4h_pct_status: FeatureStatus
    bars_above_ema20_4h: int | None
    bars_above_ema20_4h_status: FeatureStatus
    bars_above_ema50_4h: int | None
    bars_above_ema50_4h_status: FeatureStatus
    bars_above_high20_4h: int | None
    bars_above_high20_4h_status: FeatureStatus
    bars_since_last_new_low_4h: int | None
    bars_since_last_new_low_4h_status: FeatureStatus
    fixed_structural_break_anchor_4h: float | None
    fixed_structural_break_anchor_4h_status: FeatureStatus
    close_vs_high20_4h_pct: float | None
    close_vs_high20_4h_pct_status: FeatureStatus
    break_close_4h: float | None
    break_close_4h_status: FeatureStatus
    move_from_last_structural_break_pct: float | None
    move_from_last_structural_break_pct_status: FeatureStatus
    bars_since_last_structural_break_4h: int | None
    bars_since_last_structural_break_4h_status: FeatureStatus
    distance_to_last_structural_anchor_pct_abs: float | None
    distance_to_last_structural_anchor_pct_abs_status: FeatureStatus
    bars_since_last_volume_shift_4h: int | None
    bars_since_last_volume_shift_4h_status: FeatureStatus
    distance_to_range_high_pct_abs: float | None
    distance_to_range_high_pct_abs_status: FeatureStatus
    dist_to_ema20_4h_pct_abs: float | None
    dist_to_ema20_4h_pct_abs_status: FeatureStatus
    pullback_depth_vs_last_impulse_pct_4h: float | None
    pullback_depth_vs_last_impulse_pct_4h_status: FeatureStatus
    pullback_volume_ratio_4h: float | None
    pullback_volume_ratio_4h_status: FeatureStatus
    lowest_low_vs_ema20_4h_pct: float | None
    lowest_low_vs_ema20_4h_pct_status: FeatureStatus
    impulse_start_price_4h: float | None
    impulse_start_price_4h_status: FeatureStatus
    impulse_high_price_4h: float | None
    impulse_high_price_4h_status: FeatureStatus
    pullback_low_price_4h: float | None
    pullback_low_price_4h_status: FeatureStatus
    current_pullback_close_4h: float | None
    current_pullback_close_4h_status: FeatureStatus


@dataclass(frozen=True)
class RawFeaturesShared:
    range_width_12bars_4h_vs_atr1d_pct: float | None
    range_width_12bars_4h_vs_atr1d_pct_status: FeatureStatus


@dataclass(frozen=True)
class FeatureBundle:
    symbol: str
    daily_bar_id: str
    intraday_bar_id: str | None
    daily_close_time_utc_ms: int
    intraday_close_time_utc_ms: int | None
    data_4h_available: bool
    raw_1d: RawFeatures1D
    raw_4h: RawFeatures4H | None
    raw_shared: RawFeaturesShared
