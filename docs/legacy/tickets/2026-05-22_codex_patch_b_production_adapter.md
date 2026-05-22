> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# Codex Task: Patch B — Wire Production T5–T12 into Historical Replay Production Adapter

## Context

Patch A introduced `scanner/evaluation/historical_replay/production_adapter.py` with a clean adapter boundary. The default `HistoricalProductionAdapter` currently raises `NotImplementedError` because the production T5–T12 signal pipeline is not yet wired.

The current historical replay runner can now consume adapter outputs, but it still needs a real production adapter so the replay produces real signal outputs instead of placeholder/scaffold behavior.

Diagnostic context:
`docs/legacy/reports/2026-05-22__pre2_replay_runner_events0_diagnostic.md`

Approved Pre-2 ticket:
`docs/legacy/tickets/2026-05-18__BACKTEST_PRE_2__historical_daily_replay_harness.md`

## Goal

Implement `HistoricalProductionAdapter.__call__` or equivalent so the historical replay adapter calls the actual production T5–T12 signal pipeline using historical 1d/4h bars from Pre-1 Parquet history.

This patch must keep T4/live fetch bypassed and must not introduce execution, forward-return, or Backtest-1 logic.

## Required production call chain

The adapter must inspect and use the actual production modules and function signatures. Do not assume names or parameters. Read the modules before writing calls.

Intended production chain, subject to exact repo signatures:

```python
from scanner.features.bundle import build_feature_bundle
from scanner.axes.tier1 import compute_tier1_axes          # inspect for exact function name/signature
from scanner.axes.tier2 import compute_tier2_axes          # inspect for exact function name/signature
from scanner.phase.interpreter import compute_phase_interpretation  # inspect for exact name/signature
from scanner.state.invalidation import compute_invalidation_and_cycle  # inspect for exact name/signature
from scanner.state.machine import compute_state_machine    # inspect for exact function name/signature
from scanner.entry.patterns import resolve_entry_pattern   # inspect for exact name/signature
```

Also inspect:

```python
scanner/features/raw_1d.py
scanner/features/raw_4h.py
scanner/state/models.py
scanner/config.py
```

Do not wire calls based on guessed interfaces.

## Input construction

### 1. `bar_clock_context`

`build_feature_bundle(...)` requires a `bar_clock_context`.

For daily historical replay, construct it as a dict with at minimum:

```python
{
    "daily_bar_id": as_of_daily_bar_id,              # str, format "YYYY-MM-DD"
    "daily_close_time_utc_ms": daily_close_time_ms,  # int, derived from the current as-of daily bar row
}
```

Rules:

- `daily_bar_id` must be the replay `as_of_daily_bar_id` string in `YYYY-MM-DD` format.
- `daily_close_time_utc_ms` must be derived from the current as-of daily bar row's close timestamp field, e.g. `close_time_utc` or `close_time_utc_ms`.
- Do **not** synthesize `daily_close_time_utc_ms` from replay wall-clock time unless the bar row has no usable close timestamp.
- Do **not** include `intraday_bar_id` for daily replay.
- Do **not** include `intraday_close_time_utc_ms` unless the production modules explicitly require it for a daily run. Daily replay should be daily-only.

### 2. `ohlcv_1d` and `ohlcv_4h`

`build_feature_bundle(...)` accepts:

```python
ohlcv_1d: list[Any]
ohlcv_4h: list[Any] | None
```

The bar loader returns `pd.DataFrame`. Convert DataFrame rows to a list of lightweight bar objects with attribute access. Current raw feature modules expect attribute access through `hasattr(...)` / `getattr(...)`, not plain dict indexing.

Required bar object attributes:

```text
close_time_utc_ms
close
high
low
base_volume
quote_volume
```

Acceptable implementation choices:

- `dataclass(frozen=True)`
- `types.SimpleNamespace`
- a small local class

Do **not** pass plain dict rows unless you first verify and adapt `scanner/features/raw_1d.py` and `scanner/features/raw_4h.py` to support dict access. Avoid changing raw feature modules unless absolutely necessary.

Ordering and validity:

- Preserve strict ascending order by `close_time_utc_ms`.
- Do not include future bars beyond the replay `as_of` timestamp.
- Do not include open/partial bars.
- Convert numeric values to finite floats where appropriate.
- Raise a clear exception on missing required columns/attributes.

### 3. `PersistedStateMachineContext`

`scanner/state/machine.py` requires `PersistedStateMachineContext` from `scanner/state/models.py`. This is a validated dataclass, not a generic dict.

The adapter receives `persisted_state: dict` from `ReplayStateStore`. Convert it into a valid `PersistedStateMachineContext`.

Mapping rules:

- If `persisted_state` is empty or `None`, construct a bootstrap context:
  - `symbol` is required and non-empty
  - all other fields are `None`
