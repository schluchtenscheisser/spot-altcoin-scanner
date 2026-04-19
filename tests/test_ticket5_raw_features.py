from __future__ import annotations

from dataclasses import dataclass
from math import nan

import pytest

from scanner.config import ScannerConfig
from scanner.features import build_feature_bundle, compute_raw_1d, compute_raw_4h, compute_raw_shared
from scanner.features.models import RawFeatures4H
from scanner.features.raw_4h import _close_vs_high20_4h_pct


@dataclass(frozen=True)
class Bar:
    close_time_utc_ms: int
    close: float
    high: float
    low: float
    base_volume: float
    quote_volume: float


def _bars(n: int, step_ms: int, start: int = 0) -> list[Bar]:
    out = []
    for i in range(n):
        close = 100.0 + i
        out.append(
            Bar(
                close_time_utc_ms=start + ((i + 1) * step_ms),
                close=close,
                high=close + 1.0,
                low=close - 1.0,
                base_volume=1000 + (i * 10),
                quote_volume=(1000 + (i * 10)) * close,
            )
        )
    return out


def _bars_with_structural_break(anchor: float, break_close: float, last_close: float, n: int = 30) -> list[Bar]:
    bars: list[Bar] = []
    for i in range(n):
        close_time = (i + 1) * 14_400_000
        if i < 25:
            close = anchor
            high = anchor
            low = anchor * 0.99 if anchor != 0 else -1.0
        elif i == 25:
            close = break_close
            high = break_close
            low = min(anchor, break_close) * 0.99
        else:
            close = last_close
            high = max(last_close, anchor) + 0.01
            low = min(last_close, anchor) - 0.01
        bars.append(
            Bar(
                close_time_utc_ms=close_time,
                close=close,
                high=high,
                low=low,
                base_volume=1000 + i,
                quote_volume=(1000 + i) * (close if close == close else 1.0),
            )
        )
    return bars


def test_compute_raw_1d_core_fields_ok() -> None:
    cfg = ScannerConfig(raw={})
    raw = compute_raw_1d("BTCUSDT", {"daily_bar_id": 1}, _bars(160, 86_400_000), cfg)
    assert raw.close_vs_ema50_1d_pct_status == "ok"
    assert raw.volume_1d_current_vs_median10_status == "ok"
    assert raw.range_width_10bars_1d_pct_status == "ok"


def test_compute_raw_4h_none_when_unavailable() -> None:
    cfg = ScannerConfig(raw={})
    raw4h = compute_raw_4h("ETHUSDT", {"daily_bar_id": 1}, None, cfg)
    assert raw4h is None


def test_shared_field_cross_timeframe() -> None:
    cfg = ScannerConfig(raw={})
    raw1d = compute_raw_1d("SOLUSDT", {"daily_bar_id": 1}, _bars(160, 86_400_000), cfg)
    raw4h = compute_raw_4h("SOLUSDT", {"daily_bar_id": 1}, _bars(200, 14_400_000), cfg)
    shared = compute_raw_shared("SOLUSDT", {"daily_bar_id": 1}, raw1d, raw4h, cfg)
    assert shared.range_width_12bars_4h_vs_atr1d_pct_status == "ok"
    assert shared.range_width_12bars_4h_vs_atr1d_pct is not None


def test_bundle_order_and_contract() -> None:
    cfg = ScannerConfig(raw={})
    ctx = {
        "daily_bar_id": 111,
        "intraday_bar_id": 222,
        "daily_close_time_utc_ms": 111,
        "intraday_close_time_utc_ms": 222,
    }
    bundle = build_feature_bundle("XRPUSDT", ctx, _bars(180, 86_400_000), _bars(220, 14_400_000), cfg)
    assert bundle.raw_1d is not None
    assert bundle.raw_shared is not None
    assert bundle.raw_4h is not None
    assert bundle.data_4h_available is True


def test_input_validation() -> None:
    cfg = ScannerConfig(raw={})
    with pytest.raises(ValueError):
        compute_raw_1d("btcusdt", {"daily_bar_id": 1}, _bars(2, 86_400_000), cfg)
    with pytest.raises(ValueError):
        compute_raw_1d("BTCUSDT", {"daily_bar_id": 1}, [], cfg)
    with pytest.raises(ValueError):
        compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, [], cfg)


