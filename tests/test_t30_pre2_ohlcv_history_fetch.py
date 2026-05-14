from __future__ import annotations

import gzip
import json
from argparse import Namespace
from pathlib import Path

import pandas as pd
import pytest

from scripts.fetch_ohlcv_history_for_evaluation import (
    collect_symbol_universe,
    fetch_and_write_history,
    normalize_klines,
    write_ohlcv_partitions,
)


class FakeMEXCClient:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls = []

    def get_klines(self, symbol, interval="1d", limit=1000, use_cache=True):
        self.calls.append({"symbol": symbol, "interval": interval, "limit": limit, "use_cache": use_cache})
        payload = self.payloads[symbol]
        if isinstance(payload, Exception):
            raise payload
        return payload


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_diag(path: Path, records) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _report(root: Path, day: str, run_id: str, symbol_lists: dict) -> Path:
    y, m, d = day.split("-")
    path = root / "reports" / "runs" / y / m / d / run_id / "report.json"
    _write_json(path, {"schema_version": "ir1.5", "symbol_lists": symbol_lists})
    return path


def _args(tmp_path: Path, **overrides) -> Namespace:
    values = {
        "project_root": str(tmp_path),
        "reports_root": "reports/runs",
        "snapshots_runs_root": "snapshots/runs",
        "history_root": "snapshots/history",
        "start_date": "2026-05-03",
        "end_date": "2026-05-04",
        "horizons": "1,3,5,10",
        "include_buckets": "confirmed_candidates,early_candidates",
        "symbol_source": "auto",
        "output_summary": "evaluation/replay/ohlcv_history_fetch_summary.json",
        "output_symbols": "evaluation/replay/ohlcv_history_symbols.json",
        "dry_run": False,
        "use_cache": True,
        "max_symbols": None,
        "force_refetch": False,
        "fail_on_empty_universe": False,
        "mexc_limit": 1000,
    }
    values.update(overrides)
    return Namespace(**values)


def _kline(day: str, close: str = "1.4"):
    ts = int(pd.Timestamp(f"{day}T00:00:00Z").timestamp() * 1000)
    close_ts = int(pd.Timestamp(f"{day}T23:59:59Z").timestamp() * 1000)
    return [ts, "1.0", "1.5", "0.9", close, "100", close_ts, "140"]


def test_symbol_extraction_from_report_lists(tmp_path: Path):
    reports_root = tmp_path / "reports" / "runs"
    _report(
        tmp_path,
        "2026-05-03",
        "daily-a",
        {
            "confirmed_candidates": ["INJUSDT"],
            "early_candidates": ["ABCUSDT"],
            "watchlist": ["SHOULDNOTINCLUDEUSDT"],
        },
    )
    _report(
        tmp_path,
        "2026-05-04",
        "daily-b",
        {
            "confirmed_candidates": [{"symbol": "OBJUSDT"}],
            "early_candidates": [],
            "watchlist": ["NOPEUSDT"],
        },
    )

    universe = collect_symbol_universe(
        reports_root=reports_root,
        start_date="2026-05-03",
        end_date="2026-05-04",
        include_buckets=["confirmed_candidates", "early_candidates"],
        symbol_source="reports",
    )

    assert universe.symbols == ["ABCUSDT", "INJUSDT", "OBJUSDT"]
    assert "SHOULDNOTINCLUDEUSDT" not in universe.symbols
    assert universe.skipped_runs == []


def test_symbol_extraction_from_nested_diagnostics_without_tradeability(tmp_path: Path):
    report_path = _report(
        tmp_path,
        "2026-05-03",
        "daily-a",
        {"confirmed_candidates": [], "early_candidates": []},
    )
    _write_diag(
        report_path.with_name("symbol_diagnostics.jsonl.gz"),
        [
            {"symbol": "INJUSDT", "decision": {"decision_bucket": "confirmed_candidates"}},
            {"symbol": "ABCUSDT", "decision": {"decision_bucket": "early_candidates"}},
            {"symbol": "WATCHUSDT", "decision": {"decision_bucket": "watchlist"}},
            {"symbol": "LATEUSDT", "decision": {"decision_bucket": "late_monitor"}},
            {"symbol": "DROPUSDT", "decision": {"decision_bucket": "discarded"}},
        ],
    )

    universe = collect_symbol_universe(
        reports_root=tmp_path / "reports" / "runs",
        start_date="2026-05-03",
        end_date="2026-05-03",
        include_buckets=["confirmed_candidates", "early_candidates"],
        symbol_source="diagnostics",
    )

    assert universe.symbols == ["ABCUSDT", "INJUSDT"]
    assert universe.source_counts["diagnostics"] == 1


