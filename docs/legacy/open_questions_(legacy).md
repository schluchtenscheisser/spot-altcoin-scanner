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

Resolved by Ticket `2026-04-18__P0__feature_bundle_gap_fill_t5_1`:
- `bars_since_last_volume_shift_event` resolved as `bars_since_last_volume_shift_4h` in `RawFeatures4H`.
- `distance_to_range_high_pct_abs` resolved as `distance_to_range_high_pct_abs` in `RawFeatures4H` (rolling high window uses configurable 4h lookback and high as denominator).
- `freshness_distance_structural` input coverage is now 4/4 via `FeatureBundle`.

The following fields remain unresolved and are intentionally not implemented in Ticket 5:
- `dist_to_base_mid_pct`

Consequence note:

> `dist_to_base_mid_pct` remains without authoritative formula. The related `expansion_progress_structural` subscore stays absent and the axis uses weight-dropout re-normalization with `expansion_progress_structural_reduced_resolution = true`.

## Ticket 6 unresolved carry-forward

- `dist_to_base_mid_pct` remains unresolved.
- Consequence: `expansion_progress_structural` uses reduced resolution with weight-dropout as long as this input is unresolved.

## Ticket 7 follow-up boundary

- Ticket 7 resolved Tier-2-Simplified axis computation and typed `Tier2AxisBundle` output.
- Ticket 8 remains responsible for phase interpretation and any cross-axis weighting policy (including Tier-1/Tier-2 interaction), which is intentionally out of scope for Ticket 7.
