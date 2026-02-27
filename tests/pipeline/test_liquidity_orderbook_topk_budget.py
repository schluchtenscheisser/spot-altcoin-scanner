from scanner.pipeline.liquidity import apply_liquidity_metrics_to_shortlist, fetch_orderbooks_for_top_k


class _DummyMexc:
    def __init__(self):
        self.calls = []

    def get_orderbook(self, symbol, limit=200):
        self.calls.append((symbol, limit))
        return {"symbol": symbol, "bids": [["99", "10"]], "asks": [["101", "10"]]}


def test_topk_budget_does_not_insert_none_orderbooks_and_does_not_crash():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 40.0, "quote_volume_24h": 100},
        {"symbol": "C", "proxy_liquidity_score": 50.0, "quote_volume_24h": 100},
        {"symbol": "D", "proxy_liquidity_score": 60.0, "quote_volume_24h": 100},
    ]
    shortlist = [{"symbol": "A"}, {"symbol": "D"}]
    cfg = {"liquidity": {"orderbook_top_k": 1}}
    client = _DummyMexc()

    payload = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 1
    assert set(payload.keys()) == {"D"}

    out = apply_liquidity_metrics_to_shortlist(shortlist, payload, cfg)
    by_symbol = {r["symbol"]: r for r in out}
    assert by_symbol["D"]["liquidity_grade"] in {"A", "B", "C", "D"}
    assert by_symbol["A"]["spread_bps"] is None
    assert by_symbol["A"]["slippage_bps"] is None
    assert by_symbol["A"]["liquidity_grade"] == "D"
    assert by_symbol["A"]["liquidity_insufficient"] is True
