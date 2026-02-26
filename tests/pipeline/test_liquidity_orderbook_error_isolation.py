from scanner.pipeline.liquidity import apply_liquidity_metrics_to_shortlist, fetch_orderbooks_for_top_k


class _DummyMexcWithOneFailure:
    def __init__(self, failing_symbol):
        self.calls = []
        self.failing_symbol = failing_symbol

    def get_orderbook(self, symbol, limit=200):
        self.calls.append((symbol, limit))
        if symbol == self.failing_symbol:
            raise RuntimeError("simulated orderbook failure")
        return {"symbol": symbol, "bids": [["99", "10"]], "asks": [["101", "10"]]}


def test_orderbook_exception_isolated_per_symbol():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 40.0, "quote_volume_24h": 100},
        {"symbol": "C", "proxy_liquidity_score": 50.0, "quote_volume_24h": 100},
        {"symbol": "D", "proxy_liquidity_score": 60.0, "quote_volume_24h": 100},
    ]
    shortlist = [{"symbol": "C"}, {"symbol": "D"}]
    cfg = {"liquidity": {"orderbook_top_k": 2}}
    client = _DummyMexcWithOneFailure(failing_symbol="D")

    payload = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 2
    assert set(payload.keys()) == {"C"}

    out = apply_liquidity_metrics_to_shortlist(shortlist, payload, cfg)
    by_symbol = {r["symbol"]: r for r in out}

    assert by_symbol["C"]["liquidity_grade"] in {"A", "B", "C", "D"}
    assert by_symbol["D"]["spread_bps"] is None
    assert by_symbol["D"]["slippage_bps"] is None
    assert by_symbol["D"]["liquidity_grade"] is None
    assert by_symbol["D"]["liquidity_insufficient"] is None
