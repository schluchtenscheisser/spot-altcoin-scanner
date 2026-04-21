> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Implement invalidation + setup-cycle pre-state layer (Ticket 9)

## Context / Source

This ticket implements **Ticket 9** from the Independence-Release consolidated concept: the **invalidation + cycle** pre-state layer.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 9.

`depends_on: [8]` — requires:
- Ticket 8 (`phase interpreter`)
- and, through Ticket 8’s typed upstream contracts:
  - Ticket 6 (`tier1 axes`)
  - Ticket 7 (`tier2 simplified axes`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, older ticket assumptions, or archived ticket follow-up notes conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements the **Layer-4 invalidation and setup-cycle pre-state logic only**.

It implements:

- `scanner/state/invalidation.py`
- `scanner/state/cycle.py`
- the required typed read/output models in `scanner/state/models.py`

It does **not** implement:

- `scanner/state/freshness.py`
- `scanner/state/machine.py`
- final state assignment (`watch`, `early_ready`, `confirmed_ready`, `late`, `chased`, `rejected`)
- final cycle-end persistence writes triggered by actual state transitions
- entry logic
- ranking / decision buckets
- execution
- output/report logic
- repository access or persistence writes in the pure Ticket-9 computation function

### Layer-split clarification

Gesamtkonzept and the target repo structure explicitly split the `state/` layer into:

- `invalidation.py`
- `cycle.py`
- `freshness.py`
- `machine.py`
- `models.py`

Under this implementation split:

- **Ticket 9** is authoritative for:
  - structural invalidation rules
  - timing invalidation rules as pre-state signals
  - setup-cycle reset / new-cycle detection logic
  - resolved `setup_cycle_id` for the current run

- **Ticket 10** remains authoritative for:
  - state-freshness recomputation
  - final state transition selection
  - final transitions into `late`, `chased`, `rejected`
  - the single authoritative persistence write for state/cycle fields

### Critical implementation split

Ticket 9 computes and returns the deterministic pre-state invalidation/cycle contract.

Ticket 10 consumes that contract and:
- does **not** independently recompute `setup_cycle_id`
- takes the resolved `setup_cycle_id` from the Ticket-9 output bundle
- persists it as part of the authoritative state write
- writes `cycle_end_bar_index` / `cycle_end_timestamp` only when the State Machine actually transitions into `rejected` or `chased`

### Addendum / working-context checks

This ticket explicitly follows the addendum working-context leitplanken:

- **A.2 Schichtenarchitektur** — T9 remains strictly inside Layer 4 pre-state logic and does not leak into entry / decision / output / execution logic
- **A.3 `bar_clock.py` ist Fundamentmodul** — all `bars_since_*` counters consumed by T9 rely on canonical 4h-bar semantics
- **A.5 Persistenz ist fachlicher Kern** — T9 consumes persisted prior state/cycle/freshness context as a fachlich relevant input
- **A.6 Historie liefert Kontext, aber keinen Override** — prior persisted context informs invalidation/cycle continuity, but does not override current-run phase/axis evaluation
- **Teil B Präzisierungs-Check** — the `Persisted Candidate Context / Watchlist-Kontinuität` block is explicitly operationalized here for the T9/T10 boundary rather than guessed silently

---

## Goal

After this ticket is completed:

- `scanner/state/invalidation.py` computes the canonical structural/timing invalidation signals
- `scanner/state/cycle.py` computes canonical setup-cycle reset / new-cycle detection
- `scanner/state/models.py` contains:
  - `PersistedStateCycleContext`
  - `InvalidationCycleBundle`
- Ticket 9 consumes only typed current-run bundles, typed prior persisted context, and `cfg`
- Ticket 9 returns a deterministic typed in-memory invalidation/cycle result
- structural invalidation and timing invalidation remain strictly separated
- `new_cycle_detected` and `structural_invalidation` remain logically exclusive
- `resolved_setup_cycle_id` is computed once in Ticket 9 and later persisted by Ticket 10
- downstream Ticket 10 can consume a stable typed invalidation/cycle contract without recomputing cycle logic

---

## Scope

Allowed change surface:

- `scanner/state/invalidation.py` (new)
- `scanner/state/cycle.py` (new)
- `scanner/state/models.py` (new or extend if bootstrap already exists)
- `scanner/state/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.invalidation` and `cfg.cycle` defaults / merge / validation rules
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope

This ticket must not:

- implement `scanner/state/freshness.py`
- implement `scanner/state/machine.py`
- assign final states (`watch`, `early_ready`, `confirmed_ready`, `late`, `chased`, `rejected`)
- recompute state-based freshness from raw state-entry reference prices
- perform repository access or persistence writes in the pure computation function
- persist `cycle_end_bar_index` / `cycle_end_timestamp`
- compute or re-compute Tier-1 / Tier-2 / phase logic
- consume `FeatureBundle`, OHLCV bars, raw timestamps, or `now`
- introduce entry / ranking / execution / output logic
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2 and §19 Ticket 9
- `v2_1_abschnitt_5_invalidation_setup_cycle_rev3_aligned.md` — **the invalidation/cycle rules in this ticket operationalize Abschnitt 5; Codex must not reconstruct missing logic from free interpretation**
- `v2_1_abschnitt_4_state_machine_rev3_aligned.md` — authoritative for state enum, state-internal field semantics, and transition ordering around `new_cycle_detected`, `rejected`, `chased`
- Ticket 8 — typed `PhaseInterpretationBundle` contract
- Ticket 6 — typed `Tier1AxisBundle` contract
- Ticket 7 — typed `Tier2AxisBundle` contract

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

Repo process references:

- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed change (high-level)

### Before

- Ticket 8 provides the canonical Layer-3 phase interpretation.
- The repo does not yet expose a typed Layer-4 invalidation/cycle pre-state contract.
- Downstream state-machine work would otherwise be forced to reconstruct:
  - structural invalidation,
  - timing invalidation,
  - new-cycle detection,
  - and `setup_cycle_id` resolution
  ad hoc.

### After

- `scanner/state/invalidation.py` computes deterministic structural/timing invalidation signals from:
  - current phase result
  - current Tier-1 / Tier-2 bundles
  - prior persisted state/cycle/freshness context
- `scanner/state/cycle.py` computes deterministic cycle reset / new-cycle signals and the current run’s resolved `setup_cycle_id`
- `scanner/state/models.py` defines the typed read/output models for this boundary
- Ticket 10 can consume a single stable T9 contract instead of recomputing cycle logic

### Edge cases

- `market_phase = none` without prior tracked active-cycle context is **not** structural invalidation under G1
- `market_phase = none` after prior tracked active-cycle context in the same carried cycle path **is** structural invalidation under G1
- structural invalidation and timing invalidation must not both be true in the same T9 result
- `new_cycle_detected = true` and `structural_invalidation = true` must not coexist in the same T9 result
- first-seen symbols initialize `resolved_setup_cycle_id = 1` without creating a new-cycle event
- `market_phase = none` does **not** automatically imply `Z3 = false`; Z3 is evaluated against current hard-floor admissibility, not against the final phase label alone
- missing persisted history must not create synthetic structural invalidation, synthetic cycle-end events, or synthetic new-cycle resets

### Backward compatibility impact

- Config surface grows under `cfg.invalidation` and `cfg.cycle`
- a new typed in-memory T9 output contract is introduced for downstream Ticket 10
- this ticket does not expand persistence schema or repository methods
- this ticket does not reopen earlier T6/T7/T8 public interfaces

---

## Module and model structure (authoritative)

### Modules

- `scanner/state/invalidation.py`
- `scanner/state/cycle.py`
- `scanner/state/models.py`

### Public function

```python
def compute_invalidation_and_cycle(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    persisted_context: PersistedStateCycleContext,
    cfg: Config,
) -> InvalidationCycleBundle: ...
```

This is the sole public pure-computation entry point for Ticket 9.

No separate `symbol` parameter. No `FeatureBundle`. No OHLCV input. No raw timestamp or `now`. No repository handle or storage object.

### Internal helper split

Ticket 9 may implement internal helpers such as:

- `_compute_structural_invalidation(...)`
- `_compute_timing_invalidation(...)`
- `_resolve_cycle_reset(...)`

But the public contract remains the single typed function above.

---

## Input contract (authoritative)

### Accepted public input types

The public function accepts exactly:

- `phase_bundle: PhaseInterpretationBundle`
- `tier1_bundle: Tier1AxisBundle`
- `tier2_bundle: Tier2AxisBundle`
- `persisted_context: PersistedStateCycleContext`
- `cfg: Config`

Any other public input type is invalid and raises `TypeError`.

There is no dict-based loose input mode and no implicit coercion from mapping-like objects.

### Input-contract standard

> Erlaubte Input-Typen, Units, Koerzionsregeln und harte Rejection-Regeln sind vollständig spezifiziert. Mehrdeutige Inputs dürfen nicht stillschweigend umgedeutet werden.

### Current-run bundle consistency

The pure Ticket-9 computation function must reject inconsistent **current-run** bundle inputs.

Required same-run consistency covers current-run bundles only:

- `PhaseInterpretationBundle`
- `Tier1AxisBundle`
- `Tier2AxisBundle`

These must match on:

- `symbol`
- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`

If inconsistent:
- raise `ValueError`
- the error message must name the inconsistent field

There is no silent reconciliation.

### Persisted-context consistency

`PersistedStateCycleContext` is prior-run context and is **not** subject to same-run equality checks for:

- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`

It must, however, belong to the same `symbol`.

If `persisted_context.symbol != phase_bundle.symbol`:
- raise `ValueError`
- the error message must name `symbol`

### PersistedStateCycleContext validation

Ticket 9 introduces a typed persisted read model:

```python
@dataclass
class PersistedStateCycleContext:
    symbol: str

    current_setup_cycle_id: int | None
    previous_setup_cycle_id: int | None
    state_recorded_in_cycle_id: int | None

    prev_state_machine_state: str | None

    # the setup-cycle id under which `prev_state_machine_state` was recorded

    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None

    bars_since_state_entered: int | None
    bars_since_early_entered: int | None
    bars_since_confirmed_entered: int | None
    bars_since_cycle_end: int | None

    reclaim_below_reset_floor_seen_since_cycle_end: bool | None
```

#### Validation rules

- `symbol` must be non-empty `str`
- `current_setup_cycle_id`, `previous_setup_cycle_id`, `state_recorded_in_cycle_id`:
  - allowed: positive `int`, or `None`
  - rejected: `0`, negative integers, `bool`, non-integer numerics, strings, `NaN`, `inf`
  - semantics:
    - `current_setup_cycle_id` = the carried active cycle id for the current run before any Ticket-9 increment
    - `previous_setup_cycle_id` = the immediately prior cycle id, if known
    - `state_recorded_in_cycle_id` = the cycle id under which `prev_state_machine_state` was recorded
- `prev_state_machine_state`:
  - allowed closed set:
    - `"watch"`
    - `"early_ready"`
    - `"confirmed_ready"`
    - `"late"`
    - `"chased"`
    - `"rejected"`
    - or `None`
  - any other value → `ValueError`
- `freshness_distance_state_early`, `freshness_distance_state_confirmed`:
  - allowed: finite float/int in `0..100`, or `None`
  - rejected: `bool`, `NaN`, `inf`, `-inf`, values outside `0..100`
- `bars_since_state_entered`, `bars_since_early_entered`, `bars_since_confirmed_entered`, `bars_since_cycle_end`:
  - unit = canonical closed 4h bars
  - allowed: non-negative `int`, or `None`
  - rejected: `bool`, negative values, non-integer numerics, `NaN`, `inf`
- `reclaim_below_reset_floor_seen_since_cycle_end`:
  - allowed: `True`, `False`, or `None`
  - `None` means the optional Z5 support field is unavailable / not tracked in prior persistence
- bootstrap consistency rule:
  - `current_setup_cycle_id = None` is allowed only for first-seen / no-prior-cycle-context bootstrap cases
  - if `current_setup_cycle_id = None` while other prior-cycle continuity fields indicate non-bootstrap carried state, raise `ValueError`

#### Meaning of `None` in persisted context

- `None` means "not available from prior persisted context", not `0` and not `False`
- `None` must not be coerced via `bool(...)`
- history-dependent rules that need a missing field are not satisfiable from that field

### Freshness-source decision

Ticket 9 does **not** recompute state-based freshness.

Instead, Ticket 9 reads the persisted prior-run state/freshness context and uses it as the sole authoritative source for timing-invalidation inputs that depend on prior state progression.

The following fields are actively consumed by Ticket 9 computation:

- `prev_state_machine_state`
- `current_setup_cycle_id`
- `state_recorded_in_cycle_id`
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`
- `bars_since_cycle_end`
- `reclaim_below_reset_floor_seen_since_cycle_end` (only when optional Z5 is enabled)

The following fields may be carried in `PersistedStateCycleContext` for broader persistence continuity, diagnostics, or Ticket-10-side freshness/state updates, but Ticket 9 does not consume them in any invalidation rule or cycle-reset rule:

- `previous_setup_cycle_id`
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`

Ticket 10 (`freshness.py` + `machine.py`) remains responsible for:
- recomputing state-based freshness after the new state is determined
- updating the persisted state/freshness context for the next run

### Non-consumed broader persistence payload

The broader state/freshness persistence layer may contain additional fields such as:

- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`
- `cycle_end_bar_index`
- `cycle_end_timestamp`

These are not part of the minimal Ticket-9 pure-computation input contract.
They may be used by Ticket 10 / `freshness.py` / the persistence writer layer, but Ticket 9 must not use them to recompute state freshness or to drive invalidation logic directly.

---

## Output contract (authoritative)

Ticket 9 defines a typed pure-computation output model:

```python
@dataclass
class InvalidationCycleBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    structural_invalidation: bool
    structural_invalidation_reason: str | None

    timing_invalidation: bool
    timing_invalidation_reason: str | None

    new_cycle_detected: bool
    cycle_reason_code: str

    resolved_setup_cycle_id: int

    phase_floor_recovered_since_cycle_end: bool
    expansion_reset_condition_met: bool | None
    reclaim_reset_condition_met: bool | None
```

### Important note on bar-id field types

`daily_bar_id`, `intraday_bar_id`, and `data_4h_available` in `InvalidationCycleBundle` mirror the already-established upstream current-run bundle contracts from Tickets 6/7/8 exactly. Ticket 9 does not redefine their representation.

### Output semantics

- `structural_invalidation_reason` is populated iff `structural_invalidation = true`
- `timing_invalidation_reason` is populated iff:
  - `structural_invalidation = false`
  - and `timing_invalidation = true`
- if `structural_invalidation = true`, then:
  - `timing_invalidation = false`
  - `timing_invalidation_reason = None`
- `new_cycle_detected = true` implies:
  - `structural_invalidation = false`
- `resolved_setup_cycle_id` is never `None`
- first-seen initialization uses:
  - `new_cycle_detected = false`
  - `resolved_setup_cycle_id = 1`
  - `cycle_reason_code = "FIRST_CYCLE_INITIALIZED"`

### `cycle_reason_code` semantics

`cycle_reason_code` is **always** populated by Ticket 9.

Semantics:
- if `new_cycle_detected = true`, it carries the positive confirmation code for the detected cycle-reset path
- if `new_cycle_detected = false`, it carries the highest-priority blocking reason explaining why the current run did not qualify for a new cycle
- if the symbol is first-seen with no prior persisted cycle context, it carries `FIRST_CYCLE_INITIALIZED`

`cycle_reason_code` must therefore never be `None`.

### Closed enums

`structural_invalidation_reason` closed set:
- `"PHASE_TO_NONE"`
- `"INSUFFICIENT_TIER1_SUPPORT"`
- `"PRESSURE_BUILD_COMPRESSION_BREAK"`
- `"PRESSURE_BUILD_BASE_BREAK"`
- `"PRESSURE_BUILD_VOLUME_BREAK"`
- `"TREND_RESUME_TREND_BREAK"`
- `"TREND_RESUME_RECLAIM_BREAK"`
- `"TREND_RESUME_PULLBACK_FAILURE"`
- `"TREND_RESUME_REACCEL_FAILURE"`
- `"TRANSITION_RECLAIM_RECLAIM_BREAK"`
- `"TRANSITION_RECLAIM_BASE_BREAK"`
- `"TRANSITION_RECLAIM_VOLUME_BREAK"`
- or `None`

`timing_invalidation_reason` closed set:
- `"STATE_FRESHNESS_EARLY_MAXED"`
- `"STATE_FRESHNESS_CONFIRMED_MAXED"`
- `"EXPANSION_PROGRESS_MAXED"`
- `"STRUCTURAL_FRESHNESS_MAXED"`
- or `None`

`cycle_reason_code` closed set:
- `"NEW_CYCLE_AFTER_RESET"`
- `"NEW_CYCLE_AFTER_REJECTION"`
- `"NEW_CYCLE_AFTER_CHASED"`
- `"NEW_CYCLE_BLOCKED_NO_PRIOR_ENDED_CYCLE"`
- `"NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET"`
- `"NEW_CYCLE_BLOCKED_MIN_BARS_NOT_MET"`
- `"NEW_CYCLE_BLOCKED_PHASE_FLOOR_NOT_RECOVERED"`
- `"NEW_CYCLE_BLOCKED_STRUCTURAL_INVALIDATION_ACTIVE"`
- `"NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET"`
- `"FIRST_CYCLE_INITIALIZED"`

### Diagnostic-boolean semantics

- `phase_floor_recovered_since_cycle_end`
  - `True` iff at least one positive phase is currently hard-floor-admissible under the resolved Ticket-8 phase result
  - `False` otherwise
  - this is evaluated from phase-floor admissibility, **not** from the final `market_phase` label alone

- `expansion_reset_condition_met`
  - `True` iff Z1 is satisfied
  - `False` iff `expansion_progress_structural` is evaluable and Z1 is not satisfied
  - `None` iff the current expansion input is not reliably evaluable

- `reclaim_reset_condition_met`
  - `True` iff optional Z5 is enabled and satisfied
  - `False` iff optional Z5 is enabled and not satisfied
  - `None` iff Z5 is disabled or not evaluable from the required current/persisted inputs

---

## Invalidation logic (authoritative)

Ticket 9 bundles invalidation logic into two strictly ordered stages:

1. structural invalidation
2. timing invalidation

Timing invalidation is evaluated **only if** the resolved structural invalidation result is `false`.

If `structural_invalidation = true`, then:
- `timing_invalidation = false` by definition
- `timing_invalidation_reason = None`
- the setup is treated as structurally broken, not as merely timing-aged

### Structural invalidation rule set

Ticket 9 computes `structural_invalidation` from:

- global structural rules:
  - G1 `PHASE_TO_NONE`
  - G2 `INSUFFICIENT_TIER1_SUPPORT`
  - G3 as fachliche rationale only, not as an independent evaluation path
- phase-specific structural hold rules:
  - `pressure_build`: P1, P2, P3
  - `trend_resume`: T1, T2, T3, T4
  - `transition_reclaim`: R1, R2, R3

#### G1 trigger condition

`market_phase = none` becomes `structural_invalidation = true` under G1 only if all of the following hold:

1. current run’s resolved phase result is `market_phase = "none"`
2. prior persisted context exists for the same symbol
3. prior persisted state is one of:
   - `watch`
   - `early_ready`
   - `confirmed_ready`
   - `late`
4. prior active-state evidence belongs to the carried current setup-cycle context:
   - `state_recorded_in_cycle_id == current_setup_cycle_id`

#### G1 non-trigger cases

G1 must not trigger when any of the following is true:

- first-seen symbol
- no persisted prior state context
- prior persisted state is `None`
- prior persisted state is terminal only (`rejected` or `chased`) without a newly reactivated tracked cycle
- symbol has never entered a tracked active cycle path in persisted context
- prior active-state evidence belongs only to an older cycle and not to the carried current setup-cycle context

#### G2

At least two phase-critical Tier-1 axes become `null` / `not_evaluable`, and the current phase is no longer reliably evaluable.

#### G3

G3 is **not** an independently evaluable rule in Ticket 9.

It is the fachliche rationale behind the phase-specific hold rules P1–P3, T1–T4, and R1–R3.
Structural invalidation from floor loss is fully operationalized through those phase-specific rules.
Ticket 9 must not implement a separate G3 evaluation path.

#### `pressure_build` rules

P1:
- `compression_strength < cfg.invalidation.pressure_build.min_compression_hold`
- default: `45`
- reason: `"PRESSURE_BUILD_COMPRESSION_BREAK"`

P2:
- `base_integrity_simplified < cfg.invalidation.pressure_build.min_base_hold`
- default: `35`
- reason: `"PRESSURE_BUILD_BASE_BREAK"`

P3:
- `volume_regime_shift < cfg.invalidation.pressure_build.min_volume_shift_hold`
- default: `30`
- reason: `"PRESSURE_BUILD_VOLUME_BREAK"`

Important exclusion:
- high `expansion_progress_structural` is **not** a structural invalidation rule for `pressure_build`

#### `trend_resume` rules

T1:
- `trend_strength < cfg.invalidation.trend_resume.min_trend_hold`
- default: `40`
- reason: `"TREND_RESUME_TREND_BREAK"`

T2:
- `reclaim_progress < cfg.invalidation.trend_resume.min_reclaim_hold`
- default: `30`
- reason: `"TREND_RESUME_RECLAIM_BREAK"`

T3:
- `pullback_quality_simplified` evaluable
- and `< cfg.invalidation.trend_resume.min_pullback_quality_hold`
- default: `20`
- reason: `"TREND_RESUME_PULLBACK_FAILURE"`

T4:
- `reacceleration_strength_simplified` evaluable
- and `< cfg.invalidation.trend_resume.min_reaccel_hold`
- after the symbol has already been at least `early_ready` or `confirmed_ready`
- default: `20`
- reason: `"TREND_RESUME_REACCEL_FAILURE"`

T4 is persistence-dependent and must not trigger on:
- first-seen symbols
- symbols that have never reached `early_ready`
- symbols that have never reached `confirmed_ready`

#### `transition_reclaim` rules

R1:
- `reclaim_progress < cfg.invalidation.transition_reclaim.min_reclaim_hold`
- default: `30`
- reason: `"TRANSITION_RECLAIM_RECLAIM_BREAK"`

R2:
- `base_integrity_simplified` evaluable
- and `< cfg.invalidation.transition_reclaim.min_base_hold`
- default: `30`
- reason: `"TRANSITION_RECLAIM_BASE_BREAK"`

R3:
- `volume_regime_shift < cfg.invalidation.transition_reclaim.min_volume_shift_hold`
- default: `25`
- reason: `"TRANSITION_RECLAIM_VOLUME_BREAK"`

### Timing invalidation rule set

Ticket 9 computes `timing_invalidation` only when `structural_invalidation = false`.

Timing invalidation rules are:

TI1:
- `freshness_distance_state_early >= cfg.invalidation.timing.max_state_freshness`
- default: `100`
- reason: `"STATE_FRESHNESS_EARLY_MAXED"`

TI2:
- `freshness_distance_state_confirmed >= cfg.invalidation.timing.max_state_freshness`
- default: `100`
- reason: `"STATE_FRESHNESS_CONFIRMED_MAXED"`

TI3:
- `expansion_progress_structural >= cfg.invalidation.timing.max_expansion_progress`
- default: `95`
- reason: `"EXPANSION_PROGRESS_MAXED"`

TI4:
- `freshness_distance_structural >= cfg.invalidation.timing.max_structural_freshness`
- and prior persisted state is at least `early_ready`
- default: `90`
- reason: `"STRUCTURAL_FRESHNESS_MAXED"`

TI4 must not be evaluated as satisfied for:
- first-seen symbols
- symbols with no persisted prior active-state context
- symbols that have never reached `early_ready`

### Multiple-hit resolution

If multiple structural rules hit simultaneously:
- `structural_invalidation = true`
- `structural_invalidation_reason` is the highest-priority code in this order:
  1. `PHASE_TO_NONE`
  2. `INSUFFICIENT_TIER1_SUPPORT`
  3. phase-specific reclaim/trend breaks
  4. base/compression/volume breaks
  5. reaccel/pullback failures

If multiple timing rules hit simultaneously:
- `timing_invalidation = true`
- `timing_invalidation_reason` is the highest-priority code in this order:
  1. `EXPANSION_PROGRESS_MAXED`
  2. `STATE_FRESHNESS_CONFIRMED_MAXED`
  3. `STATE_FRESHNESS_EARLY_MAXED`
  4. `STRUCTURAL_FRESHNESS_MAXED`

### Nullability / evaluability rule

For invalidation rules, `null` means "not reliably evaluable", not "passes" and not "fails".

Rule consequences:
- a rule that depends on a `null` optional field does not trigger from that field alone
- `null` must never be coerced to `0` or `false`
- persistence-dependent rules (G1, T4, TI1, TI2, TI4) require the relevant prior context; without it, those rules are not satisfiable

> Nicht evaluierbar / nicht bewertet und fachlich negativ bewertet sind getrennte Zustände und müssen im Code getrennt erhalten bleiben.

---

## Setup-cycle logic (authoritative)

Ticket 9 is authoritative for new-cycle detection.

### New-cycle detection rule set

`new_cycle_detected = true` only if all required reset conditions are satisfied:

Z1 — expansion reset
- `expansion_progress_structural <= cfg.cycle.reset_max_expansion`
- default: `15`

Z2 — minimum distance from prior cycle end
- `bars_since_cycle_end >= cfg.cycle.min_bars_reset`
- default: `3`

Z3 — renewed positive structure
- at least one positive phase is currently hard-floor-admissible under the resolved Ticket-8 phase result
- this is evaluated from current hard-floor admissibility, not from the final `market_phase` label alone
- Ticket 9 must not recompute phase logic locally

Z4 — no active structural invalidation
- `structural_invalidation = false`

### Optional reset filter

Ticket 9 may support Z5 exactly as a config-gated extension:

Z5 — reclaim reset
- `reclaim_below_reset_floor_seen_since_cycle_end = True`
- and current `reclaim_progress` rises again above the relevant phase floor

Baseline v2.1:
- Z5 is disabled by default
- Ticket 9 must not require Z5 for baseline new-cycle detection

### Logical exclusivity

Because Z4 is required:
- `new_cycle_detected = true` implies `structural_invalidation = false`

Therefore, the same Ticket-9 result must not contain both:
- `new_cycle_detected = true`
- `structural_invalidation = true`

### Prior-cycle requirement

New-cycle detection requires a real prior ended cycle context.

If prior ended-cycle context is absent:
- Z2 is not satisfiable
- `new_cycle_detected = false`
- no synthetic reset is inferred from missing history

### First-seen / no-prior-cycle semantics

For first-seen symbols with no prior persisted cycle context:

- `new_cycle_detected = false`
- `resolved_setup_cycle_id = 1`
- `cycle_reason_code = "FIRST_CYCLE_INITIALIZED"`

This is the first tracked cycle initialization, not a new-cycle event.

### Resolved cycle id

If `new_cycle_detected = true`:
- Ticket 9 resolves `resolved_setup_cycle_id = current_setup_cycle_id + 1`

If `new_cycle_detected = false`:
- Ticket 9 resolves `resolved_setup_cycle_id = current_setup_cycle_id`
- or `1` for first-seen initialization

A non-first-seen symbol with missing `current_setup_cycle_id` is invalid persisted context and must raise `ValueError` rather than yielding a nullable or synthetic cycle id.

### `cycle_reason_code` resolution

Positive codes:
- if `new_cycle_detected = true` and prior persisted state is `rejected`:
  - `cycle_reason_code = "NEW_CYCLE_AFTER_REJECTION"`
- if `new_cycle_detected = true` and prior persisted state is `chased`:
  - `cycle_reason_code = "NEW_CYCLE_AFTER_CHASED"`
- if `new_cycle_detected = true` otherwise:
  - `cycle_reason_code = "NEW_CYCLE_AFTER_RESET"`

Blocking-code priority when `new_cycle_detected = false` and not first-seen:
1. `NEW_CYCLE_BLOCKED_NO_PRIOR_ENDED_CYCLE`
2. `NEW_CYCLE_BLOCKED_STRUCTURAL_INVALIDATION_ACTIVE`
3. `NEW_CYCLE_BLOCKED_EXPANSION_NOT_RESET`
4. `NEW_CYCLE_BLOCKED_MIN_BARS_NOT_MET`
5. `NEW_CYCLE_BLOCKED_PHASE_FLOOR_NOT_RECOVERED`
6. `NEW_CYCLE_BLOCKED_RECLAIM_RESET_NOT_MET` (only when Z5 is enabled)

This blocking-code priority is semantically chosen for diagnostics and does not redefine the logical requirement that Z1–Z4 all must hold. `NEW_CYCLE_BLOCKED_STRUCTURAL_INVALIDATION_ACTIVE` is prioritized immediately after the no-prior-ended-cycle bootstrap blocker because an active structural invalidation means the setup is still fundamentally broken, regardless of whether reset-distance or expansion-reset conditions also fail in the same run.

### Reset consequences of a new cycle

If a new cycle is detected, the current run is resolved as a fresh cycle with:

- state restarting at `watch`
- `bars_since_early_entered = null`
- `bars_since_confirmed_entered = null`
- `freshness_distance_state_early = null`
- `freshness_distance_state_confirmed = null`

These reset consequences are determined by the cycle logic in Ticket 9, but are written persistently only by the final Ticket-10 state write.

### No heuristic reconstruction

Ticket 9 must not infer a new cycle from:
- price pullback alone
- missing state cache
- missing cycle-end cache
- “probably reset” heuristics outside Z1–Z4 (+ optional Z5 if enabled)

New-cycle detection is strictly rule-based and persistence-aware.

---

## Persistence split with Ticket 10 (authoritative)

Ticket 9 is **not** the final persistence writer for cycle-end fields.

### Ticket 9 responsibilities

Ticket 9 computes and returns the pre-state cycle / invalidation signals:

- `structural_invalidation`
- `structural_invalidation_reason`
- `timing_invalidation`
- `timing_invalidation_reason`
- `new_cycle_detected`
- `cycle_reason_code`
- `resolved_setup_cycle_id`
- §9.3 diagnostic booleans

Ticket 9 may signal that a cycle-ending condition would lead to a terminal state if the State Machine later accepts that transition.

Ticket 9 does **not** perform the final persistence write of:
- `cycle_end_bar_index`
- `cycle_end_timestamp`

### Ticket 10 responsibilities

Ticket 10 (`freshness.py` + `machine.py`) remains authoritative for:

- final `state_machine_state`
- final transition into `rejected` or `chased`
- the single authoritative persistence write that marks cycle end
- persistence updates of state-internal counters and state/freshness context for the next run

Therefore:
- if Ticket 10 transitions the symbol into `rejected` or `chased`, Ticket 10 writes:
  - `cycle_end_bar_index`
  - `cycle_end_timestamp`
- if Ticket 10 does not perform such a terminal transition, these fields are not newly written in that run

Ticket 10 does not independently recompute `setup_cycle_id`.
It takes the resolved `setup_cycle_id` from the Ticket-9 output bundle and persists that value as part of the authoritative state write.

### No double-writer rule

There must be exactly one authoritative persistence writer for:
- `state_machine_state`
- `setup_cycle_id`
- `cycle_end_bar_index`
- `cycle_end_timestamp`
- `bars_since_cycle_end`
- state-internal freshness fields

That writer is the final state-persistence step after Ticket 10 has resolved the current run’s state.

Ticket 9 must not create a competing partial-write path for those fields.

---

## Config contract

All new config keys live under:
- `cfg.invalidation`
- `cfg.cycle`

### Merge semantics

> Partial overrides in `cfg.invalidation` and `cfg.cycle` are merged field-by-field with central defaults; missing sub-keys are not treated as invalid. Invalid values (wrong type, non-finite, out of range) produce a clear `ValueError` that includes the key name and invalid value.

### Numeric robustness

> Nicht-finite numerische Werte (`NaN`, `inf`, `-inf`) gelten als ungültige bzw. nicht auswertbare Inputs und dürfen nicht in numerisch aussehende Outputs durchgereicht werden.

### Nullability

> Semantisch nullable Eingaben und Diagnostikfelder dürfen nicht implizit via `bool(...)` zu `false` kollabieren. `None` bleibt semantisch von `False` getrennt.

### Determinism

> Bei identischem Input und identischer Config sind Auswahl, Reihenfolge, Status und Gründe identisch.

### `cfg.invalidation.pressure_build`

| Key | Default | Type | Validation |
|---|---|---|---|
| `min_compression_hold` | `45` | number | finite, `0..100` |
| `min_base_hold` | `35` | number | finite, `0..100` |
| `min_volume_shift_hold` | `30` | number | finite, `0..100` |

### `cfg.invalidation.trend_resume`

| Key | Default | Type | Validation |
|---|---|---|---|
| `min_trend_hold` | `40` | number | finite, `0..100` |
| `min_reclaim_hold` | `30` | number | finite, `0..100` |
| `min_pullback_quality_hold` | `20` | number | finite, `0..100` |
| `min_reaccel_hold` | `20` | number | finite, `0..100` |

### `cfg.invalidation.transition_reclaim`

| Key | Default | Type | Validation |
|---|---|---|---|
| `min_reclaim_hold` | `30` | number | finite, `0..100` |
| `min_base_hold` | `30` | number | finite, `0..100` |
| `min_volume_shift_hold` | `25` | number | finite, `0..100` |

### `cfg.invalidation.timing`

| Key | Default | Type | Validation |
|---|---|---|---|
| `max_state_freshness` | `100` | number | finite, `0..100` |
| `max_expansion_progress` | `95` | number | finite, `0..100` |
| `max_structural_freshness` | `90` | number | finite, `0..100` |

### `cfg.cycle`

| Key | Default | Type | Validation |
|---|---|---|---|
| `reset_max_expansion` | `15` | number | finite, `0..100` |
| `min_bars_reset` | `3` | int | `>= 0` |
| `enable_reclaim_reset_filter` | `False` | bool | bool only |
| `reclaim_reset_floor` | `20` | number | finite, `0..100` |

Missing keys fall back to these defaults. Invalid values raise `ValueError` naming the key and invalid value.

---

## Canonical docs to update

- `docs/canonical/ARCHITECTURE.md` — add `scanner/state/invalidation.py`, `scanner/state/cycle.py`, and the T9/T10 split
- `docs/canonical/DATA_MODEL.md` — add `PersistedStateCycleContext` and `InvalidationCycleBundle`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` — document 4h-bar counter semantics, state/cycle persistence split, and first-seen cycle initialization
- `docs/canonical/GLOSSARY.md` — add structural/timing invalidation terms, cycle reason codes, and first-cycle initialization semantics
- `docs/canonical/VERIFICATION_FOR_AI.md` — add the T9 rules, defaults, diagnostics, and T9/T10 split

---

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Authority precedence:** If older repo-canonical docs, archived tickets, or existing code differ from Abschnitt 5 / Abschnitt 4 / Gesamtkonzept, the authoritative source set wins.
- **Docs in same PR:** Update all listed canonical docs in the same PR as the code changes.
- **Docs first or alongside code:** Do not leave a merged PR where code changes exist without the corresponding canonical Ticket-9 contract updates.
- **Strict layer boundary:** Ticket 9 must not implement `freshness.py`, `machine.py`, entry logic, ranking, execution, or output/report logic.
- **Reader/writer split:** Ticket 9 reads prior persisted state/cycle/freshness context; Ticket 10 writes the final state/cycle/freshness persistence update.
- **No setup-cycle recomputation in Ticket 10:** Ticket 10 must consume the resolved `setup_cycle_id` from the Ticket-9 bundle and must not recompute cycle logic independently.
- **Structural suppresses timing:** If `structural_invalidation = true`, then `timing_invalidation = false` by definition.
- **No contradictory signals:** `new_cycle_detected = true` and `structural_invalidation = true` must not coexist in the same Ticket-9 result.
- **G3 is not a second path:** Ticket 9 must not implement a separate G3 evaluation path beyond P1–P3 / T1–T4 / R1–R3.
- **No phase recomputation in cycle logic:** Z3 must be evaluated from the resolved current-run phase-floor admissibility already available from Ticket 8; Ticket 9 must not recompute phase logic locally.
- **No heuristic reconstruction:** Missing prior persistence must not create synthetic cycle-end events, synthetic new-cycle resets, or inferred prior active-cycle membership.
- **No bool()-coercion of nullable values:** `None` remains semantically distinct from `0` and `False`.
- **No silent current-run bundle reconciliation:** mismatched current-run bundle identity is a hard error.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**
- **One ticket = one PR.**

---

## Acceptance Criteria (deterministic)

1. `scanner/state/invalidation.py`, `scanner/state/cycle.py`, and `scanner/state/models.py` exist.
2. `compute_invalidation_and_cycle(phase_bundle, tier1_bundle, tier2_bundle, persisted_context, cfg)` is the sole public Ticket-9 pure-computation entry point.
3. Ticket 9 consumes only `PhaseInterpretationBundle`, `Tier1AxisBundle`, `Tier2AxisBundle`, `PersistedStateCycleContext`, and `cfg`.
4. Ticket 9 does not consume `FeatureBundle`, OHLCV, raw timestamps, repositories, or storage handles in its pure computation function.
5. Public input type mismatches raise `TypeError`.
6. Current-run bundle metadata mismatches (`symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`) raise `ValueError`.
7. Persisted-context symbol mismatch raises `ValueError`.
8. Invalid persisted context values (bad enum, negative counter, non-finite freshness, invalid cycle id) raise `ValueError`.
9. `PersistedStateCycleContext` exists with exactly the fields defined in this ticket.
10. `InvalidationCycleBundle` exists with exactly the fields defined in this ticket, including §9.3 diagnostic booleans.
11. Structural invalidation is evaluated before timing invalidation.
12. If `structural_invalidation = true`, then `timing_invalidation = false` and `timing_invalidation_reason = None`.
13. G1 behaves exactly as defined here, including:
    - prior active states set = `{watch, early_ready, confirmed_ready, late}`
    - no trigger from terminal-only or missing prior context
    - no trigger from stale prior-cycle evidence
14. G2 behaves exactly as defined here.
15. `pressure_build` structural rules P1/P2/P3 behave exactly as defined here.
16. High `expansion_progress_structural` alone does not structurally invalidate `pressure_build`.
17. `trend_resume` structural rules T1/T2/T3/T4 behave exactly as defined here, including the persistence guard on T4.
18. `transition_reclaim` structural rules R1/R2/R3 behave exactly as defined here.
19. Ticket 9 does not implement an independent separate G3 evaluation path.
20. Timing rules TI1/TI2/TI3/TI4 behave exactly as defined here, including the TI4 state guard.
21. Multiple-hit structural reasons and multiple-hit timing reasons resolve to exactly one primary reason using the specified priority order.
22. `new_cycle_detected` is true only when Z1–Z4 are all satisfied (plus Z5 if enabled).
23. Z3 is evaluated from current hard-floor admissibility, not from the final `market_phase` label alone.
24. `market_phase = none` does not automatically imply `Z3 = false`.
25. `new_cycle_detected = true` implies `structural_invalidation = false`.
26. First-seen symbols produce:
    - `new_cycle_detected = false`
    - `resolved_setup_cycle_id = 1`
    - `cycle_reason_code = "FIRST_CYCLE_INITIALIZED"`
27. `resolved_setup_cycle_id` is never `None`.
28. `cycle_reason_code` is always populated.
29. Ticket 10 is documented as the single authoritative persistence writer for:
    - `state_machine_state`
    - `setup_cycle_id`
    - `cycle_end_bar_index`
    - `cycle_end_timestamp`
    - `bars_since_cycle_end`
    - state-internal freshness fields
30. Config defaults, merge semantics, validation, and invalid-value failures behave exactly as defined here.
31. Canonical docs listed in this ticket are updated in the same PR.
32. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
33. The ticket is archived in the same PR according to workflow.

---

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ covered — all `cfg.invalidation` / `cfg.cycle` keys have explicit defaults
- **Config Invalid Value Handling:** ✅ covered — wrong type / non-finite / out-of-range values raise `ValueError`
- **Nullability / kein bool()-Coercion:** ✅ covered — nullable persisted fields and diagnostic fields remain semantically distinct from `False`
- **Not-evaluated vs failed getrennt:** ✅ covered — missing prior context and hard-negative evaluation remain distinct
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ covered — pure Ticket-9 function performs no persistence writes
- **Deterministische Reihenfolge / Reason-Priorität:** ✅ covered — both invalidation categories use explicit multiple-hit priority
- **Input contract explicit:** ✅ covered — allowed types, units, and hard rejection rules are explicit
- **No synthetic history reconstruction:** ✅ covered — missing prior context does not create synthetic reset or prior activity
- **Current-run / prior-run split explicit:** ✅ covered — same-run bundle identity checks do not apply to prior-run context
- **Cycle-id initialization explicit:** ✅ covered — first-seen initializes to `1`

---

## Tests (required if logic changes)

### Category A — Public input contract / type validation

#### A1 — accepted typed inputs
- valid `PhaseInterpretationBundle`
- valid `Tier1AxisBundle`
- valid `Tier2AxisBundle`
- valid `PersistedStateCycleContext`
- valid `cfg`
- expected: computation succeeds

#### A2 — wrong public input type
- non-dataclass mapping / wrong object passed into the public function
- expected: `TypeError`

#### A3 — current-run bundle identity mismatch
- mismatch across current-run bundles in:
  - `symbol`
  - `daily_bar_id`
  - `intraday_bar_id`
  - `data_4h_available`
- expected: `ValueError` naming the mismatched field

#### A4 — persisted symbol mismatch
- `PersistedStateCycleContext.symbol` differs from current-run symbol
- expected: `ValueError`

#### A5 — dangerous but parseable persisted input
- `bars_since_early_entered=True`
- expected: `ValueError` (bool is invalid even though Python treats it as int)

---

### Category B — Structural vs timing precedence

#### B1 — structural true suppresses timing
- fixture satisfies one structural rule and one timing rule simultaneously
- expected:
  - `structural_invalidation = true`
  - `timing_invalidation = false`
  - `timing_invalidation_reason = None`

#### B2 — timing only when structure intact
- fixture satisfies TI-rule(s) but no structural rule
- expected:
  - `structural_invalidation = false`
  - `timing_invalidation = true`

---

### Category C — G1 semantics

#### C1 — G1 triggers after prior tracked active cycle
- `market_phase = none`
- prior persisted state in `{watch, early_ready, confirmed_ready, late}`
- `state_recorded_in_cycle_id == current_setup_cycle_id`
- expected:
  - `structural_invalidation = true`
  - `structural_invalidation_reason = "PHASE_TO_NONE"`

#### C2 — `market_phase = none` without prior active cycle
- first-seen or no prior active tracked state
- expected:
  - G1 does not trigger

#### C3 — prior terminal-only state does not satisfy G1
- prior state only `rejected` or `chased`
- expected:
  - G1 does not trigger by that evidence alone

#### C4 — stale prior-cycle evidence excluded
- prior active state exists but belongs to older cycle, not carried current cycle
- expected:
  - G1 does not trigger

---

### Category D — Global / phase-specific structural rules

#### D1 — G2 insufficient Tier-1 support
- at least two phase-critical Tier-1 axes become `null` / `not_evaluable`
- expected:
  - `structural_invalidation = true`
  - `structural_invalidation_reason = "INSUFFICIENT_TIER1_SUPPORT"`

#### D2 — `pressure_build` P1
- `compression_strength < min_compression_hold`
- expected reason = `"PRESSURE_BUILD_COMPRESSION_BREAK"`

#### D3 — `pressure_build` P2
- `base_integrity_simplified < min_base_hold`
- expected reason = `"PRESSURE_BUILD_BASE_BREAK"`

#### D4 — `pressure_build` P3
- `volume_regime_shift < min_volume_shift_hold`
- expected reason = `"PRESSURE_BUILD_VOLUME_BREAK"`

#### D5 — `pressure_build` high expansion is not structural break
- very high `expansion_progress_structural`
- no P1/P2/P3 hit
- expected:
  - no structural invalidation from expansion alone

#### D6 — `trend_resume` T1
- expected reason = `"TREND_RESUME_TREND_BREAK"`

#### D7 — `trend_resume` T2
- expected reason = `"TREND_RESUME_RECLAIM_BREAK"`

#### D8 — `trend_resume` T3
- expected reason = `"TREND_RESUME_PULLBACK_FAILURE"`

#### D9 — T4 valid persistence-dependent trigger
- prior state history shows at least `early_ready` or `confirmed_ready`
- `reacceleration_strength_simplified < min_reaccel_hold`
- expected reason = `"TREND_RESUME_REACCEL_FAILURE"`

#### D10 — T4 first-seen / never-early / never-confirmed guard
- `reacceleration_strength_simplified < min_reaccel_hold`
- but no qualifying prior persisted state
- expected:
  - T4 does not trigger

#### D11 — `transition_reclaim` R1
- expected reason = `"TRANSITION_RECLAIM_RECLAIM_BREAK"`

#### D12 — `transition_reclaim` R2
- expected reason = `"TRANSITION_RECLAIM_BASE_BREAK"`

#### D13 — `transition_reclaim` R3
- expected reason = `"TRANSITION_RECLAIM_VOLUME_BREAK"`

#### D14 — G3 no separate evaluation path
- fixture where a phase-specific hold rule fails
- expected:
  - structural invalidation comes from P/T/R rule only
  - no independent separate G3 path / reason is emitted

---

### Category E — Timing invalidation rules

#### E1 — TI1
- persisted `freshness_distance_state_early >= max_state_freshness`
- expected:
  - `timing_invalidation = true`
  - reason = `"STATE_FRESHNESS_EARLY_MAXED"`

#### E2 — TI2
- persisted `freshness_distance_state_confirmed >= max_state_freshness`
- expected:
  - `timing_invalidation = true`
  - reason = `"STATE_FRESHNESS_CONFIRMED_MAXED"`

#### E3 — TI3
- `expansion_progress_structural >= max_expansion_progress`
- expected:
  - `timing_invalidation = true`
  - reason = `"EXPANSION_PROGRESS_MAXED"`

#### E4 — TI4 with valid state guard
- `freshness_distance_structural >= max_structural_freshness`
- prior persisted state at least `early_ready`
- expected:
  - `timing_invalidation = true`
  - reason = `"STRUCTURAL_FRESHNESS_MAXED"`

#### E5 — TI4 for first-seen / never-early
- same structural freshness breach
- but no qualifying prior persisted state
- expected:
  - TI4 does not trigger

#### E6 — null timing inputs do not coerce
- required timing input is `None`
- expected:
  - the affected TI-rule does not trigger from that field
  - no coercion to `0` / `false`

---

### Category F — Multiple-hit priority

#### F1 — multiple structural hits
- fixture hits more than one structural rule
- expected:
  - exactly one primary `structural_invalidation_reason`
  - chosen by the specified priority order

#### F2 — multiple timing hits
- fixture hits more than one timing rule
- expected:
  - exactly one primary `timing_invalidation_reason`
  - chosen by the specified priority order

---

### Category NC — New-cycle detection

#### NC1 — positive new cycle via Z1–Z4
- reset expansion met
- min bars since cycle end met
- positive phase floors recovered
- no structural invalidation
- expected:
  - `new_cycle_detected = true`
  - incremented `resolved_setup_cycle_id`

#### NC2 — Z1 fail
- expansion not reset
- expected:
  - `new_cycle_detected = false`
  - `expansion_reset_condition_met = false`
  - blocking `cycle_reason_code`

#### NC3 — Z2 fail
- insufficient `bars_since_cycle_end`
- expected:
  - `new_cycle_detected = false`
  - blocking `cycle_reason_code`

#### NC4 — Z3 fail
- no positive phase currently hard-floor-admissible
- expected:
  - `new_cycle_detected = false`
  - `phase_floor_recovered_since_cycle_end = false`
  - blocking `cycle_reason_code`

#### NC4a — Z3 is evaluated from hard-floor admissibility, not from `market_phase` label alone
- fixture: current run resolves `market_phase = none` because top score is below the global confidence floor
- but at least one positive phase is still hard-floor-admissible under the resolved Ticket-8 result
- and Z1 / Z2 / Z4 are satisfied
- expected:
  - Z3 is treated as satisfied
  - `phase_floor_recovered_since_cycle_end = true`
  - Ticket 9 does not recompute phase logic locally
  - new-cycle eligibility depends on Z1/Z2/Z4 (+ optional Z5 if enabled), not on `market_phase != none`

#### NC5 — Z4 fail
- `structural_invalidation = true`
- expected:
  - `new_cycle_detected = false`
  - blocking `cycle_reason_code`

#### NC6 — optional Z5 disabled
- Z1–Z4 pass, Z5 not provided
- expected:
  - new cycle still allowed under baseline v2.1
  - `reclaim_reset_condition_met = None`

#### NC7 — optional Z5 enabled and unmet
- config enables Z5, reclaim reset not satisfied
- expected:
  - no new cycle
  - `reclaim_reset_condition_met = false`
  - blocking `cycle_reason_code`

---

### Category H — Exklusivität / first-seen / initialization

#### H1 — new cycle and structural invalidation mutually exclusive
- fixture attempts to combine both
- expected:
  - impossible final result
  - `new_cycle_detected = true` requires `structural_invalidation = false`

#### H2 — first-seen initialization
- no prior persisted cycle context
- expected:
  - `new_cycle_detected = false`
  - `resolved_setup_cycle_id = 1`
  - `cycle_reason_code = "FIRST_CYCLE_INITIALIZED"`

#### H3 — no synthetic cycle-end / no synthetic reset from missing history
- missing prior cycle-end context
- expected:
  - no inferred ended cycle
  - no new-cycle detection from heuristics
  - blocking `cycle_reason_code = "NEW_CYCLE_BLOCKED_NO_PRIOR_ENDED_CYCLE"`

---

### Category I — Output-contract tests

#### I1 — required fields present
- `InvalidationCycleBundle` contains all ticket-defined fields, including §9.3 diagnostics

#### I2 — reason/nullability semantics
- `structural_invalidation_reason` populated iff structural is true
- `timing_invalidation_reason` populated iff timing is true
- `cycle_reason_code` always populated

#### I3 — `resolved_setup_cycle_id` never null
- including first-seen
- including no-new-cycle
- including detected new cycle

#### I4 — spec diagnostics presence
- §9.3 diagnostic fields exist and are typed exactly as specified

---

### Category J — Determinism

#### J1 — identical input + identical config
- expected:
  - identical invalidation flags
  - identical reasons
  - identical `resolved_setup_cycle_id`
  - identical diagnostic booleans

---

### Category K — Config / numeric robustness / nullability

#### K1 — missing-key defaults
- partial override under `cfg.invalidation` or `cfg.cycle`
- expected:
  - missing nested keys fall back to defaults

#### K2 — invalid config value
- e.g. `cfg.cycle.min_bars_reset = -1`
- expected:
  - `ValueError` naming the key and invalid value

#### K3 — non-finite numeric persisted input
- `freshness_distance_state_early = float("nan")`
- expected:
  - `ValueError`

#### K4 — `null` remains `null`
- `reclaim_below_reset_floor_seen_since_cycle_end = None` with Z5 disabled
- expected:
  - `reclaim_reset_condition_met = None`
  - not coerced to `False`

#### K5 — not-evaluated vs failed
- `expansion_progress_structural = None`
- expected:
  - `expansion_reset_condition_met = None`
  - this is not silently treated as `False`

### Acceptance emphasis

Acceptance criteria for Ticket 9 must explicitly state that:
- T9 computes invalidation/cycle signals only and does not assign final state
- T9 does not write persistence
- T10 consumes the T9 bundle and performs the single authoritative state/cycle persistence write
- `cycle_reason_code` is always populated
- §9.3 diagnostic booleans are included in the output contract
- `resolved_setup_cycle_id` is never `None`
- first-seen initializes cycle id to `1` without creating a new-cycle event
- each Preflight-pflicht category is backed by at least one explicit concrete test case

> Jede Preflight-Pflichtkategorie ist durch mindestens einen explizit ausgeschriebenen Testfall oder einen ebenso expliziten, prüfbaren Nachweis abgesichert.

---

## Constraints / Invariants (must not change)

- [ ] Ticket 9 consumes only typed current-run bundles, typed persisted prior context, and `cfg`
- [ ] Ticket 9 does not consume `FeatureBundle`, OHLCV, raw timestamps, repositories, or storage handles in the pure computation function
- [ ] Ticket 9 does not recompute state-based freshness
- [ ] Ticket 9 does not assign final state
- [ ] Ticket 10 does not independently recompute `setup_cycle_id`
- [ ] structural invalidation suppresses timing invalidation
- [ ] `new_cycle_detected = true` implies `structural_invalidation = false`
- [ ] G3 is not implemented as a separate independent rule path
- [ ] Z3 is evaluated from current hard-floor admissibility, not from final phase label alone
- [ ] `resolved_setup_cycle_id` is never `None`
- [ ] first-seen initialization sets cycle id to `1` without creating a new-cycle event
- [ ] `cycle_reason_code` is always populated
- [ ] §9.3 diagnostic fields remain part of the T9 output contract
- [ ] no manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`
- [ ] one ticket = one PR

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
created_utc: "2026-04-21T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [8]
gesamtkonzept_ref: "§19 Ticket 9"
related_issues: []
follow_ups:
  - "Ticket 10: implement freshness + state machine using InvalidationCycleBundle and PersistedStateCycleContext"
  - "Ticket 15: daily runner consumes the persisted T9/T10 state/cycle contract"
  - "Ticket 17: intraday runner consumes the persisted T9/T10 state/cycle contract"
```
