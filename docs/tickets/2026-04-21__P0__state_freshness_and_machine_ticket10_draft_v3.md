> DRAFT (ticket): Not yet implemented. Canonical truth remains the authoritative source set until merged.

# Title
[P0] Implement state freshness, final state resolution, and single-write state persistence contract (Ticket 10)

## Context / Source

This ticket implements **Ticket 10** from the Independence-Release consolidated concept: the **freshness + state machine** layer.

**Gesamtkonzept reference:** Gesamtkonzept §19 Ticket 10.

`depends_on: [8, 9]` — requires:
- Ticket 8 (`phase interpreter`)
- Ticket 9 (`invalidation + cycle`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, existing repo-canonical docs, older ticket assumptions, or existing storage/config contracts conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements the **remaining Layer-4 closure** after Ticket 9.

It implements:

- `scanner/state/freshness.py`
- `scanner/state/machine.py`
- the required typed read/runtime/output models in `scanner/state/models.py`
- the canonical local derivation of `data_resolution_class` for state evaluation
- the single authoritative state/cycle persistence contract and write path for the Ticket-10 field set

It does **not** implement:

- Ticket-9 invalidation/cycle recomputation
- Tier-1 / Tier-2 / phase recomputation
- entry logic
- execution logic
- decision buckets / ranking
- output/report logic
- the unresolved “knappe Margins” confidence penalty
- a seventh state beyond the canonical six-state enum

### Layer-split clarification

Gesamtkonzept and the target repo structure explicitly split `scanner/state/` into:

- `invalidation.py`
- `cycle.py`
- `freshness.py`
- `machine.py`
- `models.py`

Under this implementation split:

- **Ticket 9** is authoritative for:
  - structural invalidation rules
  - timing invalidation rules as pre-state signals
  - setup-cycle reset / new-cycle detection
  - resolved `setup_cycle_id` for the current run

- **Ticket 10** is authoritative for:
  - state-based freshness recomputation
  - final state admission vs. non-admission
  - final state transition selection
  - state counters / entry-reference updates
  - the single authoritative persistence write for state/cycle fields

### Critical implementation split

Ticket 10 consumes the deterministic Ticket-9 contract and:

- does **not** independently recompute invalidation or cycle logic
- does **not** independently recompute `setup_cycle_id`
- takes `resolved_setup_cycle_id` from Ticket 9 as the sole cycle-id authority for the current run
- persists the final state/cycle update exactly once
- writes `cycle_end_bar_index` / `cycle_end_timestamp` only when the final state for this run newly transitions into `rejected` or `chased`

### Addendum / working-context checks

This ticket explicitly follows the addendum working-context leitplanken:

- **A.2 Schichtenarchitektur** — Ticket 10 remains strictly inside Layer 4 and does not leak into entry / execution / decision / output logic
- **A.3 `bar_clock.py` ist Fundamentmodul** — all `bars_since_*` counters and `cycle_end_timestamp` semantics rely on canonical closed-bar handling
- **A.5 Persistenz ist fachlicher Kern** — Ticket 10 is the first ticket that must establish the minimal persistent state/cycle continuity required by Abschnitt 4 and 6
- **A.6 Historie liefert Kontext, aber keinen Override** — prior persisted context informs state continuity and freshness, but does not override current-run phase/axis evaluation
- **Teil B Präzisierungs-Check** — the `Persisted Candidate Context / Watchlist-Kontinuität` block is operationalized here only for the concretely required state/cycle continuity fields, not broadened into an unspecific watchlist-history layer

---

## Goal

After this ticket is completed:

- `scanner/state/freshness.py` computes canonical state-based freshness
- `scanner/state/machine.py` computes canonical final state admission and final state selection
- `scanner/state/models.py` contains:
  - `StateRuntimeContext`
  - `PersistedStateMachineContext`
  - `StateEvaluationDisposition`
  - `StateFreshnessBundle`
  - `StateMachineBundle`
  - `StatePersistencePatch`
- Ticket 10 consumes only typed upstream bundles, typed persisted context, typed runtime context, and `cfg`
- the final state remains one of exactly:
  - `watch`
  - `early_ready`
  - `confirmed_ready`
  - `late`
  - `chased`
  - `rejected`
- `not_admitted / no_active_state` is implemented as a **disposition layer**, not as a seventh state
- all `bars_since_*` fields are updated in canonical **4h-bar units**
- state-entry reference prices and state-based freshness fields are updated deterministically
- the single authoritative state/cycle persistence patch is produced and written exactly once per admitted symbol
- `bars_since_cycle_end`, `cycle_end_bar_index`, `cycle_end_timestamp`, and the optional Z5 sticky reset flag are maintained consistently for future Ticket-9 consumption
- downstream Ticket 11 can consume a stable final state contract without re-deriving state/freshness behavior

---

## Scope

Allowed change surface:

- `scanner/state/freshness.py` (new)
- `scanner/state/machine.py` (new)
- `scanner/state/models.py` (extend)
- `scanner/state/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.state` defaults / merge / validation
- `scanner/storage/schema.py` — add the minimal state/cycle persistence table(s) required by Ticket 10
- `scanner/storage/repositories.py` (new) or equivalent minimal storage helper — implement the single authoritative read/write path for Ticket-10 state/cycle persistence
- `scanner/storage/sqlite.py` if minor additive bootstrap wiring is needed
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope

This ticket must not:

- recompute Ticket-9 invalidation/cycle signals
- recompute Tier-1 / Tier-2 / phase outputs
- consume OHLCV series directly inside the pure state-machine computation
- consume repositories/storage handles in the pure computation entrypoints
- implement entry-pattern logic
- implement execution logic
- implement decision buckets / ranking
- implement output/report generation
- introduce a seventh state for `not_admitted / no_active_state`
- operationalize the unresolved “knappe Margins” confidence penalty
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2 and §19 Ticket 10
- `v2_1_abschnitt_4_state_machine_rev3_aligned.md` — **the state-machine and state-freshness rules in this ticket operationalize Abschnitt 4; Codex must not reconstruct missing logic from free interpretation**
- `v2_1_abschnitt_6_daily_intraday_update_policy_rev3_aligned.md` — authoritative for 4h-bar counter units, state persistence minimum, scan-mode update policy, and no-backfill behavior
- Ticket 8 — typed `PhaseInterpretationBundle` contract
- Ticket 9 — typed `InvalidationCycleBundle` contract and the authoritative T9→T10 split

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

Repo process references:

- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed change (high-level)

### Before

- Ticket 8 provides the canonical phase-layer output.
- Ticket 9 provides the canonical pre-state invalidation/cycle output.
- The repo does not yet expose a typed final state-machine contract.
- The repo does not yet persist the minimal state/cycle field set required by Abschnitt 4 and 6.

### After

- `scanner/state/freshness.py` computes deterministic state-based freshness from persisted entry references plus current closed-bar runtime context
- `scanner/state/machine.py` is the authoritative orchestration entrypoint for Ticket 10: it computes disposition, final state selection, transition reason, and a typed persistence patch, and it invokes `compute_state_freshness(...)` internally exactly once per evaluation
- `scanner/storage/...` provides one authoritative read/write path for Ticket-10 state/cycle continuity
- Ticket 11 can consume final state outputs without reconstructing state logic ad hoc

### Edge cases

- `market_phase = none` without prior active-cycle evidence is **not** forced into `rejected`; it becomes `admitted = false`
- `watch -> confirmed_ready` direct transition remains allowed
- `late -> confirmed_ready`, `chased -> late`, `rejected -> early_ready`, and `rejected -> confirmed_ready` remain forbidden without a new cycle
- `close_at_early_entry_bar` and `close_at_confirmed_entry_bar` are **sticky within the cycle** once first set; they are not cleared merely because the current state leaves `early_ready` or `confirmed_ready`
- `bars_since_early_entered`, `bars_since_confirmed_entered`, `distance_from_ideal_entry_after_*`, and `freshness_distance_state_*` remain sticky within the cycle once initialized and continue to update until cycle reset
- `new_cycle_detected = true` resets the cycle-scoped state-entry/freshness fields and clears stale prior terminal-cycle end markers so that the next run cannot repeatedly re-open the same new cycle
- terminal state transitions set:
  - `cycle_end_bar_index = current_bar_index`
  - `cycle_end_timestamp = intraday_bar_id if intraday_bar_id is not None else daily_bar_id`
  - `bars_since_cycle_end = 0`
- on later runs in the same ended cycle, `bars_since_cycle_end` increments by `delta_closed_bars_relevant`
- `reclaim_below_reset_floor_seen_since_cycle_end` is a sticky cycle-reset helper flag:
  - once `True` after a cycle end, it remains `True` until new-cycle reset
  - reset to `None` on new cycle
- no backfill from missing persisted fields; missing history-dependent inputs remain `null` and make the dependent rule not satisfiable

### Backward compatibility impact

- Config surface grows under `cfg.state`
- a new typed in-memory final state-layer contract is introduced
- the SQLite schema grows with the minimal state/cycle persistence table(s)
- the repo gains its first business persistence path for final state/cycle continuity

---

## Module and model structure (authoritative)

### Modules

- `scanner/state/freshness.py`
- `scanner/state/machine.py`
- `scanner/state/models.py`

### Public pure-computation entrypoints

```python
def compute_state_freshness(
    invalidation_cycle_bundle: InvalidationCycleBundle,
    persisted_context: PersistedStateMachineContext,
    runtime_context: StateRuntimeContext,
    cfg: ScannerConfig,
) -> StateFreshnessBundle: ...
```

```python
def compute_state_machine(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    invalidation_cycle_bundle: InvalidationCycleBundle,
    persisted_context: PersistedStateMachineContext,
    runtime_context: StateRuntimeContext,
    cfg: ScannerConfig,
) -> StateMachineBundle: ...
```

### Orchestration rule

`compute_state_machine(...)` is the authoritative Ticket-10 orchestration entrypoint.

It must:
- call `compute_state_freshness(...)` internally exactly once per evaluation
- use the returned `StateFreshnessBundle` for all late/chased and persistence decisions that depend on state freshness
- expose that exact bundle again on the final `StateMachineBundle.freshness` field for downstream diagnostics

Callers must not re-implement state-freshness logic inside runners or storage code.

### Repository / persistence boundary

The repository/storage layer may expose an additive minimal API such as:

```python
def load_persisted_state_machine_context(symbol: str, connection: sqlite3.Connection) -> PersistedStateMachineContext: ...
```

```python
def apply_state_persistence_patch(
    patch: StatePersistencePatch,
    connection: sqlite3.Connection,
) -> None: ...
```

The repository path is the **only writer** for Ticket-10 state/cycle persistence. Pure computation functions remain storage-free.

---

## Input contract (authoritative)

### Accepted public input types

`compute_state_freshness(...)` accepts exactly:

- `InvalidationCycleBundle`
- `PersistedStateMachineContext`
- `StateRuntimeContext`
- `ScannerConfig`

`compute_state_machine(...)` accepts exactly:

- `PhaseInterpretationBundle`
- `Tier1AxisBundle`
- `Tier2AxisBundle`
- `InvalidationCycleBundle`
- `PersistedStateMachineContext`
- `StateRuntimeContext`
- `ScannerConfig`

Any other public input type is invalid and raises `TypeError`.

There is no dict-based loose input mode and no implicit coercion from mapping-like objects.

### Current-run bundle consistency

Current-run bundles must match exactly on:

- `symbol`
- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`

This applies across the current-run bundles consumed by `compute_state_machine(...)`:

- `PhaseInterpretationBundle`
- `Tier1AxisBundle`
- `Tier2AxisBundle`
- `InvalidationCycleBundle`

If inconsistent:
- raise `ValueError`
- the error message must name the inconsistent field

There is no silent reconciliation.

### Persisted-context consistency

`PersistedStateMachineContext` is prior-run context and is **not** subject to same-run equality checks for:

- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`

It must, however, belong to the same `symbol`.

If `persisted_context.symbol != phase_bundle.symbol`:
- raise `ValueError`
- the error message must name `symbol`

### `StateRuntimeContext`

Ticket 10 introduces a required runtime input:

```python
@dataclass(frozen=True)
class StateRuntimeContext:
    current_close: float
    current_bar_index: int
    delta_closed_bars_relevant: int
```

#### Validation rules

- `current_close`
  - allowed: finite `float`/`int` strictly `> 0`
  - rejected: `bool`, `None`, `NaN`, `inf`, `-inf`, `<= 0`

- `current_bar_index`
  - semantic unit: canonical closed-bar index in 4h-bar units supplied by the runner/persistence layer
  - allowed: non-negative `int`
  - rejected: `bool`, negative values, non-integer numerics

- `delta_closed_bars_relevant`
  - semantic unit: canonical closed 4h-bar count since the prior run
  - allowed: non-negative `int`
  - rejected: `bool`, negative values, non-integer numerics

#### Spec-term note

The field name **must** remain exactly `delta_closed_bars_relevant`. Do not rename it.

### `PersistedStateMachineContext`

Ticket 10 introduces an additive persisted read model for final state continuity:

```python
@dataclass(frozen=True)
class PersistedStateMachineContext:
    symbol: str

    current_setup_cycle_id: int | None
    previous_setup_cycle_id: int | None
    state_recorded_in_cycle_id: int | None

    prev_state_machine_state: str | None

    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None

    bars_since_state_entered: int | None
    bars_since_early_entered: int | None
    bars_since_confirmed_entered: int | None
    bars_since_cycle_end: int | None

    reclaim_below_reset_floor_seen_since_cycle_end: bool | None

    close_at_early_entry_bar: float | None
    close_at_confirmed_entry_bar: float | None

    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None

    cycle_end_bar_index: int | None
    cycle_end_timestamp: int | None
```

#### Validation rules

- `symbol`
  - must be non-empty `str`

- `current_setup_cycle_id`, `previous_setup_cycle_id`, `state_recorded_in_cycle_id`
  - allowed: positive `int` or `None`
  - rejected: `0`, negative integers, `bool`, non-integer numerics, strings, `NaN`, `inf`

- `prev_state_machine_state`
  - allowed closed set:
    - `"watch"`
    - `"early_ready"`
    - `"confirmed_ready"`
    - `"late"`
    - `"chased"`
    - `"rejected"`
    - or `None`
  - any other value → `ValueError`

- `freshness_distance_state_early`, `freshness_distance_state_confirmed`
  - allowed: finite float/int in `0..100` or `None`
  - rejected: `bool`, `NaN`, `inf`, `-inf`, values outside `0..100`

- `distance_from_ideal_entry_after_early`, `distance_from_ideal_entry_after_confirmed`
  - allowed: any finite float/int or `None`
  - rejected: `bool`, `NaN`, `inf`, `-inf`
  - note: these fields may be negative because current price can be below the recorded entry reference

- `bars_since_state_entered`, `bars_since_early_entered`, `bars_since_confirmed_entered`, `bars_since_cycle_end`
  - unit = canonical 4h bars
  - allowed: non-negative `int` or `None`
  - rejected: `bool`, negative values, non-integer numerics

- `close_at_early_entry_bar`, `close_at_confirmed_entry_bar`
  - allowed: finite float/int strictly `> 0` or `None`
  - rejected: `bool`, `NaN`, `inf`, `-inf`, `<= 0`

- `cycle_end_bar_index`
  - allowed: non-negative `int` or `None`
  - rejected: `bool`, negative values, non-integer numerics

- `cycle_end_timestamp`
  - semantic unit: UTC epoch milliseconds of the canonical closed 4h bar at which the cycle ended
  - allowed: non-negative `int` or `None`
  - rejected: `bool`, negative values, non-integer numerics

- `reclaim_below_reset_floor_seen_since_cycle_end`
  - allowed: `True`, `False`, or `None`
  - `None` means the symbol is not currently in a carried post-cycle-end reset-tracking interval

#### Meaning of `None`

- `None` means "not available / not yet initialized / not applicable in current cycle context"
- `None` must not be coerced via `bool(...)`
- missing history-dependent fields make only the dependent rule non-satisfiable; they do not silently become `0` or `False`

### Input-contract standard

> Erlaubte Input-Typen, Units, Koerzionsregeln und harte Rejection-Regeln sind vollständig spezifiziert. Mehrdeutige Inputs dürfen nicht stillschweigend umgedeutet werden.

---

## Local derivation of `data_resolution_class` (authoritative)

Ticket 10 must **not** open the Ticket-8 public interface to import a separate upstream `data_resolution_class`.

Instead, Ticket 10 derives `data_resolution_class` locally as exactly one of:

- `"full_1d_4h"`
- `"reduced_1d_4h"`
- `"daily_only"`

### Derivation rule

For the **resolved state evaluation of the current run**:

- `"daily_only"` iff `data_4h_available = False`
- `"full_1d_4h"` iff:
  - `data_4h_available = True`
  - and every state-relevant input used by the winning/held state evaluation that exposes a `_reduced_resolution` flag has that flag `False`
- `"reduced_1d_4h"` iff:
  - `data_4h_available = True`
  - and at least one state-relevant input used by the winning/held state evaluation that exposes a `_reduced_resolution` flag has that flag `True`

### State-relevant reduced-resolution inputs

The derivation must consider only the inputs actually used by the resolved state path and which expose `_reduced_resolution` flags, specifically:

- `freshness_distance_structural`
- Tier-1 axes consumed by the resolved state conditions
- Tier-2 axes consumed by the resolved state conditions

Do **not** use unrelated axes that did not participate in the resolved state path.

This rule is deterministic and must be fully implemented in Ticket 10; Codex must not invent alternative derivations.

---

## Output contract (authoritative)

### `StateEvaluationDisposition`

```python
@dataclass(frozen=True)
class StateEvaluationDisposition:
    admitted: bool
    disposition_reason: str | None
```

#### Closed enums

`disposition_reason` is exactly one of:

- `"PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE"`
- or `None`

#### Semantics

- `admitted = False` means:
  - the symbol is **not** admitted into the active state machine for this run
  - no regular state is assigned
  - no state/cycle persistence write is emitted
  - this is **not** equivalent to `rejected`

- `admitted = True` means:
  - the symbol is processed by the active state machine
  - `disposition_reason = None`

### `StateFreshnessBundle`

```python
@dataclass(frozen=True)
class StateFreshnessBundle:
    close_at_early_entry_bar: float | None
    close_at_confirmed_entry_bar: float | None

    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None

    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None
```

`StateFreshnessBundle` is a pure derived-value bundle. It does not independently carry current-run identity metadata because `compute_state_machine(...)` is the authoritative orchestration entrypoint and must call `compute_state_freshness(...)` internally from the already validated current-run bundle set.

### `StatePersistencePatch`

```python
@dataclass(frozen=True)
class StatePersistencePatch:
    symbol: str

    setup_cycle_id: int
    previous_setup_cycle_id: int | None
    state_recorded_in_cycle_id: int

    state_machine_state: str
    state_confidence: float
    state_transition_reason: str

    bars_since_state_entered: int
    bars_since_early_entered: int | None
    bars_since_confirmed_entered: int | None
    bars_since_cycle_end: int | None

    close_at_early_entry_bar: float | None
    close_at_confirmed_entry_bar: float | None

    distance_from_ideal_entry_after_early: float | None
    distance_from_ideal_entry_after_confirmed: float | None

    freshness_distance_state_early: float | None
    freshness_distance_state_confirmed: float | None

    cycle_end_bar_index: int | None
    cycle_end_timestamp: int | None

    reclaim_below_reset_floor_seen_since_cycle_end: bool | None
```

### `StateMachineBundle`

```python
@dataclass(frozen=True)
class StateMachineBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    data_resolution_class: str

    disposition: StateEvaluationDisposition

    state_machine_state: str | None
    state_confidence: float | None
    state_transition_reason: str | None

    setup_cycle_id: int | None

    qualifies_early_ready: bool
    qualifies_confirmed_ready: bool
    qualifies_late: bool
    qualifies_chased: bool

    loses_early_but_phase_intact: bool
    loses_confirmed_but_phase_intact: bool

    freshness: StateFreshnessBundle | None
    persistence_patch: StatePersistencePatch | None
```

### Important semantics

- `state_machine_state` is exactly one of the canonical six-state enum or `None`
- `state_machine_state = None` iff `disposition.admitted = False`
- `state_confidence` is `None` iff `disposition.admitted = False`
- `state_transition_reason` is `None` iff `disposition.admitted = False`
- `setup_cycle_id` is `None` iff `disposition.admitted = False`
- `persistence_patch` is `None` iff `disposition.admitted = False`
- there is **no** synthetic `rejected` fallback for `disposition.admitted = False`

### `state_transition_reason` closed set

`state_transition_reason` is exactly one of:

- `"NEW_CYCLE_RESET_TO_WATCH"`
- `"WATCH_ACTIVE_DEFAULT"`
- `"WATCH_FROM_EARLY_LOST"`

- `"EARLY_READY_ENTERED"`
- `"EARLY_READY_HELD"`

- `"CONFIRMED_READY_ENTERED"`
- `"CONFIRMED_READY_HELD"`

- `"LATE_FROM_EARLY_FRESHNESS"`
- `"LATE_FROM_CONFIRMED_FRESHNESS"`
- `"LATE_FROM_CONFIRMED_LOST"`
- `"LATE_HELD"`

- `"CHASED_FROM_EXPANSION"`
- `"CHASED_FROM_EARLY_FRESHNESS"`
- `"CHASED_FROM_CONFIRMED_FRESHNESS"`
- `"CHASED_HELD"`

- `"REJECTED_FROM_STRUCTURAL_INVALIDATION"`
- `"REJECTED_HELD"`

These codes are closed, machine-readable, and stable. No free-text reasons are allowed.

---

## State-freshness logic (authoritative)

Ticket 10 is authoritative for state-based freshness recomputation.

### Entry reference semantics

- `close_at_early_entry_bar`
  - set exactly once when the symbol first enters `early_ready` in the current cycle
  - remains sticky within the cycle
  - resets to `None` on new cycle

- `close_at_confirmed_entry_bar`
  - set exactly once when the symbol first enters `confirmed_ready` in the current cycle
  - remains sticky within the cycle
  - resets to `None` on new cycle

### Direct `watch -> confirmed_ready`

If the symbol transitions directly from `watch` to `confirmed_ready`:

- `close_at_confirmed_entry_bar = runtime_context.current_close`
- `close_at_early_entry_bar` remains whatever it already was in the cycle
- if the symbol has never been `early_ready` in the current cycle:
  - `close_at_early_entry_bar = None`
  - `distance_from_ideal_entry_after_early = None`
  - `freshness_distance_state_early = None`
  - `bars_since_early_entered = None`

Ticket 10 must not synthesize an implicit early-entry reference for an unobserved `early_ready` state.

### Distance fields

If `close_at_early_entry_bar` is not `None`:

- `distance_from_ideal_entry_after_early = ((current_close / close_at_early_entry_bar) - 1) * 100`

Else:
- `distance_from_ideal_entry_after_early = None`

If `close_at_confirmed_entry_bar` is not `None`:

- `distance_from_ideal_entry_after_confirmed = ((current_close / close_at_confirmed_entry_bar) - 1) * 100`

Else:
- `distance_from_ideal_entry_after_confirmed = None`

### Freshness distance fields

If `bars_since_early_entered` or `distance_from_ideal_entry_after_early` is `None`:
- `freshness_distance_state_early = None`

Else:
- normalize `bars_since_early_entered` using the configured bar-points
- normalize `distance_from_ideal_entry_after_early` using the configured distance-points
- aggregate:
  - `0.50` bars component
  - `0.50` distance component

If `bars_since_confirmed_entered` or `distance_from_ideal_entry_after_confirmed` is `None`:
- `freshness_distance_state_confirmed = None`

Else:
- same normalization/aggregation logic using the confirmed fields

### Sticky-within-cycle rule

Once `bars_since_early_entered`, `bars_since_confirmed_entered`, `close_at_*_entry_bar`, `distance_from_ideal_entry_after_*`, or `freshness_distance_state_*` are initialized in a cycle:

- they remain part of the carried current-cycle context
- they continue updating across later states in the same cycle
- they reset only on:
  - new cycle
  - bootstrap/no-prior-cycle initialization where not yet entered

### No-backfill rule

If the persisted context lacks a required entry reference or counter field:

- do not reconstruct it from future information
- the dependent freshness field stays `None`

This follows Abschnitt 6 no-backfill semantics.

---

## State machine logic (authoritative)

### Hard invariants

The canonical six-state enum remains exactly:

- `watch`
- `early_ready`
- `confirmed_ready`
- `late`
- `chased`
- `rejected`

Forbidden return paths remain forbidden:

- `late -> confirmed_ready`
- `chased -> late`
- `chased -> confirmed_ready`
- `chased -> early_ready`
- `rejected -> early_ready`
- `rejected -> confirmed_ready`

A symbol currently in `chased` or `rejected` can re-enter an active non-terminal state only when Ticket 9 has already resolved a **new cycle**.

### Evaluation order

Ticket 10 must evaluate in exactly this order:

1. disposition gate (`admitted` vs `not admitted`)
2. new cycle?
3. structural invalidation?
4. chased?
5. late?
6. confirmed?
7. early?
8. watch / no-change

There is no alternative ordering and no tie-break freedom.

### Disposition gate

`admitted = False` iff:

- `market_phase = "none"`
- and there is no prior active-cycle evidence in the carried current-cycle context

This operationalizes Abschnitt 4 `phase_none_without_prior_active_cycle`.

When `admitted = False`:

- `state_machine_state = None`
- `state_confidence = None`
- `state_transition_reason = None`
- `setup_cycle_id = None`
- `persistence_patch = None`
- `disposition_reason = "PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE"`

This is **not** `rejected`.

### `qualifies_early_ready`

True iff all general and phase-specific early conditions hold:

General:
- `market_phase != "none"`
- `data_4h_available = True`
- `structural_invalidation = False`
- `freshness_distance_structural <= cfg.state.early.max_structural_freshness`

Phase-specific:
- `pressure_build`
  - `compression_strength >= cfg.state.early.pressure_build.min_compression`
  - `volume_regime_shift >= cfg.state.early.pressure_build.min_volume_shift`
  - `expansion_progress_structural <= cfg.state.early.pressure_build.max_expansion`
- `trend_resume`
  - `trend_strength >= cfg.state.early.trend_resume.min_trend`
  - `reclaim_progress >= cfg.state.early.trend_resume.min_reclaim`
  - `reacceleration_strength_simplified >= cfg.state.early.trend_resume.min_reaccel`
- `transition_reclaim`
  - `reclaim_progress >= cfg.state.early.transition_reclaim.min_reclaim`
  - `volume_regime_shift >= cfg.state.early.transition_reclaim.min_volume_shift`

### `qualifies_confirmed_ready`

True iff all general and phase-specific confirmed conditions hold:

General:
- `market_phase != "none"`
- `structural_invalidation = False`
- `freshness_distance_structural <= cfg.state.confirmed.max_structural_freshness`

Phase-specific:
- `pressure_build`
  - `data_4h_available = True`
  - `reclaim_progress >= cfg.state.confirmed.pressure_build.min_reclaim`
  - `compression_strength >= cfg.state.confirmed.pressure_build.min_compression`
  - `volume_regime_shift >= cfg.state.confirmed.pressure_build.min_volume_shift`
  - `expansion_progress_structural <= cfg.state.confirmed.pressure_build.max_expansion`
- `trend_resume`
  - `reclaim_progress >= cfg.state.confirmed.trend_resume.min_reclaim`
  - `trend_strength >= cfg.state.confirmed.trend_resume.min_trend`
  - `reacceleration_strength_simplified >= cfg.state.confirmed.trend_resume.min_reaccel`
- `transition_reclaim`
  - `reclaim_progress >= cfg.state.confirmed.transition_reclaim.min_reclaim`
  - `trend_strength >= cfg.state.confirmed.transition_reclaim.min_trend_after_reclaim`

### Daily-only confirmed rule

If `data_4h_available = False`, then `confirmed_ready` is allowed **only** when:

- phase is `trend_resume` or `transition_reclaim`
- `market_phase_confidence >= cfg.state.confirmed.daily_only_min_phase_confidence`

For `pressure_build`, `confirmed_ready` remains forbidden without 4h.

### `qualifies_late`

True iff:

- `structural_invalidation = False`
- and at least one holds:
  - `freshness_distance_state_early >= cfg.state.late.min_state_freshness`
  - `freshness_distance_state_confirmed >= cfg.state.late.min_state_freshness`
  - current state is `confirmed_ready` and `qualifies_confirmed_ready = False` and phase remains intact

Priority for late reason selection:
1. confirmed freshness
2. early freshness
3. loses confirmed but phase intact

### `qualifies_chased`

True iff:

- `structural_invalidation = False`
- and at least one holds:
  - `freshness_distance_state_early >= cfg.state.chased.min_state_freshness`
  - `freshness_distance_state_confirmed >= cfg.state.chased.min_state_freshness`
  - `expansion_progress_structural >= cfg.state.chased.min_expansion_progress`

Priority for chased reason selection:
1. expansion progress
2. confirmed freshness
3. early freshness

### `loses_early_but_phase_intact`

True iff:

- current state = `early_ready`
- `qualifies_early_ready = False`
- `market_phase != "none"`
- `structural_invalidation = False`

### `loses_confirmed_but_phase_intact`

True iff:

- current state = `confirmed_ready`
- `qualifies_confirmed_ready = False`
- `market_phase != "none"`
- `structural_invalidation = False`

### Final transition matrix

Ticket 10 must operationalize the canonical matrix from Abschnitt 4:

#### From `watch`

- `[watch, new_cycle_detected] -> watch`
- `[watch, structural_invalidation] -> rejected`
- `[watch, disposition.admitted = false] -> no active state / no write`
- `[watch, qualifies_confirmed_ready] -> confirmed_ready`
- `[watch, qualifies_early_ready] -> early_ready`
- `[watch, otherwise] -> watch`

#### From `early_ready`

- `[early_ready, new_cycle_detected] -> watch`
- `[early_ready, structural_invalidation] -> rejected`
- `[early_ready, qualifies_chased] -> chased`
- `[early_ready, qualifies_late] -> late`
- `[early_ready, qualifies_confirmed_ready] -> confirmed_ready`
- `[early_ready, loses_early_but_phase_intact] -> watch`
- `[early_ready, otherwise] -> early_ready`

#### From `confirmed_ready`

- `[confirmed_ready, new_cycle_detected] -> watch`
- `[confirmed_ready, structural_invalidation] -> rejected`
- `[confirmed_ready, qualifies_chased] -> chased`
- `[confirmed_ready, qualifies_late] -> late`
- `[confirmed_ready, loses_confirmed_but_phase_intact] -> late`
- `[confirmed_ready, otherwise] -> confirmed_ready`

#### From `late`

- `[late, new_cycle_detected] -> watch`
- `[late, structural_invalidation] -> rejected`
- `[late, qualifies_chased] -> chased`
- `[late, otherwise] -> late`

#### From `chased`

- `[chased, new_cycle_detected] -> watch`
- `[chased, otherwise] -> chased`

#### From `rejected`

- `[rejected, new_cycle_detected] -> watch`
- `[rejected, otherwise] -> rejected`

---

## Persistence split with Ticket 9 (authoritative)

Ticket 9 is **not** the persistence writer for final state/cycle fields.

Ticket 10 is the single authoritative writer for:

- `state_machine_state`
- `state_confidence`
- `state_transition_reason`
- `setup_cycle_id`
- `previous_setup_cycle_id`
- `state_recorded_in_cycle_id`
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `bars_since_cycle_end`
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`
- `cycle_end_bar_index`
- `cycle_end_timestamp`
- `reclaim_below_reset_floor_seen_since_cycle_end`

### Terminal transition write rules

If the final state newly transitions into `rejected` or `chased` in the current run:

- `cycle_end_bar_index = runtime_context.current_bar_index`
- `cycle_end_timestamp = intraday_bar_id if intraday_bar_id is not None else daily_bar_id`
- `bars_since_cycle_end = 0`

This fallback is required because terminal transitions may occur in daily runs where `intraday_bar_id` is legitimately `None`. Ticket 10 must not reject such regular daily transitions.

### Terminal hold rules

If the symbol remains in `rejected` or `chased` without a new cycle:

- `cycle_end_bar_index` remains unchanged
- `cycle_end_timestamp` remains unchanged
- `bars_since_cycle_end += delta_closed_bars_relevant`

### New-cycle reset rules

If Ticket 9 resolved `new_cycle_detected = True`, Ticket 10 must write:

- `setup_cycle_id = invalidation_cycle_bundle.resolved_setup_cycle_id`
- `previous_setup_cycle_id = persisted_context.current_setup_cycle_id`
- `state_recorded_in_cycle_id = setup_cycle_id`
- `state_machine_state = "watch"`
- `bars_since_state_entered = 0`

And reset these cycle-scoped fields to `None`:

- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`
- `cycle_end_bar_index`
- `cycle_end_timestamp`
- `bars_since_cycle_end`
- `reclaim_below_reset_floor_seen_since_cycle_end`

This reset is required to prevent stale prior terminal-cycle markers from causing repeated new-cycle resolution on subsequent runs.

### `state_recorded_in_cycle_id` update rule

For every admitted Ticket-10 persistence write:

- `state_recorded_in_cycle_id = setup_cycle_id`

This applies:
- on new-cycle reset writes
- on intra-cycle state changes such as `watch -> early_ready` or `confirmed_ready -> late`
- on no-change admitted writes

Ticket 10 must not carry forward a stale or older-cycle `state_recorded_in_cycle_id` on an admitted write. The persisted field always reflects the cycle id under which the currently persisted state record is written.

### Sticky Z5 helper flag

`reclaim_below_reset_floor_seen_since_cycle_end` must be maintained as:

- `None` when there is no carried post-cycle-end reset interval
- `True` once it has become true after cycle end and before new cycle reset
- `False` when in a post-cycle-end interval and not yet seen below the reset floor

Update rule:
- if `bars_since_cycle_end is not None`
- and `cfg.cycle.enable_reclaim_reset = True`
- and current `reclaim_progress < cfg.cycle.reclaim_reset_floor`
- then set the field to `True`
- once `True`, do not revert to `False` until new-cycle reset

### No double-writer rule

There must be exactly one authoritative persistence writer for the full field set above.

That writer belongs to Ticket 10.

---

## Config contract

All new config keys live under `cfg.state`.

### Merge semantics

> Partielle Overrides in `cfg.state` werden feldweise mit zentralen Defaults gemergt; fehlende Unterkeys gelten nicht als invalid. Ungültige Werte (falscher Typ, nicht-finit, außerhalb des erlaubten Bereichs) erzeugen einen klaren `ValueError`, der den Key und den ungültigen Wert nennt.

### Numeric robustness

> Nicht-finite numerische Werte (`NaN`, `inf`, `-inf`) gelten als ungültige bzw. nicht auswertbare Inputs und dürfen nicht in numerisch aussehende Outputs durchgereicht werden.

### Nullability

> Semantisch nullable Eingaben und Diagnostikfelder dürfen nicht implizit via `bool(...)` zu `false` kollabieren. `None` bleibt semantisch von `False` getrennt.

### Determinism

> Bei identischem Input und identischer Config sind Auswahl, Reihenfolge, Status und Gründe identisch.

### Confidence-penalty scope

Ticket 10 implements exactly these confidence penalties:

- `market_phase_blended = true` → `cfg.state.confidence.blended_penalty`
- `data_resolution_class != "full_1d_4h"` → `cfg.state.confidence.not_full_resolution_penalty`

Ticket 10 does **not** implement the unresolved “knappe Margins” penalty.

### Defaults

```yaml
state:
  confidence:
    blended_penalty: 5
    not_full_resolution_penalty: 10

  freshness:
    bars_points:
      - [0, 0]
      - [1, 20]
      - [2, 40]
      - [4, 70]
      - [6, 100]
    distance_points:
      - [0, 0]
      - [1, 25]
      - [2, 50]
      - [3, 75]
      - [5, 100]

  early:
    max_structural_freshness: 65
    pressure_build:
      min_compression: 65
      min_volume_shift: 55
      max_expansion: 45
    trend_resume:
      min_trend: 55
      min_reclaim: 40
      min_reaccel: 50
    transition_reclaim:
      min_reclaim: 45
      min_volume_shift: 45

  confirmed:
    max_structural_freshness: 55
    daily_only_min_phase_confidence: 70
    pressure_build:
      min_reclaim: 55
      min_compression: 60
      min_volume_shift: 55
      max_expansion: 50
    trend_resume:
      min_reclaim: 50
      min_trend: 60
      min_reaccel: 55
    transition_reclaim:
      min_reclaim: 55
      min_trend_after_reclaim: 50

  late:
    min_state_freshness: 60

  chased:
    min_state_freshness: 85
    min_expansion_progress: 80
```

### Validation rules

- all penalties and thresholds
  - finite number in `0..100`
- `daily_only_min_phase_confidence`
  - finite number in `0..100`
- `bars_points`, `distance_points`
  - point lists with strictly ascending `x`
  - `y` values in `0..100`

Missing keys fall back to defaults. Invalid values raise `ValueError` naming the key and invalid value.

---

## Minimal state/cycle persistence schema (authoritative)

Ticket 10 must introduce the minimal persistent table(s) necessary to support Abschnitt 4 and 6 continuity.

### Required persisted fields

At minimum, the schema must persist per symbol:

- `symbol`
- `setup_cycle_id`
- `previous_setup_cycle_id`
- `state_recorded_in_cycle_id`

- `state_machine_state`
- `state_confidence`
- `state_transition_reason`

- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `bars_since_cycle_end`

- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`

- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`

- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`

- `cycle_end_bar_index`
- `cycle_end_timestamp`

- `reclaim_below_reset_floor_seen_since_cycle_end`

The exact table split may be one table or a minimal tightly-coupled state/cycle table set, but the write path must remain logically single-writer and per-symbol deterministic.

### Table-split constraint

Do **not** create competing partial-write tables where state and cycle fields can diverge. If multiple tables are used, the write must remain atomic and single-authority.

---

## Canonical docs to update

- `docs/canonical/ARCHITECTURE.md` — add `scanner/state/freshness.py`, `scanner/state/machine.py`, and the Ticket-10 persistence-writer role
- `docs/canonical/DATA_MODEL.md` — add the Ticket-10 runtime, persisted, output, and patch models
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` — document `delta_closed_bars_relevant`, sticky-within-cycle behavior, state persistence minimum, and the not-admitted disposition path
- `docs/canonical/GLOSSARY.md` — add `data_resolution_class`, disposition semantics, state transition reasons, and the Ticket-10 field meanings
- `docs/canonical/VERIFICATION_FOR_AI.md` — add the Ticket-10 rules, defaults, persistence semantics, and explicit exclusion of the unresolved “knappe Margins” penalty

---

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Authority precedence:** If existing code, config defaults, or older docs differ from Abschnitt 4 / Abschnitt 6 / Ticket 9 / Gesamtkonzept, the authoritative source set wins.
- **Docs in same PR:** Update all listed canonical docs in the same PR as the code changes.
- **Strict layer boundary:** Ticket 10 must not implement entry / execution / decision / output logic.
- **No T9 recomputation:** Ticket 10 consumes the Ticket-9 bundle and must not independently recompute invalidation or cycle logic.
- **No seventh state:** `not_admitted / no_active_state` must be modeled only as `StateEvaluationDisposition`.
- **No synthetic rejection:** `admitted = false` must not collapse to `rejected`.
- **No setup-cycle recomputation:** `setup_cycle_id` comes from Ticket 9.
- **Single writer:** Ticket 10 is the only writer for final state/cycle persistence.
- **Sticky-within-cycle behavior:** entry refs and state freshness fields remain sticky until new cycle reset.
- **Clear cycle-end fields on new cycle:** new-cycle activation must clear stale prior terminal-cycle markers.
- **Use exact spec term `delta_closed_bars_relevant`.**
- **No bool()-coercion of nullable values.**
- **No silent current-run bundle reconciliation.**
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**
- **One ticket = one PR.**

---

## Acceptance Criteria (deterministic)

1. `scanner/state/freshness.py` and `scanner/state/machine.py` exist.
2. `scanner/state/models.py` contains the Ticket-10 typed models defined in this ticket.
3. `compute_state_freshness(...)` and `compute_state_machine(...)` exist with exactly the typed public input contracts defined here.
4. `compute_state_machine(...)` is the authoritative Ticket-10 orchestration entrypoint and calls `compute_state_freshness(...)` internally exactly once per evaluation.
5. Pure computation functions do not consume repositories or storage handles.
6. Public input type mismatches raise `TypeError`.
7. Current-run bundle metadata mismatches raise `ValueError` naming the mismatched field.
8. Persisted-context symbol mismatch raises `ValueError`.
9. Invalid `StateRuntimeContext` values raise `ValueError`.
10. Invalid persisted context values raise `ValueError`.
11. `data_resolution_class` is derived locally exactly as specified here.
12. `not_admitted / no_active_state` is implemented only as `StateEvaluationDisposition`.
13. `admitted = false` produces:
    - `state_machine_state = None`
    - `persistence_patch = None`
    - no synthetic `rejected`
14. The canonical six-state enum remains unchanged.
15. `watch -> confirmed_ready` direct transition is supported exactly as specified.
16. Forbidden return paths remain forbidden exactly as specified.
17. `close_at_early_entry_bar`, `close_at_confirmed_entry_bar`, `distance_from_ideal_entry_after_*`, and `freshness_distance_state_*` are computed exactly as specified.
18. Entry reference and state-freshness fields are sticky within the cycle and reset only on new cycle.
19. `bars_since_state_entered`, `bars_since_early_entered`, `bars_since_confirmed_entered`, and `bars_since_cycle_end` are maintained in canonical 4h-bar units using `delta_closed_bars_relevant`.
20. `bars_since_cycle_end` is explicitly updated by Ticket 10, not left stale after Ticket 9 consumption.
21. `cycle_end_bar_index`, `cycle_end_timestamp`, and `bars_since_cycle_end = 0` are written exactly on newly terminal transitions into `rejected` or `chased`.
22. On terminal holds, `bars_since_cycle_end` increments and `cycle_end_*` remain unchanged.
23. On new cycle, cycle-scoped state-entry/freshness fields and prior cycle-end markers are reset exactly as specified.
24. `reclaim_below_reset_floor_seen_since_cycle_end` is maintained as a sticky optional Z5 helper flag exactly as specified.
25. `state_confidence` starts from `market_phase_confidence` and applies only the explicitly allowed penalties from this ticket.
26. Ticket 10 does **not** implement the unresolved “knappe Margins” penalty.
27. `state_transition_reason` comes from the exact closed enum defined in this ticket.
28. The SQLite schema is extended with the minimal state/cycle persistence field set required by this ticket.
29. The state/cycle write path is atomic and single-authority.
30. Canonical docs listed in this ticket are updated in the same PR.
31. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
32. The ticket is archived in the same PR according to workflow.

---

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ covered — all `cfg.state` keys have explicit defaults
- **Config Invalid Value Handling:** ✅ covered — invalid type / non-finite / out-of-range values raise `ValueError`
- **Nullability / kein bool()-Coercion:** ✅ covered — nullable runtime/persisted/output fields remain semantically distinct from `False`
- **Not-evaluated vs failed getrennt:** ✅ covered — `not admitted`, `rejected`, and state-negative evaluations remain distinct
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ covered — pure compute is storage-free and the final persistence path is single-writer / atomic
- **Deterministische Reihenfolge / Priority:** ✅ covered — evaluation order and reason priorities are explicit
- **Input contract explicit:** ✅ covered — accepted types, units, and rejection rules are explicit
- **No synthetic history reconstruction:** ✅ covered — missing persisted state does not backfill entry refs or state freshness
- **Current-run / prior-run split explicit:** ✅ covered — same-run bundle identity checks do not apply to prior-run context
- **No seventh state:** ✅ covered — `not admitted` is a disposition only

---

## Tests (required if logic changes)

### Category A — Public input contract / runtime context / validation

#### A1 — valid typed inputs
- valid current-run bundles
- valid `PersistedStateMachineContext`
- valid `StateRuntimeContext`
- expected: computation succeeds

#### A2 — wrong public input type
- pass dict or wrong object into a public function
- expected: `TypeError`

#### A3 — current-run bundle mismatch
- mismatch in:
  - `symbol`
  - `daily_bar_id`
  - `intraday_bar_id`
  - `data_4h_available`
- expected: `ValueError` naming the field

#### A4 — persisted symbol mismatch
- expected: `ValueError`

#### A5 — invalid runtime context bool trap
- `current_bar_index = True`
- expected: `ValueError`

#### A6 — terminal transition in daily-only run (`intraday_bar_id = None`)
- terminal transition into `rejected` or `chased`
- `intraday_bar_id = None`
- expected:
  - no `ValueError`
  - `cycle_end_timestamp = daily_bar_id`
  - `cycle_end_bar_index = current_bar_index`
  - `bars_since_cycle_end = 0`

---

### Category B — Disposition / no-active-state path

#### B1 — `phase_none_without_prior_active_cycle`
- `market_phase = none`
- no prior active-cycle evidence
- expected:
  - `admitted = false`
  - `disposition_reason = "PHASE_NONE_WITHOUT_PRIOR_ACTIVE_CYCLE"`
  - `state_machine_state = None`
  - `persistence_patch = None`

#### B2 — `market_phase = none` after prior active-cycle evidence
- expected:
  - disposition admits evaluation
  - final path depends on T9 structural invalidation / rejection handling
  - no collapse into `not admitted`

---

### Category C — State freshness / sticky-within-cycle behavior

#### C1 — first early entry initializes early reference
- prior early fields `None`
- final state enters `early_ready`
- expected:
  - `close_at_early_entry_bar = current_close`
  - `bars_since_early_entered = 0`

#### C2 — first confirmed entry initializes confirmed reference
- prior confirmed fields `None`
- final state enters `confirmed_ready`
- expected:
  - `close_at_confirmed_entry_bar = current_close`
  - `bars_since_confirmed_entered = 0`

#### C3 — direct `watch -> confirmed_ready`
- expected:
  - confirmed fields initialize
  - early fields stay `None` if never observed

#### C4 — sticky early fields survive leaving `early_ready`
- prior cycle has early fields initialized
- current run transitions `early_ready -> watch`
- expected:
  - `close_at_early_entry_bar` retained
  - `bars_since_early_entered` increments
  - `freshness_distance_state_early` recomputed, not nulled

#### C5 — sticky confirmed fields survive leaving `confirmed_ready`
- analogous expected behavior

#### C6 — no-backfill on missing entry refs
- missing `close_at_early_entry_bar`
- expected:
  - dependent early distance/freshness fields remain `None`

---

### Category D — Final transition order and forbidden paths

#### D1 — structural invalidation beats chased/late
- fixture hits structural invalidation and chased
- expected:
  - final state = `rejected`

#### D2 — chased beats late
- fixture hits both late and chased triggers
- expected:
  - final state = `chased`

#### D3 — confirmed beats early
- both qualifies true
- expected:
  - final state = `confirmed_ready`

#### D4 — `late -> confirmed_ready` forbidden
- current state late, confirmed qualifies
- expected:
  - no return to confirmed

#### D5 — `chased -> early_ready` forbidden without new cycle
- expected:
  - remains `chased`

#### D6 — `rejected -> confirmed_ready` forbidden without new cycle
- expected:
  - remains `rejected`

---

### Category E — State-specific qualifying logic

#### E1 — `early_ready` pressure_build
- expected exact threshold behavior

#### E2 — `early_ready` trend_resume
- expected exact threshold behavior

#### E3 — `early_ready` transition_reclaim
- expected exact threshold behavior

#### E4 — `confirmed_ready` pressure_build with 4h
- expected exact threshold behavior

#### E5 — `confirmed_ready` daily_only allowed path
- `data_4h_available = false`
- phase in `{trend_resume, transition_reclaim}`
- confidence above threshold
- expected: confirmed allowed

#### E6 — `confirmed_ready` daily_only forbidden for pressure_build
- expected: not confirmed

---

### Category F — Late / chased reason priority

#### F1 — chased by expansion wins over freshness
- expected reason = `"CHASED_FROM_EXPANSION"`

#### F2 — chased confirmed freshness beats early freshness
- expected reason = `"CHASED_FROM_CONFIRMED_FRESHNESS"`

#### F3 — late confirmed freshness beats early freshness
- expected reason = `"LATE_FROM_CONFIRMED_FRESHNESS"`

#### F4 — loses_confirmed_but_phase_intact maps to late
- expected reason = `"LATE_FROM_CONFIRMED_LOST"`

---

### Category G — Counter progression in canonical 4h units

#### G1 — no-change hold increments `bars_since_state_entered`
- expected increment by `delta_closed_bars_relevant`

#### G2 — early counter increments even after leaving early
- expected sticky increment behavior

#### G3 — confirmed counter increments even after leaving confirmed
- expected sticky increment behavior

#### G4 — `bars_since_cycle_end` increments on terminal holds
- expected increment by `delta_closed_bars_relevant`

---

### Category H — New-cycle reset behavior

#### H1 — new cycle resets watch and clears cycle-scoped freshness fields
- expected:
  - state = `watch`
  - counters/freshness refs reset as specified

#### H2 — new cycle clears stale cycle-end markers
- expected:
  - `cycle_end_bar_index = None`
  - `cycle_end_timestamp = None`
  - `bars_since_cycle_end = None`

#### H3 — `previous_setup_cycle_id` update on new cycle
- expected:
  - previous = old current
  - current = resolved new id

---

### Category I — Terminal writes

#### I1 — transition into `rejected` with intraday bar id present
- expected:
  - `cycle_end_bar_index = current_bar_index`
  - `cycle_end_timestamp = intraday_bar_id`
  - `bars_since_cycle_end = 0`

#### I2 — transition into `chased` with intraday bar id present
- same expectations

#### I3 — terminal transition in daily run with `intraday_bar_id = None`
- expected:
  - `cycle_end_bar_index = current_bar_index`
  - `cycle_end_timestamp = daily_bar_id`
  - no `ValueError`

#### I4 — terminal hold
- expected:
  - `cycle_end_*` unchanged
  - `bars_since_cycle_end` increments

---

### Category J — Z5 sticky helper field

#### J1 — post-cycle-end reclaim reset flag becomes true
- after cycle end, reclaim drops below reset floor
- expected:
  - flag becomes `True`

#### J2 — sticky true remains true
- later run no longer below reset floor
- expected:
  - flag remains `True`

#### J3 — new cycle clears flag
- expected:
  - flag reset to `None`

---

### Category K — `data_resolution_class` derivation and confidence penalties

#### K1 — `daily_only`
- `data_4h_available = false`
- expected class = `daily_only`

#### K2 — `full_1d_4h`
- 4h available and all consumed reduced-resolution flags false
- expected class = `full_1d_4h`

#### K3 — `reduced_1d_4h`
- 4h available and one consumed reduced-resolution flag true
- expected class = `reduced_1d_4h`

#### K4 — confidence penalties only from allowed sources
- expected:
  - blended penalty applied when relevant
  - not-full-resolution penalty applied when relevant
  - no knappe-margins penalty

---

### Category L — Persistence write path

#### L1 — admitted symbol emits patch
- expected: non-null patch

#### L2 — not-admitted symbol emits no patch
- expected: `persistence_patch = None`

#### L3 — `state_recorded_in_cycle_id` on admitted intra-cycle state change
- e.g. `watch -> early_ready` without new cycle
- expected:
  - `state_recorded_in_cycle_id = setup_cycle_id`

#### L4 — `state_recorded_in_cycle_id` on admitted no-change write
- e.g. `late -> late` in same cycle
- expected:
  - `state_recorded_in_cycle_id = setup_cycle_id`

#### L5 — repository write is idempotent for identical patch
- same patch twice
- expected: stable persisted row without divergent duplicates

#### L6 — atomic write behavior
- if storage write fails, no partial state/cycle divergence is committed

---

### Category M — Determinism

#### M1 — identical input + identical config
- expected:
  - identical disposition
  - identical final state
  - identical reason
  - identical patch

---

## Constraints / Invariants (must not change)

- [ ] Ticket 10 consumes Ticket-9 invalidation/cycle output and does not recompute it
- [ ] `not_admitted / no_active_state` remains a disposition, not a seventh state
- [ ] `admitted = false` does not collapse to `rejected`
- [ ] the canonical six-state enum remains unchanged
- [ ] `setup_cycle_id` comes from Ticket 9
- [ ] `delta_closed_bars_relevant` remains the canonical runtime field name
- [ ] all `bars_since_*` counters remain in canonical 4h-bar units
- [ ] entry references and state freshness fields are sticky within the cycle
- [ ] new-cycle activation clears stale prior cycle-end markers
- [ ] terminal transitions write `cycle_end_*` exactly once on transition
- [ ] Ticket 10 is the only writer for final state/cycle persistence
- [ ] Ticket 10 does not implement the unresolved “knappe Margins” penalty
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
- [ ] Added minimal persistent schema + single write path required by Ticket 10
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` in the same PR

---

## Metadata

```yaml
created_utc: "2026-04-21T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [8, 9]
gesamtkonzept_ref: "§19 Ticket 10"
related_issues: []
follow_ups:
  - "Ticket 11: implement entry patterns on top of final state outputs"
  - "Ticket 15: daily runner consumes the persisted T10 state/cycle contract"
  - "Ticket 17: intraday runner consumes the persisted T10 state/cycle contract"
  - "feature_enhancements.md: operationalize the unresolved 'knappe Margins' state-confidence penalty"
```
