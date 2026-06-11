# DOC-F0: Documentation Cleanup Closure Review

## Metadata

- Ticket ID: DOC-F0
- Title: Documentation Cleanup Closure Review — Post DOC-A to DOC-E2 Triage
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Documentation audit / triage only
- Primary output:
  - `docs/audit/documentation_cleanup_closure_review_v0.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Canonical documentation impact: None in this ticket
- Predecessors:
  - DOC-A — Documentation Inventory Baseline
  - DOC-B — Documentation Authority Consolidation
  - DOC-C — Documentation Impact Process Guard
  - DOC-D — Current-State Runtime and Architecture Documentation
  - DOC-E1 — Data and Reports Evidence Inventory
  - DOC-E2 — Data Model and Reports Current-State Documentation Update

---

## 1. Context

The DOC-A through DOC-E2 workstream cleaned up the core documentation authority, workflow, runtime architecture, data model, and report documentation.

The current repository now has a substantially cleaner documentation baseline, but several boundaries were intentionally left unresolved or only partially documented.

DOC-F0 is a closure review and decision-triage ticket. It must not update canonical documentation directly. It must inspect the post-DOC-E2 state and produce a concise audit that answers:

- which documentation cleanup items are complete,
- which open questions remain valid,
- which open questions can be closed or deferred,
- which follow-up tickets are actually needed,
- whether the next step should be a small doc cleanup, a CODE-FU technical boundary ticket, or a dedicated evaluation/T30 documentation ticket.

---

## 2. Problem

Without a closure review, the project risks one of two bad outcomes:

1. starting an overly broad next documentation ticket that reopens already-settled areas, or
2. ignoring unresolved boundaries now recorded in `docs/canonical/open_questions.md`.

The highest-risk unresolved areas after DOC-E2 are:

- Evaluation/T30 output schema,
- legacy snapshot evaluation export tooling,
- `SNAPSHOTS.md` coverage,
- `SCHEMA_CHANGES.md` role/navigation,
- newly added `open_questions.md` items from DOC-E2.

DOC-F0 must turn these into a structured triage result.

---

## 3. Goal

Create:

```text
docs/audit/documentation_cleanup_closure_review_v0.md
```

The audit must:

1. summarize the final post-DOC-A-to-DOC-E2 documentation state,
2. compare current canonical docs against the known cleanup objectives,
3. systematically review `docs/canonical/open_questions.md`,
4. classify each relevant open question as complete / follow-up needed / deferred / still unclear,
5. explicitly inspect the four known unresolved boundaries listed in section 8,
6. recommend the next ticket sequence,
7. avoid modifying canonical docs in this ticket.

---

## 4. Scope

Codex may only create:

```text
docs/audit/documentation_cleanup_closure_review_v0.md
```

If Codex creates the file and then refines it before committing, it may update that same file in the same PR.

No other file may be created, modified, moved, renamed, or deleted.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
docs/SCHEMA_CHANGES.md
docs/AI_CONTEXT_CURRENT.md
docs/AGENTS.md
docs/dev_workflow.md
docs/tickets/_TEMPLATE.md
docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
README.md
feature_enhancements.md
```

Codex must not modify:

- code,
- tests,
- schemas,
- CI/workflows,
- runtime behavior,
- generated artifacts,
- historical run outputs,
- existing audit inventories,
- decision notes,
- ticket files.

Codex must not:

- close or rewrite open questions,
- update canonical docs,
- create follow-up tickets,
- decide CODE-FU-B implementation details,
- document Evaluation/T30 schemas as current-state facts,
- treat this audit as authoritative replacement for canonical docs.

---

## 6. Read-only evidence sources

