from __future__ import annotations

import dataclasses
import math

import pytest

from scanner.axes.models import Tier1AxisBundle
from scanner.axes.normalization import (
    norm_linear_clamped,
    norm_linear_clamped_inv,
    norm_piecewise_linear,
    weighted_mean,
)
from scanner.axes.tier1 import compute_tier1_axes
from scanner.config import ScannerConfig
from scanner.features.models import FeatureBundle, RawFeatures1D, RawFeatures4H, RawFeaturesShared


def _defaults(dc_cls):
    data = {}
    for f in dataclasses.fields(dc_cls):
        data[f.name] = "insufficient_history" if f.name.endswith("_status") else None
    return data


def _bundle(*, data_4h_available: bool = True, raw1: dict | None = None, raw4: dict | None = None, raws: dict | None = None) -> FeatureBundle:
    r1 = _defaults(RawFeatures1D)
    r1.update(raw1 or {})

    r4_obj = None
    if data_4h_available:
        r4 = _defaults(RawFeatures4H)
        r4.update(raw4 or {})
        r4_obj = RawFeatures4H(**r4)

    rs = _defaults(RawFeaturesShared)
    rs.update(raws or {})

    return FeatureBundle(
        symbol="TESTUSDT",
        daily_bar_id=1,
        intraday_bar_id=2 if data_4h_available else None,
        daily_close_time_utc_ms=1,
        intraday_close_time_utc_ms=2 if data_4h_available else None,
        data_4h_available=data_4h_available,
        raw_1d=RawFeatures1D(**r1),
        raw_4h=r4_obj,
        raw_shared=RawFeaturesShared(**rs),
    )


def _cfg(overrides: dict | None = None) -> ScannerConfig:
    raw = dict(overrides or {})
    raw.setdefault("independence_release", {})
    return ScannerConfig(raw=raw)


def test_norm_linear_clamped_basics_and_invalids():
    assert norm_linear_clamped(-10, -10, 0, 10) == 0
    assert norm_linear_clamped(0, -10, 0, 10) == 50
    assert norm_linear_clamped(10, -10, 0, 10) == 100
    assert norm_linear_clamped(-100, -10, 0, 10) == 0
    assert norm_linear_clamped(100, -10, 0, 10) == 100
    assert norm_linear_clamped(-5, -10, 0, 10) == 25
    assert norm_linear_clamped(5, -10, 0, 10) == 75
    assert norm_linear_clamped(float("nan"), -10, 0, 10) is None
    assert norm_linear_clamped(float("inf"), -10, 0, 10) is None
    assert norm_linear_clamped(float("-inf"), -10, 0, 10) is None
    with pytest.raises(ValueError):
        norm_linear_clamped(1, 0, 0, 1)


def test_norm_linear_clamped_inv_basics_and_invalids():
    assert norm_linear_clamped_inv(0, 0, 5, 10) == 100
    assert norm_linear_clamped_inv(5, 0, 5, 10) == 50
    assert norm_linear_clamped_inv(10, 0, 5, 10) == 0
    assert norm_linear_clamped_inv(-1, 0, 5, 10) == 100
    assert norm_linear_clamped_inv(12, 0, 5, 10) == 0
    assert norm_linear_clamped_inv(float("nan"), 0, 5, 10) is None
    with pytest.raises(ValueError):
        norm_linear_clamped_inv(1, 2, 2, 10)


def test_norm_piecewise_linear_basics_and_invalids():
    points = [(0, 0), (2, 50), (4, 100)]
    assert norm_piecewise_linear(-1, points) == 0
    assert norm_piecewise_linear(5, points) == 100
    assert norm_piecewise_linear(2, points) == 50
    assert norm_piecewise_linear(1, points) == 25
    assert norm_piecewise_linear(float("nan"), points) is None
    with pytest.raises(ValueError):
        norm_piecewise_linear(1, [(0, 0)])


def test_weighted_mean_basics_and_dropout():
    assert weighted_mean([(20, 0.2), (80, 0.8)]) == 68
    assert weighted_mean([(20, 0.2), (None, 0.8)]) == 20
    assert weighted_mean([]) is None
    assert weighted_mean([(None, 1.0)]) is None
    with pytest.raises(ValueError):
        weighted_mean([(120, 1.0)])


def test_axis_pregates_and_reduced_resolution_rules():
    fb = _bundle(data_4h_available=False)
    out = compute_tier1_axes(fb, _cfg())
    assert out.compression_strength is None and out.compression_strength_not_evaluable
    assert out.expansion_progress_structural is None and out.expansion_progress_structural_not_evaluable
    assert out.volume_regime_shift is None and out.volume_regime_shift_not_evaluable


def test_expansion_progress_structural_uses_expected_080_ratio_when_only_base_mid_missing():
    fb = _bundle(
        raw4={
            "move_from_last_structural_break_pct": 6,
            "move_from_last_structural_break_pct_status": "ok",
            "bars_since_last_structural_break_4h": 4,
            "bars_since_last_structural_break_4h_status": "ok",
            "dist_to_ema20_4h_pct_abs": 5,
            "dist_to_ema20_4h_pct_abs_status": "ok",
        }
    )
    out = compute_tier1_axes(fb, _cfg())
    assert out.expansion_progress_structural_not_evaluable is False
    assert out.expansion_progress_structural_reduced_resolution is True
    assert out.expansion_progress_structural_effective_weight_ratio == pytest.approx(0.80)


