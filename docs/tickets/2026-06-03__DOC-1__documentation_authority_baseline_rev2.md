# Ticket DOC-1 — Documentation Authority Baseline

## Status

Ready for Codex implementation.

## Objective

Create `docs/AUTHORITY.md` as the single, explicit documentation of:

1. The authority hierarchy for all repository documents and code artifacts.
2. The documentation taxonomy (what each document class is for and how it is maintained).
3. The relationship between v2.1 build-spec (design intent) and current canonical docs (implemented state).
4. A brief README update pointing to `docs/AUTHORITY.md`.

This ticket is documentation-only. No code, schema, or test changes.

---

## Background

The repository currently has no single file that explicitly states which documents are authoritative, which are reference-only, which are historical, and which are generated. This has caused:

- Codex treating stale documents as active architecture authority.
- AI context helpers (GPT_SNAPSHOT.md, code_map.md) being treated as domain truth.
- The v2.1 build-spec being used as implemented-state documentation instead of as design-intent documentation.
- Documentation drift accumulating silently across tickets T1–T_EL2, T29, T30.

`docs/AUTHORITY.md` is the foundation required before the documentation drift inventory (Phase 3a) and any documentation update tickets can proceed correctly.

---

## Scope

Create or update only:

```text
docs/AUTHORITY.md        ← create (or overwrite if a stub already exists)
README.md                ← small addition: one paragraph + link to docs/AUTHORITY.md
```

No changes to:

- Any canonical documentation files.
- Any code, tests, schemas, or CI workflows.
- Any v2.1 build-spec files.
- `docs/AI_CONTEXT_CURRENT.md`, `docs/GPT_SNAPSHOT.md`, `docs/code_map.md`.

---

## Required outcome

### `docs/AUTHORITY.md`

The file must define:

#### 1. Purpose

State explicitly: This file is the master reference for which documents are authoritative for what purpose in the Independence Release repository. When documents conflict, this hierarchy resolves the conflict.

#### 2. Authority hierarchy

Reproduce this hierarchy **semantically unchanged** in `docs/AUTHORITY.md`. If `docs/canonical/WORKFLOW_CODEX.md` contains a materially different hierarchy, stop and surface the inconsistency before proceeding.

**Level 1 — Current validated repository reality**

The strongest source for what currently exists and how it currently behaves.

Includes:
- current code (all `scanner/` modules)
- tests
- schemas
- GitHub Actions workflows
- generated run artifacts (reports, diagnostics, manifests, snapshots)
- evaluation replay outputs

**Important constraint on generated artifacts:** Generated run artifacts (reports, diagnostics, manifests, snapshots) are evidence of observed behavior for their specific run and schema version. They are not normative if they are stale, known-buggy, or contradicted by current code, schemas, or accepted fixes. A single old or incorrect artifact does not override current code or accepted implementation contracts.

**Level 2 — Build-spec authority where not superseded**

Includes:
- the 7 v2.1 section documents (`v2_1_abschnitt_*.md`)
- `independence_release_gesamtkonzept_final.md`

These documents define design intent and domain logic for areas where no newer current-state implementation contract or validated current-state canonical documentation exists.

They are not ordinary legacy docs. They are not implemented-state documentation.

When current code, current canonical docs, or accepted implementation decisions (locked architectural decisions, decision notes) supersede a v2.1 spec statement, the current state wins. The v2.1 spec remains the reference for unresolved or underspecified domain logic.

**Level 3 — Current ticket (during active implementation)**

Defines the concrete task, scope, and acceptance criteria for the active PR.

Does not override architecture contracts except when the ticket explicitly documents an approved post-spec decision, references the relevant decision source (decision note or explicit Martin approval), and the change has been accepted. If the ticket conflicts with Level 1 or Level 2 without such documentation, Codex must stop and surface the conflict rather than silently resolving it.

