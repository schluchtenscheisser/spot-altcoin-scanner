"""
OHLCV Data Fetching
===================

Fetches OHLCV (klines) data for shortlisted symbols.
Supports multiple timeframes with caching.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

try:
    from scanner.utils.raw_collector import collect_raw_ohlcv
except ImportError:
    collect_raw_ohlcv = None

logger = logging.getLogger(__name__)


class OHLCVFetcher:
    """Fetches and caches OHLCV data for symbols."""

    def __init__(self, mexc_client, config: Dict[str, Any]):
        self.mexc = mexc_client
        root = config.raw if hasattr(config, 'raw') else config

        ohlcv_config = root.get('ohlcv', {})
        general_cfg = root.get('general', {})
        history_cfg = root.get('universe_filters', {}).get('history', {})

        self.timeframes = ohlcv_config.get('timeframes', ['1d', '4h'])

        lookback_1d = int(general_cfg.get('lookback_days_1d', 120))
        lookback_4h = int(general_cfg.get('lookback_days_4h', 30)) * 6
        self.lookback = {
            '1d': lookback_1d,
            '4h': lookback_4h,
            **ohlcv_config.get('lookback', {}),
        }

        self.min_candles = ohlcv_config.get('min_candles', {'1d': 50, '4h': 50})
        self.min_history_days_1d = int(history_cfg.get('min_history_days_1d', 60))

        logger.info(f"OHLCV Fetcher initialized: timeframes={self.timeframes}, lookback={self.lookback}")

    def fetch_all(self, shortlist: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        results = {}
        total = len(shortlist)

        logger.info(f"Fetching OHLCV for {total} symbols across {len(self.timeframes)} timeframes")

        for i, sym_data in enumerate(shortlist, 1):
            symbol = sym_data['symbol']
            logger.info(f"[{i}/{total}] Fetching {symbol}...")

            symbol_ohlcv = {}
            failed = False

            for tf in self.timeframes:
                limit = int(self.lookback.get(tf, 120))

                try:
                    klines = self.mexc.get_klines(symbol, tf, limit=limit)

                    if not klines:
                        logger.warning(f"  {symbol} {tf}: No data returned")
                        failed = True
                        break

                    min_required = int(self.min_candles.get(tf, 50))
                    if len(klines) < min_required:
                        logger.warning(f"  {symbol} {tf}: Insufficient data ({len(klines)} < {min_required} candles)")
                        failed = True
                        break

                    if tf == '1d' and len(klines) < self.min_history_days_1d:
                        logger.warning(
                            f"  {symbol} {tf}: Below history threshold ({len(klines)} < {self.min_history_days_1d} days)"
                        )
                        failed = True
                        break

                    symbol_ohlcv[tf] = klines
                    logger.info(f"  ✓ {symbol} {tf}: {len(klines)} candles")

                except Exception as e:
                    logger.error(f"  ✗ {symbol} {tf}: {e}")
                    failed = True
                    break

            if not failed:
                results[symbol] = symbol_ohlcv
            else:
                logger.warning(f"  Skipping {symbol} (incomplete data)")

        logger.info(f"OHLCV fetch complete: {len(results)}/{total} symbols with complete data")

        if collect_raw_ohlcv and results:
            try:
                collect_raw_ohlcv(results)
            except Exception as e:
                logger.warning(f"Could not collect raw OHLCV snapshot: {e}")

        return results

    def get_fetch_stats(self, ohlcv_data: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        if not ohlcv_data:
            return {'symbols_count': 0, 'timeframes': [], 'total_candles': 0}

        total_candles = 0
        for symbol_data in ohlcv_data.values():
            for tf_data in symbol_data.values():
                total_candles += len(tf_data)

        date_range = None
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
            'date_range': date_range,
        }
