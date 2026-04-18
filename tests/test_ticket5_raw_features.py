from __future__ import annotations

from dataclasses import dataclass

import pytest

from scanner.config import ScannerConfig
from scanner.features import build_feature_bundle, compute_raw_1d, compute_raw_4h, compute_raw_shared


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

    with pytest.raises(ValueError):
        ScannerConfig(raw={"features": {"segmentation_window_4h": 1}}).feature_layer_config
