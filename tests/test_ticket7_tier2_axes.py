from __future__ import annotations

import dataclasses

import pytest

from scanner.axes.models import Tier2AxisBundle
from scanner.axes.tier2 import compute_tier2_axes
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
        daily_bar_id="2026-01-01",
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


def test_tier2_4h_full_path_all_axes_full_resolution():
    fb = _bundle(
        data_4h_available=True,
        raw4={
            "bars_since_last_new_low_4h": 4, "bars_since_last_new_low_4h_status": "ok",
            "range_width_12bars_4h_pct": 9, "range_width_12bars_4h_pct_status": "ok",
            "close_position_in_range_12bars_4h": 0.5, "close_position_in_range_12bars_4h_status": "ok",
            "close_above_range_mid_ratio_12bars_4h": 0.5, "close_above_range_mid_ratio_12bars_4h_status": "ok",
            "pullback_depth_vs_last_impulse_pct_4h": 20, "pullback_depth_vs_last_impulse_pct_4h_status": "ok",
            "pullback_volume_ratio_4h": 1.0, "pullback_volume_ratio_4h_status": "ok",
            "close_vs_ema20_4h_pct": 0, "close_vs_ema20_4h_pct_status": "ok",
            "lowest_low_vs_ema20_4h_pct": -2, "lowest_low_vs_ema20_4h_pct_status": "ok",
            "impulse_start_price_4h": 100, "impulse_start_price_4h_status": "ok",
            "impulse_high_price_4h": 110, "impulse_high_price_4h_status": "ok",
            "close_vs_rolling_high_5_4h_pct": 0, "close_vs_rolling_high_5_4h_pct_status": "ok",
            "volume_4h_current_vs_median10": 1.2, "volume_4h_current_vs_median10_status": "ok",
            "ema20_slope_4h_pct_per_bar": 0, "ema20_slope_4h_pct_per_bar_status": "ok",
        },
    )
    out = compute_tier2_axes(fb, _cfg())
    for axis in [
        "base_integrity_simplified",
        "pullback_quality_simplified",
        "reacceleration_strength_simplified",
    ]:
        assert getattr(out, axis) is not None
        assert getattr(out, f"{axis}_not_evaluable") is False
        assert getattr(out, f"{axis}_reduced_resolution") is False
        assert getattr(out, f"{axis}_effective_weight_ratio") == pytest.approx(1.0)


def test_tier2_1d_fallback_sets_reduced_resolution_true():
    fb = _bundle(
        data_4h_available=False,
        raw1={
            "bars_since_last_new_low_1d": 4, "bars_since_last_new_low_1d_status": "ok",
            "range_width_10bars_1d_pct": 15, "range_width_10bars_1d_pct_status": "ok",
            "close_position_in_range_10bars_1d": 0.5, "close_position_in_range_10bars_1d_status": "ok",
            "close_above_range_mid_ratio_10bars_1d": 0.5, "close_above_range_mid_ratio_10bars_1d_status": "ok",
            "pullback_depth_vs_last_impulse_pct_1d": 20, "pullback_depth_vs_last_impulse_pct_1d_status": "ok",
            "pullback_volume_ratio_1d": 1.0, "pullback_volume_ratio_1d_status": "ok",
            "close_vs_ema20_1d_pct": 0, "close_vs_ema20_1d_pct_status": "ok",
            "lowest_low_vs_ema20_1d_pct": -2, "lowest_low_vs_ema20_1d_pct_status": "ok",
            "impulse_start_price_1d": 100, "impulse_start_price_1d_status": "ok",
            "impulse_high_price_1d": 110, "impulse_high_price_1d_status": "ok",
            "close_vs_rolling_high_5_1d_pct": 0, "close_vs_rolling_high_5_1d_pct_status": "ok",
            "volume_1d_current_vs_median10": 1.2, "volume_1d_current_vs_median10_status": "ok",
            "ema20_slope_1d_pct_per_bar": 0, "ema20_slope_1d_pct_per_bar_status": "ok",
        },
    )
    out = compute_tier2_axes(fb, _cfg())
    assert out.base_integrity_simplified_not_evaluable is False
    assert out.pullback_quality_simplified_not_evaluable is False
    assert out.reacceleration_strength_simplified_not_evaluable is False
    assert out.base_integrity_simplified_reduced_resolution is True
    assert out.pullback_quality_simplified_reduced_resolution is True
    assert out.reacceleration_strength_simplified_reduced_resolution is True


