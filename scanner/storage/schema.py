"""SQLite schema management for Independence-Release infrastructure."""

from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA_VERSION: Final[int] = 2
RUN_METADATA_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS run_metadata (
    run_id          TEXT PRIMARY KEY,
    scan_mode       TEXT NOT NULL CHECK (scan_mode IN ('daily_discovery', 'intraday_promotion')),
    started_at_utc  TEXT NOT NULL,
    finished_at_utc TEXT,
    daily_bar_id    TEXT NOT NULL,
    intraday_bar_id INTEGER,
    schema_version  INTEGER NOT NULL,
    status          TEXT NOT NULL CHECK (status IN ('running', 'completed', 'failed')),
    eligible_pre_1d_count INTEGER NOT NULL DEFAULT 0,
    activity_gate_passed_count INTEGER NOT NULL DEFAULT 0,
    monitoring_bypass_count INTEGER NOT NULL DEFAULT 0,
    selected_for_4h_count INTEGER NOT NULL DEFAULT 0
);
""".strip()




SYMBOL_METADATA_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS symbol_metadata (
    symbol TEXT PRIMARY KEY,
    mexc_first_tradable_date TEXT,
    updated_at_utc TEXT NOT NULL
);
""".strip()

SYMBOL_RUN_DECISIONS_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS symbol_run_decisions (
    run_id TEXT NOT NULL,
    symbol TEXT NOT NULL,
    eligible_pre_1d INTEGER,
    activity_gate_status TEXT,
    pre_4h_filter_status TEXT,
    pre_4h_filter_primary_reason TEXT,
    monitoring_bypass_applied INTEGER,
    monitoring_bypass_reason TEXT,
    was_capped_after_filter INTEGER,
    selected_for_4h_fetch INTEGER,
    quote_volume_24h REAL,
    active_days_last_14 INTEGER,
    matched_filter_rules_json TEXT,
    PRIMARY KEY (run_id, symbol),
    FOREIGN KEY (run_id) REFERENCES run_metadata(run_id) ON DELETE CASCADE
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
        cols = {row[1] for row in connection.execute("PRAGMA table_info(run_metadata)").fetchall()}
        for col, ddl in [
            ("eligible_pre_1d_count", "ALTER TABLE run_metadata ADD COLUMN eligible_pre_1d_count INTEGER NOT NULL DEFAULT 0"),
            ("activity_gate_passed_count", "ALTER TABLE run_metadata ADD COLUMN activity_gate_passed_count INTEGER NOT NULL DEFAULT 0"),
            ("monitoring_bypass_count", "ALTER TABLE run_metadata ADD COLUMN monitoring_bypass_count INTEGER NOT NULL DEFAULT 0"),
            ("selected_for_4h_count", "ALTER TABLE run_metadata ADD COLUMN selected_for_4h_count INTEGER NOT NULL DEFAULT 0"),
        ]:
            if col not in cols:
                connection.execute(ddl)
        connection.execute(SYMBOL_METADATA_TABLE_SQL)
        connection.execute(SYMBOL_RUN_DECISIONS_TABLE_SQL)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")

    return SCHEMA_VERSION
