"""
Universe Filtering
==================

Filters the MEXC universe to create a tradable shortlist:
1. Market Cap Filter (100M - 3B USD)
2. Liquidity Filter (minimum volume)
3. Exclusions (stablecoins, wrapped tokens, leveraged tokens)
"""

import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class UniverseFilters:
    """Filters for reducing MEXC universe to tradable MidCaps."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize filters with config.
        
        Args:
            config: Config dict with 'filters' section
        """
        legacy_filters = config.get('filters', {})
        universe_cfg = config.get('universe_filters', {})
        exclusions_cfg = config.get('exclusions', {})

        mcap_cfg = universe_cfg.get('market_cap', {})
        volume_cfg = universe_cfg.get('volume', {})
        history_cfg = universe_cfg.get('history', {})

        # Market Cap bounds (in USD)
        self.mcap_min = mcap_cfg.get('min_usd', legacy_filters.get('mcap_min', 100_000_000))  # 100M
        self.mcap_max = mcap_cfg.get('max_usd', legacy_filters.get('mcap_max', 3_000_000_000))  # 3B

        # Liquidity (24h volume in USDT)
        self.min_volume_24h = volume_cfg.get('min_quote_volume_24h', legacy_filters.get('min_volume_24h', 1_000_000))

        # Minimum 1d history used by OHLCV filtering step.
        self.min_history_days_1d = int(history_cfg.get('min_history_days_1d', 60))

        self.include_only_usdt_pairs = bool(universe_cfg.get('include_only_usdt_pairs', True))

        default_patterns = {
            'stablecoin_patterns': ['USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD'],
            'wrapped_patterns': ['WBTC', 'WETH', 'WBNB'],
            'leveraged_patterns': ['UP', 'DOWN', 'BULL', 'BEAR'],
            'synthetic_patterns': [],
        }

        if legacy_filters.get('exclusion_patterns'):
            self.exclusion_patterns = [str(p).upper() for p in legacy_filters['exclusion_patterns']]
        else:
            self.exclusion_patterns = []
            if exclusions_cfg.get('exclude_stablecoins', True):
                self.exclusion_patterns.extend(exclusions_cfg.get('stablecoin_patterns', default_patterns['stablecoin_patterns']))
            if exclusions_cfg.get('exclude_wrapped_tokens', True):
                self.exclusion_patterns.extend(exclusions_cfg.get('wrapped_patterns', default_patterns['wrapped_patterns']))
            if exclusions_cfg.get('exclude_leveraged_tokens', True):
                self.exclusion_patterns.extend(exclusions_cfg.get('leveraged_patterns', default_patterns['leveraged_patterns']))
            if exclusions_cfg.get('exclude_synthetic_derivatives', False):
                self.exclusion_patterns.extend(exclusions_cfg.get('synthetic_patterns', default_patterns['synthetic_patterns']))
            self.exclusion_patterns = [str(p).upper() for p in self.exclusion_patterns]
        
        logger.info(f"Filters initialized: MCAP {self.mcap_min/1e6:.0f}M-{self.mcap_max/1e9:.1f}B, "
                   f"Min Volume {self.min_volume_24h/1e6:.1f}M")
    
    def apply_all(
        self,
        symbols_with_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Apply all filters in sequence.
        
        Args:
            symbols_with_data: List of dicts with keys:
                - symbol: str (e.g. "BTCUSDT")
                - base: str (e.g. "BTC")
                - quote_volume_24h: float
                - market_cap: float (from CMC mapping)
        
        Returns:
            Filtered list
        """
        original_count = len(symbols_with_data)
        logger.info(f"Starting filters with {original_count} symbols")
        
        # Step 1: Market Cap filter
        filtered = self._filter_mcap(symbols_with_data)
        logger.info(f"After MCAP filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        # Step 2: Liquidity filter
        filtered = self._filter_liquidity(filtered)
        logger.info(f"After Liquidity filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        # Step 3: Exclusions
        filtered = self._filter_exclusions(filtered)
        logger.info(f"After Exclusions filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")
        
        logger.info(f"Final universe: {len(filtered)} symbols "
                   f"(filtered out {original_count - len(filtered)})")
        
        return filtered
    
    def _filter_mcap(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by market cap range."""
        filtered = []
        
        for sym_data in symbols:
            mcap = sym_data.get('market_cap')
            
            # Skip if no market cap data
            if mcap is None:
                continue
            
            # Check bounds
            if self.mcap_min <= mcap <= self.mcap_max:
                filtered.append(sym_data)
        
        return filtered
    
    def _filter_liquidity(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by minimum 24h volume."""
        filtered = []
        
        for sym_data in symbols:
            volume = sym_data.get('quote_volume_24h', 0)
            
            if volume >= self.min_volume_24h:
                filtered.append(sym_data)
        
        return filtered
    
    def _filter_exclusions(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Exclude stablecoins, wrapped tokens, leveraged tokens."""
        filtered = []
        
        for sym_data in symbols:
            base = sym_data.get('base', '')
            
            # Check if base matches any exclusion pattern
            is_excluded = False
            for pattern in self.exclusion_patterns:
                if pattern in base.upper():
                    is_excluded = True
                    break
            
            if not is_excluded:
                filtered.append(sym_data)
        
        return filtered
    
    def get_filter_stats(self, symbols: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Get statistics about what would be filtered.
        
        Args:
            symbols: Input symbols
        
        Returns:
            Dict with filter stats
        """
        total = len(symbols)
        
        # Count what passes each filter
        mcap_pass = len(self._filter_mcap(symbols))
        liquidity_pass = len(self._filter_liquidity(symbols))
        exclusion_pass = len(self._filter_exclusions(symbols))
        
        # Full pipeline
        final_pass = len(self.apply_all(symbols))
        
        return {
            'total_input': total,
            'mcap_pass': mcap_pass,
            'mcap_fail': total - mcap_pass,
            'liquidity_pass': liquidity_pass,
            'liquidity_fail': total - liquidity_pass,
            'exclusion_pass': exclusion_pass,
            'exclusion_fail': total - exclusion_pass,
            'final_pass': final_pass,
            'final_fail': total - final_pass,
            'filter_rate': f"{final_pass/total*100:.1f}%" if total > 0 else "0%"
        }
