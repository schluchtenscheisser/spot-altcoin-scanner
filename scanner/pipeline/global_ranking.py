"""Global ranking aggregation across setup-specific rankings."""

from __future__ import annotations

from typing import Any, Dict, List


def _config_get(root: Dict[str, Any], path: List[str], default: Any) -> Any:
    cur: Any = root
    for key in path:
        if not isinstance(cur, dict):
            return default
        cur = cur.get(key)
        if cur is None:
            return default
    return cur


def compute_global_top20(
    reversal_results: List[Dict[str, Any]],
    breakout_results: List[Dict[str, Any]],
    pullback_results: List[Dict[str, Any]],
    config: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Build unique global top-20 list from setup results using weighted setup score."""
    root = config.raw if hasattr(config, "raw") else config

    weights = {
        "breakout": float(_config_get(root, ["global_ranking", "setup_weights", "breakout"], 1.0)),
        "pullback": float(_config_get(root, ["global_ranking", "setup_weights", "pullback"], 0.9)),
        "reversal": float(_config_get(root, ["global_ranking", "setup_weights", "reversal"], 0.8)),
    }

    setup_map = {
        "breakout": breakout_results,
        "pullback": pullback_results,
        "reversal": reversal_results,
    }

    by_symbol: Dict[str, Dict[str, Any]] = {}

    for setup_type, entries in setup_map.items():
        weight = weights[setup_type]
        for entry in entries:
            symbol = entry.get("symbol")
            if not symbol:
                continue
            setup_score = float(entry.get("score", 0.0))
            weighted = setup_score * weight

            if symbol not in by_symbol:
                agg = dict(entry)
                agg["setup_score"] = setup_score
                agg["best_setup_type"] = setup_type
                agg["best_setup_score"] = setup_score
                agg["setup_weight"] = weight
                agg["global_score"] = round(weighted, 6)
                agg["confluence"] = 1
                agg["valid_setups"] = [setup_type]
                by_symbol[symbol] = agg
                continue

            prev = by_symbol[symbol]
            prev_setups = set(prev.get("valid_setups", []))
            prev_setups.add(setup_type)
            prev["valid_setups"] = sorted(prev_setups)
            prev["confluence"] = len(prev_setups)

            if weighted > float(prev.get("global_score", 0.0)):
                prev.update(entry)
                prev["setup_score"] = setup_score
                prev["best_setup_type"] = setup_type
                prev["best_setup_score"] = setup_score
                prev["setup_weight"] = weight
                prev["global_score"] = round(weighted, 6)
                prev["confluence"] = len(prev_setups)
                prev["valid_setups"] = sorted(prev_setups)

    ranked = sorted(
        by_symbol.values(),
        key=lambda x: (
            -float(x.get("global_score", 0.0)),
            float("inf") if x.get("slippage_bps") is None else float(x.get("slippage_bps")),
            -float(x.get("proxy_liquidity_score", 0.0) or 0.0),
            str(x.get("symbol", "")),
        ),
    )

    top20 = ranked[:20]
    for i, e in enumerate(top20, start=1):
        e["rank"] = i
    return top20
