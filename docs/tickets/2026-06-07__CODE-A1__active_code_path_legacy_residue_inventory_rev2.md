# CODE-A1: Active Code Path & Legacy Residue Inventory

## Metadata

- Ticket ID: CODE-A1
- Title: Active Code Path & Legacy Residue Inventory
- Status: Draft — Codex-ready after Martin approval
- Priority: P0 / P1 audit prerequisite
- Type: Audit-only / evidence collection
- Language: Implementation and audit artifact in English
- Primary output: `docs/audit/active_code_path_inventory_v0.md`
- Optional output: `docs/audit/active_code_path_inventory_v0.json`
- Scope type: Repository audit, no behavior change
- Blocks: DOC-D / current-state documentation updates until reviewed
- Related previous work:
  - DOC-A: neutral documentation inventory
  - DOC-B: consolidated `docs/canonical/AUTHORITY.md`
  - DOC-C: documentation-impact workflow integration

---

## Context

The Independence / Spot-Altcoin-Scanner repository was rebuilt around the v2.1 Independence Release architecture.

However, not every file in the repository is automatically part of the active current scanner. Some code was newly implemented, some was refactored, and some legacy modules may remain for reference, compatibility, tests, analysis, or historical reasons.

Before updating current-state canonical documentation such as `DATA_MODEL.md`, `REPORTS.md`, `ARCHITECTURE.md`, or `RUNTIME_AND_OPERATIONS.md`, the repository needs an evidence-based inventory of:

- actual runtime entry points,
- active daily / intraday scanner call paths,
- active evaluation / replay call paths,
- active scripts and utilities,
- test-only legacy usage,
- unused or unclear legacy residue,
- artifact and output write paths.

This ticket creates an audit artifact only. It must not change code, tests, schemas, runtime behavior, or current-state domain documentation.

---

## Authority and reference hierarchy

Use the current repository authority model.

Primary references:

1. `docs/canonical/AUTHORITY.md`
2. `docs/canonical/INDEX.md`
3. `docs/AI_CONTEXT_CURRENT.md`
4. `docs/GPT_SNAPSHOT.md`
5. `docs/code_map.md` as generated navigation only
6. Current repository code, tests, schemas, GitHub Actions workflows, current reports, manifests, diagnostics, and evaluation outputs
7. v2.1 section files and `independence_release_gesamtkonzept_final.md` as build-spec / design-intent sources where not contradicted by current repository reality

Mandatory interpretation rule:

> Current repository reality is the primary anchor for implemented behavior, but code that exists in the repository is not automatically active current scanner behavior. Active status must be supported by entry-point, import, call, test, workflow, or artifact-path evidence.

Mandatory conflict rule:

> If current code, tests, workflows, artifacts, validated current-state documentation, AI context helpers, generated code maps, and build-spec intent conflict, do not silently choose one source. Surface the conflict explicitly in the audit.

Generated navigation rule:

> `docs/code_map.md` may be used as a search/navigation aid only. It is not architecture authority and must not be used by itself as evidence that a file is active current architecture.

---

## Goal

Create an evidence-based inventory at:

```text
docs/audit/active_code_path_inventory_v0.md
```

The audit must classify repository code paths and modules into active, utility, evaluation, legacy, test-only, unused, or ambiguous categories.

The audit must make it safe to decide later whether legacy-looking code should be documented, isolated, marked reference-only, deleted, or left untouched.

This ticket does not make any of those follow-up decisions.

---

## Scope

### In scope

Audit and document:

1. Runtime entry points
   - GitHub Actions workflows
   - `scanner/main.py`
   - Daily Discovery runner
   - Intraday Promotion runner
   - CLI/script entry points

2. Active call paths
   - Daily runtime path
   - Intraday runtime path
   - Evaluation/replay path
   - Analysis/script path
   - Utility-only path

3. Module classification
   - classify modules and relevant files into the taxonomy defined below