def test_tier2_no_fallthrough_when_4h_available_and_missing_inputs():
    fb = _bundle(
        data_4h_available=True,
        raw1={
            "bars_since_last_new_low_1d": 7, "bars_since_last_new_low_1d_status": "ok",
            "range_width_10bars_1d_pct": 20, "range_width_10bars_1d_pct_status": "ok",
            "close_position_in_range_10bars_1d": 0.9, "close_position_in_range_10bars_1d_status": "ok",
            "close_above_range_mid_ratio_10bars_1d": 0.9, "close_above_range_mid_ratio_10bars_1d_status": "ok",
        },
        raw4={
            "bars_since_last_new_low_4h": 4, "bars_since_last_new_low_4h_status": "ok",
            "range_width_12bars_4h_pct": None, "range_width_12bars_4h_pct_status": "upstream_dependency_null",
            "close_position_in_range_12bars_4h": 0.5, "close_position_in_range_12bars_4h_status": "ok",
            "close_above_range_mid_ratio_12bars_4h": 0.5, "close_above_range_mid_ratio_12bars_4h_status": "ok",
            "impulse_start_price_4h": 100, "impulse_start_price_4h_status": "ok",
            "impulse_high_price_4h": 110, "impulse_high_price_4h_status": "ok",
        },
    )
    out = compute_tier2_axes(fb, _cfg())
    assert out.base_integrity_simplified_not_evaluable is False
    assert out.base_integrity_simplified_reduced_resolution is True
    assert out.base_integrity_simplified_effective_weight_ratio == pytest.approx(0.80)


def test_tier2_both_paths_fail_when_1d_missing():
    out = compute_tier2_axes(_bundle(data_4h_available=False), _cfg())
    for axis in [
        "base_integrity_simplified",
        "pullback_quality_simplified",
        "reacceleration_strength_simplified",
    ]:
        assert getattr(out, axis) is None
        assert getattr(out, f"{axis}_not_evaluable") is True
        assert getattr(out, f"{axis}_effective_weight_ratio") is None
        assert getattr(out, f"{axis}_reduced_resolution") is False


def test_pullback_segmentation_gate_behavior():
    fb_invalid_4h = _bundle(
        raw4={
            "impulse_start_price_4h": 100, "impulse_start_price_4h_status": "ok",
            "impulse_high_price_4h": 90, "impulse_high_price_4h_status": "ok",
            "pullback_depth_vs_last_impulse_pct_4h": 20, "pullback_depth_vs_last_impulse_pct_4h_status": "ok",
            "pullback_volume_ratio_4h": 1.0, "pullback_volume_ratio_4h_status": "ok",
            "close_vs_ema20_4h_pct": 0, "close_vs_ema20_4h_pct_status": "ok",
            "lowest_low_vs_ema20_4h_pct": -2, "lowest_low_vs_ema20_4h_pct_status": "ok",
        }
    )
    out1 = compute_tier2_axes(fb_invalid_4h, _cfg())
    assert out1.pullback_quality_simplified is None
    assert out1.pullback_quality_simplified_not_evaluable is True

    fb_valid_1d = _bundle(
        data_4h_available=False,
        raw1={
            "impulse_start_price_1d": 100, "impulse_start_price_1d_status": "ok",
            "impulse_high_price_1d": 110, "impulse_high_price_1d_status": "ok",
            "pullback_depth_vs_last_impulse_pct_1d": 20, "pullback_depth_vs_last_impulse_pct_1d_status": "ok",
            "pullback_volume_ratio_1d": 1.0, "pullback_volume_ratio_1d_status": "ok",
            "close_vs_ema20_1d_pct": 0, "close_vs_ema20_1d_pct_status": "ok",
            "lowest_low_vs_ema20_1d_pct": -2, "lowest_low_vs_ema20_1d_pct_status": "ok",
        },
    )
    out2 = compute_tier2_axes(fb_valid_1d, _cfg())
    assert out2.pullback_quality_simplified_not_evaluable is False
    assert out2.pullback_quality_simplified_reduced_resolution is True