def test_auto_mode_prefers_diagnostics_and_falls_back_to_reports(tmp_path: Path):
    diag_report = _report(
        tmp_path,
        "2026-05-03",
        "daily-a",
        {"confirmed_candidates": ["REPORTSHOULDNOTWINUSDT"], "early_candidates": []},
    )
    _write_diag(
        diag_report.with_name("symbol_diagnostics.jsonl.gz"),
        [{"symbol": "DIAGUSDT", "decision": {"decision_bucket": "confirmed_candidates"}}],
    )
    _report(
        tmp_path,
        "2026-05-04",
        "daily-b",
        {"confirmed_candidates": [], "early_candidates": ["FALLBACKUSDT"]},
    )
    bad = tmp_path / "reports" / "runs" / "2026" / "05" / "04" / "bad" / "report.json"
    bad.parent.mkdir(parents=True)
    bad.write_text("not-json", encoding="utf-8")

    universe = collect_symbol_universe(
        reports_root=tmp_path / "reports" / "runs",
        start_date="2026-05-03",
        end_date="2026-05-04",
        include_buckets=["confirmed_candidates", "early_candidates"],
        symbol_source="auto",
    )

    assert universe.symbols == ["DIAGUSDT", "FALLBACKUSDT"]
    assert universe.source_counts == {"reports": 1, "diagnostics": 1}
    assert universe.skipped_runs == [
        {"path": bad.as_posix(), "reason": "missing_or_invalid_report"}
    ]


def test_kline_normalization_outputs_required_columns_and_drops_invalid_rows():
    rows, invalid_count = normalize_klines(
        "INJUSDT",
        [
            _kline("2026-05-03"),
            _kline("2026-05-04", close="not-a-number"),
            _kline("2026-05-05", close="0"),
            [pd.Timestamp("2026-05-06T00:00:00Z").timestamp() * 1000, "1", "-1", "1", "1", "1"],
            _kline("2026-05-07", close="NaN"),
            _kline("2026-05-08", close="inf"),
        ],
        start_date="2026-05-03",
        fetch_end_date="2026-05-10",
        fetched_at_utc="2026-05-14T00:00:00Z",
    )

    assert list(rows.columns) == [
        "symbol",
        "timeframe",
        "daily_bar_id",
        "open_time_utc_ms",
        "close_time_utc_ms",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "source",
        "fetched_at_utc",
    ]
    assert rows["daily_bar_id"].tolist() == ["2026-05-03"]
    assert rows.loc[0, "source"] == "mexc_spot_klines"
    assert invalid_count == 5


def test_parquet_partition_layout_and_idempotent_dedup(tmp_path: Path):
    bars, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-03"), _kline("2026-05-03"), _kline("2026-05-04")],
        start_date="2026-05-03",
        fetch_end_date="2026-05-04",
        fetched_at_utc="2026-05-14T00:00:00Z",
    )
    history_root = tmp_path / "snapshots" / "history"

    first = write_ohlcv_partitions(history_root, "INJUSDT", bars)
    second = write_ohlcv_partitions(history_root, "INJUSDT", bars)

    expected = history_root / "ohlcv" / "timeframe=1d" / "symbol=INJUSDT" / "year=2026" / "month=05" / "part-000.parquet"
    assert first["partition_paths"] == [expected.as_posix()]
    assert first["new_row_count"] == 2
    assert second["partition_paths"] == []
    assert second["new_row_count"] == 0
    assert second["existing_duplicate_row_count"] == 2
    stored = pd.read_parquet(expected)
    assert stored["daily_bar_id"].tolist() == ["2026-05-03", "2026-05-04"]
    assert not stored["daily_bar_id"].duplicated().any()


