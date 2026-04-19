# Title
[P0] Implement normalization utilities and complete Tier-1 axis bundle (Ticket 6)

## Context / Source

This ticket implements **Ticket 6** from the Independence-Release consolidated concept: the normalization utilities and the complete Tier-1 axis layer.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 6.

`depends_on: [5, "5.1"]` — requires:
- Ticket 5 (`raw features + helper metrics`)
- Ticket 5.1 (`feature bundle gap-fill: structural-break anchor naming and missing deterministic helper fields`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements:

- the pure normalization utilities in `scanner/axes/normalization.py`
- the complete **Tier-1 axis bundle** — exactly six axes as defined in Abschnitt 1
- axis-level Missing-Data / weight-dropout handling
- a typed in-memory `Tier1AxisBundle` contract for downstream consumption

This ticket does **not** implement:

- Tier-2-Simplified axes (Ticket 7)
- phase interpretation (Ticket 8)
- invalidation / cycle logic
- state machine logic
- entry logic
- ranking / decision buckets
- persistence of axis outputs
- direct OHLCV access

### Ticket-5 / T5.1 contract reminder

Ticket 5 already fixed that the following belong to Ticket 6 and are **not** part of Ticket 5:

- `norm_linear_clamped`
- `norm_linear_clamped_inv`
- `norm_piecewise_linear`
- `weighted_mean`
- axis-layer Missing-Data redistribution rules

Ticket 5.1 added the following fields to `RawFeatures4H`:

- `bars_since_last_volume_shift_4h` (with companion `_status`)
- `distance_to_range_high_pct_abs` (with companion `_status`)
- consolidated `fixed_structural_break_anchor_4h` as the sole canonical anchor name (deprecated `fixed_high20_break_anchor_4h` removed)

### Input contract boundary

Ticket 6 consumes **only** the typed Ticket-5 / T5.1 feature contract:

- `FeatureBundle`
- `RawFeatures1D`
- `RawFeatures4H`
- `RawFeaturesShared`

Ticket 6 must not access:

- OHLCV bars directly
- repositories / cache / SQLite / Parquet
- raw timestamps / `now`
- storage layers of any kind

### State-machine scope boundary

Ticket 6 sets axis values and axis-level flags. It does **not** make state-machine decisions. The consequence `data_4h_available = false → early_ready not allowed` belongs to later state-machine logic, not to Ticket 6.

---

## Goal

After this ticket is completed:

- `scanner/axes/normalization.py` contains the four pure normalization utilities
- the complete Tier-1 axis set from Abschnitt 1 is implemented as typed in-memory output
- axis computation consumes only `FeatureBundle` and `cfg`
- missing / invalid feature inputs are handled via the canonical weight-dropout / reduced-resolution / not-evaluable rules
- `freshness_distance_structural` is fully computable from FeatureBundle after T5.1
- `expansion_progress_structural` remains computable under reduced resolution while `dist_to_base_mid_pct` stays unresolved
- downstream Ticket 8 can consume a typed `Tier1AxisBundle`

---

## Scope

Allowed change surface:

- `scanner/axes/normalization.py` (new)
- `scanner/axes/tier1.py` (new)
- `scanner/axes/models.py` (new)
- `scanner/axes/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.axes` defaults / merge / validation rules
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/open_questions.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope

This ticket must not:

- implement Tier-2-Simplified axes
- implement phase interpretation
- implement invalidation / cycle / state / entry / ranking logic
- introduce any persistence for axis outputs
- write SQLite / Parquet / file outputs
- accept OHLCV bars or raw timestamps as public-function inputs
- re-open Ticket-5 or T5.1 feature-layer architecture
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2, §19 Ticket 6
- `v2_1_abschnitt_1_tier_1_achsen_rev2.md` — **per-axis specs in this ticket supersede any independent reading of Abschnitt 1; Codex must not reconstruct axis parameters from Abschnitt 1 on its own**
- Ticket 5 — typed feature contract
- Ticket 5.1 — T5.1 gap-fill and naming consolidation

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

---

## Proposed change (high-level)

### Before

- Ticket 5 / T5.1 provide the typed feature-layer input contract.
- There is no canonical Tier-1 axis bundle yet.
- There is no canonical axis-layer normalization utility module yet.
- Ticket 8 cannot yet consume a stable Tier-1 output object.

### After

- `scanner/axes/normalization.py` provides the canonical pure normalization / aggregation utilities
- `scanner/axes/tier1.py` computes all six Tier-1 axes
- `scanner/axes/models.py` defines the typed `Tier1AxisBundle`
- Ticket 6 consumes only `FeatureBundle` and `cfg`
- Ticket 6 returns a typed in-memory `Tier1AxisBundle`
- Missing-Data and reduced-resolution semantics are implemented exactly as specified

---

## Tier-1 axis set (authoritative)

Ticket 6 must implement **exactly six** Tier-1 axes from Abschnitt 1:

1. `trend_strength`
2. `reclaim_progress`
3. `compression_strength`
4. `expansion_progress_structural`
5. `volume_regime_shift`
6. `freshness_distance_structural`

There is no seventh Tier-1 axis. `base_integrity_simplified` belongs to Ticket 7 (Tier-2-Simplified), not Ticket 6.

### Current unresolved dependency note

After T5.1:

- `freshness_distance_structural` is fully computable from FeatureBundle inputs
- `expansion_progress_structural` still has one unresolved sub-input: `dist_to_base_mid_pct`

Until that spec gap is resolved, `expansion_progress_structural` must support reduced resolution via canonical weight-dropout.

---

## Module and model structure (authoritative)

### Modules

- `scanner/axes/normalization.py`
- `scanner/axes/tier1.py`
- `scanner/axes/models.py`

### Public function

```python
def compute_tier1_axes(
    feature_bundle: FeatureBundle,
    cfg: Config,
) -> Tier1AxisBundle: ...
```

No separate `symbol` parameter. `symbol` is read from `feature_bundle.symbol`.

No OHLCV input, raw timestamp, repository handle, or storage object is accepted.

---

## Output contract (authoritative)

```python
@dataclass
class Tier1AxisBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    trend_strength: Optional[float]
    trend_strength_not_evaluable: bool
    trend_strength_reduced_resolution: bool
    trend_strength_effective_weight_ratio: Optional[float]

    reclaim_progress: Optional[float]
    reclaim_progress_not_evaluable: bool
    reclaim_progress_reduced_resolution: bool
    reclaim_progress_effective_weight_ratio: Optional[float]

    compression_strength: Optional[float]
    compression_strength_not_evaluable: bool
    compression_strength_reduced_resolution: bool
    compression_strength_effective_weight_ratio: Optional[float]

    expansion_progress_structural: Optional[float]
    expansion_progress_structural_not_evaluable: bool
    expansion_progress_structural_reduced_resolution: bool
    expansion_progress_structural_effective_weight_ratio: Optional[float]

    volume_regime_shift: Optional[float]
    volume_regime_shift_not_evaluable: bool
    volume_regime_shift_reduced_resolution: bool
    volume_regime_shift_effective_weight_ratio: Optional[float]

    freshness_distance_structural: Optional[float]
    freshness_distance_structural_not_evaluable: bool
    freshness_distance_structural_reduced_resolution: bool
    freshness_distance_structural_effective_weight_ratio: Optional[float]
```

### Semantics

`Tier1AxisBundle` carries only: `symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`, the six Tier-1 axis values, and per-axis companion fields.

It must not carry: raw-feature fields, phase outputs, subscore breakdown objects, normalization intermediate tables, state/history context, storage metadata, run metadata.

### Null semantics

- `<axis> = None` means "not evaluable", not "bad" or "low"
- `<axis> = None` must never be coerced to `0`, `False`, or any sentinel value
- `<axis>_not_evaluable = True` implies `<axis> is None`
- `<axis>_effective_weight_ratio = None` when `<axis>_not_evaluable = True`

---

## Normalization utilities (authoritative)

All four utilities live in `scanner/axes/normalization.py`. They are pure functions, stateless, have no config access, receive anchor values / point lists as call arguments, and do not read repo / storage / feature bundle objects directly.

### Utility 1 — `norm_linear_clamped`

```python
def norm_linear_clamped(
    x: float,
    low: float,
    mid: float,
    high: float,
) -> Optional[float]: ...
```

#### Parameter validation
- `mid == low` → `ValueError`
- `high == mid` → `ValueError`
- `low >= high` → `ValueError`

#### Input validation
- `x = NaN`, `inf`, `-inf` → return `None`

#### Mathematical definition
Piecewise-linear with hard clamp to `0..100`:

- if `x <= low` → `0`
- if `x >= high` → `100`
- if `low < x <= mid`: `((x - low) / (mid - low)) * 50`
- if `mid < x < high`: `50 + ((x - mid) / (high - mid)) * 50`

### Utility 2 — `norm_linear_clamped_inv`

```python
def norm_linear_clamped_inv(
    x: float,
    low_good: float,
    mid: float,
    high_bad: float,
) -> Optional[float]: ...
```

#### Parameter validation
- `mid == low_good` → `ValueError`
- `high_bad == mid` → `ValueError`
- `low_good >= high_bad` → `ValueError`

#### Input validation
- `x = NaN`, `inf`, `-inf` → return `None`

#### Mathematical definition
Inverse piecewise-linear with hard clamp to `0..100`:

- if `x <= low_good` → `100`
- if `x >= high_bad` → `0`
- if `low_good < x <= mid`: `100 - ((x - low_good) / (mid - low_good)) * 50`
- if `mid < x < high_bad`: `50 - ((x - mid) / (high_bad - mid)) * 50`

### Utility 3 — `norm_piecewise_linear`

```python
def norm_piecewise_linear(
    x: float,
    points: list[tuple[float, float]],
) -> Optional[float]: ...
```

#### Parameter validation
- fewer than 2 points → `ValueError`
- x-values not strictly ascending → `ValueError`
- any y-value outside `[0, 100]` → `ValueError`

#### Input validation
- `x = NaN`, `inf`, `-inf` → return `None`

#### Mathematical definition
Let the points be `(x0, y0), (x1, y1), ..., (xn, yn)`. Then:

- if `x <= x0` → `y0`
- if `x >= xn` → `yn`
- if `xi <= x <= x(i+1)` for some segment: linearly interpolate between `(xi, yi)` and `(x(i+1), y(i+1))`

### Utility 4 — `weighted_mean`

```python
def weighted_mean(
    scores_and_weights: list[tuple[Optional[float], float]],
) -> Optional[float]: ...
```

#### Validation
- any score outside `[0, 100]` → `ValueError`
- any weight `<= 0` → `ValueError`
- any non-finite weight → `ValueError`

#### Behavior
- scores with value `None` are dropped before aggregation
- retained weights are re-normalized internally to sum to 1.0
- empty input or empty retained set → return `None`
- total retained weight `== 0` after dropout → return `None`

#### Effective weight ratio
This function does **not** return the ratio itself. Callers compute it as:

```
effective_weight_ratio
= sum(original weights whose scores are retained)
  / sum(all original axis weights)
```

This ratio is computed **before** internal re-normalization and stored in `<axis>_effective_weight_ratio`.

---

## Feature-input availability rule (authoritative)

A T5 / T5.1 field is considered **available and usable** for Ticket 6 exactly when:

- its value is not `None`
- **and** its companion status field is exactly `ok`

Any other combination means the input is treated as **missing** for axis aggregation. All five T5 status values other than `ok` (`insufficient_history`, `gap_in_required_window`, `upstream_dependency_null`, `invalid_upstream_value`) mean missing. No other status values are allowed.

---

## Axis-level Missing-Data rules (authoritative)

### Generic weight-dropout rule

Missing sub-inputs are removed from axis aggregation. Their original weights are dropped. The remaining weights are re-normalized internally for the final `weighted_mean`.

### Global floor

```python
cfg.axes.min_effective_weight_ratio: float = 0.60
```

If `effective_weight_ratio` falls below this value after dropout:

- `<axis> = None`
- `<axis>_not_evaluable = True`

### Reduced-resolution rule

If an axis remains computable after dropout but is missing one or more original sub-inputs:

- `<axis>_reduced_resolution = True`

unless an axis-specific rule says otherwise.

---

## Axis-specific pre-gates (authoritative)

These rules are applied **before** the generic weight-dropout / `weighted_mean` path.

### `compression_strength` pre-gate

`compression_strength` requires at least one valid 4h compression input. If all remaining valid inputs are 1d-only (i.e. only `atr_pct_rank_120_1d_pct` remains), the axis is not evaluable regardless of `effective_weight_ratio`:

- `compression_strength = None`
- `compression_strength_not_evaluable = True`

### `expansion_progress_structural` pre-gate

If `data_4h_available = False`:

- `expansion_progress_structural = None`
- `expansion_progress_structural_not_evaluable = True`

If `dist_to_base_mid_pct` is missing (always, currently) but the three remaining inputs (`move_from_last_structural_break_pct`, `bars_since_last_structural_break_4h`, `dist_to_ema20_4h_pct_abs`) yield `effective_weight_ratio >= cfg.axes.min_effective_weight_ratio`:

- axis is computed
- `expansion_progress_structural_reduced_resolution = True`

If additional losses pull `effective_weight_ratio` below the floor:

- `expansion_progress_structural = None`
- `expansion_progress_structural_not_evaluable = True`

### `volume_regime_shift` pre-gate

If `data_4h_available = False`:

- `volume_regime_shift = None`
- `volume_regime_shift_not_evaluable = True`

### `freshness_distance_structural` minimum-input rule

This axis has a dedicated minimum-input rule from Abschnitt 1 §7.5, checked **before** the generic `min_effective_weight_ratio` rule:

- fewer than 2 valid inputs → `not_evaluable = True`
- exactly 2 or 3 valid inputs → axis is computed, `_reduced_resolution = True`
- all 4 valid inputs → normal computation, `_reduced_resolution = False`

---

## Per-axis specifications (authoritative)

**The following six sections are the authoritative implementation contract for Ticket 6. Codex must implement exactly these inputs, normalization functions, anchor/point values, and weights. Codex must not reconstruct these values from Abschnitt 1 independently.**

---

### Axis 1 — `trend_strength`

**Source: Abschnitt 1 §2.3 / §2.4**

This axis has eight flat sub-inputs aggregated in a single `weighted_mean`.

#### Sub-input definitions

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `close_vs_ema20_1d_pct` | `norm_linear_clamped` | low=`-10`, mid=`0`, high=`+10` | `0.20` |
| 2 | `close_vs_ema50_1d_pct` | `norm_linear_clamped` | low=`-10`, mid=`0`, high=`+10` | `0.15` |
| 3 | `close_vs_ema20_4h_pct` | `norm_linear_clamped` | low=`-10`, mid=`0`, high=`+10` | `0.15` |
| 4 | `close_vs_ema50_4h_pct` | `norm_linear_clamped` | low=`-10`, mid=`0`, high=`+10` | `0.10` |
| 5 | `ema20_slope_1d_pct_per_bar` | `norm_linear_clamped` | low=`-1.5`, mid=`0`, high=`+1.5` | `0.10` |
| 6 | `ema20_slope_4h_pct_per_bar` | `norm_linear_clamped` | low=`-1.5`, mid=`0`, high=`+1.5` | `0.10` |
| 7 | `ema20_vs_ema50_1d_pct` | `norm_linear_clamped` | low=`-8`, mid=`0`, high=`+8` | `0.10` |
| 8 | `ema20_vs_ema50_4h_pct` | `norm_linear_clamped` | low=`-8`, mid=`0`, high=`+8` | `0.10` |

Original weights sum to `1.00`.

#### Aggregation

`trend_strength = weighted_mean(subscores, weights)`

#### Missing-Data rule

If 4h inputs (rows 3, 4, 6, 8) are missing but 1d inputs remain with `effective_weight_ratio >= cfg.axes.min_effective_weight_ratio`:

- axis is computed
- `trend_strength_reduced_resolution = True`

Otherwise: generic weight-dropout + floor applies.

---

### Axis 2 — `reclaim_progress`

**Source: Abschnitt 1 §3.3 / §3.4**

This axis uses a **two-level aggregation**. It must not be flattened into a single-level `weighted_mean`.

#### Level 1 — Per-anchor score

For each of the five anchors, compute an `anchor_score`:

```
anchor_score = 0.70 * distance_score + 0.30 * hold_score
```

**Distance score** (same formula for all five anchors):

```
distance_score = norm_linear_clamped(close_vs_anchor_pct, low=-3, mid=0, high=+3)
```

**Hold score** (same formula for all five anchors):

```
hold_score = norm_piecewise_linear(bars_above_anchor, [(0, 0), (1, 40), (2, 70), (3, 100)])
```

Values above 3 are capped at 100 by the right-clamp rule of `norm_piecewise_linear`.

#### Level 1 — Anchor-to-field mapping

| Anchor | Distance input field | Hold input field |
|---|---|---|
| 4h EMA20 | `close_vs_ema20_4h_pct` | `bars_above_ema20_4h` |
| 4h EMA50 | `close_vs_ema50_4h_pct` | `bars_above_ema50_4h` |
| 1d EMA20 | `close_vs_ema20_1d_pct` | `bars_above_ema20_1d` |
| 1d EMA50 | `close_vs_ema50_1d_pct` | `bars_above_ema50_1d` |
| 4h fixed structural anchor | `close_vs_high20_4h_pct` | `bars_above_high20_4h` |

**`close_vs_high20_4h_pct` is a `RawFeatures4H` field, not a local T6 computation.**

It is defined as `((close_4h / fixed_structural_break_anchor_4h) - 1) * 100` and must be present in the FeatureBundle as a T5.1 output with a companion status field. If it is not yet present in the T5.1 implementation, it must be added to T5.1's scope before T6 is executed — T6 must not compute it locally from raw prices.

T6 treats this field the same as all other FeatureBundle inputs: available only when value `!= None` and companion status `== ok`. If `close_vs_high20_4h_pct` is unavailable, the 4h fixed structural anchor score is absent and its weight (0.20 at Level 2) is dropped.

#### Level 2 — Cross-anchor aggregation

| Anchor | Weight |
|---|---|
| 4h EMA20 | `0.25` |
| 4h EMA50 | `0.20` |
| 1d EMA20 | `0.20` |
| 1d EMA50 | `0.15` |
| 4h fixed structural anchor | `0.20` |

Original weights sum to `1.00`.

`reclaim_progress = weighted_mean(anchor_scores, weights)`

#### Missing-Data at anchor level

For each anchor: if both the distance input and the hold input are available, the anchor score is fully computable. If one or both are missing, the anchor score is `None` and its weight is dropped from Level 2 aggregation. The `effective_weight_ratio` is computed over the five anchor-level weights (not over the ten raw sub-inputs).

#### Missing-Data rule

If 4h anchors (4h EMA20, 4h EMA50, 4h fixed structural) are missing but 1d anchors remain with `effective_weight_ratio >= cfg.axes.min_effective_weight_ratio`:

- axis is computed
- `reclaim_progress_reduced_resolution = True`

Otherwise: generic floor applies.

---

### Axis 3 — `compression_strength`

**Source: Abschnitt 1 §4.3 / §4.4**

#### Sub-input definitions

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `bb_width_rank_120_4h_pct` | `norm_linear_clamped_inv` | low_good=`10`, mid=`50`, high_bad=`100` | `0.35` |
| 2 | `atr_pct_rank_120_1d_pct` | `norm_linear_clamped_inv` | low_good=`10`, mid=`50`, high_bad=`100` | `0.25` |
| 3 | `range_width_12bars_4h_vs_atr1d_pct` | `norm_linear_clamped_inv` | low_good=`50`, mid=`100`, high_bad=`200` | `0.25` |
| 4 | `std_return_rank_12bars_4h_pct` | `norm_linear_clamped_inv` | low_good=`10`, mid=`50`, high_bad=`100` | `0.15` |

Original weights sum to `1.00`.

#### Aggregation

`compression_strength = weighted_mean(subscores, weights)`

#### Missing-Data rule

Axis-specific pre-gate applies (defined above): at least one of rows 1, 3, or 4 (4h inputs) must be valid. If only row 2 (`atr_pct_rank_120_1d_pct`) remains, the axis is `not_evaluable` regardless of `effective_weight_ratio`.

---

### Axis 4 — `expansion_progress_structural`

**Source: Abschnitt 1 §5.3 / §5.4**

#### Sub-input definitions

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `move_from_last_structural_break_pct` | `norm_piecewise_linear` | `[(0, 0), (3, 30), (6, 60), (10, 100)]` | `0.40` |
| 2 | `bars_since_last_structural_break_4h` | `norm_piecewise_linear` | `[(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]` | `0.20` |
| 3 | `dist_to_base_mid_pct` | `norm_piecewise_linear` | `[(0, 0), (3, 35), (6, 65), (10, 100)]` | `0.20` |
| 4 | `dist_to_ema20_4h_pct_abs` | `norm_piecewise_linear` | `[(0, 0), (2, 30), (5, 65), (8, 100)]` | `0.20` |

Original weights sum to `1.00`.

Row 3 (`dist_to_base_mid_pct`) is currently unresolved and not present in the FeatureBundle. It must be treated as a permanently missing input until resolved. Its weight (0.20) is dropped; the remaining three inputs carry a combined original weight of 0.80, which exceeds `cfg.axes.min_effective_weight_ratio = 0.60`, so the axis remains computable under `_reduced_resolution = True`.

#### Aggregation

`expansion_progress_structural = weighted_mean(available_subscores, weights)`

#### Missing-Data rule

Axis-specific pre-gate applies (defined above). When only `dist_to_base_mid_pct` is missing and the three remaining inputs are valid:

- `effective_weight_ratio = 0.80`
- axis is computed
- `expansion_progress_structural_reduced_resolution = True`

If additional inputs are also missing and `effective_weight_ratio` falls below the floor: `not_evaluable`.

---

### Axis 5 — `volume_regime_shift`

**Source: Abschnitt 1 §6.3 / §6.4**

#### Sub-input definitions

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `volume_quote_spike_1d` | `norm_linear_clamped` | low=`0.9`, mid=`1.2`, high=`2.0` | `0.25` |
| 2 | `volume_quote_spike_4h` | `norm_linear_clamped` | low=`0.9`, mid=`1.2`, high=`2.0` | `0.35` |
| 3 | `volume_spike_persistence_4h` | `norm_piecewise_linear` | `[(0.00, 0), (0.25, 30), (0.50, 60), (0.75, 85), (1.00, 100)]` | `0.20` |
| 4 | `volume_4h_current_vs_median10` | `norm_piecewise_linear` | `[(0.8, 0), (1.0, 40), (1.3, 70), (1.8, 100)]` | `0.20` |

Original weights sum to `1.00`.

Note on row 4: the field is `volume_4h_current_vs_median10` (4h, not 1d).

#### Aggregation

`volume_regime_shift = weighted_mean(subscores, weights)`

#### Missing-Data rule

Axis-specific pre-gate applies (defined above): if `data_4h_available = False`, the axis is `not_evaluable`. There is no 1d-only fallback for this axis.

---

### Axis 6 — `freshness_distance_structural`

**Source: Abschnitt 1 §7.3 / §7.4**

#### Sub-input definitions

| # | FeatureBundle field | Utility | Parameters | Weight |
|---|---|---|---|---|
| 1 | `distance_to_last_structural_anchor_pct_abs` | `norm_piecewise_linear` | `[(0, 0), (1, 25), (2, 50), (3, 75), (5, 100)]` | `0.35` |
| 2 | `distance_to_range_high_pct_abs` | `norm_piecewise_linear` | `[(0, 0), (1, 30), (2, 55), (4, 100)]` | `0.25` |
| 3 | `bars_since_last_volume_shift_4h` | `norm_piecewise_linear` | `[(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]` | `0.20` |
| 4 | `bars_since_last_structural_break_4h` | `norm_piecewise_linear` | `[(0, 0), (1, 20), (2, 40), (4, 70), (6, 100)]` | `0.20` |

Original weights sum to `1.00`.

Note on field names: `bars_since_last_volume_shift_4h` (T5.1 canonical name) implements spec field `bars_since_last_volume_shift_event`; `bars_since_last_structural_break_4h` (T5 canonical name) implements spec field `bars_since_last_structural_break_event`.

All four of these inputs are defined and present in the FeatureBundle after T5.1. This axis has no permanently unresolved sub-inputs.

#### Aggregation

`freshness_distance_structural = weighted_mean(available_subscores, weights)`

#### Missing-Data rule

Dedicated minimum-input rule applies (defined in axis-specific pre-gates section). There is no hard `data_4h_available = False` pre-gate for this axis — its evaluability is governed solely by the input-count rule (at least 2 of 4 inputs valid). Note that all four inputs are 4h-derived fields; if 4h data is unavailable all four will typically be absent, which triggers `not_evaluable` via the count rule rather than via a separate availability gate.

---

## Config contract (authoritative)

All configurable parameters must be sourced exclusively from the Ticket-1 config object.

### Root key

```python
cfg.axes
```

### Root-level key

```python
cfg.axes.min_effective_weight_ratio: float = 0.60
```

Validation:
- `<= 0` → `ValueError`
- `> 1.0` → `ValueError`
- non-finite → `ValueError`

### Per-axis anchor blocks

Per-axis normalization parameters live under per-axis config blocks:

```python
cfg.axes.trend_strength
cfg.axes.reclaim_progress
cfg.axes.compression_strength
cfg.axes.expansion_progress_structural
cfg.axes.volume_regime_shift
cfg.axes.freshness_distance_structural
```

The default values for all anchor / point parameters are exactly as defined in the per-axis specifications above. These defaults are the starting calibration values and are explicitly expected to be adjusted after real runs (Abschnitt 1 §1.8).

### Merge semantics

Partial overrides of `cfg.axes` and nested axis blocks are merged field-by-field with canonical defaults. Missing subkeys are not invalid; the default applies. Invalid values (wrong type, out of range, malformed point lists, impossible anchor order) raise `ValueError` at config-validation time.

---

## Acceptance Criteria (deterministic)

1. The following modules exist: `scanner/axes/normalization.py`, `scanner/axes/tier1.py`, `scanner/axes/models.py`
2. `compute_tier1_axes(feature_bundle, cfg)` exists as the sole public entry point for Tier-1 axis computation. No `symbol` parameter.
3. Ticket 6 consumes only `FeatureBundle` and `cfg`. No OHLCV, repositories, cache, SQLite, Parquet, or storage.
4. `Tier1AxisBundle` exists with exactly the fields defined in this ticket.
5. Ticket 6 implements exactly six Tier-1 axes and no phantom seventh axis.
6. `freshness_distance_structural` is fully computable from FeatureBundle after T5.1.
7. `expansion_progress_structural` is in scope and computable under `_reduced_resolution = True` due to the unresolved `dist_to_base_mid_pct`.
8. All four normalization utilities behave exactly as mathematically defined in this ticket.
9. A T5/T5.1 input is treated as available only when `value != None` and companion status == `ok`.
10. `reclaim_progress` uses two-level aggregation: anchor scores computed first, then cross-anchor `weighted_mean`.
11. Generic weight-dropout, `effective_weight_ratio`, and `min_effective_weight_ratio` behavior match this ticket exactly.
12. Axis-specific pre-gates for `compression_strength`, `expansion_progress_structural`, `volume_regime_shift`, `freshness_distance_structural` are enforced before the generic path.
13. `null` axis values are not coerced to `0`, `False`, or sentinel values.
14. All config values are sourced exclusively from `cfg.axes` defaults / overrides.
15. Canonical docs listed in this ticket are updated in the same PR.
16. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
17. The ticket is archived in the same PR per workflow.

---

## Tests (required)

### Category A — Normalization utilities

#### A1 `norm_linear_clamped`
- `x == low` → `0`; `x == mid` → `50`; `x == high` → `100`
- `x < low` → `0`; `x > high` → `100`
- midpoint between `low` and `mid` → `25`; midpoint between `mid` and `high` → `75`
- `mid == low` → `ValueError`; `high == mid` → `ValueError`; `low >= high` → `ValueError`
- `x = NaN` → `None`; `x = inf` → `None`; `x = -inf` → `None`

#### A2 `norm_linear_clamped_inv`
- `x == low_good` → `100`; `x == mid` → `50`; `x == high_bad` → `0`
- clamp below `low_good` → `100`; clamp above `high_bad` → `0`
- invalid anchors → `ValueError`
- `x = NaN` → `None`; `x = inf` → `None`

#### A3 `norm_piecewise_linear`
- correct interpolation within an interior segment
- left clamp (`x < x0`) → `y0`; right clamp (`x > xn`) → `yn`
- exact support point `x == xi` → `yi`
- fewer than 2 points → `ValueError`
- non-strictly-ascending x-values → `ValueError`
- y-value outside `[0, 100]` → `ValueError`
- `x = NaN` → `None`

#### A4 `weighted_mean`
- standard weighted calculation with known inputs: verify result numerically
- dropout of one `None` score: verify result with re-normalized remaining weights
- all scores `None` → `None`
- empty input → `None`
- score outside `[0, 100]` → `ValueError`
- weight `<= 0` → `ValueError`; non-finite weight → `ValueError`
- `weighted_mean` does not return `effective_weight_ratio`; caller-level tests in Category B/C/D verify `effective_weight_ratio = retained_original_weight / total_original_weight` before re-normalization

### Category B — Axis-specific pre-gates

#### B1 `compression_strength`
- `data_4h_available = False` → `not_evaluable = True`
- all 4h inputs null / non-ok, only 1d ATR-rank valid → `not_evaluable = True`
- at least one of `bb_width_rank_120_4h_pct`, `range_width_12bars_4h_vs_atr1d_pct`, `std_return_rank_12bars_4h_pct` valid → axis may compute

#### B2 `expansion_progress_structural`
- `data_4h_available = False` → `not_evaluable = True`
- `dist_to_base_mid_pct` absent (always), three others valid → computed + `reduced_resolution = True`, `effective_weight_ratio = 0.80`
- `dist_to_base_mid_pct` absent plus one further input null → check floor; if below → `not_evaluable = True`

#### B3 `volume_regime_shift`
- `data_4h_available = False` → `not_evaluable = True`

#### B4 `freshness_distance_structural`
- exactly 1 valid input → `not_evaluable = True`
- exactly 2 valid inputs → computed + `reduced_resolution = True`
- exactly 3 valid inputs → computed + `reduced_resolution = True`
- all 4 valid inputs → computed + `reduced_resolution = False`

### Category C — Per-axis golden fixtures

For each of the six Tier-1 axes:

- at least one **full-input golden**: all required inputs present and status `ok`, expected output manually precomputed (not copied from implementation)
  - must yield `_not_evaluable = False`, `_reduced_resolution = False`, `_effective_weight_ratio = 1.0`
- at least one **dropout golden**: one input missing, expected output manually precomputed with re-normalized weights

For `reclaim_progress` specifically:
- at least one golden that verifies the two-level structure: given known distance and hold inputs per anchor, verify that the intermediate anchor scores and the final axis value match manually precomputed values

### Category D — Output contract

- `compute_tier1_axes(feature_bundle, cfg)` returns `Tier1AxisBundle`
- all six axes and all companion fields present
- `symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available` correctly read from `FeatureBundle`
- no storage access occurs during execution
- identical `feature_bundle` + identical `cfg` → identical `Tier1AxisBundle` (determinism)
- `not_evaluable = True` implies `<axis> is None` — no counter-examples permitted

### Category E — Config

- missing `cfg.axes` block → defaults merge without error
- `cfg.axes.min_effective_weight_ratio = 0.0` → `ValueError`
- `cfg.axes.min_effective_weight_ratio = 1.5` → `ValueError`
- missing nested axis anchor key → default applies, no error
- malformed point list / impossible anchor order in per-axis block → `ValueError`

---

## Definition of Done (non-test AC items)

- canonical docs updated for: `scanner/axes/` module structure, Tier-1 axis bundle contract, normalization utility definitions, axis-level Missing-Data rules, config structure under `cfg.axes`
- `docs/canonical/open_questions.md` retains `dist_to_base_mid_pct` as unresolved and documents the `expansion_progress_structural_reduced_resolution = True` consequence
- `docs/canonical/VERIFICATION_FOR_AI.md` updated with: six Tier-1 axis names and their T5/T5.1 input fields, utility-function formulas, availability rule, `effective_weight_ratio` definition, axis-specific pre-gates, two-level aggregation note for `reclaim_progress`

---

## Constraints / Invariants

- [ ] Ticket 6 consumes only `FeatureBundle` and `cfg`
- [ ] Ticket 6 does not access OHLCV or storage
- [ ] `close_vs_high20_4h_pct` must be present in `RawFeatures4H` as a T5.1 output before T6 executes; T6 must not compute it locally from raw prices
- [ ] Ticket 6 implements exactly six Tier-1 axes
- [ ] `reclaim_progress` uses two-level aggregation, not a flat weighted_mean
- [ ] Tier-2 remains out of scope
- [ ] Phase / state / entry / ranking remain out of scope
- [ ] `freshness_distance_structural` is fully computable after T5.1
- [ ] `expansion_progress_structural` remains `_reduced_resolution` until `dist_to_base_mid_pct` is defined
- [ ] All normalization utilities are pure functions with no config access
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
gesamtkonzept_ref: "§19 Ticket 6"
related_issues: []
follow_ups:
  - "Ticket 7: implement Tier-2-Simplified axes"
  - "Ticket 8: implement phase interpreter using FeatureBundle + Tier1AxisBundle + Tier2AxisBundle"
  - "Resolve dist_to_base_mid_pct in canonical open questions"
```
