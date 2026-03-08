from scanner.pipeline.liquidity import apply_liquidity_metrics_to_shortlist, compute_tradeability_metrics


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


def test_pr08_tradeability_class_taxonomy_covered():
    direct_ok = compute_tradeability_metrics(
        {"bids": [[99.95, 3_000], [99.90, 2_000]], "asks": [[100.05, 3_000], [100.10, 2_000]]},
        _tradeability_cfg(),
    )
    tranche_ok = compute_tradeability_metrics(
        {"bids": [[99.95, 3_000], [99.90, 2_000]], "asks": [[100.05, 50], [101.0, 200], [101.5, 3_000]]},
        _tradeability_cfg(),
    )
    marginal = compute_tradeability_metrics(
        {"bids": [[99.95, 3_000], [99.9, 2_000]], "asks": [[100.05, 20], [101.5, 50], [102.0, 2_000]]},
        _tradeability_cfg(),
    )
    fail = compute_tradeability_metrics(
        {"bids": [[80.0, 500]], "asks": [[120.0, 500]]},
        _tradeability_cfg(),
    )
    unknown = compute_tradeability_metrics(
        {"bids": [[99.9, 100]], "asks": [[100.1, 100]], "stale": True},
        _tradeability_cfg(),
    )

    assert direct_ok["tradeability_class"] == "DIRECT_OK"
    assert tranche_ok["tradeability_class"] == "TRANCHE_OK"
    assert tranche_ok["tradeable_20k"] is False
    assert marginal["tradeability_class"] == "MARGINAL"
    assert marginal["execution_mode"] == "none"
    assert fail["tradeability_class"] == "FAIL"
    assert unknown["tradeability_class"] == "UNKNOWN"
    assert fail["tradeability_class"] != unknown["tradeability_class"]


def test_pr08_unknown_reason_paths_missing_stale_and_not_in_budget():
    shortlist = [{"symbol": "A"}, {"symbol": "B"}]
    out = apply_liquidity_metrics_to_shortlist(shortlist, {}, _tradeability_cfg(), selected_symbols={"A"})
    by_symbol = {r["symbol"]: r for r in out}

    stale = compute_tradeability_metrics({"bids": [[99.9, 100]], "asks": [[100.1, 100]], "is_stale": True}, _tradeability_cfg())

    assert by_symbol["A"]["tradeability_class"] == "UNKNOWN"
    assert by_symbol["A"]["tradeability_reason_keys"] == ["orderbook_data_missing"]
    assert stale["tradeability_class"] == "UNKNOWN"
    assert stale["tradeability_reason_keys"] == ["orderbook_data_stale"]
    assert by_symbol["B"]["tradeability_class"] == "UNKNOWN"
    assert by_symbol["B"]["tradeability_reason_keys"] == ["orderbook_not_in_budget"]


def test_pr08_missing_config_defaults_and_invalid_thresholds_error():
    ob = {"bids": [[99.95, 5_000]], "asks": [[100.05, 5_000]]}

    defaults_used = compute_tradeability_metrics(ob, {"tradeability": {}})
    assert defaults_used["tradeability_class"] in {"DIRECT_OK", "TRANCHE_OK", "MARGINAL", "FAIL"}

    invalid_cfg = _tradeability_cfg(
        {
            "class_thresholds": {
                "direct_ok_max_slippage_bps": 100,
                "tranche_ok_max_slippage_bps": 50,
                "marginal_max_slippage_bps": 10,
            }
        }
    )
    try:
        compute_tradeability_metrics(ob, invalid_cfg)
        raised = False
    except ValueError as exc:
        raised = True
        assert "must satisfy" in str(exc)

    assert raised is True


def test_pr08_tradeability_reason_paths_are_deterministic_for_same_input():
    ob = {"bids": [[80.0, 500]], "asks": [[120.0, 500]]}
    cfg = _tradeability_cfg()

    out1 = compute_tradeability_metrics(ob, cfg)
    out2 = compute_tradeability_metrics(ob, cfg)

    assert out1["tradeability_class"] == out2["tradeability_class"] == "FAIL"
    assert out1["tradeability_reason_keys"] == out2["tradeability_reason_keys"]
