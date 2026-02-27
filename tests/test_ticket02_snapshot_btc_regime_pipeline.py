from __future__ import annotations

from pathlib import Path

from scanner.config import ScannerConfig
import scanner.pipeline as pipeline


class _DummyMappingResult:
    mapped = True
    cmc_data = {"name": "AAA", "date_added": "2020-01-01T00:00:00Z"}

    def _get_market_cap(self):
        return 123456789


class _DummyMEXCClient:
    def get_exchange_info(self, use_cache=True):
        return {
            "symbols": [
                {
                    "symbol": "AAAUSDT",
                    "quoteAsset": "USDT",
                    "isSpotTradingAllowed": True,
                    "status": "1",
                }
            ]
        }

    def get_24h_tickers(self, use_cache=True):
        return [{"symbol": "AAAUSDT", "quoteVolume": "1000000", "lastPrice": "1.23"}]


class _DummyMarketCapClient:
    def __init__(self, api_key=""):
        self.api_key = api_key

    def get_listings(self, use_cache=True):
        return []

    def build_symbol_map(self, listings):
        return {"AAA": {}}


class _DummySymbolMapper:
    def __init__(self):
        self.stats = {"mapped": 1, "total": 1}

    def map_universe(self, universe, cmc_symbol_map):
        return {"AAAUSDT": _DummyMappingResult()}

    def map_symbol(self, symbol, cmc_symbol_map):
        return _DummyMappingResult()


class _DummyUniverseFilters:
    def __init__(self, raw):
        self.raw = raw

    def apply_all(self, symbols_with_data):
        return symbols_with_data


class _DummyShortlistSelector:
    def __init__(self, raw):
        self.raw = raw

    def select(self, filtered):
        return [
            {
                "symbol": "AAAUSDT",
                "market_cap": 123456789,
                "quote_volume_24h": 1000000,
                "proxy_liquidity_score": 10,
                "spread_bps": 5,
                "slippage_bps": 8,
                "liquidity_grade": "A",
                "liquidity_insufficient": False,
                "risk_flags": [],
                "soft_penalties": {},
            }
        ]


class _DummyOHLCVFetcher:
    def __init__(self, mexc, raw):
        self.mexc = mexc
        self.raw = raw
        self.lookback = {"1d": 120, "4h": 30}

    def fetch_all(self, shortlist):
        return {
            "AAAUSDT": {
                "1d": [[1700000000000, 1.0, 1.1, 0.9, 1.0, 1000]],
                "4h": [[1700000000000, 1.0, 1.1, 0.9, 1.0, 1000]],
            }
        }


class _DummyFeatureEngine:
    def __init__(self, config):
        self.config = config

    def compute_all(self, ohlcv_data, asof_ts_ms=None):
        return {
            "AAAUSDT": {
                "1d": {
                    "close": 1.0,
                    "ema_20": 0.9,
                    "ema_50": 0.8,
                },
                "4h": {"close": 1.0},
            }
        }

class _DummyReportGenerator:
    def __init__(self, raw):
        self.raw = raw

    def save_reports(self, *args, **kwargs):
        return {"markdown": "reports/a.md", "json": "reports/a.json"}


class _DummySnapshotManager:
    captured_metadata = None

    def __init__(self, raw):
        self.raw = raw

    def create_snapshot(self, **kwargs):
        _DummySnapshotManager.captured_metadata = kwargs["metadata"]
        return Path("snapshots/history/2026-02-27.json")


class _DummyRuntimeMetaExporter:
    def __init__(self, config):
        self.config = config

    def export(self, **kwargs):
        return Path("snapshots/runtime/runtime_market_meta_2026-02-27.json")


def test_run_pipeline_passes_btc_regime_into_snapshot_metadata(monkeypatch) -> None:
    btc_regime = {
        "state": "RISK_ON",
        "multiplier_risk_on": 1.0,
        "multiplier_risk_off": 0.85,
        "checks": {"close_gt_ema50": True, "ema20_gt_ema50": True},
    }

    monkeypatch.setattr(pipeline, "utc_now", lambda: __import__("datetime").datetime(2026, 2, 27))
    monkeypatch.setattr(pipeline, "timestamp_to_ms", lambda dt: 1772150400000)
    monkeypatch.setattr(pipeline, "MEXCClient", _DummyMEXCClient)
    monkeypatch.setattr(pipeline, "MarketCapClient", _DummyMarketCapClient)
    monkeypatch.setattr(pipeline, "SymbolMapper", _DummySymbolMapper)
    monkeypatch.setattr(pipeline, "UniverseFilters", _DummyUniverseFilters)
    monkeypatch.setattr(pipeline, "ShortlistSelector", _DummyShortlistSelector)
    monkeypatch.setattr(pipeline, "fetch_orderbooks_for_top_k", lambda *args, **kwargs: {})
    monkeypatch.setattr(pipeline, "apply_liquidity_metrics_to_shortlist", lambda shortlist, *_: shortlist)
    monkeypatch.setattr(pipeline, "OHLCVFetcher", _DummyOHLCVFetcher)
    monkeypatch.setattr(pipeline, "FeatureEngine", _DummyFeatureEngine)
    monkeypatch.setattr(pipeline, "compute_btc_regime", lambda *args, **kwargs: btc_regime)
    monkeypatch.setattr(pipeline, "compute_discovery_fields", lambda **kwargs: {"discovery": False})
    monkeypatch.setattr(pipeline, "score_reversals", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "score_breakout_trend_1_5d", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "score_pullbacks", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "compute_global_top20", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "ReportGenerator", _DummyReportGenerator)
    monkeypatch.setattr(pipeline, "SnapshotManager", _DummySnapshotManager)
    monkeypatch.setattr(pipeline, "RuntimeMarketMetaExporter", _DummyRuntimeMetaExporter)

    config = ScannerConfig(raw={"general": {"run_mode": "fast"}})

    pipeline.run_pipeline(config)

    assert _DummySnapshotManager.captured_metadata is not None
    assert _DummySnapshotManager.captured_metadata["btc_regime"] == btc_regime
    assert _DummySnapshotManager.captured_metadata["asof_ts_ms"] == 1772150400000
    assert _DummySnapshotManager.captured_metadata["asof_iso"] == "2026-02-27T00:00:00Z"
