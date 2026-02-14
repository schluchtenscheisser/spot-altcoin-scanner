from scanner.pipeline.filters import UniverseFilters
from scanner.pipeline.shortlist import ShortlistSelector
from scanner.pipeline.ohlcv import OHLCVFetcher
from scanner.pipeline.scoring.breakout import BreakoutScorer
from scanner.pipeline.scoring.pullback import PullbackScorer
from scanner.pipeline.scoring.reversal import ReversalScorer


class _DummyMexc:
    def __init__(self, klines):
        self.klines = klines
        self.calls = []

    def get_klines(self, symbol, tf, limit=0):
        self.calls.append((symbol, tf, limit))
        return self.klines.get((symbol, tf), [])


def test_universe_filters_reads_universe_filters_and_exclusions():
    cfg = {
        "universe_filters": {
            "market_cap": {"min_usd": 200, "max_usd": 400},
            "volume": {"min_quote_volume_24h": 50},
        },
        "exclusions": {
            "exclude_stablecoins": True,
            "stablecoin_patterns": ["USD"],
            "exclude_wrapped_tokens": False,
            "exclude_leveraged_tokens": False,
            "exclude_synthetic_derivatives": False,
        },
    }
    f = UniverseFilters(cfg)
    out = f.apply_all([
        {"symbol": "AAAUSDT", "base": "AAA", "quote_volume_24h": 100, "market_cap": 300},
        {"symbol": "BBBUSDT", "base": "BBBUSD", "quote_volume_24h": 100, "market_cap": 300},
    ])
    assert [x["symbol"] for x in out] == ["AAAUSDT"]


def test_shortlist_selector_prefers_general_shortlist_size():
    selector = ShortlistSelector({"general": {"shortlist_size": 1}, "shortlist": {"max_size": 2}})
    out = selector.select([
        {"symbol": "A", "quote_volume_24h": 10},
        {"symbol": "B", "quote_volume_24h": 20},
    ])
    assert len(out) == 1
    assert out[0]["symbol"] == "B"


def test_ohlcv_fetcher_uses_general_lookback_and_history_filter():
    klines_1d = [[0, 1, 1, 1, 1, 1, 0, 0]] * 60
    klines_4h = [[0, 1, 1, 1, 1, 1, 0, 0]] * 59
    mexc = _DummyMexc({("AUSDT", "1d"): klines_1d, ("AUSDT", "4h"): klines_4h})
    fetcher = OHLCVFetcher(mexc, {
        "general": {"lookback_days_1d": 120, "lookback_days_4h": 10},
        "universe_filters": {"history": {"min_history_days_1d": 60}},
        "ohlcv": {"min_candles": {"1d": 50, "4h": 60}},
    })
    out = fetcher.fetch_all([{"symbol": "AUSDT"}])
    assert out == {}
    assert ("AUSDT", "4h", 60) in mexc.calls


def test_scorer_weights_are_config_driven():
    b = BreakoutScorer({"scoring": {"breakout": {"weights": {"breakout": 1, "volume": 0, "trend": 0, "momentum": 0}}}})
    p = PullbackScorer({"scoring": {"pullback": {"weights": {"trend": 1, "pullback": 0, "rebound": 0, "volume": 0}}}})
    r = ReversalScorer({"scoring": {"reversal": {"weights": {"drawdown": 1, "base": 0, "reclaim": 0, "volume": 0}}}})
    assert b.weights["breakout"] == 1.0
    assert p.weights["trend"] == 1.0
    assert r.weights["drawdown"] == 1.0