def test_existing_partition_merge_keeps_existing_overlap_without_force_and_replaces_with_force(tmp_path: Path):
    history_root = tmp_path / "snapshots" / "history"
    existing, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-03", close="1.4")],
        start_date="2026-05-03",
        fetch_end_date="2026-05-03",
        fetched_at_utc="2026-05-14T00:00:00Z",
    )
    fetched, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-03", close="9.9"), _kline("2026-05-04", close="2.4")],
        start_date="2026-05-03",
        fetch_end_date="2026-05-04",
        fetched_at_utc="2026-05-15T00:00:00Z",
    )

    write_ohlcv_partitions(history_root, "INJUSDT", existing)
    write_ohlcv_partitions(history_root, "INJUSDT", fetched, force_refetch=False)
    path = history_root / "ohlcv" / "timeframe=1d" / "symbol=INJUSDT" / "year=2026" / "month=05" / "part-000.parquet"
    stored = pd.read_parquet(path)
    assert stored["daily_bar_id"].tolist() == ["2026-05-03", "2026-05-04"]
    assert stored.loc[stored["daily_bar_id"] == "2026-05-03", "close"].iloc[0] == 1.4

    write_ohlcv_partitions(history_root, "INJUSDT", fetched, force_refetch=True)
    stored = pd.read_parquet(path)
    assert stored.loc[stored["daily_bar_id"] == "2026-05-03", "close"].iloc[0] == 9.9


def test_fetch_drops_in_progress_daily_candle_before_writing(tmp_path: Path):
    _report(tmp_path, "2026-05-12", "daily-a", {"confirmed_candidates": ["INJUSDT"], "early_candidates": []})
    client = FakeMEXCClient({"INJUSDT": [_kline("2026-05-12"), _kline("2026-05-13"), _kline("2026-05-14")]})

    exit_code, summary, _ = fetch_and_write_history(
        _args(tmp_path, start_date="2026-05-12", end_date="2026-05-14"),
        client=client,
        now_utc="2026-05-14T10:00:00Z",
    )

    path = tmp_path / "snapshots" / "history" / "ohlcv" / "timeframe=1d" / "symbol=INJUSDT" / "year=2026" / "month=05" / "part-000.parquet"
    stored = pd.read_parquet(path)
    assert exit_code == 0
    assert stored["daily_bar_id"].tolist() == ["2026-05-12", "2026-05-13"]
    assert summary["per_symbol"]["INJUSDT"]["status"] == "fetched"
    assert summary["per_symbol"]["INJUSDT"]["new_row_count"] == 2
    assert summary["per_symbol"]["INJUSDT"]["bars_written"] == 2
    assert summary["symbols_with_new_history"] == 1


def test_duplicate_only_fetch_is_reported_as_skipped_existing_complete(tmp_path: Path):
    _report(tmp_path, "2026-05-12", "daily-a", {"confirmed_candidates": ["INJUSDT"], "early_candidates": []})
    history_root = tmp_path / "snapshots" / "history"
    existing, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-12"), _kline("2026-05-13")],
        start_date="2026-05-12",
        fetch_end_date="2026-05-13",
        fetched_at_utc="2026-05-14T00:00:00Z",
        now_utc="2026-05-14T10:00:00Z",
    )
    write_ohlcv_partitions(history_root, "INJUSDT", existing)
    client = FakeMEXCClient({"INJUSDT": [_kline("2026-05-12"), _kline("2026-05-13")]})

    exit_code, summary, _ = fetch_and_write_history(
        _args(tmp_path, start_date="2026-05-12", end_date="2026-05-13"),
        client=client,
        now_utc="2026-05-14T10:00:00Z",
    )

    per_symbol = summary["per_symbol"]["INJUSDT"]
    assert exit_code == 0
    assert per_symbol["status"] == "skipped_existing_complete"
    assert per_symbol["new_row_count"] == 0
    assert per_symbol["existing_duplicate_row_count"] == 2
    assert per_symbol["partition_paths"] == []
    assert summary["symbols_with_new_history"] == 0


def test_partial_new_fetch_counts_only_new_daily_bar_ids(tmp_path: Path):
    _report(tmp_path, "2026-05-12", "daily-a", {"confirmed_candidates": ["INJUSDT"], "early_candidates": []})
    history_root = tmp_path / "snapshots" / "history"
    existing, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-12")],
        start_date="2026-05-12",
        fetch_end_date="2026-05-12",
        fetched_at_utc="2026-05-14T00:00:00Z",
        now_utc="2026-05-14T10:00:00Z",
    )
    write_ohlcv_partitions(history_root, "INJUSDT", existing)
    client = FakeMEXCClient({"INJUSDT": [_kline("2026-05-12"), _kline("2026-05-13")]})

    exit_code, summary, _ = fetch_and_write_history(
        _args(tmp_path, start_date="2026-05-12", end_date="2026-05-13"),
        client=client,
        now_utc="2026-05-14T10:00:00Z",
    )

    per_symbol = summary["per_symbol"]["INJUSDT"]
    assert exit_code == 0
    assert per_symbol["status"] == "fetched"
    assert per_symbol["new_row_count"] == 1
    assert per_symbol["existing_duplicate_row_count"] == 1
    assert summary["symbols_with_new_history"] == 1


