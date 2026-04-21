> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

> DRAFT (ticket): Not yet implemented. Canonical truth remains the authoritative source set until merged.

# Title
[P0] Implement entry-pattern resolution and typed EntryPatternBundle (Ticket 11)

## Context / Source

This ticket implements **Ticket 11** from the Independence-Release consolidated concept: the **entry patterns** layer.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §13.4, §19 Ticket 11, §20 Festlegung 6.

`depends_on: [8, 10]` — requires:
- Ticket 8 (`phase interpreter`) — provides `PhaseInterpretationBundle` with the final `market_phase`; `market_phase` is a direct data input to the resolver function
- Ticket 10 (`freshness + state machine`) — provides `StateMachineBundle`; Ticket 10 is a **sequencing dependency, not a data-input dependency** for the resolver function; pattern resolution may only run after the state machine layer has completed, but `StateMachineBundle` fields are not consumed by the resolver

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older ticket assumptions, repo-canonical docs, or legacy material conflict with that source set, the authoritative source set wins. Do not invent semantics beyond the authoritative source set. If a conflict or missing rule is encountered during implementation, stop at the narrowest safe implementation boundary and document the gap explicitly in the PR notes.

The addendum (`v2_1_addendum_for_future_tickets_and_new_chats.md`) is supplemental working context only. It does not constitute a competing authority and must not override the source set above.

---

### Important framing for this ticket

This ticket implements the **entry-pattern resolution layer** (Layer 5), which sits after the Phase Interpreter (Layer 3) and the State Machine (Layer 4), and before Decision Buckets and Ranking (Ticket 12).

The layer's single responsibility is:

> Given the current `market_phase` and the canonical upstream axis values, determine which entry pattern (if any) applies, and produce a typed `EntryPatternBundle`.

**Critical input contract clarification — why `state_bundle` is not a function parameter:**

`depends_on: [8, 10]` is semantically real: pattern resolution may only occur after the state machine has run (Layer 4 must complete before Layer 5). However, `resolve_entry_pattern` does not receive `StateMachineBundle` as a function argument.

Rationale: Pattern admission conditions and pattern scores are derived exclusively from `market_phase` and canonical axis values (Abschnitt 7 §§4–8). Including `state_bundle` in the resolver signature would create a temptation — and an opportunity for Codex — to condition pattern logic on state fields. That is architecturally prohibited. The layer dependency is enforced at the pipeline/runner level, not at the function signature level.

Codex must not add `state_bundle`, `state_machine_state`, `state_confidence`, `structural_invalidation`, `timing_invalidation`, or any other T10 output field to the resolver signature or its implementation.

---

### Downstream guardrail (authoritative, operative in Ticket 12)

Ticket 11 does **not** implement bucket assignment. However, the following downstream semantics are authoritative and must be documented at the T11 interface boundary so that Ticket 12 cannot misinterpret the `entry_pattern = "none"` output:

- `state_machine_state = "early_ready"` + `entry_pattern = "none"` → mapped by T12 to `watchlist` (not `discarded`)
- `state_machine_state = "confirmed_ready"` + `entry_pattern = "none"` → mapped by T12 to `late_monitor` with Reason Code `CONFIRMED_PATTERN_UNRESOLVED`

Source authority: Gesamtkonzept §13.4, §20 Festlegung 6; Abschnitt 7 §10.1, §10.4.

`entry_pattern = "none"` is a valid fachlicher output, not an error condition. Ticket 11 must not treat it as exceptional.

---

### Layer-split clarification

Under the Independence-Release architecture:

- **Ticket 11** is authoritative for: phase-gated pattern admission, pattern scoring, argmax selection, tie-break ordering, and the typed `EntryPatternBundle` output
- **Ticket 12** is authoritative for: bucket assignment, priority score, reason codes, ranking, and the execution influence on final output

Ticket 11 must not implement any Ticket-12 logic, and Ticket 12 must not re-implement any Ticket-11 logic.

---

### Addendum / working-context checks

This ticket explicitly follows the addendum working-context leitplanken:

- **A.2 Schichtenarchitektur** — T11 remains strictly inside its own layer; it does not pull state re-derivation, invalidation logic, execution logic, bucket assignment, or ranking into pattern resolution
- **A.5 Persistenz ist fachlicher Kern** — T11 produces run-local in-memory outputs only; no persistence of pattern outputs occurs in this ticket
- **A.6 Historie liefert Kontext, aber keinen Override** — T11 is intentionally stateless and history-free; it consumes only current-run upstream bundles
- **Teil B Präzisierungs-Check** — the `confirmed_ready + entry_pattern = none → late_monitor` rule is resolved and authoritative; Ticket 11 documents it as a downstream guardrail and does not operationalize it

