> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Populate Daily/Intraday Diagnostics for Evaluation Replay (Ticket 21)

## Context / Source

This ticket implements the **diagnostics serialization layer** for the Independence-Release
pipeline, closing the gap between computed pipeline objects and the evaluation-ready
`symbol_diagnostics.jsonl.gz` contract established by T13/T18.

```yaml
depends_on: [13, 15, 17, 18, 20]
```

The authoritative fachliche source set for this ticket is:

- The 7 uploaded v2.1 section files, especially:
  - `v2_1_abschnitt_3_phase_interpreter_rev2.md` (phase output fields)
  - `v2_1_abschnitt_4_state_machine_rev3_aligned.md` (state output fields)
  - `v2_1_abschnitt_5_invalidation_setup_cycle_rev3_aligned.md` (invalidation/cycle fields)
  - `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` (field classes)
  - `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` (decision/pattern fields)
- `independence_release_gesamtkonzept_final.md` §15 (Output Schema)
- T13 ticket (diagnostics record contract and stub fixture — binding)
- T18 ticket (replay field expectations — binding)
- Current `scanner/output/schema.py` (bar-ID contract — binding)

If the current authoritative source set and existing code conflict, the source set wins.
The addendum is supplemental context only and does not override the source set.

---

## Scope

### In scope

1. Add `scanner/output/diagnostics_serialization.py` — explicit field-by-field
   serialization helpers for all diagnostic blocks.
2. Update `scanner/runners/daily.py` — populate all diagnostic blocks from already-
   computed pipeline objects; serialize the final post-execution decision.
3. Update `scanner/runners/intraday.py` — populate diagnostic blocks from fields
   available in Monitoring Row / Intraday refresh / Execution results only; document
   which fields are available; do not extend provider contracts.
4. Update `scanner/output/schema.py` — add sentinel-based co-presence invariants via
   one central validation path in `validate_diagnostics_record`.
5. Update `scanner/evaluation/replay.py` — add `cycle.resolved_setup_cycle_id` as
   fallback level 4 in the cycle-ID extraction path.
6. Tests for all of the above.

### Out of scope

- Business logic changes (phase rules, state transitions, invalidation rules, ranking).
- New decision buckets or state machine states.
- Changes to execution selection logic.
- Changes to `predecision_provider` or `postdecision_provider` contracts.
- New SQLite carry-forward contract for Intraday.
- Full Intraday replay completeness (deferred follow-up).
- Forward Returns / MFE / MAE changes for terminal events.
- New top-level compatibility mirrors for replay fields.
- Changes to report schemas, snapshot schemas, or index files.
- Changes to output artifact paths.

---

## Important framing

The T20 smoke test proved end-to-end pipeline executability. However, all fachliche
diagnostic blocks (`axes`, `phase`, `invalidation`, `cycle`, `state`, `pattern`,
`decision`, `reasons`) are written as empty `{}` at runtime, even though the Daily
Runner fully computes the corresponding objects. This ticket closes that serialization
gap without changing any business logic.

---

## T13 Compatibility Rule (binding)

T13 established the canonical minimal stub fixture shape:

```json
{
  "schema_version": "ir1.0",
  "run_id": "stub-run-id",
  "scan_mode": "daily",
  "symbol": "STUBUSDT",
  "as_of_utc": "2026-01-01T00:00:00Z",
  "daily_bar_id": "2025-12-31",
  "intraday_bar_id": null,
  "data_4h_available": false,
  "axes": {},
  "phase": {},
  "invalidation": {},
  "cycle": {},
  "state": {},
  "pattern": {},
  "decision": {},
  "reasons": {}
}
```

This stub shape remains valid for schema fixture tests and for **explicitly
non-processed technical no-op records** — records for which no fachliche pipeline
computation was attempted (e.g. Intraday `MISSING_DAILY_CACHE`,
`STALE_4H_REFRESH_FAILED`, `NO_NEW_4H_BAR`).

