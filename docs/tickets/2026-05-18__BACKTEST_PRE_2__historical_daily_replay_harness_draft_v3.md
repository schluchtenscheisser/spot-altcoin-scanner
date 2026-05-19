# 2026-05-18__BACKTEST_PRE_2__historical_daily_replay_harness — DRAFT v2

## Title

Backtest-Pre-2: Historical Daily Replay Harness for Signal-Quality Replay

## Status

Draft for Martin / Claude review. Do not hand to Codex as final until reviewed and approved.

## Context / Source

We are adding the second preparation ticket for the **Historical Signal-Quality Replay** workstream.

This workstream is not a trading backtest. It is a historical signal-quality validation layer for the Independence-Release scanner. Pre-1 builds reusable Binance Spot USDT OHLCV history. Pre-2 must use that history to run the existing scanner signal-generation layers day-by-day over historical data, preserving point-in-time semantics and replay-local state continuity.

Pre-2 is not a T18 reuse. T18 is a post-hoc evaluation layer over finished run artifacts. Pre-2 must build a real historical replay harness that executes the scanner signal stack over historical closed bars.

The agreed architecture decisions for Pre-2 are:

- Use Scenario-YAML as the canonical replay run definition.
- Do not use ad-hoc CLI overrides for scenario-defining replay parameters.
- Bypass T4 / live OHLCV fetch and load Pre-1 Binance Parquet directly.
- Do not call MEXC APIs or live fetch clients.
- Use T5–T12 production modules directly where possible; do not clone fachliche signal logic.
- Execute historical daily replay only; no intraday promotion simulation.
- Maintain replay-local state, fully separate from live/shadow state.
- Keep Execution fully disabled: `disabled_historical_ohlcv_only`.
- Do not emit `decision_bucket` in replay outputs.
- Emit `historical_signal_bucket` as the only bucket field in replay outputs.
- Emit event candidates only; do not calculate forward returns, MFE, MAE, or segment-quality metrics.

## Authoritative references

Use the current authoritative Independence-Release reference set:

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. The current canonical project documents, only insofar as they do not contradict the above reference set.
4. The implemented Pre-1 contract for Binance OHLCV history fetch, if merged.
5. The agreed Historical Signal-Quality Replay decisions from Martin / ChatGPT / Claude review.

If the current authoritative reference set, existing repo authority/canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only insofar as they do not contradict this reference set.

Existing repo paths/helpers may be reused if they do not contradict the current authoritative reference set. Do not introduce a second competing truth for state semantics, time semantics, scenario semantics, or replay output fields.

## Goal

Implement a historical daily replay harness that:

1. Loads Pre-1 OHLCV Parquet history for a configured Scenario-YAML.
2. Slices 1d and 4h bars point-in-time for each historical daily replay date.
3. Runs the existing production signal-generation modules T5–T12 over those closed bars.
4. Maintains replay-local state continuity day-by-day.
5. Emits replay diagnostics and event-candidate exports for later Backtest-1 evaluation.
6. Preserves strict no-lookahead semantics.
7. Does not evaluate execution, tradeability, forward returns, MFE, MAE, or calibration/validation performance.

## Scope

Implement exactly this Pre-2 scope:

1. Scenario-YAML parser/validator for historical daily replay scenarios.
2. Scenario immutability enforcement via an operative `scenario_config_hash`.
3. Loading Pre-1 OHLCV Parquet history and Pre-1 manifests.
4. Point-in-time daily slicing for 1d and 4h bars.
5. Historical daily replay loop over `evaluation.start_date` through `evaluation.end_date`.
6. T4 bypass and direct production module invocation for T5–T12 equivalents.
7. Replay-local state persistence.
8. Handling warm-up, missing 1d bars, missing/incomplete 4h context, and later-eligible symbols.
9. Replay diagnostics output.
10. `historical_signal_bucket` derivation and output.
11. Replay event-candidate export without forward returns.
12. Replay manifest output.
13. Tests for scenario validation, point-in-time slicing, state persistence, missing-data behavior, execution-disabled semantics, and output schema constraints.

## Out of scope

Do not implement any of the following in this ticket:

- Binance OHLCV fetching.
- Changes to Pre-1 fetch behavior, except if needed only to consume its current output contract.
- T4 refactor or generic live data-source abstraction.
- Calls to `scanner/data/ohlcv_fetch.py`.
- Calls to `scanner/clients/mexc_client.py`.
- MEXC API calls.
- Live daily runner changes.
- Intraday promotion replay.
- Multiple replay runs per historical day.
- Execution grading.
- Orderbook / liquidity simulation.
- Dummy execution fields implying tradeability.
- Live `decision_bucket` output in replay artifacts.
- Forward returns.
- `next_daily_open` calculation.
- MFE / MAE.
- Segment-quality evaluation.
- Calibration/validation reports.
- Config tuning.
- Dynamic historical universe reconstruction.
- Delisting-aware historical universe reconstruction.
- Market-regime label generation. Pre-2 may record a `regime_labels.method_ref`, but must not compute or analyze regimes unless already provided as metadata.

## Terminology

Use these terms consistently:

| Term | Meaning |
|---|---|
| Historical Signal-Quality Replay | The full historical signal validation workstream. Not a trading backtest. |
| Pre-1 | Historical Binance OHLCV fetch and Parquet history dataset. |
| Pre-2 | Historical daily replay harness defined by this ticket. |
| Backtest-1 | Later signal-quality evaluation over Pre-2 replay outputs. |
| Scenario-YAML | Canonical replay run definition for Pre-2 and later stages. |
| `scenario_id` | Stable identifier for a replay scenario. |
| `replay_id` | UTC timestamp of the replay run start in `YYYY-MM-DDTHH:MM:SSZ` format, no microseconds. |
| `scenario_config_hash` | Hash of replay-operative scenario fields, excluding analysis-only `splits.*`. |
| `as_of_daily_bar_id` | UTC date of the daily bar being replayed. |
| `daily_replay_run_time_utc` | Timestamp after the relevant daily bar is fully closed. |
| `historical_signal_bucket` | Replay-only pre-execution bucket field. |
| `decision_bucket` | Live operational bucket field; must not be written by Pre-2. |
| `disposition_status` | Replay/admission status explaining whether a symbol was evaluated or why not. |
| `signal_daily_close` | Close of the signal-producing daily bar. Not an executable entry reference. |

## Scenario-YAML contract

### Canonical run definition

Pre-2 must be driven by Scenario-YAML. Scenario-defining parameters must not be overridden ad hoc via CLI flags.

A thin CLI may accept only:

```text
--scenario <path/to/scenario.yml>
--output-root <optional technical root override if repo convention requires it>
--dry-run-validate-scenario
```

The CLI must not provide ad-hoc overrides for fields such as dates, universe mode, execution mode, scanner config hash, or history refs.

### Replay ID

Pre-2 must define `replay_id` deterministically from the replay run start timestamp:

```text
replay_id = replay_run_started_at_utc formatted as YYYY-MM-DDTHH:MM:SSZ
```

Rules:

- Use UTC.
- Use no microseconds.
- Use a filesystem-safe exact string.
- Use the same `replay_id` in output paths, `replay_manifest.json`, replay diagnostics, event candidates, and replay-state metadata.
- If two runs start within the same second for the same `scenario_id`, fail fast or append a deterministic collision suffix; do not silently overwrite an existing replay directory.


### Required scenario shape

Implement a typed, validated Scenario-YAML contract. Example:

```yaml
scenario_id: hsq_replay_2025_05_to_2026_05_v1

history_dataset_ref: snapshots/history/ohlcv
history_manifest_ref: snapshots/history/manifests/history_manifest.json
universe_manifest_ref: snapshots/history/manifests/universe_manifest.json

evaluation:
  start_date: 2025-05-01
  end_date: 2026-05-17

timeframes:
  - 1d
  - 4h

universe_mode: fixed_current_mexc_binance_intersection

execution:
  mode: disabled_historical_ohlcv_only

scanner_config:
  ref: config/config.yml
  hash: "<sha256>"

regime_labels:
  method_ref: btc_weekly_30d_return_vol_v1

daily_replay_time_policy:
  settlement_delay_seconds: 0

warmup:
  warm_up_1d_bars: 120
  warm_up_4h_bars: 120

splits:
  calibration:
    start_date: 2025-05-01
    end_date: 2026-01-31
  validation:
    start_date: 2026-02-01
    end_date: 2026-05-17
```

### Required fields

These fields are required:

```text
scenario_id
history_dataset_ref
history_manifest_ref
universe_manifest_ref
evaluation.start_date
evaluation.end_date
timeframes
universe_mode
execution.mode
scanner_config.ref
scanner_config.hash
regime_labels.method_ref
daily_replay_time_policy.settlement_delay_seconds
warmup.warm_up_1d_bars
warmup.warm_up_4h_bars
```

### Optional fields

`splits.calibration` and `splits.validation` may be present. If present, validate that:

- dates are valid ISO dates;
- each split has `start_date <= end_date`;
- split dates lie within the evaluation window;
- calibration and validation windows do not overlap.

Pre-2 must record `splits.*` in `replay_manifest.json`, but must not evaluate or report calibration/validation performance.

### Scenario immutability

After the first replay run has been created for a `scenario_id`, the replay-operative scenario definition is immutable.

Implement:

```text
scenario_config_hash = sha256(canonicalized replay-operative Scenario-YAML fields)
```

A replay run start must follow these rules:

| Case | Behavior |
|---|---|
| `scenario_id` has no prior recorded hash | Allow run and record `scenario_config_hash`. |
| `scenario_id` exists and hash is identical | Allow additional replay run. |
| `scenario_id` exists and hash differs | Fail fast with a clear error. |

The scenario registry must be persisted in a repo-local replay registry store:

```text
evaluation/replay/scenario_registry.sqlite
```

The registry must at least store `scenario_id`, `scenario_config_hash`, first-seen timestamp, and the path or hash of the scenario file used for the first replay run.


### Fields included in `scenario_config_hash`

The hash must include only replay-operative fields:

```text
scenario_id
history_dataset_ref
history_manifest_ref
universe_manifest_ref
evaluation.start_date
evaluation.end_date
timeframes
universe_mode
execution.mode
scanner_config.ref
scanner_config.hash
regime_labels.method_ref
daily_replay_time_policy.settlement_delay_seconds
warmup.warm_up_1d_bars
warmup.warm_up_4h_bars
```

### Fields excluded from `scenario_config_hash`

These fields must not affect `scenario_config_hash`:

```text
splits.calibration
splits.validation
notes
description
human-readable labels
comments
```

Reason: `splits.*` are later analysis windows. They do not affect replay execution and must not force a new `scenario_id` when changed.

## Date and bar-clock semantics

### Allowed date input type

Scenario dates must be ISO date strings:

```text
YYYY-MM-DD
```

Date timezone semantics:

- Dates are interpreted in UTC.
- Naive calendar dates are allowed only as dates with UTC exchange-bar semantics.
- Datetime strings are not accepted where a date is required.

Reject:

- invalid date strings;
- datetime strings where dates are required;
- `evaluation.start_date > evaluation.end_date`;
- unsupported timeframes;
- `execution.mode` values other than `disabled_historical_ohlcv_only`.

### Daily replay run time

For each `as_of_daily_bar_id`, Pre-2 simulates a daily replay run after the UTC daily bar is fully closed.

Default:

```text
daily_replay_run_time_utc = daily_bar_close_time_utc + settlement_delay_seconds
settlement_delay_seconds = 0
```

For `as_of_daily_bar_id = 2025-05-01`, the replay run may use only bars closed through the end of the UTC daily bar for 2025-05-01. It must not use bars from 2025-05-02.

### 1d point-in-time slice

For a replay run with `as_of_daily_bar_id = D`:

```text
available_1d_bars = all 1d bars with close_time_utc <= daily_replay_run_time_utc
```

No open/partial daily bar may be included.

### 4h point-in-time slice

For the same replay run:

```text
available_4h_bars = all 4h bars with close_time_utc <= daily_replay_run_time_utc
```

At UTC daily close this normally includes all six fully closed 4h bars for that UTC day:

```text
00:00-04:00
04:00-08:00
08:00-12:00
12:00-16:00
16:00-20:00
20:00-24:00
```

No open/partial 4h bar may be included.

### Closed-bar-only invariant

Pre-2 must not generate features, states, buckets, diagnostics, or event candidates from open or partial candles.

## Warm-up and symbol eligibility

A symbol is replay-evaluable for signal generation on the first daily replay date where all are true:

```text
at least warm_up_1d_bars closed 1d bars are available
and at least warm_up_4h_bars closed 4h bars are available
and the symbol is signal-evaluable according to Pre-1 universe / symbol completeness
```

Before this point:

```text
state_machine_state = null
state_confidence = null
state_transition_reason = null
setup_cycle_id = null
disposition_status = not_evaluable_warmup
disposition_reason = WARMUP_INSUFFICIENT
historical_signal_bucket = not_evaluable_warmup
```

Pre-2 must not emit one warm-up diagnostics row per symbol/day by default. Instead, record warm-up summary metadata in `replay_manifest.json` per symbol, including at least `first_evaluable_date` and `warmup_days_skipped`. Warm-up days must not generate signal events.

## Disposition and State Machine admission semantics

### State enum remains closed

Do not introduce new State Machine states. The only allowed non-null `state_machine_state` values are:

```text
watch
early_ready
confirmed_ready
late
chased
rejected
```

Before admission or when not evaluable, use `state_machine_state = null` plus disposition fields.

### Disposition fields

Pre-2 diagnostics must include:

```text
disposition_status
disposition_reason
```

Allowed `disposition_status` values:

```text
admitted
untracked
not_evaluable_warmup
not_evaluable_missing_data
```

Meanings:

| Value | Meaning |
|---|---|
| `admitted` | Symbol was fachlich evaluated through the State Machine for this replay date. |
| `untracked` | Symbol has no active setup context and was not admitted, for example phase none without prior active cycle. |
| `not_evaluable_warmup` | Warm-up is insufficient for signal evaluation. |
| `not_evaluable_missing_data` | Required bar data for this replay date is missing. |

`disposition_reason` must be a stable machine-readable reason code. Required reason codes include at least:

```text
PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE
WARMUP_INSUFFICIENT
MISSING_1D_BAR
MISSING_4H_CONTEXT
```

Additional reason codes may be added if required by repo reality, but must be stable and documented in tests.

### Null semantics

`state_machine_state = null` means no current State Machine state was assigned for this replay date. It must not be coerced to `watch`, `rejected`, `false`, or any pseudo-state string.

`state_confidence = null` means no state confidence was evaluated.

`setup_cycle_id = null` means no active setup cycle exists for this symbol at this replay date.

## T4 bypass and production module usage

Pre-2 must not call T4 or live OHLCV fetch.

Do not call:

```text
scanner/data/ohlcv_fetch.py
scanner/clients/mexc_client.py
MEXC API clients
```

Pre-2 must load Pre-1 Parquet OHLCV rows, convert/slice them into the same closed-bar input shape expected by production signal modules, and call T5–T12 production modules directly where possible.

Acceptance criterion:

```text
T5–T12 modules are importable without side effects:
  - no API clients initialized at import time
  - no SQLite connections opened at import time
  - no filesystem writes at import time
```

If side effects are found, fix the import boundary minimally. Do not copy fachliche signal logic into parallel replay-only implementations.

## Scan mode

Pre-2 implements only:

```text
scan_mode = historical_daily_replay
```

Do not implement:

```text
intraday_promotion_scan
4h-intraday transitions
multiple replay cycles per calendar day
```

4h data is used only as an input to the daily replay run.

## Replay-local state persistence

Pre-2 must never read from or write to live/shadow scanner state.

Replay state must be stored under a replay-specific path, for example:

```text
evaluation/replay/runs/<scenario_id>/<replay_id>/state.sqlite
```

Allowed equivalent paths are acceptable if they are clearly replay-scoped and recorded in `replay_manifest.json`.

Hard rules:

- No reads from live scanner state.
- No writes to live scanner state.
- No reuse of Shadow-Live state databases.
- No state leakage between different `scenario_id`s.
- No state leakage between different scenario hashes.

Persist at least:

```text
symbol
state_machine_state
state_confidence
state_transition_reason
setup_cycle_id
bars_since_state_entered
bars_since_early_entered
bars_since_confirmed_entered
close_at_early_entry_bar
close_at_confirmed_entry_bar
cycle_end_timestamp
bars_since_cycle_end
last_aging_daily_bar_id
freshness_distance_state_early
freshness_distance_state_confirmed
distance_from_ideal_entry_after_early
distance_from_ideal_entry_after_confirmed
last_evaluable_replay_date
consecutive_missing_1d_bars
consecutive_missing_4h_bars
```

Also persist all fields present in the production `StatePersistencePatch` dataclass or equivalent production state-persistence model, unless a field is proven irrelevant to historical replay and explicitly documented in the implementation notes. This prevents replay state from diverging from production state-machine semantics.

If repo reality has an existing canonical state model with additional required fields, reuse it as long as it does not read/write live state and does not conflict with this ticket.

## Daily replay loop

For each `as_of_daily_bar_id` in the inclusive evaluation date range:

```text
for each replay symbol:
  load previous replay-local state
  slice point-in-time 1d bars
  slice point-in-time 4h bars
  evaluate warm-up / missing-data disposition
  if evaluable:
    run T5–T12 production signal logic
    derive historical_signal_bucket
    persist updated replay state
    emit replay diagnostics
    emit event candidate if an event condition occurs
  else:
    carry or update non-evaluable replay metadata according to rules below
    emit diagnostics if configured
```

### State aging idempotency guard

Before applying any state-aging increment for a symbol, compare the current `as_of_daily_bar_id` with the persisted `last_aging_daily_bar_id`.

```text
if current as_of_daily_bar_id == persisted last_aging_daily_bar_id:
  skip bars_since_* aging increments
else:
  apply exactly one daily aging step if the symbol is evaluable for this bar
  set last_aging_daily_bar_id = current as_of_daily_bar_id
```

This guard is mandatory for replay restart/idempotency. Re-running the same replay day must not increment `bars_since_state_entered`, `bars_since_early_entered`, `bars_since_confirmed_entered`, or related aging fields a second time.


For symbols that become evaluable later in the replay window:

```text
Before eligibility:
  state_machine_state = null
  disposition_status = not_evaluable_warmup
  historical_signal_bucket = not_evaluable_warmup

On first eligible day:
  run normal production signal computation
  allow direct classification into watch / early_ready / confirmed_ready / late / chased / rejected if rules produce it
```

Direct first-day `confirmed_ready` is allowed if the production/v2.1 rules produce it.

## Missing data behavior

### Missing current 1d bar

If a symbol has no current 1d bar for `as_of_daily_bar_id`:

```text
do not evaluate the symbol for that day
do not increment bars_since_*
do not age state
do not create synthetic bars
do not forward-fill price
carry previous replay state unchanged
historical_signal_bucket = not_evaluable_missing_data
disposition_status = not_evaluable_missing_data
disposition_reason = MISSING_1D_BAR
increment consecutive_missing_1d_bars
```

No automatic `rejected`, `late`, `chased`, or stale transition may be triggered solely because a 1d bar is missing.

### Missing or incomplete 4h context

If a current 1d bar exists but 4h context is missing or incomplete:

```text
data_4h_available = false
data_resolution_class = daily_only or reduced, according to production conventions
consecutive_missing_4h_bars increments
```

Evaluate only if the production T5–T12 path supports the reduced-resolution/daily-only case.

Required state restrictions:

- `early_ready` is not allowed without 4h.
- `confirmed_ready` without 4h is allowed only if the v2.1/production daily-only constraints allow it.
- If required inputs are absent, set `historical_signal_bucket = not_evaluable_missing_data` and record `disposition_reason = MISSING_4H_CONTEXT`.

No 4h bars may be synthesized, forward-filled, or inferred.

### Longer gaps

For Pre-2 v1:

```text
State remains frozen for any length of consecutive missing 1d bars.
No automatic rejected / stale / chased transition is triggered solely by missing data.
```

