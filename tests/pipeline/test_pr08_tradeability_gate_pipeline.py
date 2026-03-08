from scanner.pipeline import _apply_tradeability_gate


def test_pr08_unknown_is_stopped_and_never_forwarded_as_wait():
    rows = [
        {"symbol": "AAAUSDT", "tradeability_class": "DIRECT_OK"},
        {"symbol": "BBBUSDT", "tradeability_class": "UNKNOWN", "tradeability_reason_keys": ["orderbook_data_missing"]},
        {"symbol": "CCCUSDT", "tradeability_class": "FAIL", "tradeability_reason_keys": ["slippage_20k_too_high"]},
    ]

    passed, stopped = _apply_tradeability_gate(rows)

    assert [row["symbol"] for row in passed] == ["AAAUSDT"]
    assert [row["symbol"] for row in stopped] == ["BBBUSDT", "CCCUSDT"]

    unknown_row = next(row for row in stopped if row["symbol"] == "BBBUSDT")
    assert unknown_row["tradeability_gate_stop_reason_keys"] == ["orderbook_data_missing"]
    assert unknown_row.get("decision") != "WAIT"
