# CODE-A2: Legacy Pipeline Boundary Review & Decision Matrix

## Metadata

- Ticket ID: CODE-A2
- Title: Legacy Pipeline Boundary Review & Decision Matrix
- Status: Draft — Codex-ready after Martin approval
- Priority: P0 / P1 documentation prerequisite
- Type: Audit + decision-preparation artifact
- Language: Audit artifact in English
- Primary output: `docs/audit/legacy_pipeline_boundary_review_v0.md`
- Scope type: Repository boundary review, no behavior change
- Depends on: CODE-A1 — `docs/audit/active_code_path_inventory_v0.md`
- Blocks: DOC-D / current-state documentation updates until reviewed
- Related evidence:
  - `docs/audit/active_code_path_inventory_v0.md`
  - `docs/canonical/AUTHORITY.md`
  - `docs/canonical/INDEX.md`
  - `docs/AI_CONTEXT_CURRENT.md`
  - `docs/GPT_SNAPSHOT.md`

---

## Context

CODE-A1 created an evidence-based active-code-path and legacy-residue inventory.

That audit found that `scanner/pipeline/` is not safely classifiable as a single category:

- it is self-labeled or context-labeled as legacy/reference-only in current authority helpers,
- it is not the active Daily/Intraday Independence runtime architecture,
- but parts of it remain reachable through active or executable tool, evaluation, backfill, test, and utility paths.

This creates a boundary problem before DOC-D / current-state documentation work can continue.

DOC-D must not accidentally document old scanner scoring, ranking, output, or legacy pipeline semantics as current Independence runtime behavior. At the same time, DOC-D must not falsely claim that all `scanner/pipeline/` code is dead if active tools still depend on it.

CODE-A2 must therefore turn the CODE-A1 evidence into a focused boundary review and a decision matrix that Martin can use to choose follow-up actions.

This ticket does not implement those follow-up actions.

---

## Authority and reference hierarchy

Use the current repository authority model.

Primary references:

1. `docs/canonical/AUTHORITY.md`
2. `docs/canonical/INDEX.md`
3. `docs/AI_CONTEXT_CURRENT.md`
4. `docs/GPT_SNAPSHOT.md`
5. `docs/audit/active_code_path_inventory_v0.md`
6. Current repository code, tests, workflows, scripts, artifacts, schemas, reports, manifests, and evaluation outputs
7. v2.1 section files and `independence_release_gesamtkonzept_final.md` as build-spec / design-intent sources where not contradicted by current repository reality

Mandatory interpretation rule:

> Current repository reality is the primary anchor for implemented behavior, but code that exists in the repository is not automatically active current scanner behavior. Active status must be supported by entry-point, import, call, workflow, script, test, or artifact evidence.

Mandatory boundary rule:

> `scanner/pipeline/` must not be treated as either fully active or fully dead. CODE-A2 must classify each conflict area by evidence and present explicit options for Martin.

Mandatory conflict rule:

> If current code, tests, workflows, artifacts, validated current-state documentation, AI context helpers, generated code maps, and build-spec intent conflict, do not silently choose one source. Surface the conflict explicitly in the audit and decision matrix.

---

## Goal

Create:

```text
docs/audit/legacy_pipeline_boundary_review_v0.md
```

The document must:

1. Review the CODE-A1 findings for legacy pipeline boundary conflicts.
2. Analyze the four mandatory conflict areas listed below.
3. Produce a decision matrix for each conflict area.
4. Present options such as canonicalize, isolate, extract, keep as compatibility-only, deprecate/remove later, or needs Martin decision.
5. Identify what blocks DOC-D and what does not.
6. Recommend follow-up tickets without implementing them.

This must be a decision-preparation artifact, not a second broad inventory.

---

## Mandatory conflict areas

CODE-A2 must analyze exactly these four conflict areas at minimum:

### 1. Active execution dependency into legacy-labeled namespace

```text
scanner/execution/grading.py
-> scanner.pipeline.liquidity.compute_tradeability_metrics
```

Questions to answer:

- Is this dependency current active runtime behavior?
- Is `scanner.pipeline.liquidity` merely misplaced active utility code?
- Should the dependency be canonicalized, extracted, or isolated?
- Can DOC-D document execution grading while this dependency remains unresolved?
- Which follow-up ticket would be required?

### 2. Active evaluation export dependency on legacy ranking/backtest helpers