Record these fields in diagnostics and event candidates:

```text
consecutive_missing_1d_bars
consecutive_missing_4h_bars
last_evaluable_replay_date
```

Backtest-1 may later exclude or separately analyze events after long missing-data gaps. Pre-2 must not implement that analysis.

## Execution-disabled semantics

Pre-2 must set:

```text
execution_mode = disabled_historical_ohlcv_only
execution_evaluation_status = not_evaluated_historical_ohlcv_only
```

Replay output field semantics:

```text
execution_status_raw = not_evaluated
execution_size_class = not_evaluated
execution_grade_effective = null
is_tradeable_candidate = null
```

`null` means not evaluated. It must not be coerced to `false` unless an existing output schema physically forbids null; if that happens, keep `execution_evaluation_status = not_evaluated_historical_ohlcv_only` and document the schema constraint in the manifest. Prefer nullable output for replay artifacts.

Pre-2 must not use execution fields in ranking or bucket decisions.

## Historical signal buckets

Pre-2 must emit:

```text
historical_signal_bucket
```

Allowed values:

```text
confirmed_candidates
early_candidates
watchlist
late_monitor
discarded
not_evaluable_warmup
not_evaluable_missing_data
```

Use the same bucket value names as live where applicable, but in the replay-only field `historical_signal_bucket`.

Hard rule:

```text
decision_bucket must not be written to replay diagnostics.
decision_bucket must not be written to replay_event_candidates.parquet.
historical_signal_bucket is the only bucket field in replay output.
```

### Historical bucket derivation

Pre-2 must use this narrow pre-execution mapping. Execution-conditioned live Decision rules do not apply because execution is deliberately disabled. `execution_status = disabled_historical_ohlcv_only` is not a pass, not a fail, and not an input to bucket assignment.

| Replay state / pattern condition | `historical_signal_bucket` |
|---|---|
| `state_machine_state = confirmed_ready` and `entry_pattern != none` | `confirmed_candidates` |
| `state_machine_state = confirmed_ready` and `entry_pattern = none` | `late_monitor` |
| `state_machine_state = early_ready` and `entry_pattern != none` | `early_candidates` |
| `state_machine_state = early_ready` and `entry_pattern = none` | `watchlist` |
| `state_machine_state = watch` | `watchlist` |
| `disposition_status = untracked` | `watchlist` |
| `state_machine_state in {late, chased}` | `late_monitor` |
| `state_machine_state = rejected` | `discarded` |
| `disposition_status = not_evaluable_warmup` | `not_evaluable_warmup` |
| `disposition_status = not_evaluable_missing_data` | `not_evaluable_missing_data` |

Live execution-fail demotion rules such as execution fail → `late_monitor` or execution fail → `discarded` are out of scope and must not be applied in Pre-2.


## Entry Pattern

Entry Pattern Resolution is in scope.

Pre-2 must emit, where evaluable:

```text
market_phase
market_phase_confidence
state_machine_state
entry_pattern
entry_pattern_score
historical_signal_bucket
```

Do not skip Entry Pattern Resolution merely because Execution is disabled.

## Replay outputs

Pre-2 must write replay artifacts under a replay-specific path, for example:

```text
evaluation/replay/runs/<scenario_id>/<replay_id>/
  replay_manifest.json
  replay_symbol_diagnostics.jsonl.gz
  replay_state_final.sqlite
  replay_event_candidates.parquet
```

Equivalent paths are acceptable if clearly replay-scoped and manifest-recorded.

### `replay_symbol_diagnostics.jsonl.gz`

The replay diagnostics must be line-oriented, deterministic, and include one record per symbol/replay date when a symbol is processed or intentionally recorded as not evaluable.

Diagnostic emission rules:

- `untracked` days must be emitted in replay diagnostics because the symbol is evaluable but has no active setup context.
- Warm-up days must not be emitted as one row per symbol/day; warm-up coverage is recorded only as an aggregate summary in `replay_manifest.json`.
- Missing-data days may be emitted when the symbol is otherwise in-scope but cannot be evaluated for the current replay date.

Required fields include at least:

```text
scenario_id
replay_id
as_of_daily_bar_id
symbol
disposition_status
disposition_reason
state_machine_state
state_confidence
state_transition_reason
setup_cycle_id
market_phase
market_phase_confidence
entry_pattern
entry_pattern_score
historical_signal_bucket
execution_mode
execution_evaluation_status
execution_status_raw
execution_size_class
execution_grade_effective
is_tradeable_candidate
signal_daily_close
consecutive_missing_1d_bars
consecutive_missing_4h_bars
last_evaluable_replay_date
data_4h_available
data_resolution_class
```

Do not include `decision_bucket`.

### `replay_event_candidates.parquet`

Pre-2 must write event candidates, without forward returns.

Minimum event types:

```text
first_early_ready
first_confirmed_ready
first_confirmed_with_entry_pattern
first_late
first_chased
first_rejected
```

Required fields per event:

```text
scenario_id
replay_id
symbol
event_type
as_of_daily_bar_id
event_timestamp_utc
state_machine_state
historical_signal_bucket
market_phase
market_phase_confidence
entry_pattern
entry_pattern_score
setup_cycle_id
signal_daily_close
consecutive_missing_1d_bars_at_event
consecutive_missing_4h_bars_at_event
```

