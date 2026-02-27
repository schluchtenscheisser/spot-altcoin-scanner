from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, Mapping, Optional, Sequence


DEFAULT_T_TRIGGER_MAX = 5
DEFAULT_T_HOLD = 10
DEFAULT_THRESHOLDS_PCT = (10.0, 20.0)


def _to_float(value: Any) -> Optional[float]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if numeric != numeric:
        return None
    return numeric


def _threshold_key(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else str(value)


def _parse_date(value: str) -> Optional[date]:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError):
        return None


def _resolve_thresholds(params: Mapping[str, Any]) -> list[float]:
    raw = params.get("thresholds_pct", DEFAULT_THRESHOLDS_PCT)
    resolved: set[float] = set()
    for value in raw:
        numeric = _to_float(value)
        if numeric is None:
            continue
        resolved.add(numeric)
    resolved.add(10.0)
    resolved.add(20.0)
    return sorted(resolved)


def _trade_level_status(setup_type: str, trade_levels: Mapping[str, Any]) -> tuple[bool, bool]:
    if setup_type == "breakout":
        has_entry_trigger = "entry_trigger" in trade_levels
        has_breakout_level = "breakout_level_20" in trade_levels
        if not has_entry_trigger and not has_breakout_level:
            return True, False

        trigger = _to_float(trade_levels.get("entry_trigger"))
        breakout = _to_float(trade_levels.get("breakout_level_20"))
        trigger_invalid = has_entry_trigger and (trigger is None or trigger <= 0)
        breakout_invalid = has_breakout_level and (breakout is None or breakout <= 0)

        if has_entry_trigger and has_breakout_level:
            if trigger_invalid and breakout_invalid:
                return False, True
            return False, False

        if has_entry_trigger and trigger_invalid:
            return False, True
        if has_breakout_level and breakout_invalid:
            return False, True
        return False, False

    if setup_type == "reversal":
        if "entry_trigger" not in trade_levels:
            return True, False
        trigger = _to_float(trade_levels.get("entry_trigger"))
        if trigger is None or trigger <= 0:
            return False, True
        return False, False

    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone")
        if not isinstance(zone, Mapping):
            return True, False

        missing = "lower" not in zone or "upper" not in zone
        if missing:
            return True, False

        lower = _to_float(zone.get("lower"))
        upper = _to_float(zone.get("upper"))
        if lower is None or upper is None or lower <= 0 or upper <= 0 or lower > upper:
            return False, True
        return False, False

    return True, False


def _is_triggered(setup_type: str, close: float, trade_levels: Mapping[str, Any]) -> bool:
    if setup_type == "breakout":
        trigger = _to_float(trade_levels.get("entry_trigger"))
        fallback = _to_float(trade_levels.get("breakout_level_20"))
        level = trigger if trigger is not None and trigger > 0 else fallback
        return level is not None and level > 0 and close >= level

    if setup_type == "reversal":
        trigger = _to_float(trade_levels.get("entry_trigger"))
        return trigger is not None and trigger > 0 and close >= trigger

    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone")
        if not isinstance(zone, Mapping):
            return False
        lower = _to_float(zone.get("lower"))
        upper = _to_float(zone.get("upper"))
        if lower is None or upper is None or lower > upper:
            return False
        return lower <= close <= upper

    return False


def evaluate_e2_candidate(
    *,
    t0_date: str,
    setup_type: str,
    trade_levels: Mapping[str, Any],
    price_series: Mapping[str, Mapping[str, Any]],
    params: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    runtime_params = params or {}
    t_trigger_max = int(runtime_params.get("T_trigger_max", DEFAULT_T_TRIGGER_MAX))
    t_hold = int(runtime_params.get("T_hold", DEFAULT_T_HOLD))
    thresholds = _resolve_thresholds(runtime_params)

    hits: Dict[str, Optional[bool]] = {_threshold_key(threshold): None for threshold in thresholds}

    t0 = _parse_date(t0_date)
    missing_trade_levels, invalid_trade_levels = _trade_level_status(setup_type, trade_levels)
    if t0 is None:
        return {
            "reason": "missing_price_series",
            "t_trigger_date": None,
            "t_trigger_day_offset": None,
            "entry_price": None,
            "hit_10": None,
            "hit_20": None,
            "hits": hits,
            "mfe_pct": None,
            "mae_pct": None,
        }

    has_evaluable_close = False
    trigger_date: Optional[date] = None
    trigger_day_offset: Optional[int] = None
    entry_price: Optional[float] = None

    for offset in range(t_trigger_max + 1):
        day = t0 + timedelta(days=offset)
        candle = price_series.get(day.isoformat())
        close = _to_float(candle.get("close") if isinstance(candle, Mapping) else None)
        if close is None:
            continue
        has_evaluable_close = True
        if _is_triggered(setup_type, close, trade_levels):
            trigger_date = day
            trigger_day_offset = offset
            entry_price = close
            break

    missing_price_series = not has_evaluable_close
    invalid_entry_price = trigger_date is not None and (entry_price is None or entry_price <= 0)
    no_trigger = trigger_date is None

    insufficient_forward_history = False
    max_high: Optional[float] = None
    min_low: Optional[float] = None
    if trigger_date is not None:
        highs: list[float] = []
        lows: list[float] = []
        for hold_offset in range(1, t_hold + 1):
            hold_day = trigger_date + timedelta(days=hold_offset)
            candle = price_series.get(hold_day.isoformat())
            high = _to_float(candle.get("high") if isinstance(candle, Mapping) else None)
            low = _to_float(candle.get("low") if isinstance(candle, Mapping) else None)
            if high is None or low is None:
                insufficient_forward_history = True
                break
            highs.append(high)
            lows.append(low)

        if not insufficient_forward_history and highs and entry_price is not None and entry_price > 0:
            max_high = max(highs)
            min_low = min(lows)
            for threshold in thresholds:
                target = entry_price * (1 + threshold / 100.0)
                hits[_threshold_key(threshold)] = max_high >= target

    if missing_price_series:
        reason = "missing_price_series"
    elif invalid_entry_price:
        reason = "invalid_entry_price"
    elif missing_trade_levels:
        reason = "missing_trade_levels"
    elif invalid_trade_levels:
        reason = "invalid_trade_levels"
    elif no_trigger:
        reason = "no_trigger"
    elif insufficient_forward_history:
        reason = "insufficient_forward_history"
    else:
        reason = "ok"

    hit_10 = hits.get("10")
    hit_20 = hits.get("20")

    mfe_pct = None
    mae_pct = None
    if reason == "ok" and entry_price is not None and entry_price > 0 and max_high is not None and min_low is not None:
        mfe_pct = (max_high / entry_price - 1.0) * 100.0
        mae_pct = (min_low / entry_price - 1.0) * 100.0

    return {
        "reason": reason,
        "t_trigger_date": trigger_date.isoformat() if trigger_date is not None else None,
        "t_trigger_day_offset": trigger_day_offset,
        "entry_price": entry_price,
        "hit_10": hit_10,
        "hit_20": hit_20,
        "hits": hits,
        "mfe_pct": mfe_pct,
        "mae_pct": mae_pct,
    }
