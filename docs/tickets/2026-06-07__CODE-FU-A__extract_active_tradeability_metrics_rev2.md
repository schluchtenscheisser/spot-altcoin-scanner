# CODE-FU-A: Extract Active Tradeability Metrics from Legacy Pipeline Namespace

## Metadata

- Ticket ID: CODE-FU-A
- Title: Extract Active Tradeability Metrics from Legacy Pipeline Namespace
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Type: Code cleanup / boundary refactor
- Language: Implementation and code artifacts in English
- Primary module affected: `scanner/execution/`
- Legacy module affected: `scanner/pipeline/liquidity.py`
- Target new module: `scanner/execution/tradeability_metrics.py`
- Related audits:
  - CODE-A1 — `docs/audit/active_code_path_inventory_v0.md`
  - CODE-A2 — `docs/audit/legacy_pipeline_boundary_review_v0.md`
- Related decision note:
  - `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`
- Blocks / unblocks:
  - Reduces DOC-D caveat around active runtime dependency on `scanner/pipeline/`
  - Does not need to solve legacy snapshot exporter or full-mode backfill

---

## 1. Context

CODE-A1 and CODE-A2 identified an active-runtime dependency leak from the current execution layer into the legacy-labeled `scanner/pipeline/` namespace.

Current dependency:

```text
scanner/execution/grading.py
-> scanner.pipeline.liquidity.compute_tradeability_metrics
```

The Decision Note records Martin’s decision for conflict area A:

```text
A — scanner.execution.grading -> scanner.pipeline.liquidity
Decision: extract_active_utility
```

The active tradeability/liquidity calculation should be moved out of `scanner/pipeline/` and into the active execution namespace.

The deterministic target path for this ticket is:

```text
scanner/execution/tradeability_metrics.py
```

This ticket must preserve behavior. It is a namespace/boundary refactor, not a scoring, ranking, execution-policy, or tradeability-model redesign.

---

## 2. Goal

Move the active tradeability metrics utility currently imported from:

```text
scanner.pipeline.liquidity.compute_tradeability_metrics
```

to:

```text
scanner.execution.tradeability_metrics.compute_tradeability_metrics
```

Then update active execution code to import the function from the new active namespace.

The result should be:

- active execution code no longer imports `scanner.pipeline.liquidity`,
- active runtime behavior remains unchanged,
- existing behavior for all numeric edge cases, including `NaN`, `inf`, `-inf`, missing values, zero depth, and malformed numeric inputs, is preserved as-is,
- existing tests continue to pass,
- relevant tests are updated or added to guard the new import path,
- legacy pipeline code is not otherwise reworked.

---

## 3. Scope

### In scope

- Create:

```text
scanner/execution/tradeability_metrics.py
```

- Move or copy the active `compute_tradeability_metrics` implementation from:

```text
scanner/pipeline/liquidity.py
```

into the new module.

- Update active execution imports, especially:

```text
scanner/execution/grading.py
```

to import from:

```text
scanner.execution.tradeability_metrics
```

- Update or add tests to verify:
  - active execution grading still works,
  - `compute_tradeability_metrics` behavior is unchanged,
  - active execution no longer depends on `scanner.pipeline.liquidity`.

- Preserve current runtime outputs and diagnostics.

- Decide whether `scanner/pipeline/liquidity.py` should retain a compatibility wrapper that imports/re-exports the new implementation.

### Out of scope

Do not:

- change execution grading semantics,
- change tradeability thresholds,
- change slippage/depth logic,
- change execution subset selection,
- change diagnostics schema,
- change report output schema,
- change runtime mode behavior,
- change `scanner/pipeline/scoring/*`,
- change `scanner/pipeline/global_ranking.py`,
- change `scanner/backtest/e2_model.py`,
- change `scanner/tools/export_evaluation_dataset.py`,
- change `scanner/tools/backfill_snapshots.py`,
- delete `scanner/pipeline/liquidity.py` unless clearly safe and tests prove no remaining imports,
- perform broad legacy cleanup,
- update DOC-D or canonical current-state docs.

---

## 4. Required implementation details

### 4.1 New active module

Create:

```text
scanner/execution/tradeability_metrics.py
```

Recommended module responsibility:

```text
Active execution-layer tradeability metric helpers.
```

The module should contain the implementation currently used by active execution grading, especially:

```text
compute_tradeability_metrics
```

If `scanner/pipeline/liquidity.py` contains supporting types/constants required by the function, move only the minimal required active utility surface.

Do not move unrelated legacy pipeline logic.

### 4.2 Update active import

Update:

```text
scanner/execution/grading.py
```

from:

```python
from scanner.pipeline.liquidity import compute_tradeability_metrics
```

to:

```python
from scanner.execution.tradeability_metrics import compute_tradeability_metrics
```

or equivalent.

### 4.3 Compatibility wrapper rule

Inspect all current imports of:

```text
scanner.pipeline.liquidity
compute_tradeability_metrics
```

Use this deterministic rule:

- If any import of `scanner.pipeline.liquidity.compute_tradeability_metrics` exists outside active execution modules, retain `scanner/pipeline/liquidity.py` as a compatibility wrapper.
- If no such import exists, the wrapper may be omitted.
- If `scanner/pipeline/liquidity.py` contains additional legacy helpers still used by tests or compatibility tooling, do not delete or overwrite those helpers.

Recommended wrapper pattern:

```python
# scanner/pipeline/liquidity.py

from scanner.execution.tradeability_metrics import compute_tradeability_metrics

__all__ = ["compute_tradeability_metrics"]
```