This stub shape must **not** be used as a fallback for symbols that partially or fully
entered the Daily business pipeline. If a source object (e.g. `t1`, `phase`) was
computed before a later symbol-level failure, the corresponding diagnostic block must
be populated with the available data where it can be done safely. Codex must not
discard previously computed diagnostic context merely because a later pipeline stage
failed. If no diagnostics record is written for a symbol that failed mid-pipeline,
document that decision explicitly in the PR.

This ticket does **not** require introducing new partial diagnostics records for symbols
that are currently skipped by existing symbol-level exception handling. It only forbids
using an all-empty stub shape when the implementation does choose to write a diagnostics
record for a partially processed symbol.

Codex must not alter the T13 base fixture shape.

### Current bar-ID contract (do not revert to T13 integer semantics)

T13 historically used `intraday_bar_id: int | null`. The current canonical contract,
established by the Post-T19 conformance fixes and enforced by `scanner/output/schema.py`,
is:

- `daily_bar_id`: string `YYYY-MM-DD`
- `intraday_bar_id`: `null` for `scan_mode=daily`
- `intraday_bar_id`: string `YYYY-MM-DDTHH:00:00Z` (UTC, 4h-aligned) for
  `scan_mode=intraday`

For `scan_mode="intraday"`, integer `intraday_bar_id` must be rejected by
`validate_diagnostics_record`. Do not reintroduce integer semantics.

---

## Canonical field layout

Use only existing field names from the relevant model files. Do not invent aliases.

### `axes` block

Source: `Tier1AxisBundle` and `Tier2AxisBundle` from `scanner/axes/models.py`.

Inspect the actual dataclass field names before serializing. Serialize every listed
dataclass field, **including fields whose value is `None`**. Do not omit nullable
fields merely because their value is `None` — absence vs. null has diagnostic meaning.

Fields include all axis values and their `_not_evaluable`, `_reduced_resolution`, and
`_effective_weight_ratio` variants. Serialize all fields from both bundles into a
single flat dict.

### `phase` block

Source: `PhaseInterpretationBundle` from `scanner/phase/models.py`.

Serialize every dataclass field, including `None`-valued fields. Fields include
`market_phase`, `market_phase_confidence`, `market_phase_runner_up`, `market_phase_gap`,
`market_phase_blended`, per-phase scores, floor margins, floor-failed flags, eval status
fields, and freshness_distance_structural fields. Inspect the actual dataclass.

### `invalidation` block

Source: `InvalidationCycleBundle` from `scanner/state/models.py`.

Fields: `structural_invalidation`, `structural_invalidation_reason`,
`timing_invalidation`, `timing_invalidation_reason`.

Serialize all four fields including `None`-valued ones.

### `cycle` block

Source: `InvalidationCycleBundle` from `scanner/state/models.py`, plus supplementary
fields from `StateMachineBundle.persistence_patch` if available.

Core fields from `InvalidationCycleBundle`:
`resolved_setup_cycle_id`, `new_cycle_detected`, `cycle_reason_code`,
`phase_floor_recovered_since_cycle_end`, `expansion_reset_condition_met`,
`reclaim_reset_condition_met`.

Supplementary fields if available from persistence patch or persisted context:
`previous_setup_cycle_id`, `bars_since_cycle_end`, `cycle_end_bar_index`,
`cycle_end_timestamp`.

`resolved_setup_cycle_id` is the canonical name in this block. Do not alias it to
`setup_cycle_id` here.

### `state` block — setup_cycle_id sourcing (critical)

Source: `StateMachineBundle` and `StateMachineBundle.persistence_patch`.

**`state.setup_cycle_id` must be serialized from
`state_bundle.persistence_patch.setup_cycle_id` when `persistence_patch` is present.**

Do not use `persisted_context.current_setup_cycle_id` as the source for
`state.setup_cycle_id` after `compute_state_machine()` — it may represent the pre-run
persisted value before the new cycle was resolved.

`state.setup_cycle_id` and `cycle.resolved_setup_cycle_id` are allowed to be equal in
value (because `StatePersistencePatch` derives `setup_cycle_id` from the resolved
cycle), but they come from different source objects and must be sourced correctly.
Do not copy `cycle.resolved_setup_cycle_id` into `state.setup_cycle_id` directly.

