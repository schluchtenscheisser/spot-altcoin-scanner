"""Deterministic trade-level derivation and Phase-1 risk-field preparation for downstream consumers."""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

from scanner.config import resolve_risk_min_rr_to_target_1


def _to_float(value: Any) -> Optional[float]:
    try:
        if value is None:
            return None
        parsed = float(value)
        if not math.isfinite(parsed):
            return None
        return parsed
    except (TypeError, ValueError):
        return None


def _atr_absolute(tf_features: Dict[str, Any]) -> Optional[float]:
    atr_pct = _to_float(tf_features.get("atr_pct"))
    close = _to_float(tf_features.get("close"))
    if atr_pct is None or close is None:
        return None
    return (atr_pct / 100.0) * close


def _targets(base: Optional[float], atr: Optional[float], multipliers: list[float]) -> list[Optional[float]]:
    if base is None or atr is None:
        return [None for _ in multipliers]
    return [base + (k * atr) for k in multipliers]


def breakout_trade_levels(features: Dict[str, Any], multipliers: list[float]) -> Dict[str, Any]:
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


def pullback_trade_levels(features: Dict[str, Any], multipliers: list[float], pb_tol_pct: float) -> Dict[str, Any]:
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


def reversal_trade_levels(features: Dict[str, Any], multipliers: list[float]) -> Dict[str, Any]:
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


def _risk_cfg(root_config: Dict[str, Any]) -> Dict[str, float]:
    risk_cfg = root_config.get("risk", {}) if isinstance(root_config, dict) else {}
    return {
        "atr_multiple": float(risk_cfg.get("atr_multiple", 2.0)),
        "min_stop_distance_pct": float(risk_cfg.get("min_stop_distance_pct", 4.0)),
        "max_stop_distance_pct": float(risk_cfg.get("max_stop_distance_pct", 12.0)),
        "min_rr_to_target_1": resolve_risk_min_rr_to_target_1(risk_cfg),
    }


def _planned_entry_price(setup_type: str, trade_levels: Dict[str, Any]) -> Optional[float]:
    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone") if isinstance(trade_levels.get("entry_zone"), dict) else {}
        return _to_float(zone.get("center"))
    return _to_float(trade_levels.get("entry_trigger"))


def compute_phase1_risk_fields(setup_type: str, trade_levels: Dict[str, Any], root_config: Dict[str, Any]) -> Dict[str, Any]:
    cfg = _risk_cfg(root_config)
    entry_price = _planned_entry_price(setup_type, trade_levels)
    atr_value = _to_float(trade_levels.get("atr_value"))

    result: Dict[str, Any] = {
        "stop_price_initial": None,
        "stop_source": None,
        "risk_pct_to_stop": None,
        "rr_to_target_1": None,
        "rr_to_target_2": None,
        "rr_to_target_3": None,
        "risk_acceptable": None,
    }

    # Canonical target ladder defaults to nullable until a valid effective stop is derivable.
    trade_levels["targets"] = [None, None, None]

    if entry_price is None or entry_price <= 0:
        return result

    invalidation = _to_float(trade_levels.get("invalidation"))
    stop_price_initial: Optional[float] = None
    stop_source: Optional[str] = None
    if invalidation is not None and invalidation > 0 and invalidation < entry_price:
        stop_price_initial = invalidation
        stop_source = "invalidation"

    if stop_price_initial is None and atr_value is not None and atr_value > 0:
        atr_stop = entry_price - (cfg["atr_multiple"] * atr_value)
        if atr_stop < entry_price:
            stop_price_initial = atr_stop
            stop_source = "atr_fallback"

    if stop_price_initial is None:
        return result
    if stop_price_initial >= entry_price:
        return result

    risk_abs = entry_price - stop_price_initial
    if risk_abs <= 0:
        return result

    risk_pct_to_stop = (risk_abs / entry_price) * 100.0

    result.update(
        {
            "stop_price_initial": stop_price_initial,
            "stop_source": stop_source,
            "risk_pct_to_stop": risk_pct_to_stop,
        }
    )

    target_1 = entry_price + risk_abs
    target_2 = entry_price + (2.0 * risk_abs)
    target_3 = entry_price + (3.0 * risk_abs)
    trade_levels["targets"] = [target_1, target_2, target_3]

    rr_to_target_1 = (target_1 - entry_price) / risk_abs
    rr_to_target_2 = (target_2 - entry_price) / risk_abs
    rr_to_target_3 = (target_3 - entry_price) / risk_abs

    risk_acceptable = (
        cfg["min_stop_distance_pct"] <= risk_pct_to_stop <= cfg["max_stop_distance_pct"]
        and rr_to_target_2 is not None
        and rr_to_target_2 >= cfg["min_rr_to_target_1"]
    )

    result.update(
        {
            "rr_to_target_1": rr_to_target_1,
            "rr_to_target_2": rr_to_target_2,
            "rr_to_target_3": rr_to_target_3,
            "risk_acceptable": risk_acceptable,
        }
    )
    return result