Codex must inspect these current-state docs:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
docs/SCHEMA_CHANGES.md
```

Codex must inspect these audit/decision inputs:

```text
docs/audit/documentation_inventory_v0.md
docs/audit/active_code_path_inventory_v0.md
docs/audit/legacy_pipeline_boundary_review_v0.md
docs/audit/data_reports_evidence_inventory_v0.md
docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md
```

Codex may inspect:

```text
feature_enhancements.md
docs/AI_CONTEXT_CURRENT.md
docs/code_map.md
docs/canonical/SNAPSHOTS.md
current code paths
current tests
```

only if needed to understand open questions or boundary status.

`docs/AI_CONTEXT_CURRENT.md` and `docs/code_map.md` are orientation aids only, not authority sources.

---

## 7. Required output structure

`docs/audit/documentation_cleanup_closure_review_v0.md` must include these sections:

```markdown
# Documentation Cleanup Closure Review v0

## Purpose

## Source coverage summary

## DOC-A to DOC-E2 completion summary

## Canonical documentation state after DOC-E2

## Open questions triage

## Known unresolved boundary checklist

## Residual documentation gaps

## Recommended follow-up sequence

## Deferred items

## Conflicts and uncertainties
```

---

## 8. Known unresolved boundary checklist

Codex must include this checklist as a structured table, not prose only.

Use this exact table shape:

```markdown
| Open area | Last decision / current state | DOC-F0 review question | Finding | Recommended next action |
|---|---|---|---|---|
| Evaluation/T30 output schema | In DOC-E2 deliberately not canonized | Is the boundary reference enough, or does this need CODE-FU-B first? | `<finding>` | `<next action>` |
| `export_evaluation_dataset.py` / `compute_global_top20` / `e2_model` | Classified as active executable legacy snapshot evaluation export tooling, not active `scanner/evaluation/*` infrastructure | Should this remain in `open_questions.md`, become CODE-FU-B, or become a dedicated evaluation-doc ticket? | `<finding>` | `<next action>` |
| `SNAPSHOTS.md` | Only touched indirectly / marginally during DOC-E2 | Is the current snapshot documentation sufficient, or is a standalone update ticket needed? | `<finding>` | `<next action>` |
| `SCHEMA_CHANGES.md` navigation | Remains an evidence/change log; INDEX/AUTHORITY role alignment may still be incomplete | Is a small INDEX/AUTHORITY navigation clarification enough, or is a separate ticket needed? | `<finding>` | `<next action>` |
```

Allowed recommended next actions:

```text
none
small_doc_patch
dedicated_doc_ticket
CODE-FU-B_first
future_evaluation_doc
defer
needs_human_decision
```

Codex may add additional rows if it finds further unresolved boundaries, but the four rows above are mandatory.

---

## 9. Mandatory open_questions.md triage

Codex must systematically review:

```text
docs/canonical/open_questions.md
```

This is a mandatory part of DOC-F0.

The audit must include a table with at least these columns:

```markdown
| Open question / subject | Source / section | Current relevance after DOC-A..E2 | Classification | Recommended action | Notes |
|---|---|---|---|---|---|
```

Use only these classifications:

| Classification | Meaning |
|---|---|
| `resolved_by_DOC_A_to_E2` | The issue appears to have been addressed by the documentation cleanup workstream |
| `follow_up_ticket_needed` | The issue remains valid and needs a concrete next ticket |
| `defer` | The issue remains valid but should not block current cleanup |
| `needs_human_decision` | The issue cannot be resolved by evidence review alone |
| `out_of_scope_for_docs_cleanup` | The item is not a documentation cleanup matter |

### Open questions handling rules

Codex must not modify `open_questions.md` in DOC-F0.

Codex must not silently ignore open questions added during DOC-E2.

Codex must explicitly check whether newly added DOC-E2 follow-up items are:

- still valid,
- already resolved by DOC-E2 final wording,
- better moved into CODE-FU-B,
- better moved into a future Evaluation/T30 documentation ticket,
- safe to defer.

The audit may recommend a future cleanup of `open_questions.md`, but must not perform it.

---

## 10. DOC-A to DOC-E2 completion summary

Codex must include a concise completion table:

```markdown
| Workstream step | Primary output / files | Current status | Residual concerns |
|---|---|---|---|
| DOC-A | `docs/audit/documentation_inventory_v0.md` | complete / partial / needs_review | `<notes>` |
| DOC-B | `docs/canonical/AUTHORITY.md`, `INDEX.md`, workflow docs | complete / partial / needs_review | `<notes>` |
| DOC-C | ticket template / preflight / workflow guard | complete / partial / needs_review | `<notes>` |
| DOC-D | `ARCHITECTURE.md`, `RUNTIME_AND_OPERATIONS.md` | complete / partial / needs_review | `<notes>` |
| DOC-E1 | `docs/audit/data_reports_evidence_inventory_v0.md` | complete / partial / needs_review | `<notes>` |
| DOC-E2 | `DATA_MODEL.md`, `REPORTS.md`, `open_questions.md` | complete / partial / needs_review | `<notes>` |
```

Do not reopen completed tickets unless current evidence shows a real contradiction.

---

## 11. Canonical documentation state after DOC-E2

Codex must include a table:

```markdown
| Canonical doc | Current role after cleanup | Apparent status | Remaining action needed? | Notes |
|---|---|---|---|---|
```

Minimum docs:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
docs/SCHEMA_CHANGES.md
```

