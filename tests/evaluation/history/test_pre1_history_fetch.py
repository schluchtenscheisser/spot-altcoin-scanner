from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd
import pytest

from scanner.evaluation.history.history_fetch_config import HistoryFetchConfig
from scanner.evaluation.history.ohlcv_history_fetch import run_history_fetch
from scanner.evaluation.history.parquet_store import load_symbol_timeframe
from scanner.evaluation.history.symbol_intersection import resolve_universe


class FakeBinanceClient:
    def __init__(self, symbols, klines=None, errors=None):
        self.symbols = symbols
        self.klines = klines or {}
        self.errors = errors or {}
        self.calls = []

    def get_spot_usdt_symbols(self):
        return list(self.symbols)

    def get_klines(self, symbol, interval, *, start_time_ms=None, end_time_ms=None, limit=1000):
        self.calls.append((symbol, interval, start_time_ms, end_time_ms, limit))
        if symbol in self.errors:
            raise RuntimeError(self.errors[symbol])
        rows = self.klines.get((symbol, interval), [])
        return [row for row in rows if (start_time_ms is None or row[0] >= start_time_ms) and (end_time_ms is None or row[0] <= end_time_ms)][:limit]


def ms(value: str) -> int:
    return int(datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)


def kline(open_iso: str, *, timeframe="1d", close="1.0"):
    duration = 86_400_000 if timeframe == "1d" else 14_400_000
    open_ms = ms(open_iso)
    return [open_ms, "1.0", "2.0", "0.5", close, "10", open_ms + duration - 1, "100", 7]


def cfg(tmp_path: Path, **overrides) -> HistoryFetchConfig:
    params = {
        "fetch_start_date": "2025-01-01",
        "fetch_end_date": "2025-01-02",
        "evaluation_start_date": "2025-01-01",
        "output_root": tmp_path / "ohlcv",
        "manifest_root": tmp_path / "manifests",
        "universe_mode": "binance_spot_usdt_all",
        "runtime_utc": datetime(2025, 1, 3, 12, tzinfo=timezone.utc),
    }
    params.update(overrides)
    return HistoryFetchConfig.resolve(**params)


def test_default_date_resolution():
    resolved = HistoryFetchConfig.resolve(runtime_utc=datetime(2026, 5, 18, 10, tzinfo=timezone.utc))
    assert resolved.fetch_start_date == date(2025, 1, 1)
    assert resolved.evaluation_start_date == date(2025, 5, 1)
    assert resolved.fetch_end_date_requested == "auto_last_closed_daily_bar"
    assert resolved.effective_fetch_end_date == date(2026, 5, 17)
    assert resolved.evaluation_end_date == resolved.effective_fetch_end_date


def test_evaluation_dates_are_manifest_only_and_do_not_change_fetch_calls(tmp_path):
    client1 = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): []})
    out1 = run_history_fetch(cfg(tmp_path / "a", evaluation_start_date="2025-01-01"), client=client1, fetch_run_id="r1")
    client2 = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): []})
    out2 = run_history_fetch(cfg(tmp_path / "b", evaluation_start_date="2025-01-02"), client=client2, fetch_run_id="r2")
    assert [(c[0], c[1], c[2], c[3]) for c in client1.calls] == [(c[0], c[1], c[2], c[3]) for c in client2.calls]
    assert out1.history_manifest["evaluation_start_date"] == "2025-01-01"
    assert out2.history_manifest["evaluation_start_date"] == "2025-01-02"


@pytest.mark.parametrize("bad", ["2025-13-01", "2025-01-01T12:00:00Z"])
def test_invalid_dates_are_rejected(bad):
    with pytest.raises(ValueError):
        HistoryFetchConfig.resolve(fetch_start_date=bad)
    with pytest.raises(ValueError):
        HistoryFetchConfig.resolve(fetch_start_date="2025-01-03", fetch_end_date="2025-01-02")


