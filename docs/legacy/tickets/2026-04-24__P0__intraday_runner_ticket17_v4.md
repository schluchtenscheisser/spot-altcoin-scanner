> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Implement intraday promotion runner and resolve intraday execution frequency policy (Ticket 17)

## Context / Source

This ticket implements **Ticket 17** from the Independence-Release consolidated concept: the **Intraday Promotion Runner** (`intraday_promotion_scan`).

It builds on:

```yaml
depends_on: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
```

The authoritative fachliche source set for this ticket is:

- the 7 uploaded v2.1 section files, especially `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md`
- `independence_release_gesamtkonzept_final.md`
- `docs/canonical/open_questions.md`, specifically the remaining intraday part of §21/3

If the current authoritative source set, existing repo-authority/canonical documents, and existing code conflict, the current authoritative source set wins. Repo documents remain in force only insofar as they do not contradict this source set. Do not create a second competing authority.

The addendum (`v2_1_addendum_for_future_tickets_and_new_chats_updated.md`) is supplemental working context only. It does not override the source set above.

### Primary spec references

- Abschnitt 6 §§1–4: Daily vs Intraday Update Policy, scan modes, universe selection, field classes
- Abschnitt 6 §§8–9: execution subset and cache policy
- Abschnitt 6 §§11–16: intraday operational behavior, scheduling, persistence, and failure modes
- Abschnitt 4: State Machine invariants, especially 4h requirement for `early_ready`
- Abschnitt 5: Invalidation and setup-cycle continuity
- Abschnitt 7: Entry Pattern and Decision Bucket order
- Ticket 15: daily runner architecture and canonical `daily_bar_id`
- Ticket 16: execution adapter and daily execution subset precedent

---

## Important framing for this ticket

This ticket implements the **intraday runner**, not a second daily runner.

The intraday runner is a reduced, cache-aware, 4h-driven follow-up run. It must not perform broad universe discovery, must not recompute Daily-only fields, and must not silently introduce a new storage, execution, ranking, or decision model.

The runner's purpose is to detect and persist promotion/decay transitions inside the already monitored universe:

- `watch -> early_ready`
- `early_ready -> confirmed_ready`
- `watch/early_ready/confirmed_ready -> late`
- `watch/early_ready/confirmed_ready/late -> chased`
- state/cycle continuation, invalidation, and diagnostics for monitored symbols

This ticket also resolves the still-open intraday part of **§21/3 Execution frequency + Top-N policy**:

> Intraday execution subset selection adopts Abschnitt 6 §8.2 inside the already reduced intraday monitoring universe. No fachlicher Top-N cap is applied. Optional safety limits are technical hard-fail or run-incomplete guards only and must never act as silent business ranking/truncation.

---

## Explicit decisions carried by this ticket

### 1. `daily_bar_id` contract

`daily_bar_id` was resolved by Ticket 15 and is not re-decided here.

Canonical type and format:

```text
str, YYYY-MM-DD
```

T17 must reuse this contract unchanged for `daily_cache_bar_id` and any runner-facing daily bar provenance. No new conversion boundary, dual representation, or `int` fallback is permitted. If existing code in the T17 call graph still emits or expects `daily_bar_id` as `int`, Codex must repair that occurrence to the T15 canonical string contract rather than invent a third representation.

### 2. `intraday_bar_id` / `intraday_cache_bar_id` contract

This ticket introduces the canonical 4h bar identifier used by the intraday runner.

Canonical type and format:

```text
str, YYYY-MM-DDTHH:00:00Z
```

Rules:

- UTC only.
- `HH` must be one of `{00, 04, 08, 12, 16, 20}`.
- The ID represents the **last fully closed 4h bar**, not the runner invocation timestamp.
- The owner is `scanner/data/bar_clock.py`.
- The runner must not duplicate 4h clock logic locally.

Required bar-clock helpers:

```python
def get_last_closed_intraday_bar_id(now_utc: datetime, timeframe: str = "4h") -> str: ...

def has_new_intraday_bar(previous_bar_id: str | None, current_bar_id: str) -> bool: ...
```

Validation requirements:

- `timeframe="4h"` is supported in this ticket.
- Unsupported timeframes raise `ValueError`.
- Naive datetimes are invalid unless an existing bar-clock contract already normalizes them explicitly to UTC. Do not silently assume local time.
- Non-canonical previous bar IDs raise a clear validation error when used for freshness comparison.

For `frequency_hours = 6`, the data basis and bar IDs remain 4h-based. The `6h` value controls trigger cadence only; it does not create a 6h bar format.

### 3. Intraday monitoring universe

The intraday runner processes only the reduced monitoring universe.

A symbol is included if at least one condition is true, using the last persisted/available state before the current intraday recompute:

- `state_machine_state in {watch, early_ready, confirmed_ready, late}`
- or `decision_bucket in {watchlist, early_candidates, confirmed_candidates, late_monitor}`
- or `market_phase_confidence >= cfg.intraday.min_phase_confidence_for_monitoring`

Default:

```yaml
intraday:
  min_phase_confidence_for_monitoring: 55
```

Hard exclusions by default:

- `rejected`
- `chased`

These symbols are not followed intraday unless an explicit reset-check path is enabled. `discarded` is not a monitoring-universe hard exclusion in T17 because Abschnitt 6 §3.2 names only `rejected` and `chased` as default intraday follow-up exclusions. A symbol with `decision_bucket = discarded` may still enter the monitoring universe if it qualifies via the state or phase-confidence OR-rule. `discarded` remains an execution-subset exclusion and must not receive execution data.

Default reset-check behavior:

```yaml
intraday:
  enable_reset_check: false
```

T17 must not implement a broad reset scan. With `enable_reset_check = false`, `rejected` and `chased` symbols remain excluded. If a reset-check stub already exists, it may be called only when explicitly enabled; otherwise no reset behavior is introduced by this ticket.

### 4. Intraday execution subset policy (§21/3 resolution)

Within the reduced intraday monitoring universe, execution data is fetched only after a pre-execution decision pass identifies the execution-relevant subset.

Execution is requested for a symbol if at least one condition is true after the current intraday structural/state recompute and pre-execution decision pass:

- `state_machine_state in {early_ready, confirmed_ready, late}`
- or `market_phase_confidence >= cfg.execution.min_phase_confidence`
- or `decision_bucket` is in the active observed bucket set

Default:

```yaml
execution:
  min_phase_confidence: 60
```

Active observed bucket set for this ticket:

```text
{watchlist, early_candidates, confirmed_candidates, late_monitor}
```

Hard exclusions from execution:

- `state_machine_state in {rejected, chased}`
- `decision_bucket = discarded`
- symbol skipped due to stale 4h refresh failure
- symbol missing required Daily cache
- symbol not in the intraday monitoring universe

No fachlicher Top-N cap is permitted.

Optional safety limit:

```yaml
intraday:
  max_execution_subset_size: null
```

Semantics:

- `null` means no safety limit.
- If set to a positive integer and the execution subset exceeds the limit, the runner must not silently truncate by rank.
- It must either hard-fail before execution fetch or mark the run as incomplete using an existing run-status/report mechanism. Prefer hard-fail unless the repo already has a canonical incomplete-run status.
- If the repo has no canonical incomplete-run status, do not invent one silently; hard-fail with a clear error.

### 5. Decision sequence

The intraday runner must use the same conceptual execution integration pattern as Ticket 16:

1. **pre-execution decision pass**
2. **execution fetch/grade**
3. **post-execution decision pass**

The pre-execution pass must not use stale execution data. It exists to derive provisional buckets and the execution subset.

The post-execution pass receives fresh `ExecutionInputContract` data only for the symbols fetched in the current run. Symbols without fresh execution data remain in the correct pending/reduced-finality state as defined by T12/T16. They must never receive execution fields from previous runs as current decision inputs.

---

## Goal

After this ticket is completed:

- `scanner/runners/intraday.py` exists and implements the canonical Independence-Release intraday promotion runner.
- The runner uses the T15 runner architecture and T16 execution adapter call pattern.
- `scanner/data/bar_clock.py` owns canonical 4h closed-bar ID generation and comparison.
- Intraday runs are driven by `intraday_bar_id` in `YYYY-MM-DDTHH:00:00Z` format.
- Daily-only fields are loaded from Daily cache and are never recomputed inside an intraday run.
- 4h-sensitive fields are refreshed only when a new closed 4h bar exists and fresh 4h data is available.
- State-internal fields are updated for every included and evaluable symbol.
- Execution fields are fetched only for the explicit intraday execution subset and are never reused across runs for current decisions.
- Failure paths for no new 4h bar, missing Daily cache, and stale 4h refresh failure are explicitly separated.
- The open intraday part of §21/3 is resolved in `docs/canonical/open_questions.md`.
- No new OHLCV storage/read layer is introduced; the runner uses the T14-canonical OHLCV reader/writer contracts.

