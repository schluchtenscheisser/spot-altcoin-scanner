# DOC-B: Documentation Authority Consolidation

## Metadata

- Ticket ID: DOC-B
- Title: Documentation Authority Consolidation — Current-State Authority Baseline
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Documentation authority/process consolidation only
- Primary files:
  - `docs/canonical/AUTHORITY.md`
  - `docs/canonical/INDEX.md`
  - `docs/canonical/WORKFLOW_CODEX.md`
  - `docs/AGENTS.md`
  - `docs/dev_workflow.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Predecessor: DOC-A — `docs/audit/documentation_inventory_v0.md`

---

## 1. Context

DOC-A created a neutral documentation inventory under:

```text
docs/audit/documentation_inventory_v0.md
```

That inventory records that the repository documentation is currently a mixed documentation corpus consisting of previous-scanner documentation, v2.1 transformation / build-spec documentation, partially updated current-state documentation, AI/context helper documents, schema/change logs, generated navigation, and process/ticket helper documentation.

DOC-A intentionally did not resolve any authority conflicts. This ticket is the follow-up authority consolidation ticket.

The goal is to make the documentation authority model explicit, consistent, and safe for future Codex work.

---

## 2. Problem

The repository currently contains multiple authority/precedence signals that are not fully aligned.

Key observed problems:

1. `docs/canonical/AUTHORITY.md` currently reflects older precedence logic where the v2.1 build-spec / Gesamtkonzept sit ahead of `docs/canonical/*`.
2. `docs/canonical/WORKFLOW_CODEX.md` and `docs/AI_CONTEXT_CURRENT.md` reflect a newer repo-reality-first hierarchy.
3. `docs/canonical/INDEX.md` classifies multiple files/folders as `legacy_reference_only`, while some files inside those folders still declare `status: canonical`.
4. `docs/dev_workflow.md` contains older process wording, including the idea that `docs/code_map.md` becomes a single source of truth for repository structure.
5. `docs/SCHEMA_CHANGES.md` is currently a strong evidence source for schema/output changes, but it is not a full current-state data model or report specification.

These conflicts create a practical Codex safety risk: future implementation tickets may accidentally treat previous-scanner documentation or stale `status: canonical` headers as active current-state authority.

---

## 3. Goal

Consolidate the repository documentation authority model without updating scanner domain content.

After this ticket:

1. `docs/canonical/AUTHORITY.md` is the central documentation authority/precedence file.
2. No root-level `docs/AUTHORITY.md` exists or is introduced.
3. Current code, tests, schemas, workflows, and current run artifacts are the primary anchor for current-state documentation.
4. v2.1 section files and `independence_release_gesamtkonzept_final.md` are classified as build-spec / design-intent authority, not as complete current-state documentation.
5. Previous-scanner documentation remains reference-only unless explicitly revalidated.
6. `docs/canonical/INDEX.md` remains the role/navigation index.
7. If `docs/canonical/INDEX.md` classifies a file or folder as `legacy_reference_only`, that classification takes precedence over stale in-file `status: canonical` headers until a dedicated revalidation/reclassification ticket changes it.
8. `docs/dev_workflow.md` is clearly superseded by `docs/canonical/WORKFLOW_CODEX.md`.
9. AI context documents are classified as routing/context helpers, not as technical current-state authority.

---

## 4. Scope

Codex may modify only these files:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/canonical/WORKFLOW_CODEX.md
docs/AGENTS.md
docs/dev_workflow.md
```

Changes must be documentation-only and limited to authority, precedence, roles, navigation, and supersession wording.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/AI_CONTEXT_CURRENT.md
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/TEST_STRATEGY.md
docs/canonical/GLOSSARY.md
docs/canonical/open_questions.md
docs/canonical/feature_enhancements.md
docs/SCHEMA_CHANGES.md
docs/tickets/_TEMPLATE.md
docs/audit/documentation_inventory_v0.md
README.md
```

Codex must not modify:

- any code file,
- any test file,
- any schema file,
- any CI/workflow file,
- any runtime behavior,
- any generated artifact,
- any previous-scanner documentation file outside the explicitly allowed files.

Codex must not:

- create `docs/AUTHORITY.md`,
- move files,
- delete files,
- archive files,
- reclassify individual legacy-reference files as current-state documentation,
- update scanner domain content,
- update report/data model content,
- update schema semantics,
- update implementation status statements in `docs/AI_CONTEXT_CURRENT.md`.

---

## 6. Required authority model

### 6.1 Central authority file

`docs/canonical/AUTHORITY.md` must become the central documentation authority/precedence file.

It must explicitly state:

```text
This repository uses docs/canonical/AUTHORITY.md as the central documentation authority and precedence file. No separate root-level docs/AUTHORITY.md is used.
```

### 6.2 Current-state primary anchor

`docs/canonical/AUTHORITY.md` must state that current-state documentation is anchored primarily in current repository reality.

Required rule, semantically unchanged:

```text
For current implemented scanner behavior, the primary anchor is current repository reality: current code, tests, schemas, GitHub Actions workflows, current run artifacts, diagnostics, manifests, reports, and evaluation outputs.
```

It must also state that current-state documentation should describe implemented behavior, not merely historical intent or previous-scanner design.

### 6.3 Build-spec / design-intent classification

`docs/canonical/AUTHORITY.md` must classify the v2.1 section files and `independence_release_gesamtkonzept_final.md` as build-spec / design-intent authority.

Required rule, semantically unchanged:

```text
The v2.1 section files and independence_release_gesamtkonzept_final.md are build-spec / design-intent authority for the Independence transformation. They are not ordinary previous-scanner legacy documentation, but they are also not complete current-state documentation after implementation.
```

The file must state that these build-spec documents remain useful for domain intent, unresolved design questions, explaining why the current implementation exists, and identifying spec-vs-implementation gaps.

They must not silently override current code/tests/schemas/current artifacts for implemented behavior.

### 6.4 Current-state canonical documentation

`docs/canonical/AUTHORITY.md` must define current-state canonical documentation as documentation that has been validated against implemented repository reality and is intended to describe the current scanner.

It must make clear that not every file under `docs/canonical/` is automatically current-state authority.

Required rule, semantically unchanged:

```text
A file path under docs/canonical/ does not by itself make a document current-state authority. The document role in docs/canonical/INDEX.md and the current authority model determine how it may be used.
```

### 6.5 `INDEX.md` role precedence rule

This is mandatory.

`docs/canonical/AUTHORITY.md` must include this rule, semantically unchanged:

```text
Where docs/canonical/INDEX.md classifies a file or folder as legacy_reference_only, that classification takes precedence over any status: canonical declaration in the file header, until the file has been explicitly revalidated and reclassified in a dedicated ticket.
```

This rule must be presented as binding, not optional guidance.

### 6.6 Previous-scanner reference classification

`docs/canonical/AUTHORITY.md` must define previous-scanner documentation as reference-only unless explicitly revalidated.

Required rule, semantically unchanged:

```text
Previous-scanner documentation may be useful as historical reference or migration context, but it must not be used as active current-state authority unless a dedicated ticket revalidates and reclassifies it.
```

### 6.7 Tracking and evidence documents

`docs/canonical/AUTHORITY.md` must classify tracking/evidence documents such as `docs/SCHEMA_CHANGES.md`, `docs/canonical/open_questions.md`, and `docs/canonical/feature_enhancements.md`.

Required treatment:

- `docs/SCHEMA_CHANGES.md` is a schema/output change evidence log.
- It is a strong evidence source for later `DATA_MODEL.md`, `REPORTS.md`, and `SNAPSHOTS.md` updates.
- It is not a complete current-state data model or report specification.
- `open_questions.md` and `feature_enhancements.md` are active planning/tracking documents, not previous-scanner legacy docs.

### 6.8 AI context helpers

`docs/canonical/AUTHORITY.md` must classify AI context documents as routing/context helpers.

Examples:

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
docs/AGENTS.md
```

Required rule, semantically unchanged:

```text
AI context documents are routing and context helpers. They do not override current repository reality or validated current-state canonical documentation.
```

Important: `docs/AI_CONTEXT_CURRENT.md` must not be modified by this ticket.

### 6.9 Generated navigation

`docs/canonical/AUTHORITY.md` must classify `docs/code_map.md` as generated navigation only.

Required rule, semantically unchanged:

```text
docs/code_map.md is generated structural navigation. It is not architecture authority and is not a source of truth for implemented behavior.
```

### 6.10 Conflict handling

`docs/canonical/AUTHORITY.md` must state that conflicts must be surfaced explicitly.

Required rule, semantically unchanged:

```text
If authority layers conflict, do not silently choose the convenient source. Surface the conflict in the ticket, PR, or documentation audit and resolve it through an explicit follow-up decision or ticket.
```

---

## 7. Required file-specific changes

### 7.1 `docs/canonical/AUTHORITY.md`

Update the file to implement the authority model in section 6. Do not rewrite sections that are not covered by the required rules in section 6. Where the existing file already contains a rule that is consistent with section 6, preserve the existing wording unless it directly contradicts a required rule.

The resulting file must include:

1. Purpose.
2. Authority hierarchy.
3. Document class/taxonomy.
4. `INDEX.md` role precedence rule.
5. Current-state documentation rule.
6. Build-spec / design-intent rule.
7. Previous-scanner reference rule.
8. Tracking/evidence document rule.
9. AI context helper rule.
10. Generated navigation rule.
11. Conflict-handling rule.
12. Explicit statement that no root-level `docs/AUTHORITY.md` is used.

Do not include detailed scanner domain logic in this file.

### 7.2 `docs/canonical/INDEX.md`

Update only as needed to align with the consolidated authority model.

Required changes:

- Keep it as the canonical role/navigation index.
- Ensure it points to `docs/canonical/AUTHORITY.md` as the central documentation authority file.
- Preserve the active vs. `legacy_reference_only` distinction.
- Do not reclassify individual domain files in this ticket unless strictly necessary to remove a direct contradiction with `AUTHORITY.md`.
- Do not perform full inventory cleanup in this ticket.

### 7.3 `docs/canonical/WORKFLOW_CODEX.md`

Update only as needed to align wording with the consolidated authority model.

Required changes:

- Ensure the repo-reality-first hierarchy remains consistent with `docs/canonical/AUTHORITY.md`.
- Avoid duplicating the full authority model if a concise reference to `docs/canonical/AUTHORITY.md` is clearer.
- Keep its Codex workflow/pre-read purpose.

### 7.4 `docs/AGENTS.md`

Update only as needed to avoid contradictory or stale authority guidance.

Required changes:

- Remove duplicate `docs/canonical/INDEX.md` entry if present.
- Point agents first to `docs/canonical/AUTHORITY.md`, then `docs/canonical/INDEX.md`, then `docs/canonical/WORKFLOW_CODEX.md`.
- Ensure it does not imply that auto-docs such as `docs/code_map.md` are authority.
- Keep it short.

### 7.5 `docs/dev_workflow.md`

Mark this file as superseded by `docs/canonical/WORKFLOW_CODEX.md`.

Preferred approach:

- Add a clear supersession notice near the top.
- Do not delete the file.
- Do not extensively rewrite old workflow content.
- State that `docs/canonical/WORKFLOW_CODEX.md` is the active workflow reference for Codex/current documentation work.
- Explicitly neutralize the old `code_map.md` single-source-of-truth statement.

Required wording, semantically unchanged:

```text
This document is superseded for current Codex/documentation workflow by docs/canonical/WORKFLOW_CODEX.md. Any statement in this file that treats docs/code_map.md as a source of truth is obsolete; docs/code_map.md is generated navigation only.
```

---

## 8. Expected documentation impact

Expected modified files:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/canonical/WORKFLOW_CODEX.md
docs/AGENTS.md
docs/dev_workflow.md
```

Expected created files:

```text
none
```

Expected deleted files:

```text
none
```

---

## 9. Verification

After implementation, verify:

1. No `docs/AUTHORITY.md` file exists or was created.
2. `docs/AI_CONTEXT_CURRENT.md` was not modified.
3. No code files were modified.
4. No test files were modified.
5. No schema files were modified.
6. No CI/workflow files were modified.
7. `docs/canonical/AUTHORITY.md` contains the repo-reality-first current-state anchor.
8. `docs/canonical/AUTHORITY.md` contains the binding `INDEX.md` role precedence rule.
9. `docs/canonical/AUTHORITY.md` classifies v2.1 files and `independence_release_gesamtkonzept_final.md` as build-spec / design-intent authority.
10. `docs/canonical/AUTHORITY.md` states that `docs/code_map.md` is generated navigation only.
11. `docs/dev_workflow.md` is clearly marked as superseded by `docs/canonical/WORKFLOW_CODEX.md`.
12. `docs/AGENTS.md`, `docs/canonical/INDEX.md`, and `docs/canonical/WORKFLOW_CODEX.md` do not contradict `docs/canonical/AUTHORITY.md`.
13. No scanner domain logic, schema semantics, or report/data model content was updated.

Suggested local checks:

```bash
test ! -f docs/AUTHORITY.md
git diff --name-only
grep -n "legacy_reference_only" docs/canonical/AUTHORITY.md
grep -n "takes precedence over" docs/canonical/AUTHORITY.md
grep -n "docs/code_map.md" docs/canonical/AUTHORITY.md docs/dev_workflow.md
grep -n "WORKFLOW_CODEX.md" docs/dev_workflow.md
```

---

## 10. Acceptance criteria

- [ ] `docs/canonical/AUTHORITY.md` is updated to the consolidated authority model.
- [ ] No root-level `docs/AUTHORITY.md` is created.
- [ ] `docs/AI_CONTEXT_CURRENT.md` is unchanged.
- [ ] `docs/canonical/INDEX.md` remains the role/navigation index.
- [ ] `docs/canonical/INDEX.md` active vs. `legacy_reference_only` distinction is preserved.
- [ ] `docs/canonical/AUTHORITY.md` contains a binding rule that `docs/canonical/INDEX.md` `legacy_reference_only` classification overrides stale in-file `status: canonical` declarations until explicit revalidation/reclassification.
- [ ] Current code, tests, schemas, workflows, and current artifacts are stated as the primary anchor for current implemented behavior.
- [ ] v2.1 section files and `independence_release_gesamtkonzept_final.md` are classified as build-spec / design-intent authority.
- [ ] Previous-scanner documentation is classified as reference-only unless explicitly revalidated.
- [ ] `docs/SCHEMA_CHANGES.md` is classified as schema/output evidence log, not a full data model.
- [ ] AI context documents are classified as context/routing helpers.
- [ ] `docs/code_map.md` is classified as generated navigation only.
- [ ] `docs/dev_workflow.md` is clearly superseded by `docs/canonical/WORKFLOW_CODEX.md`.
- [ ] No code, tests, schemas, CI/workflows, or runtime behavior are changed.

---

## 11. Suggested PR title

```text
DOC-B: Consolidate documentation authority model
```

## 12. Suggested PR summary

```text
## Summary
- Consolidate documentation authority in docs/canonical/AUTHORITY.md
- Align canonical index, Codex workflow, and agent guidance with the repo-reality-first authority model
- Mark dev_workflow.md as superseded by WORKFLOW_CODEX.md
- Preserve existing role classifications without domain-doc rewrites

## Scope
- Documentation authority/process only
- No scanner domain logic updates
- No code/test/schema/workflow changes
- No root-level docs/AUTHORITY.md introduced

## Verification
- Confirmed docs/AI_CONTEXT_CURRENT.md unchanged
- Confirmed docs/AUTHORITY.md not created
- Confirmed only allowed documentation files changed
```
