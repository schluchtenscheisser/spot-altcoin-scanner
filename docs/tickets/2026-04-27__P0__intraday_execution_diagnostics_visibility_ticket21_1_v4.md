# Title
[P0] Fix Intraday Execution Diagnostics Visibility and Discarded-State Invariant Documentation (Ticket 21.1)

## Context / Source

Ticket 21 implemented evaluation-ready diagnostics serialization for Daily/Intraday runs, central diagnostics invariants, and replay fallback to `cycle.resolved_setup_cycle_id`.

Post-merge review identified two small but important follow-up issues before Shadow-Live operation:

1. Intraday can currently execute symbols via `decision_rows` / `evaluate_execution_subset(...)` even when the diagnostics record does not contain enough context to attach execution diagnostics without violating the central `execution_attempted=true` invariant.
2. Canonical documentation describes the Decision/State co-presence invariant too strictly and omits the valid `discarded` exception.

This follow-up must stay strictly within the Ticket 21 boundary:

- no business logic changes,
- no execution-selection semantic changes except the deliberate Intraday execution eligibility change described below,
- no new buckets/states,
- no provider contract changes,
- no SQLite carry-forward contract,
- no output path changes.

## Depends on

```yaml
depends_on: [21]
```

## Authoritative references

- Ticket 21 diagnostics serialization contract.
- Current `scanner/output/schema.py` central diagnostics invariants.
- Current `scanner/runners/intraday.py` Intraday diagnostics and execution path.
- Current `docs/canonical/REPORTS.md` diagnostics invariant documentation.

If ticket text and existing code conflict, preserve the Ticket 21 architecture:

- nested diagnostics blocks are canonical,
- no new top-level replay mirrors,
- no Daily-only recompute in Intraday,
- all diagnostics block containers remain present,
- central invariant validation remains in `validate_diagnostics_record`.

---

## Problem 1 — Intraday execution can become invisible in diagnostics

### Current behavior

In `scanner/runners/intraday.py`, rows that pass Daily-cache and 4h-refresh gates are appended to `decision_rows`.

After that:

1. `select_execution_subset(decision_rows, cfg.execution)` selects symbols.
2. `evaluate_execution_subset(...)` may perform real execution/orderbook checks.
3. Execution diagnostics are attached only if the existing diagnostics record has enough context:
   - `state.state_machine_state`
   - `decision.decision_bucket`
   - `decision.priority_score`
   - `phase.market_phase`
   - `phase.market_phase_confidence`
   - cycle-id via `state.setup_cycle_id`, `state.current_setup_cycle_id`, or `cycle.resolved_setup_cycle_id`

If context is incomplete, execution diagnostics are silently not attached. This can lead to real execution attempts being absent from `symbol_diagnostics.jsonl.gz`.

### Required behavior

No Intraday execution attempt may occur unless the symbol has enough diagnostics context to later attach execution diagnostics consistently.

In other words:

> Intraday execution eligibility and attachable diagnostics context must use the same context gate.

If a row lacks required context, it must:

- not be added to `decision_rows`,
- not be eligible for execution selection,
- still produce a diagnostics record,
- keep `execution_attempted=false`,
- include a clear `reasons.intraday_skip_reason`.

### Explicit behavioral change

This fix intentionally changes Intraday execution eligibility: symbols that previously reached `decision_rows` despite incomplete diagnostic context will no longer be considered for execution. This is a deliberate behavioral change, not a side effect.

The purpose of this behavior change is to enforce the Ticket 21 invariant that no real Intraday execution/orderbook check may occur without an attachable diagnostics context. It must be implemented consciously and tested as behavior, not treated as a pure refactor.

---

## Problem 2 — Intraday row can fail invariant due to partial context

### Current risk

`_intraday_diag_from_row(...)` currently uses `has_cycle` as the main gate for serializing state/decision fields.

A row may contain:

- `decision_bucket`
- `resolved_setup_cycle_id`

but lack:

- `state_machine_state`

This can produce a diagnostics record with non-null `decision.decision_bucket` and null `state.state_machine_state`, which violates the central Decision/State co-presence invariant for non-`discarded` buckets.

### Required behavior

Intraday diagnostics must only populate active replay-/execution-relevant fields when the corresponding minimum context is available.

Use one shared context classifier/gate for Intraday rows. The canonical helper name for this ticket is:

```python
def _intraday_row_has_attachable_execution_context(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    ...
```

Do not implement a second helper with overlapping responsibility.

The gate must evaluate, at minimum:

```text
has_state:
  row["state_machine_state"] is not None

has_cycle:
  at least one of:
  - row["setup_cycle_id"] is not None
  - row["current_setup_cycle_id"] is not None
  - row["resolved_setup_cycle_id"] is not None

has_decision:
  row["decision_bucket"] is not None
  and row["priority_score"] is not None

has_phase:
  row["market_phase"] is not None
  and row["market_phase_confidence"] is not None
```

