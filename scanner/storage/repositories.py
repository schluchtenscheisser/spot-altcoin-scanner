from __future__ import annotations

import sqlite3
from typing import Any, Mapping


def upsert_symbol_metadata(connection: sqlite3.Connection, symbol: str, mexc_first_tradable_date: str | None) -> None:
    with connection:
        connection.execute(
            """
            INSERT INTO symbol_metadata(symbol, mexc_first_tradable_date, updated_at_utc)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            ON CONFLICT(symbol) DO UPDATE SET
              mexc_first_tradable_date=excluded.mexc_first_tradable_date,
              updated_at_utc=excluded.updated_at_utc
            """,
            (symbol, mexc_first_tradable_date),
        )


def insert_symbol_run_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    columns = [
        "run_id", "symbol", "eligible_pre_1d", "activity_gate_status", "pre_4h_filter_status",
        "pre_4h_filter_primary_reason", "monitoring_bypass_applied", "monitoring_bypass_reason",
        "was_capped_after_filter", "selected_for_4h_fetch", "quote_volume_24h", "active_days_last_14", "matched_filter_rules_json",
    ]
    values = [row.get(c) for c in columns]
    placeholders = ",".join("?" for _ in columns)
    with connection:
        connection.execute(
            f"INSERT INTO symbol_run_decisions ({','.join(columns)}) VALUES ({placeholders})",
            values,
        )
