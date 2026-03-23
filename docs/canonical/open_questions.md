# Open Questions — Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OPEN_QUESTIONS
status: canonical
```

## Purpose
This file tracks authoritative open questions that must be resolved before dependent implementation tickets can define business logic. The bootstrap ticket references Gesamtkonzept §21 as the source of these questions; the detailed question set is not checked into this repository at bootstrap time.

## Open questions
- Pending import from the authoritative Independence-Release open-question set in Gesamtkonzept §21.
- Resolution-before-ticket references must be added when the authoritative question list is available in-repo.

## Bootstrap rule
Until the authoritative question set is available in-repo, no later ticket may silently invent answers here for deferred business logic.
