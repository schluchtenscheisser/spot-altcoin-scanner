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

    payload, selected_symbols = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 2
    assert set(payload.keys()) == {"C"}

    out = apply_liquidity_metrics_to_shortlist(shortlist, payload, cfg, selected_symbols=selected_symbols)
    by_symbol = {r["symbol"]: r for r in out}

    assert by_symbol["C"]["liquidity_grade"] in {"A", "B", "C", "D"}
    assert by_symbol["D"]["spread_bps"] is None
    assert by_symbol["D"]["slippage_bps"] is None
    assert by_symbol["D"]["liquidity_grade"] == "D"
    assert by_symbol["D"]["liquidity_insufficient"] is True


class _DummyMexcWithMalformedPayloads:
    def __init__(self):
        self.calls = []

    def get_orderbook(self, symbol, limit=200):
        self.calls.append((symbol, limit))
        if symbol == "A":
            return ["not", "a", "dict"]
        if symbol == "B":
            return {"bids": [["99", "10"]]}
        if symbol == "C":
            return {"asks": [["101", "10"]]}
        return {"bids": [["99", "10"]], "asks": [["101", "10"]]}


def test_malformed_payloads_are_ignored_and_only_valid_payloads_are_kept():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 40.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 30.0, "quote_volume_24h": 100},
        {"symbol": "C", "proxy_liquidity_score": 20.0, "quote_volume_24h": 100},
        {"symbol": "D", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
    ]
    shortlist = [{"symbol": "A"}, {"symbol": "B"}, {"symbol": "C"}, {"symbol": "D"}]
    cfg = {"liquidity": {"orderbook_top_k": 4}}
    client = _DummyMexcWithMalformedPayloads()

    payload, selected_symbols = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 4
    assert set(payload.keys()) == {"D"}

    out = apply_liquidity_metrics_to_shortlist(shortlist, payload, cfg, selected_symbols=selected_symbols)
    by_symbol = {r["symbol"]: r for r in out}
    for symbol in ["A", "B", "C"]:
        assert by_symbol[symbol]["spread_bps"] is None
        assert by_symbol[symbol]["slippage_bps"] is None
        assert by_symbol[symbol]["liquidity_grade"] == "D"
        assert by_symbol[symbol]["liquidity_insufficient"] is True
