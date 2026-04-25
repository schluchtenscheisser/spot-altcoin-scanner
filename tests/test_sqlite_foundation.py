import sqlite3

import pytest

from scanner.storage import SCHEMA_VERSION, get_schema_version, init_db


def test_sqlite_bootstrap_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "independence_release.sqlite"

    connection = init_db(db_path)
    connection.close()

    second_connection = init_db(db_path)
    assert get_schema_version(second_connection) == SCHEMA_VERSION
    assert second_connection.execute("PRAGMA journal_mode;").fetchone()[0].lower() == "wal"
    second_connection.close()


def test_run_metadata_schema_and_nullable_fields(tmp_path) -> None:
    db_path = tmp_path / "independence_release.sqlite"
    connection = init_db(db_path)

    table_sql = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='run_metadata'"
    ).fetchone()[0]
    assert "finished_at_utc TEXT" in table_sql
    assert "intraday_bar_id TEXT" in table_sql
    assert "scan_mode IN ('daily_discovery', 'intraday_promotion')" in table_sql
    assert "status IN ('running', 'completed', 'failed')" in table_sql

    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            "run-1",
            "daily_discovery",
            "2026-03-24T00:00:00Z",
            None,
            "2026-03-23",
            None,
            SCHEMA_VERSION,
            "running",
        ),
    )
    connection.commit()

    row = connection.execute(
        "SELECT finished_at_utc, intraday_bar_id FROM run_metadata WHERE run_id = ?",
        ("run-1",),
    ).fetchone()
    assert row[0] is None
    assert row[1] is None

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO run_metadata (
                run_id, scan_mode, started_at_utc, finished_at_utc,
                daily_bar_id, intraday_bar_id, schema_version, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "run-2",
                "invalid",
                "2026-03-24T00:00:00Z",
                None,
                "2026-03-23",
                None,
                SCHEMA_VERSION,
                "running",
            ),
        )

    connection.close()
