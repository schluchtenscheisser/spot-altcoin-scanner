"""Breakout scoring."""

import logging
from typing import Dict, Any, List, Optional

from scanner.pipeline.scoring.weights import load_component_weights

logger = logging.getLogger(__name__)


class BreakoutScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        scoring_cfg = root.get("scoring", {}).get("breakout", {})

        self.min_breakout_pct = float(scoring_cfg.get("min_breakout_pct", 2.0))
        self.ideal_breakout_pct = float(scoring_cfg.get("ideal_breakout_pct", 5.0))
        self.max_breakout_pct = float(scoring_cfg.get("max_breakout_pct", 20.0))
        breakout_curve = scoring_cfg.get("breakout_curve", {})
        self.breakout_floor_pct = float(breakout_curve.get("floor_pct", -5.0))
        self.breakout_fresh_cap_pct = float(breakout_curve.get("fresh_cap_pct", 1.0))
        self.breakout_overextended_cap_pct = float(breakout_curve.get("overextended_cap_pct", 3.0))

        self.min_volume_spike = float(scoring_cfg.get("min_volume_spike", 1.5))
        self.ideal_volume_spike = float(scoring_cfg.get("ideal_volume_spike", 2.5))

        momentum_cfg = scoring_cfg.get("momentum", {})
        self.momentum_divisor = float(momentum_cfg.get("r7_divisor", 10.0))

        penalties_cfg = scoring_cfg.get("penalties", {})
        self.overextension_factor = float(penalties_cfg.get("overextension_factor", 0.6))
        self.max_overextension_ema20_percent = float(
            penalties_cfg.get("max_overextension_ema20_percent", scoring_cfg.get("max_overextension_ema20_percent", 25.0))
        )
        self.low_liquidity_threshold = float(penalties_cfg.get("low_liquidity_threshold", 500_000))
        self.low_liquidity_factor = float(penalties_cfg.get("low_liquidity_factor", 0.8))

        default_weights = {"breakout": 0.35, "volume": 0.30, "trend": 0.20, "momentum": 0.15}
        self.weights = load_component_weights(
            scoring_cfg=scoring_cfg,
            section_name="breakout",
            default_weights=default_weights,
            aliases={
                "breakout": "price_break",
                "volume": "volume_confirmation",
                "trend": "volatility_context",
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

        breakout_score = self._score_breakout(f1d)
        volume_score = self._score_volume(f1d, f4h)
        trend_score = self._score_trend(f1d)
        momentum_score = self._score_momentum(f1d)

        raw_score = (
            breakout_score * self.weights["breakout"]
            + volume_score * self.weights["volume"]
            + trend_score * self.weights["trend"]
            + momentum_score * self.weights["momentum"]
        )

        penalties = []
        flags = []

        breakout_dist = f1d.get("breakout_dist_20", 0)
        if breakout_dist is not None and breakout_dist > self.breakout_overextended_cap_pct:
            flags.append("overextended_breakout_zone")

        dist_ema20 = f1d.get("dist_ema20_pct")
        if dist_ema20 is not None and dist_ema20 > self.max_overextension_ema20_percent:
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

        reasons = self._generate_reasons(breakout_score, volume_score, trend_score, momentum_score, f1d, f4h, flags)

        return {
            "score": round(final_score, 2),
            "raw_score": round(raw_score, 6),
            "penalty_multiplier": round(penalty_multiplier, 6),
            "final_score": round(final_score, 6),
            "components": {
                "breakout": round(breakout_score, 2),
                "volume": round(volume_score, 2),
                "trend": round(trend_score, 2),
                "momentum": round(momentum_score, 2),
            },
            "penalties": {name: factor for name, factor in penalties},
            "flags": flags,
            "reasons": reasons,
        }

    def _score_breakout(self, f1d: Dict[str, Any]) -> float:
        dist = f1d.get("breakout_dist_20")
        if dist is None:
            return 0.0
        if dist <= self.breakout_floor_pct:
            return 0.0
        if self.breakout_floor_pct < dist < 0:
            return 30.0 * (dist - self.breakout_floor_pct) / (0 - self.breakout_floor_pct)
        if 0 <= dist < self.min_breakout_pct:
            if self.min_breakout_pct <= 0:
                return 70.0
            return 30.0 + 40.0 * (dist / self.min_breakout_pct)
        if self.min_breakout_pct <= dist <= self.ideal_breakout_pct:
            denom = self.ideal_breakout_pct - self.min_breakout_pct
            if denom <= 0:
                return 100.0
            return 70.0 + 30.0 * ((dist - self.min_breakout_pct) / denom)
        if self.ideal_breakout_pct < dist <= self.max_breakout_pct:
            denom = self.max_breakout_pct - self.ideal_breakout_pct
            if denom <= 0:
                return 0.0
            return 100.0 * (1.0 - ((dist - self.ideal_breakout_pct) / denom))
        return 0.0

    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        max_spike = max(spike_1d, spike_4h)
        if max_spike < self.min_volume_spike:
            return 0.0
        if max_spike >= self.ideal_volume_spike:
            return 100.0
        ratio = (max_spike - self.min_volume_spike) / (self.ideal_volume_spike - self.min_volume_spike)
        return ratio * 100.0

    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        score = 0.0
        dist_ema20 = f1d.get("dist_ema20_pct")
        dist_ema50 = f1d.get("dist_ema50_pct")

        if dist_ema20 is not None and dist_ema20 > 0:
            score += 40
            if dist_ema20 > 5:
                score += 10
        if dist_ema50 is not None and dist_ema50 > 0:
            score += 40
            if dist_ema50 > 5:
                score += 10
        return min(score, 100.0)

    def _score_momentum(self, f1d: Dict[str, Any]) -> float:
        r7 = f1d.get("r_7")
        if r7 is None or self.momentum_divisor <= 0:
            return 0.0
        return max(0.0, min(100.0, (float(r7) / self.momentum_divisor) * 100.0))

    def _generate_reasons(self, breakout_score: float, volume_score: float, trend_score: float, momentum_score: float,
                          f1d: Dict[str, Any], f4h: Dict[str, Any], flags: List[str]) -> List[str]:
        reasons = []
        dist = f1d.get("breakout_dist_20", 0)
        if breakout_score > 70:
            reasons.append(f"Strong breakout ({dist:.1f}% above 20d high)")
        elif breakout_score > 30:
            reasons.append(f"Moderate breakout ({dist:.1f}% above high)")
        elif dist > 0:
            reasons.append(f"Early breakout ({dist:.1f}% above high)")
        else:
            reasons.append("No breakout (below recent high)")

        spike_1d = f1d.get("volume_quote_spike") if f1d.get("volume_quote_spike") is not None else f1d.get("volume_spike", 1.0)
        spike_4h = f4h.get("volume_quote_spike") if f4h.get("volume_quote_spike") is not None else f4h.get("volume_spike", 1.0)
        vol_spike = max(spike_1d, spike_4h)
        if volume_score > 70:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        else:
            reasons.append("Low volume (no confirmation)")

        if trend_score > 70:
            reasons.append("In uptrend (above EMAs)")
        elif trend_score > 30:
            reasons.append("Neutral trend")
        else:
            reasons.append("In downtrend (below EMAs)")

        if "overextended_breakout_zone" in flags:
            reasons.append(f"⚠️ Breakout in overextended zone ({dist:.1f}% above high)")
        if "overextended" in flags:
            reasons.append("⚠️ Overextended vs EMA20")
        if "low_liquidity" in flags:
            reasons.append("⚠️ Low liquidity")
        return reasons


def score_breakouts(features_data: Dict[str, Dict[str, Any]], volumes: Dict[str, float], config: Dict[str, Any]) -> List[Dict[str, Any]]:
    scorer = BreakoutScorer(config)
    results = []
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_breakout_1d", 30))
    min_4h = int(root.get("setup_validation", {}).get("min_history_breakout_4h", 50))
    for symbol, features in features_data.items():
        candles_1d = scorer._closed_candle_count(features, "1d")
        candles_4h = scorer._closed_candle_count(features, "4h")
        if (candles_1d is not None and candles_1d < min_1d) or (candles_4h is not None and candles_4h < min_4h):
            logger.debug(
                "Skipping breakout for %s due to insufficient history (1d=%s/%s, 4h=%s/%s)",
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
