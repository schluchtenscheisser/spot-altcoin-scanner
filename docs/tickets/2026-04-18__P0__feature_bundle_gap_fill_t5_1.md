# Title
[P0] Feature bundle gap-fill: structural-break anchor naming consolidation and missing deterministic helper fields (T5.1)

## Context / Source

This ticket is a **narrow gap-fill on top of Ticket 5**. It does not introduce a new feature-layer architecture; it corrects one naming inconsistency and adds two deterministic OHLCV-lookback helper fields that Ticket 5 explicitly deferred.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 5 / Ticket 6.

`depends_on: [5]` — requires:
- Ticket 5 (`raw features + helper metrics`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Why this ticket exists

Ticket 5 explicitly deferred the following items to `docs/canonical/open_questions.md`:

- `bars_since_last_volume_shift_event` — no implementation, no authoritative field name
- `distance_to_range_high_pct_abs` — no implementation, no window definition
- Naming duplication: `fixed_structural_break_anchor_4h` and `fixed_high20_break_anchor_4h` were both listed as MVP fields in Ticket 5, but they refer to the same value.

These gaps block Ticket 6 (Tier-1 axes), which must consume these fields from the `FeatureBundle` rather than fetching OHLCV directly. T5.1 resolves the gaps so that Ticket 6's input contract can be stated cleanly as "FeatureBundle only."

This ticket does **not**:

- change the overall Ticket-5 architecture, module structure, or public function signatures
- introduce any new persistence, file output, or storage access
- implement any axis, phase, invalidation, cycle, or state logic
- introduce any changes to Ticket 4
- add any additional field families beyond the three items listed above

### Addendum / working-context checks

- **A.2 Schichtenarchitektur** — all new fields remain within `scanner/features/` and do not introduce any axis/phase/state logic or bleed across layer boundaries.
- **A.5 Persistenz ist fachlicher Kern** — T5.1 outputs remain run-local in-memory objects, not persisted.

---

## Goal

After this ticket is completed:

- `fixed_high20_break_anchor_4h` is removed from the public `RawFeatures4H` contract. `fixed_structural_break_anchor_4h` is the sole canonical name.
- `bars_since_last_volume_shift_4h` is a named field in `RawFeatures4H` with a companion status field, computed from the existing `volume_quote_spike_4h` output using the canonical threshold and a new configurable lookback.
- `distance_to_range_high_pct_abs` is a named field in `RawFeatures4H` with a companion status field, computed over a configurable N-bar rolling high.
- `docs/canonical/open_questions.md` is updated: the two previously deferred fields are closed as resolved. The `dist_to_base_mid_pct` entry remains open.
- `docs/canonical/GLOSSARY.md` and `docs/canonical/DATA_MODEL.md` reflect the naming consolidation and the two new fields.
- `docs/canonical/VERIFICATION_FOR_AI.md` is updated to reflect the updated `RawFeatures4H` contract.
- Ticket 6 can state its input contract as "FeatureBundle only, as amended by T5.1" without requiring direct OHLCV access.

---

## Scope

Allowed change surface:

- `scanner/features/raw_4h.py` — add two new fields, remove deprecated field
- `scanner/features/models.py` — update `RawFeatures4H` dataclass
- `scanner/config.py` or central config accessor — add two new config keys under `cfg.features`
- `tests/**` — add tests specified below
- `docs/canonical/open_questions.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

This ticket must not touch:

- `scanner/features/raw_1d.py`
- `scanner/features/shared.py`
- `scanner/features/bundle.py`
- `scanner/axes/` (does not exist yet)
- any storage, persistence, or repository layer
- any axis, phase, state, or entry logic

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2, §19
- `v2_1_abschnitt_1_tier_1_achsen_rev2.md` — especially §5.2 (structural break definition), §6.2 (volume spike), §7.2 (freshness inputs)
- Ticket 5 — current `RawFeatures4H` contract and field-naming decisions

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

---

## Change 1 — Naming consolidation: remove `fixed_high20_break_anchor_4h`

### Background

Ticket 5's MVP field list included both:

- `fixed_structural_break_anchor_4h`
- `fixed_high20_break_anchor_4h`

These are not two distinct fields. Both refer to the same computed value: the `rolling_high_20_4h` that was in effect at the time the last structural break event `t_break` occurred (as defined in v2.1 Abschnitt 1 §5.2).

Having two names for the same value in the public output contract is a defect that would cause Ticket 6 to introduce duplicate or inconsistent references.

### Resolution

`fixed_structural_break_anchor_4h` is the sole canonical name in the public `RawFeatures4H` contract.

`fixed_high20_break_anchor_4h` is removed from:

- `RawFeatures4H` dataclass
- all tests that reference it by the deprecated name
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

The alias must not survive in any form in the public contract. Any internal variable in `raw_4h.py` that used the deprecated name during the structural break scan must be renamed to `fixed_structural_break_anchor_4h` or a clearly-internal local variable name.

### Downstream impact note

Ticket 6 (and all later tickets) must reference only `fixed_structural_break_anchor_4h`. `reclaim_progress` (Abschnitt 1 §3) refers to "fixed high20 break anchor" in spec prose — that spec prose maps to the canonical field `fixed_structural_break_anchor_4h`.

---

## Change 2 — New field: `bars_since_last_volume_shift_4h`

### Spec mapping

This field corresponds to `bars_since_last_volume_shift_event` in v2.1 Abschnitt 1 §7.2 (input to `freshness_distance_structural`). The canonical implementation name is `bars_since_last_volume_shift_4h`.

This name mapping must be documented in GLOSSARY.md:

> `bars_since_last_volume_shift_4h` implements the spec field `bars_since_last_volume_shift_event` from Abschnitt 1 §7.2.

### Algorithm

Scan backwards over the last `cfg.features.volume_shift_lookback_4h` completed 4h bars.

For each bar `t` (backwards from the most recent closed bar), check:

```
volume_quote_spike_4h[t] >= cfg.volume.persistence_spike_threshold
```

`volume_quote_spike_4h` is an existing T5 output in `RawFeatures4H`. `cfg.volume.persistence_spike_threshold` is an existing config key defined in Ticket 5. No new threshold key is introduced.

Return value:

- If the most recent qualifying bar is found at offset `k` from the current closed bar (where `k = 0` means the most recent closed bar): return `k`
- If no qualifying bar exists within the lookback window but sufficient history is available: return `volume_shift_lookback_4h` (i.e., cap at the window boundary)
- If fewer than `volume_shift_lookback_4h` completed 4h bars exist in history: return `null` with status `insufficient_history`

### Semantics of "no event found"

When a full lookback window is available but contains no qualifying bar, the value is `volume_shift_lookback_4h` with status `ok`. This is consistent with the closed T5 status enum and correctly maps to the `freshness_distance_structural` normalization: a high integer value indicates a structurally stale or inactive setup and receives a high score (inverse: recent = lower bars count = fresher = lower score pre-inversion — note that the piecewise normalization in Abschnitt 1 §7.3C maps `0→0, 6→100`, so **higher bars count = less fresh = higher normalized score**). No new status value is required.

### Field definition

```python
# in RawFeatures4H
bars_since_last_volume_shift_4h: Optional[int]
bars_since_last_volume_shift_4h_status: str  # closed T5 status enum
```

Companion status values follow the closed T5 enum exactly:

| Status | Condition |
|---|---|
| `ok` | Full lookback window available; value is either an integer ≥ 0 or `volume_shift_lookback_4h` if no event found |
| `insufficient_history` | Fewer than `cfg.features.volume_shift_lookback_4h` completed 4h bars available |
| `upstream_dependency_null` | `volume_quote_spike_4h` is null for the bar being inspected |

No other status values are permitted.

### Config

```python
cfg.features.volume_shift_lookback_4h: int = 120  # ~30 days of 4h bars
```

This is a new key under `cfg.features`. Partial override follows the T5 merge rule: missing subkeys default to the canonical default; an invalid type raises `ValueError` at config validation time.

The existing `cfg.volume.persistence_spike_threshold` is reused unchanged. No second threshold key is introduced.

---

## Change 3 — New field: `distance_to_range_high_pct_abs`

### Spec mapping

This field corresponds to `distance_to_range_high_pct_abs` in v2.1 Abschnitt 1 §7.2 (input to `freshness_distance_structural`). The name is identical in spec and implementation.

### Algorithm

```python
rolling_high_N_4h = max(high[t] for last N completed 4h bars)

distance_to_range_high_pct_abs = abs(
    (rolling_high_N_4h - close_4h) / rolling_high_N_4h
) * 100
```

`N = cfg.features.range_high_lookback_4h`

The denominator is `rolling_high_N_4h` (the High, not the current Close). This avoids denominator instability near the high and consistently measures the downside distance from the range peak.

### Numeric special cases

- `rolling_high_N_4h == 0`: field = `null`, status = `invalid_upstream_value`
- Any bar in the required window contains non-finite OHLCV values: field = `null`, status = `invalid_upstream_value`
- Fewer than N completed 4h bars: field = `null`, status = `insufficient_history`

`abs(...)` ensures the result is always non-negative. A `close_4h` above `rolling_high_N_4h` (e.g., from a new high bar) yields a value > 0 and is valid.

### Field definition

```python
# in RawFeatures4H
distance_to_range_high_pct_abs: Optional[float]
distance_to_range_high_pct_abs_status: str  # closed T5 status enum
```

### Config

```python
cfg.features.range_high_lookback_4h: int = 20  # ~5 days of 4h bars
```

New key under `cfg.features`. Same merge / validation rule as above.

---

## Consequence for downstream Tier-1 axes

After T5.1, `freshness_distance_structural` (Abschnitt 1 §7) has all four of its required inputs defined and present in the FeatureBundle:

| Spec input name | FeatureBundle field | Status after T5.1 |
|---|---|---|
| `distance_to_last_structural_anchor_pct_abs` | same | T5 ✅ |
| `distance_to_range_high_pct_abs` | same | T5.1 ✅ |
| `bars_since_last_volume_shift_event` | `bars_since_last_volume_shift_4h` | T5.1 ✅ |
| `bars_since_last_structural_break_event` | `bars_since_last_structural_break_4h` | T5 ✅ |

`expansion_progress_structural` (Abschnitt 1 §5) still has one unresolved input: `dist_to_base_mid_pct`. This field has no authoritative formula in the spec. Until resolved, the corresponding subscore is absent and the axis operates under the standard weight-dropout / re-normalization rule from Abschnitt 1 §1.6, with `expansion_progress_structural_reduced_resolution = true`. This is documented in `open_questions.md`.

---

## Numeric robustness rules (authoritative)

All T5 numeric robustness rules apply unchanged to the new fields:

- `NaN`, `inf`, `-inf` in any input bar → field = `null`, status = `invalid_upstream_value`
- Division by zero or quasi-zero denominator → field = `null`, status = `invalid_upstream_value`
- Upstream derived field is `null` → field = `null`, status = `upstream_dependency_null`
- `null` output must not be coerced to `0`, `false`, or any sentinel numeric value

---

## Config rules (authoritative)

Two new config keys are introduced under `cfg.features`:

```python
cfg.features.volume_shift_lookback_4h: int  # default 120
cfg.features.range_high_lookback_4h: int    # default 20
```

Partial overrides of `cfg.features` are merged field-by-field with canonical defaults. Missing subkeys do not count as invalid. An invalid type or out-of-range value (e.g., `<= 0`) raises `ValueError` at config validation time, not silently.

`cfg.volume.persistence_spike_threshold` is not duplicated. The new scan reads it from its existing location.

---

## `open_questions.md` updates (authoritative)

### Close as resolved

The following items from Ticket 5's `open_questions.md` entries are now resolved and must be marked as such:

> `bars_since_last_volume_shift_event` — resolved in T5.1 as `bars_since_last_volume_shift_4h` in `RawFeatures4H`.

> `distance_to_range_high_pct_abs` — resolved in T5.1 as `distance_to_range_high_pct_abs` in `RawFeatures4H` using a configurable N-bar rolling high on 4h, with High as denominator.

> Note from T5 that `freshness_distance_structural` had only 2/4 inputs — resolved: all 4 inputs are now defined and present in the FeatureBundle after T5.1.

### Keep as open

> `dist_to_base_mid_pct` — no authoritative formula in v2.1 Abschnitt 1 for "midpoint of the last structural base/range." Until resolved, the `dist_to_base_mid_pct` subscore of `expansion_progress_structural` is absent. The axis operates on its remaining 3 components under the weight-dropout rule from Abschnitt 1 §1.6. Flag: `expansion_progress_structural_reduced_resolution = true`.

---

## Required tests (authoritative)

Each item below requires at least one explicitly written test case. "Test the field" or "test the config" is not sufficient.

### A — Naming consolidation

- `RawFeatures4H` does not contain a field named `fixed_high20_break_anchor_4h` (negative membership test)
- `RawFeatures4H` contains a field named `fixed_structural_break_anchor_4h`
- Any code path that previously populated `fixed_high20_break_anchor_4h` now populates `fixed_structural_break_anchor_4h` with the same value on a known fixture input

### B — `bars_since_last_volume_shift_4h`

- **Event found in lookback:** Given a fixture 4h bar sequence where the most recent qualified spike (`volume_quote_spike_4h >= threshold`) is at offset `k`, assert `bars_since_last_volume_shift_4h == k` and status `ok`
- **No event in lookback (full history available):** Given a fixture where no bar in the lookback window has a qualifying spike, assert `bars_since_last_volume_shift_4h == cfg.features.volume_shift_lookback_4h` and status `ok`
- **Insufficient history:** Given fewer than `volume_shift_lookback_4h` bars, assert value `null` and status `insufficient_history`
- **Config threshold respected:** Assert that a bar with `volume_quote_spike_4h` exactly at `persistence_spike_threshold` is treated as qualifying (boundary inclusion test)
- **Upstream null propagation:** Given a bar where `volume_quote_spike_4h` is null (status `upstream_dependency_null`), that bar is skipped in the scan (not treated as a qualifying event); the scan continues to older bars. Assert correct behavior on a fixture that has a `null` spike bar followed by a qualifying bar at offset `k+1`.

### C — `distance_to_range_high_pct_abs`

- **Standard case:** Given a fixture 4h sequence where rolling high over N bars is `H` and current close is `c`, assert computed value equals `abs((H - c) / H) * 100` within float precision tolerance
- **Close above rolling high:** Given a bar where `close > rolling_high_N_4h` (e.g., just made a new high), assert value is non-negative and status `ok`
- **Insufficient history:** Fewer than N closed 4h bars → `null` + `insufficient_history`
- **Zero rolling high:** If `rolling_high_N_4h == 0.0`, assert `null` + `invalid_upstream_value`
- **Non-finite OHLCV in window:** A bar containing `NaN` or `inf` within the N-bar window → `null` + `invalid_upstream_value`
- **Config key respected:** Assert that changing `cfg.features.range_high_lookback_4h` from 20 to 10 uses only the last 10 bars for the rolling high computation

### D — Config

- Missing `cfg.features.volume_shift_lookback_4h` → merges from default (`120`), no error
- Missing `cfg.features.range_high_lookback_4h` → merges from default (`20`), no error
- `cfg.features.volume_shift_lookback_4h = 0` → `ValueError` at config validation
- `cfg.features.range_high_lookback_4h = -5` → `ValueError` at config validation
- Partial `cfg.features` override (only one new key supplied) → other new key defaults correctly without error

### E — Contract / bundle integrity

- `RawFeatures4H` dataclass contains exactly the expected fields including both new companion status fields
- New fields are present in the assembled `FeatureBundle` via `build_feature_bundle`
- Neither new field introduces any storage write, file output, or persistence call
- `compute_raw_4h(ohlcv_4h=None, ...)` returns `None`; both new fields are absent (not `null`, not zero) because the whole 4h object is absent

### F — Docs / open questions

- `docs/canonical/open_questions.md` no longer marks `bars_since_last_volume_shift_event` or `distance_to_range_high_pct_abs` as unresolved
- `docs/canonical/open_questions.md` still contains an entry for `dist_to_base_mid_pct` with the correct consequence note for `expansion_progress_structural`
- `docs/canonical/GLOSSARY.md` contains the spec-name → field-name mappings for `bars_since_last_volume_shift_event` and `bars_since_last_structural_break_event`
- `docs/canonical/DATA_MODEL.md` does not reference `fixed_high20_break_anchor_4h`

---

## Codex implementation guardrails

- **No OHLCV re-scan architecture change:** The structural break scan in `raw_4h.py` was already present from Ticket 5. The new volume-shift scan follows the same architectural pattern: accept the pre-loaded `ohlcv_4h` bar sequence, scan in Python, return a typed value and status. No new dependencies.
- **No new persistence:** T5.1 outputs are run-local in-memory values. Do not write fields to SQLite, Parquet, or any file.
- **No public function signature changes:** `compute_raw_4h(...)` signature remains unchanged. The new fields are additional dataclass members populated inside the existing function.
- **Closed status enum:** The T5 companion status enum (`ok`, `insufficient_history`, `gap_in_required_window`, `upstream_dependency_null`, `invalid_upstream_value`) is not extended. Both new fields use only values from this closed set.
- **`null` must not collapse to `false` or `0`:** Nullable fields remain `None` in Python. No sentinel coercion.
- **Not-evaluable ≠ negative evaluation:** A `null` field with `insufficient_history` does not mean the field is low or unfavorable. Downstream T6 Missing-Data logic, not this field, handles that distinction.
- **One ticket = one PR.**
- **Docs in same PR:** All listed canonical docs must be updated in the same PR as the code changes.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**

---

## Authority statement

If the authoritative source set (7 v2.1 section files + `independence_release_gesamtkonzept_final.md`), existing repo canonical docs, and existing code conflict, the authoritative source set wins. Repo documents remain in force only insofar as they do not contradict the authoritative source set. This ticket does not create a second competing documentary authority.
