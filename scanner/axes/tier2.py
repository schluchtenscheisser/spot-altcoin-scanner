from __future__ import annotations

from typing import Any, Mapping

from scanner.axes.models import Tier2AxisBundle
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


def _aggregate(scores_and_weights: list[tuple[float | None, float]], min_ratio: float, fallback_path: bool) -> tuple[float | None, bool, bool, float | None]:
    total_weight = sum(w for _, w in scores_and_weights)
    retained_weight = sum(w for score, w in scores_and_weights if score is not None)
    ratio = retained_weight / total_weight if total_weight > 0 else 0.0
    if retained_weight == 0 or ratio < min_ratio:
        return None, True, False, None
    score = weighted_mean(scores_and_weights)
    if score is None:
        return None, True, False, None
    reduced = fallback_path or retained_weight < total_weight
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


def _axis_score(
    feature_bundle: FeatureBundle,
    min_ratio: float,
    cfg_block: Mapping[str, Any],
    path: str,
    specs: list[tuple[str, str, float]],
) -> tuple[float | None, bool, bool, float | None]:
    scores: list[tuple[float | None, float]] = []
    for field, mode, weight in specs:
        raw = _extract_input(feature_bundle, field)
        block = cfg_block[field]
        if mode == "lin":
            subscore = _lin_score(raw, block)
        elif mode == "lin_inv":
            subscore = _lin_inv_score(raw, block)
        else:
            subscore = _pw_score(raw, block)
        scores.append((subscore, weight))
    return _aggregate(scores, min_ratio, fallback_path=(path == "1d"))


def _valid_impulse(feature_bundle: FeatureBundle, path: str) -> bool:
    tf = "4h" if path == "4h" else "1d"
    start = _extract_input(feature_bundle, f"impulse_start_price_{tf}")
    high = _extract_input(feature_bundle, f"impulse_high_price_{tf}")
    if start is None or high is None:
        return False
    return float(high) > float(start)


def compute_tier2_axes(feature_bundle: FeatureBundle, cfg: Any) -> Tier2AxisBundle:
    axes_cfg = cfg.axes
    min_ratio = float(axes_cfg["min_effective_weight_ratio"])
    path = "4h" if feature_bundle.data_4h_available else "1d"

    base_cfg = axes_cfg["base_integrity_simplified"]
    base_specs = [
        ("bars_since_last_new_low_4h", "pw", 0.30),
        ("range_width_12bars_4h_pct", "lin_inv", 0.20),
        ("close_position_in_range_12bars_4h", "pw", 0.25),
        ("close_above_range_mid_ratio_12bars_4h", "pw", 0.25),
    ] if path == "4h" else [
        ("bars_since_last_new_low_1d", "pw", 0.30),
        ("range_width_10bars_1d_pct", "lin_inv", 0.20),
        ("close_position_in_range_10bars_1d", "pw", 0.25),
        ("close_above_range_mid_ratio_10bars_1d", "pw", 0.25),
    ]
    base, base_ne, base_rr, base_ratio = _axis_score(feature_bundle, min_ratio, base_cfg, path, base_specs)

    pb_cfg = axes_cfg["pullback_quality_simplified"]
    if not _valid_impulse(feature_bundle, path):
        pullback, pullback_ne, pullback_rr, pullback_ratio = None, True, False, None
    else:
        pb_specs = [
            ("pullback_depth_vs_last_impulse_pct_4h", "pw", 0.35),
            ("pullback_volume_ratio_4h", "pw", 0.25),
            ("close_vs_ema20_4h_pct", "lin", 0.20),
            ("lowest_low_vs_ema20_4h_pct", "lin", 0.20),
        ] if path == "4h" else [
            ("pullback_depth_vs_last_impulse_pct_1d", "pw", 0.35),
            ("pullback_volume_ratio_1d", "pw", 0.25),
            ("close_vs_ema20_1d_pct", "lin", 0.20),
            ("lowest_low_vs_ema20_1d_pct", "lin", 0.20),
        ]
        pullback, pullback_ne, pullback_rr, pullback_ratio = _axis_score(feature_bundle, min_ratio, pb_cfg, path, pb_specs)

    reac_cfg = axes_cfg["reacceleration_strength_simplified"]
    reac_specs = [
        ("close_vs_rolling_high_5_4h_pct", "lin", 0.35),
        ("volume_4h_current_vs_median10", "pw", 0.25),
        ("ema20_slope_4h_pct_per_bar", "lin", 0.20),
        ("close_vs_ema20_4h_pct", "lin", 0.20),
    ] if path == "4h" else [
        ("close_vs_rolling_high_5_1d_pct", "lin", 0.35),
        ("volume_1d_current_vs_median10", "pw", 0.25),
        ("ema20_slope_1d_pct_per_bar", "lin", 0.20),
        ("close_vs_ema20_1d_pct", "lin", 0.20),
    ]
    reacc, reacc_ne, reacc_rr, reacc_ratio = _axis_score(feature_bundle, min_ratio, reac_cfg, path, reac_specs)

    return Tier2AxisBundle(
        symbol=feature_bundle.symbol,
        daily_bar_id=feature_bundle.daily_bar_id,
        intraday_bar_id=feature_bundle.intraday_bar_id,
        data_4h_available=feature_bundle.data_4h_available,
        base_integrity_simplified=base,
        base_integrity_simplified_not_evaluable=base_ne,
        base_integrity_simplified_reduced_resolution=base_rr,
        base_integrity_simplified_effective_weight_ratio=base_ratio,
        pullback_quality_simplified=pullback,
        pullback_quality_simplified_not_evaluable=pullback_ne,
        pullback_quality_simplified_reduced_resolution=pullback_rr,
        pullback_quality_simplified_effective_weight_ratio=pullback_ratio,
        reacceleration_strength_simplified=reacc,
        reacceleration_strength_simplified_not_evaluable=reacc_ne,
        reacceleration_strength_simplified_reduced_resolution=reacc_rr,
        reacceleration_strength_simplified_effective_weight_ratio=reacc_ratio,
    )