---

## Goal

After this ticket is completed:

- `scanner/entry/patterns.py` implements `resolve_entry_pattern(phase_bundle, tier1_bundle, tier2_bundle, cfg) -> EntryPatternBundle`
- `scanner/entry/models.py` contains `EntryPatternBundle` and the `EntryPattern` Literal type
- Pattern resolution is deterministic: identical inputs and config always produce identical output
- Pattern resolution is strictly phase-gated: no cross-phase pattern evaluation occurs
- All 9 v2.1 patterns are implemented with their exact spec-defined admission conditions, score formulas, and tie-break ordering
- `compute_breakout_expansion_fit` is implemented as an explicit, separately testable helper function in `patterns.py`
- `entry_pattern = "none"` and `entry_pattern_score = 0.0` are produced whenever no pattern is admitted, regardless of whether the upstream phase or state is otherwise valid
- Non-finite, null, or otherwise invalid axis inputs cause the affected pattern(s) to be treated as not admitted — they are never propagated into scores
- `candidate_pattern_scores_within_phase` contains only admitted patterns — no 0.0 placeholder entries for non-admitted patterns
- The function signature does not include `state_bundle` or any T10 field; state fields do not influence pattern admission or scoring
- The function consumes only typed upstream bundles and validated `cfg`; it does not fetch data, access storage, access OHLCV, or produce output/report artifacts
- Downstream Ticket 12 can consume a stable, fully typed `EntryPatternBundle` without reconstructing any pattern logic

---

## Scope

Allowed change surface:

- `scanner/entry/patterns.py` (new)
- `scanner/entry/models.py` (new)
- `scanner/entry/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.pattern` defaults / merge / validation (see Config section)
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md` — update only if this file already exists at this path in the repo
- `docs/canonical/DATA_MODEL.md` — update only if this file already exists at this path in the repo
- `docs/canonical/GLOSSARY.md` — update only if this file already exists at this path in the repo

Do not create new canonical doc files in this ticket unless those paths are already established in the repo as the intended canonical locations. Canonical doc structure is not in scope for T11. Do not manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.

## Out of Scope

This ticket must not:

- implement Decision Buckets, priority score, or reason codes → Ticket 12
- implement ranking logic → Ticket 12
- implement execution adapter, execution grading, or execution pass/fail logic → Ticket 16
- implement the `execution_pending` flag or its bucket resolution → Ticket 12
- include `state_bundle`, `state_machine_state`, `state_confidence`, `structural_invalidation`, or `timing_invalidation` in the resolver function signature or its implementation
- re-derive, re-evaluate, or re-interpret state, freshness, invalidation, or cycle logic
- consume OHLCV data directly
- write to storage or produce report/diagnostics artifacts
- implement the bucket-level fallback rules for `early_ready + none` or `confirmed_ready + none` — those are T12
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `v2_1_abschnitt_7_entry_pattern_decision_buckets_rev3_aligned.md` — §§1–8 define the complete pattern layer; §§9–19 are T12 territory and must not bleed into T11
- `independence_release_gesamtkonzept_final.md` — §13.4, §20 Festlegung 6 for the downstream guardrail semantics; §19 Ticket 11 for workstream position

Supplemental upstream contract references:

- Ticket 8 — typed `PhaseInterpretationBundle` input contract (`market_phase` is the primary gate)
- Ticket 6 — typed `Tier1AxisBundle`
- Ticket 7 — typed `Tier2AxisBundle`

Supplemental working context:

- `v2_1_addendum_for_future_tickets_and_new_chats.md`

Repo process references:

- `docs/tickets/_TEMPLATE.md`
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- `docs/canonical/WORKFLOW_CODEX.md`

---

## Proposed Change (high-level)

### Before

- Tickets 8 and 10 provide the canonical phase and state outputs as upstream layer context.
- The repo does not yet expose a typed entry-pattern contract.
- Ticket 12 cannot be safely implemented without a stable `EntryPatternBundle`.

### After

- `scanner/entry/patterns.py` resolves entry patterns deterministically from phase + axes
- `scanner/entry/models.py` defines `EntryPatternBundle` and `EntryPattern`
- Ticket 12 consumes `EntryPatternBundle` without reconstructing pattern logic

### Input contract

`resolve_entry_pattern` receives exactly:

```python
def resolve_entry_pattern(
    phase_bundle: PhaseInterpretationBundle,
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg,
) -> EntryPatternBundle:
    ...