def test_config_defaults_and_invalid() -> None:
    cfg = ScannerConfig(raw={})
    resolved = cfg.feature_layer_config
    assert resolved["segmentation_window_4h"] == 20
    assert resolved["structural_break"]["min_bars_below_before_break"] == 3
    assert resolved["volume_shift_lookback_4h"] == 120
    assert resolved["range_high_lookback_4h"] == 20

    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": {"segmentation_window_4h": 1}}).feature_layer_config


def test_volume_spike_persistence_4h_requires_full_lookback() -> None:
    cfg = ScannerConfig(raw={"features": {"persistence_spike_threshold": 1.2}})
    partial = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, _bars(13, 14_400_000), cfg)
    assert partial is not None
    assert partial.volume_spike_persistence_4h is None
    assert partial.volume_spike_persistence_4h_status == "insufficient_history"

    boosted = _bars(14, 14_400_000)
    boosted = [
        Bar(
            close_time_utc_ms=b.close_time_utc_ms,
            close=b.close,
            high=b.high,
            low=b.low,
            base_volume=b.base_volume,
            quote_volume=(b.quote_volume * 3.0) if i >= 10 else b.quote_volume,
        )
        for i, b in enumerate(boosted)
    ]
    full = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, boosted, cfg)
    assert full is not None
    assert full.volume_spike_persistence_4h_status == "ok"
    assert full.volume_spike_persistence_4h == pytest.approx(1.0)


def test_1d_gap_in_required_window_sets_gap_status_field_local() -> None:
    cfg = ScannerConfig(raw={})
    bars = _bars(20, 86_400_000)
    # inject one missing daily bar inside the last-10 required window by shifting newer bars +1 day
    gapped = []
    for i, b in enumerate(bars):
        if i >= 12:
            gapped.append(
                Bar(
                    close_time_utc_ms=b.close_time_utc_ms + 86_400_000,
                    close=b.close,
                    high=b.high,
                    low=b.low,
                    base_volume=b.base_volume,
                    quote_volume=b.quote_volume,
                )
            )
        else:
            gapped.append(b)

    raw = compute_raw_1d("BTCUSDT", {"daily_bar_id": 1}, gapped, cfg)
    assert raw.range_width_10bars_1d_pct is None
    assert raw.range_width_10bars_1d_pct_status == "gap_in_required_window"
    # field-local behavior: unrelated short-window field still computes
    assert raw.close_vs_rolling_high_5_1d_pct_status == "ok"


def test_1d_contiguous_sequence_still_computes_normally() -> None:
    cfg = ScannerConfig(raw={})
    raw = compute_raw_1d("BTCUSDT", {"daily_bar_id": 1}, _bars(20, 86_400_000), cfg)
    assert raw.range_width_10bars_1d_pct_status == "ok"
    assert raw.range_width_10bars_1d_pct is not None


def test_features_config_type_validation_and_partial_merge() -> None:
    assert ScannerConfig(raw={}).feature_layer_config["segmentation_window_1d"] == 15

    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": 123}).feature_layer_config
    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": ["bad"]}).feature_layer_config

    merged = ScannerConfig(raw={"features": {"segmentation_window_1d": 21}}).feature_layer_config
    assert merged["segmentation_window_1d"] == 21
    assert merged["segmentation_window_4h"] == 20


def test_raw_4h_naming_consolidation_removes_deprecated_anchor_name() -> None:
    fields = RawFeatures4H.__dataclass_fields__
    assert "fixed_structural_break_anchor_4h" in fields
    assert "fixed_high20_break_anchor_4h" not in fields


def test_fixed_structural_anchor_still_computed_after_rename() -> None:
    cfg = ScannerConfig(raw={})
    bars = _bars(30, 14_400_000)
    bars = [
        Bar(
            close_time_utc_ms=b.close_time_utc_ms,
            close=100.0 if i < 25 else 120.0,
            high=101.0 if i < 25 else 121.0,
            low=99.0 if i < 25 else 119.0,
            base_volume=b.base_volume,
            quote_volume=b.quote_volume,
        )
        for i, b in enumerate(bars)
    ]
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.fixed_structural_break_anchor_4h_status == "ok"
    assert raw.fixed_structural_break_anchor_4h is not None


def test_bars_since_last_volume_shift_found_at_offset_with_threshold_inclusive() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 12, "persistence_spike_threshold": 1.2}})
    bars = _bars(40, 14_400_000)
    idx = len(bars) - 1 - 4
    baseline = sum(b.quote_volume for b in bars[idx - 10:idx]) / 10.0
    bars[idx] = Bar(**{**bars[idx].__dict__, "quote_volume": baseline * 1.2})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h == 4
    assert raw.bars_since_last_volume_shift_4h_status == "ok"


