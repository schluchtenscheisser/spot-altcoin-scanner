> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] T5.1 addendum: add `close_vs_high20_4h_pct` to RawFeatures4H

## Context / Source

This ticket is a **narrow addendum to Ticket 5.1**. It adds one missing field to `RawFeatures4H` that was identified as a T6 prerequisite during Ticket 6 review.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 5 / Ticket 6.

`depends_on: ["5.1"]` — requires:
- Ticket 5.1 (`feature bundle gap-fill: structural-break anchor naming and missing deterministic helper fields`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Why this ticket exists

Ticket 6 (`tier1_axes`) requires `close_vs_high20_4h_pct` as a `RawFeatures4H` FeatureBundle field for the `reclaim_progress` axis (structural anchor distance sub-input). Both upstream values needed for this computation — `close_4h` (most recent closed 4h bar close) and `fixed_structural_break_anchor_4h` — are already present in `RawFeatures4H` after T5.1.

The field was not part of T5.1's original scope. Ticket 6 explicitly requires it as a FeatureBundle output and forbids computing it locally within T6. This ticket closes that gap before T6 executes.

This ticket does **not**:

- change the T5.1 architecture, module structure, or public function signatures
- add any axis, phase, state, or entry logic
- introduce any persistence, file output, or storage access
- re-open any other T5 or T5.1 decisions

---

## Goal

After this ticket is completed:

- `RawFeatures4H` contains `close_vs_high20_4h_pct` with a companion status field
- Ticket 6 can consume this field from the FeatureBundle without accessing raw prices or computing it locally
- `docs/canonical/VERIFICATION_FOR_AI.md` reflects the updated `RawFeatures4H` contract

---

## Scope

Allowed change surface:

- `scanner/features/raw_4h.py` — add computation of `close_vs_high20_4h_pct`
- `scanner/features/models.py` — add field and companion status to `RawFeatures4H`
- `tests/**` — add tests specified below
- `docs/canonical/VERIFICATION_FOR_AI.md`

This ticket must not touch:

- `scanner/features/raw_1d.py`
- `scanner/features/shared.py`
- `scanner/features/bundle.py`
- `scanner/axes/` (does not exist yet)
- any storage, persistence, or repository layer
- any axis, phase, state, or entry logic
- `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Field definition (authoritative)

### Field

```python
# in RawFeatures4H
close_vs_high20_4h_pct: Optional[float]
close_vs_high20_4h_pct_status: str  # closed T5 status enum
```

### Formula

```python
close_vs_high20_4h_pct = (
    (close_4h / fixed_structural_break_anchor_4h) - 1
) * 100
```

Where:
- `close_4h` is the close of the most recent completed 4h bar
- `fixed_structural_break_anchor_4h` is the existing T5.1 field in `RawFeatures4H`

### Failure cases

All failure cases follow the closed T5 status enum. No new status values are introduced.

| Condition | Value | Status |
|---|---|---|
| `fixed_structural_break_anchor_4h` is `None` or its status is not `ok` | `null` | `upstream_dependency_null` |
| `fixed_structural_break_anchor_4h == 0` | `null` | `invalid_upstream_value` |
| `fixed_structural_break_anchor_4h` is `NaN`, `inf`, or `-inf` | `null` | `invalid_upstream_value` |
| `close_4h` is `NaN`, `inf`, or `-inf` | `null` | `invalid_upstream_value` |
| All inputs valid and non-zero | computed float | `ok` |

### Result range

The result is a signed percentage. It can be negative (close below anchor), zero (close at anchor), or positive (close above anchor). No clamping is applied at this layer — normalization is T6's responsibility.

### Downstream note

Ticket 6 treats this field identically to all other FeatureBundle inputs: available only when `value != None` and companion status `== ok`. If unavailable, the 4h fixed structural anchor score in `reclaim_progress` is absent and its weight (0.20 at Level 2) is dropped per the standard weight-dropout rule.

---

## Numeric robustness rules (authoritative)

Standard T5 rules apply:

- `NaN`, `inf`, `-inf` in any required input → `null` + `invalid_upstream_value`
- upstream field unavailable or non-ok → `null` + `upstream_dependency_null`
- division by zero (`fixed_structural_break_anchor_4h == 0`) → `null` + `invalid_upstream_value`
- `null` must not be coerced to `0`, `false`, or any sentinel value

---

## Required tests (authoritative)

### T1 — Standard case
Given a fixture where `close_4h = 1.05` and `fixed_structural_break_anchor_4h = 1.00` (both with status `ok`):
- assert `close_vs_high20_4h_pct ≈ 5.0`
- assert status `ok`

### T2 — Negative result
Given `close_4h = 0.95`, `fixed_structural_break_anchor_4h = 1.00`:
- assert `close_vs_high20_4h_pct ≈ -5.0`
- assert status `ok`

### T3 — Anchor unavailable
Given `fixed_structural_break_anchor_4h = None` (or status not `ok`):
- assert `close_vs_high20_4h_pct = None`
- assert status `upstream_dependency_null`

### T4 — Anchor is zero
Given `fixed_structural_break_anchor_4h = 0.0`:
- assert `close_vs_high20_4h_pct = None`
- assert status `invalid_upstream_value`

### T5 — Non-finite anchor
Given `fixed_structural_break_anchor_4h = float('inf')`:
- assert `close_vs_high20_4h_pct = None`
- assert status `invalid_upstream_value`

### T6 — Non-finite close
Given `close_4h = float('nan')`:
- assert `close_vs_high20_4h_pct = None`
- assert status `invalid_upstream_value`

### T7 — Field presence
- assert `RawFeatures4H` dataclass contains `close_vs_high20_4h_pct` and `close_vs_high20_4h_pct_status`
- assert both fields are present in the assembled `FeatureBundle` via `build_feature_bundle`

---

## Codex implementation guardrails

- **No new architecture:** This field follows the identical pattern as all other T5/T5.1 fields in `raw_4h.py`. No new computation patterns, no new abstractions.
- **No persistence:** Output is run-local in-memory only.
- **Closed status enum:** Only the five existing T5 status values are used. Do not introduce new status values.
- **`null` must not collapse to `0` or `false`:** `None` in Python, preserved as `None`.
- **Not-evaluable ≠ negative:** A `null` result with `upstream_dependency_null` does not mean the value is low or unfavorable. T6 handles that distinction.
- **One ticket = one PR.**
- **Docs in same PR:** `docs/canonical/VERIFICATION_FOR_AI.md` must be updated in the same PR.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**

---

## Authority statement

If the authoritative source set (7 v2.1 section files + `independence_release_gesamtkonzept_final.md`), existing repo canonical docs, and existing code conflict, the authoritative source set wins. This ticket does not create a second competing documentary authority.

---

## Metadata

```yaml
created_utc: "2026-04-19T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: ["5.1"]
gesamtkonzept_ref: "§2.2, §19 Ticket 5"
related_issues:
  - "T5.1: feature bundle gap-fill"
  - "T6: tier1 axes — requires this field as FeatureBundle input for reclaim_progress"
follow_ups:
  - "Ticket 6: tier1 axes and normalization utilities"
```
