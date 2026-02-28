> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# 5) 2026-02-26__P1__tests_fixture_paths_independent_of_cwd.md

## Title
[P1] Tests: Fixture-Pfade relativ zu __file__ (CWD-unabhängig)

## Context / Source (optional)
- PR-Feedback: Fixture-Pfade sind aktuell CWD-abhängig und brechen in IDE/CI-Kontexten.

## Goal
Alle Tests mit Fixtures müssen CWD-unabhängig sein.

## Scope
- Betroffene Tests (alle, die `Path("tests/...")` oder ähnliche Root-relative Pfade verwenden)
- Optional: `tests/_helpers.py` für eine zentrale Fixture-Resolver Funktion

## Out of Scope
- Keine Änderungen am Produktionscode

## Canonical References (important)
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
- Replace any `Path("tests/...")` with paths derived from `Path(__file__).resolve()` or helper.

## Acceptance Criteria (deterministic)
1) `pytest` läuft aus Repo-Root.
2) `pytest` läuft aus `tests/`.
3) Kein Test verwendet `Path("tests/")` für Fixtures.

## Tests
- Existing tests updated accordingly.

## Constraints / Invariants (must not change)
- [ ] Deterministische Tests
- [ ] Keine Produktionscode-Änderung

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented test changes per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P1
type: test
owner: codex
related_issues: []
```
