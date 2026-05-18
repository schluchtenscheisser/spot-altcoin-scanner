"""Small public Binance Spot client for Pre-1 OHLCV history fetches."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests


BASE_URL = "https://api.binance.com"


@dataclass
class BinanceSpotClient:
    base_url: str = BASE_URL
    timeout: int = 30

    def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        response = requests.get(f"{self.base_url}{path}", params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_spot_usdt_symbols(self) -> list[str]:
        data = self._get("/api/v3/exchangeInfo")
        symbols: list[str] = []
        for entry in data.get("symbols", []):
            permissions = set(entry.get("permissions") or [])
            is_spot = entry.get("isSpotTradingAllowed") is True or "SPOT" in permissions
            if entry.get("status") == "TRADING" and entry.get("quoteAsset") == "USDT" and is_spot:
                symbols.append(str(entry["symbol"]).upper())
        return sorted(set(symbols))

    def get_klines(
        self,
        symbol: str,
        interval: str,
        *,
        start_time_ms: int | None = None,
        end_time_ms: int | None = None,
        limit: int = 1000,
    ) -> list[list[Any]]:
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time_ms is not None:
            params["startTime"] = start_time_ms
        if end_time_ms is not None:
            params["endTime"] = end_time_ms
        return self._get("/api/v3/klines", params=params)
