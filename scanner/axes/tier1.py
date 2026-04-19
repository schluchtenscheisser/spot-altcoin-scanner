from __future__ import annotations

from typing import Any

from scanner.axes.models import Tier1AxisBundle
from scanner.axes.normalization import (
    norm_linear_clamped,
    norm_linear_clamped_inv,
    norm_piecewise_linear,
    weighted_mean,
)
from scanner.features.models import FeatureBundle


def _is_ok(value: Any, status: Any) -> bool:
    return value is not None and status == "ok"


def _extract_input(feature_bundle: FeatureBundle, field: str) -> float | int | None:
    if hasattr(feature_bundle.raw_1d, field):
        val = getattr(feature_bundle.raw_1d, field)
        status = getattr(feature_bundle.raw_1d, f"{field}_status")
        return val if _is_ok(val, status) else None
    if feature_bundle.raw_4h is not None and hasattr(feature_bundle.raw_4h, field):
        val = getattr(feature_bundle.raw_4h, field)
        status = getattr(feature_bundle.raw_4h, f"{field}_status")
        return val if _is_ok(val, status) else None
    if hasattr(feature_bundle.raw_shared, field):
        val = getattr(feature_bundle.raw_shared, field)
        status = getattr(feature_bundle.raw_shared, f"{field}_status")
        return val if _is_ok(val, status) else None
    return None


def _resolve_axes_cfg(cfg: Any) -> dict[str, Any]:
    if hasattr(cfg, "axes"):
        return dict(cfg.axes)
    if hasattr(cfg, "raw") and isinstance(cfg.raw, dict):
        axes = cfg.raw.get("axes", {})
        return dict(axes) if isinstance(axes, dict) else {}
    return {}


def _aggregate(scores_and_weights: list[tuple[float | None, float]], min_ratio: float) -> tuple[float | None, bool, bool, float | None]:
    total_weight = sum(w for _, w in scores_and_weights)
    retained_weight = sum(w for score, w in scores_and_weights if score is not None)
    ratio = retained_weight / total_weight if total_weight > 0 else 0.0
    if retained_weight == 0 or ratio < min_ratio:
        return None, True, False, None
    score = weighted_mean(scores_and_weights)
    if score is None:
        return None, True, False, None
    reduced = retained_weight < total_weight
    return score, False, reduced, ratio


