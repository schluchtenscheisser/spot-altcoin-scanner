# DOC-C: Documentation Impact Process Guard

## Metadata

- Ticket ID: DOC-C
- Title: Documentation Impact Process Guard — Ticket Template and Preflight Enforcement
- Status: Draft — Codex-ready after Martin approval
- Priority: P1
- Language: Implementation and documentation artifacts in English
- Scope type: Documentation process guard only
- Primary files:
  - `docs/tickets/_TEMPLATE.md`
  - `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
  - `docs/canonical/WORKFLOW_CODEX.md`
- Code impact: None
- Schema impact: None
- Runtime impact: None
- Predecessors:
  - DOC-A — `docs/audit/documentation_inventory_v0.md`
  - DOC-B — consolidated authority model in `docs/canonical/AUTHORITY.md`

---

## 1. Context

DOC-A recorded the repository documentation inventory and known documentation role conflicts.

DOC-B consolidated documentation authority into `docs/canonical/AUTHORITY.md`, established current repository reality as the primary anchor for current-state documentation, preserved `docs/canonical/INDEX.md` as the role/navigation index, and superseded stale workflow guidance via `docs/canonical/WORKFLOW_CODEX.md`.

This ticket adds a process guard so future Codex tickets must explicitly evaluate documentation impact before implementation.

The goal is to prevent documentation drift from recurring.

---

## 2. Problem

Future implementation tickets can still change scanner behavior, fields, schemas, runtime behavior, reports, diagnostics, persistence, evaluation outputs, or documentation roles without updating the relevant documentation.

The current repo already has strong ticket-quality and preflight guidance, but it does not yet enforce a concise, mandatory documentation-impact decision in every ticket.

Current state:

1. `docs/tickets/_TEMPLATE.md` has `Canonical References`, implementation notes, and Definition of Done wording, but no explicit standalone `## Documentation impact` section.
2. `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` is the active master preflight checklist and is mandatory for every Codex ticket, but it does not yet contain a generic Documentation-Impact-Check with a stop-condition for missing or empty impact decisions.
3. `docs/canonical/WORKFLOW_CODEX.md` already expects PR bodies to include a docs impact summary, but it does not yet require the source ticket itself to contain a dedicated documentation-impact section.

---

## 3. Goal

Add a mandatory documentation-impact process guard to the active ticketing workflow.

After this ticket:

1. Every future ticket created from `docs/tickets/_TEMPLATE.md` must contain a standalone `## Documentation impact` section.
2. The active preflight checklist must include a dedicated Documentation-Impact-Check.
3. The active preflight checklist must treat a missing `## Documentation impact` section, or an empty/unreasoned “no documentation update required” statement, as a stop-condition.
4. `docs/canonical/WORKFLOW_CODEX.md` must state that source tickets must include documentation-impact decisions and that PR bodies must summarize the result.
5. No scanner domain documentation is updated in this ticket.

---

## 4. Scope

Codex may modify only these files:

```text
docs/tickets/_TEMPLATE.md
docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
docs/canonical/WORKFLOW_CODEX.md
```

Changes must be documentation-process-only.

---

## 5. Out of Scope

Codex must not modify:

```text
docs/canonical/AUTHORITY.md
docs/canonical/INDEX.md
docs/AI_CONTEXT_CURRENT.md
docs/AGENTS.md
docs/dev_workflow.md
docs/SCHEMA_CHANGES.md
docs/audit/documentation_inventory_v0.md
README.md
```

Codex must not modify any scanner current-state/domain documentation, including but not limited to:

```text
docs/canonical/DATA_MODEL.md
docs/canonical/REPORTS.md
docs/canonical/ARCHITECTURE.md
docs/canonical/RUNTIME_AND_OPERATIONS.md
docs/canonical/SNAPSHOTS.md
docs/canonical/TEST_STRATEGY.md
docs/canonical/GLOSSARY.md
docs/canonical/open_questions.md
docs/canonical/feature_enhancements.md
```