---

## Scope

Allowed change surface:

- `scanner/runners/intraday.py` (new)
- `scanner/runners/__init__.py` (if needed)
- `scanner/main.py` or CLI dispatch code (only to expose/route `intraday_promotion` mode if the repo has a mode-based entrypoint)
- `scanner/data/bar_clock.py` (add canonical 4h intraday helpers)
- `scanner/config.py` or central config resolver (intraday config block and validation)
- T14-canonical OHLCV reader usage only; no new storage layer
- T15/T16 runner integration points as needed, without changing their fachliche contracts
- report/diagnostics/run-metadata wiring needed to represent intraday run outputs and skip reasons
- tests under `tests/**`
- `docs/canonical/DATA_MODEL.md` for `intraday_bar_id` / `intraday_cache_bar_id` if that file exists and already owns field contracts
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` for intraday cadence/bar-clock behavior if that file exists
- `docs/canonical/open_questions.md` to mark the intraday part of §21/3 as resolved by T17

Do not create new canonical doc files unless the repo already uses them as active canonical paths. Do not manually edit generated `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

## Out of Scope

This ticket must not:

- implement broad universe discovery for intraday
- recompute Daily-only fields during intraday
- introduce a fachlicher Top-N execution cap
- implement a new execution grading model
- modify T16 execution thresholds except through already canonical config contracts
- implement a broad reset scan for `rejected` / `chased`
- resolve `dist_to_base_mid_pct`
- change the meaning of `daily_bar_id`
- introduce a 6h bar ID format
- create a new OHLCV storage or reader layer
- change the long-term history architecture beyond using the T14-canonical reader/writer
- implement evaluation, replay, forward returns, or scheduling infrastructure
- silently extend report schemas without updating the owning canonical schema/documentation

---

## Config contract

New or extended config block:

```yaml
intraday:
  frequency_hours: 4
  min_phase_confidence_for_monitoring: 55
  enable_reset_check: false
  max_execution_subset_size: null
```

Validation:

- `frequency_hours` must be integer `4` or `6`. Other values raise `ValueError`.
- `min_phase_confidence_for_monitoring` must be a finite number in `0..100`. `None`, `NaN`, `inf`, `-inf`, strings, and booleans are invalid.
- `enable_reset_check` must be boolean.
- `max_execution_subset_size` must be `null` or a positive integer. Floats, booleans, `0`, negative values, `NaN`, and `inf` are invalid.

Override semantics:

> Partial overrides in `intraday` are merged field-wise with central defaults; missing subkeys use their defaults and are not treated as invalid. Invalid types or out-of-range values raise a clear config validation `ValueError` naming the offending key. No ad-hoc raw-dict fallback is permitted.

6h advisory:

If `frequency_hours = 6`, config resolution or runner startup must emit a warning with this meaning:

```text
6h intraday frequency selected — Abschnitt 5 freshness thresholds are calibrated for 4h cadence and may produce premature timing invalidations. Consider loosening freshness thresholds after empirical validation.
```

Do not automatically adjust freshness thresholds.

Numerical robustness:

> Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid or not evaluable inputs and must not be passed through into numeric-looking outputs.

---

## Runner execution sequence

### Phase 0 — Run setup and bar-clock

1. Resolve config and validate `cfg.intraday`.
2. Determine `daily_bar_id` using the T15/T1 canonical daily bar-clock contract: `str YYYY-MM-DD`.
3. Determine `intraday_bar_id` using `scanner/data/bar_clock.py`: `str YYYY-MM-DDTHH:00:00Z`, last fully closed 4h bar.
4. Create run metadata with:

```text
scan_mode       = intraday_promotion
status          = running
daily_bar_id    = <YYYY-MM-DD>
intraday_bar_id = <YYYY-MM-DDTHH:00:00Z>
started_at_utc  = <UTC ISO 8601>
finished_at_utc = null
```