def test_force_refetch_duplicate_refresh_is_not_counted_as_new_history(tmp_path: Path):
    _report(tmp_path, "2026-05-12", "daily-a", {"confirmed_candidates": ["INJUSDT"], "early_candidates": []})
    history_root = tmp_path / "snapshots" / "history"
    existing, _ = normalize_klines(
        "INJUSDT",
        [_kline("2026-05-12", close="1.4")],
        start_date="2026-05-12",
        fetch_end_date="2026-05-12",
        fetched_at_utc="2026-05-14T00:00:00Z",
        now_utc="2026-05-14T10:00:00Z",
    )
    write_ohlcv_partitions(history_root, "INJUSDT", existing)
    client = FakeMEXCClient({"INJUSDT": [_kline("2026-05-12", close="9.9")]})

    exit_code, summary, _ = fetch_and_write_history(
        _args(tmp_path, start_date="2026-05-12", end_date="2026-05-12", force_refetch=True),
        client=client,
        now_utc="2026-05-14T10:00:00Z",
    )

    path = history_root / "ohlcv" / "timeframe=1d" / "symbol=INJUSDT" / "year=2026" / "month=05" / "part-000.parquet"
    stored = pd.read_parquet(path)
    per_symbol = summary["per_symbol"]["INJUSDT"]
    assert exit_code == 0
    assert per_symbol["status"] == "refreshed_existing"
    assert per_symbol["new_row_count"] == 0
    assert per_symbol["replaced_row_count"] >= 1
    assert summary["symbols_with_new_history"] == 0
    assert summary["symbols_refreshed_existing"] == 1
    assert stored.loc[stored["daily_bar_id"] == "2026-05-12", "close"].iloc[0] == 9.9


def test_empty_universe_writes_summary_and_fail_option_controls_exit(tmp_path: Path):
    _report(tmp_path, "2026-05-03", "daily-a", {"confirmed_candidates": [], "early_candidates": []})

    exit_code, summary, symbols = fetch_and_write_history(_args(tmp_path, dry_run=True))
    assert exit_code == 0
    assert summary["symbol_count"] == 0
    assert symbols["symbols"] == []
    assert not (tmp_path / "snapshots" / "history" / "ohlcv").exists()

    fail_code, _, _ = fetch_and_write_history(_args(tmp_path, dry_run=True, fail_on_empty_universe=True))
    assert fail_code == 2


def test_cli_dry_run_extracts_symbols_writes_summary_and_does_not_call_mexc_or_write_parquet(tmp_path: Path):
    _report(tmp_path, "2026-05-03", "daily-a", {"confirmed_candidates": ["INJUSDT"], "early_candidates": []})
    client = FakeMEXCClient({"INJUSDT": [_kline("2026-05-03")]})

    exit_code, summary, symbols = fetch_and_write_history(_args(tmp_path, dry_run=True), client=client)

    assert exit_code == 0
    assert symbols["symbols"] == ["INJUSDT"]
    assert summary["per_symbol"]["INJUSDT"]["status"] == "skipped_existing_complete"
    assert client.calls == []
    assert not (tmp_path / "snapshots" / "history" / "ohlcv").exists()


def test_fetch_and_write_records_no_valid_bars_and_fetch_failures(tmp_path: Path):
    _report(
        tmp_path,
        "2026-05-03",
        "daily-a",
        {"confirmed_candidates": ["BADUSDT", "FAILUSDT"], "early_candidates": []},
    )
    client = FakeMEXCClient({"BADUSDT": [_kline("2026-05-03", close="0")], "FAILUSDT": RuntimeError("boom")})

    exit_code, summary, _ = fetch_and_write_history(_args(tmp_path), client=client)

    assert exit_code == 0
    assert summary["per_symbol"]["BADUSDT"]["status"] == "no_valid_bars"
    assert summary["per_symbol"]["FAILUSDT"]["status"] == "fetch_failed"
    assert summary["symbols_without_valid_bars"] == 1
    assert summary["invalid_bar_count"] == 1


def test_no_git_persistence_regression_guardrails():
    gitignore = Path(".gitignore").read_text(encoding="utf-8")
    persist = Path("scripts/persist_shadow_live_reports.py").read_text(encoding="utf-8")

    assert "snapshots/history/ohlcv/" in gitignore
    assert "snapshots/history/ohlcv/**" in gitignore or "snapshots/**/*.parquet" in gitignore
    assert "snapshots/history" not in persist
