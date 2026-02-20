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


def test_backtest_runner_applies_e2k_trigger_and_hits_for_breakout():
    snapshots = [
        _snapshot(
            "2026-02-01",
            close=99,
            high=100,
            scoring={
                "breakouts": [
                    {
                        "symbol": "AAAUSDT",
                        "analysis": {"trade_levels": {"entry_trigger": 100.0}},
                    }
                ],
                "pullbacks": [],
                "reversals": [],
            },
        ),
        _snapshot("2026-02-02", close=101, high=102, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-03", close=102, high=104, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-04", close=105, high=112, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-05", close=106, high=123, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
    ]

    out = run_backtest_from_snapshots(snapshots)
    event = out["events"]["breakout"][0]

    assert event["triggered"] is True
    assert event["trigger_day_offset"] == 1
    assert event["entry_price"] == 101
    assert event["hit_10"] is True
    assert event["hit_20"] is True


def test_backtest_runner_limits_trigger_window_and_pullback_zone_trigger():
    snapshots = [
        _snapshot(
            "2026-02-01",
            close=95,
            high=96,
            scoring={
                "breakouts": [
                    {
                        "symbol": "AAAUSDT",
                        "analysis": {"trade_levels": {"entry_trigger": 105.0}},
                    }
                ],
                "pullbacks": [
                    {
                        "symbol": "AAAUSDT",
                        "analysis": {"trade_levels": {"entry_zone": {"lower": 95.0, "upper": 97.0}}},
                    }
                ],
                "reversals": [],
            },
        ),
        _snapshot("2026-02-02", close=98, high=99, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-03", close=100, high=101, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-04", close=102, high=103, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-05", close=104, high=105, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-06", close=106, high=107, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
        _snapshot("2026-02-07", close=108, high=109, scoring={"breakouts": [], "pullbacks": [], "reversals": []}),
    ]

    out = run_backtest_from_snapshots(snapshots, config={"backtest": {"t_trigger_max": 3}})
    breakout_event = out["events"]["breakout"][0]
    pullback_event = out["events"]["pullback"][0]

    assert breakout_event["triggered"] is False
    assert pullback_event["triggered"] is True
    assert pullback_event["trigger_day_offset"] == 0
