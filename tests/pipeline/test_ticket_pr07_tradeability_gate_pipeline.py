from __future__ import annotations

from scanner.config import ScannerConfig
import scanner.pipeline as pipeline


class _DummyOHLCVFetcher:
    captured_symbols = None

    def __init__(self, mexc, raw):
        self.lookback = {"1d": 120, "4h": 30}

    def fetch_all(self, shortlist):
        _DummyOHLCVFetcher.captured_symbols = [row["symbol"] for row in shortlist]
        return {
            row["symbol"]: {
                "1d": [[1700000000000, 1.0, 1.1, 0.9, 1.0, 1000]],
                "4h": [[1700000000000, 1.0, 1.1, 0.9, 1.0, 1000]],
            }
            for row in shortlist
        }


class _DummyFeatureEngine:
    def __init__(self, config):
        self.config = config

    def compute_all(self, ohlcv_data, asof_ts_ms=None):
        return {symbol: {"1d": {}, "4h": {}} for symbol in ohlcv_data.keys()}


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


class _DummyMappingResult:
    mapped = True
    cmc_data = {"name": "AAA", "date_added": "2020-01-01T00:00:00Z"}

    def _get_market_cap(self):
        return 123456789


class _DummySymbolMapper:
    def __init__(self):
        self.stats = {"mapped": 1, "total": 1}

    def map_universe(self, universe, cmc_symbol_map):
        return {"AAAUSDT": _DummyMappingResult()}

    def map_symbol(self, symbol, cmc_symbol_map):
        return _DummyMappingResult()


class _PassThrough:
    def __init__(self, raw):
        self.raw = raw

    def apply_all(self, symbols_with_data):
        return symbols_with_data

    def select(self, filtered):
        return filtered


class _DummyReportGenerator:
    captured_args = None
    captured_kwargs = None

    def __init__(self, raw):
        self.raw = raw

    def save_reports(self, *args, **kwargs):
        _DummyReportGenerator.captured_args = args
        _DummyReportGenerator.captured_kwargs = kwargs
        return {"markdown": "reports/a.md", "json": "reports/a.json"}


class _DummySnapshotManager:
    def __init__(self, raw):
        self.raw = raw

    def create_snapshot(self, **kwargs):
        return "snapshots/history/2026-02-27.json"


class _DummyRuntimeMetaExporter:
    def __init__(self, config):
        self.config = config

    def export(self, **kwargs):
        return "snapshots/runtime/runtime_market_meta_2026-02-27.json"


def _patch_runtime(monkeypatch, shortlist_after_liquidity):
    monkeypatch.setattr(pipeline, "utc_now", lambda: __import__("datetime").datetime(2026, 2, 27))
    monkeypatch.setattr(pipeline, "timestamp_to_ms", lambda dt: 1772150400000)
    monkeypatch.setattr(pipeline, "MEXCClient", _DummyMEXCClient)
    monkeypatch.setattr(pipeline, "MarketCapClient", _DummyMarketCapClient)
    monkeypatch.setattr(pipeline, "SymbolMapper", _DummySymbolMapper)
    monkeypatch.setattr(pipeline, "UniverseFilters", _PassThrough)
    monkeypatch.setattr(pipeline, "ShortlistSelector", _PassThrough)
    monkeypatch.setattr(pipeline, "fetch_orderbooks_for_top_k", lambda *args, **kwargs: ({}, set()))
    monkeypatch.setattr(pipeline, "apply_liquidity_metrics_to_shortlist", lambda shortlist, *_, **__: shortlist_after_liquidity)
    monkeypatch.setattr(pipeline, "OHLCVFetcher", _DummyOHLCVFetcher)
    monkeypatch.setattr(pipeline, "FeatureEngine", _DummyFeatureEngine)
    monkeypatch.setattr(pipeline, "compute_btc_regime", lambda *args, **kwargs: {"state": "RISK_ON"})
    monkeypatch.setattr(pipeline, "compute_discovery_fields", lambda **kwargs: {"discovery": False})
    monkeypatch.setattr(pipeline, "score_reversals", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "score_breakout_trend_1_5d", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "score_pullbacks", lambda *args, **kwargs: [])
    monkeypatch.setattr(pipeline, "compute_global_top20", lambda *args, **kwargs: [{"symbol": "AAAUSDT", "score": 70}])
    monkeypatch.setattr(pipeline, "ReportGenerator", _DummyReportGenerator)
    monkeypatch.setattr(pipeline, "SnapshotManager", _DummySnapshotManager)
    monkeypatch.setattr(pipeline, "RuntimeMarketMetaExporter", _DummyRuntimeMetaExporter)