def test_pullback_non_monotone_curve_points():
    fb = _bundle(
        raw4={
            "impulse_start_price_4h": 100, "impulse_start_price_4h_status": "ok",
            "impulse_high_price_4h": 110, "impulse_high_price_4h_status": "ok",
            "pullback_depth_vs_last_impulse_pct_4h": 10, "pullback_depth_vs_last_impulse_pct_4h_status": "ok",
            "pullback_volume_ratio_4h": 0.6, "pullback_volume_ratio_4h_status": "ok",
            "close_vs_ema20_4h_pct": 0, "close_vs_ema20_4h_pct_status": "ok",
            "lowest_low_vs_ema20_4h_pct": -2, "lowest_low_vs_ema20_4h_pct_status": "ok",
        }
    )
    out = compute_tier2_axes(fb, _cfg())
    expected = 0.35 * 85.0 + 0.25 * 85.0 + 0.20 * 50.0 + 0.20 * 50.0
    assert out.pullback_quality_simplified == pytest.approx(expected)


def test_tier2_output_contract_and_determinism():
    fb = _bundle(
        raw4={
            "bars_since_last_new_low_4h": 4, "bars_since_last_new_low_4h_status": "ok",
            "range_width_12bars_4h_pct": 9, "range_width_12bars_4h_pct_status": "ok",
            "close_position_in_range_12bars_4h": 0.5, "close_position_in_range_12bars_4h_status": "ok",
            "close_above_range_mid_ratio_12bars_4h": 0.5, "close_above_range_mid_ratio_12bars_4h_status": "ok",
            "impulse_start_price_4h": 100, "impulse_start_price_4h_status": "ok",
            "impulse_high_price_4h": 110, "impulse_high_price_4h_status": "ok",
            "pullback_depth_vs_last_impulse_pct_4h": 20, "pullback_depth_vs_last_impulse_pct_4h_status": "ok",
            "pullback_volume_ratio_4h": 1.0, "pullback_volume_ratio_4h_status": "ok",
            "close_vs_ema20_4h_pct": 0, "close_vs_ema20_4h_pct_status": "ok",
            "lowest_low_vs_ema20_4h_pct": -2, "lowest_low_vs_ema20_4h_pct_status": "ok",
            "close_vs_rolling_high_5_4h_pct": 0, "close_vs_rolling_high_5_4h_pct_status": "ok",
            "volume_4h_current_vs_median10": 1.2, "volume_4h_current_vs_median10_status": "ok",
            "ema20_slope_4h_pct_per_bar": 0.1, "ema20_slope_4h_pct_per_bar_status": "ok",
        },
    )
    a = compute_tier2_axes(fb, _cfg())
    b = compute_tier2_axes(fb, _cfg())
    assert isinstance(a, Tier2AxisBundle)
    assert a == b
    assert a.symbol == "TESTUSDT" and a.daily_bar_id == "2026-01-01" and a.intraday_bar_id == 2
    for axis_name in [
        "base_integrity_simplified",
        "pullback_quality_simplified",
        "reacceleration_strength_simplified",
    ]:
        assert not (getattr(a, f"{axis_name}_not_evaluable") and getattr(a, axis_name) is not None)


def test_tier2_cfg_defaults_and_validation():
    cfg = _cfg()
    assert cfg.axes["base_integrity_simplified"]["range_width_12bars_4h_pct"]["mid"] == pytest.approx(9.0)
    assert cfg.axes["pullback_quality_simplified"]["pullback_depth_vs_last_impulse_pct_4h"]["points"][1] == (20.0, 100.0)

    cfg_override = _cfg({"axes": {"reacceleration_strength_simplified": {"close_vs_rolling_high_5_4h_pct": {"high": 5.0}}}})
    assert cfg_override.axes["reacceleration_strength_simplified"]["close_vs_rolling_high_5_4h_pct"]["high"] == pytest.approx(5.0)
    assert cfg_override.axes["reacceleration_strength_simplified"]["close_vs_rolling_high_5_4h_pct"]["mid"] == pytest.approx(0.0)

    with pytest.raises(ValueError):
        _cfg({"axes": {"base_integrity_simplified": {"range_width_12bars_4h_pct": {"low_good": 10, "mid": 9, "high_bad": 18}}}}).axes
    with pytest.raises(ValueError):
        _cfg({"axes": {"pullback_quality_simplified": {"pullback_depth_vs_last_impulse_pct_4h": {"points": [[0, 0], [0, 10]]}}}}).axes
