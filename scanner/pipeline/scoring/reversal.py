"""
Reversal Setup Scoring
======================

Identifies downtrend → base → reclaim setups.
"""

import logging
import math
from typing import Dict, Any, List, Optional

from scanner.pipeline.scoring.weights import load_component_weights

logger = logging.getLogger(__name__)


class ReversalScorer:
    """Scores reversal setups (downtrend → base → reclaim)."""

    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("reversal", {})

        self.min_drawdown = float(scoring_cfg.get("min_drawdown_pct", 40.0))
        self.ideal_drawdown_min = float(scoring_cfg.get("ideal_drawdown_min", 50.0))
        self.ideal_drawdown_max = float(scoring_cfg.get("ideal_drawdown_max", 80.0))
        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.5))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.overextension_threshold = float(penalties_cfg.get("overextension_threshold_pct", 15.0))
        self.overextension_factor = float(penalties_cfg.get("overextension_factor", 0.7))
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {
            "drawdown": 0.30,
            "base": 0.25,
            "reclaim": 0.25,
            "volume": 0.20,
        }
        self.weights = load_component_weights(
            scoring_cfg=scoring_cfg,
            section_name="reversal",
            default_weights=default_weights,
            aliases={
                "base": "base_structure",
                "reclaim": "reclaim_signal",
                "volume": "volume_confirmation",
            },
)
    @staticmethod
    def _closed_candle_count(features: Dict[str, Any], timeframe: str) -> Optional[int]:
        meta = features.get("meta", {})
        idx_map = meta.get("last_closed_idx", {}) if isinstance(meta, dict) else {}
        idx = idx_map.get(timeframe)
        if isinstance(idx, int) and idx >= 0:
            return idx + 1
        return None

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float) -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})

        drawdown_score = self._score_drawdown(f1d)
        base_score = self._score_base(f1d)
        reclaim_score = self._score_reclaim(f1d)
        volume_score = self._score_volume(f1d, f4h)

        raw_score = (
            drawdown_score * self.weights["drawdown"]
            + base_score * self.weights["base"]
            + reclaim_score * self.weights["reclaim"]
            + volume_score * self.weights["volume"]
        )

        penalties = []
        flags = []

        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is not None and dist_ema50 > self.overextension_threshold:
            penalties.append(("overextension", self.overextension_factor))
            flags.append("overextended")

        if quote_volume_24h < self.low_liquidity_threshold:
            penalties.append(("low_liquidity", self.low_liquidity_factor))
            flags.append("low_liquidity")

        soft_penalties = features.get("soft_penalties", {}) if isinstance(features, dict) else {}
        if isinstance(soft_penalties, dict):
            for penalty_name, factor in soft_penalties.items():
                try:
                    penalties.append((str(penalty_name), float(factor)))
                except (TypeError, ValueError):
                    continue

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor

        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(drawdown_score, base_score, reclaim_score, volume_score, f1d, f4h, flags)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "drawdown": round(drawdown_score, 2),
                "base": round(base_score, 2),
                "reclaim": round(reclaim_score, 2),
                "volume": round(volume_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
        }

    def _score_drawdown(self, f1d: Dict[str, Any]) -> float:
        dd = f1d.get("drawdown_from_ath")
        if dd is None or dd >= 0:
            return 0.0

        dd_pct = abs(dd)
        if dd_pct < self.min_drawdown:
            return 0.0
        if self.ideal_drawdown_min <= dd_pct <= self.ideal_drawdown_max:
            return 100.0
        if dd_pct < self.ideal_drawdown_min:
            ratio = (dd_pct - self.min_drawdown) / (self.ideal_drawdown_min - self.min_drawdown)
            return 50.0 + ratio * 50.0

        excess = dd_pct - self.ideal_drawdown_max
        penalty = min(excess / 20, 0.5)
        return 100.0 * (1 - penalty)

    def _score_base(self, f1d: Dict[str, Any]) -> float:
        base_score = f1d.get("base_score")
        if base_score is None:
            return 0.0

        try:
            numeric = float(base_score)
        except (TypeError, ValueError):
            return 0.0

        if not math.isfinite(numeric):
            return 0.0

        return max(0.0, min(100.0, numeric))

    def _score_reclaim(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema20 = f1d.get("dist_ema20_pct")
        dist_ema50 = f1d.get("dist_ema50_pct")

        if dist_ema20 is not None and dist_ema20 > 0:
            score += 30
        if dist_ema50 is not None and dist_ema50 > 0:
            score += 30
        if f1d.get("hh_20"):
            score += 20

        r7 = f1d.get("r_7")
        if r7 is not None:
            momentum_score = max(0.0, min(100.0, (float(r7) / 10.0) * 100.0))
            score += 0.2 * momentum_score

        return min(score, 100.0)

    def _resolve_volume_spike(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        vol_spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        vol_spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        return max(vol_spike_1d, vol_spike_4h)

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        max_spike = self._resolve_volume_spike(f1d, f4h)

        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= 3.0:
            return 100.0
        ratio = (max_spike - self.min_volume_spike) / (3.0 - self.min_volume_spike)
        return ratio * 100.0

    def _generate_reasons(
        self,
        dd_score: float,
        base_score: float,
        reclaim_score: float,
        vol_score: float,
        f1d: Dict[str, Any],
        f4h: Dict[str, Any],
        flags: List[str],
    ) -> List[str]:
        reasons = []

        dd = f1d.get("drawdown_from_ath")
        if dd and dd < 0:
            dd_pct = abs(dd)
            if dd_score > 70:
                reasons.append(f"Strong drawdown setup ({dd_pct:.1f}% from ATH)")
            elif dd_score > 30:
                reasons.append(f"Moderate drawdown ({dd_pct:.1f}% from ATH)")

        if base_score > 60:
            reasons.append("Clean base formation detected")
        elif base_score == 0:
            reasons.append("No base detected (still declining)")

        dist_ema50 = f1d.get("dist_ema50_pct")
        if reclaim_score > 60:
            reasons.append(f"Reclaimed EMAs ({dist_ema50:.1f}% above EMA50)")
        elif reclaim_score > 30:
            reasons.append("Partial reclaim in progress")
        else:
            reasons.append("Below EMAs (no reclaim yet)")

        vol_spike = self._resolve_volume_spike(f1d, f4h)
        if vol_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif vol_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")

        if "overextended" in flags:
            reasons.append(f"⚠️ Overextended ({dist_ema50:.1f}% above EMA50)")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")

        return reasons


def score_reversals(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = ReversalScorer(config)
    results = []
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_reversal_1d", 120))
    min_4h = int(root.get("setup_validation", {}).get("min_history_reversal_4h", 80))

    for symbol, features in features_data.items():
        candles_1d = scorer._closed_candle_count(features, "1d")
        candles_4h = scorer._closed_candle_count(features, "4h")
        if (candles_1d is not None and candles_1d < min_1d) or (candles_4h is not None and candles_4h < min_4h):
            logger.debug(
                "Skipping reversal for %s due to insufficient history (1d=%s/%s, 4h=%s/%s)",
                symbol,
                candles_1d,
                min_1d,
                candles_4h,
                min_4h,
            )
            continue
        volume = volumes.get(symbol, 0)
        try:
            score_result = scorer.score(symbol, features, volume)
            results.append(
                {
                    "symbol": symbol,
                    "price_usdt": features.get("price_usdt"),
                    "coin_name": features.get("coin_name"),
                    "market_cap": features.get("market_cap"),
                    "quote_volume_24h": features.get("quote_volume_24h"),
                    "proxy_liquidity_score": features.get("proxy_liquidity_score"),
                    "spread_bps": features.get("spread_bps"),
                    "slippage_bps": features.get("slippage_bps"),
                    "liquidity_grade": features.get("liquidity_grade"),
                    "liquidity_insufficient": features.get("liquidity_insufficient"),
                    "score": score_result["score"],
                    "raw_score": score_result["raw_score"],
                    "penalty_multiplier": score_result["penalty_multiplier"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "risk_flags": features.get("risk_flags", []),
                    "reasons": score_result["reasons"],
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