def compute_tier1_axes(feature_bundle: FeatureBundle, cfg: Any) -> Tier1AxisBundle:
    axes_cfg = _resolve_axes_cfg(cfg)
    min_ratio = float(axes_cfg.get("min_effective_weight_ratio", 0.60))

    # Axis 1: trend_strength
    trend_specs = [
        ("close_vs_ema20_1d_pct", lambda x: norm_linear_clamped(x, -10, 0, 10), 0.20),
        ("close_vs_ema50_1d_pct", lambda x: norm_linear_clamped(x, -10, 0, 10), 0.15),
        ("close_vs_ema20_4h_pct", lambda x: norm_linear_clamped(x, -10, 0, 10), 0.15),
        ("close_vs_ema50_4h_pct", lambda x: norm_linear_clamped(x, -10, 0, 10), 0.10),
        ("ema20_slope_1d_pct_per_bar", lambda x: norm_linear_clamped(x, -1.5, 0, 1.5), 0.10),
        ("ema20_slope_4h_pct_per_bar", lambda x: norm_linear_clamped(x, -1.5, 0, 1.5), 0.10),
        ("ema20_vs_ema50_1d_pct", lambda x: norm_linear_clamped(x, -8, 0, 8), 0.10),
        ("ema20_vs_ema50_4h_pct", lambda x: norm_linear_clamped(x, -8, 0, 8), 0.10),
    ]
    trend_scores = []
    for field, fn, weight in trend_specs:
        raw = _extract_input(feature_bundle, field)
        trend_scores.append((fn(float(raw)) if raw is not None else None, weight))
    trend, trend_ne, trend_rr, trend_ratio = _aggregate(trend_scores, min_ratio)

    # Axis 2: reclaim_progress (two-level)
    hold_points = [(0, 0), (1, 40), (2, 70), (3, 100)]
    anchor_specs = [
        ("close_vs_ema20_4h_pct", "bars_above_ema20_4h", 0.25),
        ("close_vs_ema50_4h_pct", "bars_above_ema50_4h", 0.20),
        ("close_vs_ema20_1d_pct", "bars_above_ema20_1d", 0.20),
        ("close_vs_ema50_1d_pct", "bars_above_ema50_1d", 0.15),
        ("close_vs_high20_4h_pct", "bars_above_high20_4h", 0.20),
    ]
    reclaim_scores = []
    for dist_field, hold_field, weight in anchor_specs:
        dist = _extract_input(feature_bundle, dist_field)
        hold = _extract_input(feature_bundle, hold_field)
        if dist is None or hold is None:
            reclaim_scores.append((None, weight))
            continue
        dist_score = norm_linear_clamped(float(dist), -3, 0, 3)
        hold_score = norm_piecewise_linear(float(hold), hold_points)
        if dist_score is None or hold_score is None:
            reclaim_scores.append((None, weight))
            continue
        reclaim_scores.append((0.70 * dist_score + 0.30 * hold_score, weight))
    reclaim, reclaim_ne, reclaim_rr, reclaim_ratio = _aggregate(reclaim_scores, min_ratio)

    # Axis 3: compression_strength
    if not feature_bundle.data_4h_available:
        comp, comp_ne, comp_rr, comp_ratio = None, True, False, None
    else:
        comp_specs = [
            ("bb_width_rank_120_4h", lambda x: norm_linear_clamped_inv(x, 10, 50, 100), 0.35),
            ("atr_pct_rank_120_1d", lambda x: norm_linear_clamped_inv(x, 10, 50, 100), 0.25),
            ("range_width_12bars_4h_vs_atr1d_pct", lambda x: norm_linear_clamped_inv(x, 50, 100, 200), 0.25),
            ("std_return_rank_12bars_4h_pct", lambda x: norm_linear_clamped_inv(x, 10, 50, 100), 0.15),
        ]
        comp_scores = []
        for field, fn, weight in comp_specs:
            raw = _extract_input(feature_bundle, field)
            comp_scores.append((fn(float(raw)) if raw is not None else None, weight))
        has_any_4h = any(comp_scores[idx][0] is not None for idx in (0, 2, 3))
        if not has_any_4h:
            comp, comp_ne, comp_rr, comp_ratio = None, True, False, None
        else:
            comp, comp_ne, comp_rr, comp_ratio = _aggregate(comp_scores, min_ratio)

    # Axis 4: expansion_progress_structural
    if not feature_bundle.data_4h_available:
        exp, exp_ne, exp_rr, exp_ratio = None, True, False, None
    else:
        exp_specs = [
            ("move_from_last_structural_break_pct", lambda x: norm_piecewise_linear(x, [(0, 0), (3, 30), (6, 60), (10, 100)]), 0.40),
            ("bars_since_last_structural_break_4h", lambda x: norm_piecewise_linear(x, [(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]), 0.20),
            ("dist_to_base_mid_pct", lambda x: norm_piecewise_linear(x, [(0, 0), (3, 35), (6, 65), (10, 100)]), 0.20),
            ("dist_to_ema20_4h_pct_abs", lambda x: norm_piecewise_linear(x, [(0, 0), (2, 30), (5, 65), (8, 100)]), 0.20),
        ]
        exp_scores = []
        for field, fn, weight in exp_specs:
            raw = _extract_input(feature_bundle, field) if field != "dist_to_base_mid_pct" else None
            exp_scores.append((fn(float(raw)) if raw is not None else None, weight))
        exp, exp_ne, exp_rr, exp_ratio = _aggregate(exp_scores, min_ratio)

    # Axis 5: volume_regime_shift
    if not feature_bundle.data_4h_available:
        vol, vol_ne, vol_rr, vol_ratio = None, True, False, None
    else:
        vol_specs = [
            ("volume_quote_spike_1d", lambda x: norm_linear_clamped(x, 0.9, 1.2, 2.0), 0.25),
            ("volume_quote_spike_4h", lambda x: norm_linear_clamped(x, 0.9, 1.2, 2.0), 0.35),
            ("volume_spike_persistence_4h", lambda x: norm_piecewise_linear(x, [(0.00, 0), (0.25, 30), (0.50, 60), (0.75, 85), (1.00, 100)]), 0.20),
            ("volume_4h_current_vs_median10", lambda x: norm_piecewise_linear(x, [(0.8, 0), (1.0, 40), (1.3, 70), (1.8, 100)]), 0.20),
        ]
        vol_scores = []
        for field, fn, weight in vol_specs:
            raw = _extract_input(feature_bundle, field)
            vol_scores.append((fn(float(raw)) if raw is not None else None, weight))
        vol, vol_ne, vol_rr, vol_ratio = _aggregate(vol_scores, min_ratio)

    # Axis 6: freshness_distance_structural
    fresh_specs = [
        ("distance_to_last_structural_anchor_pct_abs", lambda x: norm_piecewise_linear(x, [(0, 0), (1, 25), (2, 50), (3, 75), (5, 100)]), 0.35),
        ("distance_to_range_high_pct_abs", lambda x: norm_piecewise_linear(x, [(0, 0), (1, 30), (2, 55), (4, 100)]), 0.25),
        ("bars_since_last_volume_shift_4h", lambda x: norm_piecewise_linear(x, [(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]), 0.20),
        ("bars_since_last_structural_break_4h", lambda x: norm_piecewise_linear(x, [(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]), 0.20),
    ]
    fresh_scores = []
    for field, fn, weight in fresh_specs:
        raw = _extract_input(feature_bundle, field)
        fresh_scores.append((fn(float(raw)) if raw is not None else None, weight))
    valid_count = sum(1 for score, _ in fresh_scores if score is not None)
    if valid_count < 2:
        fresh, fresh_ne, fresh_rr, fresh_ratio = None, True, False, None
    else:
        fresh, fresh_ne, _fresh_rr_generic, fresh_ratio = _aggregate(fresh_scores, min_ratio)
        if fresh is None:
            fresh_rr = False
        else:
            fresh_rr = valid_count in (2, 3)

    return Tier1AxisBundle(
        symbol=feature_bundle.symbol,
        daily_bar_id=feature_bundle.daily_bar_id,
        intraday_bar_id=feature_bundle.intraday_bar_id,
        data_4h_available=feature_bundle.data_4h_available,
        trend_strength=trend,
        trend_strength_not_evaluable=trend_ne,
        trend_strength_reduced_resolution=trend_rr,
        trend_strength_effective_weight_ratio=trend_ratio,
        reclaim_progress=reclaim,
        reclaim_progress_not_evaluable=reclaim_ne,
        reclaim_progress_reduced_resolution=reclaim_rr,
        reclaim_progress_effective_weight_ratio=reclaim_ratio,
        compression_strength=comp,
        compression_strength_not_evaluable=comp_ne,
        compression_strength_reduced_resolution=comp_rr,
        compression_strength_effective_weight_ratio=comp_ratio,
        expansion_progress_structural=exp,
        expansion_progress_structural_not_evaluable=exp_ne,
        expansion_progress_structural_reduced_resolution=exp_rr,
        expansion_progress_structural_effective_weight_ratio=exp_ratio,
        volume_regime_shift=vol,
        volume_regime_shift_not_evaluable=vol_ne,
        volume_regime_shift_reduced_resolution=vol_rr,
        volume_regime_shift_effective_weight_ratio=vol_ratio,
        freshness_distance_structural=fresh,
        freshness_distance_structural_not_evaluable=fresh_ne,
        freshness_distance_structural_reduced_resolution=fresh_rr,
        freshness_distance_structural_effective_weight_ratio=fresh_ratio,
    )
