# CODE-FU-B: Decide Legacy Snapshot Evaluation Export Boundary

## Metadata

- Ticket ID: CODE-FU-B
- Title: Decide Legacy Snapshot Evaluation Export Boundary — Deprecate, Own Standalone, or Absorb
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Code-boundary decision and minimal implementation alignment
- Primary affected cluster:
  - `scanner/tools/export_evaluation_dataset.py`
  - `scanner.pipeline.global_ranking.compute_global_top20`
  - `scanner.backtest.e2_model`
- Primary decision output:
  - one explicit selected boundary outcome:
    - `deprecate`
    - `own_as_standalone_legacy_tool`
    - `absorb_into_active_evaluation`
- Code impact: Yes, limited to the selected decision path
- Test impact: Yes
- Documentation impact: Yes, limited to documenting the selected decision and unblocking future Evaluation/T30 documentation
- Runtime impact: No impact to Daily/Intraday scanner runtime unless explicitly justified by tests
- Predecessors:
  - CODE-A1 — Active Code Path & Legacy Residue Inventory
  - CODE-A2 — Legacy Pipeline Boundary Review & Decision Matrix
  - Decision Note — `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`
  - CODE-FU-A — Extract Active Tradeability Metrics from Legacy Pipeline Namespace
  - DOC-D — Current-State Runtime and Architecture Documentation
  - DOC-E1 — Data and Reports Evidence Inventory
  - DOC-E2 — Data Model and Reports Current-State Documentation Update
  - DOC-F0 — Documentation Cleanup Closure Review

---

## 1. Context

The documentation cleanup workstream identified one remaining high-risk code/documentation boundary:

```text
scanner/tools/export_evaluation_dataset.py
scanner.pipeline.global_ranking.compute_global_top20
scanner.backtest.e2_model
```

DOC-F0 classified this cluster as:

```text
active executable legacy snapshot evaluation export tooling, but not active scanner/evaluation/* infrastructure
```

This boundary blocks durable Evaluation/T30 documentation. As long as the cluster's future is unresolved, documentation cannot accurately state whether Evaluation/T30 output contracts belong to:

- legacy snapshot export tooling,
- standalone maintained compatibility tooling,
- active `scanner/evaluation/*` infrastructure,
- or deprecated historical code.

CODE-FU-B must resolve that boundary.

---

## 2. Problem

The cluster is neither cleanly active nor cleanly inactive.

Known current state:

- `scanner/tools/export_evaluation_dataset.py` is executable tooling.
- It depends on legacy-named or legacy-boundary components.
- `scanner.pipeline.global_ranking.compute_global_top20` is tied to global Top-20 legacy ranking semantics.
- `scanner.backtest.e2_model` is tied to legacy snapshot export/evaluation compatibility.
- Active Daily/Intraday runtime must not depend on this cluster.
- Active `scanner/evaluation/*` infrastructure must not be conflated with this cluster until a decision is made.

If CODE-FU-B only creates another inventory or marks the issue as `needs_human_decision`, the documentation blockade remains.

Therefore, this ticket must force a decision and implement the minimal required alignment for that decision.

---

## 3. Mandatory decision output

CODE-FU-B must select exactly one of these outcomes:

| Decision | Meaning |
|---|---|
| `deprecate` | The cluster is historical/compatibility-only and should not be part of future supported workflows. Keep/remove/guard it according to repository policy, but mark it as deprecated and prevent new canonical dependency. |
| `own_as_standalone_legacy_tool` | The cluster remains executable and supported as a standalone legacy snapshot evaluation export tool, with explicit ownership, CLI contract, tests, and docs boundary. |
| `absorb_into_active_evaluation` | The cluster's relevant behavior is migrated into active `scanner/evaluation/*` infrastructure; legacy imports/dependencies are removed or wrapped; future Evaluation/T30 docs can treat the resulting output as active evaluation infrastructure. |

### Hard stop condition

Codex must not finish this ticket with:

```text
needs_human_decision
needs_review
partial
unclear
inventory_only
```

as the final outcome.

If evidence is insufficient to choose, Codex must select the safest maintainable option and state why. The selected option may be conservative, but it must be explicit.

Recommended default if no stronger evidence emerges:

```text
own_as_standalone_legacy_tool
```

because it preserves executable behavior without pretending the cluster is active `scanner/evaluation/*`.

---

## 4. Goal

Resolve the legacy snapshot evaluation export boundary by:

1. auditing the current cluster only as needed to support the decision,
2. selecting exactly one decision outcome,
3. making minimal code/test/doc changes required by that outcome,
4. ensuring Daily/Intraday runtime remains unaffected,
5. ensuring future Evaluation/T30 docs have a stable boundary to reference.

---

## 5. Scope

Codex may inspect all files required to understand the boundary, but must modify only the minimum set of files required for the selected decision path.

### 5.1 Write-scope hierarchy

Codex must apply this hierarchy before editing files:

1. Start with a decision note and/or `docs/canonical/open_questions.md`.
2. Modify the affected code cluster only if the selected outcome requires code alignment.
3. Modify or add tests only where needed to prove the selected boundary.
4. Modify canonical docs only if the selected outcome specifically requires a boundary update there.
5. Do not modify broad canonical documentation merely because it is listed as a possible target.

Primary cluster files:

```text
scanner/tools/export_evaluation_dataset.py
scanner/pipeline/global_ranking.py
scanner/backtest/e2_model.py
scanner/evaluation/
```

Likely documentation files, depending on selected outcome:

```text
docs/canonical/open_questions.md
docs/decision_notes/
```

Canonical docs that may be modified only with explicit justification tied to the selected outcome:

```text
docs/canonical/ARCHITECTURE.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/INDEX.md
```

Test files may be modified or added only to cover the selected path:

```text
tests/
```

### 5.2 Minimal-change rule

Codex must keep the PR narrow.

For `own_as_standalone_legacy_tool`, the expected change set should usually be limited to:

- the affected cluster file(s),
- focused tests,
- a decision note and/or `open_questions.md`.

Canonical docs should usually remain unchanged unless Codex can explain why the selected boundary cannot be documented adequately through the decision note/open-question update.

Codex must not treat the list above as permission to update all listed docs.

---

## 6. Out of scope

Codex must not:

- change Daily/Intraday scanner runtime behavior,
- change ranking/selection policy for current Daily/Intraday runs,
- redesign Evaluation/T30 output schemas,
- implement T30 calibration,
- rewrite `scanner/evaluation/*` broadly unless `absorb_into_active_evaluation` is selected,
- rewrite canonical docs unrelated to this boundary,
- rewrite `docs/SCHEMA_CHANGES.md` as a data model,
- modify historical generated artifacts,
- create broad migrations unrelated to this cluster.

---

## 7. Required evidence inputs

Codex must inspect:

```text
docs/audit/active_code_path_inventory_v0.md
docs/audit/legacy_pipeline_boundary_review_v0.md
docs/audit/data_reports_evidence_inventory_v0.md
docs/audit/documentation_cleanup_closure_review_v0.md
docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md
docs/canonical/ARCHITECTURE.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
```

Codex must inspect current code:

```text
scanner/tools/export_evaluation_dataset.py
scanner/pipeline/global_ranking.py
scanner/backtest/e2_model.py
scanner/evaluation/
scanner/runners/daily.py
scanner/runners/intraday.py
```

Codex must inspect relevant tests:

```text
tests/
```

including any tests referencing:

```text
export_evaluation_dataset
compute_global_top20
e2_model
evaluation_dataset
forward_return
T30
segment
basket
```

---

## 8. Decision process

Codex must create a short decision section in the PR description and, if a decision-note file is appropriate, a decision note.

The decision section must include:

```markdown
## CODE-FU-B Decision

Selected outcome: `deprecate` / `own_as_standalone_legacy_tool` / `absorb_into_active_evaluation`

Reason:
- <evidence-based reason 1>
- <evidence-based reason 2>
- <evidence-based reason 3>

Rejected options:
- `deprecate`: <why rejected or why selected>
- `own_as_standalone_legacy_tool`: <why rejected or why selected>
- `absorb_into_active_evaluation`: <why rejected or why selected>

Impact:
- Daily/Intraday runtime: <unchanged / changed with explanation>
- Evaluation/T30 documentation: <unblocked how>
- Legacy compatibility: <kept / deprecated / migrated>
```

Codex must not bury the selected outcome only inside prose.

---

## 9. Required implementation by decision path

### 9.1 If selected outcome is `deprecate`

Required actions:

1. Make deprecation explicit in code and docs.
2. Ensure no active Daily/Intraday runtime imports this path.
3. Add or update tests that assert the deprecation boundary.
4. If the CLI/tool remains callable, it must emit a clear warning or documented deprecation notice.
5. If removal is safe, remove only with tests proving no current supported workflow depends on it.
6. Add or update open-question / decision documentation so future Evaluation/T30 docs do not treat it as active.