- `prev_state_machine_state` maps from replay-state field `state_machine_state`
- `current_setup_cycle_id` maps from replay-state field `setup_cycle_id`
- map `previous_setup_cycle_id` if present
- map `state_recorded_in_cycle_id` if present
- map `last_aging_daily_bar_id` if present
- map all bars-since fields if present
- map all freshness/distance fields if present
- map entry close prices if present
- map cycle end fields if present
- map `reclaim_below_reset_floor_seen_since_cycle_end` if present

Validation requirements:

- `symbol` must be a non-empty string.
- `prev_state_machine_state` must be one of the allowed production state enum values or `None`.
- `last_aging_daily_bar_id` must match `YYYY-MM-DD` or be `None`.
- All `bars_since_*` fields must be non-negative integers or `None`.
- All price fields such as `close_at_early_entry_bar` and `close_at_confirmed_entry_bar` must be finite positive floats or `None`.
- Finite distance/freshness fields must satisfy the production dataclass validation.
- Do not silently coerce invalid state values. Fail fast.

### 4. `ScannerConfig` / config object

Load the scanner config from `scanner_config_ref` using the existing config loading mechanism. Inspect `scanner/config.py` and current production entrypoints for the correct loader/validation function.

Do not hardcode config values.

Do not pass a raw dict if production functions expect a typed/resolved config object. If production modules currently accept mapping-like config, keep the behavior consistent with production.

If the repo has multiple config resolvers for different layers, use the same production path used by the live daily scanner rather than inventing a replay-only config shape.

## Output construction

Return a `ReplayProductionOutput` populated from real production module outputs.

Required fields:

```text
disposition_status
disposition_reason
market_phase
market_phase_confidence
state_machine_state
state_confidence
state_transition_reason
setup_cycle_id
entry_pattern
entry_pattern_score
signal_daily_close
transition_event_types
updated_state_patch
production_modules_used
```

Mapping guidance:

- `market_phase` from phase interpreter output
- `market_phase_confidence` from phase interpreter output
- `state_machine_state` from state machine output
- `state_confidence` from state machine output
- `state_transition_reason` from state machine output
- `setup_cycle_id` from state machine / invalidation output
- `entry_pattern` from entry pattern resolver output
- `entry_pattern_score` from entry pattern resolver output
- `signal_daily_close` from the current as-of daily bar close
- `transition_event_types` from real state transitions
- `updated_state_patch` from production `StatePersistencePatch` / equivalent state output
- `production_modules_used` as actual module paths that were imported/called

If a production output shape is different, inspect the dataclass or return type and map explicitly. Do not guess field names.

## Historical bucket separation

Pre-2 must not emit or rely on live `decision_bucket`.

Rules:

- Inspect `scanner.decision.buckets` if needed.
- Do **not** use live `decision_bucket` as replay output.
- If `assign_bucket` depends on execution/tradeability, do **not** call it for historical bucket assignment.
- Pre-2 must continue to use the approved `historical_signal_bucket` mapping in `replay_runner.py`.
- `decision_bucket` must remain absent from replay diagnostics and `replay_event_candidates.parquet`.

The adapter should provide phase/state/entry outputs. The replay runner should derive `historical_signal_bucket` using the approved replay-specific mapping.

## Event emission rules

Derive `transition_event_types` from state machine output and previous persisted state.

Use `prev_state_machine_state` from `PersistedStateMachineContext` to detect transitions.

Required event logic:

```text
first_early_ready
  emit when state transitions into early_ready for the first time in cycle

first_confirmed_ready
  emit when state transitions into confirmed_ready for the first time in cycle

first_confirmed_with_entry_pattern
  emit when state is confirmed_ready and entry_pattern != "none"
  only emit on transition/first occurrence according to replay event semantics

first_late
  emit when state transitions into late for the first time in cycle

first_chased
  emit when state transitions into chased for the first time in cycle

first_rejected
  emit when state transitions into rejected for the first time in cycle
```

Do not emit repeated `first_*` events on subsequent days in the same state.

If production state output already has transition metadata, prefer that over re-inferring transitions. If not, use previous persisted context conservatively.

## Error handling

If any production module raises an exception:

- log the exception with `symbol` and `as_of_daily_bar_id` context,
- re-raise,
- do not return placeholder output,
- do not swallow exceptions,
- do not continue silently.

The replay runner should fail fast with meaningful context.

## State persistence patch

`updated_state_patch` must contain all fields required for next-day continuity.

At minimum:

```text
state_machine_state
state_confidence
state_transition_reason
setup_cycle_id
previous_setup_cycle_id
state_recorded_in_cycle_id
bars_since_state_entered
bars_since_early_entered
bars_since_confirmed_entered
close_at_early_entry_bar
close_at_confirmed_entry_bar
cycle_end_timestamp
cycle_end_bar_index
bars_since_cycle_end
last_aging_daily_bar_id
freshness_distance_state_early
freshness_distance_state_confirmed
distance_from_ideal_entry_after_early
distance_from_ideal_entry_after_confirmed
reclaim_below_reset_floor_seen_since_cycle_end
data_resolution_class
```