Codex must not modify:

- code,
- tests,
- schemas,
- CI/workflows,
- runtime behavior,
- generated artifacts,
- run outputs,
- any legacy/reference documentation file not explicitly listed in scope.

Codex must not create new files.

---

## 6. Required change: `docs/tickets/_TEMPLATE.md`

### 6.1 Add standalone section

Add a new standalone section named exactly:

```markdown
## Documentation impact
```

Recommended insertion point:

- Insert after `## Scope` / `## Out of Scope` / `## Canonical References` if that structure is present.
- If exact placement is ambiguous, place it immediately after `## Canonical References (important)` and before `## Proposed change (high-level)`.

### 6.2 Required section content

The new section must require the ticket author / Codex to check whether the ticket changes or invalidates any of the following:

1. system architecture or pipeline flow,
2. fields, schemas, diagnostics, reports, persisted data, or output semantics,
3. runtime behavior, scheduling, persistence, artifacts, CI behavior, or operational workflow,
4. evaluation, replay, backtesting, or analysis outputs,
5. documentation authority, document role, onboarding, workflow, or process documentation.

The section must define two explicit variants.

#### Variant A — Documentation update required

Required meaning:

```text
If the ticket affects documentation, list the affected documentation files and update them in the same PR unless explicitly out of scope.
```

The template should provide a fillable checklist such as:

```markdown
### Variant A — Documentation update required

Affected documentation:
- [ ] `docs/canonical/ARCHITECTURE.md`
- [ ] `docs/canonical/DATA_MODEL.md`
- [ ] `docs/canonical/REPORTS.md`
- [ ] `docs/canonical/SNAPSHOTS.md`
- [ ] `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- [ ] `docs/canonical/TEST_STRATEGY.md`
- [ ] `docs/SCHEMA_CHANGES.md`
- [ ] `docs/canonical/WORKFLOW_CODEX.md`
- [ ] `docs/tickets/_TEMPLATE.md`
- [ ] `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- [ ] Other: `<path>`

Documentation update plan:
- `<what will be updated in this PR>`
```

Codex may adjust the list for formatting, but the required categories must remain.

#### Variant B — No documentation update required

Required wording, semantically unchanged:

```text
No canonical documentation update required.
Reason: <specific reason why this ticket does not change or invalidate architecture, data model, reports, snapshots, runtime/operations, evaluation, authority, onboarding, or process documentation>.
```

The reason must not be empty.

### 6.3 Stop-condition note in template

The template must state that a missing `## Documentation impact` section or an empty/unreasoned Variant B makes the ticket not ready for Codex implementation.

Required wording, semantically unchanged:

```text
If this section is missing, or if Variant B is selected without a specific reason, the ticket is not Codex-ready.
```

---

## 7. Required change: `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`

### 7.1 Exact insertion position

The current active preflight checklist has:

- `## 20. Pflichtsektion für Input-/Parser-/Zeitlogik-Tickets`
- `## 21. Freigabe-Gate vor Ticket-Abgabe`
- later sections through:
- `## 25. Ausgabe`

Insert a new section exactly after the current section:

```markdown
## 20. Pflichtsektion für Input-/Parser-/Zeitlogik-Tickets
```

and before the current section:

```markdown
## 21. Freigabe-Gate vor Ticket-Abgabe
```

The new section must be numbered:

```markdown
## 21. Documentation-Impact-Check
```

Renumber the existing sections as follows:

```text
old ## 21. Freigabe-Gate vor Ticket-Abgabe -> new ## 22. Freigabe-Gate vor Ticket-Abgabe
old ## 22. Wiederverwendbare Standardsätze für Tickets -> new ## 23. Wiederverwendbare Standardsätze für Tickets
old ## 23. Schnellprüfung vor Freigabe -> new ## 24. Schnellprüfung vor Freigabe
old ## 24. Zielzustand -> new ## 25. Zielzustand
old ## 25. Ausgabe -> new ## 26. Ausgabe
```

