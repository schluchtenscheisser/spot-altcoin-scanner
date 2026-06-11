# DOC-E2: Data Model and Reports Current-State Documentation Update

## Metadata

- Ticket ID: DOC-E2
- Title: Data Model and Reports Current-State Documentation Update
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Canonical documentation update based on reviewed evidence inventory
- Primary inputs:
  - `docs/audit/data_reports_evidence_inventory_v0.md`
- Primary target files:
  - `docs/canonical/DATA_MODEL.md`
  - `docs/canonical/REPORTS.md`
- Optional target files, only if required by this ticket:
  - `docs/canonical/SNAPSHOTS.md`
  - `docs/canonical/INDEX.md`
  - `docs/canonical/open_questions.md`
  - `feature_enhancements.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Predecessors:
  - DOC-A — `docs/audit/documentation_inventory_v0.md`
  - DOC-B — consolidated authority model in `docs/canonical/AUTHORITY.md`
  - DOC-C — documentation impact process guard
  - DOC-D — current-state runtime and architecture documentation
  - DOC-E1 — `docs/audit/data_reports_evidence_inventory_v0.md`

---

## 1. Context

DOC-E1 created a non-authoritative evidence inventory for data/report fields, diagnostics/report artifacts, schema-version context, candidate/tradeability fields, execution fields, Entry-Location/T_EL2 fields, nullable/skipped/failed semantics, and consumer-facing documentation gaps.

DOC-E2 is the controlled canonical documentation update step that consumes DOC-E1.

This ticket updates only current-state canonical documentation for data model and report artifacts, using the evidence inventory as the mandatory source of truth and respecting the status assigned to each evidence item.

---

## 2. Problem

`docs/canonical/DATA_MODEL.md` and `docs/canonical/REPORTS.md` are stale or incomplete relative to current implementation evidence.

The highest-risk documentation areas are:

- candidate exclusion semantics,
- tradeability and operational candidate semantics,
- execution fields,
- Entry-Location / T_EL2 fields,
- null / not evaluated / not evaluable / unknown / failed / not applicable semantics,
- report and diagnostics artifact paths,
- `schema_version` / `ir1.5+` context,
- consumer guidance for daily reports, diagnostics, Shadow-Live analysis, and operational candidate selection.

DOC-E2 must update canonical docs without over-canonizing uncertain evidence.

---

## 3. Goal

Update the current-state canonical data/report documentation so that:

1. `docs/canonical/DATA_MODEL.md` reflects confirmed current-state field semantics.
2. `docs/canonical/REPORTS.md` reflects confirmed current-state report/diagnostics artifact semantics.
3. `partial` evidence is documented only with explicit qualification or boundary language.
4. `needs_review` evidence is not written as a current-state fact.
5. unresolved items are recorded in `docs/canonical/open_questions.md` when not already captured.
6. Evaluation/T30 output schema is not canonized in DOC-E2.
7. Legacy snapshot evaluation exporter boundaries remain explicit and are not conflated with active `scanner/evaluation/*` infrastructure.

---

## 4. Scope

Codex may modify:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
```

Codex may modify only if directly required and only minimally:

```text
docs/canonical/SNAPSHOTS.md
docs/canonical/INDEX.md
docs/canonical/open_questions.md
feature_enhancements.md
```

Use optional files as follows:

| Optional file | Allowed use |
|---|---|
| `docs/canonical/SNAPSHOTS.md` | Only for artifact-path or snapshot-boundary clarification that cannot live cleanly in `REPORTS.md` |
| `docs/canonical/INDEX.md` | Only to update navigation/role descriptions after DATA_MODEL/REPORTS changes |
| `docs/canonical/open_questions.md` | To record unresolved `needs_review` or unresolved `partial` items from the evidence inventory |
| `feature_enhancements.md` | Only if an unresolved item is clearly a future feature/enhancement rather than a documentation question; otherwise prefer `open_questions.md` |

Codex must not create new canonical documents in this ticket.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/SCHEMA_CHANGES.md
docs/AI_CONTEXT_CURRENT.md
docs/AGENTS.md
docs/dev_workflow.md
docs/tickets/_TEMPLATE.md
docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
README.md
docs/audit/data_reports_evidence_inventory_v0.md
docs/audit/documentation_inventory_v0.md
docs/audit/active_code_path_inventory_v0.md
docs/audit/legacy_pipeline_boundary_review_v0.md
docs/decision_notes/
```

Codex must not modify:

- code,
- tests,
- schemas,
- CI/workflows,
- runtime behavior,
- generated artifacts,
- historical run outputs,
- ticket files,
- audit inventories,
- decision notes.

Codex must not:

- rewrite `docs/SCHEMA_CHANGES.md` as a full data model,
- document Evaluation/T30 dataset schemas as current-state canonical facts,
- promote `needs_review` evidence into canonical factual documentation,
- silently omit unresolved `needs_review` items if they are relevant to data/report docs,
- collapse legacy snapshot evaluation tooling into active `scanner/evaluation/*`,
- de-canonize active executable legacy snapshot evaluation tooling without a follow-up decision.

---

## 6. Mandatory input and evidence hierarchy

Codex must use:

```text
docs/audit/data_reports_evidence_inventory_v0.md
```

as the primary input for DOC-E2.

Codex must also inspect the current target docs before editing:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/INDEX.md
docs/canonical/open_questions.md
feature_enhancements.md
```

Codex may inspect the following only to verify a claim or resolve wording, not to override the evidence inventory silently:

```text
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/AUTHORITY.md
docs/SCHEMA_CHANGES.md
current code paths
current tests
current schemas / validators
```

### Evidence precedence

Apply this hierarchy:

1. Current code/tests/schemas/artifacts as summarized in DOC-E1.
2. DOC-E1 evidence block status and notes.
3. `docs/SCHEMA_CHANGES.md` as an evidence/change log, not as a full data model.
4. Existing canonical docs, only where consistent with DOC-E1.
5. AI context only as orientation; never as sole factual authority.

If existing canonical docs conflict with DOC-E1, DOC-E1 wins unless the conflict is itself marked `needs_review`.

---

## 7. Mandatory status-gated transfer rules

This section is a hard requirement.

Codex must apply the DOC-E1 inventory statuses exactly as follows:

| Inventory status | DOC-E2 treatment |
|---|---|
| `confirmed` | May be written into canonical docs as current-state fact |
| `partial` | May only be documented with clear limitation, boundary wording, or explicit uncertainty |
| `needs_review` | Must not be documented as a current-state fact; must either be omitted from canonical factual sections or explicitly marked as not yet fully validated / open |

### Stop conditions

Codex must stop and revise before committing if any of the following is true:

1. A `needs_review` item from DOC-E1 is written into `DATA_MODEL.md`, `REPORTS.md`, or `SNAPSHOTS.md` as a current-state fact.
2. A `needs_review` item is silently ignored even though it is relevant to a data/report documentation gap and is not already captured in `docs/canonical/open_questions.md`.
3. A `partial` item is documented without qualification.
4. A `partial` item is phrased as if it were fully confirmed.
5. A current-state claim is added without a corresponding DOC-E1 evidence basis.
6. An Evaluation/T30 output field or evaluation dataset schema is documented as a current-state canonical report/data-model fact.
7. Legacy snapshot evaluation export tooling is documented as active `scanner/evaluation/*` infrastructure.
8. Legacy snapshot evaluation export tooling is documented as inactive legacy-only despite unresolved DOC-E1 conflict status.

### Required handling for `needs_review`

For every relevant `needs_review` item in DOC-E1:

- If it is already covered in `docs/canonical/open_questions.md`, do not duplicate it.
- If it is not covered and remains relevant to DATA_MODEL/REPORTS, add a minimal entry to `docs/canonical/open_questions.md`.
- Do not use `feature_enhancements.md` unless the unresolved item is clearly a future enhancement rather than a documentation uncertainty.
- Do not turn the open question into a speculative canonical statement.

Suggested wording pattern for `open_questions.md`:

```markdown
- DOC-E2 follow-up: `<subject>` remains not yet fully validated. DOC-E1 status: `needs_review`. Resolution needed before documenting it as a current-state data/report contract.
```

---

## 8. Evaluation / T30 scope boundary

DOC-E2 must not document T30 output fields or evaluation dataset schema as current-state canonical facts.

This applies even if DOC-E1 contains `confirmed` or `partial` entries for expected or actual Evaluation/T30 fields.

Evaluation/T30-specific fields belong to:

- a future evaluation documentation ticket,
- a future T30 output documentation ticket,
- CODE-FU-B resolution,
- or a dedicated current-state evaluation artifact documentation step.

DOC-E2 may reference Evaluation/T30 only where directly needed to distinguish:

- active report artifacts,
- diagnostics artifacts,
- legacy snapshot evaluation export artifacts,
- active `scanner/evaluation/*` infrastructure boundary,
- active executable legacy snapshot evaluation export tooling.

Allowed DOC-E2 wording:

```text
Evaluation/T30 output schemas are outside this document's current-state data/report contract and remain subject to dedicated evaluation documentation and CODE-FU-B boundary resolution.
```

Not allowed:

```text
The current report schema includes forward_return_7d, forward_return_14d, MFE, MAE, segment, basket, or evaluation_dataset fields.
```

unless those fields are confirmed report fields outside the Evaluation/T30 context and DOC-E1 explicitly supports that narrower claim.

---

## 9. Legacy snapshot evaluation exporter boundary

Codex must preserve the DOC-E1 conflict nuance for the linked boundary:

```text
scanner/tools/export_evaluation_dataset.py
scanner.pipeline.global_ranking.compute_global_top20
scanner.backtest.e2_model
```

Required classification language:

```text
active executable legacy snapshot evaluation export tooling, but not active scanner/evaluation/* infrastructure
```

or a semantically equivalent phrase.

DOC-E2 must not:

- document this path as active `scanner/evaluation/*`,
- describe it as inactive legacy-only,
- omit it if it is necessary to avoid confusion with report/evaluation artifacts,
- use it as evidence to canonize Evaluation/T30 output fields in DATA_MODEL/REPORTS.

If the current docs do not need to mention this boundary, ensure unresolved treatment is captured in `docs/canonical/open_questions.md` or deferred to a future evaluation documentation ticket.

---

## 10. Required DATA_MODEL.md updates

Using only DOC-E1-supported evidence, update `docs/canonical/DATA_MODEL.md` to cover current-state field semantics for:

### 10.1 Candidate exclusion and tradeability fields

Minimum subjects:

```text
candidate_excluded
is_tradeable_candidate
is_operational_trade_candidate
```

Document:

- whether each is top-level, nested, diagnostics-only, report-only, or both,
- implemented meaning,
- relationship to any legacy/nested source,
- preferred consumer use if confirmed,
- distinction between structural exclusion, tradeability, and operational actionability.

### 10.2 Execution fields

Minimum subjects:

```text
execution_status
execution_size_class
is_reduced_size_eligible
execution_grade_t16
```

Also include confirmed closely related fields from DOC-E1 if appropriate.

Document:

- where fields appear,
- whether they are nullable,
- whether they are report-level or diagnostics-level,
- whether they are derived from orderbook/depth/tradeability evaluation,
- whether they affect ranking/selection or are analysis/reporting fields only.

### 10.3 Entry-Location / T_EL2 fields

Minimum subjects:

```text
entry_location
entry_location_bucket
entry_location_reason
entry_location_flags
entry_location_score
buy_now
watchlist
avoid_chase
reduced_25
```

Document only those fields/values whose implemented names and semantics are supported by DOC-E1.

For `partial` items, explicitly mark boundary or uncertainty.

### 10.4 Null / skipped / failed evaluation semantics

Minimum subjects:

```text
null
not_evaluated
not_evaluable
unknown
failed
not_applicable
```

Document:

- whether value means intentionally not run, not applicable, failed, unknown, missing input, or absent serialization,
- where it appears,
- whether consumers must distinguish it from `null` or missing keys.

Do not invent a universal null semantics if DOC-E1 shows artifact-specific differences.

---

## 11. Required REPORTS.md updates

Using only DOC-E1-supported evidence, update `docs/canonical/REPORTS.md` to cover current-state artifact/report semantics for:

```text
report.json
symbol_diagnostics.jsonl.gz
run manifest
daily report
intraday report
snapshot run path
```

Document:

- where each artifact is written,
- producer code path,
- human vs machine consumer purpose,
- relation to run manifests,
- daily vs intraday behavior,
- report/diagnostics `scan_mode` context where relevant,
- fields or field groups consumers should use for `ir1.5+` where confirmed.

Do not document Evaluation/T30 dataset schema as part of `REPORTS.md`.

If `REPORTS.md` needs to mention evaluation exports, it must do so only as a boundary note.

---

## 12. Optional SNAPSHOTS.md and INDEX.md updates

Codex may update `docs/canonical/SNAPSHOTS.md` only if:

- report/snapshot path distinctions are currently misleading,
- DOC-E1 confirms a snapshot artifact/path clarification,
- the clarification cannot be expressed cleanly in `REPORTS.md`.

Codex may update `docs/canonical/INDEX.md` only if:

- roles/navigation need to reflect updated DATA_MODEL/REPORTS/SNAPSHOTS scope,
- no new authority hierarchy is introduced,
- no legacy/current-state status is changed without DOC-E1 support.

---

## 13. Required open questions handling

After updating canonical docs, Codex must check all DOC-E1 `needs_review` entries that are relevant to DATA_MODEL/REPORTS.

For each one:

1. If the item is already in `docs/canonical/open_questions.md`, leave it or minimally clarify it.
2. If not present, add a concise DOC-E2 follow-up entry.
3. Do not add broad speculative roadmap text.
4. Do not add open questions for every minor absence; only add items that affect canonical data/report interpretation.

Codex may update `feature_enhancements.md` only if:

- the unresolved item clearly describes future product/code behavior,
- it is not merely a documentation uncertainty,
- and adding it there is more appropriate than `open_questions.md`.

---

## 14. Required documentation impact section

Because this ticket modifies canonical docs, the PR must include a documentation impact summary.

The PR description must state:

- which docs changed,
- which DOC-E1 sections were consumed,
- which `partial` items were documented with qualification,
- which `needs_review` items were moved to open questions or left untouched because already present,
- confirmation that Evaluation/T30 output schema was not canonized in DOC-E2,
- confirmation that no code/tests/schemas/workflows were changed.

---

## 15. Verification

After implementation, Codex must verify:

1. `git diff --name-only` contains only allowed files.
2. `docs/audit/data_reports_evidence_inventory_v0.md` was not modified.
3. `docs/SCHEMA_CHANGES.md` was not modified.
4. No code/tests/schemas/workflows were modified.
5. No `needs_review` item was written as a current-state fact.
6. Every `partial` item used in canonical docs has limitation/boundary wording.
7. Evaluation/T30 output fields were not canonized in DATA_MODEL/REPORTS.
8. The legacy snapshot evaluation exporter boundary is not misclassified.
9. `docs/canonical/open_questions.md` was updated only if needed.
10. `feature_enhancements.md` was updated only if strictly justified.
11. Existing documentation tests still pass.

Suggested local checks:

```bash
git diff --name-only

git diff -- docs/audit/data_reports_evidence_inventory_v0.md
git diff -- docs/SCHEMA_CHANGES.md

grep -n "not yet fully validated" docs/canonical/open_questions.md || true

# Confirm T30/evaluation fields were not canonized in DATA_MODEL/REPORTS.
grep -n "forward_return_7d\|forward_return_14d\|forward_return_30d\|mfe\|mae\|evaluation_dataset" docs/canonical/DATA_MODEL.md docs/canonical/REPORTS.md || true

grep -n "active executable legacy snapshot evaluation export tooling" docs/canonical/*.md feature_enhancements.md || true
grep -n "scanner/evaluation" docs/canonical/DATA_MODEL.md docs/canonical/REPORTS.md || true
```

Run existing docs/bootstrap checks, for example:

```bash
python -m pytest tests/test_independence_release_bootstrap.py::test_required_bootstrap_docs_have_expected_content -q
```

If the repository has additional documentation validation tests, run those as well.

---

## 16. Acceptance criteria

- [ ] `docs/canonical/DATA_MODEL.md` is updated using DOC-E1 evidence.
- [ ] `docs/canonical/REPORTS.md` is updated using DOC-E1 evidence.
- [ ] Optional files are changed only if justified by this ticket.
- [ ] `confirmed` items are documented as current-state facts only where relevant.
- [ ] `partial` items are documented only with qualification/boundary language.
- [ ] `needs_review` items are not documented as current-state facts.
- [ ] Relevant unresolved `needs_review` items are captured in `docs/canonical/open_questions.md` if not already present.
- [ ] Evaluation/T30 output fields and dataset schema are not canonized in DOC-E2.
- [ ] The legacy snapshot evaluation exporter boundary remains explicit and correctly scoped.
- [ ] `docs/SCHEMA_CHANGES.md` remains unchanged.
- [ ] `docs/audit/data_reports_evidence_inventory_v0.md` remains unchanged.
- [ ] No code, tests, schemas, CI/workflows, tickets, audit files, or decision notes are modified.
- [ ] PR description includes documentation impact summary.
- [ ] Documentation/bootstrap checks pass.

---

## 17. Suggested PR title

```text
DOC-E2: Update current-state data model and reports docs
```

## 18. Suggested PR summary

```text
## Summary
- Update DATA_MODEL and REPORTS from DOC-E1 evidence inventory
- Apply status-gated transfer rules for confirmed / partial / needs_review evidence
- Preserve Evaluation/T30 and legacy snapshot exporter boundaries

## Scope
- Canonical documentation update only
- No code/test/schema/workflow changes
- No SCHEMA_CHANGES rewrite
- No Evaluation/T30 schema canonization

## Documentation impact
- Updated DATA_MODEL.md and REPORTS.md
- Used DOC-E1 evidence inventory as the source of truth
- Documented partial items only with boundary wording
- Moved relevant unresolved needs_review items to open questions where needed
```
