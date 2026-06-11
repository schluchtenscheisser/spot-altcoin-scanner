from __future__ import annotations

import sqlite3

import pytest

from scanner.features.models import FeatureBundle
from scanner.runners.intraday import _create_run_metadata, _latest_completed_intraday_bar_id
from scanner.state.models import InvalidationCycleBundle, StateMachineBundle
from scanner.storage import init_db


def test_model_annotations_use_string_intraday_ids() -> None:
    assert FeatureBundle.__annotations__["intraday_bar_id"] == "str | None"
    assert InvalidationCycleBundle.__annotations__["intraday_bar_id"] == "str | None"
    assert StateMachineBundle.__annotations__["intraday_bar_id"] == "str | None"


def test_run_metadata_roundtrip_uses_canonical_intraday_id_string(tmp_path) -> None:
    conn = init_db(tmp_path / "independence_release.sqlite")
    _create_run_metadata(
        conn,
        run_id="intraday-run-1",
        daily_id="2026-04-23",
        intraday_id="2026-04-24T08:00:00Z",
        scan_mode="intraday_promotion",
    )
    conn.execute(
        "UPDATE run_metadata SET status='completed', finished_at_utc='2026-04-24T09:01:00Z' WHERE run_id='intraday-run-1'"
    )
    conn.commit()

    got = _latest_completed_intraday_bar_id(conn)
    assert got == "2026-04-24T08:00:00Z"
    conn.close()


def test_run_metadata_new_integer_intraday_id_write_fails_fast(tmp_path) -> None:
    conn = init_db(tmp_path / "independence_release.sqlite")
    with pytest.raises(TypeError, match="intraday_bar_id"):
        _create_run_metadata(
            conn,
            run_id="intraday-run-legacy-write",
            daily_id="2026-04-23",
            intraday_id=1774324800000,  # type: ignore[arg-type]
            scan_mode="intraday_promotion",
        )
    conn.close()


def test_run_metadata_new_digit_string_intraday_id_write_fails_fast(tmp_path) -> None:
    conn = init_db(tmp_path / "independence_release.sqlite")
    with pytest.raises(ValueError, match="current_bar_id"):
        _create_run_metadata(
            conn,
            run_id="intraday-run-legacy-digit-write",
            daily_id="2026-04-23",
            intraday_id="1774324800000",
            scan_mode="intraday_promotion",
        )
    conn.close()


def test_legacy_integer_row_is_converted_only_at_read_boundary(tmp_path) -> None:
    conn = sqlite3.connect(tmp_path / "legacy.sqlite")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE run_metadata (
            run_id TEXT PRIMARY KEY,
            scan_mode TEXT NOT NULL,
            started_at_utc TEXT NOT NULL,
            finished_at_utc TEXT,
            daily_bar_id TEXT NOT NULL,
            intraday_bar_id INTEGER,
            schema_version INTEGER NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "legacy-run",
            "intraday",
            "2026-04-24T09:00:00Z",
            "2026-04-24T09:01:00Z",
            "2026-04-23",
            1774324800000,
            4,
            "completed",
        ),
    )
    conn.commit()

    assert _latest_completed_intraday_bar_id(conn) == "2026-03-24T04:00:00Z"
    conn.close()


def test_legacy_digit_string_row_is_converted_only_at_read_boundary(tmp_path) -> None:
    conn = sqlite3.connect(tmp_path / "legacy_digit.sqlite")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE run_metadata (
            run_id TEXT PRIMARY KEY,
            scan_mode TEXT NOT NULL,
            started_at_utc TEXT NOT NULL,
            finished_at_utc TEXT,
            daily_bar_id TEXT NOT NULL,
            intraday_bar_id TEXT,
            schema_version INTEGER NOT NULL,
            status TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "legacy-digit-run",
            "intraday",
            "2026-04-24T09:00:00Z",
            "2026-04-24T09:01:00Z",
            "2026-04-23",
            "1774324800000",
            4,
            "completed",
        ),
    )
    conn.commit()

    assert _latest_completed_intraday_bar_id(conn) == "2026-03-24T04:00:00Z"
    conn.close()