`current_setup_cycle_id` is not a required field for new runtime records. Include it
only if explicitly present in `state_bundle.persistence_patch` as a field distinct from
`setup_cycle_id`.

Replay-critical fields (required when a state context exists):
`state_machine_state`, `state_confidence`, `state_transition_reason`, `setup_cycle_id`.

For admitted/eventful state contexts, these fields must be present and non-null where
the source object provides them. For non-admitted `StateMachineBundle` records (e.g.
`market_phase == "none"` without a prior active cycle, or `disposition.admitted=False`),
serialize available disposition and freshness fields, but `state_machine_state`,
`state_confidence`, `state_transition_reason`, and `setup_cycle_id` may be `null`
according to the source object. Do not fabricate a `setup_cycle_id` for non-admitted
records.

Additional fields: `data_resolution_class`, `freshness_distance_state_early`,
`freshness_distance_state_confirmed`, `distance_from_ideal_entry_after_early`,
`distance_from_ideal_entry_after_confirmed`, `bars_since_state_entered`,
`bars_since_early_entered`, `bars_since_confirmed_entered`, `close_at_early_entry_bar`,
`close_at_confirmed_entry_bar`, `disposition_admitted`, `disposition_reason`.

Serialize all listed fields including `None`-valued ones.

### `pattern` block

Source: `EntryPatternBundle` from `scanner/entry/models.py` (if available).

If `EntryPatternBundle` exists, serialize the pattern block even when
`entry_pattern == "none"`. The value `"none"` is a valid computed pattern result
and must not be treated as absence of a pattern object. Do not leave the block
empty merely because no confirmable entry pattern was found.

Fields: `entry_pattern`, `entry_pattern_score`, `candidate_pattern_scores_within_phase`.

`candidate_pattern_scores_within_phase` keys must be JSON string keys; values must be
finite numbers. Do not use Enum-typed keys.

### `decision` block — post-execution decision (critical)

Source: `DecisionBundle` from `scanner/decision/models.py`.

**Daily diagnostics must reflect the final post-execution decision for each symbol.**
When an execution contract exists and `assign_bucket()` was re-run after execution
evaluation, serialize the result of the second `assign_bucket()` call, not the
pre-execution decision.

`decision.decision_bucket` must be serialized as its string value (e.g. `"watchlist"`),
not as the Enum object (`DecisionBucket.WATCHLIST`).

Replay-critical fields: `decision_bucket`, `priority_score`.

Additional fields: `bucket_reason_primary`, `bucket_reason_secondary`,
`execution_required`, `execution_pending`, `entry_pattern`, `entry_pattern_score`.

Serialize all listed fields including `None`-valued ones.

### `reasons` block

Consolidates reason codes from other bundles. Do not invent a new reason system.

Unlike the source-object blocks (`axes`, `phase`, `state`, `decision`), the `reasons`
block serializes only **non-null** available reason fields. Null reason fields may be
omitted from `reasons`. If all source reason fields are `None`, `reasons` may be `{}`.

Fields to include when non-null:
`bucket_reason_primary`, `bucket_reason_secondary`, `state_transition_reason`,
`structural_invalidation_reason`, `timing_invalidation_reason`, `cycle_reason_code`,
`execution_reason_raw`.

`execution_reason_raw` must be copied from the per-symbol execution diagnostics dict
(e.g. `execution_diagnostics.get("execution_reason_raw")`), not from a global
`ExecutionEvaluationResult` object.

For Intraday no-op/error records, include `intraday_skip_reason` (or the existing
reason field) using the canonical reason code only.

The empty-reasons case (`{}`) must be covered by a dedicated test explicitly
documenting the expected scenario.

---

## Replay fallback extension

`scanner/evaluation/replay.py` currently reads the cycle ID in this priority order:

1. `state.setup_cycle_id`
2. `state.current_setup_cycle_id`
3. top-level `setup_cycle_id` / `current_setup_cycle_id` (backward compatibility)