def test_bars_since_last_volume_shift_no_event_returns_lookback_cap() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 6, "persistence_spike_threshold": 9.0}})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, _bars(40, 14_400_000), cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h == 6
    assert raw.bars_since_last_volume_shift_4h_status == "ok"


def test_bars_since_last_volume_shift_insufficient_history() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 50}})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, _bars(30, 14_400_000), cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h is None
    assert raw.bars_since_last_volume_shift_4h_status == "insufficient_history"


def test_bars_since_last_volume_shift_skips_upstream_null_bars() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 12, "persistence_spike_threshold": 1.2}})
    bars = _bars(40, 14_400_000)
    newest_idx = len(bars) - 1
    bars[newest_idx] = Bar(**{**bars[newest_idx].__dict__, "quote_volume": 0.0})
    idx = len(bars) - 1 - 1
    baseline = sum(b.quote_volume for b in bars[idx - 10:idx]) / 10.0
    bars[idx] = Bar(**{**bars[idx].__dict__, "quote_volume": baseline * 2.0})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h == 1
    assert raw.bars_since_last_volume_shift_4h_status == "ok"


def test_bars_since_last_volume_shift_null_bars_do_not_poison_no_event_result() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 12, "persistence_spike_threshold": 9.0}})
    bars = _bars(40, 14_400_000)
    for i in range(3):
        idx = len(bars) - 1 - i
        bars[idx] = Bar(**{**bars[idx].__dict__, "quote_volume": 0.0})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h == 12
    assert raw.bars_since_last_volume_shift_4h_status == "ok"


def test_bars_since_last_volume_shift_upstream_dependency_null_when_all_window_bars_non_evaluable() -> None:
    cfg = ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 12}})
    bars = _bars(40, 14_400_000)
    for i in range(22):
        idx = len(bars) - 1 - i
        bars[idx] = Bar(**{**bars[idx].__dict__, "quote_volume": 0.0})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.bars_since_last_volume_shift_4h is None
    assert raw.bars_since_last_volume_shift_4h_status == "upstream_dependency_null"


def test_distance_to_range_high_standard_and_configured_window() -> None:
    cfg = ScannerConfig(raw={"features": {"range_high_lookback_4h": 10}})
    bars = _bars(30, 14_400_000)
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    rolling_high = max(b.high for b in bars[-10:])
    expected = abs((rolling_high - bars[-1].close) / rolling_high) * 100.0
    assert raw.distance_to_range_high_pct_abs_status == "ok"
    assert raw.distance_to_range_high_pct_abs == pytest.approx(expected)


def test_distance_to_range_high_close_above_range_high_stays_non_negative() -> None:
    cfg = ScannerConfig(raw={"features": {"range_high_lookback_4h": 8}})
    bars = _bars(30, 14_400_000)
    bars[-1] = Bar(**{**bars[-1].__dict__, "close": bars[-1].high + 25.0})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.distance_to_range_high_pct_abs_status == "ok"
    assert raw.distance_to_range_high_pct_abs is not None
    assert raw.distance_to_range_high_pct_abs >= 0


def test_distance_to_range_high_insufficient_history() -> None:
    cfg = ScannerConfig(raw={"features": {"range_high_lookback_4h": 31}})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, _bars(30, 14_400_000), cfg)
    assert raw is not None
    assert raw.distance_to_range_high_pct_abs is None
    assert raw.distance_to_range_high_pct_abs_status == "insufficient_history"


def test_distance_to_range_high_zero_rolling_high_is_invalid() -> None:
    cfg = ScannerConfig(raw={"features": {"range_high_lookback_4h": 5}})
    bars = _bars(20, 14_400_000)
    bars = [Bar(**{**b.__dict__, "high": 0.0}) if i >= len(bars) - 5 else b for i, b in enumerate(bars)]
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.distance_to_range_high_pct_abs is None
    assert raw.distance_to_range_high_pct_abs_status == "invalid_upstream_value"


def test_distance_to_range_high_non_finite_window_is_invalid() -> None:
    cfg = ScannerConfig(raw={"features": {"range_high_lookback_4h": 6}})
    bars = _bars(20, 14_400_000)
    bars[-3] = Bar(**{**bars[-3].__dict__, "high": nan})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.distance_to_range_high_pct_abs is None
    assert raw.distance_to_range_high_pct_abs_status == "invalid_upstream_value"


