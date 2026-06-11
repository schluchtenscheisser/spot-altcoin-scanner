# DOC-E1: Data and Reports Evidence Inventory

## Metadata

- Ticket ID: DOC-E1
- Title: Data and Reports Evidence Inventory — Current-State Field and Artifact Evidence Baseline
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Documentation evidence inventory only
- Primary output:
  - `docs/audit/data_reports_evidence_inventory_v0.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Canonical documentation impact: None in this ticket
- Predecessors:
  - DOC-A — `docs/audit/documentation_inventory_v0.md`
  - DOC-B — consolidated authority model in `docs/canonical/AUTHORITY.md`
  - DOC-C — documentation impact process guard
  - DOC-D — current-state runtime and architecture documentation

---

## 1. Context

DOC-D updated current-state runtime and architecture documentation after the active runtime boundaries were clarified through CODE-A1, CODE-A2, the legacy pipeline boundary decision note, CODE-FU-A, and CODE-FU-D.

The next documentation area is the data/report layer:

- field semantics,
- report artifacts,
- diagnostics artifacts,
- schema/version context,
- consumer-facing field guidance,
- nullable / skipped / failed evaluation semantics.

This ticket does not update canonical current-state documentation directly. It creates a structured evidence inventory that will be reviewed before DOC-E2 updates `docs/canonical/DATA_MODEL.md` and `docs/canonical/REPORTS.md`.

---

## 2. Problem

`docs/canonical/DATA_MODEL.md` and `docs/canonical/REPORTS.md` are likely stale or incomplete relative to the implemented scanner state.

The highest-risk areas are:

- candidate exclusion semantics,
- tradeability / operational candidate semantics,
- execution fields,
- Entry-Location / T_EL2 fields,
- null / not evaluated / not evaluable / failed semantics,
- report and diagnostics artifact paths,
- `schema_version` and `ir1.5+` context.

Updating canonical docs directly without first collecting implementation evidence risks documenting assumptions or historical intent instead of current repository reality.

---

## 3. Goal

Create a structured evidence inventory for DOC-E2.

The inventory must:

1. cover the mandatory minimum field/artifact list in section 8,
2. use the mandatory structured evidence format in section 7 for every field or artifact subject,
3. cite concrete evidence sources for each claim,
4. distinguish confirmed facts from partial or uncertain findings,
5. identify documentation gaps for DOC-E2,
6. avoid modifying current-state canonical docs in this ticket.

---

## 4. Scope

Codex may only create:

```text
docs/audit/data_reports_evidence_inventory_v0.md
```

If Codex creates the file and then refines it before committing, it may update that same file in the same PR.

No other file may be created, modified, moved, renamed, or deleted.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/SCHEMA_CHANGES.md
docs/AI_CONTEXT_CURRENT.md
docs/AGENTS.md
docs/dev_workflow.md
docs/tickets/_TEMPLATE.md
docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
README.md
```

Codex must not modify:

- code,
- tests,
- schemas,
- CI/workflows,
- runtime behavior,
- generated artifacts,
- historical run outputs,
- legacy/reference-only docs,
- existing current-state canonical docs.

Codex must not:

- rewrite `DATA_MODEL.md`,
- rewrite `REPORTS.md`,
- rewrite `SNAPSHOTS.md`,
- rewrite `SCHEMA_CHANGES.md`,
- infer field semantics without evidence,
- silently resolve conflicts between code, artifacts, and docs,
- mark a field as confirmed using AI context alone,
- treat legacy/compatibility artifacts as active current-state artifacts without boundary qualification.

---

## 6. Read-only evidence sources

Codex must use current repository reality as the primary evidence anchor, consistent with `docs/canonical/AUTHORITY.md`.

Codex must inspect, as applicable:

```text
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/SCHEMA_CHANGES.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/audit/active_code_path_inventory_v0.md
docs/audit/legacy_pipeline_boundary_review_v0.md
docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md
```

Codex must inspect current code/tests/schemas/artifact-producing paths as evidence, including but not limited to:

```text
scanner/output/
scanner/runners/daily.py
scanner/runners/intraday.py
scanner/decision/
scanner/entry/
scanner/execution/
scanner/storage/
scanner/evaluation/
tests/
```

Codex may inspect legacy/compatibility paths if they contain relevant field or artifact definitions, but must classify them as legacy/compatibility where applicable:

```text
scanner/pipeline/
scanner/tools/export_evaluation_dataset.py
scanner/tools/backfill_snapshots.py
scanner/backtest/
```