Add level 4:

4. `cycle.resolved_setup_cycle_id`

Add this fallback explicitly in `reconstruct_event_timeline` or the cycle-ID extraction
helper. Do not change levels 1–3. Do not make `cycle.resolved_setup_cycle_id` the
primary writer contract for new records.

---

## Sentinel-based schema invariants

Invariants are implemented in **one central validation path only** — inside
`validate_diagnostics_record` or a helper called by it. Runners call the same
validation function before write. Do not implement a divergent duplicate invariant set
in the runner outside the shared validator.

Invariants are enforced **conditionally** based on presence of sentinel fields, so that
T13 stub records and technical no-op records continue to pass validation.

**Invariant 1 — Execution context completeness:**
Applies when: `execution_attempted=true`.
Required non-null: `state.state_machine_state`, `decision.decision_bucket`,
`decision.priority_score` (0.0 is valid), `phase.market_phase`,
`phase.market_phase_confidence` (0.0 is valid), and at least one of:
`state.setup_cycle_id`, `state.current_setup_cycle_id`, `cycle.resolved_setup_cycle_id`.

**Invariant 2 — Decision/State co-presence:**
Applies when: `decision.decision_bucket` is non-null.
Required: `state.state_machine_state` is also non-null.

**Invariant 3 — Cycle ID resolvability:**
Applies when: `state.state_machine_state` is one of `watch`, `early_ready`,
`confirmed_ready`, `late`, `chased`, `rejected`.
Required: at least one of `state.setup_cycle_id`, `state.current_setup_cycle_id`,
`cycle.resolved_setup_cycle_id` is non-null.

### Invariant violation behavior

For processed runtime diagnostics, invariant violations must raise `ValueError` before
the diagnostics file is written. Do not silently skip a processed record — doing so
removes the diagnostic evidence that this ticket exists to provide.

T13 stub records and technical no-op records (where `execution_attempted` is absent or
`false`, `decision.decision_bucket` is absent or `null`, and `state.state_machine_state`
is absent or `null`) must continue to pass `validate_diagnostics_record` unchanged.

Invariant checks are gated on the sentinel fields above. A record with all sentinel
fields absent/null passes without invariant evaluation.

---

## Intraday diagnostics scope

**Before implementing Intraday diagnostics serialization**, Codex must inspect:

1. The Monitoring Row structure and the `predecision_provider` / `postdecision_provider`
   contracts in `scanner/runners/intraday.py` — document which replay-critical fields
   (`state_machine_state`, `setup_cycle_id`, `decision_bucket`, `market_phase`) are
   actually available.
2. Whether `postdecision_provider` currently returns a serializable per-symbol result
   or is side-effect-only / returns `None`.

**Do not change the public contracts of `predecision_provider` or
`postdecision_provider`.** If `postdecision_provider` currently returns no serializable
per-symbol result, do not invent one. Intraday diagnostics may include post-decision
data only if the current provider already returns or explicitly exposes it.

**Serialize only fields explicitly available from:**
- Monitoring Row / predecision provider
- Current Intraday 4h refresh result
- Post-decision result (only if currently returned by provider)
- Execution result (per-symbol diagnostics dict)

Do not invoke Daily-only feature computation (feature bundle, Tier-1/Tier-2 axes, phase
interpreter) from within the Intraday runner to fill diagnostic blocks.

If inspection reveals that replay-critical fields are absent from all available sources,
document this as a finding in the PR description and leave the relevant blocks as `{}`
with `reasons.intraday_skip_reason` populated. Do not invent a carry-forward mechanism.

### Block containers must always be present

All block containers (`axes`, `phase`, `invalidation`, `cycle`, `state`, `pattern`,
`decision`, `reasons`) must be present as dicts in every record, including no-op/error
records. Do not omit block keys. Empty `{}` is valid for unavailable blocks.

### Intraday no-op/error records and execution

No-op/error Intraday records (`NO_NEW_4H_BAR`, `MISSING_DAILY_CACHE`,
`STALE_4H_REFRESH_FAILED`) must keep `execution_attempted=false`. They must not receive
execution diagnostics from `evaluate_execution_subset`.