```

The function must not have additional parameters. Codex must not add implicit access to OHLCV, raw features, storage, state bundles, or any other data source inside `patterns.py`.

---

## Implementation Specification

### Phase Gate (§4)

Pattern resolution is always phase-gated. The first step of `resolve_entry_pattern` is:

```python
if phase_bundle.market_phase not in {"pressure_build", "trend_resume", "transition_reclaim"}:
    return EntryPatternBundle(
        entry_pattern="none",
        entry_pattern_score=0.0,
        candidate_pattern_scores_within_phase={},
    )
```

No pattern evaluation occurs for `market_phase = "none"` or any unrecognized phase value. The `candidate_pattern_scores_within_phase` dict is empty `{}` in this case — not populated with zero-value entries.

---

### Admission and Scoring (§§5–7)

For the current phase, evaluate all patterns defined for that phase. A pattern is **admitted** if and only if all of its admission conditions are satisfied with valid, finite numeric inputs.

**General rules:**
- Each condition is an AND-conjunction — all conditions must hold
- If any axis value required for a pattern's admission conditions or score formula is `None`, `NaN`, `inf`, or `-inf`, the pattern is **not admitted**
- Score computation only occurs for admitted patterns
- Given the spec-defined formulas and the 0..100 axis scale, computed pattern scores are expected to fall within 0..100; do not add extra clamping unless the spec explicitly requires it for that formula (as it does for `compute_breakout_expansion_fit` and the `break_and_hold` expansion fit term)
- No implicit `bool()` coercion of nullable axis values

**Important: the "score-formula inputs are also required" rule for patterns without explicit admission conditions on all axes:**

For patterns where an axis appears in the score formula but not in the explicit admission conditions (specifically `volume_regime_shift` in `base_reclaim`), the axis is still treated as required for admission. Rationale: if a score-formula input is missing, the resolver would need a secondary missing-data scoring policy not defined by Abschnitt 7. For v2.1 implementation safety, all axes used in a pattern's score formula are treated as required for admission, regardless of whether they appear in the formal admission conditions.

---

#### Phase: `pressure_build`

**Candidate axis inputs (§5.1):**
`reclaim_progress`, `compression_strength`, `volume_regime_shift`, `expansion_progress_structural`, `freshness_distance_structural`, `base_integrity_simplified`

---

**Pattern: `range_reclaim` (§5.2)**

Admission conditions:
- `reclaim_progress >= cfg.pattern.pressure_build.range_reclaim.min_reclaim` (default: `45`)
- `compression_strength >= cfg.pattern.pressure_build.range_reclaim.min_compression` (default: `55`)
- `freshness_distance_structural <= cfg.pattern.pressure_build.range_reclaim.max_freshness` (default: `60`)

Score:
```
score = (0.45 * reclaim_progress
       + 0.30 * compression_strength
       + 0.25 * (100 - freshness_distance_structural))
```

---

**Pattern: `breakout` (§5.3)**

Admission conditions:
- `expansion_progress_structural >= cfg.pattern.pressure_build.breakout.min_expansion` (default: `35`)
- `volume_regime_shift >= cfg.pattern.pressure_build.breakout.min_volume_shift` (default: `55`)
- `freshness_distance_structural <= cfg.pattern.pressure_build.breakout.max_freshness` (default: `65`)

Helper function — `compute_breakout_expansion_fit` (must be implemented as a named top-level function in `patterns.py`, separately testable):

```python
def compute_breakout_expansion_fit(expansion_progress_structural: float, target_expansion: float) -> float:
    return max(0.0, min(100.0, 100.0 - abs(expansion_progress_structural - target_expansion)))
```

Default: `cfg.pattern.pressure_build.breakout.target_expansion = 40`

Score:
```
fit = compute_breakout_expansion_fit(
    expansion_progress_structural,
    cfg.pattern.pressure_build.breakout.target_expansion
)

score = (0.40 * fit
       + 0.35 * volume_regime_shift
       + 0.25 * (100 - freshness_distance_structural))
