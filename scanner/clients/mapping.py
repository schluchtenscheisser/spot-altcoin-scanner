"""
Mapping layer between MEXC symbols and CMC market cap data.

Handles:
- Symbol-based matching (primary)
- Collision detection (multiple CMC assets per symbol)
- Confidence scoring
- Manual overrides
- Mapping reports

This is a CRITICAL component - incorrect mapping = corrupted scores.
"""

from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from ..utils.logging_utils import get_logger
from ..utils.io_utils import load_json, save_json


logger = get_logger(__name__)


class MappingResult:
    """Result of a mapping operation."""
    
    def __init__(
        self,
        mexc_symbol: str,
        cmc_data: Optional[Dict[str, Any]] = None,
        confidence: str = "none",
        method: str = "none",
        collision: bool = False,
        notes: Optional[str] = None
    ):
        self.mexc_symbol = mexc_symbol
        self.cmc_data = cmc_data
        self.confidence = confidence  # "high", "medium", "low", "none"
        self.method = method
        self.collision = collision
        self.notes = notes
    
    @property
    def mapped(self) -> bool:
        """Check if mapping was successful."""
        return self.cmc_data is not None
    
    @property
    def base_asset(self) -> str:
        """Extract base asset from MEXC symbol (e.g., BTCUSDT -> BTC)."""
        # Remove USDT suffix
        if self.mexc_symbol.endswith("USDT"):
            return self.mexc_symbol[:-4]
        return self.mexc_symbol
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return {
            "mexc_symbol": self.mexc_symbol,
            "base_asset": self.base_asset,
            "mapped": self.mapped,
            "confidence": self.confidence,
            "method": self.method,
            "collision": self.collision,
            "notes": self.notes,
            "cmc_data": {
                "id": self.cmc_data.get("id") if self.cmc_data else None,
                "symbol": self.cmc_data.get("symbol") if self.cmc_data else None,
                "name": self.cmc_data.get("name") if self.cmc_data else None,
                "slug": self.cmc_data.get("slug") if self.cmc_data else None,
                "market_cap": self._get_market_cap() if self.cmc_data else None,
            }
        }
    
    def _get_market_cap(self) -> Optional[float]:
        """Extract market cap from CMC data."""
        try:
            return self.cmc_data["quote"]["USD"]["market_cap"]
        except (KeyError, TypeError):
            return None


