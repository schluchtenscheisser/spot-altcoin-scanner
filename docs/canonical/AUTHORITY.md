# Documentation Authority — Current-State Precedence (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_AUTHORITY
status: canonical
canonical_root: docs/canonical
central_authority_file: docs/canonical/AUTHORITY.md
root_level_docs_authority_used: false
last_updated_utc: "2026-06-06T00:00:00Z"
```

## 1. Purpose

This file defines the repository documentation authority model, precedence rules, and conflict-handling rules for current scanner documentation work.

This repository uses `docs/canonical/AUTHORITY.md` as the central documentation authority and precedence file. No separate root-level `docs/AUTHORITY.md` is used.

This file does not define scanner domain logic. It defines how documentation and evidence sources may be used when documenting, auditing, or changing the current repository.

## 2. Authority hierarchy

For current implemented scanner behavior, the primary anchor is current repository reality: current code, tests, schemas, GitHub Actions workflows, current run artifacts, diagnostics, manifests, reports, and evaluation outputs.

Use the following hierarchy when determining implemented current-state behavior:

1. **Current repository reality** — current code, tests, schemas, workflows, current run artifacts, diagnostics, manifests, reports, and evaluation outputs.
2. **Validated current-state canonical documentation** — documents that have been validated against implemented repository reality and are intended to describe the current scanner.
3. **Build-spec / design-intent authority** — the v2.1 section files and `independence_release_gesamtkonzept_final.md`, where useful for Independence transformation intent and not contradicted by current repository reality.
4. **Current ticket scope** — concrete task scope and acceptance criteria. A ticket does not silently override higher authority layers.
5. **Planning, tracking, evidence, routing, and context helpers** — useful supporting material with the roles defined below.
6. **Previous-scanner documentation and legacy references** — historical or migration context only unless explicitly revalidated and reclassified.

Current-state documentation should describe implemented behavior, not merely historical intent, previous-scanner design, or unvalidated build-spec expectations.

## 3. Document class / taxonomy

### 3.1 Current-state canonical documentation

Current-state canonical documentation is documentation that has been validated against implemented repository reality and is intended to describe the current scanner.

A file path under `docs/canonical/` does not by itself make a document current-state authority. The document role in `docs/canonical/INDEX.md` and the current authority model determine how it may be used.

`docs/canonical/INDEX.md` is the canonical role/navigation index. The repository uses a role-aware canonical model, not a flat source-of-truth bucket: the index records which documents are active current-state references, including `active_independence_release` documents where applicable, and which documents or folders are `legacy_reference_only`.

### 3.2 Build-spec / design-intent authority

The v2.1 section files and `independence_release_gesamtkonzept_final.md` are build-spec / design-intent authority for the Independence transformation. They are not ordinary previous-scanner legacy documentation, but they are also not complete current-state documentation after implementation.

These build-spec documents remain useful for:

- domain intent,
- unresolved design questions,
- explaining why the current implementation exists,
- identifying spec-vs-implementation gaps.

They must not silently override current code, tests, schemas, workflows, current artifacts, diagnostics, manifests, reports, evaluation outputs, or validated current-state canonical documentation for implemented behavior.

### 3.3 Previous-scanner reference documentation

Previous-scanner documentation may be useful as historical reference or migration context, but it must not be used as active current-state authority unless a dedicated ticket revalidates and reclassifies it.

This includes previous-scanner contracts that remain in the repository for migration continuity, compatibility reference, or audit history.

### 3.4 Tracking and evidence documents

`docs/SCHEMA_CHANGES.md` is a schema/output change evidence log. It is a strong evidence source for later `docs/canonical/DATA_MODEL.md`, `docs/canonical/REPORTS.md`, and `docs/canonical/SNAPSHOTS.md` updates, but it is not a complete current-state data model or report specification.

`docs/canonical/open_questions.md` and `docs/canonical/feature_enhancements.md` are active planning/tracking documents. They are not previous-scanner legacy documentation, and they do not by themselves override current repository reality.

### 3.5 AI context helpers

AI context documents are routing and context helpers. They do not override current repository reality or validated current-state canonical documentation.

Examples include:

- `docs/AI_CONTEXT_CURRENT.md`
- `docs/GPT_SNAPSHOT.md`
- `docs/AGENTS.md`

### 3.6 Generated navigation

`docs/code_map.md` is generated structural navigation. It is not architecture authority and is not a source of truth for implemented behavior.

Generated navigation can help locate files and modules, but it cannot establish requirements, resolve authority conflicts, or override current repository reality.

## 4. `INDEX.md` role precedence rule

Where `docs/canonical/INDEX.md` classifies a file or folder as `legacy_reference_only`, that classification takes precedence over any `status: canonical` declaration in the file header, until the file has been explicitly revalidated and reclassified in a dedicated ticket.

This rule is binding. Do not treat stale in-file headers as active current-state authority when `docs/canonical/INDEX.md` classifies that file or folder as `legacy_reference_only`.

## 5. Current-state documentation rule

Current-state documentation must be anchored in implemented repository reality and should identify uncertainty instead of converting historical intent into implemented facts.

When current-state documentation and current repository reality diverge, use current repository reality as the primary anchor, then update or ticket the documentation gap explicitly.

## 6. Build-spec / design-intent rule

Use the v2.1 section files and `independence_release_gesamtkonzept_final.md` as Independence transformation design-intent sources, not as complete post-implementation current-state documentation.

If build-spec intent differs from current repository reality, surface the spec-vs-implementation gap instead of silently treating either source as interchangeable.

## 7. Previous-scanner reference rule

Previous-scanner documentation is reference-only unless explicitly revalidated and reclassified in a dedicated ticket.

Do not use previous-scanner documentation to reintroduce old architecture, output contracts, scoring, ranking, runtime modes, or workflow assumptions as active current-state behavior without explicit revalidation.

## 8. Tracking / evidence document rule

Tracking and evidence documents may support audits, implementation follow-ups, and documentation updates, but their role must be respected:

- `docs/SCHEMA_CHANGES.md` records schema/output changes and is evidence for later data-model/report/snapshot documentation work.
- `docs/canonical/open_questions.md` records unresolved decisions.
- `docs/canonical/feature_enhancements.md` records planned or proposed enhancements.

These documents are not full substitutes for current code, tests, schemas, workflows, artifacts, or validated current-state canonical documentation.

## 9. AI context helper rule

AI context helpers may route an agent to relevant files, summarize recent repository state, or warn about active boundaries. They are supporting context only.

They do not override current repository reality, the binding `docs/canonical/INDEX.md` role classifications, or validated current-state canonical documentation.

## 10. Generated navigation rule

Use `docs/code_map.md` only as generated structural navigation.

Do not treat `docs/code_map.md` as architecture authority, a requirements source, or a source of truth for implemented behavior.

## 11. Conflict-handling rule

If authority layers conflict, do not silently choose the convenient source. Surface the conflict in the ticket, PR, or documentation audit and resolve it through an explicit follow-up decision or ticket.

Do not hide conflicts by relying on stale headers, legacy references, generated navigation, or context-helper summaries when current repository reality or validated role classifications say otherwise.
