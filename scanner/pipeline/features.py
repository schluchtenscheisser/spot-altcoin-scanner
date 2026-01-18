"""
Feature Engine
==============

Computes technical features from OHLCV data for both 1d and 4h timeframes.

Features computed:
- Price: Returns (1d/3d/7d), HH/HL detection
- Trend: EMA20/50, Price relative to EMAs
- Volatility: ATR%
- Volume: Spike detection, Volume SMA
- Structure: Breakout distance, Drawdown, Base detection
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Computes technical features from OHLCV data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize feature engine.
        
        Args:
            config: Config dict (not used currently, for future extensions)
        """
        self.config = config
        logger.info("Feature Engine initialized")
    
    def compute_all(
        self,
        ohlcv_data: Dict[str, Dict[str, List[List]]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute features for all symbols.
        
        Args:
            ohlcv_data: Dict mapping symbol -> timeframe -> klines
                {
                    'BTCUSDT': {
                        '1d': [[ts, o, h, l, c, v, ...], ...],
                        '4h': [[ts, o, h, l, c, v, ...], ...]
                    },
                    ...
                }
        
        Returns:
            Dict mapping symbol -> features
            {
                'BTCUSDT': {
                    '1d': {...},
                    '4h': {...},
                    'meta': {...}
                },
                ...
            }
        """
        results = {}
        total = len(ohlcv_data)
        
        logger.info(f"Computing features for {total} symbols")
        
        for i, (symbol, tf_data) in enumerate(ohlcv_data.items(), 1):
            logger.debug(f"[{i}/{total}] Computing features for {symbol}")
            
            try:
                symbol_features = {}
                
                # Compute features for each timeframe
                if '1d' in tf_data:
                    symbol_features['1d'] = self._compute_timeframe_features(
                        tf_data['1d'], 
                        timeframe='1d'
                    )
                
                if '4h' in tf_data:
                    symbol_features['4h'] = self._compute_timeframe_features(
                        tf_data['4h'],
                        timeframe='4h'
                    )
                
                # Meta info
                symbol_features['meta'] = {
                    'symbol': symbol,
                    'last_update': int(tf_data['1d'][-1][0]) if '1d' in tf_data else None
                }
                
                results[symbol] = symbol_features
                
            except Exception as e:
                logger.error(f"Failed to compute features for {symbol}: {e}")
                continue
        
        logger.info(f"Features computed for {len(results)}/{total} symbols")
        return results
    
    def _compute_timeframe_features(
        self,
        klines: List[List],
        timeframe: str
    ) -> Dict[str, Any]:
        """
        Compute features for a single timeframe.
        
        Args:
            klines: List of klines [[ts, o, h, l, c, v, ...], ...]
            timeframe: '1d' or '4h'
        
        Returns:
            Feature dict (all numpy types converted to Python native types)
        """
        # Extract OHLCV arrays
        closes = np.array([k[4] for k in klines], dtype=float)
        highs = np.array([k[2] for k in klines], dtype=float)
        lows = np.array([k[3] for k in klines], dtype=float)
        volumes = np.array([k[5] for k in klines], dtype=float)
        
        features = {}
        
        # Current price
        features['close'] = float(closes[-1])
        features['high'] = float(highs[-1])
        features['low'] = float(lows[-1])
        features['volume'] = float(volumes[-1])
        
        # Returns
        features['r_1'] = self._calc_return(closes, 1)
        features['r_3'] = self._calc_return(closes, 3)
        features['r_7'] = self._calc_return(closes, 7)
        
        # EMAs
        features['ema_20'] = self._calc_ema(closes, 20)
        features['ema_50'] = self._calc_ema(closes, 50)
        
        # Price relative to EMAs (%)
        features['dist_ema20_pct'] = ((closes[-1] / features['ema_20']) - 1) * 100 if features['ema_20'] else None
        features['dist_ema50_pct'] = ((closes[-1] / features['ema_50']) - 1) * 100 if features['ema_50'] else None
        
        # ATR (as % of price)
        features['atr_pct'] = self._calc_atr_pct(highs, lows, closes, period=14)
        
        # Volume
        # Wenn kein SMA-Wert vorhanden oder dieser 0 ist, setze Volume-Spike = 0.0 (neutral)
        features['volume_sma_14'] = self._calc_sma(volumes, 14)
        features['volume_spike'] = (
            float(volumes[-1] / features['volume_sma_14'])
            if features.get('volume_sma_14', 0) > 0
            else 0.0
        )
        
        # Higher High / Higher Low (trend structure) - convert to native bool
        features['hh_20'] = bool(self._detect_higher_high(highs, lookback=20))
        features['hl_20'] = bool(self._detect_higher_low(lows, lookback=20))
        
        # Breakout distance (distance to recent high)
        # Fallback auf 0.0, falls zu wenig Daten oder NaN-Werte vorhanden sind
        features['breakout_dist_20'] = (
            self._calc_breakout_distance(closes, highs, lookback=20) or 0.0
        )
        features['breakout_dist_30'] = (
            self._calc_breakout_distance(closes, highs, lookback=30) or 0.0
        )
        
        # Drawdown from ATH
        features['drawdown_from_ath'] = self._calc_drawdown(closes)
        
        # Base detection (sideways consolidation)
        if timeframe == '1d':
            base_result = self._detect_base(closes, lows, lookback=30)
            features['base_detected'] = bool(base_result) if base_result is not None else None
        else:
            features['base_detected'] = None
        
        # Ensure all numeric values are native Python types for JSON serialization
        return self._convert_to_native_types(features)
    
    def _convert_to_native_types(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Convert numpy types to Python native types for JSON serialization."""
        converted = {}
        for key, value in features.items():
            if value is None:
                converted[key] = None
            elif isinstance(value, (np.floating, np.float64, np.float32)):
                converted[key] = float(value)
            elif isinstance(value, (np.integer, np.int64, np.int32)):
                converted[key] = int(value)
            elif isinstance(value, (np.bool_, bool)):
                converted[key] = bool(value)
            else:
                converted[key] = value
        return converted
    
    def _calc_return(self, closes: np.ndarray, periods: int) -> Optional[float]:
        """Calculate return over N periods (%)."""
        if len(closes) <= periods:
            return None
        return float(((closes[-1] / closes[-periods-1]) - 1) * 100)
    
    def _calc_ema(self, data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Exponential Moving Average."""
        if len(data) < period:
            return None
        
        alpha = 2 / (period + 1)
        ema = data[0]
        
        for val in data[1:]:
            ema = alpha * val + (1 - alpha) * ema
        
        return float(ema)
    
    def _calc_sma(self, data: np.ndarray, period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(data) < period:
            return None
        return float(np.mean(data[-period:]))
    
    def _calc_atr_pct(
        self,
        highs: np.ndarray,
        lows: np.ndarray,
        closes: np.ndarray,
        period: int = 14
    ) -> Optional[float]:
        """Calculate Average True Range as % of price."""
        if len(highs) < period + 1:
            return None
        
        # True Range
        tr = []
        for i in range(1, len(highs)):
            hl = highs[i] - lows[i]
            hc = abs(highs[i] - closes[i-1])
            lc = abs(lows[i] - closes[i-1])
            tr.append(max(hl, hc, lc))
        
        tr = np.array(tr)
        
        # ATR
        atr = np.mean(tr[-period:])
        
        # As % of current price
        return float((atr / closes[-1]) * 100) if closes[-1] > 0 else None
    
    def _detect_higher_high(self, highs: np.ndarray, lookback: int = 20) -> bool:
        """Detect if recent high is highest in lookback period."""
        if len(highs) < lookback:
            return False
        
        recent_high = np.max(highs[-5:])  # Last 5 bars
        lookback_high = np.max(highs[-lookback:-5])  # Previous bars
        
        return bool(recent_high > lookback_high)
    
    def _detect_higher_low(self, lows: np.ndarray, lookback: int = 20) -> bool:
        """Detect if recent low is higher than lookback period."""
        if len(lows) < lookback:
            return False
        
        recent_low = np.min(lows[-5:])  # Last 5 bars
        lookback_low = np.min(lows[-lookback:-5])  # Previous bars
        
        return bool(recent_low > lookback_low)
    
    def _calc_breakout_distance(
        self,
        closes: np.ndarray,
        highs: np.ndarray,
        lookback: int = 20
    ) -> Optional[float]:
        """
        Calculate distance to breakout level (%).
        Positive = above recent high, Negative = below.
        """
        if len(highs) < lookback:
            return None
        
        recent_high = np.max(highs[-lookback:])
        current = closes[-1]
        
        return float(((current / recent_high) - 1) * 100)
    
    def _calc_drawdown(self, closes: np.ndarray) -> Optional[float]:
        """Calculate drawdown from ATH (%)."""
        if len(closes) == 0:
            return None
        
        ath = np.max(closes)
        current = closes[-1]
        
        return float(((current / ath) - 1) * 100)
    
    def _detect_base(
        self,
        closes: np.ndarray,
        lows: np.ndarray,
        lookback: int = 30
    ) -> Optional[bool]:
        """
        Detect base formation (sideways consolidation).
        
        Criteria:
        - No new lows in last 10 bars
        - Low volatility (ATR)
        """
        if len(closes) < lookback:
            return None
        
        recent_period = lookback // 3  # Last third of lookback
        
        # Check for new lows
        recent_low = np.min(lows[-recent_period:])
        prior_low = np.min(lows[-lookback:-recent_period])
        
        no_new_lows = recent_low >= prior_low
        
        # Check volatility (simple range check)
        recent_range = (np.max(closes[-recent_period:]) - np.min(closes[-recent_period:])) / np.mean(closes[-recent_period:])
        
        low_volatility = recent_range < 0.15  # Less than 15% range
        
        return bool(no_new_lows and low_volatility)
