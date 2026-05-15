> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# T30-Fix-1 — Make Early/Confirmed Forward Returns Evaluable and Enrich Event Metrics with Segment Fields

## 1. Ticket Metadata

- **Ticket ID:** T30-FIX-1
- **Priority:** P1
- **Type:** Evaluation / T18-T30 follow-up fix
- **Target PR size:** 1 PR
- **Primary owner:** Codex
- **Status:** Draft for implementation
- **Language:** English
- **Created:** 2026-05-14

---

## 2. Context

T30 v1 successfully validated the technical forward-return evaluation pipeline:

- Shadow-Live artifacts can be downloaded in GitHub Actions.
- T30 inputs can be prepared from `independence-shadow-live-*` ZIP artifacts.
- Candidate-scoped 1d OHLCV history can be fetched.
- T18 replay can reconstruct events.
- T30 outputs are generated.

However, the first real T30 run is **analytically blocked for the core signal population**.

Observed T30 v1 result:

```text
Replay manifests found: 36
Events reconstructed: 4,585
Missing diagnostics runs: 0
OHLCV symbols fetched: 469
```

The problem is that all early/confirmed signal events are currently not evaluable:

```text
first_early_ready:       609 rows
first_confirmed_ready:   502 rows
total early/confirmed: 1,111 rows
```

All 1,111 rows currently produce:

```text
reference_price_status = reference_price_not_evaluable
reference_price_reason = missing_persisted_state_reference
```

This means the first T30 run computed forward returns only for a subset of `first_watch` events. It did **not** evaluate the main scanner population.

A second limitation is that `signal_event_metrics.parquet` does not currently carry the segmentation fields required for the intended T30 analysis groups, such as:

```text
is_operational_trade_candidate
execution_size_class
is_reduced_size_eligible
candidate_excluded
entry_location_status
entry_action_hint
available_depth_ratio
depth_ratio_band
schema_version
```

Claude and ChatGPT agree that the reference-price fallback and the segment-field enrichment should be implemented together, because both touch the T18/T30 event export path.

---

## 3. Authoritative References

Use the current authoritative reference set for the Independence Release:

1. v2.1 specification sections
2. `independence_release_gesamtkonzept_final.md`
3. canonical docs where they do not conflict with v2.1
4. `docs/canonical/open_questions.md`
5. `docs/canonical/feature_enhancements.md`
6. T18 evaluation replay implementation
7. T30 v1 ticket and generated outputs
8. T30-Pre-1 and T30-Pre-2 implementation state

If the current authoritative reference set, existing Repo Authority/Canonical documents, and existing code collide, the current authoritative reference set wins. Repo documents continue to apply only where they do not conflict with that reference set.

---

## 4. Goal

Make T30 v1.1 capable of evaluating forward returns for the core signal events:

```text
first_early_ready
first_confirmed_ready
```

by adding a transparent OHLCV-based reference-price fallback when the persisted state reference is missing.

At the same time, enrich `signal_event_metrics.parquet` with diagnostic segment fields so T30 can group outcomes by execution, operational tradeability, candidate exclusion, and entry-location state.

---

## 5. Non-Goals / Out of Scope

Do **not** implement any of the following in this PR:

- No automatic GitHub Actions workflow integration.
- No scheduled T30 execution.
- No changes to Shadow-Live discovery logic.
- No changes to scanner scoring, buckets, ranking, state machine, or entry-location thresholds.
- No T_EL2 recalibration.
- No T29 reduced-size recalibration.
- No OHLCV scope expansion for `first_watch` in this ticket.
- No permanent cohort framework.
- No final performance conclusion.
- No strategy threshold changes based on T30 v1.1.
- No repo persistence of OHLCV Parquet, diagnostics, or large artifacts.
- No use of current/open daily candles as final history.
- No silent schema inference for pre-`ir1.5` fields.

The `first_watch` OHLCV-scope decision remains separate and belongs to **T30-Fix-2**.

---

## 6. Current Failure Mode

### 6.1 Reference Price Failure

T18/T30 currently expects a persisted event reference price. For early/confirmed state transitions, this reference is not available in the replayed state.

Current result:

```text
reference_price_status = reference_price_not_evaluable
reference_price_reason = missing_persisted_state_reference
```

This prevents forward returns from being calculated even when OHLCV history exists for the symbol and event date.

### 6.2 Segment Field Absence