```

Rationale (per Abschnitt 7 §5.3): monotonically more expansion is not rewarded. A moderate, fresh expansion zone is optimal. Too little expansion = break not yet clean; too much = already run.

---

**Pattern: `break_and_hold` (§5.4)**

Admission conditions:
- `reclaim_progress >= cfg.pattern.pressure_build.break_and_hold.min_reclaim` (default: `55`)
- `base_integrity_simplified >= cfg.pattern.pressure_build.break_and_hold.min_base_integrity` (default: `45`)
- `cfg.pattern.pressure_build.break_and_hold.min_expansion <= expansion_progress_structural <= cfg.pattern.pressure_build.break_and_hold.max_expansion` (defaults: `30` and `65`)

Score:
```
score = (0.35 * reclaim_progress
       + 0.25 * base_integrity_simplified
       + 0.20 * volume_regime_shift
       + 0.20 * max(0.0, min(100.0, 100.0 - abs(expansion_progress_structural - 45.0))))
```

The score target `45.0` is spec-fixed for v2.1 (Abschnitt 7 §5.4). It must not be externalized into config in this ticket. It is not the same quantity as `min_expansion` or `max_expansion`.

---

#### Phase: `trend_resume`

**Candidate axis inputs (§6.1):**
`trend_strength`, `reclaim_progress`, `pullback_quality_simplified`, `reacceleration_strength_simplified`, `freshness_distance_structural`, `expansion_progress_structural`

---

**Pattern: `shallow_pullback` (§6.2)**

Admission conditions:
- `pullback_quality_simplified >= cfg.pattern.trend_resume.shallow_pullback.min_pullback_quality` (default: `55`)
- `trend_strength >= cfg.pattern.trend_resume.shallow_pullback.min_trend` (default: `55`)
- `freshness_distance_structural <= cfg.pattern.trend_resume.shallow_pullback.max_freshness` (default: `65`)

Score:
```
score = (0.40 * pullback_quality_simplified
       + 0.30 * trend_strength
       + 0.30 * (100 - freshness_distance_structural))
```

---

**Pattern: `resume_reclaim` (§6.3)**

Admission conditions:
- `reclaim_progress >= cfg.pattern.trend_resume.resume_reclaim.min_reclaim` (default: `50`)
- `reacceleration_strength_simplified >= cfg.pattern.trend_resume.resume_reclaim.min_reaccel` (default: `50`)
- `freshness_distance_structural <= cfg.pattern.trend_resume.resume_reclaim.max_freshness` (default: `60`)

Score:
```
score = (0.35 * reclaim_progress
       + 0.35 * reacceleration_strength_simplified
       + 0.30 * (100 - freshness_distance_structural))
```

---

**Pattern: `continuation_breakout` (§6.4)**

Admission conditions:
- `trend_strength >= cfg.pattern.trend_resume.continuation_breakout.min_trend` (default: `60`)
- `reacceleration_strength_simplified >= cfg.pattern.trend_resume.continuation_breakout.min_reaccel` (default: `55`)
- `expansion_progress_structural <= cfg.pattern.trend_resume.continuation_breakout.max_expansion` (default: `70`)

Score:
```
score = (0.35 * trend_strength
       + 0.35 * reacceleration_strength_simplified
       + 0.30 * (100 - expansion_progress_structural))
```

---

#### Phase: `transition_reclaim`

**Candidate axis inputs (§7.1):**
`reclaim_progress`, `trend_strength`, `base_integrity_simplified`, `volume_regime_shift`, `freshness_distance_structural`

---

**Pattern: `ema_reclaim` (§7.2)**

Admission conditions:
- `reclaim_progress >= cfg.pattern.transition_reclaim.ema_reclaim.min_reclaim` (default: `45`)
- `trend_strength >= cfg.pattern.transition_reclaim.ema_reclaim.min_trend` (default: `40`)
- `freshness_distance_structural <= cfg.pattern.transition_reclaim.ema_reclaim.max_freshness` (default: `65`)

Score:
```
score = (0.45 * reclaim_progress
       + 0.25 * trend_strength
       + 0.30 * (100 - freshness_distance_structural))
```

---

**Pattern: `base_reclaim` (§7.3)**

Admission conditions:
- `base_integrity_simplified >= cfg.pattern.transition_reclaim.base_reclaim.min_base_integrity` (default: `45`)
- `reclaim_progress >= cfg.pattern.transition_reclaim.base_reclaim.min_reclaim` (default: `45`)
- `volume_regime_shift` must be a finite numeric value (required for score; see general "score-formula inputs are also required" rule above)

Score:
```
score = (0.40 * base_integrity_simplified
       + 0.35 * reclaim_progress
       + 0.25 * volume_regime_shift)