Allowed docs:

```text
docs/canonical/open_questions.md
docs/canonical/INDEX.md
docs/canonical/SNAPSHOTS.md
docs/canonical/REPORTS.md
docs/canonical/DATA_MODEL.md
docs/decision_notes/
```

Do not remove compatibility behavior without confirming tests and consumers.

### 9.2 If selected outcome is `own_as_standalone_legacy_tool`

Required actions:

1. Keep the tool executable.
2. Add explicit module/docstring or CLI help text stating that it is:

   ```text
   standalone legacy snapshot evaluation export tooling,
   not active scanner/evaluation/* infrastructure
   ```

3. Add or update tests that validate:
   - the tool still runs or its core transformation behavior remains stable,
   - it does not affect Daily/Intraday runtime,
   - its dependency on `compute_global_top20` / `e2_model` is intentional and documented.
4. Ensure docs/open questions reflect that the boundary is now decided:
   - it is owned as standalone legacy tooling,
   - future Evaluation/T30 docs may reference it as legacy/export compatibility, not active evaluation infrastructure.
5. Do not migrate fields into active `scanner/evaluation/*`.

### 9.3 If selected outcome is `absorb_into_active_evaluation`

Required actions:

1. Move or wrap the relevant export/evaluation behavior into `scanner/evaluation/*`.
2. Remove or reduce dependency on:
   - `scanner.pipeline.global_ranking.compute_global_top20`,
   - `scanner.backtest.e2_model`,
   where feasible.
3. Keep backwards-compatible CLI behavior if existing tests or likely users depend on the old script.
4. Add tests proving:
   - new active evaluation path works,
   - legacy wrapper still behaves or fails with clear migration guidance,
   - Daily/Intraday runtime is unaffected,
   - future Evaluation/T30 docs can reference the new active path.
5. Update docs/open questions to record that the boundary is now absorbed into active evaluation infrastructure.

This path is higher-risk. Do not select it unless the implementation is small and testable.

### Absorption fallback rule

If implementing `absorb_into_active_evaluation` requires modifying files outside the allowed absorption set below, Codex must fall back to `own_as_standalone_legacy_tool` and document why absorption was too broad.

Allowed absorption set:

```text
scanner/evaluation/
scanner/tools/export_evaluation_dataset.py
scanner/pipeline/global_ranking.py
scanner/backtest/e2_model.py
scanner/runners/daily.py
scanner/runners/intraday.py
scanner/main.py
tests/
docs/decision_notes/
docs/canonical/open_questions.md
```

The three runtime files:

```text
scanner/runners/daily.py
scanner/runners/intraday.py
scanner/main.py
```

may only be modified if required for import isolation, compatibility wrappers, or explicit proof that Daily/Intraday runtime remains unaffected. They must not receive behavioral changes to active Daily/Intraday scanning.

If absorption requires broader architectural changes, new runtime dependencies, report schema redesign, or changes to current Daily/Intraday candidate/report behavior, select `own_as_standalone_legacy_tool` instead.

---

## 10. Runtime safety constraints

Codex must prove or preserve:

- Daily runtime still uses `scanner/runners/daily.py` paths, not this legacy exporter cluster.
- Intraday runtime still uses `scanner/runners/intraday.py` paths, not this legacy exporter cluster.
- No new dependency from active Daily/Intraday runtime into `scanner.pipeline.global_ranking` or `scanner.backtest.e2_model`.
- No change to candidate selection, execution, Entry-Location, report generation, or diagnostics behavior for Daily/Intraday runs.

---

## 11. Documentation impact requirements

This ticket must include documentation updates sufficient to unblock future Evaluation/T30 documentation.

At minimum, Codex must update one of:

```text
docs/canonical/open_questions.md
docs/decision_notes/<date>__code_fu_b_legacy_snapshot_evaluation_boundary_decision_note.md
docs/canonical/SNAPSHOTS.md
docs/canonical/REPORTS.md
docs/canonical/INDEX.md
```

The documentation must state the selected outcome.

If a decision note is created, use this filename pattern:

```text
docs/decision_notes/2026-06-11__code_fu_b_legacy_snapshot_evaluation_boundary_decision_note.md
```

The decision note should be concise and must include:

```markdown
# CODE-FU-B Legacy Snapshot Evaluation Boundary Decision

## Decision

Selected outcome: `<outcome>`

## Scope

## Rationale

## Rejected alternatives

## Impact on future Evaluation/T30 documentation

## Follow-ups
```

If Codex updates `open_questions.md`, it must not simply delete open questions. It must either:

- mark the relevant item as resolved by CODE-FU-B,
- move it to a resolved/reference section if such convention exists,
- or update the text to reflect the selected outcome.

---

## 12. Tests

Codex must run existing relevant tests and add/update tests if needed.

Minimum expected test coverage:

```text
tests touching export_evaluation_dataset, e2_model, global_ranking, evaluation, or snapshot export
documentation/bootstrap tests if docs are changed
```

At minimum, run targeted tests discovered by search.

If no direct tests exist for the selected path, Codex must add at least one focused regression test unless the selected outcome is pure deprecation documentation and code is untouched. Even then, if the tool remains executable, add a minimal test.

Suggested searches:

```bash
grep -R "export_evaluation_dataset" -n tests scanner docs
grep -R "compute_global_top20" -n tests scanner docs
grep -R "e2_model" -n tests scanner docs
grep -R "evaluation_dataset" -n tests scanner docs
```

Suggested test commands:

```bash
python -m pytest tests -q
```

If full test suite is too slow, run the relevant targeted tests and document why.

---

## 13. Verification

Codex must verify:

1. Exactly one decision outcome is selected.
2. The PR description contains the CODE-FU-B decision block.
3. The selected decision is reflected in code and/or docs.
4. Daily/Intraday runtime imports do not newly depend on the legacy exporter cluster.
5. Future Evaluation/T30 documentation is unblocked by a stable boundary.
6. Tests covering the selected path pass.
7. Documentation/bootstrap tests pass if docs changed.
8. No broad unrelated files are modified.
9. No generated artifacts are modified.
10. No current report/data model contracts are changed accidentally.

Suggested checks:

```bash
grep -R "from scanner.pipeline.global_ranking import compute_global_top20" -n scanner tests docs
grep -R "from scanner.backtest import e2_model" -n scanner tests docs
grep -R "export_evaluation_dataset" -n scanner tests docs
grep -R "active executable legacy snapshot evaluation export tooling" -n docs scanner tests
```

For Daily/Intraday isolation, inspect or grep:

```bash
grep -R "global_ranking" -n scanner/runners scanner/decision scanner/execution scanner/output scanner/storage scanner/evaluation || true
grep -R "e2_model" -n scanner/runners scanner/decision scanner/execution scanner/output scanner/storage scanner/evaluation || true
```

---

## 14. Acceptance criteria

- [ ] Exactly one selected outcome is stated: `deprecate`, `own_as_standalone_legacy_tool`, or `absorb_into_active_evaluation`.
- [ ] PR description includes a clear CODE-FU-B decision block.
- [ ] The selected outcome is reflected in code and/or docs.
- [ ] The cluster is no longer classified as unresolved.
- [ ] Daily/Intraday runtime remains unaffected.
- [ ] Active `scanner/evaluation/*` is not conflated with legacy exporter tooling unless `absorb_into_active_evaluation` is selected and implemented.
- [ ] If `own_as_standalone_legacy_tool` is selected, the standalone legacy boundary is explicit in code/docs/tests.
- [ ] If `deprecate` is selected, deprecation is explicit and tested or documented.
- [ ] If `absorb_into_active_evaluation` is selected, migration/wrapper behavior is tested.
- [ ] Future Evaluation/T30 documentation can reference the selected boundary.
- [ ] Relevant tests pass.
- [ ] Documentation/bootstrap tests pass if docs changed.
- [ ] No broad unrelated files are modified.
- [ ] No generated artifacts are modified.

---

## 15. Suggested PR title

```text
CODE-FU-B: Decide legacy snapshot evaluation export boundary
```

## 16. Suggested PR summary

```text
## Summary
- Select and implement the CODE-FU-B boundary decision for legacy snapshot evaluation export tooling
- Resolve the status of export_evaluation_dataset.py, compute_global_top20, and e2_model
- Document the selected boundary so future Evaluation/T30 docs are unblocked

## Selected outcome
`deprecate` / `own_as_standalone_legacy_tool` / `absorb_into_active_evaluation`

## Verification
- Confirmed Daily/Intraday runtime remains unaffected
- Ran targeted tests for the selected path
- Ran documentation/bootstrap checks if docs changed
```