`signal_event_metrics.parquet` currently has enough information for basic event/return metrics, but not enough for T30's intended strategy groups.

The T30 v1 note therefore correctly stated that segment observations could not be derived and were not approximated.

T30-Fix-1 must eliminate this limitation by carrying the required diagnostic fields into event metrics where the source diagnostics provide them.

---

## 7. Required Behavior

### 7.1 Reference Price Source Precedence

For each signal event, determine the reference price using this ordered sequence:

1. **Persisted event/state reference price**, if present, finite, and strictly positive.
2. **OHLCV event-bar close fallback**, if:
   - persisted reference price is missing or invalid,
   - `event_bar_id` is present and not unknown,
   - symbol is present,
   - 1d OHLCV history exists for the symbol,
   - the OHLCV row for `event_bar_id` exists,
   - OHLCV `close` is finite and strictly positive.
3. Otherwise keep the event non-evaluable with explicit reason.

Do **not** silently overwrite a valid persisted reference price with OHLCV close.

### 7.2 Reference Price Output Fields

Add or preserve these fields in `signal_event_metrics.parquet`:

```text
reference_price
reference_price_status
reference_price_reason
reference_price_source
```

Allowed `reference_price_status` values:

```text
ok
reference_price_not_evaluable
```

Allowed `reference_price_source` values:

```text
persisted_state_reference
ohlcv_event_bar_close
not_available
```

Allowed `reference_price_reason` values must include at least:

```text
persisted_state_reference_available
fallback_missing_persisted_state_reference
missing_persisted_state_reference
missing_or_unknown_event_bar_id
missing_ohlcv_history
missing_event_bar_ohlcv
invalid_event_bar_close
invalid_persisted_state_reference
```

Definitions:

- `persisted_state_reference_available`: a valid persisted event/state reference price was used.
- `fallback_missing_persisted_state_reference`: persisted reference was missing or invalid, and the OHLCV close of `event_bar_id` was used.
- `missing_persisted_state_reference`: no persisted reference was available and no valid fallback could be used.
- `missing_or_unknown_event_bar_id`: event has no usable `event_bar_id`.
- `missing_ohlcv_history`: no OHLCV history exists for the symbol.
- `missing_event_bar_ohlcv`: OHLCV exists for the symbol but not for the event bar.
- `invalid_event_bar_close`: event-bar OHLCV close is missing, non-finite, zero, or negative.
- `invalid_persisted_state_reference`: persisted reference exists but is missing, non-finite, zero, or negative.

If the current code already has similar reason keys, reuse existing names when compatible. Do not introduce duplicate synonyms.

### 7.3 Forward Return Status after Fallback

If fallback succeeds, forward-return metrics for the event should evaluate normally.

Example expected state for a previously blocked early/confirmed event with OHLCV:

```text
reference_price_status = ok
reference_price_source = ohlcv_event_bar_close
reference_price_reason = fallback_missing_persisted_state_reference
metric_status_1d = ok or insufficient_future_data depending on future data availability
```

`missing_ohlcv_history` should only remain when the symbol actually lacks OHLCV history.

`insufficient_future_data` should remain distinct from reference-price failures.

---

## 8. Segment Field Enrichment

### 8.1 Add Fields to Event Metrics

Enrich signal-event metrics with these fields where available from diagnostics.

This list uses source-path notation for nested diagnostics fields. If the final Parquet export uses flat column names, `universe.universe_category` may be exported as `universe_category`, but it must be read from `rec["universe"]["universe_category"]` or the equivalent canonical nested accessor. Do not read `rec.get("universe_category")` as a top-level field.

```text
schema_version
scan_mode
run_id
symbol
event_type
event_bar_id
decision_bucket
priority_score

market_phase
market_phase_confidence
state_machine_state
state_confidence
entry_pattern

execution_status_raw
execution_size_class
is_tradeable_candidate
is_reduced_size_eligible
recommended_position_factor
execution_grade_effective
available_depth_ratio
depth_ratio_band

candidate_excluded
universe.universe_category

is_operational_trade_candidate
operational_tradeability_compat
operational_tradeability_source

entry_location_status
entry_action_hint
range_high_proximity_warning
```

If some fields already exist, preserve them and do not duplicate under alternate names.

### 8.2 Correct Source Paths

Use canonical field paths. Do not introduce top-level aliases for nested diagnostics.

Expected sources:

Top-level fields, where present:

```text
schema_version
scan_mode
execution_status_raw
execution_size_class
is_tradeable_candidate
is_reduced_size_eligible
recommended_position_factor
execution_grade_effective
available_depth_ratio
depth_ratio_band
candidate_excluded
is_operational_trade_candidate
```

Nested fields:

```text
decision.decision_bucket
decision.priority_score
phase.market_phase
phase.market_phase_confidence
state.state_machine_state
state.state_confidence
pattern.entry_pattern
universe.universe_category
entry_location.entry_location_status
entry_location.entry_action_hint
entry_location.range_high_proximity_warning
```

If the repo uses a slightly different canonical nested key, inspect current diagnostics and use the existing canonical path. Do not invent aliases.

### 8.3 Missing vs Invalid Segment Fields

Missing segment fields must remain `null`/missing in exported Parquet, not collapsed to `false`.

Rules:

- Missing boolean field → `null`, unless an explicit compatibility field is being computed.
- Missing numeric field → `null`.
- Non-finite numeric field (`NaN`, `inf`, `-inf`) → invalid/null and counted in diagnostics if the current export has numeric diagnostics.
- Missing enum/string field → `null`.
- Do not infer execution or entry-location fields from unrelated fields.
- Do not infer bucket membership from score.

### 8.4 Operational Tradeability Compatibility

Native field:

```text
is_operational_trade_candidate
```

exists only for `ir1.5+`.

For older schemas, add a separate compatibility field:

```text
operational_tradeability_compat
```

Definition:

```text
operational_tradeability_compat =
  is_tradeable_candidate == true AND candidate_excluded != true
```

Only compute this when:

- native `is_operational_trade_candidate` is missing,
- `is_tradeable_candidate` is present,
- `candidate_excluded` is present or safely defaults to `false` only if the historical schema truly lacked the field.

Preferred: if `candidate_excluded` is missing, set compatibility to `null` and source to `not_available` rather than silently treating missing as `false`.

Allowed `operational_tradeability_source` values:

```text
native_ir1_5
compat_backfill
not_available
```

Rules:

- For `ir1.5+` rows with native field:
  ```text
  operational_tradeability_source = native_ir1_5
  operational_tradeability_compat = null
  ```
- For older rows where compatibility is safely computed:
  ```text
  is_operational_trade_candidate = null
  operational_tradeability_compat = <computed bool>
  operational_tradeability_source = compat_backfill
  ```
- If not safely computable:
  ```text
  is_operational_trade_candidate = null
  operational_tradeability_compat = null
  operational_tradeability_source = not_available
  ```

Do not silently backfill native `is_operational_trade_candidate`.

---

## 9. T30 Note Update

Update `scripts/run_t30_evaluation.py` note generation so T30 v1.1 reports the improved state.

Required note additions:

### 9.1 Reference Price Coverage

Add a table by `event_type` and `reference_price_status`:

```text
event_type | reference_price_status | reference_price_source | rows
```

The note must make it obvious whether `first_early_ready` and `first_confirmed_ready` are now evaluable.

### 9.2 Metric Status by Event Type

Add a table by event type and horizon:

```text
event_type | horizon | metric_status | rows
```

### 9.3 Segment Observations

If the enriched fields are present, add summary tables for at least:

```text
event_type
execution_size_class
is_tradeable_candidate
is_operational_trade_candidate
operational_tradeability_compat
is_reduced_size_eligible
candidate_excluded
entry_location_status
entry_action_hint
depth_ratio_band
```

Use only fields present in `signal_event_metrics.parquet`.

If a field is absent, state explicitly:

```text
Segment field `<field>` is absent from signal_event_metrics.parquet and was not approximated.
```

### 9.4 No Final Performance Claim

The note must continue to include:

```text
Status: exploratory / validation note
Not a final performance conclusion
No threshold changes recommended by this note alone
```

---

## 10. File / Module Guidance

Inspect the current repo before editing. Expected relevant files include:

```text
scanner/evaluation/replay.py
scanner/evaluation/forward_returns.py
scanner/evaluation/dataset_export.py
scripts/run_t30_evaluation.py
tests/
```

Likely implementation areas:

1. Event construction / replay diagnostics enrichment:
   - Attach source diagnostic context to events or carry selected diagnostic fields into event rows.

2. Forward-return metric calculation:
   - Add OHLCV event-bar close fallback for reference price.

