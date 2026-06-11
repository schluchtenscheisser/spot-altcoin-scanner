# DOC-G: Evaluation and T30 Output Schema Documentation

## Metadata

- Ticket ID: DOC-G
- Title: Evaluation and T30 Output Schema Documentation — Current-State Boundary After CODE-FU-B
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Canonical documentation update
- Primary goal: Document current Evaluation/T30 output schema and boundaries now that CODE-FU-B has resolved the legacy snapshot exporter boundary
- Primary expected output:
  - either update an existing evaluation canonical doc if one exists,
  - or create a new canonical evaluation documentation file, e.g. `docs/canonical/EVALUATION.md`
- Secondary allowed docs:
  - `docs/canonical/INDEX.md`
  - `docs/canonical/REPORTS.md`
  - `docs/canonical/DATA_MODEL.md`
  - `docs/canonical/SNAPSHOTS.md`
  - `docs/canonical/open_questions.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Test impact: Documentation/bootstrap tests only, unless existing docs tests require updates
- Predecessors:
  - DOC-E1 — `docs/audit/data_reports_evidence_inventory_v0.md`
  - DOC-E2 — current DATA_MODEL / REPORTS update
  - DOC-F0 — `docs/audit/documentation_cleanup_closure_review_v0.md`
  - CODE-FU-B — `own_as_standalone_legacy_tool` decision for legacy snapshot evaluation export cluster

---

## 1. Context

DOC-E2 deliberately did not canonize Evaluation/T30 output fields in `DATA_MODEL.md` or `REPORTS.md`, because the legacy snapshot evaluation exporter boundary was unresolved.

CODE-FU-B has now resolved that boundary:

```text
scanner/tools/export_evaluation_dataset.py
scanner.pipeline.global_ranking.compute_global_top20
scanner.backtest.e2_model
```

are classified as:

```text
standalone legacy snapshot evaluation export tooling,
not active scanner/evaluation/* infrastructure
```

Therefore, Evaluation/T30 documentation can now proceed, provided it preserves this boundary and does not conflate legacy snapshot export tooling with active `scanner/evaluation/*`.

---

## 2. Problem

The repository has current Evaluation/T30-related behavior and output fields, but the canonical documentation does not yet provide a durable, current-state Evaluation/T30 output contract.

Known documentation constraints:

- `DATA_MODEL.md` and `REPORTS.md` intentionally exclude Evaluation/T30 output schemas.
- DOC-F0 recommended Evaluation/T30 documentation after CODE-FU-B.
- CODE-FU-B selected `own_as_standalone_legacy_tool`, so legacy exporter output must be documented separately from active evaluation infrastructure.
- `open_questions.md` still contains Q14 items that touch unvalidated or ambiguous Evaluation/T30-related fields, especially `basket`.

DOC-G must document the current Evaluation/T30 output boundary without over-canonizing unresolved fields.

---

## 3. Goal

Create or update canonical documentation so that the repository clearly documents:

1. active Evaluation/T30 infrastructure and outputs,
2. standalone legacy snapshot evaluation export tooling and outputs,
3. which fields belong to active Evaluation/T30 versus legacy exporter compatibility,
4. which fields remain not validated / out of scope,
5. how future users should interpret Evaluation/T30 artifacts without confusing them with Daily/Intraday reports.

---

## 4. Scope

Codex may modify:

```text
docs/canonical/EVALUATION.md
docs/canonical/INDEX.md
docs/canonical/REPORTS.md
docs/canonical/DATA_MODEL.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
```

### 4.1 Existing-file preference

If an appropriate canonical evaluation document already exists, update it rather than creating a duplicate.

If no appropriate canonical evaluation document exists, create:

```text
docs/canonical/EVALUATION.md
```

and add it to `docs/canonical/INDEX.md`.

### 4.2 Minimal canonical touch rule

Codex must keep canonical changes focused.

Preferred changes:

1. `docs/canonical/EVALUATION.md` or equivalent evaluation doc,
2. `docs/canonical/INDEX.md` for navigation,
3. minimal cross-reference updates in `REPORTS.md`, `DATA_MODEL.md`, or `SNAPSHOTS.md` only if needed to point readers to the new evaluation doc,
4. minimal `open_questions.md` update if Q14 or Evaluation/T30 open items are clarified by the new documentation.

Codex must not broadly rewrite `DATA_MODEL.md`, `REPORTS.md`, or `SNAPSHOTS.md`.

---

## 5. Out of scope

Codex must not modify:

- code,
- tests except documentation/bootstrap tests if necessary,
- schemas,
- CI/workflows,
- generated artifacts,
- historical run outputs,
- audit inventories,
- decision notes,
- ticket files.

Codex must not:

- change active evaluation behavior,
- change legacy exporter behavior,
- redesign Evaluation/T30 fields,
- resolve unknown fields by assumption,
- document legacy exporter outputs as active `scanner/evaluation/*`,
- document active Evaluation/T30 outputs as Daily/Intraday report fields,
- rewrite `docs/SCHEMA_CHANGES.md` as a data model.

---

## 6. Required evidence sources

Codex must inspect:

```text
docs/audit/data_reports_evidence_inventory_v0.md
docs/audit/documentation_cleanup_closure_review_v0.md
docs/decision_notes/2026-06-11__code_fu_b_legacy_snapshot_evaluation_boundary_decision_note.md
docs/canonical/ARCHITECTURE.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/open_questions.md
docs/SCHEMA_CHANGES.md
```

Codex must inspect current code/tests for Evaluation/T30 and exporter evidence:

```text
scanner/evaluation/
scanner/tools/export_evaluation_dataset.py
scanner/pipeline/global_ranking.py
scanner/backtest/e2_model.py
tests/
```

Search terms should include:

```text
evaluation
T30
forward_return
forward_return_7d
forward_return_14d
forward_return_30d
mfe
mae
basket
segment
export_evaluation_dataset
evaluation_dataset
compute_global_top20
e2_model
```

---

## 7. Required boundary model

DOC-G must explicitly distinguish these two lanes:

| Lane | Meaning | Canonical treatment |
|---|---|---|
| Active Evaluation/T30 infrastructure | Current `scanner/evaluation/*` and related current evaluation/replay outputs | May be documented as active current-state evaluation documentation if supported by code/tests |
| Standalone legacy snapshot evaluation export tooling | `scanner/tools/export_evaluation_dataset.py` plus `compute_global_top20` and `e2_model` | Must be documented as executable compatibility/legacy export tooling, not active `scanner/evaluation/*` |

Required wording or equivalent:

```text
The legacy snapshot exporter is standalone legacy snapshot evaluation export tooling. It is executable and compatibility-supported, but it is not active scanner/evaluation/* infrastructure and must not be used as the source of truth for active Evaluation/T30 output contracts.
```

---

## 8. Required documentation content

The evaluation documentation must include these sections or equivalent:

```markdown
# Evaluation and T30 Documentation

## Purpose

## Boundary summary

## Active evaluation infrastructure

## T30 / forward-return output concepts

## Current Evaluation/T30 output fields

## Legacy snapshot evaluation exporter

## Field ownership and consumer guidance

## Relationship to DATA_MODEL, REPORTS, and SNAPSHOTS

## Open questions and deferred fields
```

---

## 9. Active Evaluation/T30 content requirements

Codex must document, if supported by evidence:

- active evaluation entry points,
- active evaluation artifact paths,
- output row/entity level,
- run/date/symbol identifiers,
- forward-return horizons,
- price reference semantics,
- segment or basket fields if implemented and verified,
- MFE/MAE fields if implemented and verified,
- relationship to replay/snapshot data,
- relationship to scanner Daily/Intraday reports.

For each documented field group, state:

- field name(s),
- source code/test evidence,
- artifact location if known,
- whether active Evaluation/T30 or legacy exporter,
- whether confirmed / partial / not validated.

Do not invent fields from planned T30 concepts if not implemented.

---

## 10. Legacy exporter content requirements

Codex must document:

```text
scanner/tools/export_evaluation_dataset.py
scanner.pipeline.global_ranking.compute_global_top20
scanner.backtest.e2_model
```

as the standalone legacy snapshot evaluation export lane.

Document:

- purpose,
- output format if implemented,
- dataset schema version if present,
- known fields if evidence-supported,
- relationship to global Top-20 legacy ranking,
- relationship to E2 labels,
- compatibility status,
- why it is not active `scanner/evaluation/*`.

If the legacy exporter fields overlap with active Evaluation/T30 fields, explicitly state whether the overlap is compatibility-only, shared terminology, or a current contract.

---

## 11. Q14 / open_questions.md handling

DOC-E2 / DOC-F0 left Q14 items unresolved:

```text
execution_grade
execution_notional_usdt
entry_location_score
not_applicable
basket
```

DOC-G must inspect Q14 and handle only Evaluation/T30-relevant items.

Rules:

1. If `basket` is confirmed as an Evaluation/T30 field, document it in the evaluation doc and update `open_questions.md` accordingly.
2. If `basket` belongs only to legacy exporter compatibility, document that boundary and update `open_questions.md` accordingly.
3. If `basket` remains unconfirmed, keep it open and explicitly state it is not yet a canonical Evaluation/T30 field.
4. Do not resolve non-Evaluation Q14 items unless DOC-G evidence directly resolves them.
5. Do not delete open questions silently. Move to resolved/reference section or update wording according to existing project convention.

---

## 12. DATA_MODEL / REPORTS / SNAPSHOTS relationship

DOC-G must not move Evaluation/T30 schema into `DATA_MODEL.md` or `REPORTS.md`.

Instead:

- keep `DATA_MODEL.md` focused on current report/diagnostics data model,
- keep `REPORTS.md` focused on current Daily/Intraday report artifacts,
- keep `SNAPSHOTS.md` focused on snapshot/replay artifact placement,
- add only short cross-references if needed.

Allowed cross-reference wording:

```text
Evaluation/T30 output schema is documented in `docs/canonical/EVALUATION.md`. It is not part of the Daily/Intraday report contract.
```

---

## 13. Documentation impact requirements

The PR must include a documentation impact summary stating:

- whether a new evaluation canonical doc was created or an existing one updated,
- which docs were cross-referenced,
- which Q14 items were updated or left open,
- confirmation that no code/runtime/schema behavior changed,
- confirmation that legacy exporter remains standalone legacy tooling.

---

## 14. Verification

Codex must verify:

1. No code changed.
2. No tests changed unless docs/bootstrap tests required updates.
3. Evaluation/T30 fields are not added to DATA_MODEL/REPORTS as Daily/Intraday report fields.
4. Legacy exporter is not documented as active `scanner/evaluation/*`.
5. Active Evaluation/T30 fields are supported by code/test evidence.
6. `INDEX.md` includes the evaluation doc if a new doc is created.
7. `open_questions.md` updates are minimal and evidence-based.
8. Documentation/bootstrap tests pass.

Suggested commands:

```bash
git diff --name-only

grep -R "forward_return_7d\|forward_return_14d\|forward_return_30d\|mfe\|mae\|basket\|evaluation_dataset" -n docs/canonical/DATA_MODEL.md docs/canonical/REPORTS.md || true

grep -R "standalone legacy snapshot evaluation export tooling" -n docs/canonical docs/decision_notes scanner/tools/export_evaluation_dataset.py

python -m pytest tests/test_independence_release_bootstrap.py::test_required_bootstrap_docs_have_expected_content -q
```

If a docs index/navigation test exists, run it as well.

---

## 15. Acceptance criteria

- [ ] Current Evaluation/T30 output documentation exists in an appropriate canonical doc.
- [ ] Active `scanner/evaluation/*` infrastructure is distinguished from standalone legacy snapshot exporter tooling.
- [ ] Legacy snapshot exporter lane is documented as standalone legacy tooling, not active evaluation infrastructure.
- [ ] Evaluation/T30 fields documented as current-state facts are supported by code/test evidence.
- [ ] Planned or unresolved fields are explicitly marked as not yet canonical or left open.
- [ ] Q14 Evaluation/T30-relevant items are updated or explicitly left open.
- [ ] `DATA_MODEL.md` and `REPORTS.md` are not polluted with Evaluation/T30 schema details.
- [ ] `INDEX.md` is updated if a new canonical evaluation doc is created.
- [ ] No code/runtime/schema behavior changes.
- [ ] Documentation/bootstrap tests pass.

---

## 16. Suggested PR title

```text
DOC-G: Document Evaluation and T30 output boundaries
```

## 17. Suggested PR summary

```text
## Summary
- Add/update canonical Evaluation/T30 documentation after CODE-FU-B
- Distinguish active scanner/evaluation/* outputs from standalone legacy snapshot exporter tooling
- Document confirmed Evaluation/T30 fields and keep unresolved fields open

## Scope
- Documentation-only
- No code/runtime/schema changes
- No Evaluation/T30 schema changes

## Verification
- Confirmed legacy exporter is not documented as active scanner/evaluation/*
- Confirmed Evaluation/T30 fields are not added to Daily/Intraday report contracts
- Ran docs/bootstrap tests
```
