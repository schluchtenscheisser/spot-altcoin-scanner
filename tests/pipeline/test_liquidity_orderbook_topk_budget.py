from scanner.pipeline.liquidity import apply_liquidity_metrics_to_shortlist, fetch_orderbooks_for_top_k


class _DummyMexc:
    def __init__(self):
        self.calls = []

    def get_orderbook(self, symbol, limit=200):
        self.calls.append((symbol, limit))
        return {"symbol": symbol, "bids": [["99", "10"]], "asks": [["101", "10"]]}


def test_topk_budget_leaves_non_fetched_symbols_ungraded():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 40.0, "quote_volume_24h": 100},
        {"symbol": "C", "proxy_liquidity_score": 50.0, "quote_volume_24h": 100},
        {"symbol": "D", "proxy_liquidity_score": 60.0, "quote_volume_24h": 100},
        {"symbol": "E", "proxy_liquidity_score": 70.0, "quote_volume_24h": 100},
    ]
    shortlist = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}, {"symbol": "D"}, {"symbol": "E"}]
    cfg = {"liquidity": {"orderbook_top_k": 2}}
    client = _DummyMexc()

    payload, selected_symbols = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 2
    assert selected_symbols == {"D", "E"}
    assert set(payload.keys()) == {"D", "E"}

    out = apply_liquidity_metrics_to_shortlist(shortlist, payload, cfg, selected_symbols=selected_symbols)
    by_symbol = {r["symbol"]: r for r in out}

    assert by_symbol["D"]["liquidity_grade"] in {"A", "B", "C", "D"}
    assert by_symbol["E"]["liquidity_grade"] in {"A", "B", "C", "D"}

    for symbol in ["A", "B", "C"]:
        assert by_symbol[symbol]["spread_bps"] is None
        assert by_symbol[symbol]["slippage_bps"] is None
        assert by_symbol[symbol]["liquidity_grade"] is None
        assert by_symbol[symbol]["liquidity_insufficient"] is None