Do not include:

```text
decision_bucket
next_daily_open
entry_reference_price
forward_return_*
MFE
MAE
```

Implementation note:

```text
Backtest-1 derives next_daily_open from the Pre-1 OHLCV history dataset.
Pre-2 must not pre-compute next_daily_open and must not calculate forward returns.
```

### `replay_manifest.json`

Required fields include at least:

```text
manifest_type = replay_manifest
schema_version
scenario_id
replay_id
scenario_config_hash
scenario_config_hash_excludes_splits = true
scanner_config_hash
scanner_config_ref
history_dataset_ref
history_manifest_ref
universe_manifest_ref
evaluation_start_date
evaluation_end_date
timeframes
universe_mode
daily_replay_time_policy
warm_up_1d_bars
warm_up_4h_bars
execution_mode
execution_evaluation_status
t4_bypass = true
production_modules_used
state_store_path
scenario_registry_path
warmup_summary_by_symbol
replay_symbol_diagnostics_path
replay_event_candidates_path
splits_recorded
created_at_utc
```

If `splits.*` exist in Scenario-YAML, record them in the manifest. Do not use them for Pre-2 evaluation or reporting.

## Determinism and ordering

Pre-2 must be deterministic for identical:

```text
Scenario-YAML operative fields
Pre-1 OHLCV history dataset
scanner_config_hash
code version
```

Deterministic ordering rules:

- Process `as_of_daily_bar_id` ascending.
- Process symbols ascending by normalized symbol.
- Write diagnostics sorted by `as_of_daily_bar_id`, then `symbol`.
- Write event candidates sorted by `as_of_daily_bar_id`, then `symbol`, then `event_type`.
- Avoid dict/set iteration order as a semantic tie-breaker.

For event de-duplication:

- Emit `first_*` events only once per symbol/setup cycle where applicable.
- Do not emit repeated `first_confirmed_ready` on every confirmed day.
- Include `setup_cycle_id` to separate new cycles.

## Numerical robustness

Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid or not evaluable and must not be passed through into numeric-looking outputs.

Required behavior:

- If a required numeric input is non-finite, set the affected field to null and record a diagnostic reason if production conventions allow that.
- If the production module fails fast on non-finite inputs, catch at the symbol/day boundary and emit `disposition_status = not_evaluable_missing_data` with a stable reason rather than aborting the entire replay.
- One bad symbol/day must not abort the full replay unless the scenario/config itself is invalid.

## Nullability / tri-state requirements

These replay fields are nullable:

```text
state_machine_state
state_confidence
state_transition_reason
setup_cycle_id
market_phase
market_phase_confidence
entry_pattern
entry_pattern_score
execution_grade_effective
is_tradeable_candidate
signal_daily_close
last_evaluable_replay_date
```

`null` means not evaluated, not admitted, or not available according to the field context. It must not be implicitly coerced to `false`, `0`, `watch`, `discarded`, or `rejected`.

## Not-evaluated vs failed

Not evaluated and evaluated-but-negative are separate states.

Examples:

- `not_evaluable_warmup` means insufficient warm-up, not a bad signal.
- `not_evaluable_missing_data` means required data is missing, not a rejected setup.
- `historical_signal_bucket = discarded` means the scanner evaluated the symbol and no actionable replay signal bucket applies.
- `execution_evaluation_status = not_evaluated_historical_ohlcv_only` means execution was deliberately disabled, not that execution failed.

## Proposed implementation shape

Codex should inspect the repo first and reuse existing helpers where appropriate. The exact file names may be adjusted to fit repo reality, but keep the boundaries below.

Recommended implementation shape:

```text
scanner/evaluation/replay/
  __init__.py
  scenario.py                    # Scenario-YAML parsing, validation, operative hash
  scenario_registry.py           # scenario_id/hash immutability tracking
  bar_slicer.py                  # point-in-time 1d/4h slicing from Pre-1 Parquet
  module_adapter.py              # T5–T12 invocation adapters, no copied fachliche logic
  replay_state_store.py          # replay-local SQLite state
  historical_daily_replay.py     # main replay loop
  replay_buckets.py              # historical_signal_bucket derivation
  replay_events.py               # event candidate detection/export
  replay_outputs.py              # manifest/diagnostics/event writers

scripts/
  run_historical_daily_replay.py # thin CLI accepting --scenario only

tests/evaluation/replay/
  ...
```

If a better namespace already exists, use it. Do not modify live scanner runtime modules except for minimal import-boundary fixes needed to make T5–T12 importable without side effects.

## Acceptance criteria

### AC1 — Scenario-YAML validation

- Valid Scenario-YAML loads into a typed config object.
- Missing required fields fail fast with clear errors.
- Invalid dates fail fast.
- Datetime strings where dates are required fail fast.
- Unsupported `execution.mode` fails fast.
- Unsupported timeframes fail fast.
- `splits.*`, if present, are validated but not used for replay evaluation.

### AC2 — Scenario immutability

