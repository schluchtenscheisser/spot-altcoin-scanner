# Documentation Authority

## 1. Purpose

This file is the master reference for which documents and artifacts are authoritative for what purpose in the Independence Release repository. When documents conflict, the authority hierarchy below resolves the conflict.

This file makes the authority hierarchy from `docs/canonical/WORKFLOW_CODEX.md` explicit, standalone, and human-readable outside the Codex workflow context. It does not replace current repository reality; it explains how to decide which source wins when repository documents, build specifications, tickets, generated artifacts, and historical references disagree.

---

## 2. Authority hierarchy

### Level 1 — Current validated repository reality

Level 1 is the strongest source for what currently exists and how the scanner currently behaves.

Includes:
- current code, including all `scanner/` modules
- tests
- schemas
- GitHub Actions workflows
- generated run artifacts, including reports, diagnostics, manifests, and snapshots
- evaluation replay outputs

**Important constraint on generated artifacts:** Generated run artifacts are evidence of observed behavior for their specific run and schema version. They are not normative if they are stale, known-buggy, or contradicted by current code, schemas, or accepted fixes. A single old or incorrect artifact does not override current code or accepted implementation contracts.

### Level 2 — Build-spec authority where not superseded

Includes:
- the 7 v2.1 section documents (`v2_1_abschnitt_*.md`)
- `independence_release_gesamtkonzept_final.md`

These documents define design intent and domain logic for areas where no newer current-state implementation contract or validated current-state canonical documentation exists.

They are not ordinary legacy docs. They are not implemented-state documentation.

When current code, current canonical docs, or accepted implementation decisions such as locked architectural decisions or decision notes supersede a v2.1 spec statement, the current state wins. The v2.1 spec remains the reference for unresolved or underspecified domain logic.

### Level 3 — Current ticket during active implementation

The current ticket defines the concrete task, scope, and acceptance criteria for the active PR.

The current ticket does not override architecture contracts except when it explicitly documents an approved post-spec decision, references the relevant decision source such as a decision note or explicit Martin approval, and the change has been accepted. If a ticket conflicts with Level 1 or Level 2 without that documentation, Codex must stop and surface the conflict rather than silently resolving it.