def test_closed_bar_only_filtering(tmp_path):
    client = FakeBinanceClient(
        ["AAAUSDT"],
        {("AAAUSDT", "4h"): [kline("2025-01-02T04:00:00Z", timeframe="4h"), kline("2025-01-02T12:00:00Z", timeframe="4h")], ("AAAUSDT", "1d"): []},
    )
    out = run_history_fetch(cfg(tmp_path, timeframes=("4h",), runtime_utc=datetime(2025, 1, 2, 9, tzinfo=timezone.utc)), client=client, fetch_run_id="r")
    assert len(out.rows) == 1
    assert out.rows.iloc[0]["open_time_utc"] == "2025-01-02T04:00:00Z"
    assert out.rows["is_closed"].eq(True).all()
    assert out.history_manifest["closed_bar_only"] is True


def test_no_duplicate_rows_and_incremental_append(tmp_path):
    client = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): []})
    run_history_fetch(cfg(tmp_path, timeframes=("1d",)), client=client, fetch_run_id="r1")
    run_history_fetch(cfg(tmp_path, timeframes=("1d",)), client=client, fetch_run_id="r2")
    stored = load_symbol_timeframe(tmp_path / "ohlcv", "AAAUSDT", "1d")
    assert len(stored) == 1
    assert stored.duplicated(["source", "symbol", "timeframe", "open_time_utc"]).sum() == 0

    later = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z"), kline("2025-01-02T00:00:00Z")], ("AAAUSDT", "4h"): []})
    out = run_history_fetch(cfg(tmp_path, fetch_end_date="2025-01-03", timeframes=("1d",), runtime_utc=datetime(2025, 1, 4, 1, tzinfo=timezone.utc)), client=later, fetch_run_id="r3")
    stored = load_symbol_timeframe(tmp_path / "ohlcv", "AAAUSDT", "1d")
    assert len(stored) == 2
    assert out.history_manifest["incremental_update_summary"]["existing_partitions_detected"] >= 1