Use the existing T1/T15 `run_metadata` schema. Do not add columns unless an existing migration mechanism and schema owner already authorize them.

### Phase 1 — Monitoring universe

5. Load the latest persisted candidate/state/decision context needed to form the intraday monitoring universe.
6. Include only symbols matching the monitoring universe rule from this ticket.
7. Apply monitoring hard exclusions (`rejected`, `chased`) unless `enable_reset_check = true` and an existing reset-check path is explicitly available. Do not apply `discarded` as a monitoring hard exclusion; keep it as an execution-subset exclusion only.
8. If the monitoring universe is empty, complete a non-publishable/no-op intraday run with structured metadata and no execution fetch.

### Phase 2 — 4h freshness gate

9. Load the previous **run-level** intraday processing context from run metadata, not from any single symbol cache row. The run-level value represents the most recent closed 4h bar for which the intraday runner completed a publishable or clean no-op processing decision. It is separate from the per-symbol `intraday_cache_bar_id` field defined by Abschnitt 6 §9.2.
10. Also inspect per-symbol intraday cache state for the current monitoring universe. A symbol is refresh-required if its per-symbol `intraday_cache_bar_id` is missing, older than `current_intraday_bar_id`, or its last intraday status for the current bar indicates `STALE_4H_REFRESH_FAILED`.
11. Compute `has_new_intraday_bar(previous_run_level_intraday_bar_id, current_intraday_bar_id)`.
12. A run-level `NO_NEW_4H_BAR` no-op is permitted only if both are true:
    - `has_new_intraday_bar(...) == False`, and
    - no monitoring symbol is refresh-required for the current `intraday_bar_id`.
13. If the no-op condition is met:
    - do not fetch 4h OHLCV,
    - do not execute pre/post decision passes,
    - do not fetch execution data,
    - complete the run as a clean no-op with `skip_reason = no_new_4h_bar`,
    - persist run metadata/report diagnostics according to the existing output schema.

This is a run-level no-op. It is not an error. If at least one monitoring symbol is refresh-required, the runner must continue to Phase 3 even when the run-level previous bar ID equals the current bar ID. This allows retrying symbols that previously failed the fresh 4h fetch for the same closed 4h bar.

### Phase 3 — Per-symbol cache and 4h refresh

For each monitoring symbol independently:

14. Load cached Daily-only values and `daily_cache_bar_id`.
15. Validate that cached Daily-only values are compatible with current `daily_bar_id` and section 6 cache rules. A Daily cache is considered unusable if `daily_cache_bar_id` does not exactly match the current `daily_bar_id` — i.e. a newer Daily bar has already closed but the Daily runner has not yet processed it. Both missing and mismatched `daily_cache_bar_id` map to `MISSING_DAILY_CACHE`; do not invent a separate stale-daily reason in T17.
16. If required Daily cache is missing or unusable:
    - mark symbol as not evaluable for this intraday run,
    - set reason `MISSING_DAILY_CACHE`,
    - do not run phase/state/entry/decision for current promotion,
    - do not fetch execution,
    - continue with other symbols.
17. Before fetching 4h OHLCV, check whether the per-symbol `intraday_cache_bar_id` already equals `current_intraday_bar_id` and the symbol is not marked refresh-required per step 10. If so, use the existing per-symbol 4h cache for the current bar and proceed directly to bundle construction. Otherwise, fetch fresh 4h OHLCV using the T14-canonical OHLCV reader/fetch path for the current `intraday_bar_id`.
18. If fresh 4h fetch succeeds:
    - compute 4h-sensitive raw fields,
    - update `intraday_cache_timestamp` and `intraday_cache_bar_id`,
    - proceed to bundle construction.
19. If a newer closed 4h bar exists but fresh 4h data cannot be fetched for this symbol:
    - set `intraday_skipped_stale_4h = true`,
    - reason `STALE_4H_REFRESH_FAILED`,
    - skip this symbol for current intraday decisions,
    - do not use the previous 4h cache for current decisions,
    - continue with other symbols.

Mandatory sentence for implementation comments/tests:

> If a newer closed 4h bar exists but fresh 4h data cannot be fetched for a symbol, the previous 4h cache must not be used for current intraday decisions.

### Phase 4 — Feature/bundle construction

20. Build layer inputs per symbol from:
    - cached Daily-only values,
    - current-bar 4h-sensitive values for the current `intraday_bar_id` (freshly fetched or validly cached per Phase 3),
    - persisted state/cycle context.
21. Daily-only feature computation functions must not be called during an intraday run, regardless of whether 1d OHLCV data happens to be loaded.
22. If the symbol only has Daily fallback / reduced resolution according to upstream contracts:
    - preserve `reduced_resolution = true` flags,
    - preserve `data_4h_available = false` where appropriate,
    - ensure `early_ready` remains impossible per Abschnitt 4.

This phase is symbol-by-symbol conditional. Do not implement a uniform bundle build that assumes all monitoring symbols have fresh 4h data.

### Phase 5 — Fachliche recompute

For each evaluable symbol:

23. Recompute Tier-1/Tier-2 bundles from cached Daily-only + current-bar 4h-sensitive inputs (freshly fetched or validly cached per Phase 3).
24. Recompute Phase Interpretation.
25. Load persisted state/cycle context. This is a targeted load of the T9/T10 fachliche input fields required for invalidation and state-machine recompute, specifically: `freshness_distance_state_early`, `freshness_distance_state_confirmed`, `cycle_end_bar_index`, `cycle_end_timestamp`, all `bars_since_*` fields, prior `state_machine_state`, and prior `setup_cycle_id`. If Phase 1 already loaded a full state record including these fields, a second database read is not required; the Phase 1 loaded record may be used directly. If Phase 1 loaded only summary context for monitoring-universe selection, the runner must perform this targeted load before T9/T10 recompute.
26. Recompute invalidation and setup-cycle detection.
27. Recompute State Machine.
28. Persist updated state/cycle fields through the canonical state persistence interface.
29. Recompute Entry Pattern.

Ordering must remain consistent with the v2.1 layer order:

```text
Eligibility/context -> Features -> Tier-1 -> Tier-2 -> Phase -> Invalidation/Cycle -> State -> Entry -> Decision -> Execution -> Decision refresh
```

No output/diagnostic publication may precede required state persistence for an evaluable symbol.

### Phase 6 — Pre-execution decision pass

30. Run the decision/bucket/ranking layer without fresh execution data.
31. Use only current-run structural/state/entry outputs and no stale execution values.
32. Mark execution-required/pending status according to the existing T12/T16 contract.
33. Select the execution subset using the T17 intraday §8.2 rule.
34. Validate optional safety limit. Do not truncate.

### Phase 7 — Execution fetch/grade

35. Call the Ticket-16 execution adapter for the selected subset only.
36. Execution adapter results are run-local and fresh only for this intraday run.
37. If execution fetch/grading fails for a single symbol, preserve per-symbol fault isolation: that symbol receives the T16-defined unknown/not-evaluable execution status and current-run decision handling continues according to T16/T12. Do not abort the full run unless the failure is shared infrastructure.
38. Do not cache execution data across scans for decision purposes.

### Phase 8 — Post-execution decision pass

39. Re-run the decision/bucket/ranking layer with fresh `ExecutionInputContract` values for symbols that received them in this run.
40. Symbols without fresh execution data must remain in the correct pending/reduced-finality state.
41. No stale execution values may be used.
42. Produce deterministic final ranking and buckets.

### Phase 9 — Output, diagnostics, and run finalization

43. Write intraday run report artifacts using the existing T13/T15 report/output conventions.
44. Include run-level diagnostics for:
    - `scan_mode = intraday_promotion`
    - `daily_bar_id`
    - `intraday_bar_id`
    - monitoring universe count
    - excluded count
    - missing Daily cache count
    - stale 4h refresh skipped count
    - execution subset count
    - execution fetched count
    - no-op skip reason, if applicable
45. Include per-symbol diagnostics for:
    - Daily cache status
    - 4h refresh status
    - `intraday_skipped_stale_4h`
    - `data_4h_available`
    - reduced-resolution flags
    - state transition reason
    - decision bucket
    - execution status/current-run freshness
