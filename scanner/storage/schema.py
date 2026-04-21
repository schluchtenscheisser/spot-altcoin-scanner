"""SQLite schema management for Independence-Release infrastructure."""

from __future__ import annotations

import sqlite3
from typing import Final

SCHEMA_VERSION: Final[int] = 4
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

OHLCV_BARS_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS ohlcv_bars (
    symbol              TEXT    NOT NULL,
    timeframe           TEXT    NOT NULL,
    open_time_utc_ms    INTEGER NOT NULL,
    close_time_utc_ms   INTEGER NOT NULL,
    open                REAL    NOT NULL,
    high                REAL    NOT NULL,
    low                 REAL    NOT NULL,
    close               REAL    NOT NULL,
    base_volume         REAL    NOT NULL,
    quote_volume        REAL    NOT NULL,
    PRIMARY KEY (symbol, timeframe, close_time_utc_ms),
    CHECK (timeframe IN ('1d', '4h'))
);
""".strip()

OHLCV_BARS_INDEX_SQL: Final[str] = """
CREATE INDEX IF NOT EXISTS idx_ohlcv_bars_symbol_tf_close_desc
ON ohlcv_bars (symbol, timeframe, close_time_utc_ms DESC);
""".strip()

OHLCV_CACHE_META_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS ohlcv_cache_meta (
    symbol                    TEXT    NOT NULL,
    timeframe                 TEXT    NOT NULL,
    cached_close_time_utc_ms  INTEGER,
    last_fetch_at_utc         TEXT,
    last_fetch_status         TEXT    NOT NULL CHECK (last_fetch_status IN ('ok', 'empty', 'error_transport', 'error_invalid')),
    last_error_code           TEXT,
    PRIMARY KEY (symbol, timeframe),
    CHECK (timeframe IN ('1d', '4h'))
);
""".strip()

STATE_MACHINE_CONTEXT_TABLE_SQL: Final[str] = """
CREATE TABLE IF NOT EXISTS state_machine_context (
    symbol TEXT PRIMARY KEY,
    setup_cycle_id INTEGER NOT NULL,
    previous_setup_cycle_id INTEGER,
    state_recorded_in_cycle_id INTEGER NOT NULL,
    state_machine_state TEXT NOT NULL,
    state_confidence REAL NOT NULL,
    state_transition_reason TEXT NOT NULL,
    bars_since_state_entered INTEGER NOT NULL,
    bars_since_early_entered INTEGER,
    bars_since_confirmed_entered INTEGER,
    bars_since_cycle_end INTEGER,
    close_at_early_entry_bar REAL,
    close_at_confirmed_entry_bar REAL,
    distance_from_ideal_entry_after_early REAL,
    distance_from_ideal_entry_after_confirmed REAL,
    freshness_distance_state_early REAL,
    freshness_distance_state_confirmed REAL,
    cycle_end_bar_index INTEGER,
    cycle_end_timestamp INTEGER,
    reclaim_below_reset_floor_seen_since_cycle_end INTEGER,
    data_resolution_class TEXT NOT NULL
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
        connection.execute(OHLCV_BARS_TABLE_SQL)
        connection.execute(OHLCV_BARS_INDEX_SQL)
        connection.execute(OHLCV_CACHE_META_TABLE_SQL)
        connection.execute(STATE_MACHINE_CONTEXT_TABLE_SQL)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION};")

    return SCHEMA_VERSION
