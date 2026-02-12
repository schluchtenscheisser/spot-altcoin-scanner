import json
from pathlib import Path

from scanner.clients.mapping import MappingResult
from scanner.config import ScannerConfig
from scanner.pipeline.runtime_market_meta import RuntimeMarketMetaExporter


def test_runtime_market_meta_export_writes_expected_schema(tmp_path: Path) -> None:
    config = ScannerConfig(
        raw={
            "snapshots": {"runtime_dir": str(tmp_path)},
            "universe_filters": {
                "market_cap": {"min_usd": 100_000_000, "max_usd": 3_000_000_000},
                "volume": {"min_quote_volume_24h": 1_000_000},
            },
        }
    )

    mapping_results = {
        "EXMUSDT": MappingResult(
            mexc_symbol="EXMUSDT",
            cmc_data={
                "id": 12345,
                "name": "Example Token",
                "symbol": "EXM",
                "slug": "example-token",
                "category": "token",
                "tags": ["defi"],
                "platform": {
                    "name": "Ethereum",
                    "symbol": "ETH",
                    "token_address": "0x1234",
                },
                "circulating_supply": 50_000_000,
                "total_supply": 100_000_000,
                "max_supply": 100_000_000,
                "cmc_rank": 180,
                "quote": {
                    "USD": {
                        "market_cap": 450_000_000,
                        "fully_diluted_market_cap": 900_000_000,
                    }
                },
            },
            confidence="high",
            method="symbol_exact_match",
        )
    }

    exchange_info = {
        "symbols": [
            {
                "symbol": "EXMUSDT",
                "baseAsset": "EXM",
                "quoteAsset": "USDT",
                "status": "1",
                "quotePrecision": 6,
                "baseAssetPrecision": 1,
                "filters": [
                    {"filterType": "PRICE_FILTER", "tickSize": "0.000001"},
                    {
                        "filterType": "LOT_SIZE",
                        "stepSize": "0.1",
                        "minQty": "1",
                        "maxQty": "100000",
                    },
                    {"filterType": "MIN_NOTIONAL", "minNotional": "5"},
                ],
            }
        ]
    }

    ticker_map = {
        "EXMUSDT": {
            "lastPrice": "0.012345",
            "highPrice": "0.0132",
            "lowPrice": "0.0111",
            "quoteVolume": "12500000",
            "priceChangePercent": "6.8",
            "bidPrice": "0.012344",
            "askPrice": "0.012346",
            "count": 12000,
            "volume": "1000000000",
        }
    }

    exporter = RuntimeMarketMetaExporter(config)
    output_path = exporter.export(
        run_date="2026-02-11",
        asof_iso="2026-02-11T08:10:00Z",
        run_id="1739261400000",
        filtered_symbols=["EXMUSDT"],
        mapping_results=mapping_results,
        exchange_info=exchange_info,
        ticker_map=ticker_map,
        features={"EXMUSDT": {"meta": {}}},
        ohlcv_data={"EXMUSDT": {"1d": []}},
        exchange_info_ts_utc="2026-02-11T08:01:00Z",
        tickers_24h_ts_utc="2026-02-11T08:02:00Z",
        listings_ts_utc="2026-02-11T08:03:00Z",
    )

    assert output_path.name == "runtime_market_meta_2026-02-11.json"
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert payload["meta"]["run_id"] == "1739261400000"
    assert payload["universe"]["count"] == 1
    assert payload["universe"]["symbols"] == ["EXMUSDT"]

    coin = payload["coins"]["EXMUSDT"]
    assert coin["identity"]["cmc_id"] == 12345
    assert coin["identity"]["fdv_to_mcap"] == 2.0
    assert coin["mexc"]["symbol_info"]["tick_size"] == "0.000001"
    assert coin["mexc"]["symbol_info"]["min_notional"] == 5.0
    assert coin["quality"]["has_scanner_features"] is True
    assert coin["quality"]["has_ohlcv"] is True