### Level 4 — AI context helpers

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
```

These files are context and routing aids for Claude, ChatGPT, Codex, and other AI agents. They are not independent domain authority and must not be used as a substitute for current code, build-spec authority, or validated canonical docs. They should be updated when significant architectural decisions are made.

### Level 5 — Structural navigation

```text
docs/code_map.md
```

`docs/code_map.md` is generated structural navigation only. It may list both active and legacy files. It must not be treated as architecture authority.

### Level 6 — Legacy / historical reference

Includes:
- old scanner docs predating the Independence Release rebuild
- archived tickets
- deprecated canonical docs explicitly marked as legacy
- old pre-Independence AI snapshots

Use these sources only for historical understanding unless the current ticket explicitly requires them and current repository reality supports that use.

---

## 3. Documentation taxonomy

### Class A — Canonical: current implemented state

```text
docs/canonical/*.md

Excludes:
- docs/canonical/open_questions.md       (Class D)
- docs/canonical/feature_enhancements.md (Class D)
- any file under docs/canonical/ explicitly marked as generated or legacy
```

Class A describes the current implemented state of the scanner: architecture, data model, runtime behavior, reports, evaluation, and decision logic.

- Maintained by: Codex as part of each relevant ticket PR, with Claude/ChatGPT review.
- Must reflect implemented state, not design intent.
- When Class A files conflict with Level 1 current code, Level 1 wins and the canonical doc must be updated.
- When Class A files conflict with the v2.1 build-spec on a point where implementation has deliberately diverged, the canonical doc describing implemented state wins for operational purposes. The divergence must be documented.

### Class B — Build-spec: design intent

```text
independence_release_gesamtkonzept_final.md
v2_1_abschnitt_1_*.md through v2_1_abschnitt_7_*.md
v2_1_addendum_*.md
```

Class B describes the intended design of the scanner as specified during the Independence Release planning phase.

- Maintained by: original authors; not maintained or updated after original authoring.
- Authoritative for unresolved domain logic where no current-state canonical doc or accepted implementation decision supersedes it.
- Must not be treated as implemented-state documentation.

### Class C — Decision history

```text
docs/decision_notes/*.md
```

Class C records significant architectural and operational decisions, including reasoning and alternatives considered.

- Maintained by: humans and AI agents through accepted decision-note PRs.
- Append-only after acceptance; existing decision notes are not modified after they are accepted.
- When a decision note codifies an accepted architectural lock, it supersedes the v2.1 build-spec on that specific locked point for future implementation and documentation work. It becomes implemented-state authority only once the lock is reflected in current code, schemas, tests, or current canonical documentation (Class A). Until then, it is accepted intent, not verified implemented state.

### Class D — Open questions and feature tracking

```text
docs/canonical/open_questions.md
docs/canonical/feature_enhancements.md
```

Class D tracks unresolved specification questions and planned enhancements explicitly deferred from current scope.

These files reside under `docs/canonical/`, but they are not Class A implemented-state documentation. `docs/canonical/open_questions.md` and `docs/canonical/feature_enhancements.md` are explicitly excluded from Class A.

- Maintained by: Codex and human reviewers as questions are opened, resolved, or deferred.
- Resolved items move to a `## Resolved` section with resolution date and reference.
- Items in `open_questions.md` are stop conditions for Codex: Codex must not silently resolve them.

### Class E — AI context helpers

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
```

Class E provides routing and context for AI agents working in the repository.

- Maintained by: Codex and human reviewers when significant architectural state changes occur.
- Not domain authority. Not a substitute for canonical docs.
- If Class E conflicts with Level 1, Level 2, or validated Class A documentation, the higher authority wins and the helper should be corrected when in scope.

### Class F — Generated artifacts

```text
docs/code_map.md
```

Class F is auto-generated structural navigation.

- Maintained by: update scripts and generation workflows, not manual edits.
- Never manually edited.
- Not architecture authority.
- Regenerated by the update script when needed.

### Class G — Historical / legacy

Class G includes archived tickets, old snapshots, deprecated docs explicitly marked as legacy, and old scanner docs predating the Independence Release rebuild.

- Maintained by: not updated except for archival moves or explicit legacy labeling.
- Referenced only for historical understanding.
- If Class G conflicts with any current source, the current source wins.

---

## 4. v2.1 build-spec vs. implemented state

The Independence Release was implemented as a controlled rebuild of the existing scanner, not a complete ground-up rewrite. The v2.1 build-spec and Gesamtkonzept describe the intended architecture. The current canonical docs (Class A) must describe the actual implemented state. Where these differ, both the divergence and its rationale must be documented — either in the relevant canonical doc, in a decision note, or in `open_questions.md`. Undocumented divergences between spec and implementation are the primary source of documentation drift.

---

## 5. Conflict resolution rule

When any two documents conflict, the document at the lower level number wins: Level 1 beats Level 2, Level 2 beats Level 4, and so on. Exception: a decision note (Class C) that codifies an accepted architectural lock supersedes the v2.1 build-spec on that specific locked point. It becomes implemented-state authority only once the lock is reflected in current code, schemas, tests, or current canonical documentation.

If a conflict cannot be resolved by this hierarchy, Codex must stop and surface the conflict instead of silently choosing an interpretation.

---

## 6. Documentation maintenance rule

Every Codex ticket that changes system architecture, field contracts, pipeline behavior, report schemas, runtime behavior, or evaluation logic must update the affected canonical docs in the same PR. The PR body must include a Documentation Impact section stating either which canonical docs were updated, or an explicit statement that no canonical documentation update was required and why.