```text
scanner/tools/export_evaluation_dataset.py
-> scanner.pipeline.global_ranking.compute_global_top20
-> scanner.backtest.e2_model
```

Questions to answer:

- Is this current evaluation architecture or retained legacy evaluation tooling?
- Is `compute_global_top20` still a valid evaluation helper, or only legacy compatibility?
- Is `scanner.backtest.e2_model` current evaluation infrastructure, legacy naming, or ambiguous?
- Can DOC-D document evaluation/replay while this dependency remains unresolved?
- Which follow-up ticket would be required?

### 3. Executable backfill path reaches legacy pipeline scoring

```text
scanner/tools/backfill_snapshots.py --mode full
-> _run_full_mode
-> scanner.pipeline.run_pipeline
-> scanner.pipeline.scoring/*
```

Questions to answer:

- Is this path still intended to be executable?
- Is it compatibility/backfill-only, historical, or operationally relevant?
- Should this path be isolated, documented as legacy compatibility, removed later, or retained?
- Can DOC-D ignore this path when documenting active Daily/Intraday runtime?
- Which follow-up ticket would be required?

### 4. Old mode names still accepted by active scanner dispatch

```text
scanner/main.py
modes: standard, fast, offline, backtest
```

Questions to answer:

- Are these active runtime modes, compatibility aliases, legacy leftovers, or ambiguous?
- Do these modes change behavior, or do they route to the same active Daily runner?
- Should current-state docs mention them as compatibility aliases, deprecated accepted values, or not mention them?
- Should a future code ticket remove, rename, or explicitly normalize them?
- Which follow-up ticket would be required?

---

## Scope

### In scope

- Read and use `docs/audit/active_code_path_inventory_v0.md`.
- Inspect the current code for the four mandatory conflict areas.
- Verify call paths with direct source references.
- Check relevant tests and workflows only where they clarify boundary status.
- Produce `docs/audit/legacy_pipeline_boundary_review_v0.md`.
- Provide a decision matrix for each conflict area.
- Provide a recommendation table with follow-up ticket suggestions.
- Identify whether each conflict blocks DOC-D fully, partially, or not at all.
- Keep recommendations non-binding until Martin decides.

### Out of scope

Do not:

- change scanner code,
- change tests,
- change schemas,
- change workflows,
- change runtime behavior,
- rename modules,
- move modules,
- delete modules,
- add deprecation markers to code,
- update `docs/canonical/AUTHORITY.md`,
- update `docs/canonical/INDEX.md`,
- update current-state canonical domain docs,
- update `docs/AI_CONTEXT_CURRENT.md`,
- update `docs/GPT_SNAPSHOT.md`,
- update `docs/code_map.md`,
- implement any cleanup option,
- decide on behalf of Martin.

---

## Required output file

Create:

```text
docs/audit/legacy_pipeline_boundary_review_v0.md
```

No JSON output is required.

---

## Required document structure

The Markdown file must contain these sections:

```text
# Legacy Pipeline Boundary Review & Decision Matrix v0

## 1. Executive summary
## 2. Authority and evidence rules used
## 3. CODE-A1 findings used as input
## 4. Conflict area A — execution grading uses pipeline liquidity
## 5. Conflict area B — evaluation export uses pipeline global ranking and backtest helper
## 6. Conflict area C — full snapshot backfill reaches legacy pipeline scoring
## 7. Conflict area D — old mode names accepted by active scanner dispatch
## 8. Cross-conflict boundary model
## 9. Decision matrices
## 10. Recommended follow-up ticket map
## 11. DOC-D unblock assessment
## 12. Martin decision checklist
## 13. No action taken confirmation
```

---

## Decision option taxonomy

Use exactly these decision option values:

```text
canonicalize_current_dependency
isolate_legacy_dependency
extract_active_utility
deprecate_or_remove_later
keep_as_compatibility_only
needs_martin_decision
```

Definitions:

### `canonicalize_current_dependency`

Use when the current dependency should remain part of active current-state architecture and be documented as such.

This option implies a future documentation update, not a CODE-A2 code change.

### `isolate_legacy_dependency`

Use when the dependency remains reachable for now, but should be clearly isolated or marked so future agents do not treat the whole legacy namespace as current architecture.

This option implies a future isolation/labeling/documentation ticket, not a CODE-A2 code change.

### `extract_active_utility`