def test_freshness_min_input_rule():
    fb1 = _bundle(raw4={
        "distance_to_last_structural_anchor_pct_abs": 1,
        "distance_to_last_structural_anchor_pct_abs_status": "ok",
    })
    out1 = compute_tier1_axes(fb1, _cfg())
    assert out1.freshness_distance_structural is None
    assert out1.freshness_distance_structural_not_evaluable is True

    fb2 = _bundle(raw4={
        "distance_to_last_structural_anchor_pct_abs": 1,
        "distance_to_last_structural_anchor_pct_abs_status": "ok",
        "distance_to_range_high_pct_abs": 2,
        "distance_to_range_high_pct_abs_status": "ok",
    })
    out2 = compute_tier1_axes(fb2, _cfg())
    assert out2.freshness_distance_structural is not None
    assert out2.freshness_distance_structural_reduced_resolution is True


def test_output_contract_and_determinism():
    fb = _bundle(
        raw1={
            "close_vs_ema20_1d_pct": 1,
            "close_vs_ema20_1d_pct_status": "ok",
            "close_vs_ema50_1d_pct": 1,
            "close_vs_ema50_1d_pct_status": "ok",
            "ema20_slope_1d_pct_per_bar": 0.5,
            "ema20_slope_1d_pct_per_bar_status": "ok",
            "ema20_vs_ema50_1d_pct": 1,
            "ema20_vs_ema50_1d_pct_status": "ok",
            "volume_quote_spike_1d": 1.3,
            "volume_quote_spike_1d_status": "ok",
            "atr_pct_rank_120_1d": 30,
            "atr_pct_rank_120_1d_status": "ok",
            "bars_above_ema20_1d": 2,
            "bars_above_ema20_1d_status": "ok",
            "bars_above_ema50_1d": 2,
            "bars_above_ema50_1d_status": "ok",
        },
        raw4={
            "close_vs_ema20_4h_pct": 1,
            "close_vs_ema20_4h_pct_status": "ok",
            "close_vs_ema50_4h_pct": 1,
            "close_vs_ema50_4h_pct_status": "ok",
            "ema20_slope_4h_pct_per_bar": 0.4,
            "ema20_slope_4h_pct_per_bar_status": "ok",
            "ema20_vs_ema50_4h_pct": 1,
            "ema20_vs_ema50_4h_pct_status": "ok",
            "bars_above_ema20_4h": 2,
            "bars_above_ema20_4h_status": "ok",
            "bars_above_ema50_4h": 2,
            "bars_above_ema50_4h_status": "ok",
            "close_vs_high20_4h_pct": 1,
            "close_vs_high20_4h_pct_status": "ok",
            "bars_above_high20_4h": 2,
            "bars_above_high20_4h_status": "ok",
            "bb_width_rank_120_4h": 40,
            "bb_width_rank_120_4h_status": "ok",
            "std_return_rank_12bars_4h_pct": 35,
            "std_return_rank_12bars_4h_pct_status": "ok",
            "move_from_last_structural_break_pct": 4,
            "move_from_last_structural_break_pct_status": "ok",
            "bars_since_last_structural_break_4h": 2,
            "bars_since_last_structural_break_4h_status": "ok",
            "dist_to_ema20_4h_pct_abs": 2,
            "dist_to_ema20_4h_pct_abs_status": "ok",
            "volume_quote_spike_4h": 1.3,
            "volume_quote_spike_4h_status": "ok",
            "volume_spike_persistence_4h": 0.5,
            "volume_spike_persistence_4h_status": "ok",
            "volume_4h_current_vs_median10": 1.2,
            "volume_4h_current_vs_median10_status": "ok",
            "distance_to_last_structural_anchor_pct_abs": 1,
            "distance_to_last_structural_anchor_pct_abs_status": "ok",
            "distance_to_range_high_pct_abs": 1,
            "distance_to_range_high_pct_abs_status": "ok",
            "bars_since_last_volume_shift_4h": 1,
            "bars_since_last_volume_shift_4h_status": "ok",
        },
        raws={
            "range_width_12bars_4h_vs_atr1d_pct": 120,
            "range_width_12bars_4h_vs_atr1d_pct_status": "ok",
        },
    )
    cfg = _cfg()
    a = compute_tier1_axes(fb, cfg)
    b = compute_tier1_axes(fb, cfg)
    assert isinstance(a, Tier1AxisBundle)
    assert a == b
    assert a.symbol == "TESTUSDT"
    assert a.daily_bar_id == 1 and a.intraday_bar_id == 2
    for axis_name in [
        "trend_strength",
        "reclaim_progress",
        "compression_strength",
        "expansion_progress_structural",
        "volume_regime_shift",
        "freshness_distance_structural",
    ]:
        not_eval = getattr(a, f"{axis_name}_not_evaluable")
        axis_value = getattr(a, axis_name)
        assert not (not_eval and axis_value is not None)


def test_axes_config_defaults_and_validation():
    cfg = _cfg()
    assert math.isclose(cfg.axes["min_effective_weight_ratio"], 0.60)

    with pytest.raises(ValueError):
        _cfg({"axes": {"min_effective_weight_ratio": 0.0}}).axes
    with pytest.raises(ValueError):
        _cfg({"axes": {"min_effective_weight_ratio": 1.5}}).axes

    cfg2 = _cfg({"axes": {"trend_strength": {}}})
    assert cfg2.axes["min_effective_weight_ratio"] == 0.60

    with pytest.raises(ValueError):
        _cfg({"axes": {"trend_strength": {"foo_points": [[0, 10], [0, 20]]}}}).axes
