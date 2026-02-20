"""Deterministic trade-level helpers (output-only, no scoring impact)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _atr_absolute(tf_features: Dict[str, Any]) -> Optional[float]:
    atr_pct = _to_float(tf_features.get("atr_pct"))
    close = _to_float(tf_features.get("close"))
    if atr_pct is None or close is None:
        return None
    return (atr_pct / 100.0) * close


def _targets(base: Optional[float], atr: Optional[float], multipliers: List[float]) -> List[Optional[float]]:
    if base is None or atr is None:
        return [None for _ in multipliers]
    return [base + (k * atr) for k in multipliers]


def breakout_trade_levels(features: Dict[str, Any], multipliers: List[float]) -> Dict[str, Any]:
    f1d = features.get("1d", {})
    close_1d = _to_float(f1d.get("close"))
    breakout_dist_20 = _to_float(f1d.get("breakout_dist_20"))

    breakout_level_20: Optional[float] = None
    if close_1d is not None and breakout_dist_20 is not None and (100.0 + breakout_dist_20) != 0.0:
        breakout_level_20 = close_1d / (1.0 + breakout_dist_20 / 100.0)

    ema20_1d = _to_float(f1d.get("ema_20"))
    invalidation = min(v for v in [breakout_level_20, ema20_1d] if v is not None) if any(
        v is not None for v in [breakout_level_20, ema20_1d]
    ) else None

    atr_1d = _atr_absolute(f1d)
    return {
        "entry_trigger": breakout_level_20,
        "breakout_level_20": breakout_level_20,
        "invalidation": invalidation,
        "targets": _targets(breakout_level_20, atr_1d, multipliers),
        "atr_value": atr_1d,
    }


def pullback_trade_levels(features: Dict[str, Any], multipliers: List[float], pb_tol_pct: float) -> Dict[str, Any]:
    f4h = features.get("4h", {})
    ema20_4h = _to_float(f4h.get("ema_20"))
    ema50_4h = _to_float(f4h.get("ema_50"))

    zone = {
        "center": ema20_4h,
        "lower": None if ema20_4h is None else ema20_4h * (1.0 - pb_tol_pct / 100.0),
        "upper": None if ema20_4h is None else ema20_4h * (1.0 + pb_tol_pct / 100.0),
        "tolerance_pct": pb_tol_pct,
    }
    atr_4h = _atr_absolute(f4h)
    return {
        "entry_zone": zone,
        "invalidation": ema50_4h,
        "targets": _targets(ema20_4h, atr_4h, multipliers),
        "atr_value": atr_4h,
    }


def reversal_trade_levels(features: Dict[str, Any], multipliers: List[float]) -> Dict[str, Any]:
    f1d = features.get("1d", {})
    ema20_1d = _to_float(f1d.get("ema_20"))
    base_low = _to_float(f1d.get("base_low"))
    atr_1d = _atr_absolute(f1d)
    return {
        "entry_trigger": ema20_1d,
        "invalidation": base_low,
        "targets": _targets(ema20_1d, atr_1d, multipliers),
        "atr_value": atr_1d,
    }