4. Legacy-residue investigation
   - inspect legacy-looking paths and symbols
   - determine whether they are active, test-only, script-only, unused, or ambiguous

5. Test semantics inventory
   - classify tests according to whether they guard current semantics, legacy semantics, compatibility, schema behavior, utilities, or ambiguous behavior

6. Output and artifact write paths
   - identify current, allowed, deprecated, potentially stale, or ambiguous artifact paths

7. Risk summary
   - active legacy path risk
   - test-only legacy risk
   - AI/Codex confusion risk
   - documentation contamination risk
   - artifact-path drift risk

8. No-action confirmation
   - explicitly document that CODE-A1 made no code, test, schema, behavior, or canonical documentation changes outside the audit artifact

### Out of scope

Do not:

- change scanner code,
- change tests,
- change schemas,
- change GitHub Actions workflows,
- change runtime behavior,
- rename files,
- move files,
- delete files,
- add deprecation markers to code,
- update current-state canonical domain documentation,
- update `DATA_MODEL.md`,
- update `REPORTS.md`,
- update `ARCHITECTURE.md`,
- update `RUNTIME_AND_OPERATIONS.md`,
- update `AUTHORITY.md`,
- update `INDEX.md`,
- decide whether a legacy file should be removed,
- decide whether tests should be rewritten,
- decide whether old modes should be removed from `scanner/main.py`.

---

## Required output file

Create:

```text
docs/audit/active_code_path_inventory_v0.md
```

Optional, only if useful and low overhead:

```text
docs/audit/active_code_path_inventory_v0.json
```

If the JSON file is created, the Markdown file remains the authoritative audit artifact for human review.

---

## Required audit document structure

The Markdown audit file must contain these sections:

```text
# Active Code Path & Legacy Residue Inventory v0

## 1. Executive summary
## 2. Authority and evidence rules used
## 3. Runtime entry points
## 4. GitHub Actions / workflow entry points
## 5. CLI and script entry points
## 6. Daily runtime call path
## 7. Intraday runtime call path
## 8. Evaluation / replay call paths
## 9. Output and artifact write paths
## 10. Module classification table
## 11. Legacy-residue candidates
## 12. Test semantics inventory
## 13. Artifact path classification
## 14. Ambiguous / unresolved cases
## 15. Risk summary
## 16. No action taken confirmation
```

---

## Classification taxonomy

Use exactly these module classifications:

```text
active_runtime
active_evaluation
active_analysis_script
active_utility
legacy_residue_unused
legacy_residue_test_only
ambiguous
```

Definitions:

### `active_runtime`

A module or file is `active_runtime` only if it is invoked by or directly participates in an active scanner runtime path, such as Daily Discovery, Intraday Promotion, report/diagnostics generation, execution evaluation, state persistence, or runtime output writing.

### `active_evaluation`

A module or file is `active_evaluation` only if it is invoked by current evaluation, replay, forward-return, dataset export, or calibration entry points that are part of the current Independence evaluation architecture.

### `active_analysis_script`

A module or file is `active_analysis_script` if it is used by currently executable analysis or helper scripts but is not part of daily/intraday runtime and is not a core evaluation/replay module.

### `active_utility`

A module or file is `active_utility` if it is shared infrastructure used by active runtime, evaluation, or script paths, but does not itself own scanner domain behavior.

### `legacy_residue_unused`

A module or file is `legacy_residue_unused` only if no runtime, evaluation, script, workflow, test, or utility usage is found within the audit search strategy.

Do not assign this classification solely because the file looks old.

### `legacy_residue_test_only`

A module or file is `legacy_residue_test_only` only if evidence shows it is used by tests but no active runtime, evaluation, script, workflow, or utility path uses it.

### `ambiguous`

A module or file is `ambiguous` if evidence is insufficient, conflicting, too indirect, or outside the defined call-depth limit.

When in doubt, use `ambiguous`.

---

## Evidence strength criteria

For every relevant module/file row, include:

```text
evidence_strength: strong | medium | weak | none
```

