from __future__ import annotations

"""Deterministic backtest runner (Analytics-only, E2-K).

Canonical v2 rules (Feature-Spec section 10):
- Trigger search on 1D close within ``[t0 .. t0 + T_trigger_max]``
- ``entry_price = close[trigger_day]``
- ``hit_10`` / ``hit_20`` use ``max(high[trigger_day+1 .. trigger_day+T_hold])``
- No exit logic.
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
import json


DEFAULT_BACKTEST_CFG: Dict[str, Any] = {
    "t_hold": 10,
    "t_trigger_max": 5,
    "thresholds_pct": [10.0, 20.0],
}


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
    t0_idx = index_by_date[t0_date]

    trigger_idx: Optional[int] = None
    for idx in range(t0_idx, min(len(series_close), t0_idx + t_trigger_max + 1)):
        close = series_close[idx]
        if close is None:
            continue
        if _setup_triggered(setup_type, close, trade_levels):
            trigger_idx = idx
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

    start = trigger_idx + 1
    end_excl = min(len(series_high), trigger_idx + t_hold + 1)
    window_highs = [h for h in series_high[start:end_excl] if h is not None]
    max_high = max(window_highs) if window_highs else None

    outcome.update(
        {
            "trigger_day_offset": trigger_idx - t0_idx,
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