Do not renumber sections 1–20.

### 7.2 Required new section content

The new section must state that the Documentation-Impact-Check is mandatory for every ticket.

It must include these questions:

```markdown
### Prüffragen

* [ ] Enthält das Ticket eine eigenständige Sektion `## Documentation impact`?
* [ ] Betrifft das Ticket Architektur, Pipeline-Flow oder Systemstruktur?
* [ ] Betrifft das Ticket Felder, Schemas, Diagnostics, Reports, Snapshots, persistierte Daten oder Output-Semantik?
* [ ] Betrifft das Ticket Runtime, Scheduling, Persistenz, Artefakte, CI oder operative Workflows?
* [ ] Betrifft das Ticket Evaluation, Replay, Backtesting oder Analyse-Outputs?
* [ ] Betrifft das Ticket Documentation Authority, Dokumentrollen, Onboarding, Workflow oder Prozessdokumentation?
* [ ] Falls Dokumentation betroffen ist: sind die betroffenen Dokumente im Ticket konkret genannt?
* [ ] Falls Dokumentation betroffen ist: werden die betroffenen Dokumente im selben PR aktualisiert oder ist ein explizites Follow-up / Out-of-Scope begründet?
* [ ] Falls keine Dokumentation betroffen ist: enthält das Ticket die Formulierung `No canonical documentation update required` mit spezifischer Begründung?
```

### 7.3 Required stop-condition

The new section must include an explicit stop-condition.

Required wording, semantically unchanged:

```markdown
### Abbruchregel

Wenn die Sektion `## Documentation impact` im Ticket fehlt, ist das Ticket nicht freigabefähig.

Wenn Variante B (`No canonical documentation update required`) gewählt wird, aber die Begründung leer, generisch oder nicht auf den Ticket-Scope bezogen ist, ist das Ticket nicht freigabefähig.

Wenn das Ticket dokumentationsrelevante Änderungen enthält, aber weder eine Dokumentationsaktualisierung im selben PR noch ein explizit begründetes Follow-up / Out-of-Scope benennt, ist das Ticket nicht freigabefähig.
```

This stop-condition is mandatory.

### 7.4 Update related checklist sections

Update the existing “Freigabe-Gate” and “Schnellprüfung vor Freigabe” sections only as needed to include the documentation-impact question.

For the renumbered “Freigabe-Gate vor Ticket-Abgabe” section, add a question semantically equivalent to:

```markdown
* [ ] Könnte Codex die PR umsetzen, ohne bei Documentation Impact oder betroffenen Current-State-Docs raten zu müssen?
```

For the renumbered “Schnellprüfung vor Freigabe” section, add a short subsection:

```markdown
### Documentation Impact

* [ ] `## Documentation impact` vorhanden?
* [ ] Falls keine Doku betroffen: spezifische Begründung enthalten?
* [ ] Falls Doku betroffen: betroffene Dateien / Follow-up klar benannt?
```

Do not otherwise rewrite the preflight checklist.

---

## 8. Required change: `docs/canonical/WORKFLOW_CODEX.md`

Update `docs/canonical/WORKFLOW_CODEX.md` minimally.

Required additions:

1. State that every Codex-targeted ticket must contain a `## Documentation impact` section.
2. State that PR bodies must summarize the documentation-impact outcome.
3. State that if documentation is affected but not updated in the same PR, the ticket and PR must explicitly name the follow-up or explain why it is out of scope.
4. Keep `docs/canonical/AUTHORITY.md` as the central authority reference.
5. Do not duplicate the full template or preflight checklist if a concise reference to `docs/tickets/_TEMPLATE.md` and `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` is clearer.

Suggested insertion points:

- In the ticket/pre-read or PR preparation area, add a concise reference to the mandatory Documentation Impact section.
- In the PR body/completion checklist area, ensure the docs impact summary requirement points back to the ticket’s `## Documentation impact` section.

Do not restructure the whole file.

---

## 9. Expected documentation impact

Expected modified files:

```text
docs/tickets/_TEMPLATE.md
docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
docs/canonical/WORKFLOW_CODEX.md
```

Expected created files:

```text
none
```

Expected deleted files:

```text
none
```

No current-state scanner documentation is updated in this ticket.

---

## 10. Verification

After implementation, verify:

1. Only the allowed files were modified:
   - `docs/tickets/_TEMPLATE.md`
   - `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
   - `docs/canonical/WORKFLOW_CODEX.md`
2. No code, tests, schemas, CI/workflows, README, authority file, index file, or current-state domain docs were modified.
3. `docs/tickets/_TEMPLATE.md` contains exactly one standalone `## Documentation impact` section.
4. `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` contains `## 21. Documentation-Impact-Check`.
5. The previous sections 21–25 in `_TICKET_PREFLIGHT_CHECKLIST.md` were renumbered to 22–26.
6. `_TICKET_PREFLIGHT_CHECKLIST.md` contains the required stop-condition for missing `## Documentation impact`.
7. `_TICKET_PREFLIGHT_CHECKLIST.md` contains the required stop-condition for empty/unreasoned Variant B.
8. `_TICKET_PREFLIGHT_CHECKLIST.md` contains the required stop-condition for affected documentation without same-PR update or explicit follow-up/out-of-scope.
9. `docs/canonical/WORKFLOW_CODEX.md` states that each Codex-targeted ticket must include a `## Documentation impact` section.
10. No `docs/AUTHORITY.md` was created.
11. `docs/AI_CONTEXT_CURRENT.md` was not modified.

Suggested local checks:

```bash
git diff --name-only

grep -n "^## Documentation impact" docs/tickets/_TEMPLATE.md
grep -n "^## 21\. Documentation-Impact-Check" docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
grep -n "nicht freigabefähig" docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
grep -n "No canonical documentation update required" docs/tickets/_TEMPLATE.md docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md
grep -n "Documentation impact" docs/canonical/WORKFLOW_CODEX.md

test ! -f docs/AUTHORITY.md
```

---

## 11. Acceptance criteria

- [ ] `docs/tickets/_TEMPLATE.md` contains a standalone `## Documentation impact` section.
- [ ] The template provides Variant A for documentation updates.
- [ ] The template provides Variant B with the required `No canonical documentation update required` wording and a non-empty reason placeholder.
- [ ] The template states that missing Documentation Impact or empty/unreasoned Variant B makes the ticket not Codex-ready.
- [ ] `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` contains a new `## 21. Documentation-Impact-Check` section inserted after the old section 20 and before the old section 21.
- [ ] Existing sections 21–25 in `_TICKET_PREFLIGHT_CHECKLIST.md` are renumbered to 22–26.
- [ ] The new preflight section includes the required stop-condition.
- [ ] The renumbered Freigabe-Gate includes a documentation-impact readiness question.
- [ ] The renumbered Schnellprüfung includes a Documentation Impact subsection.
- [ ] `docs/canonical/WORKFLOW_CODEX.md` references the mandatory ticket-level documentation-impact section.
- [ ] Only the allowed files were modified.
- [ ] No code, tests, schemas, CI/workflows, README, authority/index files, or domain/current-state docs were modified.

---

## 12. Suggested PR title

```text
DOC-C: Add documentation impact process guard
```

## 13. Suggested PR summary

```text
## Summary
- Add a mandatory Documentation Impact section to the ticket template
- Add a Documentation-Impact-Check with stop-conditions to the active ticket preflight checklist
- Align WORKFLOW_CODEX with the new ticket-level documentation-impact requirement

## Scope
- Documentation process only
- No current-state scanner documentation updates
- No code/test/schema/workflow changes
- No authority/index changes

## Verification
- Confirmed only allowed process docs were modified
- Confirmed template contains a standalone Documentation impact section
- Confirmed preflight checklist contains Documentation-Impact-Check and stop-conditions
- Confirmed WORKFLOW_CODEX references the new process requirement
```