Use when a specific useful function currently lives under `scanner/pipeline/` but should probably move into an active module family such as `scanner/execution/`, `scanner/evaluation/`, or `scanner/utils/`.

This option implies a future code refactor ticket, not a CODE-A2 code change.

### `deprecate_or_remove_later`

Use when evidence suggests the path should eventually be removed or disabled, but removal is outside CODE-A2 and must be separately approved.

This option implies a future cleanup ticket.

### `keep_as_compatibility_only`

Use when the path should remain executable only for compatibility, replay, backfill, migration, or historical reproduction purposes, and must not be treated as active Daily/Intraday architecture.

This option implies a future documentation or boundary-marker ticket.

### `needs_martin_decision`

Use when Codex cannot safely recommend one of the other options without Martin’s product/architecture decision.

This option must include the exact decision question for Martin.

---

## Required decision matrix format

For each mandatory conflict area, include a table with at least these columns:

```text
Option
What it would mean
Evidence supporting it
Evidence against it / risk
Impact on DOC-D
Follow-up ticket required?
Recommended? yes/no/conditional
```

Then include a short recommendation block:

```text
Recommended option:
Reason:
Required follow-up ticket:
DOC-D status:
Martin decision required:
```

Rules:

- Codex may recommend an option, but must not implement it.
- If the recommendation depends on product/architecture intent, mark `Martin decision required: yes`.
- Do not present a recommendation as already approved.
- Do not collapse multiple conflict areas into one recommendation unless evidence clearly supports the same path.

---

## Required recommendation table

The document must include a final consolidated table:

```text
conflict_area
current_evidence
risk_level: high | medium | low
available_options
recommended_option
why
required_follow_up_ticket
blocks_DOC_D: yes | no | partial
martin_decision_required: yes | no
```

Use this table to make CODE-A2 actionable.

---

## Evidence requirements

For each conflict area, document:

```text
source files inspected
functions/classes inspected
tests inspected, if relevant
workflows inspected, if relevant
call path evidence
artifact path evidence, if relevant
authority conflict, if any
```

Minimum source files to inspect:

```text
docs/audit/active_code_path_inventory_v0.md
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
scanner/execution/grading.py
scanner/pipeline/liquidity.py
scanner/tools/export_evaluation_dataset.py
scanner/pipeline/global_ranking.py
scanner/backtest/e2_model.py
scanner/tools/backfill_snapshots.py
scanner/pipeline/__init__.py
scanner/pipeline/scoring/
scanner/main.py
scanner/config.py
scanner/runners/daily.py
```

Inspect relevant tests and workflows where they clarify the boundary. Do not perform a broad second repository inventory.

---

## Required boundary model

CODE-A2 must propose a cross-conflict boundary model with these categories:

```text
active_independence_runtime
active_independence_evaluation
active_analysis_or_backfill_compatibility
active_utility_misplaced_under_legacy_namespace
legacy_test_only
legacy_reference_only
ambiguous_requires_decision
```

For each category, define:

- what it means,
- whether DOC-D may use it as current-state documentation evidence,
- whether future Codex tickets may edit it for runtime changes,
- whether it requires Martin decision before cleanup.

This boundary model is a proposal only until Martin approves it.

---

## DOC-D unblock assessment

The audit must explicitly state whether DOC-D may proceed:

- fully,
- partially,
- or not yet.

Use this required table:

```text
DOC-D area
Can proceed? yes/no/partial
Conditions
Relevant conflict areas
Notes
```

At minimum, include:

```text
Architecture overview
Runtime entry points
Daily runner
Intraday runner
Execution/tradeability
Evaluation/replay
Analysis/backfill tools
Output/report paths
Legacy/reference-only section
```

---

## Martin decision checklist

The final artifact must include a checklist Martin can use after CODE-A2:

```text
## 12. Martin decision checklist

- [ ] Decide whether `scanner.pipeline.liquidity` should be canonicalized as active utility or extracted from `scanner/pipeline/`.
- [ ] Decide whether `scanner.pipeline.global_ranking` remains active evaluation support or compatibility-only.
- [ ] Decide whether `scanner.backtest.e2_model` should be treated as active evaluation infrastructure despite its package name.
- [ ] Decide whether `backfill_snapshots.py --mode full` should remain executable as compatibility/backfill-only.
- [ ] Decide whether legacy pipeline scoring should be isolated, deprecated, or retained for historical reproduction.
- [ ] Decide whether `standard`, `fast`, `offline`, and `backtest` remain accepted compatibility aliases or should be removed/renamed later.
- [ ] Decide which DOC-D sections may proceed before cleanup.
```

