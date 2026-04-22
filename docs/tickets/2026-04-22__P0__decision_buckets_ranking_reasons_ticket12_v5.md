> DRAFT (ticket): Not yet implemented. Canonical truth remains the authoritative source set until merged.

# Title
[P0] Implement decision buckets, priority score, reason codes, and ranking (Ticket 12)

## Context / Source

This ticket implements **Ticket 12** from the Independence-Release consolidated concept: the **decision buckets + ranking + reasons** layer.

**Gesamtkonzept reference:** Gesamtkonzept §2.2 (`decision/`), §13.4, §13.5, §19 Ticket 12, §20 Festlegung 6.

`depends_on: [10, 11]` — requires:
- Ticket 10 (`freshness + state machine`) — provides `StateMachineBundle`
- Ticket 11 (`entry patterns`) — provides `EntryPatternBundle`

Additionally consumes `PhaseInterpretationBundle` from Ticket 8, which is already available in the pipeline by the time T12 runs.

The authoritative fachliche source set is:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, existing repo-canonical docs, older ticket assumptions, or existing storage/config contracts conflict with that source set, the authoritative source set wins. Repo documents remain in force only insofar as they do not contradict this source set. Extend the ticket or ask rather than interpret.

The addendum (`v2_1_addendum_for_future_tickets_and_new_chats.md`) is supplemental working context only. It does not constitute a competing authority and must not override the source set above.

**Primary spec reference for this ticket:** `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` §§9–19.

---

### Important framing for this ticket

This ticket implements the **decision layer** (Layer 6): the operational end-classification that sits after the Phase Interpreter (Layer 3), State Machine (Layer 4), and Entry Pattern Resolution (Layer 5), and before Runner orchestration, Execution Adapter (Ticket 16), and Output/Reporting (Ticket 13).

The layer's single responsibility is:

> Given upstream `PhaseInterpretationBundle`, `StateMachineBundle`, `EntryPatternBundle`, and optionally an `ExecutionInputContract`, assign each coin its final `decision_bucket`, compute its finite `priority_score`, assign stable reason codes, and sort coins deterministically within and across buckets.

This layer does **not** determine market phase, invalidation, cycles, state transitions, or entry patterns. It consumes these as read-only upstream contracts. It does not run execution evaluation; it only reads optional execution fields if already present in the current run.

---

### Dual-mode architecture (pre-execution vs. post-execution)

Abschnitt 7 defines execution inputs as optional (§2.2). The pipeline runs execution only for a reduced candidate set, after an initial decision pass. This creates two distinct operational modes for Ticket 12:

**Pre-execution mode** — no `ExecutionInputContract` provided:
- Bucket assignment uses structural conditions only.
- Priority score uses the three-factor formula (§12.2).
- Coins meeting structural candidate conditions are flagged `execution_required = True` and `execution_pending = True`.

**Post-execution mode** — `ExecutionInputContract` provided:
- Bucket assignment additionally filters by `execution_status`.
- Priority score uses the four-factor formula including `execution_grade` (§12.3).
- `execution_pending = False`.

Which mode is active in a given run is determined by the runner (Ticket 15/16/17), not by this layer. Ticket 12 defines both modes completely. The runner passes or omits the `ExecutionInputContract` argument; Ticket 12 behaves correctly in either case.

---

### Layer-split clarification

- **Ticket 8** is authoritative for: `PhaseInterpretationBundle` including `market_phase`, `market_phase_confidence`, `market_phase_blended`, `market_phase_runner_up`, `market_phase_gap`.
- **Ticket 10** is authoritative for: `StateMachineBundle` including `state_machine_state`, `state_confidence`, and state-internal freshness fields.
- **Ticket 11** is authoritative for: `EntryPatternBundle` including `entry_pattern`, `entry_pattern_score`, `candidate_pattern_scores_within_phase`.
- **Ticket 12** is authoritative for: bucket assignment, `priority_score`, `execution_grade` default mapping, reason codes, ranking, and `DecisionBundle` / `RankedDecision` output.
- **Ticket 16** is authoritative for: the execution adapter, market-side liquidity/orderbook evaluation, and the upstream execution fields. Ticket 16 must populate the fields declared in `ExecutionInputContract` and must remain backward-compatible with the read contract established here. Ticket 16 may supply a finer `execution_grade` numeric score; if it does, that value supersedes the default mapping defined in this ticket (Abschnitt 7 §13.2).

Ticket 12 must not re-implement any Ticket-8, -10, or -11 logic and must not implement any Ticket-16 logic.

---

### Spec inconsistency: `CONFIRMED_PATTERN_UNRESOLVED` in reason code list

Abschnitt 7 §10.4 explicitly assigns `CONFIRMED_PATTERN_UNRESOLVED` as the reason code for the `confirmed_ready + entry_pattern = "none" → late_monitor` rule. However, Abschnitt 7 §17.4 (standard reason code list for `late_monitor`) omits this code. This is a specification inconsistency.

**Resolution for this ticket:** The explicit bucket-assignment rule in §10.4 takes precedence over the incomplete enumeration in §17.4. `CONFIRMED_PATTERN_UNRESOLVED` is a required canonical late_monitor reason code and must be included in the closed `LateMonitorReason` enum. This decision must be documented as an explicit spec-inconsistency resolution in the inline code comment and in `docs/canonical/DATA_MODEL.md`.

---

## Goal

After this ticket is completed:

- `scanner/decision/buckets.py` implements `assign_bucket(phase_bundle, state_bundle, entry_bundle, cfg, execution_contract=None) -> DecisionBundle`
- `scanner/decision/ranking.py` implements `compute_priority_score(...) -> float`, `map_execution_grade(execution_status) -> float`, and `rank_coins(decisions, cfg) -> list[RankedDecision]`
- `scanner/decision/reasons.py` defines all closed reason-code enums and `assign_reasons(...) -> ReasonAssignment`
- `scanner/decision/models.py` defines `DecisionBundle`, `RankedDecision`, `ReasonAssignment`, and `ExecutionInputContract` (read contract for T12; canonical ownership belongs to T16)
- `RankedDecision` carries `symbol: str` as the canonical coin identifier; `symbol` is the final deterministic tie-break key in ranking and must be present on every ranking input record
- All bucket assignments are deterministic: identical inputs and config produce identical bucket, priority score, reason codes, and ranking
- All five user-facing buckets are implemented as a closed `DecisionBucket` enum; `execution_pending` is an output flag on `DecisionBundle`, never a `decision_bucket` value
- `priority_score` is always a finite `float` in `[0, 100]`; it is never `None` (see Priority Score section for the policy on non-evaluable inputs)
- The `execution_grade` default mapping (`direct_ok → 100`, `tranche_ok → 75`, `marginal → 40`, `fail → 0`) is implemented as a pure utility function `map_execution_grade()` in `ranking.py`
- Reason codes form a closed enum per bucket; assignments are fully deterministic per the reason assignment table; no ad-hoc strings and no runtime invention of assignment paths beyond that table
- The special-case rules `early_ready + entry_pattern = "none" → watchlist` and `confirmed_ready + entry_pattern = "none" → late_monitor + CONFIRMED_PATTERN_UNRESOLVED` are implemented exactly
- The `market_phase != "none"` condition is enforced for the `late/chased → late_monitor` rule
- `state_confidence = None` is handled explicitly for all confidence-gated rules (coin fails the rule's gate) and all non-gated rules / Rule 10 catch-all (bucket is still assigned; score uses the floor policy)
- `bucket_reason_primary` and `bucket_reason_secondary` values always belong to the reason-code enum of the assigned `decision_bucket`
- The layer does not access storage, fetch data, produce reports, or trigger execution

---

## Scope

Allowed change surface:

- `scanner/decision/buckets.py` (new)
- `scanner/decision/ranking.py` (new)
- `scanner/decision/reasons.py` (new)
- `scanner/decision/models.py` (new)
- `scanner/decision/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.bucket` and `cfg.priority` defaults / merge / validation (see Config section)
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md` — update only if this file already exists at this path in the repo
- `docs/canonical/DATA_MODEL.md` — update only if this file already exists at this path in the repo
- `docs/canonical/GLOSSARY.md` — update only if this file already exists at this path in the repo

Do not create new canonical doc files in this ticket unless those paths are already established in the repo. Do not manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

## Out of Scope

This ticket must not:

- re-implement or re-derive phase, state, invalidation, cycle, or entry-pattern logic from upstream tickets
- implement execution adapter, market-side liquidity evaluation, or `execution_status` derivation → Ticket 16
- implement runner orchestration or pipeline scheduling → Ticket 15/17
- implement output schemas, report builders, or diagnostics formats → Ticket 13
- implement storage writes or persistence → T12 produces run-local in-memory output only
- introduce a sixth user-facing `DecisionBucket` value beyond the five canonical ones
- produce `NaN`, `inf`, or `-inf` in any numeric output field
- use `execution_required` as a runner-scheduling directive — it is a decision-layer classification flag only
- assign `WATCH_PHASE_VALID`, `FORMER_CANDIDATE_STALE`, or any other reason code not listed in the deterministic reason assignment table — these codes exist in the closed enum per Abschnitt 7 but are not assigned by T12's core bucket logic
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` — §§9–19 define the complete decision layer; §§1–8 are T11 territory
- `independence_release_gesamtkonzept_final.md` — §2.2 (`decision/` module), §13.4, §13.5, §20 Festlegung 6, §19 Ticket 12 workstream position

---

## Upstream Contracts (read-only)

Ticket 12 consumes three typed upstream bundles plus one optional execution input. It does not re-derive any field from these bundles.

### From Ticket 8 — `PhaseInterpretationBundle`

| Field | Type | Notes |
|---|---|---|
| `market_phase` | `Literal["pressure_build", "trend_resume", "transition_reclaim", "none"]` | Required |
| `market_phase_confidence` | `float \| None` | In `[0, 100]`; nullable |
| `market_phase_blended` | `bool` | True when top-phase gap < `phase_gap_floor`; always set, never `None` (Abschnitt 3 §7.5, §8.1) |
| `market_phase_runner_up` | `str \| None` | Supplemental; not used in bucket logic |
| `market_phase_gap` | `float \| None` | Supplemental; not used in bucket logic |

### From Ticket 10 — `StateMachineBundle`

| Field | Type | Notes |
|---|---|---|
| `state_machine_state` | `Literal["watch", "early_ready", "confirmed_ready", "late", "chased", "rejected"]` | Required |
| `state_confidence` | `float \| None` | In `[0, 100]`; nullable |
| `structural_invalidation` | `bool \| None` | Supplemental context; not a bucket gate in T12 |
| `timing_invalidation` | `bool \| None` | Supplemental context; not a bucket gate in T12 |

### From Ticket 11 — `EntryPatternBundle`

| Field | Type | Notes |
|---|---|---|
| `entry_pattern` | `EntryPattern` | One of the 9 v2.1 pattern names or `\"none\"` |
| `entry_pattern_score` | `float` | In `[0.0, 100.0]`; `0.0` when `entry_pattern = \"none\"` |

### From Ticket 16 — `ExecutionInputContract` (optional, may be absent)

This is a **read contract for T12 consumption only**. The canonical execution model and field derivation are authoritative in Ticket 16. Ticket 16 must populate these fields and remain backward-compatible with this contract.

| Field | Type | Notes |
|---|---|---|
| `execution_status` | `Literal["direct_ok", "tranche_ok", "marginal", "fail"]` | Required when contract is present |
| `execution_grade` | `float \| None` | Finer numeric score from T16; if `None` or non-finite, use default mapping |
| `execution_pass` | `bool \| None` | Supplemental |
| `execution_reason` | `str \| None` | Supplemental |

**Status separation rule — non-negotiable:** `ExecutionInputContract` absent (not evaluated in this call) and `ExecutionInputContract` present with `execution_status = \"fail\"` (negatively evaluated) are strictly distinct states. Absent execution must never be treated as failed execution. Not-evaluated ≠ negative evaluation.

---

## Output Contract — `DecisionBundle`

The primary output of this ticket is a typed `DecisionBundle` per coin. Ticket 12 also produces a ranked list of `RankedDecision` across all coins processed in a run.

### `DecisionBundle` fields

| Field | Type | Notes |
|---|---|---|
| `decision_bucket` | `DecisionBucket` | One of the 5 canonical enum values; never `\"execution_pending\"` |
| `priority_score` | `float` | Always a finite float in `[0, 100]`; never `None`, `NaN`, `inf`, or `-inf` |
| `bucket_reason_primary` | `WatchlistReason \| EarlyReason \| ConfirmedReason \| LateMonitorReason \| DiscardedReason` | Always set; must be a member of the reason enum for the assigned bucket |
| `bucket_reason_secondary` | same union type, or `None` | Assigned per deterministic table; `None` when not applicable; when set, must be a member of the reason enum for the assigned bucket |
| `execution_required` | `bool` | See semantics below |
| `execution_pending` | `bool` | True iff `execution_required = True` AND no `ExecutionInputContract` was provided |
| `entry_pattern` | `EntryPattern` | Pass-through from `EntryPatternBundle` |
| `entry_pattern_score` | `float` | Pass-through from `EntryPatternBundle` |

`RankedDecision` is the ranking output record and carries at minimum:

| Field | Type | Notes |
|---|---|---|
| `symbol` | `str` | Canonical coin identifier; final deterministic tie-break key; must be unique per coin in a run |
| `decision` | `DecisionBundle` | The fully assigned decision result for that coin |
| `rank_within_bucket` | `int` | 1-based rank position within the coin's assigned bucket |

### `execution_required` semantics

`execution_required = True` means: the coin's structural conditions qualify it structurally for `early_candidates` or `confirmed_candidates`, so execution evaluation is needed to finalize or confirm the bucket. This is a **decision-layer classification flag only**. Runners (T15/T17) may schedule execution more broadly than this flag indicates and must not treat `execution_required = False` as a guarantee that execution is unnecessary.

### Reason-code bucket-binding invariant

At runtime, `bucket_reason_primary` and `bucket_reason_secondary` (when not `None`) must always be members of the reason-code enum corresponding to the assigned `decision_bucket`. The type annotation uses a union of all reason enums for implementation convenience; this does not permit cross-bucket reason codes at runtime. A `confirmed_candidates` coin must have a `ConfirmedReason` primary code. A `late_monitor` coin must have a `LateMonitorReason` primary code. And so on for all five buckets.

### Output invariants

- `decision_bucket` is always one of the five canonical `DecisionBucket` values
- `priority_score` is always a finite float in `[0, 100]`
- `execution_pending = True` implies `execution_required = True`
- `execution_pending = True` implies no `ExecutionInputContract` was provided
- `bucket_reason_primary` is a valid member of the reason enum for the assigned bucket (see bucket-binding invariant above)
- `bucket_reason_secondary`, when not `None`, is a valid member of the reason enum for the assigned bucket

---

## Bucket Assignment Logic

### Closed bucket enum

```python
class DecisionBucket(str, Enum):
    WATCHLIST = "watchlist"
    EARLY_CANDIDATES = "early_candidates"
    CONFIRMED_CANDIDATES = "confirmed_candidates"
    LATE_MONITOR = "late_monitor"
    DISCARDED = "discarded"
```

`"execution_pending"` is an output flag on `DecisionBundle.execution_pending`. It must never appear as a `decision_bucket` value.

### Evaluation order

Bucket assignment is evaluated top-to-bottom. The first matching rule wins. Each coin matches exactly one rule.

---

### Rule 1 — `discarded` (fast-exit on structural negatives)

A coin is assigned `discarded` immediately if any of the following hold:

- `market_phase = "none"` → reason: `PHASE_NONE`
- `state_machine_state = "rejected"` → reason: `STATE_REJECTED`

No further rules are evaluated.

---

### Rule 2 — `confirmed_candidates`

A coin is assigned `confirmed_candidates` if all of the following hold:

- `state_machine_state = "confirmed_ready"`
- `entry_pattern != "none"`
- `state_confidence` is finite AND `state_confidence >= cfg.bucket.confirmed.min_state_confidence` (default: `65`)
- If `ExecutionInputContract` is present: `execution_status != "fail"`

`state_confidence = None` or non-finite → this rule does not match; proceed to Rule 3.

---

### Rule 3 — `confirmed_ready` + no pattern → `late_monitor`

A coin is assigned `late_monitor` with `bucket_reason_primary = CONFIRMED_PATTERN_UNRESOLVED` if:

- `state_machine_state = "confirmed_ready"`
- `entry_pattern = "none"`

No confidence gate applies. A coin with `state_confidence = None` in this path still receives `late_monitor + CONFIRMED_PATTERN_UNRESOLVED`; its `priority_score` uses the floor policy (see Priority Score section).

Source authority: Gesamtkonzept §13.4, §20 Festlegung 6; Abschnitt 7 §10.4.

---

### Rule 4 — `confirmed_ready` + execution fail → `late_monitor`

A coin is assigned `late_monitor` with `bucket_reason_primary = EXECUTION_FAILED_MONITOR` if:

- `state_machine_state = "confirmed_ready"`
- `entry_pattern != "none"`
- `ExecutionInputContract` is present AND `execution_status = "fail"`

This rule is only reached when Rule 2 failed (execution_status = fail prevented the match) and Rule 3 did not match (entry_pattern != "none").

---

### Rule 5 — `early_candidates`

A coin is assigned `early_candidates` if all of the following hold:

- `state_machine_state = "early_ready"`
- `entry_pattern != "none"`
- `state_confidence` is finite AND `state_confidence >= cfg.bucket.early.min_state_confidence` (default: `60`)
- If `ExecutionInputContract` is present: `execution_status != "fail"`

`state_confidence = None` or non-finite → this rule does not match; proceed to Rule 6.

---

### Rule 6 — `early_ready` + no pattern → `watchlist`

A coin is assigned `watchlist` with `bucket_reason_primary = WATCH_EARLY_NO_PATTERN` if:

- `state_machine_state = "early_ready"`
- `entry_pattern = "none"`

No confidence gate applies. A coin with `state_confidence = None` in this path still receives `watchlist + WATCH_EARLY_NO_PATTERN`; its `priority_score` uses the floor policy.

Source authority: Gesamtkonzept §13.4; Abschnitt 7 §10.1, §10.5.

---

### Rule 7 — `early_ready` + execution fail → `discarded`

A coin is assigned `discarded` with `bucket_reason_primary = EXECUTION_FAILED` if:

- `state_machine_state = "early_ready"`
- `entry_pattern != "none"`
- `ExecutionInputContract` is present AND `execution_status = "fail"`

`early_ready` with failed execution does not qualify for `late_monitor` (reserved for `confirmed_ready` and `late/chased` states).

---

### Rule 8 — `watchlist` (watch state)

A coin is assigned `watchlist` if all of the following hold:

- `state_machine_state = "watch"`
- `state_confidence` is finite AND `state_confidence >= cfg.bucket.watchlist.min_state_confidence` (default: `50`)

`market_phase != "none"` is guaranteed by Rule 1. `state_confidence = None` or non-finite → proceed to Rule 10.

---

### Rule 9 — `late_monitor` (late / chased states)

A coin is assigned `late_monitor` if all of the following hold:

- `state_machine_state in {"late", "chased"}`
- `market_phase != "none"` (guaranteed by Rule 1 for coins reaching this rule, stated explicitly for clarity)

No confidence gate. A coin with `state_confidence = None` in this path still receives `late_monitor`; its `priority_score` uses the floor policy.

**Critical:** a `late` or `chased` coin with `market_phase = "none"` is caught by Rule 1 and assigned `discarded + PHASE_NONE`. It cannot reach Rule 9.

---

### Rule 10 — `discarded` (catch-all)

A coin is assigned `discarded` with `bucket_reason_primary = INSUFFICIENT_CONFIDENCE` if no earlier rule matched. Primary cases:

- `state_confidence = None` or non-finite where a confidence gate applies (Rules 2, 5, 8 not matched)
- `state_confidence` present but below the applicable bucket threshold
- Any other unclassified case

Rule 10 still produces a full `DecisionBundle`, including a finite `priority_score`. The same explicit floor-policy wrapper used for non-gated bucket paths is also applied here, so that catch-all discarded cases remain rankable and comparable within the `discarded` bucket.

---

## Execution-Grade Default Mapping

Abschnitt 7 §13 defines the canonical default mapping. This is implemented in `ranking.py` as the pure utility function `map_execution_grade(execution_status: str) -> float`.

```
"direct_ok"  → 100.0
"tranche_ok" → 75.0
"marginal"   → 40.0
"fail"       → 0.0
```

Usage rules:
- When `ExecutionInputContract` is present and `execution_grade` is a valid finite `float`, use that value directly (T16's finer score supersedes this mapping per Abschnitt 7 §13.2).
- When `ExecutionInputContract` is present but `execution_grade` is `None` or non-finite, apply `map_execution_grade(execution_status)`.
- When `ExecutionInputContract` is absent: `execution_grade` is not used; pre-execution priority score formula applies.
- Unknown or invalid `execution_status` strings must raise a `ValueError` at call time — no silent fallback.

---

## Priority Score

All input scores are in `[0, 100]`. `priority_score` is always a finite `float` in `[0, 100]` after clamping. It is never `None`, `NaN`, `inf`, or `-inf`.

### Pre-execution formula (no `ExecutionInputContract`)

```
priority_score = (
    0.35 * market_phase_confidence
  + 0.40 * state_confidence
  + 0.25 * entry_pattern_score
)
```

### Post-execution formula (`ExecutionInputContract` provided)

```
priority_score = (
    0.30 * market_phase_confidence
  + 0.35 * state_confidence
  + 0.20 * entry_pattern_score
  + 0.15 * execution_grade
)
```

Where `execution_grade` is resolved via the mapping above.

### Penalty: early without pattern

When:
- `state_machine_state = "early_ready"`
- `entry_pattern = "none"`
- `decision_bucket = "watchlist"`

Apply after base score:
```
priority_score = priority_score - cfg.priority.early_without_pattern_penalty
```

Clamp result to `[0, 100]` (minimum `0.0`; the base score cannot exceed `100` under normal inputs so upper clamp is a guard only).

Default: `cfg.priority.early_without_pattern_penalty = 15`

### Policy for non-evaluable score inputs

When a required score component (`market_phase_confidence`, `state_confidence`) is `None` or non-finite, the coin has already failed a confidence gate (Rules 2, 5, 8) and lands in Rule 10 (`discarded + INSUFFICIENT_CONFIDENCE`) before the normal gated-path score computation is attempted.

For non-gated bucket paths (Rules 3, 6, 9) **and for Rule 10 catch-all discarded paths**, score inputs may still be `None` or non-finite. In these cases: substitute `0.0` for each non-evaluable component and compute the score normally. This is an explicit floor policy, not a coercion of `None` to meaningful data. The result will typically be a low score, which is the correct behavior because such coins should sort to the bottom of their bucket.

The substitution of `0.0` for non-evaluable inputs in these paths must be implemented as an explicit named step (e.g., `_coerce_score_input_for_non_gated_path`), not as a silent None-to-zero coercion in the general scoring logic. The general scoring function must still reject `None` inputs with a `TypeError` — it is only called with substituted values from the non-gated / Rule 10 wrapper.

This floor policy is **narrowly scoped** to T12 priority-score computation for non-gated bucket paths (Rules 3, 6, 9) and Rule 10 catch-all discarded paths only. It applies specifically to `state_confidence` and `market_phase_confidence` in those paths. It must not be generalized into a repo-wide missing-numeric policy, a shared utility function, or reused for any other numeric computation in the codebase.

### `entry_pattern_score` is always finite

`entry_pattern_score` is guaranteed finite by the T11 contract (`0.0` when `entry_pattern = "none"`). No `None`/non-finite guard is needed for this field.

---

## Reason Code Assignment

All reason codes are closed enums. Reason assignment is **fully deterministic**: for each bucket path, the primary and secondary codes are fixed as specified in the table below. No implementation may invent runtime assignment paths beyond this table. Reason codes that exist in the enum but are not listed here (`WATCH_PHASE_VALID`, `FORMER_CANDIDATE_STALE`) are present because Abschnitt 7 defines them; T12's core bucket logic must not assign them. Their future assignment (e.g., by runner-level annotation) is out of scope for this ticket.

### Closed enums

```python
class WatchlistReason(str, Enum):
    WATCH_PHASE_VALID = "WATCH_PHASE_VALID"               # reserved; not assigned by T12 bucket logic
    WATCH_STATE_VALID = "WATCH_STATE_VALID"
    WATCH_WAITING_FOR_PROMOTION = "WATCH_WAITING_FOR_PROMOTION"
    WATCH_EARLY_NO_PATTERN = "WATCH_EARLY_NO_PATTERN"

class EarlyReason(str, Enum):
    EARLY_STATE_VALID = "EARLY_STATE_VALID"               # reserved; not assigned by T12 bucket logic
    EARLY_PATTERN_VALID = "EARLY_PATTERN_VALID"
    EARLY_EXECUTION_OK = "EARLY_EXECUTION_OK"
    EARLY_EXECUTION_PENDING = "EARLY_EXECUTION_PENDING"

class ConfirmedReason(str, Enum):
    CONFIRMED_STATE_VALID = "CONFIRMED_STATE_VALID"       # reserved; not assigned by T12 bucket logic
    CONFIRMED_PATTERN_VALID = "CONFIRMED_PATTERN_VALID"
    CONFIRMED_EXECUTION_OK = "CONFIRMED_EXECUTION_OK"
    CONFIRMED_EXECUTION_PENDING = "CONFIRMED_EXECUTION_PENDING"

class LateMonitorReason(str, Enum):
    LATE_STATE = "LATE_STATE"
    CHASED_STATE = "CHASED_STATE"
    EXECUTION_FAILED_MONITOR = "EXECUTION_FAILED_MONITOR"
    FORMER_CANDIDATE_STALE = "FORMER_CANDIDATE_STALE"     # reserved; not assigned by T12 bucket logic
    CONFIRMED_PATTERN_UNRESOLVED = "CONFIRMED_PATTERN_UNRESOLVED"
    # Note: CONFIRMED_PATTERN_UNRESOLVED included per Abschnitt 7 §10.4,
    # which takes precedence over the incomplete enumeration in §17.4.

class DiscardedReason(str, Enum):
    STATE_REJECTED = "STATE_REJECTED"
    PHASE_NONE = "PHASE_NONE"
    PATTERN_NONE_CONFIRMED = "PATTERN_NONE_CONFIRMED"
    # PATTERN_NONE_CONFIRMED is retained only because Abschnitt 7 lists it in the
    # discarded reason enum family. It has no active assignment path in T12:
    # the authoritative explicit rule for confirmed_ready + entry_pattern = "none"
    # is late_monitor + CONFIRMED_PATTERN_UNRESOLVED (Rule 3), not discarded.
    # T12 must not implement any code path that assigns PATTERN_NONE_CONFIRMED.
    EXECUTION_FAILED = "EXECUTION_FAILED"
    INSUFFICIENT_CONFIDENCE = "INSUFFICIENT_CONFIDENCE"
```

### Deterministic reason assignment table

For every bucket path, primary and secondary reason codes are fixed as follows. No other assignments are valid.

| Bucket | Rule | Condition | `bucket_reason_primary` | `bucket_reason_secondary` |
|---|---|---|---|---|
| `watchlist` | 8 | `watch` + finite confidence ≥ threshold | `WATCH_STATE_VALID` | `WATCH_WAITING_FOR_PROMOTION` |
| `watchlist` | 6 | `early_ready` + `entry_pattern = "none"` | `WATCH_EARLY_NO_PATTERN` | `None` |
| `early_candidates` | 5 | `early_ready` + pattern + no execution contract | `EARLY_EXECUTION_PENDING` | `EARLY_PATTERN_VALID` |
| `early_candidates` | 5 | `early_ready` + pattern + execution ok | `EARLY_EXECUTION_OK` | `EARLY_PATTERN_VALID` |
| `confirmed_candidates` | 2 | `confirmed_ready` + pattern + no execution contract | `CONFIRMED_EXECUTION_PENDING` | `CONFIRMED_PATTERN_VALID` |
| `confirmed_candidates` | 2 | `confirmed_ready` + pattern + execution ok | `CONFIRMED_EXECUTION_OK` | `CONFIRMED_PATTERN_VALID` |
| `late_monitor` | 3 | `confirmed_ready` + `entry_pattern = "none"` | `CONFIRMED_PATTERN_UNRESOLVED` | `None` |
| `late_monitor` | 4 | `confirmed_ready` + pattern + execution fail | `EXECUTION_FAILED_MONITOR` | `None` |
| `late_monitor` | 9 | `state = "late"` | `LATE_STATE` | `None` |
| `late_monitor` | 9 | `state = "chased"` | `CHASED_STATE` | `None` |
| `discarded` | 1 | `market_phase = "none"` | `PHASE_NONE` | `None` |
| `discarded` | 1 | `state = "rejected"` | `STATE_REJECTED` | `None` |
| `discarded` | 7 | `early_ready` + pattern + execution fail | `EXECUTION_FAILED` | `None` |
| `discarded` | 10 | catch-all (confidence missing or below threshold) | `INSUFFICIENT_CONFIDENCE` | `None` |

**Note on "execution ok":** `execution_status in {"direct_ok", "tranche_ok", "marginal"}` — all three non-fail statuses receive the same `EARLY_EXECUTION_OK` / `CONFIRMED_EXECUTION_OK` primary code. The grade difference is captured in `priority_score`, not in reason codes.

---

## Ranking

### Ranking input contract

`rank_coins(decisions, cfg)` consumes a list of `RankedDecision`-compatible per-coin records. Each record must contain:

- `symbol: str`
- `decision: DecisionBundle`
- access to the upstream tie-break fields needed for deterministic sorting:
  - `decision.priority_score`
  - `state_confidence`
  - `market_phase_confidence`
  - `decision.entry_pattern_score`

This may be implemented either by storing the tie-break fields directly on `RankedDecision` or by storing typed references / snapshots needed for sorting. What is **not** acceptable is an underspecified ranking input that omits one or more of these fields while still claiming deterministic sorting.

### Primary bucket ordering (for display and downstream consumers)

1. `confirmed_candidates`
2. `early_candidates`
3. `watchlist`
4. `late_monitor`
5. `discarded`

### Sort order within each bucket

`rank_coins` receives a list of per-coin records, each identified by its `symbol: str`. The `symbol` field must be present on every input and is guaranteed unique per coin per run.

Sort by the following fields in order. All comparisons are deterministic.

1. `priority_score` descending
2. `state_confidence` descending (treat `None` as lower than any finite value)
3. `market_phase_confidence` descending (treat `None` as lower than any finite value)
4. `entry_pattern_score` descending
5. `symbol` alphabetically ascending (final tie-break; always unique)

Since `priority_score` is always finite (never `None`), step 1 requires no special-casing.

### Determinism requirement

No implicit dict or set ordering may influence ranking. Given identical input bundles and identical config, the full ranked list — including bucket assignments, priority scores, reason codes, and symbol positions — must be identical across all runs and environments.

---

## Config

### Required config blocks

```
cfg.bucket
  .watchlist
    .min_state_confidence    (default: 50, float, range [0, 100])
  .early
    .min_state_confidence    (default: 60, float, range [0, 100])
  .confirmed
    .min_state_confidence    (default: 65, float, range [0, 100])

cfg.priority
  .early_without_pattern_penalty   (default: 15, float, range [0, 100])
```

Note: `cfg.bucket.discarded` is **not** defined here. The catch-all Rule 10 assigns `discarded` based on structural conditions (no earlier rule matched), not on a configurable confidence threshold. There is no operative discarded-confidence parameter in T12.

### Config rules

- All fields above are required in the resolved config. Missing fields at load time raise a fast validation error.
- Partial nested overrides merge field-by-field with spec defaults; unspecified nested fields fall back to defaults (**Merge semantics, not Replace**).
- Invalid values (negative, non-finite, outside `[0, 100]`) raise a fast validation error at config load time, not silently at runtime.
- No ad-hoc raw-dict fallbacks inside the decision logic; all threshold access goes through the validated config object.

---

## Numerics, Nullability, and Status Separation

### `priority_score` is always finite

`priority_score` is a `float` in `[0, 100]`. It is never `None`, `NaN`, `inf`, or `-inf`. See the priority score section for how non-evaluable inputs are handled per bucket path.

### Nullable upstream fields

`state_confidence` and `market_phase_confidence` are nullable. `None` means not reliably computable. They must not be silently coerced to `0.0` in general code paths. The two explicit handling contexts are:

1. **Confidence-gated rules (Rules 2, 5, 8):** `None` or non-finite causes the rule not to match. The coin proceeds to the next rule.
2. **Non-gated rules (Rules 3, 6, 9) and Rule 10 catch-all:** `None` or non-finite inputs are substituted with `0.0` via the named `_coerce_score_input_for_non_gated_path` helper before score computation. This substitution is explicit and isolated; it does not affect any other code path.

### Status separation

Three states must remain strictly distinct:

| State | Meaning | T12 handling |
|---|---|---|
| No `ExecutionInputContract` | Execution not evaluated in this call | Pre-execution mode; candidate-eligible coins get `execution_pending = True` |
| `execution_status = "fail"` | Execution negatively evaluated | Blocks candidate buckets; routes to `late_monitor` or `discarded` |
| `execution_status = "marginal"` | Execution evaluated with partial/qualified outcome | Does not block candidate buckets; affects `priority_score` via grade |

Not-evaluated must never be treated as failed.

---

## Tests

All tests are deterministic fixture-based unit tests. No live data, no external I/O, no storage access.

### Bucket assignment tests

| # | Description | Expected bucket | Expected primary reason |
|---|---|---|---|
| T-BA-1 | `market_phase = "none"`, any state | `discarded` | `PHASE_NONE` |
| T-BA-2 | `state = "rejected"`, valid phase | `discarded` | `STATE_REJECTED` |
| T-BA-3 | `confirmed_ready`, pattern valid, confidence 70, no execution | `confirmed_candidates` | `CONFIRMED_EXECUTION_PENDING` |
| T-BA-4 | `confirmed_ready`, pattern valid, confidence 70, execution `direct_ok` | `confirmed_candidates` | `CONFIRMED_EXECUTION_OK` |
| T-BA-5 | `confirmed_ready`, pattern valid, confidence 70, execution `marginal` | `confirmed_candidates` | `CONFIRMED_EXECUTION_OK` |
| T-BA-6 | `confirmed_ready`, pattern valid, confidence 70, execution `fail` | `late_monitor` | `EXECUTION_FAILED_MONITOR` |
| T-BA-7 | `confirmed_ready`, `entry_pattern = "none"`, confidence 70 | `late_monitor` | `CONFIRMED_PATTERN_UNRESOLVED` |
| T-BA-8 | `confirmed_ready`, `entry_pattern = "none"`, `state_confidence = None` | `late_monitor` | `CONFIRMED_PATTERN_UNRESOLVED` |
| T-BA-9 | `early_ready`, pattern valid, confidence 65, no execution | `early_candidates` | `EARLY_EXECUTION_PENDING` |
| T-BA-10 | `early_ready`, pattern valid, confidence 65, execution `direct_ok` | `early_candidates` | `EARLY_EXECUTION_OK` |
| T-BA-11 | `early_ready`, pattern valid, confidence 65, execution `fail` | `discarded` | `EXECUTION_FAILED` |
| T-BA-12 | `early_ready`, `entry_pattern = "none"` | `watchlist` | `WATCH_EARLY_NO_PATTERN` |
| T-BA-13 | `early_ready`, `entry_pattern = "none"`, `state_confidence = None` | `watchlist` | `WATCH_EARLY_NO_PATTERN` |
| T-BA-14 | `watch`, phase valid, `state_confidence = 55` | `watchlist` | `WATCH_STATE_VALID` |
| T-BA-15 | `watch`, phase valid, `state_confidence = 49` (below default 50) | `discarded` | `INSUFFICIENT_CONFIDENCE` |
| T-BA-16 | `watch`, phase valid, `state_confidence = None` | `discarded` | `INSUFFICIENT_CONFIDENCE` |
| T-BA-17 | `state = "late"`, `market_phase = "trend_resume"` | `late_monitor` | `LATE_STATE` |
| T-BA-18 | `state = "chased"`, `market_phase = "pressure_build"` | `late_monitor` | `CHASED_STATE` |
| T-BA-19 | `state = "late"`, `market_phase = "none"` | `discarded` | `PHASE_NONE` (Rule 1, not Rule 9) |
| T-BA-20 | `state = "chased"`, `market_phase = "none"` | `discarded` | `PHASE_NONE` (Rule 1, not Rule 9) |
| T-BA-21 | `confirmed_ready`, pattern valid, confidence exactly 65.0 | `confirmed_candidates` | `CONFIRMED_EXECUTION_PENDING` |
| T-BA-22 | `confirmed_ready`, pattern valid, confidence 64.9999 (below threshold) | `discarded` | `INSUFFICIENT_CONFIDENCE` |

### Reason code secondary assignment tests

| # | Description | Expected secondary reason |
|---|---|---|
| T-RC-1 | `early_candidates`, no execution | `EARLY_PATTERN_VALID` |
| T-RC-2 | `early_candidates`, execution ok | `EARLY_PATTERN_VALID` |
| T-RC-3 | `confirmed_candidates`, no execution | `CONFIRMED_PATTERN_VALID` |
| T-RC-4 | `watchlist` via `watch` state | `WATCH_WAITING_FOR_PROMOTION` |
| T-RC-5 | `watchlist` via `early_ready + none` | `None` |
| T-RC-6 | `late_monitor` via `CONFIRMED_PATTERN_UNRESOLVED` path | `None` |
| T-RC-7 | `discarded` via `PHASE_NONE` | `None` |

### Reason-code bucket-binding test

| # | Description | Expected |
|---|---|---|
| T-RCB-1 | For every assigned `DecisionBundle` in a multi-coin run: `bucket_reason_primary` is a member of the reason enum for that coin's `decision_bucket` | All pass; no cross-bucket reason codes |

### Priority score tests

| # | Description | Expected |
|---|---|---|
| T-PS-1 | Pre-execution: `mpc=80, sc=70, eps=60` | `0.35*80 + 0.40*70 + 0.25*60 = 71.0` |
| T-PS-2 | Post-execution: same inputs, `execution_status = "direct_ok"` (grade=100) | `0.30*80 + 0.35*70 + 0.20*60 + 0.15*100 = 75.5` |
| T-PS-3 | Post-execution: same inputs, finer `execution_grade = 85.0` from T16 | uses `85.0` directly |
| T-PS-4 | Early without pattern penalty: base score `65.0`, penalty `15` | `50.0` |
| T-PS-5 | Early without pattern penalty: base score `10.0`, penalty `15` | `0.0` (clamped) |
| T-PS-6 | Non-gated path (Rule 6), `state_confidence = None` | `priority_score` computed with `sc=0.0` substitution; result is finite float |
| T-PS-7 | Non-gated path (Rule 9), `market_phase_confidence = None` | `priority_score` computed with `mpc=0.0` substitution; result is finite float |
| T-PS-8a | `watch` + `state_confidence = None`, phase valid; Rule 8 not matched → Rule 10 → `discarded + INSUFFICIENT_CONFIDENCE` | `priority_score` is a finite float; computed via floor substitution in the Rule 10 catch-all path |
| T-PS-8b | `confirmed_ready` + `entry_pattern = "none"` + `state_confidence = None`; Rule 3 fires → `late_monitor + CONFIRMED_PATTERN_UNRESOLVED` | `priority_score` is a finite float; computed via `_coerce_score_input_for_non_gated_path` with `sc=0.0` |
| T-PS-9 | General score function called with `state_confidence = None` directly | raises `TypeError` — the general function does not accept `None` |

### execution_grade mapping tests

| # | Description | Expected |
|---|---|---|
| T-EG-1 | `map_execution_grade("direct_ok")` | `100.0` |
| T-EG-2 | `map_execution_grade("tranche_ok")` | `75.0` |
| T-EG-3 | `map_execution_grade("marginal")` | `40.0` |
| T-EG-4 | `map_execution_grade("fail")` | `0.0` |
| T-EG-5 | `map_execution_grade("unknown_value")` | raises `ValueError` |

### Ranking tests

| # | Description | Expected |
|---|---|---|
| T-RK-1 | Two coins, same bucket, `priority_score` differs | Higher score ranked first |
| T-RK-2 | Two coins, same `priority_score`, `state_confidence` differs | Higher `state_confidence` ranked first |
| T-RK-3 | Two coins, all numeric scores identical, symbols `"ZZZ"` and `"AAA"` | `"AAA"` ranked first |
| T-RK-4 | Coins across multiple buckets | Order: confirmed → early → watchlist → late → discarded |
| T-RK-5 | Same input twice | Identical ranked output |

### Status separation tests

| # | Description | Expected |
|---|---|---|
| T-SS-1 | No `ExecutionInputContract`, structural candidate | `execution_pending = True`, no execution-fail bucket effects |
| T-SS-2 | `ExecutionInputContract` with `execution_status = "fail"` | `execution_pending = False`, execution-fail bucket effects applied |
| T-SS-3 | T-SS-1 and T-SS-2 with identical structural inputs | Different `decision_bucket`; confirms not-evaluated ≠ fail |

### Config tests

| # | Description | Expected |
|---|---|---|
| T-CFG-1 | All config fields absent (full defaults) | All defaults applied |
| T-CFG-2 | Partial override: `cfg.bucket.early.min_state_confidence = 70` only | Only that field changed; watchlist and confirmed remain at defaults |
| T-CFG-3 | `cfg.bucket.confirmed.min_state_confidence = -1` | Raises validation error at load |
| T-CFG-4 | `cfg.priority.early_without_pattern_penalty = float("nan")` | Raises validation error at load |
| T-CFG-5 | `cfg.bucket` block missing entirely | Raises validation error at load |

### Non-gated / Rule 10 score floor tests

| # | Description | Expected |
|---|---|---|
| T-FL-1 | Rule 6 (`early_ready + none`), `state_confidence = None`, `market_phase_confidence = None` | `priority_score` is a finite float (≥ 0.0); not `None`, not `NaN` |
| T-FL-2 | Rule 9 (`late`), `state_confidence = None` | `priority_score` is a finite float |
| T-FL-3 | Rule 10 (`watch` with missing confidence), all score inputs `None` | `priority_score = 0.0` |

### Determinism test

| # | Description | Expected |
|---|---|---|
| T-DET-1 | Call `assign_bucket` + `rank_coins` twice with identical inputs and config | Byte-identical `RankedDecision` list and ranking both times |

---

## Docs to Update

Update the following files only if they already exist at the expected paths. If a file does not exist, do not create it in this ticket.

- **`docs/canonical/ARCHITECTURE.md`** — add `scanner/decision/` module description; note Layer-6 position; document the pre-execution / post-execution dual-mode contract; note that this layer produces only run-local in-memory output (no storage writes)
- **`docs/canonical/DATA_MODEL.md`** — document `DecisionBundle` and `RankedDecision` fields and invariants; document the five canonical `DecisionBucket` values; document the `execution_pending` flag vs. `decision_bucket` distinction; document the bucket-binding invariant for reason codes; document the `CONFIRMED_PATTERN_UNRESOLVED` spec-inconsistency resolution (§10.4 over §17.4); document the `execution_grade` default mapping and T16 override semantics; document `ExecutionInputContract` as a T12 read contract with T16 as canonical owner; document the finite-score floor policy for non-gated paths and Rule 10 catch-all paths; add cross-references to `EntryPatternBundle` (T11), `PhaseInterpretationBundle` (T8), and `StateMachineBundle` (T10)
- **`docs/canonical/GLOSSARY.md`** — add or verify entries for: `decision_bucket`, `DecisionBucket` (enum), `priority_score`, `execution_grade`, `execution_required`, `execution_pending`, `bucket_reason_primary`, `bucket_reason_secondary`, `DecisionBundle`, `RankedDecision`, `symbol` (as ranking tie-break key), `rank_within_bucket`, `ExecutionInputContract`, `map_execution_grade`, `_coerce_score_input_for_non_gated_path`, pre-execution mode, post-execution mode, and all five canonical bucket names