Status values:

```text
clean
mostly_clean
partial
stale
needs_review
```

---

## 12. Recommended follow-up sequence

Codex must recommend a concrete next sequence.

Use this table:

```markdown
| Priority | Proposed ticket | Type | Rationale | Depends on |
|---|---|---|---|---|
```

Allowed ticket types:

```text
doc_patch
doc_inventory
doc_update
code_boundary
evaluation_doc
defer
```

The recommendation must choose one of these paths as the immediate next step:

1. no next documentation ticket needed,
2. small final documentation/navigation patch,
3. standalone `SNAPSHOTS.md` update ticket,
4. CODE-FU-B first, then Evaluation/T30 documentation,
5. dedicated Evaluation/T30 documentation first,
6. human decision before next ticket.

The audit must explain why.

---

## 13. Required boundaries and wording

Codex must preserve these established decisions:

### 13.1 Evaluation/T30

Evaluation/T30 output schemas are outside the current DATA_MODEL/REPORTS canonical contract unless separately documented in a future ticket.

DOC-F0 must not recommend adding T30 output schemas to DATA_MODEL/REPORTS unless a future dedicated Evaluation/T30 documentation ticket is explicitly proposed.

### 13.2 Legacy snapshot evaluation exporter cluster

Use this phrase or an equivalent phrase:

```text
active executable legacy snapshot evaluation export tooling, but not active scanner/evaluation/* infrastructure
```

for:

```text
scanner/tools/export_evaluation_dataset.py
scanner.pipeline.global_ranking.compute_global_top20
scanner.backtest.e2_model
```

### 13.3 SCHEMA_CHANGES.md

`docs/SCHEMA_CHANGES.md` remains an evidence/change log. It must not be recommended as a full data model replacement.

If navigation is unclear, recommend a small `INDEX.md` / authority clarification, not a rewrite of `SCHEMA_CHANGES.md`.

### 13.4 SNAPSHOTS.md

Do not assume `SNAPSHOTS.md` is clean merely because REPORTS.md was updated. Inspect it and classify it.

---

## 14. Implementation guidance for Codex

Codex should:

1. Inspect all required sources.
2. Build the audit from current repository state, not from ticket assumptions.
3. Compare `open_questions.md` against DOC-A..DOC-E2 outputs.
4. Preserve all known boundary decisions.
5. Avoid turning the audit into a canonical documentation update.
6. Prefer concise tables over long prose.
7. Mark uncertainty explicitly.
8. Recommend a concrete next step.

Codex should not:

- change canonical docs,
- add new tickets,
- modify open questions,
- modify code/tests/schemas/workflows,
- resolve a code/design boundary without a follow-up ticket.

---

## 15. Documentation impact

### Variant A — Documentation update required

Affected documentation:

- [x] `docs/audit/documentation_cleanup_closure_review_v0.md`

