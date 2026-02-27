from scanner.backtest.e2_model import evaluate_e2_candidate


def _base_series():
    return {
        "2026-02-01": {"close": 100.0, "high": 101.0, "low": 99.0},
        "2026-02-02": {"close": 106.0, "high": 111.0, "low": 103.0},
        "2026-02-03": {"close": 107.0, "high": 121.0, "low": 104.0},
        "2026-02-04": {"close": 108.0, "high": 109.0, "low": 101.0},
    }


def test_e2_no_trigger_case():
    result = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={"entry_trigger": 130.0},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2, "thresholds_pct": [10, 20]},
    )

    assert result["reason"] == "no_trigger"
    assert result["t_trigger_date"] is None
    assert result["hit_10"] is None
    assert result["hit_20"] is None


def test_e2_ok_and_hit_thresholds_true_false():
    series = {
        "2026-02-01": {"close": 100.0, "high": 100.0, "low": 98.0},
        "2026-02-02": {"close": 105.0, "high": 105.0, "low": 100.0},
        "2026-02-03": {"close": 106.0, "high": 116.0, "low": 103.0},
        "2026-02-04": {"close": 107.0, "high": 124.0, "low": 104.0},
    }

    result = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={"entry_trigger": 105.0},
        price_series=series,
        params={"T_trigger_max": 1, "T_hold": 2, "thresholds_pct": [5, 10, 20]},
    )

    assert result["reason"] == "ok"
    assert result["t_trigger_date"] == "2026-02-02"
    assert result["t_trigger_day_offset"] == 1
    assert result["hit_10"] is True
    assert result["hit_20"] is False
    assert result["hits"] == {"5": True, "10": True, "20": False}
    assert result["mfe_pct"] > 18.0
    assert result["mae_pct"] < 0.0


def test_e2_missing_trade_levels_by_setup_type():
    result_breakout = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_breakout["reason"] == "missing_trade_levels"

    result_reversal = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="reversal",
        trade_levels={},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_reversal["reason"] == "missing_trade_levels"

    result_pullback = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="pullback",
        trade_levels={"entry_zone": {"lower": 100.0}},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_pullback["reason"] == "missing_trade_levels"


def test_e2_invalid_trade_levels_by_setup_type():
    result_breakout = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={"entry_trigger": "x"},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_breakout["reason"] == "invalid_trade_levels"

    result_reversal = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="reversal",
        trade_levels={"entry_trigger": 0},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_reversal["reason"] == "invalid_trade_levels"

    result_pullback = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="pullback",
        trade_levels={"entry_zone": {"lower": 105.0, "upper": 100.0}},
        price_series=_base_series(),
        params={"T_trigger_max": 2, "T_hold": 2},
    )
    assert result_pullback["reason"] == "invalid_trade_levels"


def test_e2_missing_price_series_when_search_window_has_no_valid_close():
    series = {
        "2026-02-01": {"close": None, "high": 101.0, "low": 99.0},
        "2026-02-02": {"close": None, "high": 102.0, "low": 98.0},
    }

    result = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={"entry_trigger": 100.0},
        price_series=series,
        params={"T_trigger_max": 1, "T_hold": 2},
    )

    assert result["reason"] == "missing_price_series"


def test_e2_insufficient_forward_history_when_hold_window_has_missing_day():
    series = {
        "2026-02-01": {"close": 100.0, "high": 101.0, "low": 99.0},
        "2026-02-02": {"close": 105.0, "high": 106.0, "low": 102.0},
        "2026-02-03": {"close": 107.0, "high": 108.0, "low": 101.0},
        # missing 2026-02-04 (strict hold-window failure)
    }

    result = evaluate_e2_candidate(
        t0_date="2026-02-01",
        setup_type="breakout",
        trade_levels={"entry_trigger": 105.0},
        price_series=series,
        params={"T_trigger_max": 1, "T_hold": 2},
    )

    assert result["reason"] == "insufficient_forward_history"
    assert result["hit_10"] is None
    assert result["hit_20"] is None
