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


Evaluation/T30 output schema is documented in `docs/canonical/EVALUATION.md`. It is not part of the Daily/Intraday report contract.

## Current report and diagnostics data model (`ir1.5+`)

The field contracts in this section describe the current serialized report/diagnostics artifacts produced by the output layer. They are additive to the persistence foundation above and are based on the DOC-E1 evidence inventory. Evaluation/T30 output schemas are outside this document's current-state data/report contract and remain subject to dedicated evaluation documentation and CODE-FU-B boundary resolution.

### Candidate exclusion and operational tradeability

Current diagnostics carry both structural exclusion fields and tradeability labels. Consumers must keep these concepts separate:

| Field | Serialized location | Current meaning | Consumer guidance |
|---|---|---|---|
| `candidate_excluded` | Top-level diagnostics boolean; mirrored from `universe.candidate_excluded` for compatibility | Structural candidate-facing exclusion, currently used for stable/cash-like and leveraged/margin-like categories. Excluded symbols remain present in diagnostics but are removed from actionable report candidate lists. | Prefer the top-level field for current diagnostics. Treat the nested `universe.candidate_excluded` as compatibility/source context rather than the primary current read path. |
| `is_tradeable_candidate` | Top-level diagnostics nullable boolean and exposed in execution-aware report segment rows where those rows include diagnostic field groups | Bucket-/execution-scoped audit label derived from decision bucket plus reduced-size execution eligibility. It does not by itself account for structural candidate exclusion. | Do not use this alone as the final `ir1.5+` operational tradeability label. |
| `is_operational_trade_candidate` | Top-level diagnostics boolean and exposed in execution-aware report segment rows where those rows include diagnostic field groups | Final `ir1.5+` row-level operational tradeability label: `is_tradeable_candidate is True` and `candidate_excluded is not True`. | Preferred row-level field for operational consumers. Report candidate lists also apply list-level exclusion, so list membership and row-level labels should be read as related but distinct contracts. |

Structural exclusion answers “should this symbol appear in actionable candidate lists?”; `is_tradeable_candidate` answers “did the bucket/execution policy consider this row tradeable before structural exclusion?”; `is_operational_trade_candidate` answers “is this row an operational trade candidate after both checks?”.

### Execution fields

Execution fields are current diagnostics fields and selected report-segment row fields. They are derived from orderbook/depth/tradeability evaluation and execution-size policy. They are analysis/reporting fields for current artifacts; report ranking/selection remains governed by the decision/ranking pipeline and by candidate-exclusion filtering of actionable lists.

| Field | Serialized location | Nullability / values | Current meaning |
|---|---|---|---|
| `execution_status_raw` | Top-level diagnostics; execution-aware report segment rows | Nullable string. Known raw values include `direct_ok`, `tranche_ok`, `marginal`, `fail`, `unknown`, and `null` for not-attempted symbols. | Active serialized execution status field. The expected name `execution_status` is not the current artifact field; it appears only in internal contracts before serialization. |
| `execution_size_class` | Top-level diagnostics; execution-aware report segment rows; evaluation metrics outside this document's schema scope | Nullable string. Current values include `not_evaluated`, `full`, `blocked`, `not_evaluable`, `reduced_75`, `reduced_50`, `reduced_25`, and `observe_only`. | Policy-derived position-size/action class from execution-attempt state, raw status, and depth-ratio band. Read together with `execution_status_raw`, because `full` can occur for both direct-ok capacity and marginal-quality cases. |
| `is_reduced_size_eligible` | Top-level diagnostics boolean; execution-aware report segment rows | Boolean, normalized to `false` when not eligible. | Policy-size eligibility flag derived from raw execution status, execution-size class, tradeability reason keys, and non-depth gate flags. Despite the name, `true` means tradeable at the policy-permitted size, including full-size `direct_ok` rows. It feeds `is_tradeable_candidate`. |
| `execution_grade_t16` | Top-level diagnostics compatibility field | Current validation requires `null`. | Retained compatibility field only. It is not the current scoring signal. |
| `execution_grade_effective` | Top-level diagnostics; execution-aware report segment rows | Nullable numeric. | Active effective execution-grade output derived by execution-size policy and related to `execution_size_class`. |

Related depth/orderbook diagnostics use implemented field names such as `available_depth_1pct_usdt`, `depth_threshold_1pct_usdt`, `available_depth_ratio`, `depth_ratio_band`, `bid_depth_1pct_usdt`, `ask_depth_1pct_usdt`, `estimated_slippage_bps`, and `spread_pct`. The expected label `execution_depth_impact` is not an exact active serialized field name.

### Entry-Location / T_EL2 diagnostics and report segments

Entry-Location is a nested diagnostics block, not a set of flat top-level `entry_location_*` fields. It was added in `ir1.3`; accepted older diagnostics may omit the block and version-gated consumers should treat that absence as not evaluated rather than as a present block with `null` values.

