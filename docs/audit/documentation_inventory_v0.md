# Documentation Inventory Baseline v0

## 1. Purpose and non-authority statement

This document is a neutral documentation inventory snapshot. It records observed documentation roles, labels, and conflicts. It does not resolve authority conflicts, does not reclassify documents, and does not validate documentation content against current code.

This audit snapshot is not a source of documentation authority. It records the documentation landscape as inventory input for later documentation cleanup tickets only. It does not change any file role, does not supersede existing documentation, and does not decide which conflicting source should win.

This inventory intentionally excludes `docs/legacy` and `docs/archiv`.

## 2. Historical context

The documentation corpus contains a substantial amount of previous-scanner documentation. During the v2.1 transformation, the scanner was rebuilt incrementally from the existing scanner rather than replaced with a full greenfield implementation. Many documentation files were only partially updated at a high level. Therefore, existing `canonical` labels are inventory signals, not proof of current implemented-state authority.

## 3. Exclusions

The following paths are excluded from this inventory:

```text
docs/legacy
docs/archiv
```

`docs/archiv` is excluded by policy/request regardless of whether that path currently exists in the repository.

## 4. Document groups

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

## 5. Authority and precedence conflict summary

Observed conflicts for later follow-up, without resolution in DOC-A:

1. `docs/canonical/AUTHORITY.md` currently reflects older precedence logic where the v2.1 build-spec / Gesamtkonzept sit ahead of `docs/canonical/*`.
2. `docs/canonical/WORKFLOW_CODEX.md` and `docs/AI_CONTEXT_CURRENT.md` reflect a newer repo-reality-first hierarchy.
3. `docs/canonical/INDEX.md` classifies multiple files/folders as `legacy_reference_only`, while some files inside those folders still declare `status: canonical`.
4. `docs/SCHEMA_CHANGES.md` appears more current for some report/diagnostics schema semantics than `docs/canonical/REPORTS.md`.
5. `docs/dev_workflow.md` contains older process wording, including the idea that `docs/code_map.md` becomes a single source of truth for repository structure, which conflicts with later role definitions where code map is generated navigation only.
6. `docs/canonical/AUTHORITY.md` already exists and contains authority precedence logic that conflicts with `docs/canonical/WORKFLOW_CODEX.md`. A second root-level `docs/AUTHORITY.md` does not exist and must not be introduced by this ticket. DOC-B is expected to consolidate authority into the existing `docs/canonical/AUTHORITY.md`, not create a parallel authority file.

DOC-A does not resolve these conflicts.

## 6. Top-level `docs/` inventory

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

## 7. `docs/canonical/` active/current candidate inventory

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

## 8. `docs/canonical/` legacy-reference inventory

`docs/canonical/INDEX.md` currently treats the following as `legacy_reference_only`:

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

Additional observed notes:

- `PIPELINE.md`, `OUTPUT_SCHEMA.md`, and `DECISION_LAYER.md` visibly include `role: legacy_reference_only`.
- `DATA_SOURCES.md`, `CONFIGURATION.md`, `MAPPING.md`, `RISK_MODEL.md`, and `BUDGET_AND_POOL_MODEL.md` still visibly declare `status: canonical` or strong authority language, which creates a role conflict with the index classification.

## 9. Subfolder role-conflict inventory

### 9.1 `docs/canonical/FEATURES/`

Observed files:

```text
docs/canonical/FEATURES/FEAT_ATR_WILDER.md
docs/canonical/FEATURES/FEAT_EMA_STANDARD.md
docs/canonical/FEATURES/FEAT_PERCENT_RANK.md
docs/canonical/FEATURES/FEAT_VOLUME_SPIKE.md
docs/canonical/FEATURES/FEAT_ATR_PCT_RANK_120_1D.md
docs/canonical/FEATURES/FEAT_BB_WIDTH_4H_RANK_120.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed documentation files declare or appear to declare canonical status.
```

### 9.2 `docs/canonical/LIQUIDITY/`

Observed files:

```text
docs/canonical/LIQUIDITY/RE_RANK_RULE.md
docs/canonical/LIQUIDITY/ORDERBOOK_TOPK_POLICY.md
docs/canonical/LIQUIDITY/SLIPPAGE_CALCULATION.md
docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed documentation files declare or appear to declare canonical status. TRADEABILITY_GATE.md is especially important for later validation because current execution/tradeability semantics remain central to the scanner.
```

### 9.3 `docs/canonical/OUTPUTS/`

Observed files:

```text
docs/canonical/OUTPUTS/EVALUATION_DATASET.md
docs/canonical/OUTPUTS/RUNTIME_MARKET_META_EXPORT.md
docs/canonical/OUTPUTS/SHADOW_CALIBRATION_PREP_REPORT.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed documentation files declare or appear to declare canonical status. Some files may represent later evaluation/output work rather than pure previous-scanner documentation and require ticket/code validation before reclassification.
```

### 9.4 `docs/canonical/BACKTEST/`

Observed files:

```text
docs/canonical/BACKTEST/MODEL_E2.md
docs/canonical/BACKTEST/TRADE_MODEL_4H_IMMEDIATE_RETEST.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed documentation files declare or appear to declare canonical status, including `MODEL_E2.md` with `purpose: analytics_only`.
```

### 9.5 `docs/canonical/SCORING/`

Observed files:

```text
docs/canonical/SCORING/DISCOVERY_TAG.md
docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md
docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md
docs/canonical/SCORING/SETUP_VALIDITY_RULES.md
```

Inventory finding:

```text
The folder is classified as legacy_reference_only by docs/canonical/INDEX.md, while observed documentation files declare or appear to declare canonical status. This group likely contains previous-scanner scoring logic and requires careful validation before reuse.
```

## 10. Current-state documentation candidates

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

## 11. Future ticket sequence

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
