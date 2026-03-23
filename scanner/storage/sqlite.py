"""SQLite connection helpers for Independence-Release infrastructure."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from .schema import apply_schema


def connect_sqlite(db_path: str | Path) -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    connection.execute("PRAGMA busy_timeout=5000;")
    return connection


def init_db(db_path: str | Path) -> sqlite3.Connection:
    connection = connect_sqlite(db_path)
    try:
        apply_schema(connection)
    except Exception:
        connection.close()
        raise
    return connection