Only use this if the deterministic rule above requires import compatibility. Otherwise omit the wrapper.

If a wrapper remains, it is compatibility-only and non-authoritative for active execution architecture.

### 4.4 Avoid circular imports

Ensure the new module does not import from `scanner.pipeline`.

The dependency direction must be:

```text
scanner/execution/* -> scanner/execution/tradeability_metrics.py
scanner/pipeline/liquidity.py -> scanner/execution/tradeability_metrics.py   # only if wrapper needed
```

Not:

```text
scanner/execution/tradeability_metrics.py -> scanner.pipeline.*
```

---

## 5. Test requirements

Run or update the relevant tests around execution grading and liquidity/tradeability.

At minimum inspect and run targeted tests matching these areas:

```bash
pytest -q tests/test_t23_slippage_metrics.py
pytest -q tests/test_ticket16_execution_adapter.py
pytest -q tests/test_ticket26_execution_depth_analysis.py
pytest -q tests/test_ticket28_reduced_size_policy_calibration.py
pytest -q tests/test_ticket29_reduced_size_execution_policy.py
```

If any of these files do not exist or are not relevant in the current repo state, report that and run the closest matching execution/liquidity tests.

Also run a grep/import check:

```bash
grep -R "scanner.pipeline.liquidity" -n scanner tests scripts .github docs || true
grep -R "compute_tradeability_metrics" -n scanner tests scripts .github docs || true
```

Expected result after implementation:

- Active execution modules should not import `scanner.pipeline.liquidity`.
- Any remaining imports from `scanner.pipeline.liquidity` should be legacy tests, compatibility tests, or wrapper-specific references only.
- The new active module should be the canonical owner for active tradeability metrics.

---

## 6. Acceptance criteria

CODE-FU-A is complete when:

1. `scanner/execution/tradeability_metrics.py` exists.
2. `compute_tradeability_metrics` is available from `scanner.execution.tradeability_metrics`.
3. `scanner/execution/grading.py` imports `compute_tradeability_metrics` from the new active execution module.
4. No active runtime module imports `scanner.pipeline.liquidity`.
5. Existing behavior of `compute_tradeability_metrics` is preserved.
6. Existing execution/tradeability tests pass or are updated for the new canonical import path.
7. Any retained `scanner/pipeline/liquidity.py` usage is explicitly compatibility-only.
8. No unrelated legacy pipeline code is changed.
9. No diagnostics/report schemas are changed.
10. No runtime mode behavior is changed.
11. No current-state canonical documentation is updated in this ticket.

---

## 7. Validation

Run:

```bash
git diff --stat
git diff --name-only
```

Run targeted tests:

```bash
pytest -q tests/test_t23_slippage_metrics.py
pytest -q tests/test_ticket16_execution_adapter.py
pytest -q tests/test_ticket26_execution_depth_analysis.py
pytest -q tests/test_ticket28_reduced_size_policy_calibration.py
pytest -q tests/test_ticket29_reduced_size_execution_policy.py
```

Run the import checks:

```bash
grep -R "scanner.pipeline.liquidity" -n scanner tests scripts .github docs || true
grep -R "compute_tradeability_metrics" -n scanner tests scripts .github docs || true
```

If feasible, also run:

```bash
pytest -q
```

If the full suite is too slow or unrelated failures occur, report exactly which targeted tests passed and which broader tests were not run or failed for unrelated reasons.

---

## Documentation impact

No canonical documentation update required.

Reason: this ticket is a code cleanup / namespace-boundary refactor that moves an active utility to the active execution namespace without changing runtime behavior, schemas, reports, workflows, or canonical current-state documentation.

This ticket is a code cleanup / namespace-boundary refactor.

Do not update canonical current-state documentation.

Allowed documentation updates, only if useful:

- brief inline module docstring in `scanner/execution/tradeability_metrics.py`,
- compatibility comment in `scanner/pipeline/liquidity.py` if a wrapper remains.

Do not update:

```text
docs/canonical/*
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
docs/code_map.md
docs/audit/*
docs/decision_notes/*
```

Generated docs such as `docs/code_map.md` or `docs/GPT_SNAPSHOT.md` may be updated later by their normal workflow, not manually in this ticket.

---

## Codex guardrails

- This is not a behavior-change ticket.
- Preserve all numeric outputs and classifications from `compute_tradeability_metrics`.
- Preserve existing behavior for `NaN`, `inf`, `-inf`, missing values, zero depth, and malformed numeric inputs exactly as-is; do not introduce new sanitization or validation semantics.
- Do not redesign execution grading.
- Do not change scoring/ranking/decision logic.
- Do not remove legacy pipeline modules broadly.
- Do not touch `scanner/pipeline/scoring/*`.
- Do not touch `scanner/pipeline/global_ranking.py`.
- Do not touch `scanner/backtest/e2_model.py`.
- Do not touch `scanner/tools/export_evaluation_dataset.py` unless a test import adjustment is strictly necessary and justified.
- Do not touch `scanner/tools/backfill_snapshots.py`.
- Prefer compatibility wrapper over deletion if any uncertainty remains.
- Keep the diff small and focused.

---

## Definition of Done

- Active execution tradeability metrics live in `scanner/execution/tradeability_metrics.py`.
- Active execution grading imports from the active execution namespace.
- Active runtime no longer depends on `scanner.pipeline.liquidity`.
- Compatibility imports, if retained, are explicit and non-authoritative.
- Targeted tests pass.
- The diff is limited to the extraction and necessary tests/import updates.