Execution diagnostics may only be merged into records for symbols that reached
`decision_rows` and were eligible for execution selection in the current run. A symbol
skipped due to `MISSING_DAILY_CACHE` or `STALE_4H_REFRESH_FAILED` must not appear in
the execution subset.

---

## Diagnostics serialization helpers

Add `scanner/output/diagnostics_serialization.py` with these helpers:

```python
def serialize_axes_block(t1: Tier1AxisBundle, t2: Tier2AxisBundle) -> dict: ...
def serialize_phase_block(phase: PhaseInterpretationBundle) -> dict: ...
def serialize_invalidation_block(inv: InvalidationCycleBundle) -> dict: ...
def serialize_cycle_block(
    inv: InvalidationCycleBundle,
    state_bundle=None,
    persisted=None
) -> dict: ...
def serialize_state_block(
    state_bundle,
    persisted=None
) -> dict: ...
def serialize_pattern_block(entry) -> dict: ...
def serialize_decision_block(decision) -> dict: ...
def serialize_reasons_block(
    inv: InvalidationCycleBundle,
    state_bundle,
    decision,
    execution_diagnostics: dict | None = None
) -> dict: ...
```

`serialize_state_block` must source `setup_cycle_id` from
`state_bundle.persistence_patch.setup_cycle_id` when the patch is present.

`serialize_reasons_block` receives `execution_diagnostics` as the per-symbol dict
entry (e.g. `execution_result.diagnostics.get(symbol)`), not a global result object.

Each helper returns a plain dict with JSON-stable values only. `json.dumps()` on the
return value must not raise `TypeError`.

---

## Critical implementation constraints

### No `dataclasses.asdict()`

Do not use `dataclasses.asdict()`. It recurses uncontrollably, converts Enums without
control, and loses `None`/`0.0` semantics. Use explicit field-by-field serialization.

### No truthiness defaults

Use `value is not None` checks throughout. Never use `value or default` for numeric,
confidence, priority, score, or cycle fields. `0`, `0.0`, `False` are valid values.

### Nullable fields must be serialized, not omitted

Serialize every listed dataclass field, including fields whose value is `None`. Do not
omit nullable fields. Absence of a key and presence of `null` have different diagnostic
meanings for downstream consumers.

### Enum serialization

All Enum-valued fields must be serialized as their string `.value`. `decision_bucket`
must serialize as e.g. `"watchlist"`, not as `DecisionBucket.WATCHLIST`.
`json.dumps()` on any fully serialized record must not raise `TypeError`.

### One central invariant validator

Implement all co-presence invariants in one path — `validate_diagnostics_record` or a
helper it calls. Runners call this shared function before writing. Do not implement a
separate duplicate invariant set anywhere else.

### No schema aliasing

`resolved_setup_cycle_id` stays in the `cycle` block sourced from
`InvalidationCycleBundle`. `state.setup_cycle_id` is sourced from
`state_bundle.persistence_patch`. Do not copy one to the other in serialization code.

### No new top-level mirrors

Do not add new top-level copies of `market_phase`, `state_machine_state`,
`decision_bucket`, or `priority_score`. Existing top-level fallbacks in `replay.py`
remain for backward compatibility only.

### Determinism

Given the same input bundles and persisted context, serialization helpers must produce
identical output. No timestamp injection, no randomness, no environment-dependent
branching.

### No output path changes

This ticket must not change any file paths under `reports/runs/`, `snapshots/runs/`,
`reports/daily/`, `reports/index/`, or any other output directory. Only the content of
`symbol_diagnostics.jsonl.gz` changes.

---

## Acceptance criteria

### Daily runtime completeness

- For every symbol that completes Daily phase/state/decision processing, the diagnostics
  record contains non-empty `axes`, `phase`, `cycle`, `state`, `pattern`, `decision`
  blocks where the corresponding source object was computed.
- `reasons` contains all non-null available reason fields; at minimum,
  `bucket_reason_primary` is present when `decision.bucket_reason_primary` is non-null.
