"""Storage-layer exports for Independence-Release infrastructure."""

from .schema import RUN_METADATA_TABLE_SQL, SCHEMA_VERSION, SYMBOL_METADATA_TABLE_SQL, SYMBOL_RUN_DECISIONS_TABLE_SQL, apply_schema, get_schema_version
from .sqlite import connect_sqlite, init_db

__all__ = [
    "RUN_METADATA_TABLE_SQL",
    "SCHEMA_VERSION",
    "SYMBOL_METADATA_TABLE_SQL",
    "SYMBOL_RUN_DECISIONS_TABLE_SQL",
    "apply_schema",
    "get_schema_version",
    "connect_sqlite",
    "init_db",
    "upsert_symbol_metadata",
    "insert_symbol_run_decision",
]

from .repositories import insert_symbol_run_decision, upsert_symbol_metadata
