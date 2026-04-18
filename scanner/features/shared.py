from __future__ import annotations

import math
from typing import Any

from scanner.features.models import RawFeatures1D, RawFeatures4H, RawFeaturesShared


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str):
        raise TypeError("symbol must be str")
    normalized = symbol.strip()
    if not normalized or normalized != normalized.upper():
        raise ValueError("symbol must be non-empty uppercase string")
    return normalized


def _validate_bar_clock_context(bar_clock_context: Any) -> None:
    if bar_clock_context is None:
        raise TypeError("bar_clock_context must not be None")


def compute_raw_shared(
    symbol: str,
    bar_clock_context: Any,
    raw_1d: RawFeatures1D,
    raw_4h: RawFeatures4H | None,
    cfg: Any,
) -> RawFeaturesShared:
    _validate_symbol(symbol)
    _validate_bar_clock_context(bar_clock_context)
    if not isinstance(raw_1d, RawFeatures1D):
        raise TypeError("raw_1d must be RawFeatures1D")
    if raw_4h is not None and not isinstance(raw_4h, RawFeatures4H):
        raise TypeError("raw_4h must be RawFeatures4H or None")

    if raw_4h is None:
        return RawFeaturesShared(None, "upstream_dependency_null")

    range_width = raw_4h.range_width_12bars_4h_pct
    atr_1d = raw_1d.atr_1d
    if range_width is None or atr_1d is None:
        return RawFeaturesShared(None, "upstream_dependency_null")
    if not (math.isfinite(range_width) and math.isfinite(atr_1d)) or atr_1d <= 0:
        return RawFeaturesShared(None, "invalid_upstream_value")

    return RawFeaturesShared((range_width / atr_1d) * 100.0, "ok")