Use these criteria exactly:

### `strong`

Use `strong` only if at least one applies:

- direct invocation from a runtime, evaluation, workflow, or script entry point,
- direct call chain from such an entry point within the configured call-depth limit,
- direct artifact write/read path used by an active runner or evaluation entry point,
- direct import and direct call by an active runtime/evaluation/script module within the call-depth limit.

### `medium`

Use `medium` only if at least one applies:

- imported by an active module but no direct call observed within the call-depth limit,
- used by a currently executable script/tool but not by Daily/Intraday runtime,
- referenced by active tests that appear to guard current schema/runtime behavior,
- referenced in a config path used by active runtime but without direct code invocation evidence.

### `weak`

Use `weak` only if at least one applies:

- referenced only in tests,
- referenced only in generated navigation,
- referenced only in comments,
- referenced only in stale docs,
- referenced only in historical scripts,
- no active runtime/evaluation/script call evidence was found.

### `none`

Use `none` when no import, call, reference, workflow, test, script, artifact, or config evidence is found except the file’s own existence.

---

## Audit follow-up hints

For every relevant module/file row, include:

```text
audit_follow_up_hint
```

Allowed values:

```text
none
investigate
clarify_authority_conflict
candidate_for_future_legacy_isolation_review
candidate_for_future_test_semantics_review
candidate_for_future_artifact_path_review
```

Rules:

- These hints are non-binding audit follow-up hints only.
- CODE-A1 must not mark files for deletion, removal, relocation, or deprecation as an implementation decision.
- Do not use `audit_follow_up_hint` to imply approval for cleanup.
- Use `none` if no follow-up concern is visible.
- Use `investigate` if evidence is incomplete or conflicting.
- Use `clarify_authority_conflict` if current code, docs, tests, or artifacts disagree.
- Use `candidate_for_future_legacy_isolation_review` if a module appears legacy-like and is not active runtime/evaluation/script code.
- Use `candidate_for_future_test_semantics_review` if tests appear to preserve legacy business semantics.
- Use `candidate_for_future_artifact_path_review` if artifact paths appear stale or deprecated.

---

## Call-path tracing depth

For each entry point, document call paths to this depth:

```text
Level 0: entry point file/function/workflow step.
Level 1: directly invoked functions/modules.
Level 2: direct imports and directly invoked modules/functions from Level 1.
```

Rules:

- Do not recursively expand beyond Level 2 in the main table.
- For deeper dependencies, summarize by module family, for example:
  - `scanner/axes/`
  - `scanner/state/`
  - `scanner/output/`
  - `scanner/execution/`
- If a legacy-looking module appears within Level 0–2, document it explicitly.
- If a legacy-looking module appears only deeper than Level 2 or only through generated navigation, mark it as `ambiguous` unless additional direct evidence is found.
- Distinguish imports from actual calls.
- A module import alone is not proof that business logic is executed.
- A test import alone is not proof of runtime activity.

---

## Mandatory entry point search

Inspect at minimum:

```text
.github/workflows/**
scanner/main.py
scanner/runners/**
scanner/tools/**
scripts/**
scanner/evaluation/**
scanner/backtest/**
scanner/output/**
scanner/storage/**
scanner/data/**
```

If a directory does not exist, record that in the audit.

For workflows, identify:

- scheduled workflows,
- manually triggered workflows,
- analysis-script workflows,
- Shadow-Live workflows,
- persistence workflows,
- validation/test workflows.

For each workflow, document:

```text
workflow_file
trigger
commands
called Python modules/scripts
artifact inputs
artifact outputs
classification
evidence_strength
```

---

## Legacy-residue search index

Inspect these paths and symbols explicitly.

Paths:

```text
scanner/pipeline/
scanner/pipeline/decision.py
scanner/pipeline/global_ranking.py
scanner/pipeline/scoring/
scanner/pipeline/output.py
scanner/pipeline/features.py
scanner/backtest/
scanner/tools/export_evaluation_dataset.py
scanner/tools/backfill_btc_regime.py
scanner/tools/backfill_snapshots.py
```