`docs/AI_CONTEXT_CURRENT.md` may be used for orientation only. It must not be the sole evidence source for any `confirmed` claim.

---

## 7. Mandatory evidence format

The evidence inventory must not be free-form prose only.

For every required field, field group, semantic value, or artifact subject, Codex must create one structured entry using this exact format or a clearly equivalent Markdown table/block.

### Required field/artifact evidence block

```text
Field: <field_name_or_artifact_subject>
Claim: <semantic statement>
Evidence sources:
  - ticket_text: <ticket reference or "none found">
  - current_code: <file/function or "none found">
  - test: <test file/case or "none found">
  - schema: <schema file/model/validator or "none found">
  - artifact: <artifact path/example or "none found">
  - schema_changes: <SCHEMA_CHANGES.md reference or "none found">
Status: confirmed / partial / needs_review
Notes: <optional but required when Status is partial or needs_review>
```

### Status rules

Use only these statuses:

| Status | Meaning |
|---|---|
| `confirmed` | Current code/tests/schema/artifacts or multiple consistent evidence sources support the claim |
| `partial` | Evidence supports part of the claim, but not all required semantics or all consumers |
| `needs_review` | Evidence is missing, contradictory, or too ambiguous for DOC-E2 to document without human review |

Do not use `confirmed` if:

- the only evidence source is AI context,
- the field appears only in legacy/compatibility paths without current-state confirmation,
- current docs assert the claim but code/artifacts/tests do not support it,
- evidence sources conflict.

### Evidence-source requirements

Every field/artifact evidence block must include at least one concrete evidence reference or explicitly say `none found`.

Preferred evidence order:

1. current code,
2. tests,
3. schemas / validators / typed models,
4. current report/diagnostics/evaluation artifacts,
5. `docs/SCHEMA_CHANGES.md`,
6. implementation tickets / PRs,
7. current docs,
8. AI context.

---

## 8. Mandatory minimum coverage

Codex must cover all subjects in this section.

Codex may add additional fields or artifacts if discovered during code/doc scans.

### 8.1 Candidate exclusion and tradeability fields

Required fields:

```text
candidate_excluded
is_tradeable_candidate
is_operational_trade_candidate
```

For each field, answer through the mandatory evidence format:

- where it is produced,
- whether it is top-level, nested, diagnostics-only, report-only, or both,
- implemented semantic meaning,
- relationship to legacy/nested fields if any,
- intended consumer / preferred downstream use if evidenced,
- current documentation impact for DOC-E2.

### 8.2 Execution fields

Required fields:

```text
execution_status
execution_size_class
is_reduced_size_eligible
execution_grade_t16
```

Codex must also add any closely related execution fields discovered during the scan, for example:

```text
execution_grade
execution_notional_usdt
execution_depth_impact
```

For each field, answer through the mandatory evidence format:

- where it is produced,
- whether it is report-level or diagnostics-level,
- whether it is nullable,
- whether it is derived from orderbook/depth/tradeability evaluation,
- whether it affects candidate selection, ranking, reporting, or analysis only,
- whether it is current-state or legacy/intermediate.

### 8.3 Entry-Location / T_EL2 fields

Required fields and concepts:

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

Codex must also cover discovered T_EL2 bucket/decision fields if names differ.

For each subject, answer through the mandatory evidence format:

- actual implemented field name,
- actual structure: top-level vs nested,
- relation to Entry-Location / T_EL2,
- relation to decision buckets,
- whether it affects actionable candidate status,
- whether it is for reporting, diagnostics, T30 analysis, or runtime decisions.

### 8.4 Null / skipped / failed evaluation semantics

Required semantic values:

```text
null
not_evaluated
not_evaluable
unknown
failed
not_applicable
```

For each value or semantic group, answer through the mandatory evidence format:

- where the value appears,
- whether it means intentionally not run, not applicable, failed, unknown, missing input, or serialization absence,
- which artifact types use it,
- whether consumers are expected to distinguish it from `null` or missing keys,
- whether current docs already explain it.

### 8.5 Report and diagnostics artifact paths

Required artifact subjects:

```text
report.json
symbol_diagnostics.jsonl.gz
run manifest
daily report
intraday report
snapshot run path
```

For each artifact subject, answer through the mandatory evidence format:

- where it is written,
- producer code path,
- human vs machine consumer purpose,
- relation to run manifest,
- daily vs intraday behavior,
- current docs impact for DOC-E2.

### 8.6 Schema version / ir1.5+ context

Required subjects:

```text
schema_version
ir1.5
ir1.5+
```

For each subject, answer through the mandatory evidence format:

- where schema version is defined,
- where it is emitted,
- whether `ir1.5+` changes candidate/tradeability/report semantics,
- which consumers should prefer which fields for `ir1.5+`,
- whether `SCHEMA_CHANGES.md` documents it.

### 8.7 Evaluation / T30 output fields

Required subjects:

```text
forward_return
forward_return_horizon
forward_return_7d
forward_return_14d
forward_return_30d
mfe
mae
segment
basket
entry_reference
evaluation_dataset
```

These names are expected subject names based on the T30/T30-v2 analysis context. Codex must not assume that these are the exact implemented field names.

If the implemented names differ, Codex must:

1. document the actual implemented field names,
2. keep the expected subject name as the inventory anchor where useful,
3. explicitly record the mismatch in the relevant evidence block,
4. add the mismatch to the `Conflicts and uncertainties` section,
5. avoid marking the expected name as `confirmed` unless that exact field name exists in current code, tests, schema, or artifacts.

For each subject, answer through the mandatory evidence format:

- whether the field is implemented, planned, legacy, or compatibility-only,
- which actual field name is implemented, if different from the expected subject name,
- which code path produces it,
- whether it belongs to active `scanner/evaluation/*` or legacy snapshot export path,
- whether it should be documented in `REPORTS.md`, `SNAPSHOTS.md`, a future evaluation doc, or not yet.

### 8.8 Consumer contract fields

Required consumer concepts:

```text
daily report consumer
diagnostics consumer
T30 consumer
Shadow-Live analysis consumer
operational candidate selection
```

For each concept, answer through the mandatory evidence format:

- which artifact/field set it should use,
- which fields are preferred for `ir1.5+`,
- which fields are deprecated/superseded or compatibility-only,
- which current docs need updates.

---

## 9. Required inventory structure

`docs/audit/data_reports_evidence_inventory_v0.md` must include these top-level sections:

```markdown
# Data and Reports Evidence Inventory v0

## Purpose

## Source coverage summary

## Candidate exclusion and tradeability fields

## Execution fields

## Entry-Location / T_EL2 fields

## Null / skipped / failed evaluation semantics

## Report and diagnostics artifact paths

## Schema version / ir1.5+ context

## Evaluation / T30 output fields

## Consumer contract findings

## Documentation gaps for DOC-E2

## Conflicts and uncertainties
```

### 9.1 Source coverage summary

Use this table:

```markdown
| Source type | Checked? | Paths / refs | Notes |
|---|---|---|---|
| Code | yes/no/partial | `<paths>` | `<notes>` |
| Tests | yes/no/partial | `<paths>` | `<notes>` |
| Schemas / validators | yes/no/partial | `<paths>` | `<notes>` |
| Current artifacts | yes/no/partial | `<paths>` | `<notes>` |
| SCHEMA_CHANGES | yes/no/partial | `docs/SCHEMA_CHANGES.md` | `<notes>` |
| Current docs | yes/no/partial | `<paths>` | `<notes>` |
| Tickets / PRs | yes/no/partial | `<ids/refs>` | `<notes>` |
| AI context | yes/no/partial | `<paths>` | `<notes>` |
```

### 9.2 Documentation gaps for DOC-E2

Use this table:

```markdown
| Target doc | Gap type | Subject | Evidence status | Recommended DOC-E2 action |
|---|---|---|---|---|
| `DATA_MODEL.md` | `missing` / `stale` / `partial` / `contradicted` | `<subject>` | `confirmed` / `partial` / `needs_review` | `<action>` |
```

