# Title
[P0] Implement complete Tier-2-Simplified axis bundle (Ticket 7)

## Context / Source

This ticket implements **Ticket 7** from the Independence-Release consolidated concept: the complete Tier-2-Simplified axis layer.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 7.

`depends_on: [5, "5.1"]` — requires:
- Ticket 5 (`raw features + helper metrics`)
- Ticket 5.1 (`feature bundle gap-fill`)
- Ticket 6 (`normalization utilities`) — not as a fachlicher input contract, but because `scanner/axes/normalization.py` must exist before T7 can import from it; T7 does not consume `Tier1AxisBundle`

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements:

- the complete **Tier-2-Simplified axis bundle** — exactly three axes as defined in Abschnitt 2
- a two-path evaluation model (4h primary path / 1d fallback path) for all three axes
- a typed in-memory `Tier2AxisBundle` for downstream consumption by Ticket 8

This ticket does **not** implement:

- Tier-1 axes (Ticket 6)
- new normalization utilities — T7 reuses the utilities introduced in Ticket 6 (`scanner/axes/normalization.py`)
- phase interpretation (Ticket 8)
- invalidation / cycle logic
- state machine logic
- entry logic
- ranking / decision buckets
- persistence of axis outputs
- direct OHLCV access

### Input contract boundary

Ticket 7 consumes **only** the typed Ticket-5 / T5.1 feature contract:

- `FeatureBundle` (including `RawFeatures1D`, `RawFeatures4H`, `RawFeaturesShared`)
- `cfg`

Ticket 7 does **not** consume `Tier1AxisBundle` as an input. Tier-2-Simplified axes are independent of Tier-1 axis values. T8 combines both bundles.

Ticket 7 must not access:

- OHLCV bars directly
- repositories / cache / SQLite / Parquet
- raw timestamps / `now`
- storage layers of any kind

### Interface boundary to Ticket 8

Ticket 8 (phase interpreter) will consume:

- `FeatureBundle`
- `Tier1AxisBundle` (from Ticket 6)
- `Tier2AxisBundle` (from this ticket)

Ticket 7 itself is not aware of Ticket 6 outputs. There is no feedback from T6 into T7.

### State-machine scope boundary

Ticket 7 sets axis values and axis-level flags. It does not make state-machine decisions. Consequences such as `_reduced_resolution = True → early_ready requires 4h` belong to later state-machine logic.

---

## Goal

After this ticket is completed:

- `scanner/axes/tier2.py` computes all three Tier-2-Simplified axes
- `scanner/axes/models.py` contains `Tier2AxisBundle`
- axis computation consumes only `FeatureBundle` and `cfg`
- the two-path evaluation model (4h primary / 1d fallback) is correctly implemented for all three axes
- `pullback_quality_simplified` correctly enforces the segmentation validity pre-gate
- downstream Ticket 8 can consume a typed `Tier2AxisBundle`

---

## Scope

Allowed change surface:

- `scanner/axes/tier2.py` (new)
- `scanner/axes/models.py` — add `Tier2AxisBundle` dataclass
- `scanner/config.py` or central config accessor — add `cfg.axes` sub-blocks for Tier-2 axes
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/open_questions.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope

This ticket must not:

- implement Tier-1 axes
- introduce any new normalization utility functions
- implement phase interpretation
- implement invalidation / cycle / state / entry / ranking logic
- introduce any persistence for axis outputs
- write SQLite / Parquet / file outputs
- accept OHLCV bars, raw timestamps, or `Tier1AxisBundle` as public-function inputs
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2, §19 Ticket 7
- `v2_1_abschnitt_2_tier_2_simplified_achsen_rev2.md` — **per-axis specs in this ticket supersede any independent reading of Abschnitt 2; Codex must not reconstruct axis parameters from Abschnitt 2 on its own**
- Ticket 5 / T5.1 — typed feature contract
- Ticket 6 — normalization utilities in `scanner/axes/normalization.py`

---

## Tier-2-Simplified axis set (authoritative)

Ticket 7 must implement **exactly three** Tier-2-Simplified axes from Abschnitt 2:

1. `base_integrity_simplified`
2. `pullback_quality_simplified`
3. `reacceleration_strength_simplified`

There is no fourth axis.

---

## Module and model structure (authoritative)

### Modules

- `scanner/axes/tier2.py` (new)
- `scanner/axes/models.py` (extend with `Tier2AxisBundle`)

### Public function

```python
def compute_tier2_axes(
    feature_bundle: FeatureBundle,
    cfg: Config,
) -> Tier2AxisBundle: ...
```

No separate `symbol` parameter. `symbol` is read from `feature_bundle.symbol`.

No OHLCV input, raw timestamp, `Tier1AxisBundle`, repository handle, or storage object is accepted.

---

## Output contract (authoritative)

```python
@dataclass
class Tier2AxisBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    base_integrity_simplified: Optional[float]
    base_integrity_simplified_not_evaluable: bool
    base_integrity_simplified_reduced_resolution: bool
    base_integrity_simplified_effective_weight_ratio: Optional[float]

    pullback_quality_simplified: Optional[float]
    pullback_quality_simplified_not_evaluable: bool
    pullback_quality_simplified_reduced_resolution: bool
    pullback_quality_simplified_effective_weight_ratio: Optional[float]

    reacceleration_strength_simplified: Optional[float]
    reacceleration_strength_simplified_not_evaluable: bool
    reacceleration_strength_simplified_reduced_resolution: bool
    reacceleration_strength_simplified_effective_weight_ratio: Optional[float]
```

### Bundle semantics

`Tier2AxisBundle` carries only: `symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`, the three axis values, and per-axis companion fields.

It must not carry: raw-feature fields, Tier-1 axis outputs, phase/state/entry fields, subscore breakdown objects, segmentation intermediate objects, normalization intermediate tables, storage metadata, run metadata, or OHLCV raw data.

### Null and flag semantics

- `<axis> = None` means "not evaluable", not "bad" or "low"
- `<axis> = None` must never be coerced to `0`, `False`, or any sentinel value
- `<axis>_not_evaluable = True` implies `<axis> is None`
- `<axis>_effective_weight_ratio = None` when `<axis>_not_evaluable = True`
- `<axis>_reduced_resolution = False` when `<axis>_not_evaluable = True`

---

## Feature-input availability rule (authoritative)

Identical to Ticket 6. A T5 / T5.1 field is **available and usable** exactly when:

- its value is not `None`
- **and** its companion status field is exactly `ok`

Any other combination (any non-`ok` status, or `None` value) means the input is treated as **missing**.

---

## Two-path evaluation model (authoritative)

All three Tier-2-Simplified axes follow this path-selection logic. This is evaluated **before** any scoring.

### Path selection

1. **If `data_4h_available = True`**: attempt the 4h primary path.
2. **If `data_4h_available = False`**: attempt the 1d fallback path.

There is **no automatic fallthrough from 4h to 1d** when `data_4h_available = True`. If 4h data is available but individual 4h sub-inputs are missing, the 4h path continues with standard weight-dropout. If `effective_weight_ratio` falls below `cfg.axes.min_effective_weight_ratio`, the axis is `not_evaluable` — the 1d fallback is not attempted.

### Within the selected path

Standard weight-dropout applies: missing sub-inputs are removed, remaining weights are re-normalized, `effective_weight_ratio` is computed before re-normalization. If `effective_weight_ratio` falls below `cfg.axes.min_effective_weight_ratio`:

- `<axis> = None`
- `<axis>_not_evaluable = True`

### Reduced-resolution rule

`_reduced_resolution = True` is set whenever the axis is computed with fewer inputs than the full original set for the active path — whether due to:

- 1d fallback path being active (successful 1d fallback always sets `_reduced_resolution = True`; additional weight-dropout within the 1d path is still subject to the standard `effective_weight_ratio` floor), or
- weight-dropout within the 4h primary path

`_reduced_resolution = False` only when the 4h primary path is active **and** all inputs of that path are available and status `ok`.

### 1d fallback semantics