- First run for a `scenario_id` records `scenario_config_hash`.
- Second run with the same `scenario_id` and same operative hash is allowed.
- Second run with the same `scenario_id` and different operative hash fails fast.
- Changing only `splits.*` does not change `scenario_config_hash` and does not require a new `scenario_id`.
- Scenario registry is stored at `evaluation/replay/scenario_registry.sqlite` and records scenario ID/hash metadata.

### AC3 — T4 bypass and import safety

- Pre-2 does not call T4 / live OHLCV fetch.
- Pre-2 does not call MEXC clients.
- T5–T12 production modules used by replay are importable without API/client/SQLite/filesystem side effects.
- No copied fachliche signal logic is introduced in replay-only modules.

### AC4 — Point-in-time slicing

- For each `as_of_daily_bar_id`, 1d slice includes only bars closed by `daily_replay_run_time_utc`.
- For each `as_of_daily_bar_id`, 4h slice includes only bars closed by `daily_replay_run_time_utc`.
- Bars from the following day are never included in the current daily replay run.
- Open/partial bars are never used.

### AC5 — Warm-up behavior

- Symbols before warm-up are represented by manifest-level warm-up summary metadata rather than mandatory per-symbol/day diagnostics rows.
- The manifest records per-symbol `first_evaluable_date` and `warmup_days_skipped`.
- Warm-up rows do not generate signal events.
- First eligible day may directly classify into `confirmed_ready` if production rules produce it.

### AC6 — Missing 1d behavior

- Missing current 1d bar freezes prior state.
- `bars_since_*` do not increment on missing-1d days.
- No synthetic/forward-filled price is generated.
- No automatic `rejected`, `late`, or `chased` transition is caused solely by missing data.
- `consecutive_missing_1d_bars` increments.

### AC7 — Missing 4h behavior

- Missing/incomplete 4h context sets `data_4h_available = false` or production-equivalent field.
- `early_ready` is not produced without 4h.
- Daily-only `confirmed_ready` only occurs if production/v2.1 rules allow it.
- Missing 4h context is recorded with stable diagnostics.

### AC8 — Replay-local state isolation

- Replay state is stored only under replay-scoped paths.
- No live/shadow state database is read or written.
- Runs with different `scenario_id`s do not share state.
- Persisted state contains the minimum required fields, including `last_aging_daily_bar_id` and all production `StatePersistencePatch` fields required for state-machine continuity.

### AC9 — Execution disabled semantics

- `execution_mode = disabled_historical_ohlcv_only`.
- `execution_evaluation_status = not_evaluated_historical_ohlcv_only`.
- `execution_status_raw = not_evaluated`.
- `execution_size_class = not_evaluated`.
- `execution_grade_effective = null`.
- `is_tradeable_candidate = null` unless a hard existing schema prevents null; if so, manifest documents the constraint.

### AC10 — Bucket output

- Replay outputs include `historical_signal_bucket`.
- Replay outputs do not include `decision_bucket`.
- Allowed historical bucket values are enforced and tested.
- Historical bucket derivation follows the explicit pre-execution mapping table in this ticket.
- Execution-conditioned live demotion rules are not applied.

### AC11 — Event candidate export

- `replay_event_candidates.parquet` is written.
- Minimum `first_*` event types are emitted only once per relevant symbol/setup cycle.
- Required event fields are present.
- No forward returns, `next_daily_open`, MFE, or MAE are written.
- `signal_daily_close` is present where applicable.
- `consecutive_missing_1d_bars_at_event` and `consecutive_missing_4h_bars_at_event` are present.

### AC12 — Replay manifest

- `replay_manifest.json` is written.
- Manifest includes scenario refs, hashes, input refs, time policy, state path, scenario registry path, output paths, execution mode, T4 bypass flag, warm-up summary, and production module list.
- Manifest records `splits.*` if provided, but indicates that Pre-2 did not evaluate them.

### AC13 — Determinism

- Identical scenario operative fields, input history, scanner config hash, and code version produce deterministic diagnostics/event ordering.
- Tests cover deterministic ordering for dates, symbols, and event rows.

### AC14 — Full-scope boundary

- Pre-2 does not fetch Binance data.
- Pre-2 does not compute forward returns.
- Pre-2 does not compute `next_daily_open`.
- Pre-2 does not compute MFE/MAE.
- Pre-2 does not run execution simulation.
- Pre-2 does not produce calibration/validation reports.

## Required tests

Implement focused tests. Use small fixtures and/or synthetic Parquet input; do not require network calls.

Minimum test cases:

1. **Scenario validation — valid scenario**
   - Load a complete valid Scenario-YAML.
   - Assert all typed fields are resolved.

2. **Scenario validation — invalid dates**
   - Reject invalid dates and datetime strings where dates are required.

3. **Scenario hash excludes splits**
   - Two scenarios differing only in `splits.*` have identical `scenario_config_hash`.
   - Two scenarios differing in `evaluation.start_date` have different hashes.

4. **Scenario immutability registry**
   - Same scenario/hash can run again.
   - Same scenario ID with different operative hash fails.
   - Registry metadata is persisted under `evaluation/replay/scenario_registry.sqlite`.

