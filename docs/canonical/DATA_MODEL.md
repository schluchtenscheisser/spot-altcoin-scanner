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
- Cross-layer canonical type: `daily_bar_id` is `str` (`YYYY-MM-DD`) for runner-facing typed bundles and output-facing schemas.
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
- post-Ticket 14 role: non-canonical transitional store (canonical base history is Parquet under `snapshots/history/ohlcv/`).

`ohlcv_cache_meta`
- PK: `(symbol, timeframe)`
- `cached_close_time_utc_ms`, `last_fetch_at_utc`, `last_error_code` are nullable and must round-trip as `None`.
- `last_fetch_status` closed enum: `{'ok','empty','error_transport','error_invalid'}`.
- absence of a row is the only bootstrap missing-cache state.
- post-Ticket 14 role: operational fetch/cache metadata remains valid and canonical for refresh decision support.

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

## Ticket 9 additive in-memory state pre-contracts

`PersistedStateCycleContext` defines the typed persisted-read input for Layer-4 pre-state logic.
`InvalidationCycleBundle` defines deterministic in-memory output with:
- structural/timing invalidation flags + primary reason codes,
- cycle decision (`new_cycle_detected`, `cycle_reason_code`, `resolved_setup_cycle_id`),
- diagnostics (`phase_floor_recovered_since_cycle_end`, `expansion_reset_condition_met`, `reclaim_reset_condition_met`).

Contract notes:
- `resolved_setup_cycle_id` is always a positive integer.
- `cycle_reason_code` is always populated from a closed enum.
- first-seen bootstrap initializes cycle id to `1` without emitting a new-cycle event.

## Ticket 10 additive state-machine contracts

Additive typed contracts:
- `StateRuntimeContext(current_close, current_bar_index, delta_closed_bars_relevant)`
- `PersistedStateMachineContext(...)` (state/freshness/cycle continuity fields)
- `StateEvaluationDisposition(admitted, disposition_reason)`
- `StateFreshnessBundle(...)`
- `StatePersistencePatch(...)`
- `StateMachineBundle(...)`

`StateEvaluationDisposition` is the only carrier for not-admitted outcomes; the six-state enum remains unchanged.


## Ticket 11 additive entry-pattern model

`EntryPatternBundle` is the typed Layer-5 output contract:
- `entry_pattern: EntryPattern`
- `entry_pattern_score: float`
- `candidate_pattern_scores_within_phase: dict[AdmittedEntryPattern, float]`

Type domains:
- `EntryPattern` includes the 9 positive patterns plus sentinel `"none"`.
- `AdmittedEntryPattern` includes only the 9 positive patterns; `"none"` is excluded by type.

Invariants:
- `entry_pattern == "none"` iff `entry_pattern_score == 0.0`.
- `entry_pattern != "none"` implies `candidate_pattern_scores_within_phase[entry_pattern] == entry_pattern_score`.
- `candidate_pattern_scores_within_phase` contains admitted patterns only; non-admitted patterns are absent (never represented as `0.0`).
- For `market_phase="none"` or unrecognized phase, the dict is `{}`.

Cross-layer guardrail handoff to Ticket 12 (documented interface semantics):
- `state_machine_state="early_ready"` + `entry_pattern="none"` maps to bucket `watchlist`.
- `state_machine_state="confirmed_ready"` + `entry_pattern="none"` maps to bucket `late_monitor` with reason `CONFIRMED_PATTERN_UNRESOLVED`.

## Ticket 12 additive decision model

`DecisionBucket` is a closed enum with exactly five values:
`watchlist`, `early_candidates`, `confirmed_candidates`, `late_monitor`, `discarded`.
`execution_pending` is an output flag and is never a bucket value.

`DecisionBundle` fields:
- `decision_bucket`
- `priority_score` (finite float in `[0,100]`, never null/non-finite)
- `bucket_reason_primary` / `bucket_reason_secondary`
- `execution_required` / `execution_pending`
- `entry_pattern` / `entry_pattern_score`

`RankedDecision` fields:
- `symbol` (final deterministic tie-break key)
- `decision: DecisionBundle`
- `rank_within_bucket` (1-based, per bucket)
- tie-break inputs include `state_confidence` and `market_phase_confidence`.

Execution contract note:
- `ExecutionInputContract` is consumed as optional read contract in T12.
- Canonical ownership of execution derivation remains Ticket 16.
- `ExecutionInputContract.execution_status` is closed to: `direct_ok | tranche_ok | marginal | fail`.
- `ExecutionInputContract.execution_pass` is `True` for `direct_ok/tranche_ok`, `False` for `marginal/fail`.
- Ticket-16 adapter emits `execution_grade=None` for all produced contracts; T12 applies the canonical fallback grade mapping (`direct_ok=100`, `tranche_ok=75`, `marginal=40`, `fail=0`).
- `unknown` execution outcomes do **not** produce an `ExecutionInputContract`; those symbols keep the pass-1 bucket result with `execution_pending=True`, while diagnostics carries `execution_status_raw=\"unknown\"`.

Spec inconsistency resolution (explicit): Abschnitt 7 §10.4 overrides incomplete §17.4 enumeration for this path:
`confirmed_ready + entry_pattern="none"` maps to `late_monitor` with primary reason `CONFIRMED_PATTERN_UNRESOLVED`.

Finite-score floor policy:
- For non-gated paths and Rule-10 catch-all, nullable/non-finite `state_confidence` and `market_phase_confidence` are explicitly substituted with `0.0` via `_coerce_score_input_for_non_gated_path` before scoring.
- This substitution is localized to Ticket-12 score calculation and is not a global missing-numeric policy.
