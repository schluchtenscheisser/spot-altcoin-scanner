"""SQLite schema management for Independence-Release infrastructure."""

from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA_VERSION: Final[int] = 1
RUN_METADATA_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS run_metadata (
    run_id          TEXT PRIMARY KEY,
    scan_mode       TEXT NOT NULL CHECK (scan_mode IN ('daily_discovery', 'intraday_promotion')),
    started_at_utc  TEXT NOT NULL,
    finished_at_utc TEXT,
    daily_bar_id    TEXT NOT NULL,
    intraday_bar_id INTEGER,
    schema_version  INTEGER NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed'))
);
""".strip()


def get_schema_version(connection: sqlite3.Connection) -> int:
    row = connection.execute("PRAGMA user_version;").fetchone()
    return int(row[0]) if row else 0


def apply_schema(connection: sqlite3.Connection) -> int:
    current_version = get_schema_version(connection)
    if current_version > SCHEMA_VERSION:
        raise ValueError(
            f"database schema version {current_version} is newer than supported version {SCHEMA_VERSION}"
        )

    with connection:
        connection.execute(RUN_METADATA_TABLE_SQL)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")

    return SCHEMA_VERSION
