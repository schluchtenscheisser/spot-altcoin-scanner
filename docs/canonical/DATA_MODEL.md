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

## Ticket 5 additive in-memory feature model

Ticket 5 introduces an in-memory feature contract (no persistence table):
- `RawFeatures1D`
- `RawFeatures4H`
- `RawFeaturesShared`
- `FeatureBundle`

`FeatureBundle` fields:
- `symbol`
- `daily_bar_id`
- `intraday_bar_id | None`
- `daily_close_time_utc_ms`
- `intraday_close_time_utc_ms | None`
- `data_4h_available`
- `raw_1d`
- `raw_4h | None`
- `raw_shared`

Companion status rule: each derived field has `{field}_status` with closed enum:
`ok | insufficient_history | gap_in_required_window | upstream_dependency_null | invalid_upstream_value`.

## Ticket 5.1 additive in-memory feature adjustments

- Canonical anchor field name is `fixed_structural_break_anchor_4h` (deprecated alias `fixed_high20_break_anchor_4h` removed from public contract).
- Added freshness helper fields in `RawFeatures4H`:
  - `bars_since_last_volume_shift_4h` + companion status
  - `distance_to_range_high_pct_abs` + companion status

## Ticket 6 additive in-memory axis model

Ticket 6 introduces in-memory axis output model `Tier1AxisBundle` with exactly six Tier-1 axes:
`trend_strength`, `reclaim_progress`, `compression_strength`, `expansion_progress_structural`, `volume_regime_shift`, `freshness_distance_structural`.

Per-axis companion fields are mandatory:
- `<axis>_not_evaluable`
- `<axis>_reduced_resolution`
- `<axis>_effective_weight_ratio`

Nullability contract:
- `<axis> = null` means not-evaluable only (no coercion to sentinel values).
- `not_evaluable=true => axis is null`.
- `effective_weight_ratio = null` when axis not evaluable.

## Ticket 7 additive in-memory axis model

Ticket 7 introduces `Tier2AxisBundle` as typed in-memory output for Tier-2-Simplified axes:
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Per-axis companion fields are mandatory:
- `<axis>_not_evaluable`
- `<axis>_reduced_resolution`
- `<axis>_effective_weight_ratio`

Two-path semantics are part of this contract:
- `data_4h_available=true` selects only the 4h path;
- `data_4h_available=false` selects only the 1d fallback path;
- successful 1d fallback always implies `<axis>_reduced_resolution=true`.

Nullability contract is strict:
- `<axis> = null` means not evaluable only (no sentinel coercion).
- `<axis>_not_evaluable=true => <axis> is null`.
- `<axis>_effective_weight_ratio = null` when `<axis>_not_evaluable=true`.
- `<axis>_reduced_resolution=false` when `<axis>_not_evaluable=true`.

## Ticket 8 additive in-memory phase model

Ticket 8 introduces `PhaseInterpretationBundle` as typed in-memory output with fields for:
- selected phase (`market_phase`), confidence, deterministic runner-up, gap, and blended flag,
- per-phase scores, floor margins, floor-failure flags, and eval statuses,
- passthrough freshness diagnostics (`freshness_distance_structural*`).

Closed enums:
- `market_phase ∈ {pressure_build, trend_resume, transition_reclaim, none}`
- `market_phase_runner_up ∈ {pressure_build, trend_resume, transition_reclaim}`
- `phase_eval_status_* ∈ {score_computed, minimum_basis_not_met, hard_floor_failed}`.

Nullability rules:
- `phase_floor_margin_*` may be `null` when minimum basis is missing or required floor inputs are unavailable.
- `freshness_distance_structural` passthrough keeps upstream nullability and must not be coerced.
