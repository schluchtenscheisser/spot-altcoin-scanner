# DOC-A: Documentation Inventory Baseline

## Metadata

- Ticket ID: DOC-A
- Title: Documentation Inventory Baseline — Neutral Audit Snapshot
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Documentation audit artifact only
- Primary output: `docs/audit/documentation_inventory_v0.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Authority impact: None in this ticket

---

## 1. Context

The repository documentation is currently a mixed documentation corpus.

Historically, the scanner had an extensive and largely complete documentation set for the previous scanner version. With the v2.1 specification, the scanner was then substantially rebuilt by incrementally transforming the existing scanner rather than replacing it with a full greenfield implementation.

As a result, the current documentation under `docs/` and `docs/canonical/` is partly:

- documentation of the previous scanner version,
- high-level or bootstrap documentation from the v2.1 transformation,
- AI/context handoff documentation,
- schema/change tracking documentation,
- generated navigation material,
- and partially updated current-state documentation.

The goal of the broader documentation cleanup is to bring the documentation to a clean current-state baseline that primarily reflects the implemented repository reality: current code, tests, schemas, workflows, and current run artifacts.

Before updating authority rules or rewriting canonical documentation, this ticket records the current documentation inventory and known role conflicts as a neutral audit artifact.

---

## 2. Goal

Create a neutral documentation inventory file that captures the current documentation landscape and the known role/authority conflicts.

The inventory must help future documentation tickets understand:

1. which documentation files exist in scope,
2. which files currently claim authority or canonical status,
3. which files are explicitly or implicitly legacy/reference-only,
4. which files are AI/context helpers,
5. which files are generated navigation,
6. which files are tracking/change logs,
7. where role conflicts exist, especially between `docs/canonical/INDEX.md` and individual file headers.

This ticket must not resolve those conflicts.

---

## 3. Output

Create this file:

```text
docs/audit/documentation_inventory_v0.md
```

Create the directory if it does not exist:

```text
docs/audit/
```

The file must be a human-readable Markdown audit document.

---

## 4. Scope

Codex may only:

- create `docs/audit/documentation_inventory_v0.md`,
- create `docs/audit/` if missing.

Codex must use the inventory findings below as the primary content basis.

---

## 5. Out of Scope

This ticket must not:

- create `docs/AUTHORITY.md`,
- modify `docs/canonical/AUTHORITY.md`,
- modify `docs/canonical/INDEX.md`,
- modify `docs/canonical/WORKFLOW_CODEX.md`,
- modify `docs/AGENTS.md`,
- modify `docs/AI_CONTEXT_CURRENT.md`,
- modify `docs/dev_workflow.md`,
- modify `docs/tickets/_TEMPLATE.md`,
- modify any existing canonical documentation file,
- update file headers,
- change any file role,
- move or archive files,
- delete files,
- update README,
- change code,
- change tests,
- change schemas,
- change CI/workflows,
- change runtime behavior.

This is an inventory-only ticket.

---

## 6. Required inventory content

The new file must include these sections.

### 6.1 Purpose and non-authority statement

The inventory file must clearly state:

- it is an audit snapshot,
- it is not a source of documentation authority,
- it does not resolve conflicts,
- it does not reclassify files,
- it does not validate documentation against current code,
- it intentionally excludes `docs/legacy` and `docs/archiv`.

Required wording, semantically unchanged:

```text
This document is a neutral documentation inventory snapshot. It records observed documentation roles, labels, and conflicts. It does not resolve authority conflicts, does not reclassify documents, and does not validate documentation content against current code.
```

### 6.2 Historical context

Include this context:

```text
The documentation corpus contains a substantial amount of previous-scanner documentation. During the v2.1 transformation, the scanner was rebuilt incrementally from the existing scanner rather than replaced with a full greenfield implementation. Many documentation files were only partially updated at a high level. Therefore, existing `canonical` labels are inventory signals, not proof of current implemented-state authority.
```

### 6.3 Exclusions

Explicitly state that the following paths are excluded from this inventory:

```text
docs/legacy
docs/archiv
```

If `docs/archiv` does not exist, mention that it was excluded by policy/request regardless.

### 6.4 Document groups

Include a table with these groups:

| Group | Meaning |
|---|---|
| `current_state_candidate` | Candidate for future current-state documentation; must be validated against code/tests/schemas/artifacts before being treated as current-state authority |
| `bootstrap_skeleton` | v2.1 transformation or bootstrap documentation; likely needs update or replacement |
| `legacy_prev_scanner_doc` | Previous scanner documentation retained as reference unless explicitly revalidated |
| `mixed_or_conflicting_role` | Document or folder where labels/headers/index roles conflict |
| `tracking_doc` | Change log, open questions, feature/enhancement tracking, schema history |
| `ai_context_helper` | AI/Codex/ChatGPT/Claude context or routing helper |
| `generated_navigation` | Generated structural navigation, not authority |
| `process_doc` | Ticket, workflow, or maintenance process documentation |
| `stub_legacy_redirect` | Stub that points to legacy material and explicitly denies source-of-truth status |

### 6.5 Authority and precedence conflict summary

Include these observed conflicts:

1. `docs/canonical/AUTHORITY.md` currently reflects older precedence logic where the v2.1 build-spec / Gesamtkonzept sit ahead of `docs/canonical/*`.
2. `docs/canonical/WORKFLOW_CODEX.md` and `docs/AI_CONTEXT_CURRENT.md` reflect a newer repo-reality-first hierarchy.
3. `docs/canonical/INDEX.md` classifies multiple files/folders as `legacy_reference_only`, while some files inside those folders still declare `status: canonical`.
4. `docs/SCHEMA_CHANGES.md` appears more current for some report/diagnostics schema semantics than `docs/canonical/REPORTS.md`.
5. `docs/dev_workflow.md` contains older process wording, including the idea that `docs/code_map.md` becomes a single source of truth for repository structure, which conflicts with later role definitions where code map is generated navigation only.
6. `docs/canonical/AUTHORITY.md` already exists and contains authority precedence logic that conflicts with `docs/canonical/WORKFLOW_CODEX.md`. A second root-level `docs/AUTHORITY.md` does not exist and must not be introduced by this ticket. DOC-B is expected to consolidate authority into the existing `docs/canonical/AUTHORITY.md`, not create a parallel authority file.

Do not resolve these conflicts in DOC-A.

### 6.6 Top-level `docs/` inventory

Include at least these files and classifications:

| Path | Inventory class | Notes |
|---|---|---|
| `docs/AGENTS.md` | `ai_context_helper / process_hint` | Useful agent hint; currently labels itself canonical and points to `docs/canonical/AUTHORITY.md`; duplicate `INDEX.md` entry observed |
| `docs/AI_CONTEXT_CURRENT.md` | `ai_context_helper / implementation_status_summary` | Important current context; explicitly not a full current-state technical manual |
| `docs/GPT_SNAPSHOT.md` | `ai_context_helper / stale_snapshot` | Useful AI onboarding snapshot; last reviewed for post-T1–T22 / T21.1, therefore stale relative to T29/T_EL2/ir1.5 |
| `docs/SCHEMA_CHANGES.md` | `tracking_doc / schema_history_authority` | Important schema/change evidence log; currently includes ir1.5 operational tradeability semantics |
| `docs/code_map.md` | `generated_navigation` | Auto-generated structural navigation; not architecture authority |
| `docs/dev_workflow.md` | `legacy_prev_scanner_doc / stale_process_doc` | Older process documentation; likely superseded by `docs/canonical/WORKFLOW_CODEX.md` in a later ticket |
| `docs/gpt_snapshot_guide.md` | `process_doc / ai_context_helper` | Snapshot process guide; role is generally clean |
| `docs/readme_guide.md` | `process_doc / possibly_stale_wording` | README guide; useful but uses broad `/docs/*.md` terminology |
| `docs/t30_forward_return_evaluation_v1.md` | `evaluation_runbook / needs_version_check` | Manual exploratory T30 v1 runbook; may need version check against T30-v2 and later evaluation work |
| `docs/tickets/_TEMPLATE.md` | `process_doc / process_authority` | Important ticket template; later DOC-C should add explicit Documentation Impact requirements |
| `docs/spec.md` | `stub_legacy_redirect` | Stub only; explicitly not source of truth |
| `docs/scoring.md` | `stub_legacy_redirect` | Stub only; explicitly not source of truth |

### 6.7 `docs/canonical/` active/current candidate inventory

Include these files and preliminary inventory notes:

| Path | Inventory class | Notes |
|---|---|---|
| `docs/canonical/AUTHORITY.md` | `authority_doc / needs_consolidation` | Existing authority file; currently conflicts with newer repo-reality-first hierarchy |
| `docs/canonical/INDEX.md` | `role_index / needs_precision_update` | Existing roles/navigation index; remains important and should be kept as roles index |
| `docs/canonical/WORKFLOW_CODEX.md` | `process_doc / repo_reality_first_authority_signal` | Contains newer repo-reality-first hierarchy |
| `docs/canonical/ARCHITECTURE.md` | `current_state_candidate / bootstrap_skeleton` | Needs validation against current code |
| `docs/canonical/SCOPE.md` | `bootstrap_skeleton` | Likely v2.1/bootstrap scope, not full current-state scope |
| `docs/canonical/DATA_MODEL.md` | `current_state_candidate / likely_incomplete` | Candidate for current data model, but likely still skeleton/incomplete |
| `docs/canonical/RUNTIME_AND_OPERATIONS.md` | `current_state_candidate / needs_code_validation` | Candidate for runtime docs, but must be checked against actual workflows/runners |
| `docs/canonical/REPORTS.md` | `current_state_candidate / likely_stale_schema` | Must be reconciled with `docs/SCHEMA_CHANGES.md`, especially ir1.5 |
| `docs/canonical/SNAPSHOTS.md` | `current_state_candidate / needs_validation` | Needs validation against runtime/history/replay artifacts |
| `docs/canonical/TEST_STRATEGY.md` | `current_state_candidate / process_mix` | Likely useful but may mix test strategy and AI-sparring context |
| `docs/canonical/MIGRATION_NOTES.md` | `migration_context` | Useful for previous-scanner to Independence transition context |
| `docs/canonical/CHANGELOG.md` | `tracking_doc / likely_incomplete` | Needs freshness check |
| `docs/canonical/GLOSSARY.md` | `current_state_candidate / needs_validation` | Useful terminology map, must be checked against current code |
| `docs/canonical/ROADMAP.md` | `planning_doc` | Planning/roadmap context |
| `docs/canonical/open_questions.md` | `tracking_doc / active` | Active open questions / stop conditions |
| `docs/canonical/feature_enhancements.md` | `tracking_doc / active` | Deferred/completed enhancement tracking |
| `docs/canonical/CANONICAL_CONSISTENCY_CHECKLIST.md` | `process_doc` | Canonical helper for future consistency checks |

### 6.8 `docs/canonical/` legacy-reference inventory

Record that `docs/canonical/INDEX.md` currently treats the following as `legacy_reference_only`:

```text
docs/canonical/PIPELINE.md
docs/canonical/DATA_SOURCES.md
docs/canonical/CONFIGURATION.md
docs/canonical/OUTPUT_SCHEMA.md
docs/canonical/VERIFICATION_FOR_AI.md
docs/canonical/MAPPING.md
docs/canonical/DECISION_LAYER.md
docs/canonical/RISK_MODEL.md
docs/canonical/BUDGET_AND_POOL_MODEL.md
docs/canonical/SCORING/*
docs/canonical/LIQUIDITY/*
docs/canonical/FEATURES/*
docs/canonical/OUTPUTS/*
docs/canonical/BACKTEST/*
```

Also record:

- `PIPELINE.md`, `OUTPUT_SCHEMA.md`, and `DECISION_LAYER.md` visibly include `role: legacy_reference_only`.
- `DATA_SOURCES.md`, `CONFIGURATION.md`, `MAPPING.md`, `RISK_MODEL.md`, and `BUDGET_AND_POOL_MODEL.md` still visibly declare `status: canonical` or strong authority language, which creates a role conflict with the index classification.

### 6.9 Subfolder role-conflict inventory

Include the observed subfolder findings.

#### `docs/canonical/FEATURES/`

Observed files:

```text
docs/canonical/FEATURES/FEAT_ATR_WILDER.md
docs/canonical/FEATURES/FEAT_EMA_STANDARD.md
docs/canonical/FEATURES/FEAT_VOLUME_SPIKE.md
docs/canonical/FEATURES/FEAT_ATR_PCT_RANK_120_1D.md
docs/canonical/FEATURES/FEAT_BB_WIDTH_4H_RANK_120.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed files still declare status: canonical.
```

#### `docs/canonical/LIQUIDITY/`

Observed files:

```text
docs/canonical/LIQUIDITY/RE_RANK_RULE.md
docs/canonical/LIQUIDITY/ORDERBOOK_TOPK_POLICY.md
docs/canonical/LIQUIDITY/SLIPPAGE_CALCULATION.md
docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed files still declare status: canonical. TRADEABILITY_GATE.md is especially important for later validation because current execution/tradeability semantics remain central to the scanner.
```

#### `docs/canonical/OUTPUTS/`

Observed files:

```text
docs/canonical/OUTPUTS/EVALUATION_DATASET.md
docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md
docs/canonical/OUTPUTS/SHADOW_CALIBRATION_PREP_REPORT.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed files still declare status: canonical. Some files may represent later evaluation/output work rather than pure previous-scanner documentation and require ticket/code validation before reclassification.
```

#### `docs/canonical/BACKTEST/`

Observed files:

```text
docs/canonical/BACKTEST/MODEL_E2.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while the observed file declares status: canonical and purpose: analytics_only.
```

#### `docs/canonical/SCORING/`

Observed files:

```text
docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md
docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed files still declare status: canonical. This group likely contains previous-scanner scoring logic and requires careful validation before reuse.
```

### 6.10 Current-state documentation candidates

Record these future high-priority validation/update candidates:

| Priority | Path | Reason |
|---:|---|---|
| 1 | `docs/canonical/DATA_MODEL.md` | Central field/schema documentation |
| 1 | `docs/canonical/REPORTS.md` | Report/diagnostics schema; likely stale versus `SCHEMA_CHANGES.md` |
| 1 | `docs/canonical/RUNTIME_AND_OPERATIONS.md` | Runtime, Shadow-Live, scheduling, persistence |
| 1 | `docs/canonical/ARCHITECTURE.md` | Current module/pipeline architecture |
| 2 | `docs/canonical/SNAPSHOTS.md` | Runtime/history/replay artifacts |
| 2 | `docs/canonical/GLOSSARY.md` | Terminology and spec-to-implementation mapping |
| 2 | `docs/SCHEMA_CHANGES.md` | Strong schema evidence log |
| 3 | `docs/canonical/TEST_STRATEGY.md` | Test strategy update |
| 3 | `docs/t30_forward_return_evaluation_v1.md` | Evaluation runbook version check |

### 6.11 Future ticket sequence

End the document with this recommended sequence:

```text
DOC-B — Documentation Authority Consolidation
- Update docs/canonical/AUTHORITY.md.
- Do not create docs/AUTHORITY.md.
- Keep docs/canonical/INDEX.md as the roles index.
- Align docs/canonical/INDEX.md, docs/canonical/WORKFLOW_CODEX.md, docs/AGENTS.md, and docs/AI_CONTEXT_CURRENT.md with the consolidated authority model.
- Supersede docs/dev_workflow.md via docs/canonical/WORKFLOW_CODEX.md.
- Establish current code + tests + schemas + current artifacts as the primary anchor for current-state documentation.

DOC-C — Documentation Impact Process Guard
- Update docs/tickets/_TEMPLATE.md and related process docs.
- Require every future implementation ticket to explicitly state documentation impact.

DOC-D+ — Current-State Canonical Documentation Updates
- Prioritize DATA_MODEL, REPORTS, RUNTIME_AND_OPERATIONS, ARCHITECTURE, SNAPSHOTS.
- Use current code, tests, schemas, current artifacts, SCHEMA_CHANGES.md, implementation tickets, and PR evidence.
```

---

## 7. Verification

After implementation, verify:

1. `docs/audit/documentation_inventory_v0.md` exists.
2. No existing documentation files were modified.
3. No code files were modified.
4. No tests were modified.
5. No schema files were modified.
6. No CI/workflow files were modified.
7. No new `docs/AUTHORITY.md` file was created, and `docs/canonical/AUTHORITY.md` was not modified.
8. The inventory file explicitly states that it is non-authoritative and does not resolve conflicts.
9. The inventory file explicitly excludes `docs/legacy` and `docs/archiv`.
10. The inventory file includes the role-conflict findings for `docs/canonical/FEATURES/*`, `LIQUIDITY/*`, `OUTPUTS/*`, `BACKTEST/*`, and `SCORING/*`.

---

## 8. Documentation impact

This ticket creates a documentation audit artifact only.

Expected documentation impact:

```text
Created:
- docs/audit/documentation_inventory_v0.md

Modified:
- none
```

No canonical documentation is updated in this ticket.

---

## 9. Acceptance criteria

- [ ] `docs/audit/documentation_inventory_v0.md` is created.
- [ ] The file is written in English.
- [ ] The file is clearly marked as a neutral inventory/audit snapshot.
- [ ] The file states that it is not authoritative and does not resolve conflicts.
- [ ] The file states that `docs/legacy` and `docs/archiv` are excluded.
- [ ] The file captures the documentation groups listed in this ticket.
- [ ] The file captures the authority/preference conflicts listed in this ticket.
- [ ] The file captures the `docs/canonical/INDEX.md` vs. file-header conflicts.
- [ ] The file captures the future DOC-B / DOC-C / DOC-D+ sequence.
- [ ] No existing documentation files are changed.
- [ ] No code, tests, schemas, or CI/workflows are changed.
- [ ] No `docs/AUTHORITY.md` file is created.
- [ ] `docs/canonical/AUTHORITY.md` is not modified.

---

## 10. Suggested PR title

```text
DOC-A: Add documentation inventory baseline
```

## 11. Suggested PR summary

```text
## Summary
- Add a neutral documentation inventory audit under docs/audit/
- Record current documentation groups, authority conflicts, and role-label inconsistencies
- Capture the planned DOC-B/DOC-C/DOC-D+ follow-up sequence

## Scope
- Documentation-only audit artifact
- No authority changes
- No canonical rewrites
- No code/test/schema/workflow changes

## Verification
- Confirmed only docs/audit/documentation_inventory_v0.md was added
```
