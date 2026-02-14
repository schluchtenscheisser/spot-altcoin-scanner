"""
Shortlist Selection (Cheap Pass)
=================================

Reduces filtered universe to a shortlist for expensive operations (OHLCV fetch).
Uses cheap metrics (24h volume) to rank and select top N candidates.
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class ShortlistSelector:
    """Selects top candidates based on volume for OHLCV processing."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize shortlist selector.
        
        Args:
            config: Config dict with 'shortlist' section
        """
        self.config = config.get('shortlist', {})
        general_cfg = config.get('general', {})

        # Default: Top 100 by volume
        self.max_size = int(general_cfg.get('shortlist_size', self.config.get('max_size', 100)))
        
        # Minimum size (even if fewer pass filters)
        self.min_size = self.config.get('min_size', 10)
        
        logger.info(f"Shortlist initialized: max_size={self.max_size}, min_size={self.min_size}")
    
    def select(self, filtered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Select top N symbols by 24h volume.
        
        Args:
            filtered_symbols: List of symbols that passed filters
                Each dict must have:
                - symbol: str
                - base: str
                - quote_volume_24h: float
                - market_cap: float
        
        Returns:
            Shortlist (top N by volume)
        """
        if not filtered_symbols:
            logger.warning("No symbols to shortlist (empty input)")
            return []
        
        # Sort by volume (descending)
        sorted_symbols = sorted(
            filtered_symbols,
            key=lambda x: x.get('quote_volume_24h', 0),
            reverse=True
        )
        
        # Take top N
        shortlist = sorted_symbols[:self.max_size]
        
        logger.info(f"Shortlist selected: {len(shortlist)} symbols from {len(filtered_symbols)} "
                   f"(top {len(shortlist)/len(filtered_symbols)*100:.1f}% by volume)")
        
        # Log volume range
        if shortlist:
            max_vol = shortlist[0].get('quote_volume_24h', 0)
            min_vol = shortlist[-1].get('quote_volume_24h', 0)
            logger.info(f"Volume range: ${max_vol/1e6:.2f}M - ${min_vol/1e6:.2f}M")
        
        return shortlist
    
    def get_shortlist_stats(
        self,
        filtered_symbols: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get statistics about shortlist selection.
        
        Args:
            filtered_symbols: Input (post-filter)
            shortlist: Output (post-shortlist)
        
        Returns:
            Stats dict
        """
        if not filtered_symbols:
            return {
                'input_count': 0,
                'shortlist_count': 0,
                'reduction_rate': '0%',
                'volume_coverage': '0%'
            }
        
        # Volume stats
        total_volume = sum(s.get('quote_volume_24h', 0) for s in filtered_symbols)
        shortlist_volume = sum(s.get('quote_volume_24h', 0) for s in shortlist)
        
        coverage = (shortlist_volume / total_volume * 100) if total_volume > 0 else 0
        
        return {
            'input_count': len(filtered_symbols),
            'shortlist_count': len(shortlist),
            'reduction_rate': f"{(1 - len(shortlist)/len(filtered_symbols))*100:.1f}%",
            'total_volume': f"${total_volume/1e6:.2f}M",
            'shortlist_volume': f"${shortlist_volume/1e6:.2f}M",
            'volume_coverage': f"{coverage:.1f}%"
        }