class SymbolMapper:
    """
    Maps MEXC symbols to CMC market cap data.
    """
    
    def __init__(
        self,
        overrides_file: str = "config/mapping_overrides.json"
    ):
        """
        Initialize mapper.
        
        Args:
            overrides_file: Path to manual overrides JSON
        """
        self.overrides_file = Path(overrides_file)
        self.overrides = self._load_overrides()
        
        # Statistics
        self.stats = {
            "total": 0,
            "mapped": 0,
            "unmapped": 0,
            "collisions": 0,
            "overrides_used": 0,
            "confidence": {
                "high": 0,
                "medium": 0,
                "low": 0,
                "none": 0
            }
        }
    
    def _load_overrides(self) -> Dict[str, Any]:
        """Load manual mapping overrides."""
        if not self.overrides_file.exists():
            logger.info(f"No overrides file found at {self.overrides_file}")
            return {}
        
        try:
            overrides = load_json(self.overrides_file)
            logger.info(f"Loaded {len(overrides)} mapping overrides")
            return overrides
        except Exception as e:
            logger.error(f"Failed to load overrides: {e}")
            return {}
    
    def map_symbol(
        self,
        mexc_symbol: str,
        cmc_symbol_map: Dict[str, Dict[str, Any]]
    ) -> MappingResult:
        """
        Map a single MEXC symbol to CMC data.
        
        Args:
            mexc_symbol: MEXC trading pair (e.g., 'BTCUSDT')
            cmc_symbol_map: Symbol -> CMC data mapping
            
        Returns:
            MappingResult with confidence + collision info
        """
        # Extract base asset
        base_asset = mexc_symbol[:-4] if mexc_symbol.endswith("USDT") else mexc_symbol
        base_asset_upper = base_asset.upper()
        
        # Check overrides first
        if base_asset_upper in self.overrides:
            override = self.overrides[base_asset_upper]
            
            # Override can specify CMC symbol or "exclude"
            if override == "exclude":
                return MappingResult(
                    mexc_symbol=mexc_symbol,
                    cmc_data=None,
                    confidence="none",
                    method="override_exclude",
                    notes="Manually excluded via overrides"
                )
            
            # Try to find CMC data for override symbol
            override_symbol = override.upper()
            if override_symbol in cmc_symbol_map:
                self.stats["overrides_used"] += 1
                return MappingResult(
                    mexc_symbol=mexc_symbol,
                    cmc_data=cmc_symbol_map[override_symbol],
                    confidence="high",
                    method="override_match",
                    notes=f"Overridden to {override_symbol}"
                )
        
        # Direct symbol match
        if base_asset_upper in cmc_symbol_map:
            return MappingResult(
                mexc_symbol=mexc_symbol,
                cmc_data=cmc_symbol_map[base_asset_upper],
                confidence="high",
                method="symbol_exact_match"
            )
        
        # No match found
        return MappingResult(
            mexc_symbol=mexc_symbol,
            cmc_data=None,
            confidence="none",
            method="no_match",
            notes=f"Symbol {base_asset_upper} not found in CMC data"
        )
    
    def map_universe(
        self,
        mexc_symbols: List[str],
        cmc_symbol_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, MappingResult]:
        """
        Map entire MEXC universe to CMC data.
        
        Args:
            mexc_symbols: List of MEXC trading pairs
            cmc_symbol_map: CMC symbol -> data mapping
            
        Returns:
            Dict mapping mexc_symbol -> MappingResult
        """
        logger.info(f"Mapping {len(mexc_symbols)} MEXC symbols to CMC data")
        
        results = {}
        self.stats["total"] = len(mexc_symbols)
        
        for symbol in mexc_symbols:
            result = self.map_symbol(symbol, cmc_symbol_map)
            results[symbol] = result
            
            # Update stats
            if result.mapped:
                self.stats["mapped"] += 1
            else:
                self.stats["unmapped"] += 1
            
            if result.collision:
                self.stats["collisions"] += 1
            
            self.stats["confidence"][result.confidence] += 1
        
        # Log summary
        logger.info(f"Mapping complete:")
        logger.info(f"  Mapped: {self.stats['mapped']}/{self.stats['total']}")
        logger.info(f"  Unmapped: {self.stats['unmapped']}")
        logger.info(f"  Collisions: {self.stats['collisions']}")
        logger.info(f"  Confidence: {self.stats['confidence']}")
        logger.info(f"  Overrides used: {self.stats['overrides_used']}")
        
        return results
    
    def generate_reports(
        self,
        mapping_results: Dict[str, MappingResult],
        output_dir: str = "reports"
    ) -> None:
        """
        Generate mapping reports.
        
        Creates:
        - unmapped_symbols.json: Symbols without CMC match
        - mapping_collisions.json: Symbols with multiple CMC candidates
        - mapping_stats.json: Overall statistics
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Unmapped symbols
        unmapped = [
            {
                "mexc_symbol": result.mexc_symbol,
                "base_asset": result.base_asset,
                "notes": result.notes
            }
            for result in mapping_results.values()
            if not result.mapped
        ]
        
        unmapped_file = output_path / "unmapped_symbols.json"
        save_json(unmapped, unmapped_file)
        logger.info(f"Saved {len(unmapped)} unmapped symbols to {unmapped_file}")
        
        # Collisions
        collisions = [
            result.to_dict()
            for result in mapping_results.values()
            if result.collision
        ]
        
        collisions_file = output_path / "mapping_collisions.json"
        save_json(collisions, collisions_file)
        logger.info(f"Saved {len(collisions)} collisions to {collisions_file}")
        
        # Stats
        stats_file = output_path / "mapping_stats.json"
        save_json(self.stats, stats_file)
        logger.info(f"Saved mapping stats to {stats_file}")
    
    def suggest_overrides(
        self,
        mapping_results: Dict[str, MappingResult],
        output_file: str = "reports/suggested_overrides.json"
    ) -> Dict[str, str]:
        """
        Generate suggested overrides for unmapped symbols.
        
        Returns:
            Dict of base_asset -> "exclude" (user must review)
        """
        suggestions = {}
        
        for result in mapping_results.values():
            if not result.mapped and result.base_asset not in self.overrides:
                # Suggest exclusion (user can change to proper symbol)
                suggestions[result.base_asset] = "exclude"
        
        if suggestions:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            save_json(suggestions, output_path, indent=2)
            logger.info(f"Generated {len(suggestions)} override suggestions: {output_file}")
        
        return suggestions
