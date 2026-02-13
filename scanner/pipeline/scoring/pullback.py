"""Pullback scoring."""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class PullbackScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("pullback", {})

        self.min_trend_strength = float(scoring_cfg.get("min_trend_strength", 5.0))
        self.min_rebound = float(scoring_cfg.get("min_rebound", 3.0))
        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.3))

        momentum_cfg = scoring_cfg.get("momentum", {})
        self.momentum_divisor = float(momentum_cfg.get("r7_divisor", 10.0))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.broken_trend_factor = float(penalties_cfg.get("broken_trend_factor", 0.5))
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {"trend": 0.30, "pullback": 0.25, "rebound": 0.25, "volume": 0.20}
        self.weights = self._load_weights(scoring_cfg, default_weights)

    def _load_weights(self, scoring_cfg: Dict[str, Any], default_weights: Dict[str, float]) -> Dict[str, float]:
        cfg_weights = scoring_cfg.get("weights")
        if not cfg_weights:
            logger.warning("Using legacy default weights; please define config.scoring.pullback.weights")
            return default_weights

        mapped = {
            "trend": cfg_weights.get("trend", cfg_weights.get("trend_quality")),
            "pullback": cfg_weights.get("pullback", cfg_weights.get("pullback_quality")),
            "rebound": cfg_weights.get("rebound", cfg_weights.get("rebound_signal")),
            "volume": cfg_weights.get("volume"),
        }
        merged = {k: float(mapped[k]) if mapped.get(k) is not None else v for k, v in default_weights.items()}
        total = sum(merged.values())
        if total <= 0:
            logger.warning("Using legacy default weights; please define config.scoring.pullback.weights")
            return default_weights
        return {k: v / total for k, v in merged.items()}

    def score(self, symbol: str, features: Dict[str, Any], quote_volume_24h: float) -> Dict[str, Any]:
        f1d = features.get("1d", {})
        f4h = features.get("4h", {})

        trend_score = self._score_trend(f1d)
        pullback_score = self._score_pullback(f1d)
        rebound_score = self._score_rebound(f1d, f4h)
        volume_score = self._score_volume(f1d, f4h)

        raw_score = (
            trend_score * self.weights["trend"]
            + pullback_score * self.weights["pullback"]
            + rebound_score * self.weights["rebound"]
            + volume_score * self.weights["volume"]
        )

        penalties = []
        flags = []

        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is not None and dist_ema50 < 0:
            penalties.append(("broken_trend", self.broken_trend_factor))
            flags.append("broken_trend")

        if quote_volume_24h < self.low_liquidity_threshold:
            penalties.append(("low_liquidity", self.low_liquidity_factor))
            flags.append("low_liquidity")

        penalty_multiplier = 1.0
        for _, factor in penalties:
            penalty_multiplier *= factor
        final_score = max(0.0, min(100.0, raw_score * penalty_multiplier))

        reasons = self._generate_reasons(trend_score, pullback_score, rebound_score, volume_score, f1d, f4h, flags)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "trend": round(trend_score, 2),
                "pullback": round(pullback_score, 2),
                "rebound": round(rebound_score, 2),
                "volume": round(volume_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
        }

    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema50 = f1d.get("dist_ema50_pct")
        if dist_ema50 is None or dist_ema50 < 0:
            return 0.0

        if dist_ema50 >= 15:
            score += 60
        elif dist_ema50 >= 10:
            score += 50
        elif dist_ema50 >= self.min_trend_strength:
            score += 40
        else:
            score += 20

        if f1d.get("hh_20"):
            score += 40
        return min(score, 100.0)

    def _score_pullback(self, f1d: Dict[str, Any]) -> float:
        dist_ema20 = f1d.get("dist_ema20_pct", 100)
        dist_ema50 = f1d.get("dist_ema50_pct", 100)

        if -2 <= dist_ema20 <= 2:
            return 100.0
        if -2 <= dist_ema50 <= 2:
            return 80.0
        if dist_ema20 < 0 and dist_ema50 > 0:
            return 60.0
        if dist_ema20 > 5:
            return 20.0
        if dist_ema50 < -5:
            return 10.0
        return 40.0

    def _score_rebound(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        score = 0.0
        r3 = f1d.get("r_3", 0)
        if r3 >= 10:
            score += 50
        elif r3 >= self.min_rebound:
            score += 30
        elif r3 > 0:
            score += 10

        r3_4h = f4h.get("r_3", 0)
        if r3_4h >= 5:
            score += 50
        elif r3_4h >= 2:
            score += 30
        elif r3_4h > 0:
            score += 10

        r7 = f1d.get("r_7")
        if r7 is not None and self.momentum_divisor > 0:
            score = 0.8 * score + 0.2 * max(0.0, min(100.0, (float(r7) / self.momentum_divisor) * 100.0))

        return min(score, 100.0)

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        max_spike = max(f1d.get("volume_spike", 1.0), f4h.get("volume_spike", 1.0))
        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= 2.5:
            return 100.0
        if max_spike >= 2.0:
            return 80.0
        ratio = (max_spike - self.min_volume_spike) / (2.0 - self.min_volume_spike)
        return ratio * 70.0

    def _generate_reasons(self, trend_score: float, pullback_score: float, rebound_score: float, volume_score: float,
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str]) -> List[str]:
        reasons = []

        dist_ema50 = f1d.get("dist_ema50_pct", 0)
        if trend_score > 70:
            reasons.append(f"Strong uptrend ({dist_ema50:.1f}% above EMA50)")
        elif trend_score > 30:
            reasons.append(f"Moderate uptrend ({dist_ema50:.1f}% above EMA50)")
        else:
            reasons.append("Weak/no uptrend")

        dist_ema20 = f1d.get("dist_ema20_pct", 0)
        if pullback_score > 70:
            reasons.append(f"At support level ({dist_ema20:.1f}% from EMA20)")
        elif pullback_score > 40:
            reasons.append("Healthy pullback depth")
        else:
            reasons.append("No clear pullback")

        r3 = f1d.get("r_3", 0)
        if rebound_score > 60:
            reasons.append(f"Strong rebound ({r3:.1f}% in 3d)")
        elif rebound_score > 30:
            reasons.append("Moderate rebound")
        else:
            reasons.append("No rebound yet")

        vol_spike = max(f1d.get("volume_spike", 1.0), f4h.get("volume_spike", 1.0))
        if volume_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")

        if "broken_trend" in flags:
            reasons.append("⚠️ Below EMA50 (trend broken)")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")

        return reasons


def score_pullbacks(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = PullbackScorer(config)
    results = []
    for symbol, features in features_data.items():
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
                    "score": score_result["score"],
                    "components": score_result["components"],
                    "penalties": score_result["penalties"],
                    "flags": score_result["flags"],
                    "reasons": score_result["reasons"],
                }
            )
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue

    results.sort(key=lambda x: x["score"], reverse=True)
    return results
