import pytest

from scanner.pipeline.shortlist import ShortlistSelector


def _row(symbol: str, volume: float, market_cap: float, **extra):
    row = {
        "symbol": symbol,
        "base": symbol,
        "quote_volume_24h": volume,
        "market_cap": market_cap,
    }
    row.update(extra)
    return row


def test_shortlist_size_defaults_to_200_from_central_budget_defaults():
    selector = ShortlistSelector({})
    assert selector.max_size == 200


def test_shortlist_size_zero_raises_clear_error():
    with pytest.raises(ValueError, match="budget.shortlist_size"):
        ShortlistSelector({"budget": {"shortlist_size": 0}})


def test_shortlist_applies_pre_shortlist_market_cap_floor_before_ranking():
    selector = ShortlistSelector({
        "budget": {
            "shortlist_size": 5,
            "pre_shortlist_market_cap_floor_usd": 25_000_000,
        }
    })

    out = selector.select([
        _row("LOW", volume=10_000_000, market_cap=10_000_000),
        _row("HIGH", volume=100, market_cap=30_000_000),
    ])

    assert [row["symbol"] for row in out] == ["HIGH"]


def test_shortlist_cap_is_strict_and_keeps_all_when_under_cap():
    selector = ShortlistSelector({"budget": {"shortlist_size": 2, "pre_shortlist_market_cap_floor_usd": 0}})
    rows = [
        _row("A", 10, 30_000_000),
        _row("B", 20, 30_000_000),
        _row("C", 30, 30_000_000),
    ]
    out = selector.select(rows)
    assert [x["symbol"] for x in out] == ["C", "B"]

    selector_all = ShortlistSelector({"budget": {"shortlist_size": 10, "pre_shortlist_market_cap_floor_usd": 0}})
    out_all = selector_all.select(rows)
    assert [x["symbol"] for x in out_all] == ["C", "B", "A"]


def test_same_score_and_volume_uses_explicit_symbol_tie_breaker():
    selector = ShortlistSelector({"budget": {"shortlist_size": 10, "pre_shortlist_market_cap_floor_usd": 0}})
    rows = [
        _row("CCC", 1000, 30_000_000),
        _row("AAA", 1000, 30_000_000),
        _row("BBB", 1000, 30_000_000),
    ]

    out = selector.select(rows)
    assert [x["symbol"] for x in out] == ["AAA", "BBB", "CCC"]


def test_irrelevant_orderbook_or_tradeability_fields_do_not_affect_shortlist_order():
    selector = ShortlistSelector({"budget": {"shortlist_size": 2, "pre_shortlist_market_cap_floor_usd": 0}})
    out = selector.select([
        _row("VOL_LOW", 100, 30_000_000, slippage_bps=0.1, tradeability_class="DIRECT_OK"),
        _row("VOL_HIGH", 1_000_000, 30_000_000, slippage_bps=999, tradeability_class="FAIL"),
    ])

    assert [x["symbol"] for x in out] == ["VOL_HIGH", "VOL_LOW"]


def test_coin_above_legacy_market_cap_max_can_be_shortlisted_when_above_floor():
    selector = ShortlistSelector({"budget": {"shortlist_size": 1, "pre_shortlist_market_cap_floor_usd": 25_000_000}})
    out = selector.select([
        _row("MEGA", 1_000_000, 100_000_000_000),
        _row("MID", 10_000, 30_000_000),
    ])
    assert out[0]["symbol"] == "MEGA"