Symbols / strings:

```text
global_score
GLOBAL_RANKING_TOP20
base_score
multiplier
btc_regime
fast
standard
offline
backtest
reports/analysis
reports/YYYY-MM-DD.md
run.manifest.json under reports/
scanner.pipeline
pipeline.decision
pipeline.global_ranking
pipeline.scoring
compute_global_top20
legacy
shadow_mode
entry_ready
ENTER
WAIT
NO_TRADE
```

Important search-context notes:

- `entry_ready`, `ENTER`, `WAIT`, and `NO_TRADE` are not legacy indicators by themselves. They may appear in active or historically valid scanner contexts. Finding these strings is not a legacy signal unless the surrounding call path proves old decision/scoring/output semantics.
- `shadow_mode` is not a legacy indicator by itself. Shadow-Live is an active operational context. Treat `shadow_mode` findings as context-dependent and classify by actual call path, workflow usage, and authority evidence.
- `btc_regime` is context-dependent. It may appear in legacy scoring context, such as BTC-regime multiplier logic, and it may also appear in current or retained backtest/evaluation infrastructure. Distinguish by call context and do not classify it as legacy without surrounding evidence.

Rules:

- This list is a search index only.
- Do not treat a path or symbol as confirmed legacy merely because it appears in this list.
- Confirm status only from evidence.
- If evidence is conflicting, classify as `ambiguous`.

---

## Test semantics inventory

Inspect tests for current-vs-legacy semantics.

Use the following test classifications:

```text
current_semantics_test
legacy_semantics_test
compatibility_test
schema_guard_test
utility_test
ambiguous_test
```

Definitions:

### `current_semantics_test`

A test that guards current Independence Release behavior, schema, runtime path, diagnostics contract, artifact path, or active evaluation behavior.

### `legacy_semantics_test`

A test that appears to guard old scanner business logic, old scoring/ranking/output semantics, old modes, or previous-scanner behavior not currently active.

### `compatibility_test`

A test that intentionally preserves backward compatibility, migration behavior, or legacy input tolerance without making that behavior active current semantics.

### `schema_guard_test`

A test that guards current schema validation, diagnostics shape, report shape, manifest shape, or artifact serialization.

### `utility_test`

A test for shared utilities, parsing, time helpers, IO helpers, config validation, numerical helpers, or other domain-neutral functions.

### `ambiguous_test`

A test whose semantic role cannot be determined from file name, assertions, imports, and local context.

Mandatory test search anchors:

```text
global_score
GLOBAL_RANKING_TOP20
base_score
multiplier
btc_regime
fast
standard
offline
backtest
reports/analysis
reports/YYYY-MM-DD.md
run.manifest.json under reports/
scanner.pipeline
pipeline.decision
pipeline.global_ranking
pipeline.scoring
compute_global_top20
legacy
shadow_mode
entry_ready
ENTER
WAIT
NO_TRADE
```

Important test-search-context notes:

- `entry_ready`, `ENTER`, `WAIT`, and `NO_TRADE` findings are not automatically legacy-test findings. Classify them by the surrounding assertion and the module under test.
- `shadow_mode` findings are not automatically legacy-test findings. Classify them by whether the test guards active Shadow-Live behavior, compatibility behavior, or obsolete semantics.
- `btc_regime` findings are context-dependent. Separate legacy BTC-regime multiplier scoring tests from retained/current backtest, labeling, or evaluation infrastructure tests.

For each relevant test group, document:

```text
test_file
important assertions / strings
modules under test
classification
evidence_strength
audit_follow_up_hint
notes
```

---

## Artifact path classification

Use exactly these artifact path classifications:

```text
expected_current
allowed_analysis_or_auxiliary
potentially_stale
confirmed_deprecated_by_authority
ambiguous
```

Definitions:

### `expected_current`

