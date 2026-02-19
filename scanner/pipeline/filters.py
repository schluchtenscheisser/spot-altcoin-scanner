"""
Universe Filtering
==================

Filters the MEXC universe to create a tradable shortlist:
1. Market Cap Filter (100M - 3B USD)
2. Liquidity Filter (minimum volume)
3. Exclusions (stablecoins, wrapped tokens, leveraged tokens)
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import yaml

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
        risk_cfg = config.get('risk_flags', {})

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

        default_quote_allowlist = ['USDT', 'USDC', 'DAI', 'TUSD', 'FDUSD', 'USDP', 'BUSD']
        self.quote_allowlist = [str(q).upper() for q in universe_cfg.get('quote_allowlist', default_quote_allowlist)]

        default_patterns = {
            'stablecoin_patterns': ['USD', 'USDT', 'USDC', 'BUSD', 'DAI', 'TUSD'],
            'wrapped_patterns': ['WBTC', 'WETH', 'WBNB'],
            'leveraged_patterns': ['UP', 'DOWN', 'BULL', 'BEAR'],
            'synthetic_patterns': [],
        }

        def _build_exclusion_patterns_from_new_config() -> List[str]:
            patterns: List[str] = []
            if exclusions_cfg.get('exclude_stablecoins', True):
                patterns.extend(exclusions_cfg.get('stablecoin_patterns', default_patterns['stablecoin_patterns']))
            if exclusions_cfg.get('exclude_wrapped_tokens', True):
                patterns.extend(exclusions_cfg.get('wrapped_patterns', default_patterns['wrapped_patterns']))
            if exclusions_cfg.get('exclude_leveraged_tokens', True):
                patterns.extend(exclusions_cfg.get('leveraged_patterns', default_patterns['leveraged_patterns']))
            if exclusions_cfg.get('exclude_synthetic_derivatives', False):
                patterns.extend(exclusions_cfg.get('synthetic_patterns', default_patterns['synthetic_patterns']))
            return [str(p).upper() for p in patterns]

        if 'exclusion_patterns' in legacy_filters:
            # Legacy override is key-presence based: [] explicitly disables exclusions.
            # A null value is treated as unset to avoid accidental broad allow-through.
            legacy_patterns = legacy_filters.get('exclusion_patterns')
            if legacy_patterns is None:
                logger.warning(
                    "filters.exclusion_patterns is null; treating as unset and falling back to exclusions.*"
                )
                self.exclusion_patterns = _build_exclusion_patterns_from_new_config()
            else:
                self.exclusion_patterns = [str(p).upper() for p in legacy_patterns]
        else:
            self.exclusion_patterns = _build_exclusion_patterns_from_new_config()

        self.minor_unlock_penalty_factor = float(risk_cfg.get('minor_unlock_penalty_factor', 0.9))
        self.denylist_path = Path(risk_cfg.get('denylist_file', 'config/denylist.yaml'))
        self.unlock_overrides_path = Path(risk_cfg.get('unlock_overrides_file', 'config/unlock_overrides.yaml'))

        self.denylist_symbols, self.denylist_bases = self._load_denylist(self.denylist_path)
        (
            self.major_unlock_symbols,
            self.major_unlock_bases,
            self.minor_unlock_symbols,
            self.minor_unlock_bases,
        ) = self._load_unlock_overrides(self.unlock_overrides_path)
        
        logger.info(f"Filters initialized: MCAP {self.mcap_min/1e6:.0f}M-{self.mcap_max/1e9:.1f}B, "
                   f"Min Volume {self.min_volume_24h/1e6:.1f}M")

    @staticmethod
    def _safe_load_yaml(path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        with path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return data if isinstance(data, dict) else {}

    def _load_denylist(self, path: Path) -> tuple[set[str], set[str]]:
        data = self._safe_load_yaml(path)
        symbols = set()
        bases = set()

        hard_exclude = data.get('hard_exclude', {}) if isinstance(data.get('hard_exclude', {}), dict) else {}
        for key in ('symbols', 'symbol'):
            raw = hard_exclude.get(key, [])
            if isinstance(raw, str):
                raw = [raw]
            symbols.update(str(v).upper() for v in raw)

        for key in ('bases', 'base'):
            raw = hard_exclude.get(key, [])
            if isinstance(raw, str):
                raw = [raw]
            bases.update(str(v).upper() for v in raw)

        return symbols, bases

    def _load_unlock_overrides(self, path: Path) -> tuple[set[str], set[str], set[str], set[str]]:
        data = self._safe_load_yaml(path)
        major_symbols: set[str] = set()
        major_bases: set[str] = set()
        minor_symbols: set[str] = set()
        minor_bases: set[str] = set()

        entries = data.get('overrides', [])
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            return major_symbols, major_bases, minor_symbols, minor_bases

        for entry in entries:
            if not isinstance(entry, dict):
                continue
            severity = str(entry.get('severity', '')).lower()
            days_to_unlock = entry.get('days_to_unlock')
            if days_to_unlock is not None and int(days_to_unlock) > 14:
                continue
            symbol = entry.get('symbol')
            base = entry.get('base')
            if severity == 'major':
                if symbol:
                    major_symbols.add(str(symbol).upper())
                if base:
                    major_bases.add(str(base).upper())
            elif severity == 'minor':
                if symbol:
                    minor_symbols.add(str(symbol).upper())
                if base:
                    minor_bases.add(str(base).upper())

        return major_symbols, major_bases, minor_symbols, minor_bases
    
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

        # Step 2: Quote asset filter (USDT-only or stablecoin allowlist)
        filtered = self._filter_quote_assets(filtered)
        logger.info(f"After Quote filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 3: Liquidity filter
        filtered = self._filter_liquidity(filtered)
        logger.info(f"After Liquidity filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 4: Exclusions
        filtered = self._filter_exclusions(filtered)
        logger.info(f"After Exclusions filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 5: Risk hard-excludes and soft penalties
        filtered = self._apply_risk_flags(filtered)
        logger.info(f"After Risk filter: {len(filtered)} symbols "
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
    

    def _extract_quote_asset(self, sym_data: Dict[str, Any]) -> Optional[str]:
        quote = sym_data.get('quote')
        if quote:
            return str(quote).upper()

        symbol = str(sym_data.get('symbol', '')).upper()
        for q in sorted(self.quote_allowlist, key=len, reverse=True):
            if symbol.endswith(q):
                return q

        return None

    def _filter_quote_assets(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter by quote asset according to include_only_usdt_pairs semantics."""
        filtered: List[Dict[str, Any]] = []

        for sym_data in symbols:
            quote = self._extract_quote_asset(sym_data)
            if self.include_only_usdt_pairs:
                if quote == 'USDT':
                    filtered.append(sym_data)
            else:
                if quote in self.quote_allowlist:
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

    def _apply_risk_flags(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        filtered = []
        for sym_data in symbols:
            symbol = str(sym_data.get('symbol', '')).upper()
            base = str(sym_data.get('base', '')).upper()

            hard_reasons = []
            if symbol in self.denylist_symbols or base in self.denylist_bases:
                hard_reasons.append('denylist')
            if symbol in self.major_unlock_symbols or base in self.major_unlock_bases:
                hard_reasons.append('major_unlock_within_14d')

            if hard_reasons:
                continue

            row = dict(sym_data)
            row['risk_flags'] = []
            row['soft_penalties'] = {}

            if symbol in self.minor_unlock_symbols or base in self.minor_unlock_bases:
                row['risk_flags'].append('minor_unlock_within_14d')
                row['soft_penalties']['minor_unlock_within_14d'] = self.minor_unlock_penalty_factor

            filtered.append(row)

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
        quote_pass = len(self._filter_quote_assets(symbols))
        liquidity_pass = len(self._filter_liquidity(symbols))
        exclusion_pass = len(self._filter_exclusions(symbols))
        
        # Full pipeline
        final_pass = len(self.apply_all(symbols))
        
        return {
            'total_input': total,
            'mcap_pass': mcap_pass,
            'mcap_fail': total - mcap_pass,
            'quote_pass': quote_pass,
            'quote_fail': total - quote_pass,
            'liquidity_pass': liquidity_pass,
            'liquidity_fail': total - liquidity_pass,
            'exclusion_pass': exclusion_pass,
            'exclusion_fail': total - exclusion_pass,
            'final_pass': final_pass,
            'final_fail': total - final_pass,
            'filter_rate': f"{final_pass/total*100:.1f}%" if total > 0 else "0%"
        }
