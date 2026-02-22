"""Breakout Trend 1-5D scoring (immediate + retest)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class BreakoutTrend1to5DScorer:
    def __init__(self, config: Dict[str, Any]):
        root = config.raw if hasattr(config, "raw") else config
        cfg = root.get("scoring", {}).get("breakout_trend_1_5d", {})

        self.min_24h_risk_off = float(cfg.get("risk_off_min_quote_volume_24h", 15_000_000))

    @staticmethod
    def _calc_high_20d_excluding_current(f1d: Dict[str, Any]) -> Optional[float]:
        highs = f1d.get("high_series") or []
        if len(highs) < 21:
            return None
        window = highs[-21:-1]
        return float(max(window)) if window else None

    @staticmethod
    def _find_first_breakout_idx(f4h: Dict[str, Any], high_20d_1d: float) -> Optional[int]:
        closes = f4h.get("close_series") or []
        if not closes:
            return None
        start = max(0, len(closes) - 6)
        for idx in range(start, len(closes)):
            if float(closes[idx]) > high_20d_1d:
                return idx
        return None

    @staticmethod
    def _anti_chase_multiplier(r7: float) -> float:
        if r7 < 30:
            return 1.0
        if r7 <= 60:
            return 1.0 - ((r7 - 30.0) / 30.0) * 0.25
        return 0.75

    @staticmethod
    def _overextension_multiplier(dist_ema20_pct_1d: float) -> float:
        d = dist_ema20_pct_1d
        if d < 12:
            return 1.0
        if d <= 20:
            return 1.0 - ((d - 12.0) / 8.0) * 0.15
        if d < 28:
            return 0.85 - ((d - 20.0) / 8.0) * 0.15
        return 0.0

    @staticmethod
    def _breakout_distance_score(dist: float) -> float:
        floor, min_breakout, ideal, max_breakout = -5.0, 2.0, 5.0, 20.0
        if dist <= floor:
            return 0.0
        if floor < dist < 0:
            return 30.0 * (dist - floor) / (0.0 - floor)
        if 0 <= dist < min_breakout:
            return 30.0 + 40.0 * (dist / min_breakout)
        if min_breakout <= dist <= ideal:
            return 70.0 + 30.0 * (dist - min_breakout) / (ideal - min_breakout)
        if ideal < dist <= max_breakout:
            return 100.0 * (1.0 - (dist - ideal) / (max_breakout - ideal))
        return 0.0

    @staticmethod
    def _volume_score(spike_combined: float) -> float:
        if spike_combined < 1.5:
            return 0.0
        if spike_combined >= 2.5:
            return 100.0
        return (spike_combined - 1.5) * 100.0

    @staticmethod
    def _trend_score(f4h: Dict[str, Any]) -> float:
        score = 70.0
        close = float(f4h.get("close") or 0.0)
        ema20 = float(f4h.get("ema_20") or 0.0)
        ema50 = float(f4h.get("ema_50") or 0.0)
        if close > ema20:
            score += 15.0
        if ema20 > ema50:
            score += 15.0
        return min(score, 100.0)

    @staticmethod
    def _bb_score(rank: float) -> float:
        if rank <= 0.2:
            return 100.0
        if rank <= 0.6:
            return 100.0 - (rank - 0.2) * (60.0 / 0.4)
        return 0.0

    def _btc_multiplier(
        self,
        feature_row: Dict[str, Any],
        btc_regime: Optional[Dict[str, Any]],
    ) -> Optional[float]:
        if not btc_regime or btc_regime.get("state") == "RISK_ON":
            return 1.0

        if float(feature_row.get("quote_volume_24h") or 0.0) < self.min_24h_risk_off:
            return None

        f1d = feature_row.get("1d", {})
        alt_r7 = float(f1d.get("r_7") or 0.0)
        alt_r3 = float(f1d.get("r_3") or 0.0)
        btc_r7 = float((btc_regime.get("btc_returns") or {}).get("r_7") or 0.0)
        btc_r3 = float((btc_regime.get("btc_returns") or {}).get("r_3") or 0.0)

        override = (alt_r7 - btc_r7) >= 7.5 or (alt_r3 - btc_r3) >= 3.5
        return 0.85 if override else None

    def score_symbol(
        self,
        symbol: str,
        feature_row: Dict[str, Any],
        quote_volume_24h: float,
        btc_regime: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        f1d = feature_row.get("1d", {})
        f4h = feature_row.get("4h", {})

        high_20 = self._calc_high_20d_excluding_current(f1d)
        if high_20 is None:
            return []

        first_breakout_idx = self._find_first_breakout_idx(f4h, high_20)
        if first_breakout_idx is None:
            return []

        if not (float(f1d.get("close") or 0.0) > float(f1d.get("ema_50") or 0.0) and float(f1d.get("ema_20") or 0.0) > float(f1d.get("ema_50") or 0.0)):
            return []
        if float(f1d.get("atr_pct_rank_120") or 0.0) < 0.5:
            return []
        if float(f1d.get("r_7") or 0.0) <= 0.0:
            return []

        dist_ema20 = float(f1d.get("dist_ema20_pct") or 0.0)
        if dist_ema20 >= 28.0:
            return []

        close_4h_last = float(f4h.get("close") or 0.0)
        dist_pct = ((close_4h_last / high_20) - 1.0) * 100.0

        spike_1d = float(f1d.get("volume_quote_spike") or 0.0)
        spike_4h = float(f4h.get("volume_quote_spike") or 0.0)
        spike_combined = 0.7 * spike_1d + 0.3 * spike_4h

        breakout_distance_score = self._breakout_distance_score(dist_pct)
        volume_score = self._volume_score(spike_combined)
        trend_score = self._trend_score(f4h)
        bb_rank = float(f4h.get("bb_width_rank_120") or 0.0)
        bb_score = self._bb_score(bb_rank)

        base_score = (
            0.35 * breakout_distance_score
            + 0.35 * volume_score
            + 0.15 * trend_score
            + 0.15 * bb_score
        )

        anti = self._anti_chase_multiplier(float(f1d.get("r_7") or 0.0))
        over = self._overextension_multiplier(dist_ema20)
        btc_mult = self._btc_multiplier({**feature_row, "quote_volume_24h": quote_volume_24h}, btc_regime)
        if btc_mult is None:
            return []

        final_score = max(0.0, min(100.0, base_score * anti * over * btc_mult))

        base = {
            "symbol": symbol,
            "score": round(final_score, 6),
            "base_score": round(base_score, 6),
            "final_score": round(final_score, 6),
            "high_20d_1d": round(high_20, 8),
            "dist_pct": round(dist_pct, 6),
            "volume_quote_spike_1d": spike_1d,
            "volume_quote_spike_4h": spike_4h,
            "spike_combined": round(spike_combined, 6),
            "atr_pct_rank_120_1d": f1d.get("atr_pct_rank_120"),
            "bb_width_pct_4h": f4h.get("bb_width_pct"),
            "bb_width_rank_120_4h": bb_rank,
            "overextension_multiplier": round(over, 6),
            "anti_chase_multiplier": round(anti, 6),
            "btc_multiplier": round(btc_mult, 6),
            "breakout_distance_score": round(breakout_distance_score, 6),
            "volume_score": round(volume_score, 6),
            "trend_score": round(trend_score, 6),
            "bb_score": round(bb_score, 6),
            "triggered": True,
            "quote_volume_24h": quote_volume_24h,
            "coin_name": feature_row.get("coin_name"),
            "market_cap": feature_row.get("market_cap"),
            "price_usdt": feature_row.get("price_usdt"),
            "proxy_liquidity_score": feature_row.get("proxy_liquidity_score"),
            "spread_bps": feature_row.get("spread_bps"),
            "slippage_bps": feature_row.get("slippage_bps"),
            "liquidity_grade": feature_row.get("liquidity_grade"),
            "liquidity_insufficient": feature_row.get("liquidity_insufficient"),
            "risk_flags": feature_row.get("risk_flags", []),
        }

        results: List[Dict[str, Any]] = [{**base, "setup_id": "breakout_immediate_1_5d", "retest_valid": False, "retest_invalidated": False}]

        lows = f4h.get("low_series") or []
        closes = f4h.get("close_series") or []
        zone_low = high_20 * 0.99
        zone_high = high_20 * 1.01
        retest_valid = False
        retest_invalidated = False
        end_idx = min(len(closes) - 1, first_breakout_idx + 12)
        for j in range(first_breakout_idx + 1, end_idx + 1):
            c = float(closes[j])
            if c < high_20:
                retest_invalidated = True
                break
            low = float(lows[j]) if j < len(lows) else c
            touch = zone_low <= low <= zone_high
            reclaim = c >= high_20
            if touch and reclaim:
                retest_valid = True
                break

        if retest_valid and not retest_invalidated:
            results.append({**base, "setup_id": "breakout_retest_1_5d", "retest_valid": True, "retest_invalidated": False})

        return results


def score_breakout_trend_1_5d(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any],
    btc_regime: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    scorer = BreakoutTrend1to5DScorer(config)
    root = config.raw if hasattr(config, "raw") else config
    min_1d = int(root.get("setup_validation", {}).get("min_history_breakout_1d", 30))
    min_4h = int(root.get("setup_validation", {}).get("min_history_breakout_4h", 50))

    results: List[Dict[str, Any]] = []
    for symbol, feature_row in features_data.items():
        idxs = ((feature_row.get("meta") or {}).get("last_closed_idx") or {})
        candles_1d = int(idxs.get("1d", -1)) + 1 if idxs.get("1d") is not None else None
        candles_4h = int(idxs.get("4h", -1)) + 1 if idxs.get("4h") is not None else None
        if (candles_1d is not None and candles_1d < min_1d) or (candles_4h is not None and candles_4h < min_4h):
            continue
        rows = scorer.score_symbol(symbol, feature_row, float(volumes.get(symbol, 0.0)), btc_regime)
        results.extend(rows)

    results.sort(key=lambda x: (float(x.get("final_score", 0.0)), x.get("setup_id") == "breakout_retest_1_5d"), reverse=True)
    return results
