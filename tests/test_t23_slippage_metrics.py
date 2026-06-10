from scanner.execution.tradeability_metrics import compute_tradeability_metrics
from scanner.pipeline.global_ranking import compute_global_top20
from scanner.pipeline.liquidity import (
    apply_liquidity_metrics_to_shortlist,
    compute_orderbook_liquidity_metrics,
    compute_orderbook_metrics,
)


def _tradeability_cfg(overrides=None):
    cfg = {
        "tradeability": {
            "notional_total_usdt": 20_000,
            "notional_chunk_usdt": 5_000,
            "max_tranches": 4,
            "band_pct": 1.0,
            "max_spread_pct": 0.2,
            "min_depth_1pct_usd": 20_000,
            "class_thresholds": {
                "direct_ok_max_slippage_bps": 50,
                "tranche_ok_max_slippage_bps": 100,
                "marginal_max_slippage_bps": 150,
            },
        }
    }
    if overrides:
        cfg["tradeability"].update(overrides)
    return cfg


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
    assert by_symbol["B"]["liquidity_grade"] is None


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


def test_compute_orderbook_metrics_spread_and_depth_correctness():
    ob = {
        "bids": [[99, 10], [98, 10]],
        "asks": [[101, 10], [102, 10]],
    }
    out = compute_orderbook_metrics(ob, bands_pct=[1.0])

    assert out["orderbook_ok"] is True
    assert out["spread_pct"] == 2.0
    assert out["depth_bid_1pct_usd"] == 990
    assert out["depth_ask_1pct_usd"] == 1010


def test_compute_orderbook_metrics_missing_book_returns_nan_like_fields():
    out = compute_orderbook_metrics({"bids": [], "asks": []}, bands_pct=[0.5, 1.0])

    assert out["orderbook_ok"] is False
    assert out["spread_pct"] is None
    assert out["depth_bid_0_5pct_usd"] is None
    assert out["depth_ask_0_5pct_usd"] is None
    assert out["depth_bid_1pct_usd"] is None
    assert out["depth_ask_1pct_usd"] is None


def test_tradeability_direct_ok_sets_direct_mode():
    ob = {
        "bids": [[99.95, 3_000], [99.90, 2_000]],
        "asks": [[100.05, 3_000], [100.10, 2_000]],
    }
    out = compute_tradeability_metrics(ob, _tradeability_cfg())

    assert out["tradeability_class"] == "DIRECT_OK"
    assert out["execution_mode"] == "direct"
    assert out["tradeable_20k"] is True
    assert out["tradeable_via_tranches"] is True
    assert out["tradeability_reason_keys"] == []


def test_tradeability_tranche_ok_when_20k_fails_but_5k_passes():
    ob = {
        "bids": [[99.95, 3_000], [99.9, 2_000]],
        "asks": [[100.05, 50], [101.0, 200], [101.5, 3_000]],
    }
    out = compute_tradeability_metrics(ob, _tradeability_cfg())

    assert out["tradeability_class"] == "TRANCHE_OK"
    assert out["execution_mode"] == "tranches"
    assert out["tradeable_20k"] is False
    assert out["tradeable_5k"] is True
    assert out["tradeable_via_tranches"] is True
    assert out["tradeability_reason_keys"] == []


def test_tradeability_marginal_classification_and_none_mode():
    ob = {
        "bids": [[99.95, 3_000], [99.9, 2_000]],
        "asks": [[100.05, 20], [101.5, 50], [102.0, 2_000]],
    }
    out = compute_tradeability_metrics(ob, _tradeability_cfg())

    assert out["tradeability_class"] == "MARGINAL"
    assert out["execution_mode"] == "none"
    assert out["tradeable_20k"] is False
    assert out["tradeable_via_tranches"] is False


def test_tradeability_fail_classification_and_reasons():
    ob = {
        "bids": [[80.0, 500]],
        "asks": [[120.0, 500]],
    }
    out = compute_tradeability_metrics(ob, _tradeability_cfg())

    assert out["tradeability_class"] == "FAIL"
    assert out["execution_mode"] == "none"
    assert "spread_too_wide" in out["tradeability_reason_keys"]
    assert "tranche_execution_not_feasible" in out["tradeability_reason_keys"]


def test_apply_liquidity_metrics_sets_unknown_missing_and_not_in_budget():
    shortlist = [{"symbol": "A"}, {"symbol": "B"}]
    out = apply_liquidity_metrics_to_shortlist(shortlist, {}, _tradeability_cfg(), selected_symbols={"A"})
    by_symbol = {r["symbol"]: r for r in out}

    assert by_symbol["A"]["tradeability_class"] == "UNKNOWN"
    assert by_symbol["A"]["execution_mode"] == "none"
    assert by_symbol["A"]["tradeability_reason_keys"] == ["orderbook_data_missing"]
    assert by_symbol["A"]["slippage_bps_5k"] is None

    assert by_symbol["B"]["tradeability_class"] == "UNKNOWN"
    assert by_symbol["B"]["tradeability_reason_keys"] == ["orderbook_not_in_budget"]


def test_tradeability_stale_orderbook_is_unknown():
    ob = {"bids": [[99.9, 100]], "asks": [[100.1, 100]], "stale": True}
    out = compute_tradeability_metrics(ob, _tradeability_cfg())
    assert out["tradeability_class"] == "UNKNOWN"
    assert out["execution_mode"] == "none"
    assert out["tradeability_reason_keys"] == ["orderbook_data_stale"]


def test_tradeability_defaults_apply_when_keys_missing():
    cfg = {"tradeability": {}}
    ob = {"bids": [[99.95, 5_000]], "asks": [[100.05, 5_000]]}
    out = compute_tradeability_metrics(ob, cfg)
    assert out["tradeability_class"] in {"DIRECT_OK", "TRANCHE_OK", "MARGINAL", "FAIL"}


def test_tradeability_invalid_thresholds_raise_clear_error():
    cfg = _tradeability_cfg(
        {
            "class_thresholds": {
                "direct_ok_max_slippage_bps": 100,
                "tranche_ok_max_slippage_bps": 50,
                "marginal_max_slippage_bps": 10,
            }
        }
    )
    ob = {"bids": [[99.95, 5_000]], "asks": [[100.05, 5_000]]}

    try:
        compute_tradeability_metrics(ob, cfg)
        raised = False
    except ValueError as exc:
        raised = True
        assert "must satisfy" in str(exc)

    assert raised is True
