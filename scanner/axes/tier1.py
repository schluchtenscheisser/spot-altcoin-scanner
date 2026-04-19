from __future__ import annotations

from typing import Any, Mapping

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


def _lin_score(raw: float | int | None, block: Mapping[str, Any]) -> float | None:
    if raw is None:
        return None
    return norm_linear_clamped(float(raw), float(block["low"]), float(block["mid"]), float(block["high"]))


def _lin_inv_score(raw: float | int | None, block: Mapping[str, Any]) -> float | None:
    if raw is None:
        return None
    return norm_linear_clamped_inv(float(raw), float(block["low_good"]), float(block["mid"]), float(block["high_bad"]))


def _pw_score(raw: float | int | None, block: Mapping[str, Any]) -> float | None:
    if raw is None:
        return None
    points = [(float(x), float(y)) for x, y in block["points"]]
    return norm_piecewise_linear(float(raw), points)


def compute_tier1_axes(feature_bundle: FeatureBundle, cfg: Any) -> Tier1AxisBundle:
    axes_cfg = _resolve_axes_cfg(cfg)
    min_ratio = float(axes_cfg.get("min_effective_weight_ratio", 0.60))

    trend_cfg = axes_cfg["trend_strength"]
    trend_fields = [
        "close_vs_ema20_1d_pct",
        "close_vs_ema50_1d_pct",
        "close_vs_ema20_4h_pct",
        "close_vs_ema50_4h_pct",
        "ema20_slope_1d_pct_per_bar",
        "ema20_slope_4h_pct_per_bar",
        "ema20_vs_ema50_1d_pct",
        "ema20_vs_ema50_4h_pct",
    ]
    trend_scores = [(_lin_score(_extract_input(feature_bundle, field), trend_cfg[field]), float(trend_cfg[field]["weight"])) for field in trend_fields]
    trend, trend_ne, trend_rr, trend_ratio = _aggregate(trend_scores, min_ratio)

    reclaim_cfg = axes_cfg["reclaim_progress"]
    reclaim_dist = reclaim_cfg["distance"]
    hold_points = [(float(x), float(y)) for x, y in reclaim_cfg["hold_points"]]
    anchor_map = [
        ("ema20_4h", "close_vs_ema20_4h_pct", "bars_above_ema20_4h"),
        ("ema50_4h", "close_vs_ema50_4h_pct", "bars_above_ema50_4h"),
        ("ema20_1d", "close_vs_ema20_1d_pct", "bars_above_ema20_1d"),
        ("ema50_1d", "close_vs_ema50_1d_pct", "bars_above_ema50_1d"),
        ("fixed_structural_4h", "close_vs_high20_4h_pct", "bars_above_high20_4h"),
    ]
    reclaim_scores = []
    for anchor_key, dist_field, hold_field in anchor_map:
        dist = _extract_input(feature_bundle, dist_field)
        hold = _extract_input(feature_bundle, hold_field)
        weight = float(reclaim_cfg["anchors"][anchor_key]["weight"])
        if dist is None or hold is None:
            reclaim_scores.append((None, weight))
            continue
        dist_score = norm_linear_clamped(float(dist), float(reclaim_dist["low"]), float(reclaim_dist["mid"]), float(reclaim_dist["high"]))
        hold_score = norm_piecewise_linear(float(hold), hold_points)
        if dist_score is None or hold_score is None:
            reclaim_scores.append((None, weight))
            continue
        reclaim_scores.append((0.70 * dist_score + 0.30 * hold_score, weight))
    reclaim, reclaim_ne, reclaim_rr, reclaim_ratio = _aggregate(reclaim_scores, min_ratio)

    comp_cfg = axes_cfg["compression_strength"]
    if not feature_bundle.data_4h_available:
        comp, comp_ne, comp_rr, comp_ratio = None, True, False, None
    else:
        comp_fields = [
            "bb_width_rank_120_4h",
            "atr_pct_rank_120_1d",
            "range_width_12bars_4h_vs_atr1d_pct",
            "std_return_rank_12bars_4h_pct",
        ]
        comp_scores = [(_lin_inv_score(_extract_input(feature_bundle, field), comp_cfg[field]), float(comp_cfg[field]["weight"])) for field in comp_fields]
        has_any_4h = any(comp_scores[idx][0] is not None for idx in (0, 2, 3))
        if not has_any_4h:
            comp, comp_ne, comp_rr, comp_ratio = None, True, False, None
        else:
            comp, comp_ne, comp_rr, comp_ratio = _aggregate(comp_scores, min_ratio)

    exp_cfg = axes_cfg["expansion_progress_structural"]
    if not feature_bundle.data_4h_available:
        exp, exp_ne, exp_rr, exp_ratio = None, True, False, None
    else:
        exp_fields = [
            "move_from_last_structural_break_pct",
            "bars_since_last_structural_break_4h",
            "dist_to_base_mid_pct",
            "dist_to_ema20_4h_pct_abs",
        ]
        exp_scores = []
        for field in exp_fields:
            raw = _extract_input(feature_bundle, field) if field != "dist_to_base_mid_pct" else None
            exp_scores.append((_pw_score(raw, exp_cfg[field]), float(exp_cfg[field]["weight"])))
        exp, exp_ne, exp_rr, exp_ratio = _aggregate(exp_scores, min_ratio)

    vol_cfg = axes_cfg["volume_regime_shift"]
    if not feature_bundle.data_4h_available:
        vol, vol_ne, vol_rr, vol_ratio = None, True, False, None
    else:
        vol_specs = [
            ("volume_quote_spike_1d", _lin_score),
            ("volume_quote_spike_4h", _lin_score),
            ("volume_spike_persistence_4h", _pw_score),
            ("volume_4h_current_vs_median10", _pw_score),
        ]
        vol_scores = []
        for field, scorer in vol_specs:
            vol_scores.append((scorer(_extract_input(feature_bundle, field), vol_cfg[field]), float(vol_cfg[field]["weight"])))
        vol, vol_ne, vol_rr, vol_ratio = _aggregate(vol_scores, min_ratio)

    fresh_cfg = axes_cfg["freshness_distance_structural"]
    fresh_fields = [
        "distance_to_last_structural_anchor_pct_abs",
        "distance_to_range_high_pct_abs",
        "bars_since_last_volume_shift_4h",
        "bars_since_last_structural_break_4h",
    ]
    fresh_scores = [(_pw_score(_extract_input(feature_bundle, field), fresh_cfg[field]), float(fresh_cfg[field]["weight"])) for field in fresh_fields]
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