def test_closed_partition_immutability_and_force_repair(tmp_path):
    jan = {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z", close="1.0")], ("AAAUSDT", "4h"): []}
    run_history_fetch(cfg(tmp_path, fetch_end_date="2025-02-02", timeframes=("1d",), runtime_utc=datetime(2025, 2, 3, tzinfo=timezone.utc)), client=FakeBinanceClient(["AAAUSDT"], jan), fetch_run_id="r1")
    changed = {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z", close="9.0")], ("AAAUSDT", "4h"): []}
    normal = run_history_fetch(cfg(tmp_path, fetch_end_date="2025-02-02", timeframes=("1d",), runtime_utc=datetime(2025, 2, 3, tzinfo=timezone.utc)), client=FakeBinanceClient(["AAAUSDT"], changed), fetch_run_id="r2")
    stored = load_symbol_timeframe(tmp_path / "ohlcv", "AAAUSDT", "1d")
    assert float(stored.iloc[0]["close"]) == 1.0
    assert normal.history_manifest["partitions_skipped_existing"]

    repaired = run_history_fetch(cfg(tmp_path, fetch_end_date="2025-02-02", timeframes=("1d",), runtime_utc=datetime(2025, 2, 3, tzinfo=timezone.utc), force_repair=True), client=FakeBinanceClient(["AAAUSDT"], changed), fetch_run_id="r3")
    stored = load_symbol_timeframe(tmp_path / "ohlcv", "AAAUSDT", "1d")
    assert float(stored.iloc[0]["close"]) == 9.0
    assert repaired.history_manifest["partitions_repaired"]


def test_universe_modes_and_exclusion_reasons(tmp_path):
    fixed = resolve_universe(
        universe_mode="fixed_current_mexc_binance_intersection",
        binance_symbols=["AAAUSDT", "BBBUSDT"],
        mexc_symbols=["BBB_USDT", "AAAUSDT", "CCCUSDT", "DUP_USDT", "DUPUSDT", "BAD"],
    )
    assert fixed.source_mexc_symbol_count == 6
    assert fixed.included_symbols == ["AAAUSDT", "BBBUSDT"]
    reasons = [item.reason for item in fixed.excluded_symbols]
    assert "mexc_only" in reasons
    assert "normalization_mismatch" in reasons

    all_mode = resolve_universe(universe_mode="binance_spot_usdt_all", binance_symbols=["BBBUSDT", "AAAUSDT"])
    assert all_mode.source_mexc_symbol_count is None
    assert all_mode.included_symbols == ["AAAUSDT", "BBBUSDT"]
    assert not all_mode.excluded_symbols

    client = FakeBinanceClient(["AAAUSDT", "EMPTYUSDT", "ERRUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): [], ("EMPTYUSDT", "1d"): [], ("EMPTYUSDT", "4h"): []}, errors={"ERRUSDT": "boom"})
    out = run_history_fetch(cfg(tmp_path, timeframes=("1d",), universe_mode="binance_spot_usdt_all"), client=client, fetch_run_id="r")
    excluded = {item["source_symbol"]: item["reason"] for item in out.universe_manifest["excluded_symbols"]}
    assert excluded["EMPTYUSDT"] == "no_binance_history"
    assert excluded["AAAUSDT"] == "insufficient_history"
    assert excluded["ERRUSDT"] == "fetch_error"
    assert out.universe_manifest["source_mexc_symbol_count"] is None
    assert out.universe_manifest["excluded_counts"]["mexc_only"] == 0


def test_manifests_are_separate_and_written(tmp_path):
    client = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): []})
    run_history_fetch(cfg(tmp_path), client=client, fetch_run_id="r")
    history = json.loads((tmp_path / "manifests" / "history_manifest.json").read_text())
    universe = json.loads((tmp_path / "manifests" / "universe_manifest.json").read_text())
    completeness = json.loads((tmp_path / "manifests" / "symbol_completeness.json").read_text())
    assert history["manifest_type"] == "history_manifest"
    assert universe["manifest_type"] == "universe_manifest"
    assert completeness["manifest_type"] == "symbol_completeness"
    assert "bar_counts_by_symbol_timeframe" in completeness
    assert "included_symbols" not in history


def test_dry_run_writes_no_artifacts(tmp_path):
    client = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): []})
    out = run_history_fetch(cfg(tmp_path), client=client, fetch_run_id="r", dry_run=True)
    assert out.history_manifest["fetch_run_id"] == "r"
    assert not (tmp_path / "ohlcv").exists()
    assert not (tmp_path / "manifests").exists()


def test_deterministic_ordering(tmp_path):
    client = FakeBinanceClient(["ZZZUSDT", "AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-02T00:00:00Z"), kline("2025-01-01T00:00:00Z")], ("AAAUSDT", "4h"): [], ("ZZZUSDT", "1d"): [kline("2025-01-01T00:00:00Z")], ("ZZZUSDT", "4h"): []})
    out = run_history_fetch(cfg(tmp_path, timeframes=("1d",)), client=client, fetch_run_id="r")
    assert out.universe_manifest["included_symbols"] == ["AAAUSDT", "ZZZUSDT"]
    assert list(out.rows["symbol"]) == ["AAAUSDT", "AAAUSDT", "ZZZUSDT"]
    assert list(out.rows[out.rows["symbol"] == "AAAUSDT"]["open_time_utc"]) == ["2025-01-01T00:00:00Z", "2025-01-02T00:00:00Z"]


def test_numeric_robustness_records_issue_and_does_not_write_bad_row(tmp_path):
    client = FakeBinanceClient(["AAAUSDT"], {("AAAUSDT", "1d"): [kline("2025-01-01T00:00:00Z", close="NaN")], ("AAAUSDT", "4h"): []})
    out = run_history_fetch(cfg(tmp_path, timeframes=("1d",)), client=client, fetch_run_id="r")
    assert out.rows.empty
    assert out.history_manifest["data_quality_issues"]
