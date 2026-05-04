"""Liquidity stage utilities (Top-K orderbook budget + slippage metrics)."""

from __future__ import annotations

import logging

from typing import Any, Dict, List, Set, Tuple


logger = logging.getLogger(__name__)


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


def _read_tradeability_thresholds(config: Dict[str, Any]) -> Tuple[float, float, float]:
    if hasattr(config, "tradeability_class_thresholds"):
        cfg = config.tradeability_class_thresholds
    else:
        root = _root_config(config)
        cfg = root.get("tradeability", {}).get(
            "class_thresholds",
            {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        )

    if not isinstance(cfg, dict):
        raise ValueError("tradeability.class_thresholds must be an object")

    required = [
        "direct_ok_max_slippage_bps",
        "tranche_ok_max_slippage_bps",
        "marginal_max_slippage_bps",
    ]
    missing = [key for key in required if key not in cfg]
    if missing:
        raise ValueError(f"tradeability.class_thresholds missing keys: {missing}")

    direct_max = float(cfg[required[0]])
    tranche_max = float(cfg[required[1]])
    marginal_max = float(cfg[required[2]])
    if direct_max < 0 or tranche_max < 0 or marginal_max < 0:
        raise ValueError("tradeability.class_thresholds values must be >= 0")
    if not (direct_max <= tranche_max <= marginal_max):
        raise ValueError(
            "tradeability.class_thresholds must satisfy direct_ok_max_slippage_bps <= tranche_ok_max_slippage_bps <= marginal_max_slippage_bps"
        )
    return direct_max, tranche_max, marginal_max


def _tradeability_params(config: Dict[str, Any]) -> Dict[str, float]:
    direct_max, tranche_max, marginal_max = _read_tradeability_thresholds(config)
    root = _root_config(config)
    tradeability_cfg = root.get("tradeability", {})
    return {
        "notional_total_usdt": float(
            config.tradeability_notional_total_usdt if hasattr(config, "tradeability_notional_total_usdt") else tradeability_cfg.get("notional_total_usdt", 20_000)
        ),
        "notional_chunk_usdt": float(
            config.tradeability_notional_chunk_usdt if hasattr(config, "tradeability_notional_chunk_usdt") else tradeability_cfg.get("notional_chunk_usdt", 5_000)
        ),
        "max_tranches": int(config.tradeability_max_tranches if hasattr(config, "tradeability_max_tranches") else tradeability_cfg.get("max_tranches", 4)),
        "band_pct": float(config.tradeability_band_pct if hasattr(config, "tradeability_band_pct") else tradeability_cfg.get("band_pct", 1.0)),
        "max_spread_pct": float(config.tradeability_max_spread_pct if hasattr(config, "tradeability_max_spread_pct") else tradeability_cfg.get("max_spread_pct", 0.15)),
        "min_depth_1pct_usd": float(
            config.tradeability_min_depth_1pct_usd if hasattr(config, "tradeability_min_depth_1pct_usd") else tradeability_cfg.get("min_depth_1pct_usd", 200_000)
        ),
        "direct_ok_max_slippage_bps": direct_max,
        "tranche_ok_max_slippage_bps": tranche_max,
        "marginal_max_slippage_bps": marginal_max,
    }


def select_top_k_for_orderbook(candidates: List[Dict[str, Any]], top_k: int) -> List[Dict[str, Any]]:
    """Select top-k candidates by proxy_liquidity_score then quote_volume_24h."""
    ranked = sorted(
        candidates,
        key=lambda x: (float(x.get("proxy_liquidity_score", 0.0)), float(x.get("quote_volume_24h", 0.0))),
        reverse=True,
    )
    return ranked[: max(0, top_k)]


def fetch_orderbooks_for_top_k(
    mexc_client: Any,
    candidates: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> Tuple[Dict[str, Any], Set[str]]:
    """Fetch Top-K orderbooks and return (validated_payloads, selected_symbols)."""
    top_k = get_orderbook_top_k(config)
    selected = select_top_k_for_orderbook(candidates, top_k)

    payload: Dict[str, Any] = {}
    selected_symbols: Set[str] = set()

    for row in selected:
        symbol = row.get("symbol")
        if not symbol:
            continue
        selected_symbols.add(symbol)
        try:
            fetched = mexc_client.get_orderbook(symbol)
            if not isinstance(fetched, dict):
                logger.debug("Malformed orderbook payload ignored for %s: non-dict", symbol)
                continue
            bids = fetched.get("bids")
            asks = fetched.get("asks")
            if not isinstance(bids, list) or not bids or not isinstance(asks, list) or not asks:
                logger.debug("Malformed orderbook payload ignored for %s: missing/empty bids or asks", symbol)
                continue
            payload[symbol] = fetched
        except Exception as exc:
            logger.warning("Orderbook fetch failed for %s: %s", symbol, exc, exc_info=True)
    return payload, selected_symbols


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


def _compute_slippage_bps(orderbook: Dict[str, Any], notional_usdt: float) -> float | None:
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))
    if not bids or not asks:
        return None
    best_bid = bids[0][0]
    best_ask = asks[0][0]
    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return None
    vwap_ask, insufficient = _compute_buy_vwap(asks, notional_usdt)
    if insufficient or vwap_ask <= 0:
        return None
    return round(((vwap_ask - mid) / mid) * 10_000.0, 6)