46. Update only intraday-owned index paths and generic run metadata indexes atomically after all required run artifacts are written. T17 must not overwrite or replace index files that are semantically owned by the Daily runner, such as `latest_daily.json`, unless T13/T15 explicitly defines that file as a shared latest-result pointer. Codex must inspect the T13/T15 index contract before writing any index path. If no intraday-specific index path exists, add the minimal explicitly named intraday path in the owning output schema/canonical docs in the same PR; do not silently invent ad-hoc index files.
47. Set run metadata to `completed` or `failed` in a `finally` path. A run must not remain terminally `running`.

---

## Failure modes and semantic separation

### Run-level no-op: `EMPTY_MONITORING_UNIVERSE`

Meaning:

- The runner started successfully.
- The monitoring-universe selection produced zero symbols after applying the OR-rule and monitoring hard exclusions.

Behavior:

- No 4h fetch.
- No pre/post decision pass.
- No execution fetch.
- Run completes successfully with `skip_reason = empty_monitoring_universe`.
- Run metadata and a minimal run-scoped report/diagnostic record are written.
- No Daily-owned index files are updated.
- If an intraday-owned recent-runs or audit index exists, it may be updated atomically as an operational audit entry only; otherwise no index update is required.
- No refreshed candidate/bucket outputs are published.
- This is not a failure and must not be reported as a negative evaluation.

### Run-level no-op: `NO_NEW_4H_BAR`

Meaning:

- The runner started successfully.
- The current closed 4h bar ID equals the previous run-level processed `intraday_bar_id`.
- There is no new 4h information to process and no monitoring symbol is refresh-required for the current bar.

Behavior:

- No 4h fetch.
- No execution fetch.
- No decision refresh.
- Run completes successfully with `skip_reason = no_new_4h_bar`.
- This is not a failure and must not be reported as a negative evaluation.

Publishing behavior:

- A `NO_NEW_4H_BAR` run writes run metadata and a minimal run-scoped report/diagnostic record with `skip_reason = no_new_4h_bar`.
- It must not update Daily-owned index files.
- It must not publish refreshed candidate/bucket outputs because no decision refresh occurred.
- If an intraday-owned recent-runs or audit index exists, it may be updated atomically as an operational audit entry only; otherwise no index update is required.

### Per-symbol not evaluable: `MISSING_DAILY_CACHE`

Meaning:

- The symbol is in the monitoring universe.
- Required Daily-only cached values are missing or incompatible.

Behavior:

- Symbol is not evaluable for intraday promotion.
- Current symbol does not proceed to state/entry/decision/execution.
- Run continues for other symbols.
- `null` means not robustly evaluable and must not be coerced to `false`.

### Per-symbol skipped stale 4h: `STALE_4H_REFRESH_FAILED`

Meaning:

- A newer closed 4h bar exists.
- Fresh 4h data could not be fetched for the symbol.
- Previous 4h cache is stale for current intraday decisions.

Behavior:

- Set `intraday_skipped_stale_4h = true`.
- Do not use prior 4h cache for current decisions.
- Do not fetch execution.
- Symbol is skipped for current intraday decisions.
- Run continues for other symbols.

### Symbol-local operational failure

Examples:

- malformed single-symbol OHLCV payload
- single-symbol fetch timeout after retries
- single-symbol execution adapter unknown result

Behavior:

- Preserve per-symbol fault isolation.
- Continue other symbols.
- Record structured warning with `symbol`, `stage_of_failure`, `exception_type`, and reason.

### Shared infrastructure failure

Examples:

- state database unreachable at run start
- canonical OHLCV reader unavailable globally
- report/index writer cannot write required artifacts
- shared typed contract violation not attributable to one symbol

Behavior:

- Abort run.
- Set run metadata `failed`.
- Do not update index files.
- Re-raise so the process exits non-zero.

---

## Invariants

1. Intraday must not perform broad universe discovery.
2. Intraday must not recompute Daily-only fields.
3. Daily-only feature computation functions must not be called during an intraday run, regardless of whether 1d OHLCV data happens to be loaded.
4. Intraday may refresh only 4h-sensitive, state-internal, and required execution/orderbook data according to field class rules.
5. Execution data is never valid across scans for current decisions.
6. If a newer closed 4h bar exists and fresh 4h fetch fails, old 4h cache is forbidden for current decisions.
7. `early_ready` remains impossible without valid 4h data.
8. `rejected` and `chased` cannot return to active states without a new `setup_cycle_id` and explicit reset path.
9. `null` / not evaluable must not collapse to `false` / negative evaluation.
10. At identical input, config, persisted context, and bar IDs, outputs, ordering, statuses, and reasons are deterministic.
11. Dict/set iteration order must not determine ranking, subset selection, output order, or reason ordering.
12. Index files must not point to a partially written or failed run.