```

---

**Pattern: `early_reversal_break` (§7.4)**

Admission conditions:
- `reclaim_progress >= cfg.pattern.transition_reclaim.early_reversal_break.min_reclaim` (default: `50`)
- `volume_regime_shift >= cfg.pattern.transition_reclaim.early_reversal_break.min_volume_shift` (default: `50`)
- `freshness_distance_structural <= cfg.pattern.transition_reclaim.early_reversal_break.max_freshness` (default: `60`)

Score:
```
score = (0.40 * reclaim_progress
       + 0.30 * volume_regime_shift
       + 0.30 * (100 - freshness_distance_structural))
```

---

### Pattern Selection (§8)

After computing scores for all admitted patterns within the current phase:

```
entry_pattern = argmax(admitted_pattern_scores)
entry_pattern_score = max(admitted_pattern_scores)
```

If no pattern is admitted:
```
entry_pattern = "none"
entry_pattern_score = 0.0
candidate_pattern_scores_within_phase = {}
```

**Tie-break (§8.4):** When two or more admitted patterns produce an exactly equal score, select by the following fixed priority order (earlier = higher priority):

| Phase | Tie-break order |
|---|---|
| `pressure_build` | `range_reclaim` > `break_and_hold` > `breakout` |
| `trend_resume` | `resume_reclaim` > `shallow_pullback` > `continuation_breakout` |
| `transition_reclaim` | `base_reclaim` > `ema_reclaim` > `early_reversal_break` |

Rationale (per Abschnitt 7 §8.4): stable, well-defined patterns take precedence over more aggressive or earlier-signal variants.

---

### Missing / Invalid / Nullability Rules

These rules apply universally and are non-negotiable. Codex must not introduce implicit fallbacks.

1. **Non-finite inputs:** If a required axis value is `float('nan')`, `float('inf')`, or `float('-inf')`, the pattern is **not admitted**. Non-finite values must not be propagated into score computations.

2. **Null inputs:** If a required axis value is `None`, the pattern is **not admitted**. No implicit coercion of `None` to `0`, `0.0`, or `False` is permitted.

3. **Required axis scope:** Any axis appearing in a pattern's admission conditions or score formula is treated as required. If any required axis is missing or invalid, the pattern is not admitted (see rule 1 and 2).

4. **`market_phase = "none"` or unrecognized phase:** Immediately return `entry_pattern = "none"`, `entry_pattern_score = 0.0`, `candidate_pattern_scores_within_phase = {}`. No pattern evaluation occurs.

5. **No implicit `bool()` coercion:** Nullable axis fields must not be evaluated in boolean context as a shorthand for a numeric comparison. Use explicit `is not None` and `math.isfinite()` guards.

6. **Determinism:** The function must be deterministic. Identical input bundles and identical config must always produce identical output. No random tie-breaking, no timestamp-based selection, no mutable default arguments.

---

## Output Contract — `EntryPatternBundle`

### `EntryPattern` and `AdmittedEntryPattern` types

```python
from typing import Literal

# All valid entry_pattern values including the "none" sentinel
EntryPattern = Literal[
    "range_reclaim",
    "breakout",
    "break_and_hold",
    "shallow_pullback",
    "resume_reclaim",
    "continuation_breakout",
    "ema_reclaim",
    "base_reclaim",
    "early_reversal_break",
    "none",
]

# Only the 9 positive patterns — used as key type for candidate_pattern_scores_within_phase
# "none" is explicitly excluded because it can never be a key in the admitted-scores dict
AdmittedEntryPattern = Literal[
    "range_reclaim",
    "breakout",
    "break_and_hold",
    "shallow_pullback",
    "resume_reclaim",
    "continuation_breakout",
    "ema_reclaim",
    "base_reclaim",
    "early_reversal_break",
]
```

### `EntryPatternBundle`

```python
@dataclass(frozen=True)
class EntryPatternBundle:
    entry_pattern: EntryPattern
    entry_pattern_score: float  # 0.0..100.0; exactly 0.0 when entry_pattern == "none"
    candidate_pattern_scores_within_phase: dict[AdmittedEntryPattern, float]
    # Keys: only admitted patterns for the current market_phase (type excludes "none")
    # Values: the computed score for each admitted pattern
    # Empty dict {} when no pattern is admitted or market_phase is not a positive phase
