from __future__ import annotations

"""Deterministic backtest runner (Analytics-only, E2-K).

Canonical v2 rules (Feature-Spec section 10):
- Trigger search on 1D close within ``[t0 .. t0 + T_trigger_max]``
- ``entry_price = close[trigger_day]``
- ``hit_10`` / ``hit_20`` use ``max(high[trigger_day+1 .. trigger_day+T_hold])``
- No exit logic.
"""

from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import json


DEFAULT_BACKTEST_CFG: Dict[str, Any] = {
    "t_hold": 10,
    "t_trigger_max": 5,
    "thresholds_pct": [10.0, 20.0],
}

BREAKOUT_TREND_SETUP_IDS = {"breakout_immediate_1_5d", "breakout_retest_1_5d"}
FOUR_H_TIME_STOP_CANDLES = 42  # 168h / 4h


def _float_or_none(value: Any) -> Optional[float]:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    if f != f:  # NaN guard
        return None
    return f


def _extract_backtest_config(config: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    if not config:
        return dict(DEFAULT_BACKTEST_CFG)

    bt = config.get("backtest", config)
    out = dict(DEFAULT_BACKTEST_CFG)

    # Canonical aliases in case legacy keys still exist.
    out["t_hold"] = int(bt.get("t_hold", bt.get("max_holding_days", out["t_hold"])))
    out["t_trigger_max"] = int(bt.get("t_trigger_max", out["t_trigger_max"]))

    if "thresholds_pct" in bt:
        out["thresholds_pct"] = [float(x) for x in bt.get("thresholds_pct", [])]
    elif "thresholds" in bt:
        out["thresholds_pct"] = [float(x) for x in bt.get("thresholds", [])]

    return out


def _setup_triggered(setup_type: str, close: float, trade_levels: Mapping[str, Any]) -> bool:
    if setup_type == "breakout":
        trigger = _float_or_none(trade_levels.get("entry_trigger") or trade_levels.get("breakout_level_20"))
        return trigger is not None and close >= trigger
    if setup_type == "reversal":
        trigger = _float_or_none(trade_levels.get("entry_trigger"))
        return trigger is not None and close >= trigger
    if setup_type == "pullback":
        zone = trade_levels.get("entry_zone") or {}
        low = _float_or_none(zone.get("lower"))
        high = _float_or_none(zone.get("upper"))
        return low is not None and high is not None and low <= close <= high
    return False


def _evaluate_candidate(
    *,
    symbol: str,
    setup_type: str,
    t0_date: str,
    index_by_date: Mapping[str, int],
    series_close: Sequence[Optional[float]],
    series_high: Sequence[Optional[float]],
    trade_levels: Mapping[str, Any],
    t_trigger_max: int,
    t_hold: int,
    thresholds_pct: Sequence[float],
) -> Dict[str, Any]:
    def _iso_to_date(value: str) -> Optional[date]:
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            return None

    def _calendar_window_indices(
        *,
        start_date: date,
        days_inclusive: int,
    ) -> Iterable[Tuple[int, int]]:
        for day_offset in range(days_inclusive + 1):
            day = (start_date + timedelta(days=day_offset)).isoformat()
            idx = index_by_date.get(day)
            if idx is None:
                continue
            yield day_offset, idx

    t0_parsed = _iso_to_date(t0_date)
    if t0_parsed is None:
        return {
            "symbol": symbol,
            "setup_type": setup_type,
            "t0_date": t0_date,
            "triggered": False,
            "trigger_day_offset": None,
            "entry_price": None,
            "max_high_after_entry": None,
            **{f"hit_{int(thr)}": False for thr in thresholds_pct},
        }

    trigger_idx: Optional[int] = None
    trigger_day_offset: Optional[int] = None
    for day_offset, idx in _calendar_window_indices(start_date=t0_parsed, days_inclusive=t_trigger_max):
        close = series_close[idx]
        if close is None:
            continue
        if _setup_triggered(setup_type, close, trade_levels):
            trigger_idx = idx
            trigger_day_offset = day_offset
            break

    outcome: Dict[str, Any] = {
        "symbol": symbol,
        "setup_type": setup_type,
        "t0_date": t0_date,
        "triggered": trigger_idx is not None,
        "trigger_day_offset": None,
        "entry_price": None,
        "max_high_after_entry": None,
    }

    for thr in thresholds_pct:
        outcome[f"hit_{int(thr)}"] = False

    if trigger_idx is None:
        return outcome

    entry_price = series_close[trigger_idx]
    if entry_price is None or entry_price <= 0:
        return outcome

    trigger_date = t0_parsed + timedelta(days=trigger_day_offset or 0)
    window_highs: List[float] = []
    for hold_offset in range(1, t_hold + 1):
        hold_day = (trigger_date + timedelta(days=hold_offset)).isoformat()
        hold_idx = index_by_date.get(hold_day)
        if hold_idx is None:
            continue
        high = series_high[hold_idx]
        if high is None:
            continue
        window_highs.append(high)

    max_high = max(window_highs) if window_highs else None

    outcome.update(
        {
            "trigger_day_offset": trigger_day_offset,
            "entry_price": entry_price,
            "max_high_after_entry": max_high,
        }
    )

    if max_high is None:
        return outcome

    for thr in thresholds_pct:
        target = entry_price * (1.0 + thr / 100.0)
        outcome[f"hit_{int(thr)}"] = max_high >= target

    return outcome


def _summarize(events: Sequence[Dict[str, Any]], thresholds_pct: Sequence[float]) -> Dict[str, Any]:
    total = len(events)
    triggered = [e for e in events if e.get("triggered")]
    summary: Dict[str, Any] = {
        "count": total,
        "triggered_count": len(triggered),
        "trigger_rate": (len(triggered) / total) if total else 0.0,
    }

    for thr in thresholds_pct:
        key = f"hit_{int(thr)}"
        hit_count = sum(1 for e in triggered if e.get(key))
        summary[f"{key}_count"] = hit_count
        summary[f"{key}_rate_on_triggered"] = (hit_count / len(triggered)) if triggered else 0.0

    return summary


def _simulate_breakout_4h_trade(entry: Mapping[str, Any], setup_id: str) -> Optional[Dict[str, Any]]:
    analysis = entry.get("analysis") if isinstance(entry.get("analysis"), Mapping) else {}
    trade_levels = analysis.get("trade_levels") if isinstance(analysis.get("trade_levels"), Mapping) else {}
    bt = analysis.get("backtest_4h") if isinstance(analysis.get("backtest_4h"), Mapping) else {}
    candles = bt.get("candles") if isinstance(bt.get("candles"), list) else []
    if not candles:
        return None

    breakout_level = _float_or_none(trade_levels.get("entry_trigger") or trade_levels.get("breakout_level_20"))
    if breakout_level is None:
        return None

    trigger_idx = None
    for idx, candle in enumerate(candles):
        close = _float_or_none(candle.get("close") if isinstance(candle, Mapping) else None)
        if close is not None and close > breakout_level:
            trigger_idx = idx
            break
    if trigger_idx is None:
        return {
            "symbol": entry.get("symbol"),
            "setup_id": setup_id,
            "triggered": False,
            "entry_idx": None,
            "exit_reason": None,
        }

    if setup_id == "breakout_immediate_1_5d":
        entry_idx = trigger_idx + 1
        if entry_idx >= len(candles):
            return None
        entry_price = _float_or_none(candles[entry_idx].get("open") if isinstance(candles[entry_idx], Mapping) else None)
    else:
        entry_price = breakout_level
        entry_idx = None
        for idx in range(trigger_idx + 1, len(candles)):
            candle = candles[idx]
            if not isinstance(candle, Mapping):
                continue
            close = _float_or_none(candle.get("close"))
            if close is not None and close < breakout_level:
                return {
                    "symbol": entry.get("symbol"),
                    "setup_id": setup_id,
                    "triggered": True,
                    "entry_idx": None,
                    "entry_price": None,
                    "retest_invalidated": True,
                    "exit_reason": None,
                }
            low = _float_or_none(candle.get("low"))
            high = _float_or_none(candle.get("high"))
            if low is not None and high is not None and low <= entry_price <= high:
                entry_idx = idx
                break
        if entry_idx is None:
            return None

    if entry_price is None:
        return None

    atr_abs = _float_or_none(bt.get("atr_abs_4h"))
    if atr_abs is None:
        atr_pct = _float_or_none(bt.get("atr_pct_4h_last_closed"))
        close_4h = _float_or_none(bt.get("close_4h_last_closed"))
        if atr_pct is not None and close_4h is not None:
            atr_abs = (atr_pct / 100.0) * close_4h
    if atr_abs is None:
        return None

    stop = entry_price - 1.2 * atr_abs
    r_val = entry_price - stop
    partial_target = entry_price + 1.5 * r_val

    partial_hit = False
    partial_idx = None
    exit_idx = None
    exit_reason = None
    exit_price = None

    for idx in range(entry_idx, len(candles)):
        candle = candles[idx]
        if not isinstance(candle, Mapping):
            continue
        low = _float_or_none(candle.get("low"))
        high = _float_or_none(candle.get("high"))

        # Intra-candle priority: STOP > PARTIAL > TRAIL
        if low is not None and low <= stop:
            exit_idx = idx
            exit_reason = "stop"
            exit_price = stop
            break

        if (not partial_hit) and high is not None and high >= partial_target:
            partial_hit = True
            partial_idx = idx

        if partial_hit:
            close = _float_or_none(candle.get("close"))
            ema20 = _float_or_none(candle.get("ema20"))
            if close is not None and ema20 is not None and close < ema20 and (idx + 1) < len(candles):
                nxt = candles[idx + 1]
                if isinstance(nxt, Mapping):
                    exit_idx = idx + 1
                    exit_reason = "trail"
                    exit_price = _float_or_none(nxt.get("open"))
                    break

        hold_candles = idx - entry_idx + 1
        if hold_candles >= FOUR_H_TIME_STOP_CANDLES and (idx + 1) < len(candles):
            nxt = candles[idx + 1]
            if isinstance(nxt, Mapping):
                exit_idx = idx + 1
                exit_reason = "time_stop"
                exit_price = _float_or_none(nxt.get("open"))
                break

    return {
        "symbol": entry.get("symbol"),
        "setup_id": setup_id,
        "triggered": True,
        "entry_idx": entry_idx,
        "entry_price": entry_price,
        "stop": stop,
        "partial_target": partial_target,
        "partial_hit": partial_hit,
        "partial_idx": partial_idx,
        "exit_idx": exit_idx,
        "exit_reason": exit_reason,
        "exit_price": exit_price,
    }


def run_backtest_from_snapshots(
    snapshots: Sequence[Mapping[str, Any]],
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Run deterministic E2-K backtest on in-memory snapshot payloads."""
    cfg = _extract_backtest_config(config)
    t_hold = cfg["t_hold"]
    t_trigger_max = cfg["t_trigger_max"]
    thresholds_pct = cfg["thresholds_pct"]

    sorted_snapshots = sorted(snapshots, key=lambda s: str(s.get("meta", {}).get("date", "")))
    all_dates = [str(s.get("meta", {}).get("date")) for s in sorted_snapshots]
    index_by_date = {d: i for i, d in enumerate(all_dates)}

    closes: Dict[str, List[Optional[float]]] = defaultdict(lambda: [None] * len(all_dates))
    highs: Dict[str, List[Optional[float]]] = defaultdict(lambda: [None] * len(all_dates))

    for i, snap in enumerate(sorted_snapshots):
        features = snap.get("data", {}).get("features", {})
        for symbol, feat in features.items():
            one_d = feat.get("1d", {}) if isinstance(feat, Mapping) else {}
            closes[symbol][i] = _float_or_none(one_d.get("close"))
            highs[symbol][i] = _float_or_none(one_d.get("high"))

    setup_map = {
        "breakout": "breakouts",
        "pullback": "pullbacks",
        "reversal": "reversals",
    }

    events_by_setup: Dict[str, List[Dict[str, Any]]] = {k: [] for k in setup_map}

    for snap in sorted_snapshots:
        t0_date = str(snap.get("meta", {}).get("date"))
        scoring = snap.get("scoring", {})

        for setup_type, score_key in setup_map.items():
            for entry in scoring.get(score_key, []):
                symbol = entry.get("symbol")
                if symbol not in closes or t0_date not in index_by_date:
                    continue

                setup_id = str(entry.get("setup_id") or "")
                if setup_type == "breakout" and setup_id in BREAKOUT_TREND_SETUP_IDS:
                    event_4h = _simulate_breakout_4h_trade(entry, setup_id)
                    if event_4h is not None:
                        event_4h["t0_date"] = t0_date
                        events_by_setup.setdefault(setup_id, []).append(event_4h)
                    continue

                trade_levels = (
                    entry.get("analysis", {}).get("trade_levels")
                    if isinstance(entry.get("analysis"), Mapping)
                    else None
                ) or {}

                event = _evaluate_candidate(
                    symbol=symbol,
                    setup_type=setup_type,
                    t0_date=t0_date,
                    index_by_date=index_by_date,
                    series_close=closes[symbol],
                    series_high=highs[symbol],
                    trade_levels=trade_levels,
                    t_trigger_max=t_trigger_max,
                    t_hold=t_hold,
                    thresholds_pct=thresholds_pct,
                )
                events_by_setup[setup_type].append(event)

    summary_by_setup = {
        setup_type: _summarize(events, thresholds_pct)
        for setup_type, events in events_by_setup.items()
    }

    return {
        "params": {
            "t_hold": t_hold,
            "t_trigger_max": t_trigger_max,
            "thresholds_pct": thresholds_pct,
        },
        "by_setup": summary_by_setup,
        "events": events_by_setup,
    }


def run_backtest_from_history(
    history_dir: str | Path,
    config: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Load all snapshot json files from ``history_dir`` and run backtest."""
    history_path = Path(history_dir)
    snapshots: List[Dict[str, Any]] = []

    for snapshot_file in sorted(history_path.glob("*.json")):
        with open(snapshot_file, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if isinstance(payload, dict) and payload.get("meta", {}).get("date"):
            snapshots.append(payload)

    return run_backtest_from_snapshots(snapshots, config=config)