3. Dataset export:
   - Ensure enriched fields are included in `signal_event_metrics.parquet`.

4. T30 note generation:
   - Add coverage/segment summaries.

Do not duplicate the T18 forward-return engine in the script. The script should orchestrate and report; core metric logic belongs in evaluation modules.

---

## 11. Data and Artifact Policy

Do not commit or persist:

```text
symbol_diagnostics.jsonl.gz
*.parquet
snapshots/history/ohlcv/**
data/shadow-live-zips/**
large snapshot payloads
SQLite state files
```

Generated evaluation outputs remain artifacts unless explicitly committed in a later documentation decision.

---

## 12. Required Tests

Add or update tests. Tests must be deterministic and not call the MEXC API.

### 12.1 Reference Fallback Succeeds

Fixture:

- Event:
  ```text
  symbol = AAAUSDT
  event_type = first_confirmed_ready
  event_bar_id = 2026-05-05
  persisted reference price missing
  ```
- OHLCV:
  ```text
  daily_bar_id = 2026-05-05
  close = 10.0
  future close at 1d = 11.0
  ```

Expected:

```text
reference_price = 10.0
reference_price_status = ok
reference_price_source = ohlcv_event_bar_close
reference_price_reason = fallback_missing_persisted_state_reference
metric_status_1d = ok
return_1d_pct approximately 10.0
```

### 12.2 Persisted Reference Takes Precedence

Fixture:

- persisted reference price = 9.5
- event-bar OHLCV close = 10.0

Expected:

```text
reference_price = 9.5
reference_price_source = persisted_state_reference
reference_price_reason = persisted_state_reference_available
```

### 12.3 Missing Event-Bar OHLCV Remains Non-Evaluable

Fixture:

- persisted reference missing
- OHLCV exists for symbol but not for `event_bar_id`

Expected:

```text
reference_price_status = reference_price_not_evaluable
reference_price_source = not_available
reference_price_reason = missing_event_bar_ohlcv
```

### 12.4 Missing Symbol OHLCV Remains Missing OHLCV

Fixture:

- persisted reference missing
- no OHLCV partition for symbol

Expected:

```text
metric_status_* = missing_ohlcv_history
reference_price_status = reference_price_not_evaluable
reference_price_reason = missing_ohlcv_history
```

### 12.5 Invalid Event-Bar Close Is Rejected

Test these OHLCV close values:

```text
None
NaN
inf
-inf
0
-1
```

Expected:

```text
reference_price_status = reference_price_not_evaluable
reference_price_reason = invalid_event_bar_close
```

### 12.6 Early and Confirmed Events Become Evaluable

Use fixtures for:

```text
first_early_ready
first_confirmed_ready
```

Expected both can become `metric_status_1d = ok` when OHLCV is complete.

### 12.7 Segment Fields Are Exported

Fixture diagnostic record includes:

```json
{
  "schema_version": "ir1.5",
  "execution_size_class": "reduced_50",
  "is_tradeable_candidate": true,
  "is_reduced_size_eligible": true,
  "is_operational_trade_candidate": true,
  "candidate_excluded": false,
  "available_depth_ratio": 0.54,
  "depth_ratio_band": "reduced_50",
  "decision": {"decision_bucket": "confirmed_candidates", "priority_score": 66.7},
  "phase": {"market_phase": "trend_resume", "market_phase_confidence": 81.0},
  "state": {"state_machine_state": "confirmed_ready", "state_confidence": 77.0},
  "pattern": {"entry_pattern": "resume_reclaim"},
  "universe": {"universe_category": "standard_altcoin"},
  "entry_location": {
    "entry_location_status": "fresh_entry",
    "entry_action_hint": "acceptable_if_strategy_allows",
    "range_high_proximity_warning": false
  }
}
```

Expected `signal_event_metrics.parquet` includes the corresponding columns and values.

### 12.8 Missing Segment Fields Stay Null

Fixture older-schema diagnostic record missing:

```text
is_operational_trade_candidate
entry_location
execution_size_class
```

Expected:

```text
native missing fields are null
no false collapse
no invented aliases
```

### 12.9 Operational Compatibility Field

Fixture older-schema diagnostic record:

```json
{
  "schema_version": "ir1.4",
  "is_tradeable_candidate": true,
  "candidate_excluded": false
}
```

Expected:

```text
is_operational_trade_candidate = null
operational_tradeability_compat = true
operational_tradeability_source = compat_backfill
```

