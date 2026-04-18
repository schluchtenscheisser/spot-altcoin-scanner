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

## Resolved by Ticket 2026-04-13__P0__eligibility_market_data_budget_pre_4h_candidate_filter (3)
- §21 Question 1 resolved: monitored symbols receive deterministic 4h monitoring bypass before non-bypass cap.
- §21 Question 2 resolved: pre-4h filter is a cheap 1d-only, 3-rule OR gate with deterministic reason priority and cap tie-break.

## Ticket 4 follow-up

- Ticket 14 must define and implement the long-term OHLCV history-storage migration path beyond Ticket-4 transitional SQLite OHLCV persistence.

## Ticket 5 unresolved-field carry-forward

The following fields remain unresolved and are intentionally not implemented in Ticket 5:
- `bars_since_last_volume_shift_event`
- `dist_to_base_mid_pct`
- `distance_to_range_high_pct_abs`

Consequence note:

> Two of four inputs for `freshness_distance_structural` currently lack authoritative definitions (`distance_to_range_high_pct_abs`, `bars_since_last_volume_shift_event`). Until resolved, the axis operates at minimum viable input coverage using the two defined inputs under the Missing-Data rules from Abschnitt 1.
