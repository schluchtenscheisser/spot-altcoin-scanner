from scanner.pipeline.global_ranking import compute_global_top20
from scanner.pipeline.liquidity import compute_orderbook_liquidity_metrics, apply_liquidity_metrics_to_shortlist


def test_compute_orderbook_liquidity_metrics_returns_spread_slippage_and_grade():
    ob = {
        "bids": [["99", "500"], ["98", "500"]],
        "asks": [["101", "100"], ["102", "200"], ["103", "500"]],
    }
    out = compute_orderbook_liquidity_metrics(ob, notional_usdt=20_000, thresholds_bps=(20, 50, 100))
    assert out["spread_bps"] is not None
    assert out["slippage_bps"] is not None
    assert out["liquidity_grade"] in {"A", "B", "C", "D"}
    assert out["liquidity_insufficient"] is False


def test_compute_orderbook_liquidity_metrics_marks_insufficient_depth():
    ob = {"bids": [["99", "1"]], "asks": [["101", "1"]]}
    out = compute_orderbook_liquidity_metrics(ob, notional_usdt=20_000, thresholds_bps=(20, 50, 100))
    assert out["slippage_bps"] is None
    assert out["liquidity_grade"] == "D"
    assert out["liquidity_insufficient"] is True


def test_apply_liquidity_metrics_to_shortlist_enriches_topk_payload():
    shortlist = [{"symbol": "A"}, {"symbol": "B"}]
    orderbooks = {
        "A": {"bids": [["99", "500"]], "asks": [["101", "500"]]},
    }
    cfg = {"liquidity": {"slippage_notional_usdt": 1000, "grade_thresholds_bps": {"a_max": 20, "b_max": 50, "c_max": 100}}}
    out = apply_liquidity_metrics_to_shortlist(shortlist, orderbooks, cfg)
    by_symbol = {r["symbol"]: r for r in out}
    assert by_symbol["A"]["liquidity_grade"] in {"A", "B", "C", "D"}
    assert by_symbol["B"]["slippage_bps"] is None


def test_global_ranking_uses_slippage_then_proxy_tiebreak():
    reversals = []
    breakouts = [
        {"symbol": "A", "score": 80.0, "slippage_bps": 30.0, "proxy_liquidity_score": 10.0},
        {"symbol": "B", "score": 80.0, "slippage_bps": 10.0, "proxy_liquidity_score": 5.0},
        {"symbol": "C", "score": 80.0, "slippage_bps": 10.0, "proxy_liquidity_score": 20.0},
    ]
    pullbacks = []
    out = compute_global_top20(reversals, breakouts, pullbacks, {})
    assert [x["symbol"] for x in out[:3]] == ["C", "B", "A"]
