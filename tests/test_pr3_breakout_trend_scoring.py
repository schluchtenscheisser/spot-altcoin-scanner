from scanner.pipeline.global_ranking import compute_global_top20
from scanner.pipeline.scoring.breakout_trend_1_5d import BreakoutTrend1to5DScorer, score_breakout_trend_1_5d


def _kline(idx: int, close: float, high: float | None = None, low: float | None = None) -> list[float]:
    h = close if high is None else high
    l = close if low is None else low
    ts = 1_700_000_000_000 + idx * 60_000
    return [ts, close, h, l, close, 1_000.0, ts + 59_000, close * 1_000.0]


def _feature_row(dist_pct: float = 10.0, r7: float = 10.0) -> dict:
    high_20 = 100.0
    closes_1d = [80.0 + i for i in range(19)] + [100.0, 120.0]
    highs_1d = [80.5 + i for i in range(19)] + [100.0, 130.0]

    close_last_4h = high_20 * (1 + dist_pct / 100.0)
    close_4h = [90.0] * 44 + [99.0, 101.0, 102.0, close_last_4h]
    low_4h = [89.0] * 48

    return {
        "1d": {
            "close": 120.0,
            "ema_20": 110.0,
            "ema_50": 105.0,
            "dist_ema20_pct": 10.0,
            "atr_pct_rank_120": 0.5,
            "r_7": r7,
            "r_3": 5.0,
            "volume_quote_spike": 2.0,
            "close_series": closes_1d,
            "high_series": highs_1d,
        },
        "4h": {
            "close": close_last_4h,
            "ema_20": 101.0,
            "ema_50": 100.0,
            "bb_width_pct": 8.0,
            "bb_width_rank_120": 0.3,
            "volume_quote_spike": 2.0,
            "close_series": close_4h,
            "low_series": low_4h,
        },
        "quote_volume_24h": 30_000_000,
        "meta": {"last_closed_idx": {"1d": 20, "4h": 47}},
    }


def test_high_20d_excludes_current_1d_candle() -> None:
    scorer = BreakoutTrend1to5DScorer({})
    high_20 = scorer._calc_high_20d_excluding_current(_feature_row()["1d"])  # noqa: SLF001
    assert high_20 == 100.0


def test_trigger_detection_uses_last_6_closed_4h_candles() -> None:
    scorer = BreakoutTrend1to5DScorer({})
    feature = _feature_row()
    high_20 = 100.0

    # trigger older than 6 bars -> invalid
    feature["4h"]["close_series"] = [101.0] + [90.0] * 47
    assert scorer._find_first_breakout_idx(feature["4h"], high_20) is None  # noqa: SLF001

    # trigger in last 6 bars -> valid
    feature["4h"]["close_series"] = [90.0] * 43 + [99.0, 101.0, 99.0, 98.0, 97.0]
    idx = scorer._find_first_breakout_idx(feature["4h"], high_20)  # noqa: SLF001
    assert idx == 44


def test_multipliers_boundaries() -> None:
    scorer = BreakoutTrend1to5DScorer({})

    assert scorer._anti_chase_multiplier(30.0) == 1.0  # noqa: SLF001
    assert scorer._anti_chase_multiplier(45.0) == 0.875  # noqa: SLF001
    assert scorer._anti_chase_multiplier(60.0) == 0.75  # noqa: SLF001

    assert scorer._overextension_multiplier(12.0) == 1.0  # noqa: SLF001
    assert scorer._overextension_multiplier(20.0) == 0.85  # noqa: SLF001
    assert scorer._overextension_multiplier(27.9) > 0.70  # noqa: SLF001


def test_global_top20_dedup_tie_prefers_retest_setup() -> None:
    breakout_rows = [
        {"symbol": "AAAUSDT", "score": 80.0, "final_score": 80.0, "setup_id": "breakout_immediate_1_5d"},
        {"symbol": "AAAUSDT", "score": 80.0, "final_score": 80.0, "setup_id": "breakout_retest_1_5d"},
    ]

    top = compute_global_top20([], breakout_rows, [], {})

    assert len(top) == 1
    assert top[0]["setup_id"] == "breakout_retest_1_5d"


def test_global_top20_prefers_higher_final_score_over_weighted_setup_type() -> None:
    reversals = [{"symbol": "AAAUSDT", "score": 99.0, "final_score": 99.0, "setup_id": "reversal"}]
    breakouts = [{"symbol": "AAAUSDT", "score": 90.0, "final_score": 90.0, "setup_id": "breakout_immediate_1_5d"}]

    top = compute_global_top20(reversals, breakouts, [], {})

    assert len(top) == 1
    assert top[0]["setup_id"] == "reversal"
    assert top[0]["global_score"] == 99.0


def test_score_output_contains_both_setup_ids() -> None:
    cfg = {"setup_validation": {"min_history_breakout_1d": 20, "min_history_breakout_4h": 40}}
    rows = score_breakout_trend_1_5d(
        {"AAAUSDT": _feature_row()},
        {"AAAUSDT": 30_000_000},
        cfg,
        btc_regime={"state": "RISK_ON"},
    )
    ids = {r["setup_id"] for r in rows}
    assert "breakout_immediate_1_5d" in ids
