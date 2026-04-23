from datetime import date

import pytest

from scanner.storage import (
    build_ohlcv_history_partition_dir,
    build_run_manifest_path,
    build_run_snapshot_dir,
    is_month_open,
    month_mutability_policy,
)


def test_history_partition_dir_for_1d_and_4h_is_canonical() -> None:
    assert build_ohlcv_history_partition_dir(
        timeframe="1d",
        symbol="TAOUSDT",
        year=2026,
        month=3,
    ) == "snapshots/history/ohlcv/timeframe=1d/symbol=TAOUSDT/year=2026/month=03/"

    assert build_ohlcv_history_partition_dir(
        timeframe="4h",
        symbol="TAOUSDT",
        year=2026,
        month=3,
    ) == "snapshots/history/ohlcv/timeframe=4h/symbol=TAOUSDT/year=2026/month=03/"


def test_timeframe_validation_accepts_only_1d_and_4h() -> None:
    build_ohlcv_history_partition_dir(timeframe="1d", symbol="BTCUSDT", year=2026, month=1)
    build_ohlcv_history_partition_dir(timeframe="4h", symbol="BTCUSDT", year=2026, month=1)

    with pytest.raises(ValueError, match="timeframe"):
        build_ohlcv_history_partition_dir(timeframe="1h", symbol="BTCUSDT", year=2026, month=1)


def test_symbol_rejects_path_traversal_and_separators() -> None:
    for value in ("../x", "A/B", "A\\B"):
        with pytest.raises(ValueError, match="symbol"):
            build_ohlcv_history_partition_dir(timeframe="1d", symbol=value, year=2026, month=1)


def test_month_open_closed_and_mutability_policy() -> None:
    assert is_month_open(year=2026, month=3, reference_date=date(2026, 3, 15)) is True
    assert is_month_open(year=2026, month=3, reference_date=date(2026, 4, 1)) is False

    open_policy = month_mutability_policy(year=2026, month=3, reference_date=date(2026, 3, 15))
    assert open_policy.is_open is True
    assert open_policy.mutable_in_normal_operation is True
    assert open_policy.targeted_repair_allowed is True

    closed_policy = month_mutability_policy(year=2026, month=3, reference_date=date(2026, 4, 1))
    assert closed_policy.is_open is False
    assert closed_policy.mutable_in_normal_operation is False
    assert closed_policy.targeted_repair_allowed is True


def test_run_manifest_path_is_derived_from_daily_bar_id_and_repo_relative() -> None:
    path = build_run_manifest_path(daily_bar_id="2026-04-23", run_id="example-run-id")
    assert path == "snapshots/runs/2026/04/23/example-run-id/run.manifest.json"
    assert not path.startswith("/")


def test_manifest_path_derivation_does_not_require_file_existence() -> None:
    path = build_run_manifest_path(daily_bar_id="2026-04-23", run_id="not-created-yet")
    assert path.endswith("/run.manifest.json")


def test_run_snapshot_dir_helper_is_deterministic() -> None:
    path1 = build_run_snapshot_dir(daily_bar_id="2026-04-23", run_id="run-a")
    path2 = build_run_snapshot_dir(daily_bar_id="2026-04-23", run_id="run-a")
    assert path1 == path2
