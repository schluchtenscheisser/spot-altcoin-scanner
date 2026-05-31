from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from scripts.backtest.generate_exit_path_metrics_4h import (
    Backtest3AConfig,
    build_exit_path_metrics,
    run,
    validate_preflight,
)


def _write_events(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_parquet(path, index=False)


def _event(**overrides: object) -> dict[str, object]:
    row = {
        "symbol": "AAAUSDT",
        "decision_bucket": "early_candidates",
        "entry_pattern": "base_reclaim",
        "signal_timestamp": "2026-05-01T01:00:00Z",
        "setup_cycle_id": 1,
        "signal_reference_price": 100.0,
    }
    row.update(overrides)
    return row


def _bar(symbol: str, ts: str, open_: float, high: float, low: float, close: float) -> dict[str, object]:
    return {
        "source": "fixture",
        "symbol": symbol,
        "timeframe": "4h",
        "open_time_utc": ts,
        "close_time_utc": pd.Timestamp(ts) + pd.Timedelta(hours=4),
        "open": open_,
        "high": high,
        "low": low,
        "close": close,
        "volume": 1.0,
        "quote_volume": 100.0,
        "trade_count": 1,
        "is_closed": True,
        "fetch_run_id": "fixture",
        "fetched_at_utc": "2026-05-30T00:00:00Z",
    }


def _write_ohlcv(history_root: Path, symbol: str, rows: list[dict[str, object]]) -> None:
    frame = pd.DataFrame(rows)
    ts = pd.to_datetime(frame["open_time_utc"], utc=True)
    for (year, month), group in frame.groupby([ts.dt.year, ts.dt.month], sort=True):
        path = history_root / "timeframe=4h" / f"symbol={symbol}" / f"year={int(year):04d}" / f"month={int(month):02d}" / "part-000.parquet"
        path.parent.mkdir(parents=True, exist_ok=True)
        group.to_parquet(path, index=False)


def _basic_history(history_root: Path, symbol: str = "AAAUSDT") -> None:
    rows = []
    for idx, ts in enumerate(pd.date_range("2026-04-28T00:00:00Z", periods=24, freq="4h")):
        rows.append(_bar(symbol, ts.strftime("%Y-%m-%dT%H:%M:%SZ"), 99 + idx, 101 + idx, 98 + idx, 100 + idx))
    _write_ohlcv(history_root, symbol, rows)


def test_cli_defaults_path_bars_42_and_primary_only_true() -> None:
    config = Backtest3AConfig()
    assert config.path_bars == 42
    assert config.primary_only is True


@pytest.mark.parametrize("path_bars", [0, 241])
def test_invalid_path_bars_fails_preflight(tmp_path: Path, path_bars: int) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event()])
    history = tmp_path / "history" / "ohlcv"
    history.mkdir(parents=True)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=path_bars)

    with pytest.raises(ValueError, match="path_bars"):
        validate_preflight(config)
    assert not (tmp_path / "out").exists()


def test_invalid_timeframe_fails_preflight(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event()])
    history = tmp_path / "history" / "ohlcv"
    history.mkdir(parents=True)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, bar_timeframe="1d")

    with pytest.raises(ValueError, match="bar_timeframe"):
        validate_preflight(config)
    assert not (tmp_path / "out").exists()


