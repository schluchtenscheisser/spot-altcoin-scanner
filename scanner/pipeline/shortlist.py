"""
Shortlist Selection (Cheap Pass)
=================================

Reduces filtered universe to a shortlist for expensive operations (OHLCV fetch).
Uses cheap metrics (24h volume) to rank and select top N candidates.
"""

import logging
import math
from typing import List, Dict, Any

from scanner.config import ScannerConfig

from .cross_section import percent_rank_average_ties

logger = logging.getLogger(__name__)


class ShortlistSelector:
    """Select top candidates based on cheap-pass proxy liquidity."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize shortlist selector from central config defaults."""
        cfg = ScannerConfig(raw=config)
        self.max_size = int(cfg.budget_shortlist_size)
        self.pre_shortlist_market_cap_floor_usd = float(cfg.pre_shortlist_market_cap_floor_usd)

        if self.max_size < 1:
            raise ValueError(f"budget.shortlist_size ({self.max_size}) must be >= 1")
        if self.pre_shortlist_market_cap_floor_usd < 0:
            raise ValueError(
                "budget.pre_shortlist_market_cap_floor_usd "
                f"({self.pre_shortlist_market_cap_floor_usd}) must be >= 0"
            )

        logger.info(
            "Shortlist initialized: max_size=%s, pre_shortlist_market_cap_floor_usd=%.2f",
            self.max_size,
            self.pre_shortlist_market_cap_floor_usd,
        )

    def _attach_proxy_liquidity_score(self, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Attach proxy_liquidity_score based on quote_volume_24h percent-rank (log-scaled input)."""
        if not rows:
            return []

        log_volumes: List[float] = []
        for row in rows:
            vol = float(row.get('quote_volume_24h', 0) or 0)
            log_volumes.append(math.log1p(max(0.0, vol)))

        percent_scores = percent_rank_average_ties(log_volumes)

        enriched: List[Dict[str, Any]] = []
        for row, score in zip(rows, percent_scores):
            r = dict(row)
            r['proxy_liquidity_score'] = round(float(score), 6)
            r['proxy_liquidity_population_n'] = len(rows)
            enriched.append(r)

        return enriched

    def select(self, filtered_symbols: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Select top-N symbols via cheap-pass ranking under budget + floor constraints."""
        if not filtered_symbols:
            logger.warning("No symbols to shortlist (empty input)")
            return []

        eligible_symbols = [
            row for row in filtered_symbols
            if float(row.get('market_cap', 0) or 0) >= self.pre_shortlist_market_cap_floor_usd
        ]

        with_proxy_score = self._attach_proxy_liquidity_score(eligible_symbols)

        # Deterministic ordering: score desc, volume desc, symbol asc.
        sorted_symbols = sorted(
            with_proxy_score,
            key=lambda x: (
                -float(x.get('proxy_liquidity_score', 0) or 0),
                -float(x.get('quote_volume_24h', 0) or 0),
                str(x.get('symbol', '')),
            ),
        )

        shortlist = sorted_symbols[:self.max_size]

        logger.info(
            "Shortlist selected: %s symbols from %s eligible (%s input before floor; top %.1f%% of eligible by volume)",
            len(shortlist),
            len(eligible_symbols),
            len(filtered_symbols),
            (len(shortlist) / len(eligible_symbols) * 100.0) if eligible_symbols else 0.0,
        )

        if shortlist:
            max_vol = float(shortlist[0].get('quote_volume_24h', 0) or 0)
            min_vol = float(shortlist[-1].get('quote_volume_24h', 0) or 0)
            logger.info(f"Volume range: ${max_vol/1e6:.2f}M - ${min_vol/1e6:.2f}M")

        return shortlist

    def get_shortlist_stats(
        self,
        filtered_symbols: List[Dict[str, Any]],
        shortlist: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Get statistics about shortlist selection."""
        if not filtered_symbols:
            return {
                'input_count': 0,
                'shortlist_count': 0,
                'reduction_rate': '0%',
                'volume_coverage': '0%'
            }

        total_volume = sum(float(s.get('quote_volume_24h', 0) or 0) for s in filtered_symbols)
        shortlist_volume = sum(float(s.get('quote_volume_24h', 0) or 0) for s in shortlist)

        coverage = (shortlist_volume / total_volume * 100) if total_volume > 0 else 0

        return {
            'input_count': len(filtered_symbols),
            'shortlist_count': len(shortlist),
            'reduction_rate': f"{(1 - len(shortlist)/len(filtered_symbols))*100:.1f}%",
            'total_volume': f"${total_volume/1e6:.2f}M",
            'shortlist_volume': f"${shortlist_volume/1e6:.2f}M",
            'volume_coverage': f"{coverage:.1f}%"
        }
