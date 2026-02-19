from scanner.pipeline.liquidity import fetch_orderbooks_for_top_k, select_top_k_for_orderbook


class _DummyMexc:
    def __init__(self):
        self.calls = []

    def get_orderbook(self, symbol, limit=200):
        self.calls.append((symbol, limit))
        return {"symbol": symbol, "bids": [], "asks": []}


def test_select_top_k_for_orderbook_uses_proxy_liquidity_score_desc():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 80.0, "quote_volume_24h": 50},
        {"symbol": "C", "proxy_liquidity_score": 80.0, "quote_volume_24h": 70},
    ]
    selected = select_top_k_for_orderbook(rows, top_k=2)
    assert [r["symbol"] for r in selected] == ["C", "B"]


def test_fetch_orderbooks_for_top_k_respects_budget():
    rows = [
        {"symbol": "A", "proxy_liquidity_score": 10.0, "quote_volume_24h": 100},
        {"symbol": "B", "proxy_liquidity_score": 40.0, "quote_volume_24h": 100},
        {"symbol": "C", "proxy_liquidity_score": 50.0, "quote_volume_24h": 100},
        {"symbol": "D", "proxy_liquidity_score": 60.0, "quote_volume_24h": 100},
    ]
    cfg = {"liquidity": {"orderbook_top_k": 2}}
    client = _DummyMexc()

    payload = fetch_orderbooks_for_top_k(client, rows, cfg)

    assert len(client.calls) == 2
    assert set(payload.keys()) == {"D", "C"}