The 1d fallback is a spec-defined alternate computation path using 1d-specific inputs and 1d-specific normalization anchors/points. It is not a shortened-window substitute. When successful:

- `<axis>_reduced_resolution = True`
- `<axis>_not_evaluable = False`

---

## `pullback_quality_simplified` segmentation validity pre-gate (authoritative)

Before any scoring begins on the **selected path**, the T5 segmentation fields for that timeframe must yield a valid upward impulse:

```
impulse_high_price_{tf} > impulse_start_price_{tf}
```

Where `{tf}` is `4h` for the primary path and `1d` for the fallback path.

If this condition is not met (including when either field is `None` or status is not `ok`), the path is **invalid** and the axis is immediately `not_evaluable`. This is a path-validity gate, not a sub-input dropout case. No weight-dropout is applied; scoring does not begin.

For the 1d fallback path: if `data_4h_available = False` and the 1d segmentation is also invalid, the axis is `not_evaluable`.

---

## Per-axis specifications (authoritative)

**The following three sections are the authoritative implementation contract for Ticket 7. Codex must implement exactly these inputs, normalization functions, anchor/point values, and weights. Codex must not reconstruct these values from Abschnitt 2 independently.**

---

### Axis 1 — `base_integrity_simplified`

**Source: Abschnitt 2 §2.3 / §2.4**

No additional pre-gate beyond the standard two-path model.

#### Sub-input definitions — 4h primary path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `bars_since_last_new_low_4h` | `norm_piecewise_linear` | `[(0,0),(2,25),(4,50),(8,80),(12,100)]` | `0.30` |
| 2 | `range_width_12bars_4h_pct` | `norm_linear_clamped_inv` | low_good=`4`, mid=`9`, high_bad=`18` | `0.20` |
| 3 | `close_position_in_range_12bars_4h` | `norm_piecewise_linear` | `[(0.0,0),(0.25,20),(0.50,50),(0.75,80),(1.00,100)]` | `0.25` |
| 4 | `close_above_range_mid_ratio_12bars_4h` | `norm_piecewise_linear` | `[(0.00,0),(0.25,25),(0.50,50),(0.75,80),(1.00,100)]` | `0.25` |

#### Sub-input definitions — 1d fallback path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `bars_since_last_new_low_1d` | `norm_piecewise_linear` | `[(0,0),(2,35),(4,60),(7,85),(10,100)]` | `0.30` |
| 2 | `range_width_10bars_1d_pct` | `norm_linear_clamped_inv` | low_good=`8`, mid=`15`, high_bad=`30` | `0.20` |
| 3 | `close_position_in_range_10bars_1d` | `norm_piecewise_linear` | `[(0.0,0),(0.25,20),(0.50,50),(0.75,80),(1.00,100)]` | `0.25` |
| 4 | `close_above_range_mid_ratio_10bars_1d` | `norm_piecewise_linear` | `[(0.00,0),(0.25,25),(0.50,50),(0.75,80),(1.00,100)]` | `0.25` |

Original weights sum to `1.00` on both paths.

#### Aggregation

`base_integrity_simplified = weighted_mean(subscores, weights)`

---

### Axis 2 — `pullback_quality_simplified`

**Source: Abschnitt 2 §3.3 / §3.4 / §3.5**

This axis requires the segmentation validity pre-gate (defined above) before any scoring.

#### Sub-input definitions — 4h primary path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `pullback_depth_vs_last_impulse_pct_4h` | `norm_piecewise_linear` | `[(0,70),(20,100),(40,75),(60,40),(100,0)]` | `0.35` |
| 2 | `pullback_volume_ratio_4h` | `norm_piecewise_linear` | `[(0.3,100),(0.6,85),(1.0,50),(1.3,20),(1.8,0)]` | `0.25` |
| 3 | `close_vs_ema20_4h_pct` | `norm_linear_clamped` | low=`-8`, mid=`0`, high=`+8` | `0.20` |
| 4 | `lowest_low_vs_ema20_4h_pct` | `norm_linear_clamped` | low=`-10`, mid=`-2`, high=`+4` | `0.20` |