Documentation update plan:

- Create a non-authoritative closure review / triage audit.
- Do not update canonical current-state docs in this ticket.
- Do not modify open questions in this ticket.

---

## 16. Verification

After implementation, verify:

1. Only `docs/audit/documentation_cleanup_closure_review_v0.md` was created or modified.
2. No canonical docs were modified.
3. `docs/canonical/open_questions.md` was not modified.
4. No code, tests, schemas, workflows, README, ticket, audit-input, or decision-note files were modified.
5. The output includes the mandatory sections from section 7.
6. The output includes the known unresolved boundary checklist from section 8.
7. The output includes the `open_questions.md` triage table from section 9.
8. The output includes a recommended follow-up sequence.
9. The output preserves the Evaluation/T30 boundary.
10. The output preserves the legacy snapshot evaluation exporter boundary phrase or equivalent.
11. The output does not recommend rewriting `SCHEMA_CHANGES.md` into a full data model.

Suggested local checks:

```bash
git diff --name-only

test -f docs/audit/documentation_cleanup_closure_review_v0.md

grep -n "Known unresolved boundary checklist" docs/audit/documentation_cleanup_closure_review_v0.md
grep -n "Open questions triage" docs/audit/documentation_cleanup_closure_review_v0.md
grep -n "Recommended follow-up sequence" docs/audit/documentation_cleanup_closure_review_v0.md
grep -n "Evaluation/T30 output schema" docs/audit/documentation_cleanup_closure_review_v0.md
grep -n "active executable legacy snapshot evaluation export tooling" docs/audit/documentation_cleanup_closure_review_v0.md
grep -n "SCHEMA_CHANGES.md" docs/audit/documentation_cleanup_closure_review_v0.md

git diff -- docs/canonical/open_questions.md
git diff -- docs/canonical/AUTHORITY.md docs/canonical/INDEX.md docs/canonical/ARCHITECTURE.md docs/canonical/RUNTIME_AND_OPERATIONS.md docs/canonical/DATA_MODEL.md docs/canonical/REPORTS.md docs/canonical/SNAPSHOTS.md docs/SCHEMA_CHANGES.md
```

---

## 17. Acceptance criteria

- [ ] `docs/audit/documentation_cleanup_closure_review_v0.md` is created.
- [ ] The file is written in English.
- [ ] The file states that it is an audit/triage document, not canonical documentation.
- [ ] The file includes a source coverage summary.
- [ ] The file includes the DOC-A to DOC-E2 completion summary.
- [ ] The file includes the canonical documentation state table.
- [ ] The file includes a systematic `open_questions.md` triage.
- [ ] The file includes the four mandatory unresolved boundary checks.
- [ ] The file includes residual documentation gaps.
- [ ] The file includes a recommended follow-up sequence.
- [ ] The file explicitly preserves Evaluation/T30 boundaries.
- [ ] The file explicitly preserves the legacy snapshot evaluation exporter boundary.
- [ ] The file does not recommend rewriting `SCHEMA_CHANGES.md` as a full data model.
- [ ] No canonical docs are modified.
- [ ] `docs/canonical/open_questions.md` is not modified.
- [ ] No code, tests, schemas, CI/workflows, README, ticket, audit-input, or decision-note files are modified.

---

## 18. Suggested PR title

```text
DOC-F0: Add documentation cleanup closure review
```

## 19. Suggested PR summary

```text
## Summary
- Add a post DOC-A..DOC-E2 closure review and documentation cleanup triage
- Systematically review open_questions.md after DOC-E2
- Classify known unresolved boundaries and recommend the next follow-up sequence

## Scope
- Audit/triage output only
- No canonical documentation changes
- No code/test/schema/workflow changes

## Verification
- Confirmed only docs/audit/documentation_cleanup_closure_review_v0.md was added
- Confirmed open_questions.md and canonical docs were not modified
- Confirmed Evaluation/T30 and legacy snapshot exporter boundaries are preserved
```
