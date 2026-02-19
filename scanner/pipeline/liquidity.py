"""Liquidity stage utilities (Top-K orderbook budget)."""

from __future__ import annotations

from typing import Any, Dict, List


def _root_config(config: Dict[str, Any]) -> Dict[str, Any]:
    return config.raw if hasattr(config, "raw") else config


def get_orderbook_top_k(config: Dict[str, Any]) -> int:
    root = _root_config(config)
    return int(root.get("liquidity", {}).get("orderbook_top_k", 200))


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