---

## No-action confirmation

The final section must include this exact checklist and mark each item as confirmed:

```text
## 13. No action taken confirmation

- [ ] No scanner code changed.
- [ ] No tests changed.
- [ ] No schemas changed.
- [ ] No workflows changed.
- [ ] No runtime behavior changed.
- [ ] No files moved.
- [ ] No files deleted.
- [ ] No deprecation markers added.
- [ ] No current-state canonical domain documentation updated.
- [ ] Only the CODE-A2 audit/decision-preparation artifact was added.
```

If any item cannot be checked, stop and report the issue instead of completing the ticket.

---

## Documentation impact

This ticket intentionally creates an audit/decision-preparation artifact, but it is not current-state canonical domain documentation.

Required documentation impact outcome:

- Add only:
  - `docs/audit/legacy_pipeline_boundary_review_v0.md`

Do not update:

- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/REPORTS.md`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/AI_CONTEXT_CURRENT.md`
- `docs/GPT_SNAPSHOT.md`
- `docs/code_map.md`

The output file is evidence and decision support for later documentation and cleanup work. It is not itself a replacement for validated current-state canonical documentation.

---

## Codex guardrails

- Audit and decision-preparation only.
- No behavior changes.
- No code changes.
- No test changes.
- No schema changes.
- No workflow changes.
- No cleanup decisions.
- No cleanup implementation.
- Do not infer active status from file existence.
- Do not infer inactive status from legacy-labeled namespace alone.
- Do not infer that all `scanner/pipeline/` files share one classification.
- Use the exact decision option taxonomy from this ticket.
- Keep recommendations non-binding until Martin decides.
- Surface authority conflicts explicitly.
- If evidence is insufficient, use `needs_martin_decision`.
- If a path is active only through a tool/backfill/evaluation script, do not describe it as active Daily/Intraday runtime architecture.
- If a path is active runtime but located under `scanner/pipeline/`, treat that as a boundary conflict, not as proof that the whole pipeline is current architecture.

---

## Suggested implementation approach

Codex may use commands such as:

```bash
grep -R "compute_tradeability_metrics" -n scanner tests scripts .github docs || true
grep -R "compute_global_top20" -n scanner tests scripts .github docs || true
grep -R "evaluate_e2_candidate\\|scanner.backtest.e2_model" -n scanner tests scripts .github docs || true
grep -R "_run_full_mode\\|run_pipeline\\|scanner.pipeline.scoring" -n scanner tests scripts .github docs || true
grep -R "standard\\|fast\\|offline\\|backtest" -n scanner/main.py scanner/config.py tests docs .github scripts || true
```

Also inspect the relevant files manually. Do not rely only on grep.

---

## Acceptance criteria

CODE-A2 is complete when:

1. `docs/audit/legacy_pipeline_boundary_review_v0.md` exists.
2. All required sections are present.
3. All four mandatory conflict areas are analyzed.
4. Each conflict area includes source evidence.
5. Each conflict area includes a decision matrix.
6. Each conflict area includes a recommended option or `needs_martin_decision`; if `needs_martin_decision` is used, the exact decision question for Martin must be included.
7. The consolidated recommendation table is present.
8. The proposed boundary model is present.
9. The DOC-D unblock assessment is present.
10. The Martin decision checklist is present.
11. The no-action confirmation checklist is present and fully checked.
12. No files other than `docs/audit/legacy_pipeline_boundary_review_v0.md` were changed.

---

## Validation / checks

Because this is an audit/decision-preparation artifact only:

- Do not modify tests.
- Do not modify code.
- Running the full test suite is optional, not required.
- If tests are run, report the command and result.
- At minimum, run:

```bash
git diff --stat
git diff --name-only
```

Confirm that only:

```text
docs/audit/legacy_pipeline_boundary_review_v0.md
```

changed.

---

## Definition of Done

- CODE-A2 output exists at `docs/audit/legacy_pipeline_boundary_review_v0.md`.
- The artifact turns CODE-A1 evidence into an actionable boundary review and decision matrix.
- The artifact makes clear which decisions Martin must make before DOC-D.
- The artifact makes clear which DOC-D sections can proceed, partially proceed, or must wait.
- No cleanup decisions are implemented.
- No current-state canonical documentation is changed.
