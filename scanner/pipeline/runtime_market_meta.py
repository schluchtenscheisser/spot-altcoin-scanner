"""Runtime market metadata export for each pipeline run."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..clients.mapping import MappingResult
from ..config import ScannerConfig
from ..utils.io_utils import save_json
from ..utils.time_utils import utc_now

logger = logging.getLogger(__name__)


class RuntimeMarketMetaExporter:
    """Builds and writes runtime market metadata export JSON."""

    def __init__(self, config: ScannerConfig | Dict[str, Any]):
        if hasattr(config, "raw"):
            self.config = config
            snapshots_config = config.raw.get("snapshots", {})
        else:
            self.config = ScannerConfig(raw=config)
            snapshots_config = config.get("snapshots", {})

        self.runtime_dir = Path(snapshots_config.get("runtime_dir", "snapshots/runtime"))
        self.runtime_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _to_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _build_exchange_symbol_map(exchange_info: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        return {
            symbol_info.get("symbol"): symbol_info
            for symbol_info in exchange_info.get("symbols", [])
            if symbol_info.get("symbol")
        }

    @staticmethod
    def _extract_filter_value(symbol_info: Dict[str, Any], filter_type: str, field: str) -> Any:
        for item in symbol_info.get("filters", []):
            if item.get("filterType") == filter_type:
                return item.get(field)
        return None

    def _build_identity(self, mapping: MappingResult) -> Dict[str, Any]:
        cmc_data = mapping.cmc_data or {}
        quote_usd = cmc_data.get("quote", {}).get("USD", {})

        market_cap = self._to_float(quote_usd.get("market_cap"))
        fdv = self._to_float(quote_usd.get("fully_diluted_market_cap"))

        platform = cmc_data.get("platform")
        platform_obj = None
        if isinstance(platform, dict):
            token_address = platform.get("token_address")
            platform_obj = {
                "name": platform.get("name"),
                "symbol": platform.get("symbol"),
                "token_address": token_address,
            }
        else:
            token_address = None

        fdv_to_mcap = None
        if fdv is not None and market_cap not in (None, 0):
            fdv_to_mcap = fdv / market_cap

        return {
            "cmc_id": cmc_data.get("id"),
            "name": cmc_data.get("name"),
            "symbol": cmc_data.get("symbol"),
            "slug": cmc_data.get("slug"),
            "category": cmc_data.get("category"),
            "tags": cmc_data.get("tags"),
            "platform": platform_obj,
            "is_token": bool(token_address),
            "market_cap_usd": market_cap,
            "circulating_supply": self._to_float(cmc_data.get("circulating_supply")),
            "total_supply": self._to_float(cmc_data.get("total_supply")),
            "max_supply": self._to_float(cmc_data.get("max_supply")),
            "fdv_usd": fdv,
            "fdv_to_mcap": fdv_to_mcap,
            "rank": self._to_int(cmc_data.get("cmc_rank")),
        }

    def _build_symbol_info(self, symbol: str, exchange_symbol: Dict[str, Any]) -> Dict[str, Any]:
        tick_size = self._extract_filter_value(exchange_symbol, "PRICE_FILTER", "tickSize")
        step_size = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "stepSize")
        min_qty = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "minQty")
        max_qty = self._extract_filter_value(exchange_symbol, "LOT_SIZE", "maxQty")

        min_notional = self._extract_filter_value(exchange_symbol, "MIN_NOTIONAL", "minNotional")
        max_notional = self._extract_filter_value(exchange_symbol, "NOTIONAL", "maxNotional")


        return {
            "mexc_symbol": symbol,
            "base_asset": exchange_symbol.get("baseAsset"),
            "quote_asset": exchange_symbol.get("quoteAsset"),
            "status": exchange_symbol.get("status"),
            "price_precision": self._to_int(exchange_symbol.get("quotePrecision") or exchange_symbol.get("priceScale")),
            "quantity_precision": self._to_int(exchange_symbol.get("baseAssetPrecision") or exchange_symbol.get("quantityScale")),
            "tick_size": tick_size,
            "step_size": step_size,
            "min_qty": self._to_float(min_qty),
            "max_qty": self._to_float(max_qty),
            "min_notional": self._to_float(min_notional),
            "max_notional": self._to_float(max_notional),
        }

    def _build_ticker(self, ticker: Dict[str, Any]) -> Dict[str, Any]:
        bid = self._to_float(ticker.get("bidPrice"))
        ask = self._to_float(ticker.get("askPrice"))
        mid = None
        spread_pct = None

        if bid is not None and ask is not None:
            mid = (bid + ask) / 2
            if mid != 0:
                spread_pct = ((ask - bid) / mid) * 100

        return {
            "last_price": self._to_float(ticker.get("lastPrice")),
            "high_24h": self._to_float(ticker.get("highPrice")),
            "low_24h": self._to_float(ticker.get("lowPrice")),
            "quote_volume_24h": self._to_float(ticker.get("quoteVolume")),
            "price_change_pct_24h": self._to_float(ticker.get("priceChangePercent")),
            "bid_price": bid,
            "ask_price": ask,
            "spread_pct": spread_pct,
            "mid_price": mid,
            "trades_24h": self._to_int(ticker.get("count")),
            "base_volume_24h": self._to_float(ticker.get("volume")),
        }

    def _build_quality(
        self,
        symbol: str,
        identity: Dict[str, Any],
        symbol_info: Dict[str, Any],
        has_scanner_features: bool,
        has_ohlcv: bool,
    ) -> Dict[str, Any]:
        missing_fields: List[str] = []

        if symbol_info.get("tick_size") in (None, ""):
            missing_fields.append("tick_size")
        if symbol_info.get("min_notional") is None:
            missing_fields.append("min_notional")
        if identity.get("platform") and not identity["platform"].get("token_address"):
            missing_fields.append("token_address")

        return {
            "has_scanner_features": has_scanner_features,
            "has_ohlcv": has_ohlcv,
            "missing_fields": missing_fields,
            "notes": None,
        }

    def export(
        self,
        run_date: str,
        asof_iso: str,
        run_id: str,
        filtered_symbols: List[str],
        mapping_results: Dict[str, MappingResult],
        exchange_info: Dict[str, Any],
        ticker_map: Dict[str, Dict[str, Any]],
        features: Dict[str, Dict[str, Any]],
        ohlcv_data: Dict[str, Dict[str, Any]],
        exchange_info_ts_utc: str,
        tickers_24h_ts_utc: str,
        listings_ts_utc: str,
    ) -> Path:
        """Create and save runtime market metadata export."""
        exchange_symbol_map = self._build_exchange_symbol_map(exchange_info)

        coins: Dict[str, Dict[str, Any]] = {}
        symbols = sorted(filtered_symbols)

        for symbol in symbols:
            mapping = mapping_results.get(symbol)
            if not mapping or not mapping.mapped:
                continue

            exchange_symbol = exchange_symbol_map.get(symbol, {})
            ticker = ticker_map.get(symbol, {})

            identity = self._build_identity(mapping)
            symbol_info = self._build_symbol_info(symbol, exchange_symbol)
            ticker_24h = self._build_ticker(ticker)

            quality = self._build_quality(
                symbol=symbol,
                identity=identity,
                symbol_info=symbol_info,
                has_scanner_features=symbol in features,
                has_ohlcv=symbol in ohlcv_data,
            )

            coins[symbol] = {
                "identity": identity,
                "mexc": {
                    "symbol_info": symbol_info,
                    "ticker_24h": ticker_24h,
                },
                "quality": quality,
            }

        payload = {
            "meta": {
                "run_id": run_id,
                "asof_utc": asof_iso,
                "generated_at_utc": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "mexc": {
                    "api_base": "https://api.mexc.com",
                    "exchange_info_ts_utc": exchange_info_ts_utc,
                    "tickers_24h_ts_utc": tickers_24h_ts_utc,
                },
                "cmc": {
                    "listings_ts_utc": listings_ts_utc,
                    "source": "CoinMarketCap",
                },
                "config": {
                    "mcap_min_usd": self.config.market_cap_min,
                    "mcap_max_usd": self.config.market_cap_max,
                    "min_quote_volume_24h_usdt": self.config.min_quote_volume_24h,
                },
            },
            "universe": {
                "count": len(coins),
                "symbols": list(coins.keys()),
            },
            "coins": coins,
        }

        output_path = self.runtime_dir / f"runtime_market_meta_{run_date}.json"
        save_json(payload, output_path)

        logger.info("Runtime market meta export saved: %s", output_path)
        logger.info("Runtime market meta universe count: %s", payload["universe"]["count"])

        return output_path