**Level 4 — AI context helpers**

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
```

Context and routing aids for Claude, ChatGPT, and Codex. Not independent domain authority. Must be updated when significant architectural decisions are made.

**Level 5 — Structural navigation**

```text
docs/code_map.md
```

Generated structural navigation only. May list both active and legacy files. Must not be treated as architecture authority.

**Level 6 — Legacy / historical reference**

Includes:
- old scanner docs predating the Independence Release rebuild
- archived tickets
- deprecated canonical docs explicitly marked as legacy
- old pre-Independence AI snapshots

Use only for historical understanding unless the current ticket explicitly requires it and current repository reality supports it.

#### 3. Documentation taxonomy

Define these document classes explicitly. For each class, state: what it describes, who maintains it, and how conflicts with other classes are resolved.

**Class A — Canonical (current implemented state)**

```text
docs/canonical/*.md

Excludes:
- docs/canonical/open_questions.md       (Class D)
- docs/canonical/feature_enhancements.md (Class D)
- any file under docs/canonical/ explicitly marked as generated or legacy
```

Describes the current implemented state of the scanner: architecture, data model, runtime behavior, reports, evaluation, decision logic.

- Maintained by: Codex (as part of each relevant ticket's PR), with Claude/ChatGPT review.
- Must reflect implemented state, not design intent.
- When these files conflict with Level 1 (current code), Level 1 wins and the canonical doc must be updated.
- When these files conflict with v2.1 build-spec on a point where implementation has deliberately diverged, the canonical doc describing the implemented state wins for operational purposes. The divergence must be documented.

**Class B — Build-spec (design intent)**

```text
independence_release_gesamtkonzept_final.md
v2_1_abschnitt_1_*.md through v2_1_abschnitt_7_*.md
v2_1_addendum_*.md
```

Describes the intended design of the scanner as specified during the Independence Release planning phase.

- Not maintained / not updated after original authoring.
- Authoritative for unresolved domain logic where no current-state canonical doc or accepted implementation decision supersedes them.
- Must not be treated as implemented-state documentation.

**Class C — Decision history**

```text
docs/decision_notes/*.md
```

Records significant architectural and operational decisions, including the reasoning and alternatives considered.

- Append-only. Existing decision notes are not modified after acceptance.
- When a decision note codifies an accepted architectural lock, it supersedes the v2.1 build-spec on that specific locked point for future implementation and documentation work. It becomes implemented-state authority only once the lock is reflected in current code, schemas, tests, or current canonical documentation (Class A). Until then, it is accepted intent, not verified implemented state.

**Class D — Open questions and feature tracking**

```text
docs/canonical/open_questions.md
docs/canonical/feature_enhancements.md
```

Tracks unresolved specification questions and planned enhancements explicitly deferred from current scope.

Note: These files reside under `docs/canonical/` but are not Class A implemented-state documentation. They are explicitly Class D.

- Maintained actively. Resolved items move to a `## Resolved` section with resolution date and reference.
- Items in `open_questions.md` are stop conditions for Codex: Codex must not silently resolve them.

**Class E — AI context helpers**

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
```

Routing and context documents for AI agents working in the repository.

- Maintained when significant architectural state changes occur.
- Not domain authority. Not a substitute for canonical docs.

**Class F — Generated artifacts**

```text
docs/code_map.md
```

Auto-generated structural navigation.

- Never manually edited.
- Not architecture authority.
- Regenerated by the update script when needed.

**Class G — Historical / legacy**

Archived tickets, old snapshots, deprecated docs explicitly marked as legacy.

- Not updated.
- Referenced only for historical understanding.

#### 4. Key clarification: v2.1 build-spec vs. implemented state

State this explicitly:

> The Independence Release was implemented as a controlled rebuild of the existing scanner, not a complete ground-up rewrite. The v2.1 build-spec and Gesamtkonzept describe the intended architecture. The current canonical docs (Class A) must describe the actual implemented state. Where these differ, both the divergence and its rationale must be documented — either in the relevant canonical doc, in a decision note, or in `open_questions.md`. Undocumented divergences between spec and implementation are the primary source of documentation drift.

#### 5. Conflict resolution rule

State this rule:

> When any two documents conflict, the document at the lower level number wins (Level 1 beats Level 2, Level 2 beats Level 4, etc.). Exception: a decision note (Class C) that codifies an accepted architectural lock supersedes the v2.1 build-spec on that specific locked point. It becomes Level 1 authority only once the lock is reflected in current code, schemas, tests, or current canonical documentation.

#### 6. Documentation maintenance rule

State this rule:

> Every Codex ticket that changes system architecture, field contracts, pipeline behavior, report schemas, runtime behavior, or evaluation logic must update the affected canonical docs in the same PR. The PR body must include a Documentation Impact section stating either which canonical docs were updated, or an explicit statement that no canonical documentation update was required and why.

---

### `README.md` update

Add a short paragraph in the README under an existing relevant section (or create a new `## Documentation` section if none exists), with approximately this content:

> **Documentation authority:** See [`docs/AUTHORITY.md`](docs/AUTHORITY.md) for the complete authority hierarchy and documentation taxonomy. When documents conflict, `docs/AUTHORITY.md` defines which source wins.

The README update must not restructure or rewrite other README content. One paragraph addition only.

---

## Authority reference

This ticket is self-referential: it establishes the authority document.

The hierarchy it defines is already operative — it was established in `docs/canonical/WORKFLOW_CODEX.md` (T0.1A). `docs/AUTHORITY.md` makes this hierarchy explicit, standalone, and human-readable outside of the Codex workflow context.

> When the current authoritative reference set, existing repo Authority/Canonical documents, and existing code conflict, current repository reality (Level 1) wins. The v2.1 build-spec (Level 2) governs unresolved domain logic where Level 1 does not yet have a clear answer.

---

## Preflight checks (Pflichtsektion 19 — Repo/Authority/Onboarding)

- [x] Aktuelle autoritative Referenzmenge explizit benannt: v2.1 section docs + Gesamtkonzept + current code
- [x] Ältere Repo-Authority-Dateien gelten nur insoweit fort, wie sie nicht widersprechen: explicit in hierarchy rules
- [x] Keine entwertete Datei verbleibt als aktive SoT markiert: GPT_SNAPSHOT / code_map explicitly Class E/F
- [x] README-/Onboarding-Funktion bleibt benutzbar: README change is additive only
- [x] Keine zweite konkurrierende Dokumenten-Autorität wird erzeugt: AUTHORITY.md extends WORKFLOW_CODEX.md, does not contradict it

---

## Documentation Impact

This ticket creates `docs/AUTHORITY.md` and makes a small additive change to `README.md`.

It does not update any other canonical documentation. The drift inventory (Phase 3a) will identify which canonical docs require updates as a separate subsequent step.

---

## Acceptance criteria

- `docs/AUTHORITY.md` exists and contains all six sections specified above (Purpose, Authority hierarchy, Documentation taxonomy, v2.1-vs-implemented-state clarification, Conflict resolution rule, Documentation maintenance rule).
- The authority hierarchy in `docs/AUTHORITY.md` is semantically consistent with the hierarchy already defined in `docs/canonical/WORKFLOW_CODEX.md`. If any material inconsistency is found, Codex must stop and surface it rather than silently resolving it.
- `README.md` contains a reference to `docs/AUTHORITY.md`.
- No other files are changed.
- Class A excludes `open_questions.md` and `feature_enhancements.md` explicitly.
- The generated-artifact constraint (stale/known-buggy artifacts are not normative) is present under Level 1.
- The Level 3 ticket-override rule is conditioned on explicit approved post-spec decision documentation.
- The decision note / implemented-state distinction is explicit: decision notes become Level 1 authority only once reflected in code/schemas/tests/canonical docs.
- The documentation maintenance rule (Documentation Impact section in every relevant PR) is explicitly stated.

---

## Verification

Because this is documentation-only, verification is text-based.

1. Confirm `docs/AUTHORITY.md` exists and contains these strings:
   - `Level 1`
   - `Level 2`
   - `v2.1`
   - `design intent`
   - `implemented state`
   - `Class A`
   - `Class B`
   - `Class C`
   - `open_questions.md`
   - `feature_enhancements.md`
   - `Documentation Impact`
   - `stale`
   - `post-spec`

2. Confirm `docs/AUTHORITY.md` explicitly excludes `open_questions.md` and `feature_enhancements.md` from Class A.

3. Confirm `docs/AUTHORITY.md` does not treat `docs/GPT_SNAPSHOT.md` or `docs/code_map.md` as domain authority.

4. Confirm `README.md` contains a link to `docs/AUTHORITY.md`.

5. Confirm no code files, test files, schema files, or CI workflow files were changed.

6. Confirm `docs/canonical/WORKFLOW_CODEX.md` was not modified.

---

## Out of scope

- Creating or updating any other canonical documentation files.
- Performing the documentation drift inventory (Phase 3a — separate subsequent ticket).
- Adding the Documentation Impact section to `_TICKET_PREFLIGHT_CHECKLIST_updated.md` (Ticket DOC-2 — separate subsequent ticket).
- Classifying individual existing documentation files as current / stale / legacy (part of drift inventory).
- Any code, test, schema, or CI changes.