Fixture `candidate_excluded = true` with `is_tradeable_candidate = true`:

```text
operational_tradeability_compat = false
operational_tradeability_source = compat_backfill
```

Fixture `candidate_excluded = false` but missing `is_tradeable_candidate`:

```text
operational_tradeability_compat = null
operational_tradeability_source = not_available
```

Fixture missing `candidate_excluded` with `is_tradeable_candidate = true`:

```text
operational_tradeability_compat = null
operational_tradeability_source = not_available
```

### 12.10 T30 Note Reports Reference Coverage

Run note generation on fixture output where early/confirmed events have fallback reference prices.

Expected note includes:

```text
Reference Price Coverage
first_early_ready
first_confirmed_ready
ohlcv_event_bar_close
```

### 12.11 No Watch Scope Change

Ensure this PR does not change the OHLCV symbol selection script or enable new watchlist OHLCV fetching.

The following remains out of scope:

```text
first_watch OHLCV scope expansion
```

---

## 13. Acceptance Criteria

1. T30 early/confirmed events with complete OHLCV can produce forward-return metrics.
2. Valid persisted reference prices remain preferred over fallback prices.
3. OHLCV fallback is explicit via `reference_price_source` and `reference_price_reason`.
4. Missing OHLCV remains distinct from missing reference price.
5. `insufficient_future_data` remains distinct from reference-price failures.
6. Invalid OHLCV close values are rejected.
7. `signal_event_metrics.parquet` includes the required segmentation fields where available.
8. Missing segment fields are not collapsed to false.
9. Older schema compatibility is explicit via `operational_tradeability_compat` and `operational_tradeability_source`.
10. No native `is_operational_trade_candidate` is silently backfilled.
11. T30 note includes reference-price coverage by event type.
12. T30 note includes metric-status coverage by event type and horizon.
13. T30 note includes segment observations when fields are present.
14. T30 note clearly states if any segment field remains absent.
15. No OHLCV, diagnostics, Parquet, ZIP, or SQLite data is committed.
16. No Shadow-Live workflow automation is added.
17. No scanner decision, scoring, bucket, entry-location, or execution-threshold behavior is changed.
18. Tests cover reference fallback, invalid prices, segment extraction, compatibility fields, and note reporting.
19. Existing T18 tests continue to pass.
20. The PR remains limited to T30-Fix-1 scope.

---

## 14. Definition of Done

- Implementation complete.
- Tests added/updated and passing.
- Relevant existing evaluation tests passing.
- T30 full pipeline can be rerun and should show early/confirmed events no longer entirely blocked by `missing_persisted_state_reference` when OHLCV exists.
- No large generated files committed.
- T30 note remains explicitly exploratory and non-final.
- PR description documents:
  - fallback logic,
  - segment-field enrichment,
  - compatibility handling,
  - exact tests run.

---

## 15. Suggested Manual Validation

After merge, run the existing full T30 pipeline:

```bash
python scripts/run_t30_full_pipeline.py \
  --repo schluchtenscheisser/spot-altcoin-scanner \
  --since 2026-05-03
```

Then inspect:

```text
evaluation/notes/T30_forward_return_evaluation_v1.md
evaluation/exports/evaluation_summary.json
evaluation/exports/signal_event_metrics.parquet
evaluation/replay/replay_diagnostics.json
evaluation/replay/t30_run_summary.json
```

Expected high-level change vs T30 v1:

```text
first_early_ready and first_confirmed_ready should no longer be 100% reference_price_not_evaluable
when OHLCV for event_bar_id exists.
```

The exact number of `ok` rows depends on available OHLCV and future-bar coverage.

---

## 16. Self-Review Checklist for Codex

Before opening the PR, verify:

- [ ] No new strategy logic was added.
- [ ] No score/bucket/state/entry-location semantics changed.
- [ ] Fallback reference price is explicitly marked.
- [ ] Persisted reference price still wins over fallback.
- [ ] Missing vs invalid vs insufficient future data remain separate.
- [ ] Segment fields use canonical nested/top-level paths.
- [ ] Missing booleans are not collapsed to false.
- [ ] Pre-`ir1.5` operational compatibility is explicit and separate.
- [ ] No watchlist OHLCV scope change was made.
- [ ] No large generated data was committed.
- [ ] Tests prove the reference fallback and segment enrichment.