```

**Semantic contract for `candidate_pattern_scores_within_phase`:**
- Contains only patterns that passed all admission conditions
- Non-admitted patterns have **no entry** in this dict — they are absent, not represented by `0.0`
- This cleanly separates "not evaluated / not admitted" from "evaluated and scored zero"
- When `entry_pattern = "none"`, this dict is `{}`

**Invariants (enforced):**
- `entry_pattern_score == 0.0` if and only if `entry_pattern == "none"`
- `entry_pattern != "none"` implies `candidate_pattern_scores_within_phase[entry_pattern] == entry_pattern_score`
- `entry_pattern` must be a value of `EntryPattern`
- No key in `candidate_pattern_scores_within_phase` may be `"none"`

---

## Config Specification

All pattern thresholds live under `cfg.pattern.<phase>.<pattern_name>.<field>`.

**Single source of defaults:** All defaults must be defined centrally once — in the config loader or a dedicated defaults structure. Pattern-resolution code must consume validated config values only. Fallback literals must not be embedded in pattern logic in `patterns.py`.

**Config block structure:**

```
cfg.pattern
  .pressure_build
    .range_reclaim
      .min_reclaim           (default: 45)
      .min_compression       (default: 55)
      .max_freshness         (default: 60)
    .breakout
      .min_expansion         (default: 35)
      .min_volume_shift      (default: 55)
      .max_freshness         (default: 65)
      .target_expansion      (default: 40)
    .break_and_hold
      .min_reclaim           (default: 55)
      .min_base_integrity    (default: 45)
      .min_expansion         (default: 30)
      .max_expansion         (default: 65)
  .trend_resume
    .shallow_pullback
      .min_pullback_quality  (default: 55)
      .min_trend             (default: 55)
      .max_freshness         (default: 65)
    .resume_reclaim
      .min_reclaim           (default: 50)
      .min_reaccel           (default: 50)
      .max_freshness         (default: 60)
    .continuation_breakout
      .min_trend             (default: 60)
      .min_reaccel           (default: 55)
      .max_expansion         (default: 70)
  .transition_reclaim
    .ema_reclaim
      .min_reclaim           (default: 45)
      .min_trend             (default: 40)
      .max_freshness         (default: 65)
    .base_reclaim
      .min_base_integrity    (default: 45)
      .min_reclaim           (default: 45)
    .early_reversal_break
      .min_reclaim           (default: 50)
      .min_volume_shift      (default: 50)
      .max_freshness         (default: 60)