| Implemented field or segment | Location | Current meaning / boundary |
|---|---|---|
| `entry_location` | Optional nested diagnostics block | Current container for Entry-Location / T_EL2 diagnostics. |
| `entry_location.entry_location_status` | Nested diagnostics field | Implemented status/bucket-like field. Current values include `fresh_entry`, `acceptable_entry`, `extended_entry`, `chased_entry`, and `not_evaluable`. The expected name `entry_location_bucket` is not an active field. |
| `entry_location.entry_action_hint` | Nested diagnostics field | Current action hint. Values include `buy_now_candidate`, `acceptable_if_strategy_allows`, `wait_for_pullback`, `avoid_chasing`, `monitor_only`, and `not_evaluable`. Plain-English labels such as “buy now” and “avoid chase” should be mapped to these exact serialized values. |
| `entry_location.entry_location_reason_primary` and `entry_location.entry_location_reason_codes` | Nested diagnostics fields | Implemented reason representation. There is no current single flat `entry_location_reason` field. |
| `entry_location.range_high_proximity_warning` | Nested diagnostics field and duplicated under `entry_location_inputs_used` for audit context | Current implemented flag-like field. There is no current grouped `entry_location_flags` field. |
| `entry_location.entry_location_inputs_used` | Nested diagnostics field | Audit context for input values used by Entry-Location classification; numeric input distances live here rather than in a current `entry_location_score`. |
| `entry_location_candidate_segments.buy_now_candidates` | Daily report segment block | Emitted report-side segment for rows whose `entry_action_hint` is `buy_now_candidate`. There is no diagnostics boolean named exactly `buy_now`. |
| `entry_location_candidate_segments.wait_pullback_candidates` | Daily report segment block | Emitted report-side segment for rows whose `entry_action_hint` is `wait_for_pullback`. |
| `entry_location_candidate_segments.early_watch_candidates` | Daily report segment block | Emitted report-side monitor segment for early fresh/acceptable rows. This is separate from the general report `watchlist` symbol list. |
| `entry_location_candidate_segments.good_location_but_not_tradeable` | Daily report segment block | Emitted report-side segment for rows with acceptable Entry-Location context that are not currently tradeable. |
| `entry_location_candidate_segments.tradeable_but_extended` | Daily report segment block | Emitted report-side segment for tradeable, non-excluded rows whose `entry_location_status` is `extended_entry` or `chased_entry`. Chased rows with `entry_action_hint="avoid_chasing"` may appear here when they satisfy those tradeability/exclusion conditions. |
| `avoid_chasing` | Entry-Location action-hint value only | Valid `entry_location.entry_action_hint` value. It is not currently an emitted `entry_location_candidate_segments` key; consumers that need avoid-chasing rows must filter emitted row fields, especially `entry_location.entry_action_hint == "avoid_chasing"`, or inspect `tradeable_but_extended` rows with `entry_location_status == "chased_entry"` when the row is tradeable and not excluded. |
| `reduced_25` | Execution size class value and execution-aware reporting concept | This is an execution-size class, not an Entry-Location field. Entry-Location may coexist with reduced-size execution reporting, but the concepts are distinct. |

The existence and semantics of an `entry_location_score` field are not yet fully validated and must not be treated as a current output contract until resolved.

### Null, skipped, failed, and absent-value semantics

There is no universal meaning for `null` or missing keys across all artifacts. Consumers must apply field-specific semantics and distinguish explicit serialized values from omitted compatibility blocks.

| Value / condition | Current use | Consumer rule |
|---|---|---|
| `null` | Used on nullable diagnostics fields such as not-attempted execution fields, compatibility `execution_grade_t16`, nullable effective grades, and other field-specific outputs. | Interpret using the owning field. Do not coerce `null` to `false`, zero, or a universal “not applicable” meaning. |
| Missing optional block | Older accepted diagnostics may omit blocks introduced by later schema versions, notably pre-`ir1.3` `entry_location`. | Treat version-gated absence according to that block's compatibility rule, e.g. missing older `entry_location` means not evaluated. Do not treat all missing keys as equivalent to explicit `null`. |
| `not_evaluated` | Explicit execution-size class when execution was not attempted; also a compatibility interpretation for missing older Entry-Location blocks. | Distinguish an explicit serialized `not_evaluated` value from an omitted older block interpreted as not evaluated. |
| `not_evaluable` | Used when the evaluation path exists but inputs/state are insufficient or unsuitable, including Entry-Location status/action hint, execution-size classification for unknown/unhandled states, depth-ratio bands with missing ratio, and some gate contexts. | Means conceptually considered but not computable/evaluable, not merely skipped. |
| `unknown` | Raw execution status for missing/stale/fetch-failed orderbook/depth classification and selected evaluation compatibility contexts. | For execution, read with `execution_reason_raw`/depth fields where available. Do not equate with `fail`. |
| `fail` / `failed` | Raw execution status uses `fail`; report counts/segments use normalized label `failed` for failed execution categories. | Keep raw field values and summary/report labels separate. |
| `not_applicable` | No active current diagnostics/report field value named exactly `not_applicable` is validated in the DOC-E1 evidence set. | Do not require or invent this value for current data/report consumers; unresolved status is tracked in open questions. |

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
- `intraday_bar_id`: for intraday runner/report contracts canonical type is `str` in `YYYY-MM-DDTHH:00:00Z` (UTC, `HH ∈ {00,04,08,12,16,20}`) representing the last fully closed 4h bar. `NULL` remains valid for daily-only runs.
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
