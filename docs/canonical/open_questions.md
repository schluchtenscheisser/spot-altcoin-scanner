# Open Questions — Independence-Release Bootstrap (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OPEN_QUESTIONS
status: canonical
```

## Purpose
This file tracks authoritative open questions that remain unresolved in the current Independence-Release architecture and therefore must not be silently decided by later implementation tickets.

## Bootstrap rule
Until an open question listed here is resolved in canonical documentation, later tickets and implementations must not silently invent business-logic answers for it.

## Open questions

### 1) `dist_to_base_mid_pct` remains unresolved

**Context**

The field `dist_to_base_mid_pct` was identified during the Ticket-5 / Ticket-5.1 / Ticket-6 workstream as a required input for `expansion_progress_structural`, but no authoritative formula was found in the governing specifications.

The field name and descriptive intent exist, but the architecture still lacks a canonical definition for:

- what exactly the “base mid” is,
- which historical range/base it refers to,
- how that base is selected,
- and the exact formula for converting it into `dist_to_base_mid_pct`.

**Why this matters**

Without an authoritative formula, independent implementations may invent incompatible meanings for the same field, causing divergence in:

- Tier-1 axis computation,
- diagnostics and explainability,
- later runner/state interpretation,
- backtest comparability.

**Current consequence**

`expansion_progress_structural` must continue to treat this sub-input as absent.

The related subscore remains unavailable, and the axis continues to rely on canonical weight-dropout / re-normalization with:

- `expansion_progress_structural_reduced_resolution = true`

for as long as `dist_to_base_mid_pct` has no authoritative formula.

**Still to decide**

A future canonical resolution must define:

1. the authoritative base-selection rule,
2. the exact mathematical formula,
3. whether any lookback/config parameter is involved,
4. and which module owns the computation contract.

---

### 2) Long-term OHLCV history storage path beyond Ticket 4 transitional SQLite persistence

**Context**

Ticket 4 explicitly introduced SQLite-backed OHLCV persistence as a transitional implementation. The long-term architecture still expects a durable historical-storage migration path beyond this interim state.

**Why this matters**

Later layers may otherwise incorrectly assume that current SQLite OHLCV persistence is permanent, which would blur the boundary between:

- transitional runtime persistence,
- long-term historical storage,
- and future history/research/export workflows.

**Still to decide / implement**

Ticket 14 (or equivalent canonical follow-up) must define and implement the long-term OHLCV history-storage target and migration path, including:

- the authoritative storage layer for bulk OHLCV history,
- the ownership of migration from transitional SQLite persistence,
- downstream reader expectations after migration,
- and any canonical doc/schema updates required by that migration.

Until then, current OHLCV persistence must continue to be treated as transitional rather than final.

---

### 3) `daily_bar_id` type consistency across Independence-Release layers

**Context**

There is an unresolved cross-layer type inconsistency around `daily_bar_id` in the current Independence-Release implementation/contracts:

- Ticket 1 / bar-clock semantics define `daily_bar_id(t)` canonically as a string in `YYYY-MM-DD` format.
- Current internal typed layer models were implemented with `daily_bar_id: int` in multiple places, including:
  - `Tier1AxisBundle`
  - `Tier2AxisBundle`
  - `PhaseInterpretationBundle`
- Output/report/schema validation currently still treats `daily_bar_id` canonically as a string in `YYYY-MM-DD` format.

This means the architecture currently exposes two competing representations:

- internal bundle-layer representation: `int`
- canonical output/schema representation: `str` (`YYYY-MM-DD`)

**Why this matters**

If this remains unresolved, later runner / integration / diagnostics work may silently introduce:

- ad hoc conversions between `int` and `str`,
- inconsistent typed contracts across layers,
- schema friction between in-memory bundles and output artifacts,
- avoidable bugs in reporting, persistence boundaries, diagnostics, or runner integration.

This is especially relevant before broader integration tickets finalize cross-layer boundaries.

**Open question**

What is the canonical type of `daily_bar_id` across the Independence-Release architecture?

**Decision options**

1. **Canonicalize on string (`YYYY-MM-DD`) everywhere**
   - aligns directly with bar-clock output,
   - simplifies report/output contracts,
   - avoids dual representations.

2. **Allow internal non-string representation, but require an explicit boundary conversion**
   - internal bundles may use a non-string representation for technical reasons,
   - but canonical docs must define exactly:
     - where conversion happens,
     - which module owns it,
     - and which layers are allowed to see which representation.

**Required before / during later integration work**

Before later runner/integration/output work is finalized, canonical docs should explicitly decide:

- the cross-layer canonical type of `daily_bar_id`,
- whether any internal exception is allowed,
- if yes: which boundary owns conversion to canonical string form,
- and which typed models/docs/schemas must be harmonized.

**Current recommendation**

Prefer a single canonical representation unless there is a strong technical reason not to. If dual representation is retained, the conversion boundary must be explicit, documented, and tested.
