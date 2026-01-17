"""
OHLCV Data Fetching
===================

Fetches OHLCV (klines) data for shortlisted symbols.
Supports multiple timeframes with caching.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OHLCVFetcher:
    """Fetches and caches OHLCV data for symbols."""
    
    def __init__(self, mexc_client, config: Dict[str, Any]):
        """
        Initialize OHLCV fetcher.
        
        Args:
            mexc_client: Instance of MEXCClient
            config: Config dict with 'ohlcv' section
        """
        self.mexc = mexc_client
        
        # Handle both dict and ScannerConfig object
        if hasattr(config, 'get'):
            self.config = config.get('ohlcv', {})
        else:
            # It's a ScannerConfig object, access via attributes
            self.config = getattr(config, 'ohlcv', {}) if hasattr(config, 'ohlcv') else {}
        
        # Timeframes to fetch
        self.timeframes = self.config.get('timeframes', ['1d', '4h']) if isinstance(self.config, dict) else ['1d', '4h']
        
        # Lookback (number of candles)
        if isinstance(self.config, dict):
            self.lookback = self.config.get('lookback', {'1d': 120, '4h': 180})
            self.min_candles = self.config.get('min_candles', {'1d': 60, '4h': 90})
        else:
            self.lookback = {'1d': 120, '4h': 180}
            self.min_candles = {'1d': 60, '4h': 90}
        
        logger.info(f"OHLCV Fetcher initialized: timeframes={self.timeframes}")
    
    def fetch_all(
        self,
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch OHLCV for all symbols in shortlist.
        
        Args:
            shortlist: List of symbol dicts with 'symbol' key
        
        Returns:
            Dict mapping symbol -> timeframe -> OHLCV data
            {
                'BTCUSDT': {
                    '1d': [...],
                    '4h': [...]
                },
                ...
            }
        """
        results = {}
        total = len(shortlist)
        
        logger.info(f"Fetching OHLCV for {total} symbols across {len(self.timeframes)} timeframes")
        
        for i, sym_data in enumerate(shortlist, 1):
            symbol = sym_data['symbol']
            
            logger.info(f"[{i}/{total}] Fetching {symbol}...")
            
            symbol_ohlcv = {}
            failed = False
            
            # Fetch each timeframe
            for tf in self.timeframes:
                limit = self.lookback.get(tf, 120)
                
                try:
                    klines = self.mexc.get_klines(symbol, tf, limit=limit)
                    
                    if not klines:
                        logger.warning(f"  {symbol} {tf}: No data returned")
                        failed = True
                        break
                    
                    # Check minimum candles
                    min_required = self.min_candles.get(tf, 60)
                    if len(klines) < min_required:
                        logger.warning(f"  {symbol} {tf}: Insufficient data "
                                     f"({len(klines)} < {min_required} candles)")
                        failed = True
                        break
                    
                    symbol_ohlcv[tf] = klines
                    logger.info(f"  ✓ {symbol} {tf}: {len(klines)} candles")
                    
                except Exception as e:
                    logger.error(f"  ✗ {symbol} {tf}: {e}")
                    failed = True
                    break
            
            # Only include if all timeframes succeeded
            if not failed:
                results[symbol] = symbol_ohlcv
            else:
                logger.warning(f"  Skipping {symbol} (incomplete data)")
        
        logger.info(f"OHLCV fetch complete: {len(results)}/{total} symbols with complete data")
        
        return results
    
    def get_fetch_stats(
        self,
        ohlcv_data: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about fetched OHLCV data.
        
        Args:
            ohlcv_data: Output from fetch_all()
        
        Returns:
            Stats dict
        """
        if not ohlcv_data:
            return {
                'symbols_count': 0,
                'timeframes': [],
                'total_candles': 0
            }
        
        # Count candles
        total_candles = 0
        for symbol_data in ohlcv_data.values():
            for tf_data in symbol_data.values():
                total_candles += len(tf_data)
        
        # Get date range (from 1d data)
        date_range = None
        if ohlcv_data:
            first_symbol = list(ohlcv_data.keys())[0]
            if '1d' in ohlcv_data[first_symbol]:
                candles = ohlcv_data[first_symbol]['1d']
                if candles:
                    oldest = datetime.fromtimestamp(candles[0][0] / 1000).strftime('%Y-%m-%d')
                    newest = datetime.fromtimestamp(candles[-1][0] / 1000).strftime('%Y-%m-%d')
                    date_range = f"{oldest} to {newest}"
        
        return {
            'symbols_count': len(ohlcv_data),
            'timeframes': self.timeframes,
            'total_candles': total_candles,
            'avg_candles_per_symbol': total_candles / len(ohlcv_data) if ohlcv_data else 0,
            'date_range': date_range
        }
