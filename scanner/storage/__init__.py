"""Storage-layer exports for Independence-Release infrastructure."""

from .schema import OHLCV_BARS_INDEX_SQL, OHLCV_BARS_TABLE_SQL, OHLCV_CACHE_META_TABLE_SQL, RUN_METADATA_TABLE_SQL, SCHEMA_VERSION, STATE_MACHINE_CONTEXT_TABLE_SQL, SYMBOL_METADATA_TABLE_SQL, SYMBOL_RUN_DECISIONS_TABLE_SQL, apply_schema, get_schema_version
from .sqlite import connect_sqlite, init_db
from .snapshots import MonthMutabilityPolicy, build_ohlcv_history_partition_dir, build_run_manifest_path, build_run_snapshot_dir, is_month_open, month_mutability_policy

__all__ = [
    "OHLCV_BARS_TABLE_SQL",
    "OHLCV_BARS_INDEX_SQL",
    "OHLCV_CACHE_META_TABLE_SQL",
    "RUN_METADATA_TABLE_SQL",
    "STATE_MACHINE_CONTEXT_TABLE_SQL",
    "SCHEMA_VERSION",
    "SYMBOL_METADATA_TABLE_SQL",
    "SYMBOL_RUN_DECISIONS_TABLE_SQL",
    "apply_schema",
    "get_schema_version",
    "connect_sqlite",
    "init_db",
    "build_ohlcv_history_partition_dir",
    "is_month_open",
    "month_mutability_policy",
    "MonthMutabilityPolicy",
    "build_run_snapshot_dir",
    "build_run_manifest_path",
    "upsert_symbol_metadata",
    "insert_symbol_run_decision",
    "load_persisted_state_machine_context",
    "apply_state_persistence_patch",
]

from .repositories import OhlcvBarRecord, OhlcvCacheMetaRecord, apply_state_persistence_patch, get_ohlcv_cache_meta, insert_symbol_run_decision, load_persisted_state_machine_context, ohlcv_bar_exists, read_recent_ohlcv_bars, upsert_ohlcv_cache_meta, upsert_symbol_metadata, write_ohlcv_bars_conflict_strict
