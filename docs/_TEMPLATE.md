# Ticket Template (for AI-generated tickets)

> Place new tickets in `docs/tickets/`.
>
> Naming convention (recommended): `YYYY-MM-DD__<priority>__<short_slug>.md`
> - priority: P0 | P1 | P2 | P3

---

## Title
[P?] Kurz, konkret, verifizierbar

## Context / Source (optional)
- Why is this change needed?
- Links to prior analysis, runs, or legacy context (if any)

## Goal
Was soll nach der Änderung möglich/anders sein?

## Scope
Welche Module/Dateien dürfen geändert werden? (Allowlist, optional but helpful)
- ...

## Out of Scope
Was explizit nicht?
- ...

## Canonical References (important)
List the canonical documents that define/are affected by this change.
(Do not link to legacy as authority.)

- docs/canonical/...
- docs/canonical/...

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary):
- Before:
- After:
- Edge cases:
- Backward compatibility impact:

## Implementation Notes (optional but useful)
- Dataflow / pipeline stage impacts
- Determinism (sorting, tie-breaks, NaN policies, closed-candle/no-lookahead)
- Performance / budgets (Top-K, API calls)
- Output/schema impacts (new fields, removed fields)

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.
1) ...
2) ...
3) ...

## Tests (required if logic changes)
- Unit:
- Integration:
- Golden fixture / verification:
  - If scoring/threshold/curve changes: update `docs/canonical/VERIFICATION_FOR_AI.md`

## Constraints / Invariants (must not change)
Examples:
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges clamp to 0..100
- Timestamp unit = ms

- [ ] ...
- [ ] ...

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` (if logic/params/outputs changed)
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if any scoring/threshold/curve behavior changed
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-02-25T22:42:57Z"
priority: P2
type: feature|bugfix|refactor|docs
owner: codex
related_issues: []
```