5. **Point-in-time 1d slicing**
   - Run for date D includes D's closed daily bar.
   - Run for date D does not include D+1.

6. **Point-in-time 4h slicing**
   - Run for date D includes only 4h bars closed by replay run time.
   - Open/partial 4h bars are excluded.

7. **Warm-up not evaluable**
   - Symbol with insufficient 1d/4h bars is recorded in replay manifest warm-up summary.
   - Manifest includes `first_evaluable_date` and `warmup_days_skipped` for the symbol.
   - No mandatory per-symbol/day warm-up diagnostics rows are required.
   - No event candidate is emitted.

8. **First eligible direct confirmed**
   - Fixture/stub production output representing first eligible day as `confirmed_ready` is accepted and event candidate emitted.

9. **Missing 1d freezes state**
   - Prior active state exists.
   - Current replay date has no 1d bar.
   - State unchanged.
   - `bars_since_*` unchanged.
   - `consecutive_missing_1d_bars` increments.

9a. **State aging idempotency guard**
   - Replaying the same `as_of_daily_bar_id` twice does not increment `bars_since_*` twice.
   - `last_aging_daily_bar_id` prevents duplicate aging on restart/rerun.

10. **Missing 4h blocks early**
   - 1d present, 4h missing.
   - `early_ready` is not emitted.
   - Missing 4h diagnostic fields are set.

11. **Execution disabled fields**
   - Output has disabled execution semantics exactly as specified.

12. **No decision_bucket**
   - `decision_bucket` absent from replay diagnostics and event candidates.

13. **Historical signal bucket values and mapping**
   - Allowed values only.
   - Same live bucket names where applicable, but in `historical_signal_bucket` field.
   - Explicit mapping cases are tested: confirmed+pattern, confirmed+no pattern, early+pattern, early+no pattern, watch, late/chased, rejected, warm-up, and missing-data.
   - Execution-conditioned live demotion rules are not applied.

14. **Event export schema**
   - Required event fields present.
   - No forward-return fields.
   - No `next_daily_open`.
   - No MFE/MAE.

15. **Replay state isolation**
   - Replay writes state only to replay-scoped path.
   - Test must ensure live/shadow state paths are not touched.

16. **Deterministic ordering**
   - Diagnostics and event candidates are sorted deterministically.

17. **Import side-effect guard**
   - Import the production modules required for T5–T12 adapter.
   - Assert no API clients, SQLite connections, or filesystem writes occur at import time using mocks/monkeypatches where practical.

18. **Backtest-1 boundary**
   - Assert Pre-2 output does not contain `entry_reference_price`, `next_daily_open`, forward returns, MFE, or MAE.

## Definition of Done

- Scenario-YAML is implemented as the canonical Pre-2 replay definition.
- Scenario immutability is enforced using an operative `scenario_config_hash` excluding `splits.*`, stored in `evaluation/replay/scenario_registry.sqlite`.
- Pre-2 reads Pre-1 OHLCV Parquet and Pre-1 manifests.
- Pre-2 bypasses T4 and does not call MEXC clients.
- Pre-2 uses production T5–T12 signal logic directly where possible and does not clone fachliche logic.
- Historical daily replay loop works over an inclusive evaluation date range.
- Replay-local state persistence is implemented and isolated from live/shadow state, including `last_aging_daily_bar_id` and required production `StatePersistencePatch` fields.
- Missing data and warm-up semantics match this ticket, including manifest-level warm-up summary instead of mandatory per-symbol/day warm-up diagnostics rows.
- Execution is disabled with explicit not-evaluated semantics.
- Replay outputs contain `historical_signal_bucket` and do not contain `decision_bucket`.
- `replay_event_candidates.parquet` exists and contains only event candidates, not returns.
- `replay_manifest.json` records all required provenance.
- Focused tests pass.
- Full test suite is run if practical.
- No Binance fetch, no forward-return evaluation, no MFE/MAE, no intraday replay, and no execution simulation are introduced.

## Suggested implementation notes

- Prefer small adapters around existing production modules over rewriting logic.
- If production module signatures are not easy to call directly, introduce a narrow adapter that converts replay bar inputs into production-compatible inputs.
- If a production module import has side effects, fix the side effect boundary rather than forking logic.
- Keep Scenario-YAML canonicalization stable: sorted keys, normalized date strings, no comments, no non-operative fields in hash.
- Keep output rows compact enough for long replay windows; gzip JSONL diagnostics are expected.
- Keep `replay_event_candidates.parquet` narrow and analysis-ready.

## Review notes for Martin / Claude

This draft incorporates the reviewed Pre-2 decisions:

1. Use `disposition_status` / `disposition_reason` without introducing pseudo-state enum values. If repo reality already has equivalent T10 names, map to those names without changing semantics.
2. Use a narrow pre-execution `historical_signal_bucket` mapper exactly as specified in this ticket. Do not reuse execution-conditioned live bucket demotion rules.
3. Do not emit mandatory warm-up diagnostics rows for every symbol/date. Record warm-up summary metadata in `replay_manifest.json` instead.
4. Production T5–T12 module boundaries still need repo-reality verification during implementation; if import side effects exist, fix the import boundary rather than cloning fachliche logic.
