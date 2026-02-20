from scanner.pipeline.backtest_runner import run_backtest_from_snapshots


def _snapshot(date, close, high, scoring):
    return {
        "meta": {"date": date},
        "data": {
            "features": {
                "AAAUSDT": {
                    "1d": {
                        "close": close,
                        "high": high,
                    }
                }
            }
        },
        "scoring": scoring,
    }


def test_trigger_window_uses_calendar_days_not_snapshot_index():
    snapshots = [
        _snapshot(
            "2026-01-01",
            close=99,
            high=100,
            scoring={
                "breakouts": [
                    {
                        "symbol": "AAAUSDT",
                        "analysis": {"trade_levels": {"entry_trigger": 101.0}},
                    }
                ],
                "pullbacks": [],
                "reversals": [],
            },
        ),
        _snapshot("2026-01-02", close=100, high=102, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-01-05", close=101, high=110, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
    ]

    out = run_backtest_from_snapshots(snapshots, config={"backtest": {"t_trigger_max": 3, "t_hold": 2}})
    event = out["events"]["breakout"][0]

    assert event["triggered"] is False
    assert event["trigger_day_offset"] is None


def test_hold_window_uses_calendar_days_after_trigger():
    snapshots = [
        _snapshot(
            "2026-01-01",
            close=101,
            high=101,
            scoring={
                "breakouts": [
                    {
                        "symbol": "AAAUSDT",
                        "analysis": {"trade_levels": {"entry_trigger": 101.0}},
                    }
                ],
                "pullbacks": [],
                "reversals": [],
            },
        ),
        _snapshot("2026-01-02", close=100, high=100, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-01-04", close=99, high=130, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
    ]

    out = run_backtest_from_snapshots(snapshots, config={"backtest": {"t_trigger_max": 1, "t_hold": 2}})
    event = out["events"]["breakout"][0]

    assert event["triggered"] is True
    assert event["trigger_day_offset"] == 0
    assert event["max_high_after_entry"] == 100
    assert event["hit_10"] is False