---

## Acceptance Criteria

1. `scanner/runners/intraday.py` exists and exposes the canonical intraday runner function. Recommended signature:

```python
def run_intraday_scan(cfg, now_utc: datetime | None = None) -> None: ...
```

If the repo already has a runner signature convention from T15, use that convention and document the chosen signature in tests.

2. CLI/main dispatch can invoke the intraday runner using the repo's existing mode mechanism. It must not replace the daily runner.
3. `scanner/data/bar_clock.py` exposes `get_last_closed_intraday_bar_id(..., timeframe="4h") -> str` and `has_new_intraday_bar(...) -> bool`.
4. `intraday_bar_id` format is exactly `YYYY-MM-DDTHH:00:00Z`, UTC-aligned with `HH in {00, 04, 08, 12, 16, 20}`.
5. `daily_bar_id` remains `str YYYY-MM-DD`; no `int` representation is introduced in the T17 runner call graph.
6. `cfg.intraday.frequency_hours` accepts exactly `4` or `6`. Invalid values raise `ValueError`.
7. `frequency_hours = 6` emits the required warning and does not modify thresholds.
8. `cfg.intraday.min_phase_confidence_for_monitoring` default is `55` and rejects non-finite values.
9. `cfg.intraday.enable_reset_check` default is `false`.
10. `cfg.intraday.max_execution_subset_size` default is `null`; if set and exceeded, the runner does not truncate the subset.
11. Monitoring universe inclusion follows the OR-rule for state, bucket, and phase confidence.
12. `rejected` and `chased` are excluded from the monitoring universe by default. `discarded` is not a monitoring hard exclusion, but remains excluded from execution.
13. Empty monitoring universe completes cleanly without execution fetch and follows the `EMPTY_MONITORING_UNIVERSE` publishing behavior.
14. No new 4h bar completes cleanly with `skip_reason = no_new_4h_bar` and no execution fetch only when no monitoring symbol is refresh-required for the current bar.
15. Missing Daily cache or mismatched `daily_cache_bar_id` produces `MISSING_DAILY_CACHE` for that symbol and does not abort the full run.
16. Newer 4h bar + failed fresh 4h fetch produces `intraday_skipped_stale_4h = true` and `STALE_4H_REFRESH_FAILED`; old 4h cache is not used.
17. Daily-only feature computation functions are not called during intraday runs. This is covered by tests using mocks/spies or equivalent call assertions.
18. Per-symbol bundle construction branches correctly for fresh 4h data, cached valid 4h data when no new bar exists, missing Daily cache, and stale 4h refresh failure.
19. Reduced-resolution flags are preserved when only fallback data is available.
20. `early_ready` is not emitted for symbols without valid 4h data.
21. State/cycle context is loaded before invalidation/state recompute and persisted before output publication.
22. Pre-execution decision pass runs without stale execution data.
23. Execution subset follows Abschnitt 6 §8.2 within the reduced intraday monitoring universe.
24. Execution adapter is called only for the selected subset.
25. Post-execution decision pass uses only current-run fresh execution data.
26. Symbols without current-run execution data do not receive stale execution values.
27. Output/report diagnostics include the run-level and per-symbol fields listed in this ticket, using existing schema locations where available.
28. If a required diagnostics/report field has no existing schema location, Codex must update the owning schema/canonical doc in the same PR rather than silently writing ad-hoc fields.
29. `docs/canonical/open_questions.md` marks the intraday part of §21/3 as resolved by T17.
30. No new OHLCV reader/storage layer is introduced; the T14-canonical reader/writer path is used.
31. Shared infrastructure failures mark the run failed and do not update index files.
32. Identical input/config/persisted state/bar IDs produce identical output, execution subset, ranking, statuses, and reasons.

---

## Required tests

### Bar-clock tests

