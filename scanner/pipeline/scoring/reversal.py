"""
Reversal Setup Scoring
======================

Identifies downtrend → base → reclaim setups.

Scoring Components:
1. Drawdown Context (30%) - Deep enough pullback from ATH
2. Base Quality (25%) - Consolidation without new lows
3. Reclaim Strength (25%) - Breaking back above EMAs with momentum
4. Volume Confirmation (20%) - Volume expansion on reclaim

Penalties:
- Overextension (too far above EMAs)
- Low liquidity
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ReversalScorer:
    """Scores reversal setups (downtrend → base → reclaim)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize reversal scorer.
        
        Args:
            config: Config dict with 'scoring' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            scoring_config = config.raw.get('scoring', {}).get('reversal', {})
        else:
            scoring_config = config.get('scoring', {}).get('reversal', {})
        
        # Thresholds
        self.min_drawdown = scoring_config.get('min_drawdown_pct', 40)  # Min 40% drawdown
        self.ideal_drawdown_min = scoring_config.get('ideal_drawdown_min', 50)  # 50-80% ideal
        self.ideal_drawdown_max = scoring_config.get('ideal_drawdown_max', 80)
        
        self.min_base_days = scoring_config.get('min_base_days', 10)  # Min consolidation
        self.min_volume_spike = scoring_config.get('min_volume_spike', 1.5)  # 1.5x normal
        
        self.overextension_threshold = scoring_config.get('overextension_threshold', 15)  # >15% above EMA50
        
        # Component weights
        self.weights = {
            'drawdown': 0.30,
            'base': 0.25,
            'reclaim': 0.25,
            'volume': 0.20
        }
        
        logger.info("Reversal Scorer initialized")
    
    def score(
        self,
        symbol: str,
        features: Dict[str, Any],
        quote_volume_24h: float
    ) -> Dict[str, Any]:
        """
        Score a single symbol for reversal setup.
        
        Args:
            symbol: Trading pair (e.g., 'BTCUSDT')
            features: Feature dict with '1d' and '4h' sub-dicts
            quote_volume_24h: 24h volume in USDT
        
        Returns:
            Score dict with:
            - score: float (0-100)
            - components: dict of component scores
            - flags: list of condition flags
            - reasons: list of human-readable reasons
        """
        f1d = features.get('1d', {})
        f4h = features.get('4h', {})
        
        # Components
        drawdown_score = self._score_drawdown(f1d)
        base_score = self._score_base(f1d)
        reclaim_score = self._score_reclaim(f1d, f4h)
        volume_score = self._score_volume(f1d, f4h)
        
        # Weighted total
        raw_score = (
            drawdown_score * self.weights['drawdown'] +
            base_score * self.weights['base'] +
            reclaim_score * self.weights['reclaim'] +
            volume_score * self.weights['volume']
        )
        
        # Penalties & Flags
        penalties = []
        flags = []
        
        # Overextension penalty
        dist_ema50 = f1d.get('dist_ema50_pct')
        if dist_ema50 and dist_ema50 > self.overextension_threshold:
            penalties.append(('overextension', 0.7))
            flags.append('overextended')
        
        # Low liquidity penalty
        if quote_volume_24h < 500_000:  # <500K USDT
            penalties.append(('low_liquidity', 0.8))
            flags.append('low_liquidity')
        
        # Apply penalties (multiplicative)
        final_score = raw_score
        for name, factor in penalties:
            final_score *= factor
        
        # Reasons
        reasons = self._generate_reasons(
            drawdown_score, base_score, reclaim_score, volume_score,
            f1d, f4h, flags
        )
        
        return {
            'score': round(final_score, 2),
            'components': {
                'drawdown': round(drawdown_score, 2),
                'base': round(base_score, 2),
                'reclaim': round(reclaim_score, 2),
                'volume': round(volume_score, 2)
            },
            'penalties': {name: factor for name, factor in penalties},
            'flags': flags,
            'reasons': reasons
        }
    
    def _score_drawdown(self, f1d: Dict[str, Any]) -> float:
        """
        Score drawdown context (0-100).
        
        Ideal: 50-80% drawdown from ATH
        """
        dd = f1d.get('drawdown_from_ath')
        if dd is None or dd >= 0:
            return 0.0
        
        dd_pct = abs(dd)
        
        # Below minimum
        if dd_pct < self.min_drawdown:
            return 0.0
        
        # Ideal range
        if self.ideal_drawdown_min <= dd_pct <= self.ideal_drawdown_max:
            return 100.0
        
        # Below ideal (linear scale)
        if dd_pct < self.ideal_drawdown_min:
            ratio = (dd_pct - self.min_drawdown) / (self.ideal_drawdown_min - self.min_drawdown)
            return 50.0 + ratio * 50.0
        
        # Above ideal (diminishing returns)
        if dd_pct > self.ideal_drawdown_max:
            excess = dd_pct - self.ideal_drawdown_max
            penalty = min(excess / 20, 0.5)  # Max 50% penalty
            return 100.0 * (1 - penalty)
        
        return 50.0
    
    def _score_base(self, f1d: Dict[str, Any]) -> float:
        """
        Score base formation quality (0-100).
        
        Good base = consolidation without new lows.
        """
        base_detected = f1d.get('base_detected')
        
        if base_detected is None:
            return 0.0
        
        if base_detected:
            # Check volatility (ATR)
            atr = f1d.get('atr_pct')
            if atr and atr < 5:  # Very tight base
                return 100.0
            elif atr and atr < 10:  # Good base
                return 80.0
            else:
                return 60.0
        else:
            # No base detected
            return 0.0
    
    def _score_reclaim(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score reclaim strength (0-100).
        
        Strong reclaim:
        - Price above EMA20 and EMA50
        - Recent higher high
        - Positive momentum
        """
        score = 0.0
        
        # 1d reclaim
        dist_ema20 = f1d.get('dist_ema20_pct')
        dist_ema50 = f1d.get('dist_ema50_pct')
        
        # Above both EMAs
        if dist_ema20 and dist_ema20 > 0:
            score += 30
        if dist_ema50 and dist_ema50 > 0:
            score += 30
        
        # Higher high detected
        if f1d.get('hh_20'):
            score += 20
        
        # Momentum (recent returns)
        r7 = f1d.get('r_7')
        if r7 and r7 > 10:  # >10% in 7 days
            score += 20
        elif r7 and r7 > 5:
            score += 10
        
        return min(score, 100.0)
    
    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """
        Score volume confirmation (0-100).
        
        Strong volume = spike on reclaim.
        """
        vol_spike_1d = f1d.get('volume_spike', 1.0)
        vol_spike_4h = f4h.get('volume_spike', 1.0)
        
        # Use higher of the two
        max_spike = max(vol_spike_1d, vol_spike_4h)
        
        if max_spike < self.min_volume_spike:
            return 0.0
        
        # Linear scale from min to 3x
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
        flags: List[str]
    ) -> List[str]:
        """Generate human-readable reasons for the score."""
        reasons = []
        
        # Drawdown
        dd = f1d.get('drawdown_from_ath')
        if dd and dd < 0:
            dd_pct = abs(dd)
            if dd_score > 70:
                reasons.append(f"Strong drawdown setup ({dd_pct:.1f}% from ATH)")
            elif dd_score > 30:
                reasons.append(f"Moderate drawdown ({dd_pct:.1f}% from ATH)")
        
        # Base
        if base_score > 60:
            reasons.append("Clean base formation detected")
        elif base_score == 0:
            reasons.append("No base detected (still declining)")
        
        # Reclaim
        dist_ema50 = f1d.get('dist_ema50_pct')
        if reclaim_score > 60:
            reasons.append(f"Reclaimed EMAs (${dist_ema50:.1f}% above EMA50)")
        elif reclaim_score > 30:
            reasons.append("Partial reclaim in progress")
        else:
            reasons.append("Below EMAs (no reclaim yet)")
        
        # Volume
        vol_spike = max(f1d.get('volume_spike', 1.0), f4h.get('volume_spike', 1.0))
        if vol_score > 60:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif vol_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        
        # Flags
        if 'overextended' in flags:
            reasons.append(f"⚠️ Overextended ({dist_ema50:.1f}% above EMA50)")
        
        if 'low_liquidity' in flags:
            reasons.append("⚠️ Low liquidity")
        
        return reasons


def score_reversals(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all symbols for reversal setups and return ranked list.
    
    Args:
        features_data: Dict mapping symbol -> features
        volumes: Dict mapping symbol -> 24h volume
        config: Config dict
    
    Returns:
        List of scored symbols, sorted by score (descending)
    """
    scorer = ReversalScorer(config)
    results = []
    
    logger.info(f"Scoring {len(features_data)} symbols for reversal setups")
    
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        
        try:
            score_result = scorer.score(symbol, features, volume)
            
            results.append({
                'symbol': symbol,
                'price_usdt': features.get('price_usdt'),
                'coin_name': features.get('coin_name'),
                'market_cap': features.get('market_cap'),
                'quote_volume_24h': features.get('quote_volume_24h'),
                'score': score_result['score'],
                'components': score_result['components'],
                'penalties': score_result['penalties'],
                'flags': score_result['flags'],
                'reasons': score_result['reasons']
            })
            
        except Exception as e:
            logger.error(f"Failed to score {symbol}: {e}")
            continue
    
    # Sort by score (descending)
    results.sort(key=lambda x: x['score'], reverse=True)
    
    logger.info(f"Reversal scoring complete: {len(results)} symbols scored")
    
    return results