```

**Config rules:**
- All fields above are required in the resolved config. Missing fields at load time raise a fast validation error.
- Partial nested overrides merge field-by-field with the spec defaults; unspecified nested fields fall back to defaults.
- Invalid threshold values raise a fast validation error at config load time — not silently at runtime. Examples: negative values for fields conceptually in `[0, 100]`; `min_expansion >= max_expansion` for `break_and_hold`; non-finite `target_expansion`.
- `target_expansion` must be in `[0, 100]`.
- `break_and_hold.min_expansion` must be strictly less than `break_and_hold.max_expansion`.

---

## Tests

The following test cases are required. All tests must be deterministic fixture-based unit tests (no live data, no external I/O, no storage access).

### Phase-gate tests

| # | Description | Expected |
|---|---|---|
| T-PG-1 | `market_phase = "none"` | `entry_pattern = "none"`, `score = 0.0`, `candidate_scores = {}` |
| T-PG-2 | Unrecognized phase string | `entry_pattern = "none"`, `score = 0.0`, `candidate_scores = {}` |

### Pattern admission tests — per pattern (9 × 2 = 18 tests)

For each of the 9 patterns, provide:
- **Positive test:** all admission conditions met with valid inputs; verify pattern name is returned and score > 0
- **Negative test:** exactly one admission condition violated (value one epsilon beyond threshold); verify pattern is not admitted (absent from `candidate_pattern_scores_within_phase`)

Patterns to cover: `range_reclaim`, `breakout`, `break_and_hold`, `shallow_pullback`, `resume_reclaim`, `continuation_breakout`, `ema_reclaim`, `base_reclaim`, `early_reversal_break`

### Boundary tests

| # | Description | Expected |
|---|---|---|
| T-BD-1 | Axis value exactly on admission threshold | Pattern admitted |
| T-BD-2 | Axis value one epsilon below `>=` threshold | Pattern not admitted |
| T-BD-3 | Axis value one epsilon above `<=` threshold | Pattern not admitted |

### Pattern selection tests

| # | Description | Expected |
|---|---|---|
| T-SEL-1 | All 3 patterns admitted for `pressure_build`; `range_reclaim` has highest score | `range_reclaim` selected; all 3 appear in `candidate_pattern_scores_within_phase` |
| T-SEL-2 | Only `breakout` admitted for `pressure_build` | `breakout` selected; `candidate_pattern_scores_within_phase` has exactly 1 key |
| T-SEL-3 | No pattern admitted for `trend_resume` | `entry_pattern = "none"`, `score = 0.0`, `candidate_scores = {}` |

### Tie-break tests — one per phase (3 tests)

| # | Description | Expected |
|---|---|---|
| T-TB-1 | `pressure_build`: `range_reclaim` and `break_and_hold` produce identical computed scores | `range_reclaim` wins |
| T-TB-2 | `trend_resume`: `resume_reclaim` and `shallow_pullback` produce identical computed scores | `resume_reclaim` wins |
| T-TB-3 | `transition_reclaim`: `base_reclaim` and `ema_reclaim` produce identical computed scores | `base_reclaim` wins |

### `compute_breakout_expansion_fit` helper tests

| # | Description | Expected |
|---|---|---|
| T-BEF-1 | `expansion = 40.0` (== `target_expansion`) | `fit = 100.0` |
| T-BEF-2 | `expansion = 10.0` | `fit = 70.0` |
| T-BEF-3 | `expansion = 0.0` | `fit = 60.0` |
| T-BEF-4 | `expansion = 90.0` | `fit = 50.0` |
| T-BEF-5 | `expansion = 145.0` (clamp boundary) | `fit = 0.0` |

### Missing / invalid input tests

| # | Description | Expected |
|---|---|---|
| T-INV-1 | Required admission-condition axis for `range_reclaim` is `None` | Pattern not admitted; absent from `candidate_pattern_scores_within_phase` |
| T-INV-2 | Required axis for `shallow_pullback` is `float('nan')` | Pattern not admitted |
| T-INV-3 | Required axis is `float('inf')` | Pattern not admitted |
| T-INV-4 | `volume_regime_shift = None` for `base_reclaim` (score-formula input) | Pattern not admitted |

### `candidate_pattern_scores_within_phase` semantic tests

| # | Description | Expected |
|---|---|---|
| T-CAND-1 | 2 of 3 patterns admitted for `transition_reclaim` | Dict has exactly 2 keys; non-admitted pattern is absent (no `0.0` entry) |
| T-CAND-2 | `market_phase = "none"` | Dict is `{}` |

### Determinism and phase isolation tests

| # | Description | Expected |
|---|---|---|
| T-DET-1 | Call `resolve_entry_pattern` twice with identical inputs and cfg | Identical `EntryPatternBundle` both times |
| T-ISO-1 | `market_phase = "trend_resume"`; axis values that would admit a `pressure_build` pattern | Only `trend_resume` patterns evaluated; no `pressure_build` pattern in output |

### Pipeline boundary tests

| # | Description | Expected |
|---|---|---|
| T-PB-1 | Verify `resolve_entry_pattern` signature has exactly the four declared parameters | No `state_bundle` or T10 field in signature |

---

## Docs to Update

Update the following files only if they already exist at the expected paths. If a file does not exist, do not create it in this ticket.

- **`docs/canonical/ARCHITECTURE.md`** — add `scanner/entry/` module description; note Layer-5 position and pure-computation contract (no IO, no storage, no state access)
- **`docs/canonical/DATA_MODEL.md`** — document `EntryPatternBundle` fields and invariants; document the downstream guardrail semantics (`early_ready + none → watchlist`, `confirmed_ready + none → late_monitor + CONFIRMED_PATTERN_UNRESOLVED`) as a cross-reference to T12; note `candidate_pattern_scores_within_phase` semantics (admitted-only dict, keyed by `AdmittedEntryPattern`)
- **`docs/canonical/GLOSSARY.md`** — add or verify entries for: `entry_pattern`, `entry_pattern_score`, `breakout_expansion_fit`, `candidate_pattern_scores_within_phase`, `EntryPattern`, `AdmittedEntryPattern`, and all 9 v2.1 pattern names