def test_primary_scope_filter_excludes_late_monitor_and_non_primary(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(
        events,
        [
            _event(symbol="AAAUSDT", decision_bucket="early_candidates", entry_pattern="base_reclaim"),
            _event(symbol="BBBUSDT", decision_bucket="confirmed_candidates", entry_pattern="ema_reclaim"),
            _event(symbol="CCCUSDT", decision_bucket="early_candidates", entry_pattern="early_reversal_break"),
            _event(symbol="DDDUSDT", decision_bucket="confirmed_candidates", entry_pattern="base_reclaim"),
            _event(symbol="EEEUSDT", decision_bucket="late_monitor", entry_pattern="base_reclaim"),
        ],
    )
    history = tmp_path / "history" / "ohlcv"
    for symbol in ("AAAUSDT", "BBBUSDT", "CCCUSDT"):
        _basic_history(history, symbol)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, summary, report, _ = build_exit_path_metrics(config)

    assert set(event_df["segment_key"]) == {
        "early_candidates__base_reclaim",
        "confirmed_candidates__ema_reclaim",
        "early_candidates__early_reversal_break",
    }
    assert summary["late_monitor_included"] is False
    assert "late_monitor was not included in Primary Trade Scope metrics." in report


def test_daily_close_aligned_path_bar_1_open_is_used_as_reference_price(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T23:59:59Z", signal_reference_price=None)])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-02T00:00:00Z", 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["path_bar_1_timestamp"] == "2026-05-02T00:00:00Z"
    assert row["path_bar_1_open"] == 100.0
    assert row["reference_price"] == 100.0
    assert row["reference_price_status"] == "available"
    assert row["reference_price_source"] == "path_bar_1_open"
    assert row["reference_price_reason"] == "fallback_to_path_bar_1_open"
    assert row["mfe_pct"] == pytest.approx(3.0)
    assert row["mae_pct"] == pytest.approx(-2.0)
    assert bar_df.iloc[0]["return_close_pct"] == pytest.approx(1.0)


@pytest.mark.parametrize(
    ("signal_timestamp", "path_bar_1_timestamp"),
    [
        ("2026-05-01T00:01:00Z", "2026-05-01T04:00:00Z"),
        ("2026-05-01T23:59:58Z", "2026-05-02T00:00:00Z"),
    ],
)
def test_path_bar_1_open_fallback_rejects_delta_greater_than_one_second(
    tmp_path: Path, signal_timestamp: str, path_bar_1_timestamp: str
) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp=signal_timestamp, signal_reference_price=None)])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", path_bar_1_timestamp, 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["path_bar_1_timestamp"] == path_bar_1_timestamp
    assert row["path_bar_1_open"] == 100.0
    assert row["reference_price_status"] == "missing"
    assert row["reference_price_source"] == "null"
    assert pd.isna(row["reference_price"])
    assert pd.isna(row["mfe_pct"])
    assert pd.isna(row["mae_pct"])
    assert bar_df["return_close_pct"].isna().all()


@pytest.mark.parametrize("value", [None, float("nan"), 0.0, -1.0])
def test_invalid_path_bar_1_open_does_not_fire_reference_price_fallback(tmp_path: Path, value: float | None) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T23:59:59Z", signal_reference_price=None)])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-02T00:00:00Z", value, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["reference_price_status"] == "missing"
    assert row["reference_price_source"] == "null"
    assert pd.isna(row["reference_price"])
    assert pd.isna(row["mfe_pct"])
    assert pd.isna(row["mae_pct"])
    assert bar_df.empty


def test_path_bar_1_open_fallback_uses_computed_path_value_not_input_row_value(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(
        events,
        [_event(signal_timestamp="2026-05-01T23:59:59Z", signal_reference_price=None, path_bar_1_open=float("nan"))],
    )
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-02T00:00:00Z", 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["path_bar_1_open"] == 100.0
    assert row["reference_price"] == 100.0
    assert row["reference_price_source"] == "path_bar_1_open"
    assert row["reference_price_status"] == "available"


def test_ambiguous_event_close_remains_not_evaluable(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_reference_price=None, close=100.0, signal_close=101.0)])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["reference_price_status"] == "ambiguous"
    assert row["reference_price_source"] == "null"
    assert pd.isna(row["mfe_pct"])


def test_nan_reference_price_column_continues_fallback(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_reference_price=float("nan"), entry_reference_price=50.0)])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["reference_price"] == 50.0
    assert row["reference_price_source"] == "entry_reference_price"
    assert row["reference_price_status"] == "available"


@pytest.mark.parametrize("value", [float("inf"), float("-inf")])
def test_non_finite_reference_price_remains_invalid(tmp_path: Path, value: float) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_reference_price=value)])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)

    assert event_df.iloc[0]["reference_price_status"] == "invalid"
    assert pd.isna(event_df.iloc[0]["mfe_pct"])


def test_mfe_mae_math_from_4h_high_low_and_first_tie_wins(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T00:00:00Z", signal_reference_price=100.0)])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(
        history,
        "AAAUSDT",
        [
            _bar("AAAUSDT", "2026-05-01T00:00:00Z", 100, 103, 98, 101),
            _bar("AAAUSDT", "2026-05-01T04:00:00Z", 101, 108, 95, 106),
            _bar("AAAUSDT", "2026-05-01T08:00:00Z", 106, 108, 95, 107),
        ],
    )
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=3)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["mfe_pct"] == pytest.approx(8.0)
    assert row["mae_pct"] == pytest.approx(-5.0)
    assert row["mfe_bar_index_4h"] == 2
    assert row["mae_bar_index_4h"] == 2


