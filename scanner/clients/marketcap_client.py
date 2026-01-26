"""
CoinMarketCap API Client for market cap data.

Responsibilities:
- Fetch bulk cryptocurrency listings
- Get market cap, rank, supply data
- Cache daily for rate-limit efficiency

API Docs: https://coinmarketcap.com/api/documentation/v1/
"""

import os
from typing import Dict, List, Optional, Any
import requests
from ..utils.logging_utils import get_logger
from ..utils.io_utils import load_cache, save_cache, cache_exists

# 🔹 Neu: zentralisierte Rohdaten-Speicherung
try:
    from scanner.utils.raw_collector import collect_raw_marketcap
except ImportError:
    collect_raw_marketcap = None


logger = get_logger(__name__)


class MarketCapClient:
    """
    CoinMarketCap API client with caching and rate-limit protection.
    """
    
    BASE_URL = "https://pro-api.coinmarketcap.com"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        """
        Initialize CMC client.
        
        Args:
            api_key: CMC API key (default: from CMC_API_KEY env var)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("CMC_API_KEY")
        self.timeout = timeout
        
        if not self.api_key:
            logger.warning("CMC_API_KEY not set - client will fail on API calls")
        
        self.session = requests.Session()
        self.session.headers.update({
            "X-CMC_PRO_API_KEY": self.api_key or "",
            "Accept": "application/json"
        })
    
    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make API request.
        
        Args:
            endpoint: API endpoint (e.g., '/v1/cryptocurrency/listings/latest')
            params: Query parameters
            
        Returns:
            API response data
            
        Raises:
            requests.RequestException: On API failure
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            response = self.session.get(
                url,
                params=params,
                timeout=self.timeout
            )
            
            # Handle rate limit
            if response.status_code == 429:
                logger.error("CMC rate limit hit - check your plan limits")
                raise requests.RequestException("CMC rate limit exceeded")
            
            response.raise_for_status()
            
            data = response.json()
            
            # CMC wraps data in 'data' field
            if "data" not in data:
                logger.error(f"Unexpected CMC response structure: {data.keys()}")
                raise ValueError("Invalid CMC response format")
            
            return data
            
        except requests.RequestException as e:
            logger.error(f"CMC API request failed: {e}")
            raise
    
    def get_listings(
        self,
        start: int = 1,
        limit: int = 5000,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get cryptocurrency listings with market cap data.
        
        Args:
            start: Start rank (1-based)
            limit: Number of results (max 5000)
            use_cache: Use cached data if available (today)
            
        Returns:
            List of cryptocurrency dicts with keys:
            - id: CMC ID
            - symbol: Ticker symbol
            - name: Full name
            - slug: URL slug
            - cmc_rank: CMC rank
            - quote.USD.market_cap: Market cap in USD
            - quote.USD.price: Current price
            - circulating_supply: Circulating supply
            - total_supply: Total supply
            - max_supply: Max supply
        """
        cache_key = f"cmc_listings_start{start}_limit{limit}"
        
        if use_cache and cache_exists(cache_key):
            logger.info("Loading CMC listings from cache")
            cached = load_cache(cache_key)
            data = cached.get("data", []) if isinstance(cached, dict) else []

            # 🔹 Rohdaten-Snapshot auch bei Cache-Hit speichern
            if collect_raw_marketcap and data:
                try:
                    collect_raw_marketcap(data)
                except Exception as e:
                    logger.warning(f"Could not collect MarketCap snapshot: {e}")

            return data
        
        logger.info(f"Fetching CMC listings (start={start}, limit={limit})")
        
        params = {
            "start": start,
            "limit": min(limit, 5000),  # API max
            "convert": "USD",
            "sort": "market_cap",
            "sort_dir": "desc"
        }
        
        try:
            response = self._request("/v1/cryptocurrency/listings/latest", params)
            data = response.get("data", [])
            
            logger.info(f"Fetched {len(data)} listings from CMC")
            
            # Cache the full response
            save_cache(response, cache_key)

            # 🔹 Rohdaten-Snapshot über zentralen Collector speichern
            if collect_raw_marketcap and data:
                try:
                    collect_raw_marketcap(data)
                except Exception as e:
                    logger.warning(f"Could not collect MarketCap snapshot: {e}")
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to fetch CMC listings: {e}")
            return []
    
    def get_all_listings(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Get all available listings (up to 5000).
        
        Returns:
            List of all cryptocurrency dicts
        """
        return self.get_listings(start=1, limit=5000, use_cache=use_cache)
    
    def build_symbol_map(
        self,
        listings: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Build a symbol → data mapping for fast lookups.
        
        Args:
            listings: CMC listings (default: fetch all)
            
        Returns:
            Dict mapping symbol (uppercase) to full CMC data
            
        Note:
            If multiple coins share a symbol, only the highest-ranked is kept.
        """
        if listings is None:
            listings = self.get_all_listings()
        
        symbol_map = {}
        collisions = []
        
        for item in listings:
            symbol = item.get("symbol", "").upper()
            
            if not symbol:
                continue
            
            # Collision detection
            if symbol in symbol_map:
                # Keep higher-ranked (lower cmc_rank number)
                existing_rank = symbol_map[symbol].get("cmc_rank", float('inf'))
                new_rank = item.get("cmc_rank", float('inf'))
                
                if new_rank < existing_rank:
                    collisions.append({
                        "symbol": symbol,
                        "replaced": symbol_map[symbol].get("name"),
                        "with": item.get("name")
                    })
                    symbol_map[symbol] = item
                else:
                    collisions.append({
                        "symbol": symbol,
                        "kept": symbol_map[symbol].get("name"),
                        "ignored": item.get("name")
                    })
            else:
                symbol_map[symbol] = item
        
        if collisions:
            logger.warning(f"Found {len(collisions)} symbol collisions (kept higher-ranked)")
            logger.debug(f"Collisions: {collisions[:10]}")  # Show first 10
        
        logger.info(f"Built symbol map with {len(symbol_map)} unique symbols")
        return symbol_map
    
    def get_market_cap_for_symbol(
        self,
        symbol: str,
        symbol_map: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> Optional[float]:
        """
        Get market cap for a specific symbol.
        
        Args:
            symbol: Ticker symbol (e.g., 'BTC')
            symbol_map: Pre-built symbol map (default: build from listings)
            
        Returns:
            Market cap in USD or None if not found
        """
        if symbol_map is None:
            symbol_map = self.build_symbol_map()
        
        symbol = symbol.upper()
        data = symbol_map.get(symbol)
        
        if not data:
            return None
        
        try:
            return data["quote"]["USD"]["market_cap"]
        except (KeyError, TypeError):
            return None