def test_tradeability_gate_only_passes_allowed_classes(monkeypatch):
    rows = [
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK"},
        {"symbol": "BBBUSDT", "tradeability_class": "TRANCHE_OK"},
        {"symbol": "CCCUSDT", "tradeability_class": "MARGINAL"},
        {"symbol": "DDDUSDT", "tradeability_class": "FAIL", "tradeability_reason_keys": ["slippage_20k_too_high"]},
        {"symbol": "EEEUSDT", "tradeability_class": "UNKNOWN", "tradeability_reason_keys": ["orderbook_not_in_budget"]},
    ]

    passed, stopped = pipeline._apply_tradeability_gate(rows)

    assert [row["symbol"] for row in passed] == ["AAAUSDT", "BBBUSDT", "CCCUSDT"]
    assert [row["symbol"] for row in stopped] == ["DDDUSDT", "EEEUSDT"]
    assert stopped[1]["tradeability_gate_stop_reason_keys"] == ["orderbook_not_in_budget"]


def test_run_pipeline_skips_ohlcv_for_fail_and_unknown(monkeypatch):
    shortlist_after_liquidity = [
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK"},
        {"symbol": "BBBUSDT", "tradeability_class": "TRANCHE_OK"},
        {"symbol": "CCCUSDT", "tradeability_class": "MARGINAL"},
        {"symbol": "DDDUSDT", "tradeability_class": "FAIL", "tradeability_reason_keys": ["slippage_20k_too_high"]},
        {"symbol": "EEEUSDT", "tradeability_class": "UNKNOWN", "tradeability_reason_keys": ["orderbook_data_missing"]},
    ]
    _patch_runtime(monkeypatch, shortlist_after_liquidity)

    config = ScannerConfig(raw={"general": {"run_mode": "fast"}})
    pipeline.run_pipeline(config)

    assert _DummyOHLCVFetcher.captured_symbols == ["AAAUSDT", "BBBUSDT", "CCCUSDT"]


def test_shadow_mode_legacy_only_disables_new_path_outputs(monkeypatch):
    shortlist_after_liquidity = [{"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK"}]
    _patch_runtime(monkeypatch, shortlist_after_liquidity)
    monkeypatch.setattr(pipeline, "apply_decision_layer", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not be called")))

    config = ScannerConfig(raw={"general": {"run_mode": "fast"}, "shadow": {"mode": "legacy_only"}})
    pipeline.run_pipeline(config)

    args = _DummyReportGenerator.captured_args
    kwargs = _DummyReportGenerator.captured_kwargs
    assert args[0] == []
    assert args[1] == []
    assert args[2] == []
    assert args[3] == []
    assert kwargs["metadata"]["pipeline_paths"] == {
        "shadow_mode": "legacy_only",
        "legacy_path_enabled": True,
        "new_path_enabled": False,
        "primary_path": "legacy",
        "primary_path_source": "derived",
    }


def test_shadow_mode_new_only_disables_legacy_setup_outputs(monkeypatch):
    shortlist_after_liquidity = [{"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK"}]
    _patch_runtime(monkeypatch, shortlist_after_liquidity)
    monkeypatch.setattr(pipeline, "apply_decision_layer", lambda rows, *_args, **_kwargs: rows)

    config = ScannerConfig(raw={"general": {"run_mode": "fast"}, "shadow": {"mode": "new_only"}})
    pipeline.run_pipeline(config)

    args = _DummyReportGenerator.captured_args
    kwargs = _DummyReportGenerator.captured_kwargs
    assert args[0] == []
    assert args[1] == []
    assert args[2] == []
    assert args[3] != []
    assert kwargs["metadata"]["pipeline_paths"] == {
        "shadow_mode": "new_only",
        "legacy_path_enabled": False,
        "new_path_enabled": True,
        "primary_path": "new",
        "primary_path_source": "derived",
    }