Minimum target docs to consider:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
docs/SCHEMA_CHANGES.md
future evaluation documentation
```

`docs/SCHEMA_CHANGES.md` should normally remain a change/evidence log. Do not recommend rewriting it as a full data model.

### 9.3 Conflicts and uncertainties

Use this table:

```markdown
| Subject | Conflict / uncertainty | Evidence refs | Suggested resolution path |
|---|---|---|---|
```

Include any case where:

- code and docs disagree,
- `SCHEMA_CHANGES.md` and current docs disagree,
- field names differ between tickets/docs/code/artifacts,
- fields appear only in legacy/compatibility paths,
- fields appear in code/artifacts but not in docs,
- evidence is insufficient for `confirmed`.

---

## 10. Implementation guidance for Codex

Codex should:

1. Search for each mandatory field/subject explicitly.
2. Record `none found` where a required evidence source is unavailable.
3. Prefer code/tests/schemas/artifacts over prose docs.
4. Use current architecture/runtime boundaries from DOC-D.
5. Treat `scanner/tools/export_evaluation_dataset.py` and `scanner.backtest.e2_model` as legacy/compatibility unless evidence proves otherwise.
6. Treat `scanner/evaluation/*` as the active evaluation/replay infrastructure.
7. Treat `docs/SCHEMA_CHANGES.md` as a strong schema/output evidence log, not as a full data model.
8. Mark uncertainty explicitly.
9. Do not rewrite any existing docs.

Suggested search terms:

```text
candidate_excluded
is_tradeable_candidate
is_operational_trade_candidate
execution_status
execution_size_class
is_reduced_size_eligible
execution_grade_t16
entry_location
buy_now
watchlist
avoid_chase
reduced_25
not_evaluated
not_evaluable
unknown
failed
not_applicable
report.json
symbol_diagnostics
manifest
schema_version
ir1.5
forward_return
mfe
mae
evaluation_dataset
```

---

## 11. Documentation impact

### Variant A — Documentation update required

Affected documentation:

- [x] `docs/audit/data_reports_evidence_inventory_v0.md`

Documentation update plan:

- Create a non-authoritative evidence inventory for DOC-E2.
- Do not update canonical current-state docs in this ticket.

---

## 12. Verification

After implementation, verify:

1. Only `docs/audit/data_reports_evidence_inventory_v0.md` was created or modified.
2. No existing docs were modified.
3. No code, tests, schemas, workflows, README, audit/decision/ticket docs were modified.
4. The inventory contains the required top-level sections from section 9.
5. Every mandatory subject from section 8 is covered.
6. Every field/artifact subject uses the mandatory evidence format from section 7.
7. Every block includes `Field`, `Claim`, `Evidence sources`, `Status`, and `Notes`.
8. No claim is marked `confirmed` using AI context alone.
9. Unclear findings are marked `partial` or `needs_review`.
10. `Documentation gaps for DOC-E2` is present and structured.
11. `Conflicts and uncertainties` is present and structured.
12. `Source coverage summary` is present and structured.

Suggested local checks:

```bash
git diff --name-only

test -f docs/audit/data_reports_evidence_inventory_v0.md

grep -n "^Field: candidate_excluded" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: is_tradeable_candidate" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: is_operational_trade_candidate" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: execution_status" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: execution_size_class" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: is_reduced_size_eligible" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: execution_grade_t16" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: entry_location" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: report.json" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: symbol_diagnostics.jsonl.gz" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: schema_version" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "^Field: ir1.5" docs/audit/data_reports_evidence_inventory_v0.md

grep -n "Documentation gaps for DOC-E2" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "Conflicts and uncertainties" docs/audit/data_reports_evidence_inventory_v0.md
grep -n "Source coverage summary" docs/audit/data_reports_evidence_inventory_v0.md
```

---

## 13. Acceptance criteria

- [ ] `docs/audit/data_reports_evidence_inventory_v0.md` is created.
- [ ] The file is written in English.
- [ ] The file states that it is an evidence inventory, not canonical current-state documentation.
- [ ] The file uses the mandatory evidence format for every required field/artifact subject.
- [ ] All mandatory fields and artifact subjects in section 8 are covered.
- [ ] Each entry has concrete evidence refs or explicitly says `none found`.
- [ ] Each entry has `Status: confirmed`, `partial`, or `needs_review`.
- [ ] No AI-context-only claim is marked `confirmed`.
- [ ] The file includes a source coverage summary.
- [ ] The file includes documentation gaps for DOC-E2.
- [ ] The file includes conflicts and uncertainties.
- [ ] No existing docs are modified.
- [ ] No code, tests, schemas, workflows, README, tickets, audit files, or decision notes are modified.

---

## 14. Suggested PR title

```text
DOC-E1: Add data and reports evidence inventory
```

## 15. Suggested PR summary

```text
## Summary
- Add a structured evidence inventory for data/report fields and artifacts
- Cover candidate exclusion, tradeability, execution, Entry-Location, null/skipped/failed semantics, report artifacts, schema_version/ir1.5+, and T30/evaluation outputs
- Identify documentation gaps for DOC-E2 without modifying canonical current-state docs

## Scope
- Documentation evidence inventory only
- No DATA_MODEL/REPORTS/SNAPSHOTS rewrite
- No code/test/schema/workflow changes

## Verification
- Confirmed only docs/audit/data_reports_evidence_inventory_v0.md was added
- Confirmed mandatory field/artifact subjects are covered with structured evidence blocks
- Confirmed uncertain claims are marked partial or needs_review
```