def test_atr_insufficient_history_outputs_not_available(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T00:00:00Z")])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-01T00:00:00Z", 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["atr_4h_available"] is False or row["atr_4h_available"] == False
    assert pd.isna(row["atr_4h_value"])
    assert row["atr_4h_source"] == "not_available"


def test_missing_event_id_generates_stable_hash(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event()])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    first, *_ = build_exit_path_metrics(config)
    second, *_ = build_exit_path_metrics(config)

    assert first.iloc[0]["event_id"] == second.iloc[0]["event_id"]
    assert str(first.iloc[0]["event_id"]).startswith("bt3a_")


def test_signal_inside_4h_bar_uses_next_bar(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T01:00:00Z")])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(
        history,
        "AAAUSDT",
        [
            _bar("AAAUSDT", "2026-05-01T00:00:00Z", 90, 91, 89, 90),
            _bar("AAAUSDT", "2026-05-01T04:00:00Z", 100, 103, 98, 101),
        ],
    )
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)

    assert event_df.iloc[0]["path_bar_1_timestamp"] == "2026-05-01T04:00:00Z"


def test_signal_on_4h_boundary_uses_boundary_bar(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T04:00:00Z")])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-01T04:00:00Z", 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)

    assert event_df.iloc[0]["path_bar_1_timestamp"] == "2026-05-01T04:00:00Z"


def test_naive_datetime_marked_invalid(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T04:00:00")])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(config)

    assert event_df.iloc[0]["path_coverage_status"] == "path_failed_invalid_input"


def test_backtest_3a_fixture_outputs_all_required_files_and_keeps_edge_rows(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    rows = [
        _event(symbol="AAAUSDT", decision_bucket="early_candidates", entry_pattern="base_reclaim"),
        _event(symbol="BBBUSDT", decision_bucket="confirmed_candidates", entry_pattern="ema_reclaim"),
        _event(symbol="CCCUSDT", decision_bucket="early_candidates", entry_pattern="early_reversal_break", signal_reference_price=None),
        _event(symbol="DDDUSDT", decision_bucket="early_candidates", entry_pattern="base_reclaim"),
        _event(symbol="EEEUSDT", decision_bucket="confirmed_candidates", entry_pattern="base_reclaim"),
        _event(symbol="FFFUSDT", decision_bucket="late_monitor", entry_pattern="base_reclaim"),
    ]
    _write_events(events, rows)
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history, "AAAUSDT")
    _basic_history(history, "BBBUSDT")
    _basic_history(history, "CCCUSDT")
    _write_ohlcv(history, "DDDUSDT", [_bar("DDDUSDT", "2026-05-01T04:00:00Z", 100, 101, 99, 100)])
    out = tmp_path / "out"
    config = Backtest3AConfig(input_events_path=events, output_dir=out, history_root=history, path_bars=3)

    summary = run(config)

    for filename in (
        "exit_path_metrics_4h.parquet",
        "exit_path_metrics_4h.csv",
        "exit_path_metrics_4h_summary.json",
        "exit_path_metrics_4h_report.md",
        "exit_path_returns_by_bar.parquet",
        "exit_path_returns_by_bar.csv",
    ):
        assert (out / filename).exists()
    event_df = pd.read_parquet(out / "exit_path_metrics_4h.parquet")
    assert "path_partial" in set(event_df["path_coverage_status"])
    assert "path_not_evaluated" not in set(event_df.loc[event_df["symbol"] != "DDDUSDT", "path_coverage_status"])
    assert summary["counts"]["primary_scope_rows"] == 4


def test_no_ohlcv_not_silent_drop_and_preflight_failure_writes_no_files(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(symbol="NOHISTUSDT")])
    history = tmp_path / "history" / "ohlcv"
    history.mkdir(parents=True)
    good = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, _summary, _report, _ = build_exit_path_metrics(good)
    assert len(event_df) == 1
    assert event_df.iloc[0]["path_coverage_status"] == "path_not_evaluated"

    bad = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "bad_out", history_root=history, path_bars=0)
    with pytest.raises(ValueError):
        run(bad)
    assert not (tmp_path / "bad_out").exists()


def test_repeated_runs_identical_output_order(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(
        events,
        [
            _event(symbol="BBBUSDT", decision_bucket="confirmed_candidates", entry_pattern="ema_reclaim"),
            _event(symbol="AAAUSDT", decision_bucket="early_candidates", entry_pattern="base_reclaim"),
        ],
    )
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history, "AAAUSDT")
    _basic_history(history, "BBBUSDT")
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    first_events, first_bars, *_ = build_exit_path_metrics(config)
    second_events, second_bars, *_ = build_exit_path_metrics(config)

    pd.testing.assert_frame_equal(first_events, second_events)
    pd.testing.assert_frame_equal(first_bars, second_bars)


