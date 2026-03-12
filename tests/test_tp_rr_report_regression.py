import pytest

from scanner.pipeline.output import ReportGenerator


def test_trade_candidates_target_rr_fields_follow_setup_targets_only() -> None:
    generator = ReportGenerator({"output": {"top_n_per_setup": 5}})

    global_top20 = [
        {
            "symbol": "AUSDT",
            "coin_name": "A",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 100.0,
            "stop_price_initial": 95.0,
            "analysis": {"trade_levels": {"entry_trigger": 100.0, "targets": [110.0, 120.0]}},
            "best_setup_type": "breakout",
        },
        {
            "symbol": "BUSDT",
            "coin_name": "B",
            "decision": "WAIT",
            "decision_reasons": ["entry_not_confirmed"],
            "price_usdt": 100.0,
            "stop_price_initial": None,
            "analysis": {"trade_levels": {"entry_trigger": 100.0, "targets": [110.0]}},
            "best_setup_type": "breakout",
        },
    ]

    rows = generator.generate_json_report([], [], [], global_top20, "2026-03-10")["trade_candidates"]
    by_symbol = {row["symbol"]: row for row in rows}

    a = by_symbol["AUSDT"]
    assert "tp10_price" not in a
    assert "tp20_price" not in a
    assert "rr_to_tp10" not in a
    assert "rr_to_tp20" not in a
    assert a["target_1_price"] == pytest.approx(110.0)
    assert a["target_2_price"] == pytest.approx(120.0)
    assert a["rr_to_target_1"] == pytest.approx((110.0 - 100.0) / (100.0 - 95.0))
    assert a["rr_to_target_2"] == pytest.approx((120.0 - 100.0) / (100.0 - 95.0))

    b = by_symbol["BUSDT"]
    assert b["target_1_price"] == pytest.approx(110.0)
    assert b["target_2_price"] is None
    assert b["rr_to_target_1"] is None
    assert b["rr_to_target_2"] is None