#### Sub-input definitions — 1d fallback path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `pullback_depth_vs_last_impulse_pct_1d` | `norm_piecewise_linear` | `[(0,70),(20,100),(40,75),(60,40),(100,0)]` | `0.35` |
| 2 | `pullback_volume_ratio_1d` | `norm_piecewise_linear` | `[(0.3,100),(0.6,85),(1.0,50),(1.3,20),(1.8,0)]` | `0.25` |
| 3 | `close_vs_ema20_1d_pct` | `norm_linear_clamped` | low=`-8`, mid=`0`, high=`+8` | `0.20` |
| 4 | `lowest_low_vs_ema20_1d_pct` | `norm_linear_clamped` | low=`-10`, mid=`-2`, high=`+4` | `0.20` |

Original weights sum to `1.00` on both paths.

#### Note on row 1 — non-monotone curve

The pullback-depth normalization curve `[(0,70),(20,100),(40,75),(60,40),(100,0)]` is intentionally non-monotone. A moderate pullback (~20%) is rated highest. Both zero pullback and full reversal are penalized. `norm_piecewise_linear` handles this correctly — no monotonicity requirement applies to y-values.

#### Aggregation

`pullback_quality_simplified = weighted_mean(subscores, weights)`

---

### Axis 3 — `reacceleration_strength_simplified`

**Source: Abschnitt 2 §4.3 / §4.4**

No additional pre-gate beyond the standard two-path model.

#### Sub-input definitions — 4h primary path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `close_vs_rolling_high_5_4h_pct` | `norm_linear_clamped` | low=`-4`, mid=`0`, high=`+4` | `0.35` |
| 2 | `volume_4h_current_vs_median10` | `norm_piecewise_linear` | `[(0.8,10),(1.0,40),(1.2,65),(1.5,85),(2.0,100)]` | `0.25` |
| 3 | `ema20_slope_4h_pct_per_bar` | `norm_linear_clamped` | low=`-1.0`, mid=`0`, high=`+1.0` | `0.20` |
| 4 | `close_vs_ema20_4h_pct` | `norm_linear_clamped` | low=`-6`, mid=`0`, high=`+6` | `0.20` |

#### Sub-input definitions — 1d fallback path

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `close_vs_rolling_high_5_1d_pct` | `norm_linear_clamped` | low=`-4`, mid=`0`, high=`+4` | `0.35` |
| 2 | `volume_1d_current_vs_median10` | `norm_piecewise_linear` | `[(0.8,10),(1.0,40),(1.2,65),(1.5,85),(2.0,100)]` | `0.25` |
| 3 | `ema20_slope_1d_pct_per_bar` | `norm_linear_clamped` | low=`-1.0`, mid=`0`, high=`+1.0` | `0.20` |
| 4 | `close_vs_ema20_1d_pct` | `norm_linear_clamped` | low=`-6`, mid=`0`, high=`+6` | `0.20` |

Original weights sum to `1.00` on both paths.

#### Correlation note

`reacceleration_strength_simplified` shares inputs with `trend_strength` (Tier-1): `ema20_slope_*` and `close_vs_ema20_*`. This is intentional per Abschnitt 2 §4.6. The resulting correlation between axes is addressed in Ticket 8 (phase interpreter) through weights, not here.

#### Aggregation

`reacceleration_strength_simplified = weighted_mean(subscores, weights)`

---

## Config contract (authoritative)

All configurable parameters must be sourced exclusively from the Ticket-1 config object.

### Root key

```python
cfg.axes
```

Shared with Ticket 6. The `min_effective_weight_ratio` key defined in Ticket 6 applies to T7 as well.

### Per-axis anchor blocks

```python
cfg.axes.base_integrity_simplified
cfg.axes.pullback_quality_simplified
cfg.axes.reacceleration_strength_simplified
```

The default values for all anchor / point parameters are exactly as defined in the per-axis specifications above.

### Merge semantics

Identical to Ticket 6: partial overrides merged field-by-field with canonical defaults. Missing subkeys are not invalid. Invalid values raise `ValueError` at config-validation time.

