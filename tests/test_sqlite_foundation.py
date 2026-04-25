import sqlite3

import pytest

from scanner.storage import SCHEMA_VERSION, apply_schema, get_schema_version, init_db


def _create_legacy_run_metadata_table(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE run_metadata (
            run_id          TEXT PRIMARY KEY,
            scan_mode       TEXT NOT NULL CHECK (scan_mode IN ('daily_discovery', 'intraday_promotion', 'standard', 'fast', 'offline', 'backtest')),
            started_at_utc  TEXT NOT NULL,
            finished_at_utc TEXT,
            daily_bar_id    TEXT NOT NULL,
            intraday_bar_id TEXT,
            schema_version  INTEGER NOT NULL,
            status          TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
            eligible_pre_1d_count INTEGER NOT NULL DEFAULT 0,
            activity_gate_passed_count INTEGER NOT NULL DEFAULT 0,
            monitoring_bypass_count INTEGER NOT NULL DEFAULT 0,
            selected_for_4h_count INTEGER NOT NULL DEFAULT 0
        )
        """
    )


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
    assert "scan_mode IN ('daily', 'intraday')" in table_sql
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
            "daily",
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


def test_run_metadata_scan_mode_migration_from_legacy_constraint(tmp_path) -> None:
    db_path = tmp_path / "legacy.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON;")
    _create_legacy_run_metadata_table(connection)
    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("legacy-d", "daily_discovery", "2026-03-24T00:00:00Z", None, "2026-03-23", None, 4, "completed"),
    )
    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("legacy-i", "intraday_promotion", "2026-03-24T04:00:00Z", None, "2026-03-23", "2026-03-24T00:00:00Z", 4, "completed"),
    )
    connection.commit()

    apply_schema(connection)

    modes = {
        row[0]: row[1]
        for row in connection.execute("SELECT run_id, scan_mode FROM run_metadata ORDER BY run_id")
    }
    assert modes == {"legacy-d": "daily", "legacy-i": "intraday"}

    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("new-d", "daily", "2026-03-25T00:00:00Z", None, "2026-03-24", None, SCHEMA_VERSION, "running"),
    )
    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("new-i", "intraday", "2026-03-25T04:00:00Z", None, "2026-03-24", "2026-03-25T00:00:00Z", SCHEMA_VERSION, "running"),
    )
    connection.commit()

    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO run_metadata (
                run_id, scan_mode, started_at_utc, finished_at_utc,
                daily_bar_id, intraday_bar_id, schema_version, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("bad-d", "daily_discovery", "2026-03-26T00:00:00Z", None, "2026-03-25", None, SCHEMA_VERSION, "running"),
        )
    with pytest.raises(sqlite3.IntegrityError):
        connection.execute(
            """
            INSERT INTO run_metadata (
                run_id, scan_mode, started_at_utc, finished_at_utc,
                daily_bar_id, intraday_bar_id, schema_version, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("bad-i", "intraday_promotion", "2026-03-26T04:00:00Z", None, "2026-03-25", "2026-03-26T00:00:00Z", SCHEMA_VERSION, "running"),
        )
    connection.close()


def test_run_metadata_scan_mode_migration_unknown_legacy_values_fail(tmp_path) -> None:
    db_path = tmp_path / "legacy-unknown.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON;")
    connection.execute(
        """
        CREATE TABLE run_metadata (
            run_id          TEXT PRIMARY KEY,
            scan_mode       TEXT NOT NULL,
            started_at_utc  TEXT NOT NULL,
            finished_at_utc TEXT,
            daily_bar_id    TEXT NOT NULL,
            intraday_bar_id TEXT,
            schema_version  INTEGER NOT NULL,
            status          TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("unknown", "mystery_mode", "2026-03-24T00:00:00Z", None, "2026-03-23", None, 4, "running"),
    )
    connection.commit()

    with pytest.raises(ValueError, match="mystery_mode"):
        apply_schema(connection)
    connection.close()


def test_run_metadata_scan_mode_migration_is_idempotent(tmp_path) -> None:
    db_path = tmp_path / "legacy-idempotent.sqlite"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA foreign_keys=ON;")
    _create_legacy_run_metadata_table(connection)
    connection.execute(
        """
        INSERT INTO run_metadata (
            run_id, scan_mode, started_at_utc, finished_at_utc,
            daily_bar_id, intraday_bar_id, schema_version, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        ("legacy", "daily_discovery", "2026-03-24T00:00:00Z", None, "2026-03-23", None, 4, "completed"),
    )
    connection.commit()

    apply_schema(connection)
    apply_schema(connection)

    row = connection.execute("SELECT scan_mode FROM run_metadata WHERE run_id='legacy'").fetchone()
    assert row is not None
    assert row[0] == "daily"

    count = connection.execute("SELECT COUNT(*) FROM run_metadata").fetchone()[0]
    assert count == 1
    connection.close()
