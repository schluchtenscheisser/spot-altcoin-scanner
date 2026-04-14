# Data Model — Independence-Release Infrastructure Foundation (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_DATA_MODEL
status: canonical
persistence_foundation: sqlite
history_foundation: parquet
bootstrap_level: foundation_plus_skeleton
```

## Purpose
This document defines the first canonical persistence foundation required by the Independence-Release architecture: deterministic bar identifiers, SQLite infrastructure scope, and the initial `run_metadata` table. Business tables remain deferred until their fields are canonically specified.

## Persistence (SQLite)
SQLite is the persistence foundation for the Independence-Release target architecture.

### Infrastructure scope for this ticket
The infrastructure layer is limited to:
- opening or creating the SQLite database,
- enabling WAL mode,
- applying idempotent schema bootstrap,
- tracking schema version with `PRAGMA user_version`,
- creating exactly one table: `run_metadata`.

### Explicitly out of scope
The following tables are not created in this ticket:
- `symbol_state`
- `cycle_state`
- `cache_meta`

These depend on later business-field definitions.

### Schema version tracking
Schema version is tracked through SQLite `PRAGMA user_version`. This avoids introducing an extra metadata table and keeps `run_metadata` as the only SQL table created by the foundation ticket.

### `run_metadata` table
```sql
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
```

#### Field semantics
- `run_id`: runner-generated unique identifier; concrete format is deferred to the runner ticket.
- `scan_mode`: exactly one of `daily_discovery` or `intraday_promotion`.
- `started_at_utc`: ISO-8601 UTC timestamp of run start.
- `finished_at_utc`: nullable ISO-8601 UTC timestamp of completion. `NULL` means the run is still in progress.
- `daily_bar_id`: canonical `YYYY-MM-DD` daily bar identifier for the run context.
- `intraday_bar_id`: nullable UTC epoch-millisecond close time of the 4h bar context. `NULL` is valid for daily-only runs.
- `schema_version`: integer schema version copied from the SQLite infrastructure layer.
- `status`: exactly one of `running`, `completed`, `failed`.

### Idempotency requirement
Running the SQLite bootstrap multiple times against the same database must succeed without duplicate-table failures or schema corruption.

## History (Parquet)
Parquet is the history and export-oriented storage foundation for snapshot/history material in the target architecture. Exact datasets and field-level schemas remain deferred.

## Field Groups

### Group A
Reserved for the authoritative Field Group A defined by Abschnitt 6 §4. This document does not restate or extend the unresolved field list.

### Group B
Reserved for the authoritative Field Group B defined by Abschnitt 6 §4. This document does not restate or extend the unresolved field list.

### Group C
Reserved for the authoritative Field Group C defined by Abschnitt 6 §4. This document does not restate or extend the unresolved field list.

### Group D
Reserved for the authoritative Field Group D defined by Abschnitt 6 §4. This document does not restate or extend the unresolved field list.

### Ticket 3 additive schema
`run_metadata` includes additive counters: `eligible_pre_1d_count`, `activity_gate_passed_count`, `monitoring_bypass_count`, `selected_for_4h_count`.

`symbol_metadata(symbol PK, mexc_first_tradable_date, updated_at_utc)` persists listing-age bootstrap state.

`symbol_run_decisions(run_id, symbol PK)` persists per-symbol decision diagnostics including gate/filter/bypass/cap outcomes and matched filter rules.

## Ticket 4 OHLCV cache data model (transitional)

`ohlcv_bars`
- PK: `(symbol, timeframe, close_time_utc_ms)`
- `timeframe` closed enum: `{'1d','4h'}`
- historical bars are conflict-strict immutable: same PK + differing values is an error (no replace).

`ohlcv_cache_meta`
- PK: `(symbol, timeframe)`
- `cached_close_time_utc_ms`, `last_fetch_at_utc`, `last_error_code` are nullable and must round-trip as `None`.
- `last_fetch_status` closed enum: `{'ok','empty','error_transport','error_invalid'}`.
- absence of a row is the only bootstrap missing-cache state.

Terminology mapping note: `cached_close_time_utc_ms` is the OHLCV-cache representation aligned with the same close-bar semantics later represented by `daily_cache_bar_id` / `intraday_cache_bar_id` in state-oriented persistence layers.