For Intraday execution eligibility, require:

```text
has_state && has_cycle && has_decision && has_phase
```

If this requirement is not met:

- do not add the symbol to `decision_rows`,
- keep event/decision fields null or absent according to current serializers,
- write `reasons.intraday_skip_reason` with a stable machine-readable reason.

Suggested reason keys:

```text
missing_intraday_state_context
missing_intraday_cycle_context
missing_intraday_decision_context
missing_intraday_phase_context
```

If only one generic reason is preferred, use:

```text
missing_intraday_execution_context
```

Do not introduce new business-state or bucket values.

---

## Problem 3 — Canonical documentation omits the `discarded` exception

### Current documentation issue

`docs/canonical/REPORTS.md` currently describes the invariant as:

> non-null `decision.decision_bucket` requires non-null `state.state_machine_state`

But Ticket 21 intentionally allows:

```text
decision.decision_bucket == "discarded"
state.state_machine_state == null
```

This is valid for non-admitted Daily records such as `market_phase="none"` without an active prior cycle.

### Required documentation fix

Update canonical documentation to say:

```text
A non-null decision.decision_bucket requires non-null state.state_machine_state,
except decision.decision_bucket="discarded", which may validly occur with
state.state_machine_state=null for non-admitted / market_phase=none records.
```

Do not change the code invariant unless it currently differs from this rule.

---

## Scope

### In scope

- Refactor Intraday row handling so diagnostics context gating happens before adding rows to `decision_rows`.
- Ensure execution diagnostics are only possible for symbols that have attachable diagnostics context.
- Ensure rows with insufficient Intraday context still emit diagnostics with `execution_attempted=false` and a clear `reasons.intraday_skip_reason`.
- Ensure no skipped Intraday row appears in the execution subset.
- Update `docs/canonical/REPORTS.md` with the `discarded` invariant exception.
- Add/adjust tests for the above.

### Out of scope

- Any Daily business logic changes.
- Any phase/state/decision/invalidation rule changes.
- Any changes to `select_execution_subset(...)` semantics.
- Any changes to Execution grading.
- Any new SQLite carry-forward or Monitoring Row persistence contract.
- Any provider contract changes for `predecision_provider` / `postdecision_provider`.
- Any new top-level diagnostics fields.
- Any output path changes.
- Any report/index/manifest path changes.
- Any automatic trading/order execution.

---

## Required implementation details

### Intraday context gate

Introduce a small internal helper in `scanner/runners/intraday.py`, for example:

```python
def _intraday_row_has_attachable_execution_context(row: Mapping[str, Any]) -> tuple[bool, str | None]:
    ...
```

The helper must use explicit `is not None` checks, not truthiness.

Valid `0` / `0.0` values must not be treated as missing.

Examples:

- `priority_score=0.0` is valid.
- `market_phase_confidence=0.0` is valid.
- `setup_cycle_id=0` should not be dropped by truthiness, even though canonical cycle IDs should normally be positive.

### Applying the gate

In `run_intraday_scan(...)`:

1. For each Monitoring Row that passes Daily-cache and 4h-refresh checks, build a diagnostics record.
2. Check whether the row has attachable execution context.
3. Only if the context is attachable:
   - create/append the `row_obj`,
   - allow it into `decision_rows`,
   - populate `state`, `cycle`, `phase`, and `decision` fields from the row.
4. If context is not attachable:
   - do not append to `decision_rows`,
   - emit diagnostics with all block containers present,
   - keep `execution_attempted=false`,
   - set `reasons.intraday_skip_reason` to a stable reason key.

### Execution diagnostics merge

After `evaluate_execution_subset(...)`:

- Keep the existing rule that execution diagnostics are attached only when the candidate has complete context.
- There should now be no execution diagnostics for symbols without attachable context, because such symbols never enter `decision_rows`.
- Do not silently discard execution diagnostics for symbols that were actually executed.
- If execution diagnostics exist for a symbol in `execution.diagnostics`, the corresponding diagnostics record must either:
  - attach them successfully, or
  - raise `ValueError` because this indicates an internal invariant violation.

### Provider contracts

Do not change public behavior or signatures of:

```text
intraday_predecision_provider
intraday_postdecision_provider
```

If `postdecision_provider` returns a mapping, existing Ticket 21 behavior may remain.  
If it returns `None`, do not invent a return contract.

---

## Tests

Add or adjust tests in the existing Intraday / Ticket 21 test files.

### Required tests

#### 1. Intraday row without cycle context is not executed

Given a Monitoring Row with:

- `decision_bucket`
- `priority_score`
- `market_phase`
- `market_phase_confidence`
- `state_machine_state`
- but no `setup_cycle_id`, no `current_setup_cycle_id`, no `resolved_setup_cycle_id`

Expected:

- diagnostics record is written,
- `execution_attempted=false`,
- `reasons.intraday_skip_reason` is set,
- symbol is not passed to `evaluate_execution_subset`.

#### 2. Intraday row without state context is not executed

Given a Monitoring Row with:

- `decision_bucket`
- `priority_score`
- `market_phase`
- `market_phase_confidence`
- `resolved_setup_cycle_id`
- but `state_machine_state=None`

Expected:

- diagnostics record validates,
- no non-null `decision.decision_bucket` is written unless state context is present,
- `execution_attempted=false`,
- symbol is not passed to execution.

#### 3. Discarded Intraday row without state context is valid but not executable

Given a Monitoring Row with:

- `decision_bucket="discarded"`
- `state_machine_state=None`
- complete Phase context
- complete Cycle context

Expected:

- diagnostics record validates, because the central invariant allows `discarded` with `state_machine_state=null`,
- symbol is not added to `decision_rows`,
- `execution_attempted=false`,
- symbol is not passed to execution.

#### 4. Complete Intraday context can execute and attach diagnostics

Given a Monitoring Row with:

- `state_machine_state`
- cycle id
- `decision_bucket`
- `priority_score`
- `market_phase`
- `market_phase_confidence`

and execution returns diagnostics for the symbol.

Expected:

- symbol may enter `decision_rows`,
- execution diagnostics are attached,
- `execution_attempted=true`,
- central `validate_diagnostics_record` passes.

#### 5. `0.0` values are not treated as missing

Given:

- `priority_score=0.0`
- `market_phase_confidence=0.0`
- otherwise complete context

Expected:

- context gate treats these as present.
- no truthiness-based false missing classification.

#### 6. Documentation invariant matches code

A lightweight test is not required for docs, but update `docs/canonical/REPORTS.md` so the documented invariant includes the `discarded` exception.

---

## Acceptance criteria

- The PR explicitly implements the deliberate behavioral change that incomplete-diagnostics Intraday rows are no longer execution-eligible.
- Intraday symbols without attachable diagnostics context do not reach `decision_rows`.
- Intraday symbols without attachable diagnostics context do not reach `evaluate_execution_subset`.
- No real Intraday execution attempt can be invisible in diagnostics.
- Intraday no-op/error/context-missing records keep `execution_attempted=false`.
- All Intraday diagnostics records retain required block containers.
- Central `validate_diagnostics_record` remains the only invariant validator.
- `discarded` with `state.state_machine_state=null` remains valid.
- Non-`discarded` decision buckets still require non-null `state.state_machine_state`.
- Execution-attempted records still require full execution context.
- `0` / `0.0` values remain valid and are not treated as missing.
- `docs/canonical/REPORTS.md` documents the `discarded` exception.
- Existing Ticket 21 tests remain green.
- Full `pytest -q` passes.

---

## Anti-requirements

Codex must not:

- modify phase/state/decision business logic,
- change execution grading,
- change `select_execution_subset(...)`,
- change provider contracts,
- add new SQLite fields or tables,
- add new top-level diagnostics mirrors,
- omit required diagnostics block containers,
- silently hide execution attempts,
- use truthiness for context presence checks,
- reintroduce integer `intraday_bar_id`,
- change output paths,
- make Replay read from live SQLite.

---

## Suggested implementation sequence

1. Inspect current `scanner/runners/intraday.py` row-to-diagnostics and row-to-decision flow.
2. Add an internal Intraday context-gate helper using explicit `is not None` checks.
3. Apply the gate before appending to `decision_rows`.
4. Adjust `_intraday_diag_from_row(...)` so partial rows do not produce invariant-violating state/decision combinations.
5. Make execution diagnostics attachment fail loudly if execution diagnostics exist for a symbol but cannot be attached.
6. Update `docs/canonical/REPORTS.md` with the `discarded` exception.
7. Add tests for incomplete Intraday context, complete context, and `0.0` presence.
8. Run targeted tests:
   - `tests/test_ticket21_diagnostics_serialization.py`
   - `tests/test_ticket17_intraday_runner.py`
   - `tests/test_ticket18_evaluation_replay.py`
9. Run full suite:
   - `pytest -q`

---

## Definition of Done

- Code changes implemented within the stated scope.
- New/updated tests cover the Intraday context-gate behavior.
- Canonical docs updated for the `discarded` exception.
- Full test suite passes.
- PR description states:
  - how Intraday context gating works,
  - that the Intraday execution eligibility change is deliberate,
  - which reason key is emitted for missing context,
  - confirmation that execution attempts cannot be invisible in diagnostics,
  - confirmation that provider contracts and output paths were unchanged.