A path is `expected_current` if it is explicitly listed as current in `docs/AI_CONTEXT_CURRENT.md`, validated current-state docs, or current runner/output code.

Examples to verify against current code and docs:

```text
reports/runs/YYYY/MM/DD/<run_id>/
reports/daily/YYYY/MM/DD/report.json
reports/index/
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
snapshots/history/ohlcv/
```

### `allowed_analysis_or_auxiliary`

A path is `allowed_analysis_or_auxiliary` if it is explicitly allowed for scripts, analysis, or auxiliary outputs.

Examples to verify:

```text
evaluation/exports/
artifacts/
reports/aux/
```

### `confirmed_deprecated_by_authority`

A path is `confirmed_deprecated_by_authority` if it is explicitly listed as deprecated or forbidden active assumption in `docs/AI_CONTEXT_CURRENT.md`, `docs/GPT_SNAPSHOT.md`, or validated current-state canonical documentation.

Examples to verify:

```text
reports/analysis/
reports/YYYY-MM-DD.md
report-side run.manifest.json
```

### `potentially_stale`

A path is `potentially_stale` if it:

- is not listed as expected or allowed,
- resembles old output structure,
- appears only in legacy modules/tests,
- appears in comments or stale docs,
- or conflicts with the current artifact model but lacks explicit deprecation evidence.

### `ambiguous`

Use `ambiguous` if evidence is insufficient or conflicting.

For each path class, document:

```text
path_pattern
where_found
read_or_write
classification
evidence_strength
authority_reference_or_code_reference
notes
```

---

## Required module classification table format

The audit must include a table with at least these columns:

```text
Module / file
Primary role observed
Classification
Evidence strength
Evidence
Runtime path?
Evaluation path?
Script/tool path?
Test-only?
Artifact paths touched
Authority conflict?
Audit follow-up hint
Notes
```

Use concise evidence notes, but include enough detail that a reviewer can reproduce the classification.

---

## Required risk summary

Include a risk summary with these categories:

### 1. Active legacy path risk

Identify any legacy-looking modules that appear on active runtime/evaluation/script paths.

### 2. Test-only legacy risk

Identify tests that may keep legacy business semantics alive.

### 3. AI/Codex confusion risk

Identify files, names, modules, docs, or generated maps that could mislead future AI agents into editing inactive code.

### 4. Documentation contamination risk

Identify code paths that should not be used as sources for DOC-D or current-state canonical documentation without further review.

### 5. Artifact-path drift risk

Identify output/read/write paths that conflict with, resemble, or bypass the current report/snapshot/evaluation artifact model.

For each risk, include:

```text
risk_level: high | medium | low
evidence
why it matters
recommended audit follow-up hint
```

Risk levels are audit severity only. They are not permission to change code.

---

## No-action confirmation

The final section of the audit must include this exact checklist and mark each item as confirmed:

```text
## 16. No action taken confirmation

- [ ] No scanner code changed.
- [ ] No tests changed.
- [ ] No schemas changed.
- [ ] No workflows changed.
- [ ] No runtime behavior changed.
- [ ] No files moved.
- [ ] No files deleted.
- [ ] No deprecation markers added.
- [ ] No current-state canonical domain documentation updated.
- [ ] Only the audit artifact was added.
```

If any item cannot be checked, stop and report the issue instead of completing the ticket.

---

## Documentation impact

This ticket intentionally creates a documentation-like audit artifact, but it is not current-state canonical domain documentation.

Required documentation impact outcome:

- Add only:
  - `docs/audit/active_code_path_inventory_v0.md`
  - optional `docs/audit/active_code_path_inventory_v0.json`
- Do not update:
  - `docs/canonical/AUTHORITY.md`
  - `docs/canonical/INDEX.md`
  - `docs/canonical/DATA_MODEL.md`
  - `docs/canonical/REPORTS.md`
  - `docs/canonical/ARCHITECTURE.md`
  - `docs/canonical/RUNTIME_AND_OPERATIONS.md`
  - `docs/AI_CONTEXT_CURRENT.md`
  - `docs/GPT_SNAPSHOT.md`
  - `docs/code_map.md`

