# DOC-D: Current-State Runtime & Architecture Documentation

## Metadata

- Ticket ID: DOC-D
- Title: Current-State Runtime & Architecture Documentation
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Current-state documentation update
- Primary files:
  - `docs/canonical/ARCHITECTURE.md`
  - `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- Optional file:
  - `docs/canonical/INDEX.md` — only if needed for role/navigation alignment
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Predecessors:
  - DOC-A — `docs/audit/documentation_inventory_v0.md`
  - DOC-B — consolidated authority model in `docs/canonical/AUTHORITY.md`
  - DOC-C — documentation impact process guard
  - CODE-A1 — `docs/audit/active_code_path_inventory_v0.md`
  - CODE-A2 — `docs/audit/legacy_pipeline_boundary_review_v0.md`
  - Boundary Decision Note — `docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md`
  - CODE-FU-A — `docs/tickets/2026-06-07__CODE-FU-A__extract_active_tradeability_metrics.md`
  - CODE-FU-D — `docs/tickets/2026-06-07__CODE-FU-D__canonical_run_modes_compatibility_alias_policy.md`

---

## 1. Context

DOC-D was intentionally paused until the project clarified which code paths are active current-state runtime and which paths are legacy or compatibility residue.

That prerequisite has now been completed.

CODE-A1 identified the active runtime entry points and active module groups.

CODE-A2 reviewed legacy pipeline boundary conflicts and produced a decision matrix.

The Boundary Decision Note recorded Martin's decisions for the legacy pipeline boundary cases.

CODE-FU-A removed the active execution dependency on `scanner.pipeline.liquidity` and introduced the active deterministic target path:

```text
scanner/execution/tradeability_metrics.py
```

CODE-FU-D clarified canonical run modes and compatibility aliases.

Therefore DOC-D can now update architecture/runtime documentation without accidentally presenting legacy pipeline code as active current-state runtime.

---

## 2. Problem

The current canonical architecture and runtime documentation is not yet aligned with the implemented post-v2.1 scanner state.

The main risk is misclassifying legacy/compatibility code paths as current runtime architecture, especially under `scanner/pipeline/*`.

The documentation must now clearly distinguish:

1. active Daily/Intraday runtime paths,
2. active runtime module groups,
3. active evaluation/replay infrastructure,
4. legacy/compatibility snapshot/evaluation/backfill paths,
5. compatibility aliases for old mode names.

---

## 3. Goal

Update current-state architecture and runtime/operations documentation so it accurately reflects the implemented repository state after CODE-A1, CODE-A2, CODE-FU-A, and CODE-FU-D.

After this ticket:

1. `docs/canonical/ARCHITECTURE.md` documents active runtime entry points and module responsibilities at module-group level.
2. `docs/canonical/RUNTIME_AND_OPERATIONS.md` documents canonical run modes, compatibility aliases, and operational boundaries.
3. `scanner/pipeline/*` is neither documented as current Daily/Intraday runtime architecture nor incorrectly described as completely unused.
4. Legacy/compatibility paths are explicitly classified.
5. Deep field/report semantics remain out of scope for later DOC-E.

---

## 4. Scope

Codex may modify only:

```text
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
```

Codex may modify this file only if needed for navigation/role alignment:

```text
docs/canonical/INDEX.md
```

If `docs/canonical/INDEX.md` is modified, the change must be minimal and only reflect the role/navigation state of the updated docs.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/SNAPSHOTS.md
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
- run outputs,
- audit files,
- decision notes,
- legacy/reference-only docs.

Codex must not:

- update field-level data model semantics,
- update report field semantics,
- update diagnostics field semantics,
- update Entry-Location field definitions,
- update T30 field definitions,
- update schema versions,
- infer runtime behavior without evidence,
- treat `scanner/pipeline/*` as either fully active or fully dead.

---

## 6. Read-only evidence sources

Codex must use the following as read-only evidence:

```text
docs/audit/active_code_path_inventory_v0.md
docs/audit/legacy_pipeline_boundary_review_v0.md
docs/decision_notes/2026-06-07__legacy_pipeline_boundary_decision_note.md
docs/tickets/2026-06-07__CODE-FU-A__extract_active_tradeability_metrics.md
docs/tickets/2026-06-07__CODE-FU-D__canonical_run_modes_compatibility_alias_policy.md
```

If evidence sources conflict, apply this precedence rule:

```text
The Boundary Decision Note takes precedence over CODE-A1/CODE-A2 where it explicitly decides a boundary classification.
Where the Boundary Decision Note is silent, CODE-A1 classification applies.
CODE-A2 should be used as supporting boundary-analysis context.
Current code should be used to verify that the documented state still matches the repository after CODE-FU-A and CODE-FU-D.
```

Codex must also inspect the current code paths as evidence, including:

```text
scanner/main.py
scanner/runners/daily.py
scanner/runners/intraday.py
scanner/features/
scanner/axes/
scanner/phase/
scanner/state/
scanner/entry/
scanner/decision/
scanner/execution/
scanner/output/
scanner/storage/
scanner/evaluation/
```

Codex may inspect legacy/compatibility paths as evidence, but must classify them according to this ticket and the decision note:

```text
scanner/pipeline/
scanner/tools/export_evaluation_dataset.py
scanner/tools/backfill_snapshots.py
scanner/backtest/e2_model.py
```

---

## 7. Required architecture description depth

`docs/canonical/ARCHITECTURE.md` must document architecture at module-group level.

Codex must include:

1. active entry points,
2. active Daily/Intraday runtime flow,
3. active module groups and their responsibilities,
4. data flow between module groups,
5. active evaluation/replay boundary,
6. legacy/compatibility boundary.

Codex must not include:

- function-by-function API documentation,
- implementation internals,
- function signatures,
- exhaustive class/function listings,
- speculative future architecture,
- obsolete previous-scanner architecture as active current state.

Required description depth:

```text
Module groups and their responsibilities: yes.
Data flow between groups: yes.
Entry points and runtime boundaries: yes.
Function signatures and implementation details: no.
Full API documentation: no.
```

---

## 8. Active runtime architecture requirements

`docs/canonical/ARCHITECTURE.md` must reflect the following active runtime entry points:

```text
scanner/main.py
scanner/runners/daily.py
scanner/runners/intraday.py
```

It must document the active Daily/Intraday runtime module groups:

```text
scanner/features
scanner/axes
scanner/phase
scanner/state
scanner/entry
scanner/decision
scanner/execution
scanner/output
scanner/storage
```

It must document active evaluation/replay infrastructure as primarily:

```text
scanner/evaluation/*
```

It must explicitly state that:

```text
scanner/tools/export_evaluation_dataset.py is not part of the active scanner/evaluation/* infrastructure. It is the Legacy Snapshot Evaluation Export Path.
```

---

## 9. Mandatory legacy/compatibility boundary table

Codex must reflect the following classifications in `docs/canonical/ARCHITECTURE.md`.

Use this table verbatim or semantically unchanged:

| Path / component | Current classification |
|---|---|
| `scanner.pipeline.liquidity` | Previous active dependency removed by CODE-FU-A; active tradeability metrics now live under `scanner/execution/tradeability_metrics.py` |
| `scanner/execution/tradeability_metrics.py` | Active current-state target path for execution/tradeability metrics |
| `scanner.pipeline.global_ranking.compute_global_top20` | Legacy |
| `scanner.backtest.e2_model` | Legacy compatibility helper tied to legacy snapshot exporter |
| `scanner/tools/export_evaluation_dataset.py` | Legacy Snapshot Evaluation Export Path, not active `scanner/evaluation/*` infrastructure |
| `scanner/tools/backfill_snapshots.py --mode full` | Compatibility-only / historical reconstruction path |
| `scanner.pipeline.run_pipeline` | Not active v2.1 Daily/Intraday runtime |
| `scanner.pipeline.scoring/*` | Relevant only in old/full backfill compatibility path, not active Daily/Intraday runtime |
| old mode names `standard`, `fast`, `offline`, `backtest` | Compatibility aliases only; not independent runtime modes |

`docs/canonical/ARCHITECTURE.md` must also include this statement verbatim or semantically unchanged:

```text
scanner/pipeline/* is not the current Daily/Intraday runtime architecture. It remains only where explicitly retained as legacy/compatibility or historical reconstruction support.
```

---

## 10. Runtime and operations requirements

`docs/canonical/RUNTIME_AND_OPERATIONS.md` must document:

1. active run entry points,
2. daily vs intraday operational distinction,
3. canonical run mode naming,
4. compatibility alias handling,
5. storage/report scan_mode boundary,
6. legacy full-mode backfill boundary,
7. operational expectation that compatibility aliases do not leak into new storage/report contexts.

### 10.1 Mandatory run-mode distinction

Codex must reproduce this distinction verbatim or semantically unchanged in `docs/canonical/RUNTIME_AND_OPERATIONS.md`:

```text
SQLite run_metadata.scan_mode:   daily_discovery / intraday_promotion   (T1-canonical)
Report/Diagnostics scan_mode:    daily / intraday                        (T13-canonical)
Compatibility aliases:           standard / fast / offline / backtest    (CLI/input-layer only)
```

Required semantics:

- SQLite `run_metadata.scan_mode` uses `daily_discovery` / `intraday_promotion`.
- Report/Diagnostics `scan_mode` uses `daily` / `intraday`.
- Old input names `standard`, `fast`, `offline`, `backtest` are compatibility aliases only.
- Compatibility aliases may exist at CLI/config/input-layer boundaries.
- Compatibility aliases must not be documented as canonical runtime modes.
- Compatibility aliases must not leak into new Storage, Report, or Diagnostics contexts.

### 10.2 Mandatory compatibility wording

`docs/canonical/RUNTIME_AND_OPERATIONS.md` must include this statement verbatim or semantically unchanged:

```text
The old mode names standard, fast, offline, and backtest are compatibility aliases at the CLI/config/input layer. They are not independent runtime modes and must not be emitted as new canonical Storage, Report, or Diagnostics scan_mode values.
```

### 10.3 Backfill compatibility boundary

`docs/canonical/RUNTIME_AND_OPERATIONS.md` must document:

```text
backfill_snapshots.py --mode full is retained as compatibility-only / historical reconstruction support. It is not the current v2.1 Daily/Intraday runtime.
```

---

## 11. Required document structure guidance

Codex may adapt headings to the existing document style, but the updated docs must contain these concepts.

### 11.1 `docs/canonical/ARCHITECTURE.md`

Required sections or equivalent:

1. Purpose / scope of the document.
2. Active runtime entry points.
3. Active Daily/Intraday runtime flow.
4. Active module groups and responsibilities.
5. Active evaluation/replay boundary.
6. Legacy and compatibility boundaries.
7. Explicit `scanner/pipeline/*` boundary.
8. Pointers to later docs for data/report field semantics.

### 11.2 `docs/canonical/RUNTIME_AND_OPERATIONS.md`

Required sections or equivalent:

1. Purpose / scope of the document.
2. Runtime entry points.
3. Daily vs intraday operation.
4. Canonical run mode naming.
5. Storage vs Report/Diagnostics scan_mode distinction.
6. Compatibility aliases.
7. Backfill / historical reconstruction compatibility.
8. Operational guardrails.
9. Pointers to later docs for output/report/data model details.

---

## 12. Relationship to later DOC-E

DOC-D must avoid deep field/report/data semantics.

The following belong to later DOC-E, not DOC-D:

```text
candidate_excluded
is_tradeable_candidate
is_operational_trade_candidate
execution_status
execution_size_class
is_reduced_size_eligible
Entry-Location fields
T30 output fields
diagnostics/report field definitions
schema_version field semantics beyond run-mode boundary
nullable / not_evaluated semantics
```

DOC-D may mention those areas only as examples of output/data semantics that are handled elsewhere.

---

## 13. Documentation impact

### Variant A — Documentation update required

Affected documentation:

- [x] `docs/canonical/ARCHITECTURE.md`
- [x] `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- [ ] `docs/canonical/INDEX.md` — only if needed for navigation/role alignment

Documentation update plan:

- Update `ARCHITECTURE.md` to document active current-state runtime architecture, active module groups, data flow at module-group level, and legacy/compatibility boundaries.
- Update `RUNTIME_AND_OPERATIONS.md` to document active run entry points, canonical scan_mode contexts, compatibility aliases, and backfill compatibility boundary.
- Update `INDEX.md` only if needed to align role/navigation references.

---

## 14. Verification

After implementation, verify:

1. Only allowed files were modified:
   - `docs/canonical/ARCHITECTURE.md`
   - `docs/canonical/RUNTIME_AND_OPERATIONS.md`
   - optionally `docs/canonical/INDEX.md`
2. No code, tests, schemas, workflows, README, audit files, decision notes, or tickets were modified.
3. `docs/canonical/ARCHITECTURE.md` documents active runtime entry points:
   - `scanner/main.py`
   - `scanner/runners/daily.py`
   - `scanner/runners/intraday.py`
4. `docs/canonical/ARCHITECTURE.md` documents active runtime module groups.
5. `docs/canonical/ARCHITECTURE.md` includes the mandatory legacy/compatibility boundary table or semantically equivalent content.
6. `docs/canonical/ARCHITECTURE.md` states that `scanner/pipeline/*` is not the current Daily/Intraday runtime architecture.
7. `docs/canonical/ARCHITECTURE.md` does not document function signatures or full API details.
8. `docs/canonical/RUNTIME_AND_OPERATIONS.md` includes the mandatory scan_mode distinction:
   - SQLite `run_metadata.scan_mode`: `daily_discovery` / `intraday_promotion`
   - Report/Diagnostics `scan_mode`: `daily` / `intraday`
   - Compatibility aliases: `standard` / `fast` / `offline` / `backtest`
9. `docs/canonical/RUNTIME_AND_OPERATIONS.md` states that compatibility aliases are CLI/config/input-layer only.
10. `docs/canonical/RUNTIME_AND_OPERATIONS.md` states that compatibility aliases must not be emitted as new canonical Storage, Report, or Diagnostics scan_mode values.
11. `docs/canonical/RUNTIME_AND_OPERATIONS.md` documents `backfill_snapshots.py --mode full` as compatibility-only / historical reconstruction support.
12. DOC-D does not update field/report/data semantics reserved for DOC-E.
13. `docs/AI_CONTEXT_CURRENT.md` was not modified.

Suggested local checks:

```bash
git diff --name-only

grep -n "scanner/main.py" docs/canonical/ARCHITECTURE.md
grep -n "scanner/runners/daily.py" docs/canonical/ARCHITECTURE.md
grep -n "scanner/runners/intraday.py" docs/canonical/ARCHITECTURE.md
grep -n "scanner/pipeline" docs/canonical/ARCHITECTURE.md
grep -n "not the current" docs/canonical/ARCHITECTURE.md
grep -n "tradeability_metrics.py" docs/canonical/ARCHITECTURE.md

grep -n "daily_discovery" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "intraday_promotion" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "standard" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "fast" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "offline" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "backtest" docs/canonical/RUNTIME_AND_OPERATIONS.md
grep -n "CLI/config/input" docs/canonical/RUNTIME_AND_OPERATIONS.md
```

---

## 15. Acceptance criteria

- [ ] `docs/canonical/ARCHITECTURE.md` is updated to current-state runtime architecture.
- [ ] `docs/canonical/ARCHITECTURE.md` documents module groups and responsibilities, not function-level API details.
- [ ] `docs/canonical/ARCHITECTURE.md` documents active Daily/Intraday runtime entry points.
- [ ] `docs/canonical/ARCHITECTURE.md` documents active runtime module groups.
- [ ] `docs/canonical/ARCHITECTURE.md` documents active `scanner/evaluation/*` as evaluation/replay infrastructure.
- [ ] `docs/canonical/ARCHITECTURE.md` classifies `scanner/tools/export_evaluation_dataset.py` as Legacy Snapshot Evaluation Export Path.
- [ ] `docs/canonical/ARCHITECTURE.md` includes the required legacy/compatibility boundary classifications.
- [ ] `docs/canonical/ARCHITECTURE.md` does not present `scanner/pipeline/*` as current Daily/Intraday runtime architecture.
- [ ] `docs/canonical/ARCHITECTURE.md` does not present `scanner/pipeline/*` as completely unused.
- [ ] `docs/canonical/RUNTIME_AND_OPERATIONS.md` documents the two scan_mode contexts exactly or semantically unchanged.
- [ ] `docs/canonical/RUNTIME_AND_OPERATIONS.md` documents compatibility aliases as CLI/config/input-layer only.
- [ ] `docs/canonical/RUNTIME_AND_OPERATIONS.md` states that old mode names are not independent runtime modes.
- [ ] `docs/canonical/RUNTIME_AND_OPERATIONS.md` documents `backfill_snapshots.py --mode full` as compatibility-only / historical reconstruction support.
- [ ] `docs/canonical/INDEX.md` is unchanged unless navigation/role alignment required a minimal update.
- [ ] No code, tests, schemas, workflows, audit files, decision notes, tickets, README, or AI context docs were modified.

---

## 16. Suggested PR title

```text
DOC-D: Update current-state runtime and architecture docs
```

## 17. Suggested PR summary

```text
## Summary
- Update ARCHITECTURE.md with active Daily/Intraday runtime entry points, module groups, and legacy boundaries
- Update RUNTIME_AND_OPERATIONS.md with canonical scan_mode contexts and compatibility alias policy
- Clarify scanner/pipeline compatibility boundaries after CODE-A1/A2 and CODE-FU-A/D

## Scope
- Documentation only
- Runtime/architecture docs only
- No data/report field semantics
- No code/test/schema/workflow changes

## Verification
- Confirmed active runtime entry points documented
- Confirmed scanner/pipeline boundary documented without treating it as fully active or fully dead
- Confirmed scan_mode contexts and compatibility aliases documented
- Confirmed DOC-E field/report semantics remain out of scope
```