- If all source reason fields are `None`, `reasons` may be `{}` — covered by a test.
- The T13 minimal stub fixture continues to pass `validate_diagnostics_record`.

### Post-execution decision

- Daily diagnostics `decision.decision_bucket` reflects the final post-execution decision
  when `assign_bucket()` was re-run after execution.
- A test proves pre-execution vs post-execution decision distinction.

### Execution context invariant

- Any processed record with `execution_attempted=true` passes Invariant 1 or `ValueError`
  is raised before write.
- A test fixture with `execution_attempted=true` but missing `decision.decision_bucket`
  raises `ValueError`.

### Decision/State co-presence

- Any record with non-null `decision.decision_bucket` also has non-null
  `state.state_machine_state` or `ValueError` is raised.

### State setup_cycle_id sourcing

- A test proves `state.setup_cycle_id` is sourced from `state_bundle.persistence_patch`,
  not from `persisted_context.current_setup_cycle_id`.

### Replay reconstruction

- `replay.py` reconstructs `first_watch` from a fixture with
  `state.state_machine_state="watch"` and `state.setup_cycle_id` set.
- `replay.py` reconstructs `first_watch` from a fixture where `state.setup_cycle_id`
  is absent but `cycle.resolved_setup_cycle_id` is set (level-4 fallback).
- `market_phase_confidence=0.0`, `state_confidence=0.0`, `priority_score=0.0` are not
  treated as missing.

### 0/0.0 and nullable field preservation

- Serialization helper tests assert that `0`, `0.0`, `False`, and `None` are preserved
  and not replaced by omission or a default value.

### Enum serialization

- Tests verify Enum-valued fields serialize as strings.
- `json.dumps()` on a fully serialized record does not raise.

### T13 and bar-ID contracts

- `validate_diagnostics_record` accepts the T13 stub fixture unchanged.
- For `scan_mode="intraday"`, integer `intraday_bar_id` is rejected by
  `validate_diagnostics_record`.

### Intraday correctness

- Intraday no-op/error records keep `execution_attempted=false` with no execution
  diagnostics merged.
- All block containers are present in all Intraday records (may be `{}`).
- Intraday does not call Daily-only feature computation functions.
- PR description documents: which Monitoring Row fields are available, and whether
  `postdecision_provider` returns serializable per-symbol data.

### One central invariant validator

- A code review or grep confirms invariants are implemented in one shared validation
  path only. No duplicate invariant set exists in runners.

### No `asdict()` usage

- A grep confirms no `dataclasses.asdict()` call in any serialization helper introduced
  by this ticket.

### Full test suite

- `pytest -q` passes with all existing tests green.

---

## Definition of done

- All acceptance criteria above are met.
- `pytest -q` result reported with pass count.
- PR description includes:
  - List of computed objects available at Daily diagnostics-write time.
  - Intraday Monitoring Row field availability finding.
  - Whether `postdecision_provider` returns serializable per-symbol data.
  - Confirmation that invariants are implemented in one shared path.
- No production business logic changed.

---

## Non-goals and anti-requirements

Codex must not:

- Modify phase, state, invalidation, cycle, or decision business logic.
- Change execution selection or ranking rules.
- Add new decision buckets or state machine states.
- Change `predecision_provider` or `postdecision_provider` contracts.
- Use `dataclasses.asdict()` for serialization.
- Use `value or default` for numeric/confidence/priority/score/cycle fields.
- Omit `None`-valued dataclass fields from serialized blocks.
- Copy `cycle.resolved_setup_cycle_id` into `state.setup_cycle_id` directly.
- Use `persisted_context.current_setup_cycle_id` as the source for `state.setup_cycle_id`.
- Add new top-level copies of replay-critical fields.
- Invoke Daily-only feature computation from the Intraday runner.
- Omit block container keys from any diagnostics record.
- Silently skip a processed record on invariant violation — raise `ValueError` instead.
- Implement duplicate invariant sets in runners separate from the shared validator.
- Change the T13 minimal stub fixture shape.
- Reintroduce integer `intraday_bar_id` semantics.
- Extend terminal event Forward Returns, MFE, or MAE.
- Make `replay.py` read from live SQLite state.
- Implement a new SQLite carry-forward contract.
- Change any output file paths.
- Invent a carry-forward mechanism to populate Intraday diagnostics.

