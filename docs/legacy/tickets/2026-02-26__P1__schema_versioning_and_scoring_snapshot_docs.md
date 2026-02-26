> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# 4) 2026-02-26__P1__schema_versioning_and_scoring_snapshot_docs.md

## Title
[P1] Schema-Version bump + docs/SCHEMA_CHANGES + GPT Snapshot Scoring-Text sichern

## Context / Source (optional)
- PR-Feedback: Schema-Versionierung für neue Output-Felder (discovery) fehlt.
- PR-Feedback: GPT Snapshot Workflow darf Scoring-Regeln nicht verlieren, wenn `docs/scoring.md` nur Redirect ist.

## Goal
1) Output-Schema Version ist eindeutig gebumpt und changelogged.  
2) Scoring-Regeln sind weiterhin im GPT Snapshot enthalten.

## Scope
- `scanner/pipeline/output.py` (Version field in meta bump)
- `docs/SCHEMA_CHANGES.md` (anlegen falls fehlt)
- `docs/scoring.md` und/oder `.github/workflows/generate-gpt-snapshot.yml`
- Tests:
  - `tests/test_output_schema_version.py` (checks exact expected version string)

## Out of Scope
- Keine Scoring-Änderungen
- Keine Discovery-Änderungen

## Canonical References (important)
- `docs/canonical/PIPELINE.md`
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/canonical/OUTPUTS/` (falls vorhanden)

## Proposed change (high-level)
- Bump schema version string in report meta (e.g. `1.5`→`1.6`).
- Add `docs/SCHEMA_CHANGES.md` entry documenting added discovery fields.
- Ensure scoring rules text is included in GPT snapshot generation:
  - Preferred: restore full text into `docs/scoring.md`
  - Alternative: modify workflow to include canonical scoring docs directly.

## Acceptance Criteria (deterministic)
1) Output meta contains the new exact schema version string.
2) `docs/SCHEMA_CHANGES.md` contains a matching entry with discovery field list.
3) GPT snapshot generation still includes scoring rules text (verified by checking generated snapshot file in CI output or by running workflow locally).
4) No scoring behavior changes.

## Tests (required if logic changes)
- Unit: `test_output_schema_version_is_expected`
- Verification: PR description includes steps to verify snapshot content

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only
- [ ] No lookahead
- [ ] Keine Scoring-Kurve geändert

---

## Definition of Done (Codex must satisfy)
- [ ] Implemented code/doc changes per Acceptance Criteria
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata (optional)
```yaml
created_utc: "2026-02-26T21:11:08Z"
priority: P1
type: docs
owner: codex
related_issues: []
```

---