The audit file is evidence for later documentation work. It is not itself a replacement for validated current-state canonical documentation.

---

## Codex guardrails

- Audit only.
- No behavior changes.
- No code changes.
- No test changes.
- No schema changes.
- No workflow changes.
- No cleanup decisions.
- Do not infer active status from file existence.
- Do not infer active status from `docs/code_map.md` alone.
- Do not infer legacy status from path name alone.
- Use `ambiguous` when evidence is insufficient.
- Use the exact classification taxonomies in this ticket.
- Keep the audit readable; summarize deep dependencies by module family after Level 2.
- Surface authority conflicts explicitly.
- If the audit discovers a serious contradiction, document it; do not fix it.

---

## Suggested implementation approach

Codex may use commands such as:

```bash
find .github/workflows -type f -maxdepth 3 2>/dev/null || true
find scanner -type f -name "*.py" | sort
find scripts -type f 2>/dev/null | sort
find tests -type f 2>/dev/null | sort
grep -R "global_score\|GLOBAL_RANKING_TOP20\|base_score\|compute_global_top20" -n . || true
grep -R "fast\|standard\|offline\|backtest" -n scanner tests .github scripts docs || true
grep -R "reports/analysis\|reports/YYYY-MM-DD.md\|run.manifest.json" -n scanner tests .github scripts docs || true
grep -R "scanner.pipeline\|pipeline.decision\|pipeline.global_ranking\|pipeline.scoring" -n scanner tests scripts docs || true
```

Do not rely only on grep. Inspect the relevant files to distinguish:

- import-only references,
- actual calls,
- test-only assertions,
- comments,
- docs,
- generated navigation,
- executable scripts,
- active workflows.

---

## Acceptance criteria

CODE-A1 is complete when:

1. `docs/audit/active_code_path_inventory_v0.md` exists.
2. The audit contains all required sections.
3. Runtime entry points are identified and classified.
4. GitHub Actions/workflow entry points are identified and classified.
5. CLI/script entry points are identified and classified.
6. Daily runtime call path is documented to Level 0–2.
7. Intraday runtime call path is documented to Level 0–2.
8. Evaluation/replay call paths are documented to Level 0–2.
9. Output and artifact write paths are inventoried and classified.
10. The module classification table uses the required taxonomy.
11. Evidence strength uses the required criteria.
12. Audit follow-up hints use only the allowed values.
13. Legacy-residue candidates are documented with evidence, not assumptions.
14. Tests are classified using the required test taxonomy.
15. Mandatory test search anchors were used and their findings summarized.
16. Artifact paths are classified using the required artifact taxonomy.
17. Ambiguous cases are explicitly listed.
18. Risk summary is included.
19. No-action confirmation checklist is included and fully checked.
20. No files other than the audit artifact and optional JSON artifact were changed.

---

## Validation / checks

Because this is an audit-only documentation artifact:

- Do not modify tests.
- Do not modify code.
- Running the full test suite is optional, not required.
- If Codex runs tests, report the command and result.
- At minimum, run:

```bash
git diff --stat
git diff --name-only
```

Confirm that only allowed audit artifact files changed.

If available, also run a Markdown sanity check or inspect the rendered Markdown manually.

---

## Definition of Done

- The audit artifact exists at `docs/audit/active_code_path_inventory_v0.md`.
- Optional JSON exists only if Codex chose to create it.
- The audit is evidence-based, reviewable, and does not make cleanup decisions.
- The audit distinguishes active runtime, active evaluation, active analysis scripts, active utilities, unused legacy residue, test-only legacy residue, and ambiguous cases.
- The audit is sufficient for Martin, ChatGPT, Claude, and Codex to decide follow-up tickets before DOC-D resumes.
- No current-state canonical documentation updates are made in this ticket.
