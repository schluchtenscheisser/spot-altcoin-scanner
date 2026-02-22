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

    setup_map = {
        "breakout": breakout_results,
        "pullback": pullback_results,
        "reversal": reversal_results,
    }

    by_symbol: Dict[str, Dict[str, Any]] = {}

    for setup_type, entries in setup_map.items():
        for entry in entries:
            symbol = entry.get("symbol")
            if not symbol:
                continue
            setup_score = float(entry.get("final_score", entry.get("score", 0.0)))
            weighted = setup_score

            if symbol not in by_symbol:
                agg = dict(entry)
                agg["setup_score"] = setup_score
                agg["best_setup_type"] = setup_type
                agg["best_setup_score"] = setup_score
                agg["setup_weight"] = 1.0
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

            prev_weighted = float(prev.get("global_score", 0.0))
            prev_setup_id = str(prev.get("setup_id", ""))
            cur_setup_id = str(entry.get("setup_id", ""))
            prefer_retest = weighted == prev_weighted and cur_setup_id.endswith("retest_1_5d") and not prev_setup_id.endswith("retest_1_5d")

            if weighted > prev_weighted or prefer_retest:
                prev.update(entry)
                prev["setup_score"] = setup_score
                prev["best_setup_type"] = setup_type
                prev["best_setup_score"] = setup_score
                prev["setup_weight"] = 1.0
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
