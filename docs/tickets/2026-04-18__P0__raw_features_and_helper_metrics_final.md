# Title
[P0] Implement raw feature derivation and deterministic helper metrics for 1d / 4h OHLCV

## Context / Source

This ticket implements **Ticket 5** from the Independence-Release consolidated concept: the raw-field and deterministic helper-metric layer under `scanner/features/`.

**Gesamtkonzept reference:** Gesamtkonzept §19, Ticket 5.

`depends_on: [1, 4]` — requires:
- Ticket 1 (`bar_clock + sqlite + config foundation`)
- Ticket 4 (`ohlcv fetch + cache policy + transitional SQLite OHLCV persistence`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, or older ticket assumptions conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements the **raw-field and deterministic helper-metric layer** under `scanner/features/`.

It sits:
- **after** Ticket 4 closed-bar OHLCV fetch / validation / persistence
- **before** Tier-1 / Tier-2 axes, phase interpretation, invalidation/cycle, state machine, entry logic, and ranking

This ticket therefore defines:
- how canonical raw fields and deterministic helper metrics are computed from closed 1d / 4h OHLCV
- how Missing / Gap / Insufficient-History semantics are represented
- how feature outputs are materialized as in-memory typed objects for downstream tickets

This ticket does **not** define:
- axis normalization utilities
- axes
- phase
- invalidation/cycle
- state
- entry
- ranking
- execution
- any persisted feature store

### Authority resolution for “normalization”

The Gesamtkonzept Ticket-5 shorthand (“raw features + normalization”) is superseded here by the more specific module-responsibility layer in Gesamtkonzept §2.2:

- `features/` = pure raw-field computation from 1d / 4h OHLCV
- `axes/normalization.py` = normalization functions and Missing-Data rules

Therefore this ticket **does not** implement:
- `norm_linear_clamped`
- `norm_linear_clamped_inv`
- `norm_piecewise_linear`
- `weighted_mean`
- axis-layer Missing-Data redistribution rules

Those belong to **Ticket 6**, not Ticket 5.

### Addendum / working-context checks

This ticket explicitly follows the addendum working-context leitplanken:

- **A.2 Schichtenarchitektur** — T5 remains below axes/phase/state and does not reintroduce mixed-layer logic.
- **A.3 `bar_clock.py` is fundamentmodul** — all bar-span/window semantics reuse Ticket-1 bar-clock outputs; no raw `now` timestamp is accepted by T5 public functions.
- **A.5 Persistenz ist fachlicher Kern** — T5 consumes persisted OHLCV history but does not create a second persisted feature authority.
- **A.8 Basisdaten vs. Run-Artefakte** — T5 outputs are run-local derived artifacts, not long-lived historical base data.

## Goal

After this ticket is completed, the repo must be able to:

- compute canonical 1d / 4h raw fields and deterministic helper metrics from pre-loaded canonical OHLCV bars
- expose those outputs as typed in-memory models (`RawFeatures1D`, `RawFeatures4H`, `RawFeaturesShared`, `FeatureBundle`)
- preserve strict Missing / Gap / Insufficient-History semantics with companion status fields per derived field
- provide the complete field layer required by Ticket 3 and by the later Tier-1 / Tier-2 workstream, without pushing OHLCV-helper reconstruction into T6 / T7
- keep event-/cycle-/state-dependent and normalization logic explicitly out of scope
- record unresolved field-definition gaps in `docs/canonical/open_questions.md`

## Scope

Allowed change surface:

- `scanner/features/raw_1d.py` (new)
- `scanner/features/raw_4h.py` (new)
- `scanner/features/shared.py` (new)
- `scanner/features/models.py` (new)
- `scanner/features/bundle.py` (new)
- `scanner/features/__init__.py` if needed
- `scanner/config.py` or central config accessor — add feature-layer config keys and merge / validation rules
- `tests/**` — add tests specified below
- `docs/canonical/**` — update docs listed below

## Out of Scope

This ticket must not:

- implement or persist any feature store table in SQLite / Parquet / files
- re-emit original OHLCV bars as feature outputs
- implement normalization utilities (`norm_*`, `weighted_mean`)
- implement Tier-1 or Tier-2 axes
- implement phase interpretation
- implement invalidation / cycle logic
- implement state machine logic
- implement entry patterns
- implement decision buckets / ranking
- implement execution logic
- access repositories, SQLite, Parquet, cache metadata, or storage layers directly
- derive bar-clock context from `now` or raw timestamps locally
- introduce event semantics for unresolved fields such as `bars_since_last_volume_shift_event`
- introduce interpretations based on persisted setup/state/history context
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

## Canonical References (important)

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.1, §2.2, §18, §19 Ticket 5
- `v2_1_abschnitt_1_tier_1_achsen_rev2.md`
- `v2_1_abschnitt_2_tier_2_simplified_achsen_rev2.md`
- Ticket 1 — canonical bar-clock outputs and bar-id semantics
- Ticket 4 — canonical OHLCV-bar contract and closed-bar-only persistence semantics

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

Repo process references:

- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- `docs/canonical/WORKFLOW_CODEX.md`

### Canonical docs to update

- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/open_questions.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Proposed change (high-level)

### Before

- Ticket 4 provides canonical closed 1d / 4h OHLCV bars and cache semantics.
- Ticket 3 already assumes a 1d raw-field derivation layer exists before post-1d activity gate and pre-4h candidate filtering.
- There is no canonical typed feature layer yet, and later axis tickets would be forced to reconstruct OHLCV helpers ad hoc.

### After

- `scanner/features/` provides the canonical raw-feature derivation layer:
  - `raw_1d.py`
  - `raw_4h.py`
  - `shared.py`
  - `models.py`
  - `bundle.py`
- Ticket 5 exposes four strict public functions:
  - `compute_raw_1d(...)`
  - `compute_raw_4h(...)`
  - `compute_raw_shared(...)`
  - `build_feature_bundle(...)`
- Feature outputs are materialized as typed in-memory dataclasses:
  - `RawFeatures1D`
  - `RawFeatures4H`
  - `RawFeaturesShared`
  - `FeatureBundle`
- Every derived field has a companion status field in the same dataclass.
- T6 / T7 consume a single canonical feature-layer output contract instead of rebuilding OHLCV helpers.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Docs in same PR:** Update all listed canonical docs in the same PR as the code.
- **No feature persistence:** Ticket 5 outputs are run-local in-memory objects only. Do not create SQLite / Parquet / file-backed feature materialization.
- **No repository access in T5:** Ticket 5 accepts pre-loaded OHLCV bar sequences only. It must not read repositories, cache meta, SQLite, or Parquet.
- **No raw `now` in public APIs:** Ticket 5 public functions accept Ticket-1 `BarClockContext`, not a raw timestamp.
- **Bar-clock semantics reused:** All window/span logic must use Ticket-1 bar-clock semantics and bar ids as input context, not reimplemented local time logic.
- **No second OHLCV derivation path in shared.py:** `compute_raw_shared(...)` may read only `RawFeatures1D`, `RawFeatures4H`, `BarClockContext`, and `cfg`. It must not accept or access OHLCV bars directly.
- **Field-local failures only:** Numeric / input-window failures null only the affected field with companion status; they do not fail the whole feature pass.
- **No shortened-window fallback:** Unless the authoritative spec defines a distinct alternative field path, fields require the full canonical input window.
- **Tier-2 1d fallback is an alternative path, not a shortened-window exception.**
- **EMA warm-up rule fixed:** EMA-derived fields use SMA bootstrap and require at least `2 × period` bars before status `ok`.
- **Companion status fields required:** Every derived field has a same-model companion status field named `{field_name}_status`.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**
- **One ticket = one PR.**

## Module and model structure (authoritative)

### Modules

- `scanner/features/raw_1d.py`
- `scanner/features/raw_4h.py`
- `scanner/features/shared.py`
- `scanner/features/models.py`
- `scanner/features/bundle.py`

### Dataclass home

The dataclass definitions live in:

- `scanner/features/models.py`

This module contains:
- `RawFeatures1D`
- `RawFeatures4H`
- `RawFeaturesShared`
- `FeatureBundle`

`RawFeaturesShared` carries cross-timeframe derived fields whose computation requires outputs from both `RawFeatures1D` and `RawFeatures4H`. The primary explicit MVP example in Ticket 5 is `range_width_12bars_4h_vs_atr1d_pct`.

`BarClockContext` is not defined here; it is imported from Ticket-1 output models / types.

### Public functions

- `compute_raw_1d(...) -> RawFeatures1D`
- `compute_raw_4h(...) -> RawFeatures4H | None`
- `compute_raw_shared(...) -> RawFeaturesShared`
- `build_feature_bundle(...) -> FeatureBundle`

### Fixed builder call order

`build_feature_bundle(...)` must execute in this exact order:

1. `compute_raw_1d(...)`
2. `compute_raw_4h(...)`
3. `compute_raw_shared(...)`
4. assemble `FeatureBundle`

`compute_raw_shared(...)` may consume already-computed `RawFeatures1D` / `RawFeatures4H` instances. It must not independently re-read or re-scan OHLCV input.

## Input contract

### Symbol
- type: `str`
- required form: non-empty, already-normalized uppercase symbol string
- wrong type → `TypeError`
- empty / whitespace-only / invalid content → `ValueError`

T5 does not perform best-effort symbol normalization.

### BarClockContext
Public functions do not accept raw timestamps. They accept a Ticket-1 `BarClockContext` carrying canonical references for the feature computation context.

### OHLCV bar sequences
T5 functions accept pre-loaded canonical closed-bar sequences from Ticket 4.

Global rules:
- ascending by `close_time_utc_ms`
- duplicate-free
- closed bars only
- no future / partial bars
- no storage access by T5

Violation of these content rules is a caller error.

### `ohlcv_1d`
For T5 invocation, 1d data is a precondition.

- `ohlcv_1d` must be a non-empty canonical OHLCV list
- empty list → `ValueError`

### `ohlcv_4h`
- `None` = 4h not available
- non-empty canonical OHLCV list = 4h available
- empty list → `ValueError`

The caller must pass `None` when 4h data is unavailable.

### Exception types
- wrong argument types → `TypeError`
- invalid content / violated preconditions → `ValueError`
- assertions must not be used for public-function precondition checks

### Precondition timing
All public-function preconditions are checked at function entry before any computation begins. Functions fail fast on the first violated precondition.

## Function signatures (authoritative)

```python
def compute_raw_1d(
    symbol: str,
    bar_clock_context: BarClockContext,
    ohlcv_1d: list[OHLCVBar],
    cfg: Config,
) -> RawFeatures1D: ...

def compute_raw_4h(
    symbol: str,
    bar_clock_context: BarClockContext,
    ohlcv_4h: list[OHLCVBar] | None,
    cfg: Config,
) -> RawFeatures4H | None: ...

def compute_raw_shared(
    symbol: str,
    bar_clock_context: BarClockContext,
    raw_1d: RawFeatures1D,
    raw_4h: RawFeatures4H | None,
    cfg: Config,
) -> RawFeaturesShared: ...

def build_feature_bundle(
    symbol: str,
    bar_clock_context: BarClockContext,
    ohlcv_1d: list[OHLCVBar],
    ohlcv_4h: list[OHLCVBar] | None,
    cfg: Config,
) -> FeatureBundle: ...
```

## FeatureBundle contract (authoritative)

```python
@dataclass
class FeatureBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    daily_close_time_utc_ms: int
    intraday_close_time_utc_ms: int | None
    data_4h_available: bool
    raw_1d: RawFeatures1D
    raw_4h: RawFeatures4H | None
    raw_shared: RawFeaturesShared
```

Semantics:
- `raw_1d` is always present
- `raw_4h is None` iff `data_4h_available = False`
- `raw_shared` is always present
- `intraday_bar_id` and `intraday_close_time_utc_ms` are `None` iff `data_4h_available = False`

Precondition:
- Ticket 5 is invoked only after the Ticket-3 / Ticket-4 1d stage succeeded for the symbol
- missing 1d data is a pre-T5 abort condition, not a FeatureBundle state

`FeatureBundle` carries only:
- symbol identity
- Ticket-1 bar-clock references
- 4h availability flag
- the three feature dataclass instances

It must not carry:
- run metadata
- fetch/cache metadata
- eligibility context
- state / cycle / history context
- config snapshots
- ranking / decision outputs

## Scope lock for field families (authoritative)

### Included field families

Ticket 5 includes these field families:

- **Trend / Level Core**
- **Volume / Reference Core**
- **Range / Compression / Volatility Core**
- **Stateless Counter / Break Core**
- **Deterministic Pullback / Impulse Segmentation Core**

### Excluded field families

Ticket 5 excludes:

- original OHLCV bars as feature outputs
- normalization utilities (`norm_*`, `weighted_mean`)
- event-/cycle-/state-dependent fields
- interpretive axis / phase / state / entry / ranking logic

### Original OHLCV clarification

Original OHLCV bars are Ticket-4 outputs and remain part of the data layer. Ticket 5 derives fields from them; it does not re-emit or persist the raw OHLCV bars as feature outputs.

Simple candlestick-derived fields are included only if they are explicitly required by downstream tickets. They are not part of Ticket 5 by default merely because they are derivable.

## Required MVP field groups (authoritative)

### Ticket-3 direct 1d prerequisite fields
These are mandatory because Ticket 3 already depends on them:

- `close_vs_ema50_1d_pct`
- `ema20_vs_ema50_1d_pct`
- `ema20_slope_1d_pct_per_bar`
- `volume_1d_current_vs_median10`
- `range_width_10bars_1d_pct`
- `close_position_in_range_10bars_1d`

### Trend / Level Core
Mandatory MVP includes at least:

- EMA20 / EMA50 on 1d and 4h
- rolling highs / lows in required spec windows
- `close_vs_ema20_1d_pct`, `close_vs_ema20_4h_pct`
- `close_vs_ema50_1d_pct`, `close_vs_ema50_4h_pct`
- `ema20_vs_ema50_1d_pct`, `ema20_vs_ema50_4h_pct`
- `ema20_slope_1d_pct_per_bar`, `ema20_slope_4h_pct_per_bar`
- `close_vs_rolling_high_5_1d_pct`, `close_vs_rolling_high_5_4h_pct`

`close_vs_rolling_low_*` is **not** mandatory MVP unless a downstream consumer is explicitly demonstrated.

### Volume / Reference Core
Mandatory MVP includes at least:

- rolling SMA / median volume references required by spec
- current-vs-reference volume ratios required by spec
- `volume_1d_current_vs_median10`
- `volume_4h_current_vs_median10`
- `volume_quote_spike_1d` (= `current_1d_volume / rolling_sma_volume_excl_current_1d`)
- `volume_quote_spike_4h` (= `current_4h_volume / rolling_sma_volume_excl_current_4h`)
- `volume_spike_persistence_4h`

### Range / Compression / Volatility Core
Mandatory MVP includes at least:

- `range_width_10bars_1d_pct`
- `range_width_12bars_4h_pct` (4h-only; lives in `RawFeatures4H`)
- `range_width_12bars_4h_vs_atr1d_pct`
  - defined as `(range_width_last_12_4h / atr_1d) * 100`
  - cross-timeframe field; lives in `RawFeaturesShared`
- `close_position_in_range_*`
- `close_above_range_mid_ratio_10bars_1d`
- `close_above_range_mid_ratio_12bars_4h`
- ATR / ATR%
- BB-width
- return-volatility basis
- rank-based fields:
  - `bb_width_rank_120_*`
  - `atr_pct_rank_120_*`
  - `std_return_rank_12bars_*`

`std_return_rank_12bars_4h_pct` is ranked over the standard deviation of the rolling 4h return series, where the underlying return series is `(close[t] / close[t-1]) - 1`. The rolling return series is an internal computation; only the rank field itself is a named T5 output.

### Stateless Counter / Break Core
Mandatory MVP includes at least:

- `bars_above_ema20_1d`, `bars_above_ema20_4h`
- `bars_above_ema50_1d`, `bars_above_ema50_4h`
- `bars_above_high20_4h`
- `bars_since_last_new_low_1d`, `bars_since_last_new_low_4h`
- `fixed_structural_break_anchor_4h`
- `fixed_high20_break_anchor_4h`
- `break_close_4h`
- `move_from_last_structural_break_pct`
- `bars_since_last_structural_break_4h`
- `distance_to_last_structural_anchor_pct_abs`
- `dist_to_ema20_4h_pct_abs`

### Deterministic Pullback / Impulse Segmentation Core
Mandatory MVP includes at least:

- `pullback_depth_vs_last_impulse_pct_1d`, `pullback_depth_vs_last_impulse_pct_4h`
- `pullback_volume_ratio_1d`, `pullback_volume_ratio_4h`
- `lowest_low_vs_ema20_1d_pct`, `lowest_low_vs_ema20_4h_pct`

The following segmentation helpers must be exposed as named T5 outputs, not merely internal temporaries:

- `impulse_start_price_1d`, `impulse_start_price_4h`
- `impulse_high_price_1d`, `impulse_high_price_4h`
- `pullback_low_price_1d`, `pullback_low_price_4h`
- `current_pullback_close_1d`, `current_pullback_close_4h`

## Explicit out-of-scope unresolved fields

These fields are not implemented in Ticket 5 and must be added as unresolved items in `docs/canonical/open_questions.md`:

- `bars_since_last_volume_shift_event`
- `dist_to_base_mid_pct`
- `distance_to_range_high_pct_abs`

And one consolidated consequence note must be added:

> Two of four inputs for `freshness_distance_structural` currently lack authoritative definitions (`distance_to_range_high_pct_abs`, `bars_since_last_volume_shift_event`). Until resolved, the axis operates at minimum viable input coverage using the two defined inputs under the Missing-Data rules from Abschnitt 1.

## Missing / Gap / Insufficient-History semantics (authoritative)

### General rule
Fields are computed only from full required canonical input windows.

If full required history is unavailable:
- field value = `null`
- companion status = `insufficient_history`

If any required bar inside the exact input window is absent:
- field value = `null`
- companion status = `gap_in_required_window`

If a required upstream derived field is `null`:
- field value = `null`
- companion status = `upstream_dependency_null`

If a required upstream value exists but is invalid for the computation:
- field value = `null`
- companion status = `invalid_upstream_value`

No interpolation, no backfill, no gap-skipping, and no shortened-window fallback are allowed unless the authoritative spec defines a separate alternative field path.

### Tier-2 1d fallback rule
For Tier-2-Simplified fields with explicit 1d fallback variants in Abschnitt 2, absence of 4h data triggers computation of the 1d variant at its own canonical window. This is a spec-defined alternative path, not a shortened-window exception.

If the 1d fallback’s own full window is unavailable, the field is `null`.

### Companion status fields
Each derived field has a same-model companion status field:
- `{field_name}`
- `{field_name}_status`

There is no central nested status dict.

### Status enum — closed and exhaustive

The complete allowed set of companion status values is exactly:

| Value | Meaning |
|---|---|
| `ok` | Field computed successfully from full canonical window |
| `insufficient_history` | Full required lookback window not yet available |
| `gap_in_required_window` | At least one bar is absent within the exact required window |
| `upstream_dependency_null` | A required upstream derived field is `null` |
| `invalid_upstream_value` | Upstream value exists but is invalid (division by zero, NaN, inf, etc.) |

No other status values are permitted. Status fields are non-nullable strings.

### EMA warm-up rule
EMA-derived fields use SMA bootstrap for initialization.

A minimum of `2 × period` bars must be present before an EMA-derived field may have status `ok`.

With fewer bars:
- field value = `null`
- companion status = `insufficient_history`

This rule is fixed in Ticket 5 and not configurable.

## Numeric special-case rules (authoritative)

### Division by zero
Division by zero or by an invalid denominator does not fail the whole feature pass.

The affected field becomes:
- value = `null`
- status = `invalid_upstream_value`

### Non-finite upstream values
If an OHLCV input field (`open`, `high`, `low`, `close`, `base_volume`, `quote_volume`) contains `NaN`, `inf`, or `-inf`, the bar is treated as invalid for any dependent feature calculation.

Any derived field that consumes such a bar becomes:
- value = `null`
- status = `invalid_upstream_value`

`NaN` / `inf` must not propagate into feature outputs.

### Flat range
- direct width metrics (`range_width_*`) with `range_high == range_low` are valid and equal `0.0`
- denominator-based position metrics (`close_position_in_range_*`) become `null` with `invalid_upstream_value`
- `close_above_range_mid_ratio_*` also becomes `null` with `invalid_upstream_value` when range width is zero

### Percent formulas
- signed pct fields: `((a / b) - 1) * 100`
- absolute pct fields: `abs(((a / b) - 1) * 100)`

Absolute-percent fields remain separate named outputs and must not be reconstructed ad hoc in later layers.

### Rank fields
Rank fields are computed on the canonical rolling window as:

`((count_strictly_less + 0.5 * count_equal) / n) * 100`

where `n` is the full canonical window length.

Output:
- unrounded float
- scale `0..100`

### No rounding in T5
Ticket 5 performs no rounding of numeric derived values.

### Numeric output types
- bar-count and streak fields (`bars_above_*`, `bars_since_*`) are `int` with no upper cap enforced in Ticket 5
- numeric derived metrics are `float`
- companion status fields are closed enum strings

## Config contract

All configurable parameters in Ticket 5 must be sourced exclusively from the Ticket-1 config object. No feature module may define its own fallback defaults outside of config.

### Class 1 — spec-fixed / not configurable
These remain fixed because their semantics are encoded by field naming or explicit spec constants:

- EMA20 / EMA50
- rolling-high / rolling-low windows where field names encode the window
- `median10`
- `range_width_10bars_*`
- `close_above_range_mid_ratio_10bars_1d`
- `close_above_range_mid_ratio_12bars_4h`
- `bb_width_rank_120_*`
- `atr_pct_rank_120_*`
- `std_return_rank_12bars_*`
- `volume_spike_persistence_4h` with `N = 4` (spec-fixed in Abschnitt 1 §6.2)

### Class 2 — configurable with spec defaults
These are internal algorithm parameters not encoded in field names:

- pullback / impulse segmentation windows
  - 4h default = `20`
  - 1d fallback default = `15`
- `persistence_spike_threshold`
- `cfg.features.structural_break.min_bars_below_before_break`
  - default = `3`

### Class 3 — not configurable in Ticket 5
These are not part of T5 config:

- normalization parameters
- axis weights
- Missing-Data redistribution rules
- phase / state / entry thresholds

### Config override semantics
Partial overrides in `cfg.features.*` are merged field-by-field with central defaults.

Missing sub-keys are not treated as invalid; the spec default applies.

A missing key is not an error. An invalid value (wrong type, out of range) raises `ValueError` at config-validation time before any feature computation begins.

## Acceptance Criteria (deterministic)

1. The following modules exist:
   - `scanner/features/raw_1d.py`
   - `scanner/features/raw_4h.py`
   - `scanner/features/shared.py`
   - `scanner/features/models.py`
   - `scanner/features/bundle.py`
2. The following public functions exist with the exact public responsibilities defined in this ticket:
   - `compute_raw_1d`
   - `compute_raw_4h`
   - `compute_raw_shared`
   - `build_feature_bundle`
3. Public functions accept `BarClockContext`, not raw timestamps.
4. Public functions do not access repositories, caches, SQLite, Parquet, or any storage layer.
5. `compute_raw_shared(...)` is callable using pre-built `RawFeatures1D` / `RawFeatures4H` instances plus `BarClockContext` and `cfg`, without OHLCV input.
6. `build_feature_bundle(...)` calls functions in the fixed order `1d -> 4h -> shared`.
7. `FeatureBundle` matches the exact contract in this ticket.
8. `raw_1d` is always present; `raw_4h is None` iff `data_4h_available = False`; `raw_shared` is always present.
9. Every derived field in T5 has a same-model companion `{field_name}_status`.
10. Ticket-3 prerequisite 1d fields listed in this ticket are implemented.
11. The mandatory MVP field groups listed in this ticket are implemented.
12. Cross-timeframe MVP field `range_width_12bars_4h_vs_atr1d_pct` is implemented in `RawFeaturesShared`.
13. Volume spike ratio fields (`volume_quote_spike_1d`, `volume_quote_spike_4h`) are implemented.
14. The unresolved fields listed in this ticket are **not** implemented and are instead added to `docs/canonical/open_questions.md` together with the consolidated `freshness_distance_structural` consequence note.
15. Missing / Gap / Insufficient-History semantics behave exactly as defined in this ticket.
16. Tier-2 1d fallback semantics behave exactly as defined in this ticket.
17. EMA warm-up behavior uses SMA bootstrap and requires at least `2 × period` bars.
18. Numeric special-case handling (division by zero, non-finite upstream values, flat range, absolute pct, rank formula, no rounding) behaves exactly as defined in this ticket.
19. Type violations raise `TypeError`; content/precondition violations raise `ValueError`; no assertions are used for public precondition enforcement.
20. All configurable T5 parameters are sourced exclusively from the Ticket-1 config object.
21. Canonical docs listed in this ticket are updated in the same PR.
22. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
23. The ticket is archived in the same PR per workflow.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅
- **Config Invalid Value Handling:** ✅
- **Nullability / Companion status explicit:** ✅
- **Not-evaluable vs invalid explicit:** ✅
- **Deterministic output / same input = same output:** ✅
- **Strict preconditions at public-function entry:** ✅
- **No repository / storage access in T5:** ✅
- **No shortened-window fallback unless spec defines alternate field path:** ✅
- **EMA warm-up fixed:** ✅
- **No hidden event semantics introduced:** ✅

## Tests (required)

### 1. Input-/Precondition-Tests
Must cover at least:
- wrong argument types → `TypeError`
- invalid symbol content → `ValueError`
- `ohlcv_1d = []` → `ValueError`
- `ohlcv_4h = []` → `ValueError`
- unsorted OHLCV bars
- duplicate `close_time_utc_ms`
- future / partial bars
- inconsistent `BarClockContext`
- invalid config values for Class-2 parameters

### 2. Determinism-Tests
Must cover:
- identical OHLCV input + identical `BarClockContext` + identical config → identical feature outputs
- identical status-field outputs across repeated runs

### 3. Missing-/Gap-/Insufficient-History-Tests
Must cover:
- insufficient history
- gap in exact required input window
- `upstream_dependency_null`
- `invalid_upstream_value`
- no shortened-window fallback
- Tier-2 1d fallback path as spec-defined alternative, not shortened 4h field

### 4. Numeric-/Edge-Case-Tests
Must cover:
- division by zero
- flat range
- `_pct` vs `_pct_abs`
- rank computation on `0..100`
- tie handling in ranks via the explicit formula
- no rounding in T5
- EMA warm-up / SMA bootstrap / `2 × period`
- OHLCV bar with `NaN` close → all dependent fields `null` with `invalid_upstream_value`
- OHLCV bar with `inf` volume → dependent volume fields `null` with `invalid_upstream_value`

### 5. Field-specific reference tests for required MVP groups
Must cover at least:
- Ticket-3 1d prerequisite fields
- `bars_above_*`
- `bars_since_last_new_low_*`
- structural break cluster
- `close_vs_rolling_high_5_*_pct`
- `volume_spike_persistence_4h`
- `close_above_range_mid_ratio_*`
- `range_width_12bars_4h_vs_atr1d_pct` as a cross-timeframe shared field
- pullback / impulse segmentation outputs
- rank fields, including that `std_return_rank_12bars_4h_pct` is ranked over rolling 4h returns rather than raw close levels

### 6. Interface-/Bundle-Tests
Must cover:
- `raw_1d` always present
- `raw_4h is None` iff `data_4h_available = False`
- `raw_shared` always present
- `FeatureBundle` carries only allowed metadata
- no run / eligibility / state fields in `FeatureBundle`
- `compute_raw_shared(...)` can run with pre-built feature instances and no OHLCV input

### 7. Config-/Parameter-Tests
Must cover:
- Class-1 parameters are not configurable
- Class-2 parameters are configurable and read from Ticket-1 config only
- no module-local fallback defaults
- pullback / segmentation windows configurable
- `persistence_spike_threshold` configurable
- `min_bars_below_before_break` configurable

### Golden fixture strategy (required)
Golden tests use small hand-constructed OHLCV sequences with committed fixture files.

At minimum one committed golden fixture per named family:

- structural break cluster
- pullback / impulse segmentation
- rank fields
- streak / counter fields
- Tier-2 1d fallback path

A dedicated pullback golden must also cover the `not_evaluable` case where `impulse_high_idx <= impulse_start_idx`.

## Definition of Done (non-test AC items)

- `docs/canonical/open_questions.md` contains one consolidated entry covering:
  - `bars_since_last_volume_shift_event`
  - `dist_to_base_mid_pct`
  - `distance_to_range_high_pct_abs`
  - the reduced-input consequence for `freshness_distance_structural`
- canonical docs are updated for:
  - `features/` module structure
  - `FeatureBundle` interface contract
  - Missing / Gap / Fallback semantics
  - config parameters
  - mandatory MVP field groups
- `docs/canonical/VERIFICATION_FOR_AI.md` is updated with:
  - mandatory field-group lists
  - Missing / Gap / Fallback rules
  - EMA warm-up rule
  - rank formula
  - config-fixed vs config-driven parameter split

## Constraints / Invariants (must not change)

- [ ] Ticket 5 remains below axes / phase / state / ranking layers.
- [ ] Ticket 5 does not implement normalization utilities.
- [ ] Ticket 5 does not load data or access storage.
- [ ] Ticket 5 accepts Ticket-1 `BarClockContext`, not raw timestamps.
- [ ] Ticket 5 outputs are run-local in-memory artifacts only.
- [ ] Every derived field has a same-model companion status field.
- [ ] `raw_4h is None` iff `data_4h_available = False`.
- [ ] `raw_shared` is never `None`.
- [ ] Tier-2 1d fallback remains a spec-defined alternate path, not a shortened-window exception.
- [ ] Unresolved fields remain unresolved and are documented in `open_questions.md`.
- [ ] One ticket = one PR.
- [ ] No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

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
created_utc: "2026-04-18T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [1, 4]
gesamtkonzept_ref: "§19 Ticket 5"
related_issues: []
follow_ups:
  - "Ticket 6: implement normalization utilities and Tier-1 axes"
  - "Resolve `bars_since_last_volume_shift_event`, `dist_to_base_mid_pct`, and `distance_to_range_high_pct_abs` via canonical open questions before finalizing full freshness_distance_structural coverage"
```
