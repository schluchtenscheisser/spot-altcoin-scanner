from scanner.pipeline.shortlist import ShortlistSelector


def _base_row(symbol: str, volume: float):
    return {
        "symbol": symbol,
        "base": symbol,
        "quote_volume_24h": volume,
        "market_cap": 500_000_000,
    }


def test_proxy_liquidity_score_is_input_order_independent():
    selector = ShortlistSelector({"general": {"shortlist_size": 100}})

    ordered = [
        _base_row("AAA", 100.0),
        _base_row("BBB", 500.0),
        _base_row("CCC", 500.0),
        _base_row("DDD", 1_500.0),
    ]
    permuted = [ordered[2], ordered[0], ordered[3], ordered[1]]

    ordered_out = selector._attach_proxy_liquidity_score(ordered)
    permuted_out = selector._attach_proxy_liquidity_score(permuted)

    ordered_scores = {row["symbol"]: row["proxy_liquidity_score"] for row in ordered_out}
    permuted_scores = {row["symbol"]: row["proxy_liquidity_score"] for row in permuted_out}

    assert ordered_scores == permuted_scores
    assert ordered_scores["BBB"] == ordered_scores["CCC"]
    assert ordered_scores["AAA"] < ordered_scores["BBB"] < ordered_scores["DDD"]
    assert all(0.0 <= score <= 100.0 for score in ordered_scores.values())