These values must be derived from production state-machine/invalidation outputs, not hard-coded.

If a field is not available from production output, document the gap and fail clearly or leave it `None` only if the production dataclass allows it and replay continuity remains valid.

## Hard constraints

Do not:

- call T4,
- call `mexc_client`,
- call any live API,
- fetch external data,
- compute forward returns,
- compute `next_daily_open`,
- compute MFE/MAE,
- implement execution grading,
- change Pre-1 fetch logic,
- modify `bar_loader.py`, `scenario.py`, or `scenario_registry.py` unless absolutely unavoidable,
- copy fachliche signal logic into `replay_runner.py`,
- change historical bucket mapping semantics,
- add `decision_bucket` to replay outputs,
- change replay output schemas except to populate already-approved fields with real values.

## Tests

Add focused tests in:

```text
tests/replay/test_historical_production_adapter.py
```

### Required test areas

1. Bar conversion / feature bundle entry

- Convert synthetic DataFrame rows to attribute-access bar objects.
- Verify the converted objects have required attributes.
- Verify the adapter reaches `build_feature_bundle(...)` successfully with converted bars.
- Do not require real Pre-1 Parquet data or network access.

2. `bar_clock_context`

- Verify `daily_bar_id` is `YYYY-MM-DD`.
- Verify `daily_close_time_utc_ms` comes from the current daily bar row.
- Verify no `intraday_bar_id` is present for daily replay.

3. `PersistedStateMachineContext` construction

- Empty persisted state -> valid context with all fields `None` except `symbol`.
- Valid persisted-state dict -> correctly mapped fields.
- Invalid state enum -> validation failure.
- Invalid negative bars-since field -> validation failure.
- Invalid `last_aging_daily_bar_id` -> validation failure.

4. Adapter output mapping

Use monkeypatch/stubs for downstream production functions where needed. Do not rely only on synthetic OHLCV accidentally triggering a real market phase.

Required assertions:

- Production phase output maps to `market_phase`.
- Production state output maps to `state_machine_state`, `state_confidence`, and `state_transition_reason`.
- Production entry output maps to `entry_pattern` and `entry_pattern_score`.
- `signal_daily_close` comes from the current daily bar close.
- `updated_state_patch` contains all required continuity fields.
- `production_modules_used` reflects actual adapter dependencies.

5. Event emission

Use controlled/stubbed state outputs:

- `prev_state = None`, new state `early_ready` -> `first_early_ready`
- `prev_state = early_ready`, new state `confirmed_ready`, `entry_pattern != "none"` -> `first_confirmed_ready` and/or `first_confirmed_with_entry_pattern` according to implemented event semantics
- `prev_state = confirmed_ready`, new state `confirmed_ready` -> no duplicate `first_confirmed_ready`
- state transitions to `late`, `chased`, `rejected` -> respective first events

6. Replay integration with adapter

Add or update runner-level tests if needed:

- Runner diagnostics use adapter-provided `market_phase`, not hard-coded `"none"`.
- Runner diagnostics use adapter-provided `state_machine_state`, not hard-coded `"watch"`.
- Runner diagnostics use adapter-provided `entry_pattern`, not hard-coded `"none"`.
- Runner emits event candidates when adapter provides event types.
- `decision_bucket` remains absent.
- `next_daily_open` and `forward_return_*` remain absent.

### Testing strategy note

Synthetic OHLCV may not naturally trigger meaningful market phases. Use monkeypatching/stubs to prove wiring and mapping. Include at least one test that reaches `build_feature_bundle(...)` with converted bar objects.

Do not require the real Pre-1 history dataset in unit tests.

## Implementation notes

- Keep adapter code narrow and explicit.
- Prefer small helper functions:
  - DataFrame row -> bar object
  - current daily bar -> `bar_clock_context`
  - replay state dict -> `PersistedStateMachineContext`
  - production outputs -> `ReplayProductionOutput`
  - state machine output -> event types
  - production persistence patch -> replay-state patch
- Fail fast with clear exceptions when production signatures or outputs do not match expectations.
- Update `replay_manifest.production_modules_used` to reflect actual adapter calls.
- Remove or avoid misleading production-module claims.

## Report

After implementation, report:

- files changed,
- which production modules are actually called,
- exact function signatures inspected and used,
- how `bar_clock_context` is constructed,
- how OHLCV DataFrames are converted to production bar lists,
- how `PersistedStateMachineContext` is constructed from `ReplayStateStore` dict,
- how scanner config is loaded,
- how event types are derived,
- any production module signature mismatches found,
- focused pytest result,
- what a first real replay run should now produce differently vs. scaffold behavior.
