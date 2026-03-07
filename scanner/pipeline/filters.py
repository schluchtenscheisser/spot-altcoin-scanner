"""Universe filtering for pre-shortlist pool construction.

Hard excludes in this stage are intentionally limited to:
- pre-shortlist market-cap floor guardrail
- quote asset allowlist
- safety exclusions (stable/wrapped/leveraged/etc.)
- hard risk blockers (denylist + major unlock)

Legacy market-cap/volume/share limits are loaded as soft-prior context only.
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

        budget_cfg = config.get('budget', {})

        # Market Cap context bounds (in USD, no hard exclude semantics).
        self.mcap_min = mcap_cfg.get('min_usd', legacy_filters.get('mcap_min', 100_000_000))  # 100M
        self.mcap_max = mcap_cfg.get('max_usd', legacy_filters.get('mcap_max', 3_000_000_000))  # 3B

        # Hard pre-shortlist floor guardrail.
        self.pre_shortlist_market_cap_floor_usd = float(budget_cfg.get('pre_shortlist_market_cap_floor_usd', 25_000_000))

        # Liquidity context (legacy hard gates are now soft priors only)
        self.min_turnover_24h = float(volume_cfg.get('min_turnover_24h', 0.03))
        if 'min_mexc_quote_volume_24h_usdt' in volume_cfg:
            self.min_mexc_quote_volume_24h_usdt = float(volume_cfg.get('min_mexc_quote_volume_24h_usdt', 5_000_000))
        else:
            self.min_mexc_quote_volume_24h_usdt = float(
                volume_cfg.get('min_quote_volume_24h', legacy_filters.get('min_volume_24h', 5_000_000))
            )
        self.min_mexc_share_24h = float(volume_cfg.get('min_mexc_share_24h', 0.01))

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
        
        logger.info(
            f"Filters initialized: pre-shortlist MCAP floor>={self.pre_shortlist_market_cap_floor_usd/1e6:.1f}M, "
            f"legacy MCAP context {self.mcap_min/1e6:.0f}M-{self.mcap_max/1e9:.1f}B, "
            f"legacy liquidity priors turnover>={self.min_turnover_24h:.4f}, "
            f"mexc_volume>={self.min_mexc_quote_volume_24h_usdt/1e6:.1f}M, "
            f"mexc_share>={self.min_mexc_share_24h:.4f}"
        )

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
            symbol = entry.get('symbol')
            base = entry.get('base')

            parsed_days = self._parse_days_to_unlock(days_to_unlock, symbol=symbol, base=base)
            if parsed_days is None:
                continue
            if parsed_days > 14:
                continue

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

    def _parse_days_to_unlock(
        self,
        value: Any,
        *,
        symbol: Optional[str] = None,
        base: Optional[str] = None,
    ) -> Optional[int]:
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            identifier = symbol or base or '<unknown>'
            logger.warning("Invalid days_to_unlock for %s: %r", identifier, value)
            return None

        if parsed < 0:
            identifier = symbol or base or '<unknown>'
            logger.warning("Invalid days_to_unlock for %s: %r", identifier, value)
            return None

        return parsed
    
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
        
        # Step 1: Hard pre-shortlist market-cap floor
        filtered = self._filter_pre_shortlist_market_cap_floor(symbols_with_data)
        logger.info(f"After pre-shortlist MCAP floor: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 2: Quote asset filter (USDT-only or stablecoin allowlist)
        filtered = self._filter_quote_assets(filtered)
        logger.info(f"After Quote filter: {len(filtered)} symbols "
                   f"({len(filtered)/original_count*100:.1f}%)")

        # Step 3: Liquidity stage is soft-prior only; no hard excludes.
        filtered = self._apply_soft_liquidity_priors(filtered)
        logger.info(f"After soft liquidity priors: {len(filtered)} symbols "
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
    
    def _filter_pre_shortlist_market_cap_floor(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply hard pre-shortlist market-cap floor guardrail."""
        filtered = []
        
        for sym_data in symbols:
            mcap = sym_data.get('market_cap')
            
            # Skip if no market cap data
            if mcap is None:
                continue
            
            # Hard guardrail: below floor is excluded before shortlist.
            if mcap >= self.pre_shortlist_market_cap_floor_usd:
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

    def _apply_soft_liquidity_priors(self, symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Keep rows unchanged; liquidity metrics remain context/prior fields only."""
        return symbols
    
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
        mcap_pass = len(self._filter_pre_shortlist_market_cap_floor(symbols))
        quote_pass = len(self._filter_quote_assets(symbols))
        liquidity_pass = len(self._apply_soft_liquidity_priors(symbols))
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