Ticket 7 introduces no new root-level config keys. All axis parameters live under `cfg.axes.<axis_name>`.

---

## Acceptance Criteria (deterministic)

1. `scanner/axes/tier2.py` and updated `scanner/axes/models.py` exist.
2. `compute_tier2_axes(feature_bundle, cfg)` is the sole public entry point. No `symbol` parameter, no `Tier1AxisBundle`, no OHLCV, no storage.
3. `Tier2AxisBundle` exists with exactly the fields defined in this ticket.
4. Ticket 7 implements exactly three Tier-2-Simplified axes.
5. No new normalization utility functions are introduced. T7 imports from `scanner/axes/normalization.py`.
6. The two-path model is correctly implemented: `data_4h_available = True` → 4h path only; `data_4h_available = False` → 1d fallback. No automatic fallthrough from 4h to 1d.
7. `_reduced_resolution = True` whenever the axis is computed with fewer than the full original input set — including 1d fallback path and 4h dropout.
8. `pullback_quality_simplified` segmentation validity pre-gate is enforced before scoring on both paths.
9. All per-axis inputs, utilities, parameters, and weights match this ticket exactly.
10. A T5/T5.1 input is treated as available only when `value != None` and companion status `== ok`.
11. `null` axis values are not coerced to `0`, `False`, or sentinel values.
12. `not_evaluable = True` implies `<axis> is None`.
13. All config values sourced from `cfg.axes` only.
14. Canonical docs updated in the same PR.
15. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` not manually edited.
16. One ticket = one PR.

---

## Tests (required)

### Category A — Two-path mechanism (all three axes)

#### A1 — 4h primary path, all inputs present
- Fixture: `data_4h_available = True`, all 4h sub-inputs available and status `ok`
- Expected: axis computed, `_reduced_resolution = False`, `_not_evaluable = False`, `_effective_weight_ratio = 1.0`

#### A2 — 1d fallback triggered by `data_4h_available = False`
- Fixture: `data_4h_available = False`, all 1d sub-inputs available and status `ok`
- Expected: axis computed, `_reduced_resolution = True`, `_not_evaluable = False`

#### A3 — No fallthrough to 1d when 4h available but one sub-input missing
- Fixture: `data_4h_available = True`, one 4h sub-input null/non-ok, 1d inputs also available
- Expected: T7 stays on 4h path. If `effective_weight_ratio >= floor`: axis computed, `_reduced_resolution = True`, `_not_evaluable = False`. If `effective_weight_ratio < floor`: `not_evaluable = True`. In neither case is the 1d path used.

#### A4 — Both paths fail
- Fixture: `data_4h_available = False`, all 1d sub-inputs null/non-ok
- Expected: `<axis> = None`, `_not_evaluable = True`, `_effective_weight_ratio = None`

### Category B — `pullback_quality_simplified` segmentation pre-gate

#### B1 — Valid 4h impulse, gate passes
- `impulse_high_price_4h > impulse_start_price_4h`, status `ok` for both, all other 4h inputs ok
- Expected: gate passes, axis computed

#### B2 — Invalid 4h impulse, `data_4h_available = True`
- `impulse_high_price_4h <= impulse_start_price_4h`, `data_4h_available = True`
- Expected: immediate `not_evaluable = True`. No dropout, no 1d fallback attempt.

#### B3 — Invalid 4h impulse, 1d fallback triggered and valid
- `data_4h_available = False`, `impulse_high_price_1d > impulse_start_price_1d`, all 1d inputs ok
- Expected: `_reduced_resolution = True`, axis computed

#### B4 — Invalid 4h impulse, 1d fallback also invalid
- `data_4h_available = False`, `impulse_high_price_1d <= impulse_start_price_1d`
- Expected: `not_evaluable = True`

#### B5 — Segmentation field null
- `impulse_high_price_4h` is `None` or status not `ok`, `data_4h_available = True`
- Expected: gate fails, `not_evaluable = True`

### Category C — Normalization reuse and non-monotone curve

#### C1 — T7 uses normalization utilities from T6
- T7 imports `norm_linear_clamped`, `norm_linear_clamped_inv`, `norm_piecewise_linear`, `weighted_mean` from `scanner/axes/normalization.py`
- `scanner/axes/tier2.py` contains no local reimplementations of these functions

#### C2 — Non-monotone pullback-depth curve
- `x=0` → `70.0`; `x=20` → `100.0`; `x=40` → `75.0`; `x=60` → `40.0`; `x=100` → `0.0`
- Intermediate: `x=10` → `85.0` (midpoint between (0,70) and (20,100))
- Confirms `norm_piecewise_linear` handles non-monotone y-sequences correctly

### Category D — Per-axis golden fixtures

For each of the three axes:

#### D1 — Full 4h golden
- All 4h sub-inputs explicitly authored, expected output manually precomputed (not copied from implementation)
- Must yield: `_not_evaluable = False`, `_reduced_resolution = False`, `_effective_weight_ratio = 1.0`

#### D2 — Full 1d fallback golden
- `data_4h_available = False`, all 1d sub-inputs set, expected output manually precomputed
- Must yield: `_not_evaluable = False`, `_reduced_resolution = True`

#### D3 — Dropout golden within 4h path
- One 4h sub-input missing, remaining weights re-normalized, expected output precomputed
- `_effective_weight_ratio < 1.0`, `_reduced_resolution = True`

### Category E — Output contract

- `compute_tier2_axes(feature_bundle, cfg)` returns `Tier2AxisBundle`
- `symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available` correctly copied from `FeatureBundle`
- All three axes and all companion fields present
- No storage access during execution
- Identical `feature_bundle` + identical `cfg` → identical `Tier2AxisBundle` (determinism)
- `not_evaluable = True` implies `<axis> is None` — no counter-examples permitted
- `Tier2AxisBundle` contains no Tier-1 fields, no segmentation intermediate objects, no OHLCV raw data

### Category F — Config

- Missing `cfg.axes` sub-block for a Tier-2 axis → defaults apply, no error
- Missing nested anchor key → default applies, no error
- Malformed point list / impossible anchor order → `ValueError` at config validation
- T7 introduces no new root-level config keys

---

## Definition of Done (non-test AC items)

- `docs/canonical/ARCHITECTURE.md` updated with `scanner/axes/tier2.py` and `Tier2AxisBundle`
- `docs/canonical/DATA_MODEL.md` updated with `Tier2AxisBundle` contract
- `docs/canonical/GLOSSARY.md` updated with Tier-2-Simplified axis names and `_simplified` semantics
- `docs/canonical/VERIFICATION_FOR_AI.md` updated with:
  - three Tier-2-Simplified axis names and their FeatureBundle input fields (both paths)
  - two-path evaluation model
  - `pullback_quality_simplified` segmentation pre-gate
  - `_reduced_resolution` semantics (covers both 1d fallback and 4h dropout)
  - non-monotone curve note

---

## Constraints / Invariants

- [ ] T7 consumes only `FeatureBundle` and `cfg`; no `Tier1AxisBundle` input
- [ ] T7 does not access OHLCV or storage
- [ ] T7 implements exactly three Tier-2-Simplified axes
- [ ] No new normalization utility functions introduced
- [ ] Two-path model: no automatic fallthrough from 4h to 1d when `data_4h_available = True`
- [ ] `_reduced_resolution = True` on 1d fallback path and on 4h dropout; `False` only when 4h path runs with all inputs present
- [ ] `pullback_quality_simplified` segmentation gate enforced before scoring on both paths
- [ ] Tier-1 axes, phase, state, entry, ranking remain out of scope
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`
- [ ] One ticket = one PR

---

## Definition of Done (Codex must satisfy)

(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Ticket moved to `docs/tickets/_in_progress/` at start
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` per this ticket
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` in the same PR
- [ ] Added / updated tests per this ticket
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-19T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [5, "5.1"]
gesamtkonzept_ref: "§19 Ticket 7"
related_issues: []
follow_ups:
  - "Ticket 8: implement phase interpreter using FeatureBundle + Tier1AxisBundle + Tier2AxisBundle"
```