def test_new_feature_keys_validate_bounds_and_partial_defaults() -> None:
    assert ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 24}}).feature_layer_config["range_high_lookback_4h"] == 20
    assert ScannerConfig(raw={"features": {"range_high_lookback_4h": 30}}).feature_layer_config["volume_shift_lookback_4h"] == 120
    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": {"volume_shift_lookback_4h": 0}}).feature_layer_config
    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": {"range_high_lookback_4h": -5}}).feature_layer_config


def test_new_fields_present_in_bundle_and_raw_4h_none_when_missing() -> None:
    cfg = ScannerConfig(raw={})
    bundle = build_feature_bundle(
        "XRPUSDT",
        {"daily_bar_id": 1, "daily_close_time_utc_ms": 1},
        _bars(180, 86_400_000),
        _bars(220, 14_400_000),
        cfg,
    )
    assert bundle.raw_4h is not None
    assert hasattr(bundle.raw_4h, "bars_since_last_volume_shift_4h")
    assert hasattr(bundle.raw_4h, "distance_to_range_high_pct_abs")

    raw4h_none = compute_raw_4h("XRPUSDT", {"daily_bar_id": 1}, None, cfg)
    assert raw4h_none is None


def test_close_vs_high20_4h_pct_standard_case() -> None:
    cfg = ScannerConfig(raw={})
    bars = _bars_with_structural_break(anchor=1.0, break_close=1.2, last_close=1.05)
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.close_vs_high20_4h_pct == pytest.approx(5.0)
    assert raw.close_vs_high20_4h_pct_status == "ok"


def test_close_vs_high20_4h_pct_negative_result() -> None:
    cfg = ScannerConfig(raw={})
    bars = _bars_with_structural_break(anchor=1.0, break_close=1.2, last_close=0.95)
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, bars, cfg)
    assert raw is not None
    assert raw.close_vs_high20_4h_pct == pytest.approx(-5.0)
    assert raw.close_vs_high20_4h_pct_status == "ok"


def test_close_vs_high20_4h_pct_anchor_unavailable() -> None:
    cfg = ScannerConfig(raw={})
    raw = compute_raw_4h("BTCUSDT", {"daily_bar_id": 1}, _bars(20, 14_400_000), cfg)
    assert raw is not None
    assert raw.fixed_structural_break_anchor_4h is None
    assert raw.close_vs_high20_4h_pct is None
    assert raw.close_vs_high20_4h_pct_status == "upstream_dependency_null"


def test_close_vs_high20_4h_pct_anchor_zero() -> None:
    value, status = _close_vs_high20_4h_pct(close_4h=1.05, fixed_structural_break_anchor_4h=0.0, fixed_structural_break_anchor_4h_status="ok")
    assert value is None
    assert status == "invalid_upstream_value"


def test_close_vs_high20_4h_pct_non_finite_anchor() -> None:
    value, status = _close_vs_high20_4h_pct(close_4h=1.05, fixed_structural_break_anchor_4h=float("inf"), fixed_structural_break_anchor_4h_status="ok")
    assert value is None
    assert status == "invalid_upstream_value"


def test_close_vs_high20_4h_pct_non_finite_close() -> None:
    value, status = _close_vs_high20_4h_pct(close_4h=float("nan"), fixed_structural_break_anchor_4h=1.0, fixed_structural_break_anchor_4h_status="ok")
    assert value is None
    assert status == "invalid_upstream_value"


def test_close_vs_high20_4h_pct_fields_present_in_raw4h_and_bundle() -> None:
    fields = RawFeatures4H.__dataclass_fields__
    assert "close_vs_high20_4h_pct" in fields
    assert "close_vs_high20_4h_pct_status" in fields

    cfg = ScannerConfig(raw={})
    bundle = build_feature_bundle(
        "XRPUSDT",
        {"daily_bar_id": 1, "daily_close_time_utc_ms": 1},
        _bars(180, 86_400_000),
        _bars_with_structural_break(anchor=1.0, break_close=1.2, last_close=1.05, n=220),
        cfg,
    )
    assert bundle.raw_4h is not None
    assert hasattr(bundle.raw_4h, "close_vs_high20_4h_pct")
    assert hasattr(bundle.raw_4h, "close_vs_high20_4h_pct_status")
