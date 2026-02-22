from scanner.pipeline.backtest_runner import run_backtest_from_snapshots


def _candle(open_, high, low, close, ema20=100.0):
    return {
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "ema20": float(ema20),
    }


def _snapshot_with_breakout(setup_id, candles):
    return {
        "meta": {"date": "2026-03-01"},
        "data": {
            "features": {
                "AAAUSDT": {
                    "1d": {"close": 100.0, "high": 101.0},
                }
            }
        },
        "scoring": {
            "breakouts": [
                {
                    "symbol": "AAAUSDT",
                    "setup_id": setup_id,
                    "analysis": {
                        "trade_levels": {"entry_trigger": 100.0, "breakout_level_20": 100.0},
                        "backtest_4h": {"atr_abs_4h": 1.0, "candles": candles},
                    },
                }
            ],
            "pullbacks": [],
            "reversals": [],
        },
    }


def test_pr4_priority_stop_over_partial_and_trail_same_candle():
    candles = [
        _candle(99.0, 101.0, 98.0, 101.0, ema20=99.0),  # trigger
        _candle(100.0, 101.7, 99.0, 101.0, ema20=99.0),  # immediate entry (below partial target)
        _candle(101.0, 102.0, 98.7, 99.0, ema20=100.0),  # stop + partial + trail signal all true
    ]
    snapshots = [_snapshot_with_breakout("breakout_immediate_1_5d", candles)]

    out = run_backtest_from_snapshots(snapshots)
    event = out["events"]["breakout_immediate_1_5d"][0]

    assert event["partial_hit"] is False
    assert event["exit_reason"] == "stop"
    assert event["exit_idx"] == 2


def test_pr4_trailing_activates_only_after_partial():
    candles = [
        _candle(99.0, 101.0, 98.0, 101.0, ema20=99.0),  # trigger
        _candle(100.0, 101.0, 99.0, 100.0, ema20=99.0),  # entry
        _candle(100.0, 100.5, 99.5, 99.0, ema20=100.0),  # close < ema20 before partial -> no trail
        _candle(100.0, 102.0, 99.8, 101.9, ema20=100.0),  # partial hit (target 101.8)
        _candle(100.0, 100.7, 99.9, 99.0, ema20=100.0),  # trail signal
        _candle(99.5, 100.0, 99.0, 99.8, ema20=100.0),   # next open fill
    ]
    snapshots = [_snapshot_with_breakout("breakout_immediate_1_5d", candles)]

    out = run_backtest_from_snapshots(snapshots)
    event = out["events"]["breakout_immediate_1_5d"][0]

    assert event["partial_hit"] is True
    assert event["partial_idx"] == 3
    assert event["exit_reason"] == "trail"
    assert event["exit_idx"] == 5


def test_pr4_time_stop_exits_on_next_open_after_168h():
    candles = [_candle(99.0, 101.0, 98.0, 101.0, ema20=99.0)]  # trigger
    candles.append(_candle(100.0, 100.5, 99.8, 100.0, ema20=99.0))  # entry
    for _ in range(40):
        candles.append(_candle(100.0, 100.6, 99.6, 100.1, ema20=99.5))
    candles.append(_candle(100.0, 100.4, 99.7, 100.2, ema20=99.5))  # 42nd hold candle
    candles.append(_candle(99.7, 100.2, 99.5, 99.9, ema20=99.5))   # next-open exit fill

    snapshots = [_snapshot_with_breakout("breakout_immediate_1_5d", candles)]
    out = run_backtest_from_snapshots(snapshots)
    event = out["events"]["breakout_immediate_1_5d"][0]

    assert event["exit_reason"] == "time_stop"
    assert event["exit_idx"] == 43
    assert event["partial_hit"] is False
