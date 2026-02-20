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
    assert ("AUSDT", "1d", 121) in mexc.calls
    assert ("AUSDT", "4h", 60) in mexc.calls


def test_scorer_weights_are_config_driven():
    b = BreakoutScorer({"scoring": {"breakout": {"weights": {"breakout": 1, "volume": 0, "trend": 0, "momentum": 0}}}})
    p = PullbackScorer({"scoring": {"pullback": {"weights": {"trend": 1, "pullback": 0, "rebound": 0, "volume": 0}}}})
    r = ReversalScorer({"scoring": {"reversal": {"weights": {"drawdown": 1, "base": 0, "reclaim": 0, "volume": 0}}}})
    assert b.weights["breakout"] == 1.0
    assert p.weights["trend"] == 1.0
    assert r.weights["drawdown"] == 1.0


def test_legacy_exclusion_patterns_empty_list_disables_exclusions() -> None:
    cfg = {
        "filters": {"exclusion_patterns": []},
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
        {"symbol": "AAAUSDT", "base": "AAA", "quote_volume_24h": 2_000_000, "market_cap": 300_000_000},
        {"symbol": "BBBUSDT", "base": "BBBUSD", "quote_volume_24h": 2_000_000, "market_cap": 300_000_000},
    ])
    assert [x["symbol"] for x in out] == ["AAAUSDT", "BBBUSDT"]


def test_legacy_exclusion_patterns_override_new_exclusions_when_present() -> None:
    cfg = {
        "filters": {"exclusion_patterns": ["WRAP"]},
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
        {"symbol": "AAAUSDT", "base": "AAAUSD", "quote_volume_24h": 2_000_000, "market_cap": 300_000_000},
        {"symbol": "WRAPUSDT", "base": "WRAPCOIN", "quote_volume_24h": 2_000_000, "market_cap": 300_000_000},
    ])
    # Only legacy pattern applies; stablecoin exclusion from new config is ignored.
    assert [x["symbol"] for x in out] == ["AAAUSDT"]


def test_ohlcv_lookback_override_takes_precedence_over_general_defaults() -> None:
    mexc = _DummyMexc({})
    fetcher = OHLCVFetcher(
        mexc,
        {
            "general": {"lookback_days_1d": 120, "lookback_days_4h": 10},
            "ohlcv": {"lookback": {"1d": 77, "4h": 88}},
        },
    )
    assert fetcher.lookback["1d"] == 78
    assert fetcher.lookback["4h"] == 88


def test_ohlcv_lookback_partial_override_keeps_general_for_missing_timeframe() -> None:
    mexc = _DummyMexc({})
    fetcher = OHLCVFetcher(
        mexc,
        {
            "general": {"lookback_days_1d": 90, "lookback_days_4h": 12},
            "ohlcv": {"lookback": {"1d": 150}},
        },
    )
    assert fetcher.lookback["1d"] == 151
    assert fetcher.lookback["4h"] == 72  # 12 days * 6 bars/day


def test_ohlcv_lookback_falls_back_to_general_when_override_absent() -> None:
    mexc = _DummyMexc({})
    fetcher = OHLCVFetcher(
        mexc,
        {"general": {"lookback_days_1d": 60, "lookback_days_4h": 5}},
    )
    assert fetcher.lookback["1d"] == 61
    assert fetcher.lookback["4h"] == 30


def test_include_only_usdt_pairs_true_excludes_non_usdt_pairs() -> None:
    cfg = {
        "universe_filters": {
            "include_only_usdt_pairs": True,
            "market_cap": {"min_usd": 1, "max_usd": 10_000_000_000},
            "volume": {"min_quote_volume_24h": 0},
        },
        "filters": {"exclusion_patterns": []},
    }
    f = UniverseFilters(cfg)
    out = f.apply_all([
        {"symbol": "AAAUSDT", "base": "AAA", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "AAAUSDC", "base": "AAA", "quote": "USDC", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "AAABTC", "base": "AAA", "quote": "BTC", "quote_volume_24h": 1, "market_cap": 100},
    ])
    assert [x["symbol"] for x in out] == ["AAAUSDT"]


def test_include_only_usdt_pairs_false_keeps_only_stablecoin_quotes() -> None:
    cfg = {
        "universe_filters": {
            "include_only_usdt_pairs": False,
            "market_cap": {"min_usd": 1, "max_usd": 10_000_000_000},
            "volume": {"min_quote_volume_24h": 0},
        },
        "filters": {"exclusion_patterns": []},
    }
    f = UniverseFilters(cfg)
    out = f.apply_all([
        {"symbol": "AAAUSDT", "base": "AAA", "quote": "USDT", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "AAAUSDC", "base": "AAA", "quote": "USDC", "quote_volume_24h": 1, "market_cap": 100},
        {"symbol": "AAABTC", "base": "AAA", "quote": "BTC", "quote_volume_24h": 1, "market_cap": 100},
    ])
    assert [x["symbol"] for x in out] == ["AAAUSDT", "AAAUSDC"]


def test_shortlist_selector_adds_proxy_liquidity_score_percent_rank():
    selector = ShortlistSelector({"general": {"shortlist_size": 3}})
    out = selector.select([
        {"symbol": "A", "quote_volume_24h": 100},
        {"symbol": "B", "quote_volume_24h": 10_000},
        {"symbol": "C", "quote_volume_24h": 1_000_000},
    ])

    assert [x["symbol"] for x in out] == ["C", "B", "A"]
    assert out[0]["proxy_liquidity_score"] == 100.0
    assert out[-1]["proxy_liquidity_score"] == 0.0


def test_shortlist_selector_proxy_liquidity_score_handles_ties_with_average_rank():
    selector = ShortlistSelector({"general": {"shortlist_size": 3}})
    out = selector.select([
        {"symbol": "A", "quote_volume_24h": 100},
        {"symbol": "B", "quote_volume_24h": 100},
        {"symbol": "C", "quote_volume_24h": 10_000},
    ])

    by_symbol = {x["symbol"]: x["proxy_liquidity_score"] for x in out}
    assert by_symbol["C"] == 100.0
    assert by_symbol["A"] == 25.0
    assert by_symbol["B"] == 25.0


def test_proxy_liquidity_population_uses_full_filtered_universe_not_shortlist():
    selector = ShortlistSelector({"general": {"shortlist_size": 1}})
    out = selector.select([
        {"symbol": "A", "quote_volume_24h": 100},
        {"symbol": "B", "quote_volume_24h": 10_000},
        {"symbol": "C", "quote_volume_24h": 1_000_000},
    ])

    assert len(out) == 1
    assert out[0]["symbol"] == "C"
    assert out[0]["proxy_liquidity_population_n"] == 3
