from scanner.pipeline.backtest_runner import run_backtest_from_snapshots


def _candle(open_, high, low, close, ema20=100.0):
    return {
        "open": float(open_),
        "high": float(high),
        "low": float(low),
        "close": float(close),
        "ema20": float(ema20),
    }


def _snapshot(setup_id: str, candles, day: str):
    return {
        "meta": {"date": day},
        "data": {"features": {"AAAUSDT": {"1d": {"close": 100.0, "high": 101.0}}}},
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


def test_pr13_triggered_no_trade_does_not_count_as_trade():
    retest_invalidated = [
        _candle(99.0, 101.2, 98.5, 101.0),  # trigger
        _candle(101.0, 101.3, 100.8, 99.9),  # invalidation: close below breakout before retest fill
    ]

    out = run_backtest_from_snapshots([_snapshot("breakout_retest_1_5d", retest_invalidated, "2026-03-01")])
    summary = out["by_setup"]["breakout_retest_1_5d"]

    assert summary["signals_count"] == 1
    assert summary["trades_count"] == 0
    assert summary["trade_rate_on_signals"] == 0.0


def test_pr13_executed_trade_counts_but_no_trade_rows_do_not():
    retest_invalidated = [
        _candle(99.0, 101.2, 98.5, 101.0),
        _candle(101.0, 101.3, 100.8, 99.9),
    ]
    retest_tradable = [
        _candle(99.0, 101.2, 98.5, 101.0),
        _candle(101.0, 101.4, 99.8, 100.9),
    ]

    out = run_backtest_from_snapshots(
        [
            _snapshot("breakout_retest_1_5d", retest_invalidated, "2026-03-01"),
            _snapshot("breakout_retest_1_5d", retest_tradable, "2026-03-02"),
        ]
    )
    summary = out["by_setup"]["breakout_retest_1_5d"]

    assert summary["signals_count"] == 2
    assert summary["trades_count"] == 1
    assert summary["trade_rate_on_signals"] == 0.5
