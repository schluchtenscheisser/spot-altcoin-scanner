"""Liquidity stage utilities (Top-K orderbook budget + slippage metrics)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _root_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return config.raw if hasattr(config, "raw") else config


def get_orderbook_top_k(config: Dict[str, Any]) -> int:
    root = _root_config(config)
    return int(root.get("liquidity", {}).get("orderbook_top_k", 200))


def get_slippage_notional_usdt(config: Dict[str, Any]) -> float:
    root = _root_config(config)
    return float(root.get("liquidity", {}).get("slippage_notional_usdt", 20_000.0))


def get_grade_thresholds_bps(config: Dict[str, Any]) -> Tuple[float, float, float]:
    root = _root_config(config)
    cfg = root.get("liquidity", {}).get("grade_thresholds_bps", {})
    a_max = float(cfg.get("a_max", 20.0))
    b_max = float(cfg.get("b_max", 50.0))
    c_max = float(cfg.get("c_max", 100.0))
    return a_max, b_max, c_max


def select_top_k_for_orderbook(candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """Select top-k candidates by proxy_liquidity_score then quote_volume_24h."""
    ranked = sorted(
        candidates,
        key=lambda x: (float(x.get("proxy_liquidity_score", 0.0)), float(x.get("quote_volume_24h", 0.0))),
        reverse=True,
    )
    return ranked[: max(0, top_k)]


def fetch_orderbooks_for_top_k(mexc_client: Any, candidates: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch orderbook only for Top-K symbols and return mapping symbol->orderbook payload."""
    top_k = get_orderbook_top_k(config)
    selected = select_top_k_for_orderbook(candidates, top_k)

    payload: Dict[str, Any] = {}
    for row in selected:
        symbol = row.get("symbol")
        if not symbol:
            continue
        payload[symbol] = mexc_client.get_orderbook(symbol)
    return payload


def _to_levels(levels: Any) -> List[Tuple[float, float]]:
    out: List[Tuple[float, float]] = []
    if not isinstance(levels, list):
        return out
    for row in levels:
        if not isinstance(row, (list, tuple)) or len(row) < 2:
            continue
        try:
            p = float(row[0])
            q = float(row[1])
        except (TypeError, ValueError):
            continue
        if p > 0 and q > 0:
            out.append((p, q))
    return out


def _compute_buy_vwap(asks: List[Tuple[float, float]], notional_usdt: float) -> Tuple[float, bool]:
    remaining = float(notional_usdt)
    if remaining <= 0:
        return 0.0, False

    spent = 0.0
    qty = 0.0
    for price, size in asks:
        level_quote = price * size
        take_quote = min(level_quote, remaining)
        take_qty = take_quote / price
        spent += take_quote
        qty += take_qty
        remaining -= take_quote
        if remaining <= 1e-9:
            break

    if qty <= 0:
        return 0.0, True
    return spent / qty, remaining > 1e-9


def compute_orderbook_liquidity_metrics(orderbook: Dict[str, Any], notional_usdt: float, thresholds_bps: Tuple[float, float, float]) -> Dict[str, Any]:
    """Compute spread/slippage/grade from an orderbook snapshot."""
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))

    if not bids or not asks:
        return {
            "spread_bps": None,
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return {
            "spread_bps": None,
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    spread_bps = ((best_ask - best_bid) / mid) * 10_000.0
    vwap_ask, insufficient = _compute_buy_vwap(asks, float(notional_usdt))

    if insufficient or vwap_ask <= 0:
        return {
            "spread_bps": round(spread_bps, 6),
            "slippage_bps": None,
            "liquidity_grade": "D",
            "liquidity_insufficient": True,
        }

    slippage_bps = ((vwap_ask - mid) / mid) * 10_000.0

    a_max, b_max, c_max = thresholds_bps
    if slippage_bps <= a_max:
        grade = "A"
    elif slippage_bps <= b_max:
        grade = "B"
    elif slippage_bps <= c_max:
        grade = "C"
    else:
        grade = "D"

    return {
        "spread_bps": round(spread_bps, 6),
        "slippage_bps": round(slippage_bps, 6),
        "liquidity_grade": grade,
        "liquidity_insufficient": False,
    }


def apply_liquidity_metrics_to_shortlist(shortlist: List[Dict[str, Any]], orderbooks: Dict[str, Any], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Attach liquidity fields to shortlist rows when orderbook data is available."""
    notional = get_slippage_notional_usdt(config)
    thresholds = get_grade_thresholds_bps(config)

    out: List[Dict[str, Any]] = []
    for row in shortlist:
        symbol = row.get("symbol")
        r = dict(row)
        if symbol in orderbooks:
            metrics = compute_orderbook_liquidity_metrics(orderbooks[symbol], notional, thresholds)
            r.update(metrics)
        else:
            r.update(
                {
                    "spread_bps": None,
                    "slippage_bps": None,
                    "liquidity_grade": None,
                    "liquidity_insufficient": None,
                }
            )
        out.append(r)
    return out