- Last closed 4h bar before boundary.
- Last closed 4h bar exactly on boundary.
- Allowed hour set `{00, 04, 08, 12, 16, 20}`.
- Non-UTC or malformed previous bar ID handling.
- `has_new_intraday_bar(None, current) == True`.
- Equal previous/current returns `False`.
- Older previous/current returns `True`.

### Config tests

- Defaults are applied.
- Partial overrides merge with defaults.
- Invalid `frequency_hours` rejected.
- `frequency_hours = 6` emits warning.
- `min_phase_confidence_for_monitoring` rejects `NaN`, `inf`, strings, booleans, and out-of-range values.
- `max_execution_subset_size` rejects `0`, negative, float, boolean, `NaN`, `inf`.

### Monitoring universe tests

- Included by active state.
- Included by active bucket.
- Included by confidence threshold.
- Excluded when `rejected`.
- Excluded when `chased`.
- Not excluded from monitoring solely because `decision_bucket = discarded` if it qualifies via state or phase confidence.
- Excluded from execution when `decision_bucket = discarded`.
- Empty monitoring universe no-ops without execution and does not update Daily-owned index files.

### Cache/failure-path tests

- No new 4h bar -> `skip_reason = no_new_4h_bar`; no execution call, only if no symbol is refresh-required.
- Missing Daily cache -> symbol `MISSING_DAILY_CACHE`; run continues.
- Mismatched `daily_cache_bar_id` versus current `daily_bar_id` -> symbol `MISSING_DAILY_CACHE`; run continues.
- Newer 4h bar + fetch failure -> `intraday_skipped_stale_4h = true`; previous 4h cache not used.
- Previous run-level bar ID equals current bar ID but one symbol is refresh-required due to prior `STALE_4H_REFRESH_FAILED` -> runner does not no-op and retries that symbol.
- Daily-only feature functions are not called during intraday, even when 1d OHLCV is available.
- Symbol-by-symbol branch behavior with mixed cache states.

### State/decision/execution tests

- `watch -> early_ready` with valid 4h data.
- `early_ready -> confirmed_ready`.
- `early_ready -> late` or `chased`.
- No `early_ready` without valid 4h data.
- No direct `rejected/chased -> early_ready/confirmed_ready` without new cycle/reset path.
- Pre-execution decision pass called before execution adapter.
- Execution subset selected by state OR confidence OR bucket.
- Safety limit does not truncate.
- Post-execution decision pass uses fresh execution input.
- Stale execution from previous run is ignored.

### Output/diagnostics tests

- Run metadata contains `scan_mode = intraday_promotion`, `daily_bar_id`, `intraday_bar_id`.
- Empty-monitoring and no-new-4h no-op runs write expected no-op metadata/report, do not fetch execution, and do not update Daily-owned index files.
- Per-symbol diagnostics contain missing Daily cache and stale 4h skip flags.
- Index update is atomic, does not occur on failed shared infrastructure run, and does not overwrite Daily-owned index files during intraday runs.
- Open question §21/3 intraday status updated in canonical docs.

---

## Implementation notes for Codex

- Inspect T15 runner before implementing. Reuse its run metadata, artifact writing, index atomicity, and failure-handling patterns wherever compatible.
- Inspect T16 execution adapter and daily execution subset implementation before implementing intraday execution integration. Do not create a parallel execution selector if a reusable helper exists and is compatible with this ticket.
- Inspect T14 OHLCV reader/writer contracts before loading 4h data. Use the canonical reader. Do not introduce a new storage abstraction.
- Inspect T13 report/diagnostics schema before writing new fields. Use existing field paths where possible. If no field path exists, update the owning schema/canonical documentation in the same PR.
- Keep helper functions small and testable: monitoring universe selection, intraday bar ID comparison, execution subset selection, and per-symbol cache classification should each be independently testable.
- Reason keys must be stable, machine-readable, and deterministic.

---

## Non-goals / deferred follow-ups

- Broad intraday reset scan for `rejected` / `chased`.
- Calibration of 6h freshness thresholds.
- Definition of `dist_to_base_mid_pct`.
- Evaluation/replay/forward-return metrics.
- GitHub Actions scheduling for intraday cadence.
- Any fachlicher Top-N policy for execution.