def test_path_bar_1_open_is_not_used_even_when_signal_is_on_boundary(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(signal_timestamp="2026-05-01T04:00:00Z", signal_reference_price=None)])
    history = tmp_path / "history" / "ohlcv"
    _write_ohlcv(history, "AAAUSDT", [_bar("AAAUSDT", "2026-05-01T04:00:00Z", 100, 103, 98, 101)])
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, bar_df, _summary, _report, _ = build_exit_path_metrics(config)
    row = event_df.iloc[0]

    assert row["path_bar_1_open"] == 100.0
    assert row["reference_price_status"] == "missing"
    assert pd.isna(row["mfe_pct"])
    assert pd.isna(row["mae_pct"])
    assert bar_df["return_close_pct"].isna().all()


def test_selected_primary_duplicate_row_is_kept_and_lower_priority_row_is_discarded(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(
        events,
        [
            _event(event_id="same-event", included_in_signal_analysis=False, event_type="duplicate_lower_priority_event", analysis_event_rank=6),
            _event(event_id="same-event", included_in_signal_analysis=True, event_type="selected_primary_event", analysis_event_rank=1),
        ],
    )
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, bar_df, summary, report, _ = build_exit_path_metrics(config)

    assert list(event_df["event_id"]) == ["same-event"]
    assert list(bar_df["event_id"].unique()) == ["same-event"]
    assert summary["counts"]["input_rows_before_deduplication"] == 2
    assert summary["counts"]["output_rows_after_deduplication"] == 1
    assert summary["counts"]["duplicate_event_id_count"] == 1
    assert summary["counts"]["discarded_duplicate_row_count"] == 1
    assert summary["counts"]["conflicting_duplicate_event_id_count"] == 0
    assert "Discarded lower-priority or identical duplicate rows: 1" in report


def test_identical_duplicate_event_ids_keep_first_deterministically(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    duplicate = _event(event_id="same-event")
    _write_events(events, [duplicate, duplicate.copy()])
    history = tmp_path / "history" / "ohlcv"
    _basic_history(history)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=2)

    event_df, _bar_df, summary, _report, _ = build_exit_path_metrics(config)

    assert list(event_df["event_id"]) == ["same-event"]
    assert summary["counts"]["discarded_duplicate_row_count"] == 1


def test_conflicting_duplicate_event_ids_fail_preflight_before_writes(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    _write_events(events, [_event(event_id="same-event"), _event(event_id="same-event", setup_cycle_id=2)])
    history = tmp_path / "history" / "ohlcv"
    history.mkdir(parents=True)
    out = tmp_path / "out"
    config = Backtest3AConfig(input_events_path=events, output_dir=out, history_root=history, path_bars=2)

    with pytest.raises(ValueError, match="Conflicting duplicate event_ids detected — cannot deduplicate safely"):
        run(config)
    assert not out.exists()


def test_backtest_3a_sized_selected_duplicates_reduce_291_rows_to_228(tmp_path: Path) -> None:
    events = tmp_path / "events.parquet"
    selected_rows = [
        _event(event_id=f"event-{idx:03d}", setup_cycle_id=idx, included_in_signal_analysis=True, event_type="selected_primary_event", analysis_event_rank=1)
        for idx in range(228)
    ]
    lower_priority_rows = [
        {**row, "included_in_signal_analysis": False, "event_type": "duplicate_lower_priority_event", "analysis_event_rank": 6}
        for row in selected_rows[:63]
    ]
    _write_events(events, [*lower_priority_rows, *selected_rows])
    history = tmp_path / "history" / "ohlcv"
    history.mkdir(parents=True)
    config = Backtest3AConfig(input_events_path=events, output_dir=tmp_path / "out", history_root=history, path_bars=1)

    event_df, _bar_df, summary, _report, _ = build_exit_path_metrics(config)

    assert summary["counts"]["input_rows_before_deduplication"] == 291
    assert summary["counts"]["output_rows_after_deduplication"] == 228
    assert summary["counts"]["duplicate_event_id_count"] == 63
    assert summary["counts"]["discarded_duplicate_row_count"] == 63
    assert summary["counts"]["conflicting_duplicate_event_id_count"] == 0
    assert summary["counts"]["primary_scope_rows"] == 228
    assert len(event_df) == 228