---

## Suggested implementation sequence

1. Inspect `scanner/runners/daily.py` symbol loop — list all computed objects at
   diagnostics-write time. Document in PR.
2. Inspect `scanner/runners/intraday.py` — document Monitoring Row structure and
   whether `postdecision_provider` returns serializable per-symbol data. Document in PR.
3. Inspect `scanner/state/models.py` `StatePersistencePatch` — confirm `setup_cycle_id`
   field name and availability.
4. Implement `scanner/output/diagnostics_serialization.py` with all helpers.
5. Update `scanner/output/schema.py` — add conditional sentinel-based invariants in
   one central validation path.
6. Update `scanner/runners/daily.py` — use helpers; serialize final post-execution
   decision; call shared validator before write.
7. Update `scanner/runners/intraday.py` — use helpers for available fields only; call
   shared validator before write; merge execution diagnostics only for decision_rows
   symbols.
8. Update `scanner/evaluation/replay.py` — add level-4 cycle-ID fallback.
9. Unit tests for each serialization helper (0/0.0, None, Enum inputs, nullable fields).
10. Integration test: Daily runner produces non-empty blocks for a processed symbol.
11. Test: `state.setup_cycle_id` sourced from `persistence_patch`.
12. Test: post-execution decision correctly serialized.
13. Test: Invariant 1, 2, 3 violation detection.
14. Test: Replay level-4 fallback.
15. Test: empty-reasons case documented.
16. `pytest -q` (full suite).

---

## Review checklist for Codex before final response

- [ ] `scanner/runners/daily.py` inspected; computed objects at diagnostics-write time
      listed in PR description.
- [ ] `scanner/runners/intraday.py` Monitoring Row and provider contracts inspected;
      available fields and `postdecision_provider` return value documented in PR.
- [ ] `StateMachineBundle.persistence_patch.setup_cycle_id` confirmed as source for
      `state.setup_cycle_id`.
- [ ] `scanner/output/diagnostics_serialization.py` exists; no `dataclasses.asdict()`.
- [ ] All fields including `None`-valued ones are serialized; no key omission for nulls.
- [ ] All numeric/score/cycle fields use `is not None` — no `or default`.
- [ ] Enum fields serialize as strings; `json.dumps()` on full record does not raise.
- [ ] `decision_bucket` serialized as string value, not Enum object.
- [ ] `resolved_setup_cycle_id` in `cycle` block from `InvalidationCycleBundle`.
- [ ] `state.setup_cycle_id` sourced from `persistence_patch`, not `persisted_context`.
- [ ] No new top-level mirrors added.
- [ ] Invariants 1, 2, 3 implemented in one central shared validation path only.
- [ ] Invariant checks conditioned on sentinel fields; T13 stub still passes.
- [ ] Invariant violation raises `ValueError` before write for processed records.
- [ ] `replay.py` level-4 fallback to `cycle.resolved_setup_cycle_id` added.
- [ ] Daily diagnostics serialize final post-execution decision.
- [ ] Intraday no-op/error records keep `execution_attempted=false`.
- [ ] Execution diagnostics merged only for decision_rows symbols in Intraday.
- [ ] Provider contracts (`predecision_provider`, `postdecision_provider`) unchanged.
- [ ] All block containers present in all records (may be `{}`).
- [ ] Intraday does not call Daily-only feature functions.
- [ ] T13 stub fixture shape unchanged; `validate_diagnostics_record` accepts it.
- [ ] Integer `intraday_bar_id` rejected for `scan_mode="intraday"`.
- [ ] No output file path changes.
- [ ] Empty-reasons case covered by a test.
- [ ] `pytest -q` passes (full suite).
- [ ] PR description meets Definition of Done requirements.
