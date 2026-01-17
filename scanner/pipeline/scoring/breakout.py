"""
Breakout Setup Scoring
======================

Identifies range breakouts with volume confirmation.

Scoring Components:
1. Breakout Distance (35%) - How far above recent high
2. Volume Confirmation (30%) - Volume spike on breakout
3. Trend Context (20%) - Uptrend vs range
4. Momentum (15%) - Recent price action strength

Penalties:
- Overextension (too far, too fast)
- Low liquidity
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class BreakoutScorer:
    """Scores breakout setups (range break + volume)."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize breakout scorer.
        
        Args:
            config: Config dict with 'scoring' section
        """
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'raw'):
            scoring_config = config.raw.get('scoring', {}).get('breakout', {})
        else:
            scoring_config = config.get('scoring', {}).get('breakout', {})
        
        # Thresholds
        self.min_breakout_pct = scoring_config.get('min_breakout_pct', 2)  # >2% above high
        self.ideal_breakout_pct = scoring_config.get('ideal_breakout_pct', 5)  # 5-10% ideal
        self.max_breakout_pct = scoring_config.get('max_breakout_pct', 20)  # >20% = overextended
        
        self.min_volume_spike = scoring_config.get('min_volume_spike', 1.5)  # 1.5x normal
        self.ideal_volume_spike = scoring_config.get('ideal_volume_spike', 2.5)  # 2.5x+
        
        # Component weights
        self.weights = {
            'breakout': 0.35,
            'volume': 0.30,
            'trend': 0.20,
            'momentum': 0.15
        }
        
        logger.info("Breakout Scorer initialized")
    
    def score(
        self,
        symbol: str,
        features: Dict[str, Any],
        quote_volume_24h: float
    ) -> Dict[str, Any]:
        """
        Score a single symbol for breakout setup.
        
        Args:
            symbol: Trading pair
            features: Feature dict with '1d' and '4h'
            quote_volume_24h: 24h volume in USDT
        
        Returns:
            Score dict
        """
        f1d = features.get('1d', {})
        f4h = features.get('4h', {})
        
        # Components
        breakout_score = self._score_breakout(f1d)
        volume_score = self._score_volume(f1d, f4h)
        trend_score = self._score_trend(f1d)
        momentum_score = self._score_momentum(f1d)
        
        # Weighted total
        raw_score = (
            breakout_score * self.weights['breakout'] +
            volume_score * self.weights['volume'] +
            trend_score * self.weights['trend'] +
            momentum_score * self.weights['momentum']
        )
        
        # Penalties & Flags
        penalties = []
        flags = []
        
        # Overextension penalty
        breakout_dist = f1d.get('breakout_dist_20', 0)
        if breakout_dist > self.max_breakout_pct:
            penalties.append(('overextension', 0.6))
            flags.append('overextended')
        
        # Low liquidity
        if quote_volume_24h < 500_000:
            penalties.append(('low_liquidity', 0.8))
            flags.append('low_liquidity')
        
        # Apply penalties
        final_score = raw_score
        for name, factor in penalties:
            final_score *= factor
        
        # Reasons
        reasons = self._generate_reasons(
            breakout_score, volume_score, trend_score, momentum_score,
            f1d, f4h, flags
        )
        
        return {
            'score': round(final_score, 2),
            'components': {
                'breakout': round(breakout_score, 2),
                'volume': round(volume_score, 2),
                'trend': round(trend_score, 2),
                'momentum': round(momentum_score, 2)
            },
            'penalties': {name: factor for name, factor in penalties},
            'flags': flags,
            'reasons': reasons
        }
    
    def _score_breakout(self, f1d: Dict[str, Any]) -> float:
        """
        Score breakout distance (0-100).
        
        Ideal: 5-10% above recent high
        """
        dist = f1d.get('breakout_dist_20', -100)
        
        # Below high (no breakout)
        if dist < self.min_breakout_pct:
            return 0.0
        
        # Ideal range
        if self.ideal_breakout_pct <= dist <= self.ideal_breakout_pct * 2:
            return 100.0
        
        # Below ideal (linear scale)
        if dist < self.ideal_breakout_pct:
            ratio = (dist - self.min_breakout_pct) / (self.ideal_breakout_pct - self.min_breakout_pct)
            return 50.0 + ratio * 50.0
        
        # Above ideal but not overextended
        if dist < self.max_breakout_pct:
            excess = dist - (self.ideal_breakout_pct * 2)
            penalty = (excess / (self.max_breakout_pct - self.ideal_breakout_pct * 2)) * 30
            return max(70.0 - penalty, 40.0)
        
        # Overextended
        return 20.0
    
    def _score_volume(self, f1d: Dict[str, Any], f4h: Dict[str, Any]) -> float:
        """Score volume confirmation (0-100)."""
        vol_1d = f1d.get('volume_spike', 1.0)
        vol_4h = f4h.get('volume_spike', 1.0)
        
        max_spike = max(vol_1d, vol_4h)
        
        # Below minimum
        if max_spike < self.min_volume_spike:
            return 0.0
        
        # Ideal or above
        if max_spike >= self.ideal_volume_spike:
            return 100.0
        
        # Linear scale
        ratio = (max_spike - self.min_volume_spike) / (self.ideal_volume_spike - self.min_volume_spike)
        return ratio * 100.0
    
    def _score_trend(self, f1d: Dict[str, Any]) -> float:
        """
        Score trend context (0-100).
        
        Better if already in uptrend (above EMAs).
        """
        score = 0.0
        
        dist_ema20 = f1d.get('dist_ema20_pct')
        dist_ema50 = f1d.get('dist_ema50_pct')
        
        # Above EMA20
        if dist_ema20 and dist_ema20 > 0:
            score += 40
            if dist_ema20 > 5:
                score += 10
        
        # Above EMA50
        if dist_ema50 and dist_ema50 > 0:
            score += 40
            if dist_ema50 > 5:
                score += 10
        
        return min(score, 100.0)
    
    def _score_momentum(self, f1d: Dict[str, Any]) -> float:
        """
        Score recent momentum (0-100).
        
        Based on recent returns.
        """
        r7 = f1d.get('r_7', 0)
        
        if r7 <= 0:
            return 0.0
        
        if r7 >= 20:  # >20% in 7 days
            return 100.0
        
        # Linear scale 0-20%
        return (r7 / 20) * 100.0
    
    def _generate_reasons(
        self,
        breakout_score: float,
        volume_score: float,
        trend_score: float,
        momentum_score: float,
        f1d: Dict[str, Any],
        f4h: Dict[str, Any],
        flags: List[str]
    ) -> List[str]:
        """Generate human-readable reasons."""
        reasons = []
        
        # Breakout
        dist = f1d.get('breakout_dist_20', 0)
        if breakout_score > 70:
            reasons.append(f"Strong breakout ({dist:.1f}% above 20d high)")
        elif breakout_score > 30:
            reasons.append(f"Moderate breakout ({dist:.1f}% above high)")
        elif dist > 0:
            reasons.append(f"Early breakout ({dist:.1f}% above high)")
        else:
            reasons.append("No breakout (below recent high)")
        
        # Volume
        vol_spike = max(f1d.get('volume_spike', 1.0), f4h.get('volume_spike', 1.0))
        if volume_score > 70:
            reasons.append(f"Strong volume ({vol_spike:.1f}x average)")
        elif volume_score > 30:
            reasons.append(f"Moderate volume ({vol_spike:.1f}x)")
        else:
            reasons.append("Low volume (no confirmation)")
        
        # Trend
        if trend_score > 70:
            reasons.append("In uptrend (above EMAs)")
        elif trend_score > 30:
            reasons.append("Neutral trend")
        else:
            reasons.append("In downtrend (below EMAs)")
        
        # Flags
        if 'overextended' in flags:
            reasons.append(f"⚠️ Overextended ({dist:.1f}% above high)")
        
        if 'low_liquidity' in flags:
            reasons.append("⚠️ Low liquidity")
        
        return reasons


def score_breakouts(
    features_data: Dict[str, Dict[str, Any]],
    volumes: Dict[str, float],
    config: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Score all symbols for breakout setups and return ranked list.
    
    Args:
        features_data: Dict mapping symbol -> features
        volumes: Dict mapping symbol -> 24h volume
        config: Config dict
    
    Returns:
        List of scored symbols, sorted by score (descending)
    """
    scorer = BreakoutScorer(config)
    results = []
    
    logger.info(f"Scoring {len(features_data)} symbols for breakout setups")
    
    for symbol, features in features_data.items():
        volume = volumes.get(symbol, 0)
        
        try:
            score_result = scorer.score(symbol, features, volume)
            
            results.append({
                'symbol': symbol,
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
    
    logger.info(f"Breakout scoring complete: {len(results)} symbols scored")
    
    return results