def _is_orderbook_stale(orderbook: Dict[str, Any]) -> bool:
    return bool(orderbook.get("stale") or orderbook.get("is_stale"))


def _unknown_tradeability(reason: str) -> Dict[str, Any]:
    return {
        "spread_pct": None,
        "depth_bid_1pct_usd": None,
        "depth_ask_1pct_usd": None,
        "slippage_bps_5k": None,
        "slippage_bps_20k": None,
        "tradeable_5k": None,
        "tradeable_20k": None,
        "tradeable_via_tranches": None,
        "tradeability_class": "UNKNOWN",
        "execution_mode": "none",
        "tradeability_reason_keys": [reason],
    }


def compute_tradeability_metrics(orderbook: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
    params = _tradeability_params(config)
    if _is_orderbook_stale(orderbook):
        return _unknown_tradeability("orderbook_data_stale")

    band_metrics = compute_orderbook_metrics(orderbook, [float(params["band_pct"])])
    band_label = _band_label(float(params["band_pct"]))
    depth_bid = band_metrics.get(f"depth_bid_{band_label}pct_usd")
    depth_ask = band_metrics.get(f"depth_ask_{band_label}pct_usd")
    spread_pct = band_metrics.get("spread_pct")

    slippage_5k = _compute_slippage_bps(orderbook, float(params["notional_chunk_usdt"]))
    slippage_20k = _compute_slippage_bps(orderbook, float(params["notional_total_usdt"]))

    spread_ok = spread_pct is not None and float(spread_pct) <= float(params["max_spread_pct"])
    depth_ok = (
        depth_bid is not None
        and depth_ask is not None
        and float(depth_bid) >= float(params["min_depth_1pct_usd"])
        and float(depth_ask) >= float(params["min_depth_1pct_usd"])
    )

    tradeable_20k = (
        slippage_20k is not None and float(slippage_20k) <= float(params["direct_ok_max_slippage_bps"]) and spread_ok and depth_ok
    )
    tradeable_5k = (
        slippage_5k is not None and float(slippage_5k) <= float(params["tranche_ok_max_slippage_bps"]) and spread_ok and depth_ok
    )
    tradeable_via_tranches = tradeable_5k and (float(params["notional_chunk_usdt"]) * int(params["max_tranches"]) >= float(params["notional_total_usdt"]))

    reasons: Set[str] = set()
    if not spread_ok:
        reasons.add("spread_too_wide")
    if not depth_ok:
        reasons.add("depth_1pct_insufficient")
    if slippage_20k is None or float(slippage_20k) > float(params["direct_ok_max_slippage_bps"]):
        reasons.add("slippage_20k_too_high")
    if slippage_5k is None or float(slippage_5k) > float(params["tranche_ok_max_slippage_bps"]):
        reasons.add("slippage_5k_too_high")
    if not tradeable_via_tranches:
        reasons.add("tranche_execution_not_feasible")

    if tradeable_20k:
        tradeability_class = "DIRECT_OK"
        execution_mode = "direct"
        reasons = set()
    elif tradeable_via_tranches:
        tradeability_class = "TRANCHE_OK"
        execution_mode = "tranches"
        reasons = set()
    else:
        within_marginal = (slippage_20k is not None and float(slippage_20k) <= float(params["marginal_max_slippage_bps"])) or (
            slippage_5k is not None and float(slippage_5k) <= float(params["marginal_max_slippage_bps"])
        )
        spread_borderline = spread_pct is not None and float(spread_pct) <= (float(params["max_spread_pct"]) * 1.25)
        depth_borderline = (
            depth_bid is not None
            and depth_ask is not None
            and float(depth_bid) >= float(params["min_depth_1pct_usd"]) * 0.8
            and float(depth_ask) >= float(params["min_depth_1pct_usd"]) * 0.8
        )
        tradeability_class = "MARGINAL" if (within_marginal or spread_borderline or depth_borderline) else "FAIL"
        execution_mode = "none"

    return {
        "spread_pct": spread_pct,
        "depth_bid_1pct_usd": depth_bid,
        "depth_ask_1pct_usd": depth_ask,
        "slippage_bps_5k": slippage_5k,
        "slippage_bps_20k": slippage_20k,
        "tradeable_5k": tradeable_5k,
        "tradeable_20k": tradeable_20k,
        "tradeable_via_tranches": tradeable_via_tranches,
        "tradeability_class": tradeability_class,
        "execution_mode": execution_mode,
        "tradeability_reason_keys": sorted(reasons),
    }


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


def _band_label(band: float) -> str:
    bf = float(band)
    if bf.is_integer():
        return str(int(bf))
    return str(bf).replace(".", "_")


def _empty_orderbook_metrics(bands_pct: List[float]) -> Dict[str, Any]:
    out: Dict[str, Any] = {"spread_pct": None, "orderbook_ok": False}
    for band in bands_pct:
        label = _band_label(band)
        out[f"depth_bid_{label}pct_usd"] = None
        out[f"depth_ask_{label}pct_usd"] = None
    return out


def compute_orderbook_metrics(orderbook: Dict[str, Any], bands_pct: List[float]) -> Dict[str, Any]:
    """Compute deterministic spread/depth metrics for execution gating."""
    metrics = _empty_orderbook_metrics(bands_pct)
    bids = _to_levels(orderbook.get("bids"))
    asks = _to_levels(orderbook.get("asks"))
    if not bids or not asks:
        return metrics

    best_bid = max(p for p, _ in bids)
    best_ask = min(p for p, _ in asks)
    if best_bid <= 0 or best_ask <= 0:
        return metrics

    mid = (best_bid + best_ask) / 2.0
    if mid <= 0:
        return metrics

    metrics["spread_pct"] = ((best_ask - best_bid) / mid) * 100.0
    for band in bands_pct:
        band_f = float(band)
        label = _band_label(band_f)
        bid_cutoff = mid * (1.0 - band_f / 100.0)
        ask_cutoff = mid * (1.0 + band_f / 100.0)

        bid_depth = sum(price * qty for price, qty in bids if price >= bid_cutoff)
        ask_depth = sum(price * qty for price, qty in asks if price <= ask_cutoff)
        metrics[f"depth_bid_{label}pct_usd"] = bid_depth
        metrics[f"depth_ask_{label}pct_usd"] = ask_depth

    metrics["orderbook_ok"] = True
    return metrics


def apply_liquidity_metrics_to_shortlist(
    shortlist: List[Dict[str, Any]],
    orderbooks: Dict[str, Any],
    config: Dict[str, Any],
    selected_symbols: Set[str] | None = None,
) -> List[Dict[str, Any]]:
    """Attach liquidity fields for fetched symbols and leave non-fetched symbols untouched."""
    notional = get_slippage_notional_usdt(config)
    thresholds = get_grade_thresholds_bps(config)

    root = _root_config(config)
    gate_cfg = root.get("execution_gates", {}).get("mexc_orderbook", {})
    bands_cfg = gate_cfg.get("bands_pct", [0.5, 1.0])
    bands_pct = [float(v) for v in bands_cfg]

    out: List[Dict[str, Any]] = []
    for row in shortlist:
        symbol = row.get("symbol")
        r = dict(row)
        orderbook = orderbooks.get(symbol)
        if isinstance(orderbook, dict):
            metrics = compute_orderbook_liquidity_metrics(orderbook, notional, thresholds)
            r.update(metrics)
            r.update(compute_orderbook_metrics(orderbook, bands_pct))
            r.update(compute_tradeability_metrics(orderbook, config))
        elif selected_symbols is not None and symbol in selected_symbols:
            r.update(
                {
                    "spread_bps": None,
                    "slippage_bps": None,
                    "liquidity_grade": "D",
                    "liquidity_insufficient": True,
                }
            )
            r.update(_empty_orderbook_metrics(bands_pct))
            r.update(_unknown_tradeability("orderbook_data_missing"))
        else:
            r.update(
                {
                    "spread_bps": None,
                    "slippage_bps": None,
                    "liquidity_grade": None,
                    "liquidity_insufficient": None,
                }
            )
            metrics = _empty_orderbook_metrics(bands_pct)
            metrics["orderbook_ok"] = None
            r.update(metrics)
            r.update(_unknown_tradeability("orderbook_not_in_budget"))
        out.append(r)
    return out
