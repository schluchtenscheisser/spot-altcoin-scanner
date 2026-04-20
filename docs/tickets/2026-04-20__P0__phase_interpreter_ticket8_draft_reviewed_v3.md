# Title
[P0] Implement phase interpreter and typed phase-classification bundle (Ticket 8)

## Context / Source

This ticket implements **Ticket 8** from the Independence-Release consolidated concept: the **phase interpreter**.

**Gesamtkonzept reference:** Gesamtkonzept §2.2, §19 Ticket 8.

`depends_on: [6, 7]` — requires:
- Ticket 6 (`tier1 axes`)
- Ticket 7 (`tier2 simplified axes`)

The authoritative fachliche source set remains:

- the 7 uploaded v2.1 section files
- `independence_release_gesamtkonzept_final.md`

If current code, older repo-canonical docs, older ticket assumptions, or archived ticket follow-up notes conflict with that source set, the authoritative source set wins. Extend the ticket or ask rather than interpret.

### Important framing for this ticket

This ticket implements:

- the complete **Layer-3 phase interpreter**
- a typed in-memory `PhaseInterpretationBundle`
- deterministic classification into:
  - `pressure_build`
  - `trend_resume`
  - `transition_reclaim`
  - `none`
- deterministic phase confidence, runner-up, gap, blended-flag, phase scores, floor margins, and zero-score diagnostics

This ticket does **not** implement:

- Tier-1 axes (Ticket 6)
- Tier-2-Simplified axes (Ticket 7)
- invalidation / cycle logic
- freshness / state-machine logic
- entry logic
- ranking / decision buckets
- persistence of phase outputs
- direct OHLCV access
- raw feature access

### Critical authority / drift clarification

Earlier archived Ticket-6 / Ticket-7 `follow_ups` text informally mentioned:

> "Ticket 8: implement phase interpreter using FeatureBundle + Tier1AxisBundle + Tier2AxisBundle"

That wording is **non-authoritative** for the Ticket-8 public interface and must not override Abschnitt 3.

Ticket 8 consumes **Tier1AxisBundle + Tier2AxisBundle + cfg only**.

It does **not** consume `FeatureBundle`.

### Section-3 design reminder

Abschnitt 3 is unusually complete. Ticket 8 therefore does **not** reopen phase architecture. It operationalizes the already-defined phase logic, output fields, tie-break, and confidence rules into a codex-safe implementation ticket.

### Addendum / working-context checks

This ticket explicitly follows the addendum working-context leitplanken:

- **A.2 Schichtenarchitektur** — T8 remains strictly in Layer 3 and does not pull raw features, state, entry, ranking, or persistence into phase logic
- **A.5 Persistenz ist fachlicher Kern** — T8 produces run-local in-memory outputs only and does not create a persisted phase authority
- **A.6 Historie liefert Kontext, aber keinen Override** — T8 is intentionally stateless and history-free
- **Teil B Präzisierungs-Check** — no unresolved Part-B block is silently imported into T8

---

## Goal

After this ticket is completed:

- `scanner/phase/interpreter.py` computes the canonical phase interpretation from `Tier1AxisBundle` and `Tier2AxisBundle`
- `scanner/phase/models.py` contains `PhaseInterpretationBundle`
- phase interpretation consumes **only** typed axis bundles and `cfg`
- all three positive phases plus `none` are classified exactly as defined in Abschnitt 3
- reduced-resolution confidence capping is handled internally from axis-level `_reduced_resolution` flags
- the three semantically distinct `none` paths are explicitly represented in diagnostics:
  - minimum basis not met
  - hard floor failed
  - global confidence floor not met
- downstream Tickets 9 and 10 can consume a stable typed phase-layer output contract

---

## Scope

Allowed change surface:

- `scanner/phase/interpreter.py` (new)
- `scanner/phase/models.py` (new)
- `scanner/phase/__init__.py` if needed
- `scanner/config.py` or central config accessor — add `cfg.phase` defaults / merge / validation rules
- `tests/**` — add tests specified below
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/DATA_MODEL.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/GLOSSARY.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope

This ticket must not:

- consume `FeatureBundle`
- consume OHLCV bars, raw timestamps, `now`, repositories, cache, SQLite, Parquet, or storage layers of any kind
- compute or re-compute Tier-1 or Tier-2 axis values
- implement invalidation / cycle / state / entry / ranking logic
- introduce any persistence for phase outputs
- write SQLite / Parquet / file outputs
- introduce `data_resolution_class` as a required upstream public input
- use `freshness_distance_structural` as a hard-floor or weighted-score input
- manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

---

## Canonical References

Primary authority for this ticket:

- `independence_release_gesamtkonzept_final.md` — especially §2.2, §19 Ticket 8
- `v2_1_abschnitt_3_phase_interpreter_rev2.md` — **the phase rules in this ticket operationalize Abschnitt 3; Codex must not reconstruct missing logic from free interpretation**
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

- Ticket 6 provides canonical Tier-1 axes.
- Ticket 7 provides canonical Tier-2-Simplified axes.
- There is no canonical typed phase-layer output object yet.
- Downstream state/invalidation tickets would otherwise be forced to reconstruct phase logic ad hoc.

### After

- `scanner/phase/interpreter.py` provides the canonical Layer-3 phase interpreter
- `scanner/phase/models.py` defines the typed `PhaseInterpretationBundle`
- Ticket 8 consumes only `Tier1AxisBundle`, `Tier2AxisBundle`, and `cfg`
- Ticket 8 returns a deterministic typed in-memory `PhaseInterpretationBundle`
- the three positive phases plus `none` are assigned exactly under the canonical floor / score / tie-break rules
- missing-data, reduced-resolution, and `none` diagnostics are explicit and auditable

### Edge cases

- all three phases can yield `phase_score = 0`
- `market_phase = none` is a valid classification result, not an error and not a proxy for missing evaluation
- `runner_up` remains deterministic even in exact-score ties and all-zero cases
- a phase may have `phase_score = 0` because minimum basis is not met or because hard floors fail; these must be distinguished diagnostically
- a top phase may remain positive while `market_phase_confidence` is capped due to reduced resolution
- `freshness_distance_structural` may be present and passed through as diagnostics, but must never influence phase floors or weighted scores

### Backward compatibility impact

- Config surface grows under `cfg.phase`
- a new typed in-memory phase-layer contract is introduced for downstream tickets
- no storage schema changes are introduced
- no legacy runtime contract is reopened

---

## Module and model structure (authoritative)

### Modules

- `scanner/phase/interpreter.py`
- `scanner/phase/models.py`

### Public function

```python
def compute_phase_interpretation(
    tier1_bundle: Tier1AxisBundle,
    tier2_bundle: Tier2AxisBundle,
    cfg: Config,
) -> PhaseInterpretationBundle: ...
```

No separate `symbol` parameter.

No `FeatureBundle`, OHLCV input, raw timestamp, repository handle, or storage object is accepted.

### Input contract boundary

Ticket 8 consumes **only**:

- `Tier1AxisBundle`
- `Tier2AxisBundle`
- `cfg`

Ticket 8 must not access:

- raw features
- OHLCV bars directly
- repositories / cache / SQLite / Parquet
- raw timestamps / `now`
- storage layers of any kind

---

## Input validation contract (authoritative)

### Accepted public input types

The public function accepts exactly:

- `tier1_bundle: Tier1AxisBundle`
- `tier2_bundle: Tier2AxisBundle`
- `cfg: Config`

Any other public input type is invalid and raises `TypeError`.

There is no dict-based loose input mode and no implicit coercion from mapping-like objects.

### Bundle metadata consistency

The following fields must match exactly between `tier1_bundle` and `tier2_bundle`:

- `symbol`
- `daily_bar_id`
- `intraday_bar_id`
- `data_4h_available`

If any of these differ:
- raise `ValueError`
- the error message must name the inconsistent field

There is no silent reconciliation.

### Axis-value validity

For every consumed axis input:

- allowed forms:
  - finite float in `0..100`
  - `None` when the companion `*_not_evaluable` flag is `True`
- rejected:
  - `NaN`
  - `inf`
  - `-inf`
  - values outside `0..100`
  - `None` with `*_not_evaluable = False`

Invalid upstream axis inputs raise `ValueError` naming the offending field.

### Companion-field consistency

For every axis consumed from either bundle:

- `<axis>_not_evaluable = True` implies `<axis> is None`
- `<axis> is None` implies `<axis>_not_evaluable = True`
- `<axis>_effective_weight_ratio = None` iff `<axis>_not_evaluable = True`
- if `<axis>_not_evaluable = True`, then `<axis>_reduced_resolution` must be `False`

Violations are invalid upstream contract and raise `ValueError`.

### No hidden `data_resolution_class` input

`data_resolution_class` is **not** a required public input for Ticket 8.

Ticket 8 derives the winning-phase reduced-resolution decision internally from the axis-level `_reduced_resolution` flags and the actual weighted-score inputs used by that phase.

### Input-contract standard

> Erlaubte Input-Typen, Units, Koerzionsregeln und harte Rejection-Regeln sind vollständig spezifiziert. Mehrdeutige Inputs dürfen nicht stillschweigend umgedeutet werden.

---

## Output contract (authoritative)

```python
@dataclass
class PhaseInterpretationBundle:
    symbol: str
    daily_bar_id: int
    intraday_bar_id: int | None
    data_4h_available: bool

    market_phase: str
    market_phase_confidence: float
    market_phase_runner_up: str
    market_phase_gap: float
    market_phase_blended: bool

    phase_score_pressure_build: float
    phase_score_trend_resume: float
    phase_score_transition_reclaim: float

    phase_floor_margin_pressure_build: float | None
    phase_floor_margin_trend_resume: float | None
    phase_floor_margin_transition_reclaim: float | None

    phase_floor_failed_pressure_build: bool
    phase_floor_failed_trend_resume: bool
    phase_floor_failed_transition_reclaim: bool

    phase_eval_status_pressure_build: str
    phase_eval_status_trend_resume: str
    phase_eval_status_transition_reclaim: str

    freshness_distance_structural: float | None
    freshness_distance_structural_not_evaluable: bool
    freshness_distance_structural_reduced_resolution: bool
```

### Closed enums and semantics

`market_phase` is exactly one of:

- `"pressure_build"`
- `"trend_resume"`
- `"transition_reclaim"`
- `"none"`

`market_phase_runner_up` is exactly one of the **positive phase names**:

- `"pressure_build"`
- `"trend_resume"`
- `"transition_reclaim"`

It is **not nullable**.

It is always populated deterministically from the ranked positive phases using the same tie-break rules as the top phase, even in exact-score ties and all-zero cases.

`phase_eval_status_*` is exactly one of:

- `"score_computed"`
- `"minimum_basis_not_met"`
- `"hard_floor_failed"`

Interpretation:
- `"score_computed"` means the phase passed minimum-basis and hard-floor admissibility and therefore received a weighted score
- `"minimum_basis_not_met"` means the phase was not admissible because its required Tier-1 evaluability basis was missing
- `"hard_floor_failed"` means the phase had enough Tier-1 basis to be evaluated, but one or more hard floors failed or phase-local weighted-score admissibility failed

### Nullability semantics

- `phase_floor_margin_* = None` when either:
  - the phase failed at the minimum-basis gate before hard-floor evaluation, or
  - at least one required hard-floor component is unavailable and the floor margin is therefore not meaningfully computable
- when all hard-floor components are evaluable, `phase_floor_margin_*` is a finite float and may be negative
- `freshness_distance_structural` passthrough fields mirror Ticket-6 values/flags exactly and must not be reinterpreted
- `freshness_distance_structural` passthrough fields are an explicit ticket-level diagnostic extension beyond Abschnitt 3 minimum outputs
- `phase_eval_status_*` fields are an explicit ticket-level diagnostic extension beyond Abschnitt 3 minimum outputs

### Meaning of `none`

`market_phase = "none"` is a valid deterministic classification result.

It does **not** mean:
- runtime error
- parser failure
- upstream bundle invalidity
- `not_evaluable` for the whole phase layer

It means that under the authoritative phase rules, no positive phase assignment was granted for this run.

---

## Phase logic (authoritative)

### General rules

#### General rule A — two-stage evaluation per phase
Each positive phase is evaluated in exactly two steps:

1. minimum-basis / hard-floor admissibility
2. weighted score if admissible

If the phase is not admissible:
- `phase_score_* = 0`

#### General rule B — no imputation
If a hard-floor input is `None` or `*_not_evaluable = True`:
- the corresponding hard floor is not met
- there is no imputation

#### General rule C — Tier-1 precedence
Tier-2-Simplified axes may complement a phase score but may never carry a phase alone.

#### General rule D — `freshness_distance_structural` exclusion
`freshness_distance_structural` is never used:
- as a minimum-basis input
- as a hard-floor input
- as a weighted-score component

Its effect belongs exclusively to later state/freshness logic.

---

## Minimum-basis gate (authoritative)

A positive phase may only be evaluated when its minimum Tier-1 basis is available.

### `pressure_build`
Requires evaluable:
- `compression_strength`
- `volume_regime_shift`

### `trend_resume`
Requires evaluable:
- `trend_strength`
- `reclaim_progress`

### `transition_reclaim`
Requires evaluable:
- `reclaim_progress`
- and at least one of:
  - `volume_regime_shift`
  - `trend_strength`

If the minimum basis for a phase is not met:

- `phase_score_* = 0`
- `phase_floor_failed_* = True`
- `phase_floor_margin_* = None`
- `phase_eval_status_* = "minimum_basis_not_met"`

This is diagnostically distinct from hard-floor failure.

---

## Phase: `pressure_build`

### Hard floors
All must hold:

- `compression_strength >= cfg.phase.pressure_build.floor_compression`
- `volume_regime_shift >= cfg.phase.pressure_build.floor_volume_shift`
- `expansion_progress_structural <= cfg.phase.pressure_build.max_expansion`

### Default values
- `floor_compression = 60`
- `floor_volume_shift = 50`
- `max_expansion = 50`

### Floor margin
When all hard-floor components are evaluable:
- `margin_compression = compression_strength - floor_compression`
- `margin_volume_shift = volume_regime_shift - floor_volume_shift`
- `margin_expansion = max_expansion - expansion_progress_structural`
- `phase_floor_margin_pressure_build = min(margin_compression, margin_volume_shift, margin_expansion)`

If any required hard-floor component is unavailable:
- `phase_floor_margin_pressure_build = None`

### Weighted score
If admissible:

- `0.40` `compression_strength`
- `0.20` `base_integrity_simplified`
- `0.20` `volume_regime_shift`
- `0.20` `(100 - expansion_progress_structural)`

### Missing-data rule
If any of:
- `compression_strength`
- `volume_regime_shift`
- `expansion_progress_structural`

is unavailable:
- hard floors fail
- `phase_score_pressure_build = 0`
- `phase_floor_failed_pressure_build = True`
- `phase_floor_margin_pressure_build = None`
- `phase_eval_status_pressure_build = "hard_floor_failed"`

`base_integrity_simplified` may be missing; then its score weight is removed and the remaining weights are re-normalized, **phase-locally**, as long as the effective phase-level weight ratio remains `>= cfg.phase.min_effective_weight_ratio`.

---

## Phase: `trend_resume`

### Hard floors
All must hold:

- `trend_strength >= cfg.phase.trend_resume.floor_trend`
- `reclaim_progress >= cfg.phase.trend_resume.floor_reclaim`
- `expansion_progress_structural <= cfg.phase.trend_resume.max_expansion`

### Default values
- `floor_trend = 55`
- `floor_reclaim = 45`
- `max_expansion = 65`

### Floor margin
When all hard-floor components are evaluable:
- `margin_trend = trend_strength - floor_trend`
- `margin_reclaim = reclaim_progress - floor_reclaim`
- `margin_expansion = max_expansion - expansion_progress_structural`
- `phase_floor_margin_trend_resume = min(margin_trend, margin_reclaim, margin_expansion)`

If any required hard-floor component is unavailable:
- `phase_floor_margin_trend_resume = None`

### Weighted score
If admissible:

- `0.35` `trend_strength`
- `0.25` `pullback_quality_simplified`
- `0.20` `reacceleration_strength_simplified`
- `0.20` `reclaim_progress`

### Missing-data rule
If any of:
- `trend_strength`
- `reclaim_progress`
- `expansion_progress_structural`

is unavailable:
- hard floors fail
- `phase_score_trend_resume = 0`
- `phase_floor_failed_trend_resume = True`
- `phase_floor_margin_trend_resume = None`
- `phase_eval_status_trend_resume = "hard_floor_failed"`

`pullback_quality_simplified` and `reacceleration_strength_simplified` may be missing; their score weights are removed and the remaining weights are re-normalized, **phase-locally**, as long as the effective phase-level weight ratio remains `>= cfg.phase.min_effective_weight_ratio`.

---

## Phase: `transition_reclaim`

### Hard floors
All must hold:

- `reclaim_progress >= cfg.phase.transition_reclaim.floor_reclaim`
- `volume_regime_shift >= cfg.phase.transition_reclaim.floor_volume_shift`
- `expansion_progress_structural <= cfg.phase.transition_reclaim.max_expansion`

### Default values
- `floor_reclaim = 45`
- `floor_volume_shift = 45`
- `max_expansion = 55`

### Floor margin
When all hard-floor components are evaluable:
- `margin_reclaim = reclaim_progress - floor_reclaim`
- `margin_volume_shift = volume_regime_shift - floor_volume_shift`
- `margin_expansion = max_expansion - expansion_progress_structural`
- `phase_floor_margin_transition_reclaim = min(margin_reclaim, margin_volume_shift, margin_expansion)`

If any required hard-floor component is unavailable:
- `phase_floor_margin_transition_reclaim = None`

### Weighted score
If admissible:

- `0.40` `reclaim_progress`
- `0.20` `base_integrity_simplified`
- `0.20` `volume_regime_shift`
- `0.20` `(100 - expansion_progress_structural)`

### Missing-data rule
If any of:
- `reclaim_progress`
- `volume_regime_shift`
- `expansion_progress_structural`

is unavailable:
- hard floors fail
- `phase_score_transition_reclaim = 0`
- `phase_floor_failed_transition_reclaim = True`
- `phase_floor_margin_transition_reclaim = None`
- `phase_eval_status_transition_reclaim = "hard_floor_failed"`

`base_integrity_simplified` may be missing; then its score weight is removed and the remaining weights are re-normalized, **phase-locally**, as long as the effective phase-level weight ratio remains `>= cfg.phase.min_effective_weight_ratio`.

---

## Phase-local effective-weight rule (authoritative)

`cfg.phase.min_effective_weight_ratio` is the minimum allowed surviving weight mass for a phase’s **weighted score inputs only**.

This rule is evaluated:

- separately for each phase
- before re-normalization
- using only that phase’s originally defined weighted-score components

Hard-floor inputs are never rescued by dropout.

Default:
- `min_effective_weight_ratio = 0.60`

If the surviving weight mass for a phase’s weighted-score components falls below this threshold:

- `phase_score_* = 0`
- `phase_floor_failed_* = True`
- `phase_eval_status_* = "hard_floor_failed"`

This is treated as score inadmissibility within the phase, not as minimum-basis failure.

---

## Reduced-resolution rule (authoritative)

Ticket 8 does not require a separate `data_resolution_class` public input.

Instead, it derives reduced-resolution status internally.

### Rule for winning phase
A winning phase is classified as `reduced_resolution` if at least one of the axis inputs that **actually contributed to its weighted score** has `<axis>_reduced_resolution = True`.

Floor-only inputs that are not part of the weighted score do **not** trigger the reduced-resolution confidence cap on their own.

### Confidence cap
If the winning phase is reduced-resolution:

- `market_phase_confidence = min(top_score, cfg.phase.reduced_resolution_confidence_cap)`

Default:
- `reduced_resolution_confidence_cap = 75`

### Ordering note
The **global confidence floor** is evaluated against the uncapped `top_score`, exactly as in Abschnitt 3.

The reduced-resolution cap may lower the reported confidence, but it does not retroactively turn a positive phase into `none`.

---

## Top phase, runner-up, gap, blended flag, and `none`

### Candidate scores
After per-phase evaluation, the following scores exist:

- `phase_score_pressure_build`
- `phase_score_trend_resume`
- `phase_score_transition_reclaim`

All are in `0..100`.

### Top phase
- `top_phase = argmax(phase_scores)`
- `top_score = max(phase_scores)`

### Runner-up
- `runner_up_phase = second-ranked positive phase`
- `runner_up_score = second-ranked score`

### Gap
- `market_phase_gap = top_score - runner_up_score`

### Global confidence floor
If:
- `top_score < cfg.phase.global_confidence_floor`

then:
- `market_phase = "none"`
- `market_phase_confidence = top_score`
- `market_phase_runner_up = runner_up_phase`
- `market_phase_blended = False`

Default:
- `global_confidence_floor = 55`

### Blended flag
If:
- `market_phase != "none"`
- and `market_phase_gap < cfg.phase.phase_gap_floor`

then:
- `market_phase_blended = True`

otherwise:
- `market_phase_blended = False`

Default:
- `phase_gap_floor = 8`

### Tie-break
If multiple phases have exactly the same `phase_score`:

1. higher `phase_floor_margin` wins
2. if still tied, fixed order:
   - `pressure_build`
   - `trend_resume`
   - `transition_reclaim`

This tie-break applies deterministically even when tied scores are `0`.

---

## Three semantically distinct `none` paths (authoritative)

Ticket 8 must preserve these three distinct paths:

### Path 1 — Minimum basis not met
A phase cannot even enter meaningful floor evaluation because the required Tier-1 evaluability basis is missing.

Per-phase result:
- `phase_score_* = 0`
- `phase_floor_failed_* = True`
- `phase_floor_margin_* = None`
- `phase_eval_status_* = "minimum_basis_not_met"`

### Path 2 — Hard floors failed
A phase had enough minimum basis to be evaluated, but at least one hard floor failed (including phase-local weighted-score admissibility falling below minimum effective weight ratio).

Per-phase result:
- `phase_score_* = 0`
- `phase_floor_failed_* = True`
- `phase_floor_margin_*` is `None` when a required hard-floor component is unavailable
- when the phase is inadmissible because the phase-local effective-weight ratio falls below the threshold (not because a hard-floor component is missing), `phase_floor_margin_*` is the computed finite floor margin if all hard-floor components are evaluable, and `None` otherwise
- when all hard-floor components are evaluable, `phase_floor_margin_*` is a computed finite value and may be negative
- `phase_eval_status_* = "hard_floor_failed"`

### Path 3 — Global confidence floor not met
At least one phase received a computed positive score, but:

- `top_score < cfg.phase.global_confidence_floor`

Result:
- `market_phase = "none"`
- phase scores remain preserved in output
- `market_phase_gap` remains the arithmetic difference `top_score - runner_up_score` as computed; it is not set to `0`
- per-phase `phase_eval_status_*` values remain whatever their own phase evaluation produced
- this path is distinct from Paths 1 and 2

---

## Config contract

All new config keys live under `cfg.phase`.

### Merge semantics
> Partial overrides in `cfg.phase` are merged field-by-field with central defaults; missing sub-keys are not treated as invalid. Invalid values (wrong type, out of range) produce a clear `ValueError` that includes the key name and the invalid value.

### Numeric robustness
> Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid for Ticket-8 axis inputs and config values. They must not be silently coerced to 0, false, or any default, and they must not remain in numeric-looking outputs.

### Determinism
> At identical `Tier1AxisBundle`, identical `Tier2AxisBundle`, and identical config, all phase outputs, tie-break outcomes, diagnostics, and flags are identical.

### Nullability
> `None` in axis inputs means "not evaluable" only when the companion upstream contract says so. It must not be implicitly coerced to 0 or false.

### Defaults

#### Root
| Key | Default | Type | Validation |
|---|---|---|---|
| `min_effective_weight_ratio` | `0.60` | number | `> 0`, `<= 1` |
| `global_confidence_floor` | `55` | number | `0..100` |
| `reduced_resolution_confidence_cap` | `75` | number | `0..100` |
| `phase_gap_floor` | `8` | number | `>= 0`, `<= 100` |

#### `cfg.phase.pressure_build`
| Key | Default | Type | Validation |
|---|---|---|---|
| `floor_compression` | `60` | number | `0..100` |
| `floor_volume_shift` | `50` | number | `0..100` |
| `max_expansion` | `50` | number | `0..100` |

#### `cfg.phase.trend_resume`
| Key | Default | Type | Validation |
|---|---|---|---|
| `floor_trend` | `55` | number | `0..100` |
| `floor_reclaim` | `45` | number | `0..100` |
| `max_expansion` | `65` | number | `0..100` |

#### `cfg.phase.transition_reclaim`
| Key | Default | Type | Validation |
|---|---|---|---|
| `floor_reclaim` | `45` | number | `0..100` |
| `floor_volume_shift` | `45` | number | `0..100` |
| `max_expansion` | `55` | number | `0..100` |

Missing keys fall back to these defaults. Invalid values raise `ValueError` naming the key and invalid value.

---

## Canonical docs to update

- `docs/canonical/ARCHITECTURE.md` — add `scanner/phase/` role and `PhaseInterpretationBundle`
- `docs/canonical/DATA_MODEL.md` — add `PhaseInterpretationBundle` contract and field semantics
- `docs/canonical/RUNTIME_AND_OPERATIONS.md` — document phase-interpreter determinism, reduced-resolution cap, and `none` semantics
- `docs/canonical/GLOSSARY.md` — add phase names, `market_phase_blended`, `runner_up`, and the three `none` paths
- `docs/canonical/VERIFICATION_FOR_AI.md` — add phase rules, defaults, tie-break, diagnostics, and explicit `freshness_distance_structural` exclusion

---

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Authority precedence:** If older repo-canonical docs, archived tickets, or existing code differ from Abschnitt 3 / Gesamtkonzept, the authoritative source set wins.
- **Docs in same PR:** Update all listed canonical docs in the same PR as the code changes.
- **Docs first or alongside code:** Do not leave a merged PR where code changes exist without the corresponding canonical Ticket-8 contract updates.
- **No raw features:** Ticket 8 must not consume `FeatureBundle`.
- **No hidden upstream dependency:** Ticket 8 must not require a separate upstream `data_resolution_class` producer.
- **Strict layer boundary:** No invalidation, cycle, freshness-state, entry, ranking, persistence, or execution logic may leak into this ticket.
- **Freshness exclusion:** `freshness_distance_structural` must never influence minimum basis, hard floors, or weighted scores.
- **Phase-local dropout only:** Weight dropout applies only to optional weighted-score inputs within the affected phase.
- **Hard floors are never rescued:** If a hard-floor input is missing or invalid, that phase is not admissible.
- **Three `none` paths must remain distinguishable:** minimum basis not met, hard floor failed, global confidence floor not met.
- **Deterministic runner-up:** `market_phase_runner_up` must remain deterministic and non-nullable.
- **No bool()-coercion of nullable values:** `None` remains semantically distinct from `0` and `False`.
- **No silent bundle reconciliation:** mismatched upstream bundle metadata is a hard error.
- **No manual edits to `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`.**
- **One ticket = one PR.**

---

## Acceptance Criteria (deterministic)

1. `scanner/phase/interpreter.py` and `scanner/phase/models.py` exist.
2. `compute_phase_interpretation(tier1_bundle, tier2_bundle, cfg)` is the sole public entry point.
3. Ticket 8 consumes only `Tier1AxisBundle`, `Tier2AxisBundle`, and `cfg`.
4. Ticket 8 does not consume `FeatureBundle`, OHLCV, raw timestamps, repositories, or storage.
5. `PhaseInterpretationBundle` exists with exactly the fields defined in this ticket.
6. Public input type mismatches raise `TypeError`.
7. Bundle metadata mismatches (`symbol`, `daily_bar_id`, `intraday_bar_id`, `data_4h_available`) raise `ValueError`.
8. Invalid upstream axis values (`NaN`, `inf`, `-inf`, out-of-range values, inconsistent nullability/flags) raise `ValueError`.
9. `pressure_build` floors, margins, score weights, and missing-data rules match this ticket exactly.
10. `trend_resume` floors, margins, score weights, and missing-data rules match this ticket exactly.
11. `transition_reclaim` floors, margins, score weights, and missing-data rules match this ticket exactly.
12. Minimum-basis admissibility is enforced before per-phase hard-floor / weighted-score logic.
13. `phase_eval_status_*` and `phase_floor_failed_*` distinguish minimum-basis failure from hard-floor failure exactly as defined here.
14. `freshness_distance_structural` is passed through unchanged from `Tier1AxisBundle` and is not used in phase scoring.
15. Reduced-resolution confidence capping is derived internally from the weighted-score inputs actually used by the winning phase.
16. Floor-only reduced-resolution inputs do not trigger the reduced-resolution cap on their own.
17. `market_phase_runner_up` is deterministic and non-nullable, including exact-score ties and all-zero cases.
18. `market_phase_blended` obeys the `phase_gap_floor` rule and is `False` whenever `market_phase = none`.
19. `market_phase = none` is produced correctly for:
    - all-phases floor failure,
    - insufficient minimum basis,
    - top-score below global confidence floor.
20. Config defaults, merge semantics, validation, and invalid-value failures behave exactly as defined here.
21. Canonical docs listed in this ticket are updated in the same PR.
22. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually edited.
23. The ticket is archived in the same PR according to workflow.

---

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ covered — all `cfg.phase` keys have explicit defaults; missing nested keys fall back without error
- **Config Invalid Value Handling:** ✅ covered — invalid type / non-finite / out-of-range values raise `ValueError`
- **Nullability / kein bool()-Coercion:** ✅ covered — nullable axis inputs and passthrough freshness fields remain semantically distinct from `0` / `False`
- **Not-evaluated vs failed getrennt:** ✅ covered — minimum-basis failure, hard-floor failure, and global confidence-floor `none` are distinct
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ N/A — no write pipeline introduced
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A
- **Deterministische Sortierung/Tie-breaker:** ✅ covered — explicit tie-break for top phase and deterministic runner-up

---

## Tests (required if logic changes)

### Category A — Public API / input contract / validation

#### A1 — Valid typed inputs
- Fixture: valid `Tier1AxisBundle`, valid `Tier2AxisBundle`, valid `cfg.phase`
- Expected: function succeeds

#### A2 — Invalid public input type
- Fixture: pass a plain dict or other non-bundle object as `tier1_bundle`
- Expected: `TypeError`

#### A3 — Mismatched symbol
- Fixture: `tier1_bundle.symbol != tier2_bundle.symbol`
- Expected: `ValueError` naming `symbol`

#### A4 — Mismatched bar identity
- Fixture: matching symbol but differing `daily_bar_id` or `intraday_bar_id`
- Expected: `ValueError` naming the mismatched field

#### A5 — Non-finite axis input
- Fixture: `trend_strength = NaN`
- Expected: `ValueError` naming `trend_strength`

#### A6 — Inconsistent upstream nullability
- Fixture: `pullback_quality_simplified = None` but `pullback_quality_simplified_not_evaluable = False`
- Expected: `ValueError`

---

### Category B — Minimum-basis gate

#### B1 — `pressure_build` minimum basis not met
- Fixture: `compression_strength = None`, `volume_regime_shift` evaluable
- Expected:
  - `phase_score_pressure_build = 0`
  - `phase_floor_failed_pressure_build = True`
  - `phase_floor_margin_pressure_build = None`
  - `phase_eval_status_pressure_build = "minimum_basis_not_met"`

#### B2 — `trend_resume` minimum basis not met
- Fixture: `trend_strength = None`, `reclaim_progress` evaluable
- Expected: analogous minimum-basis failure for `trend_resume`

#### B3 — `transition_reclaim` minimum basis not met
- Fixture: `reclaim_progress` evaluable, but both `volume_regime_shift` and `trend_strength` are `None`
- Expected: analogous minimum-basis failure for `transition_reclaim`

---

### Category C — Hard-floor failure vs minimum-basis failure

#### C1 — Hard floor failed, basis present
- Fixture: `compression_strength = 58`, `volume_regime_shift = 70`, `expansion_progress_structural = 20`
- Expected:
  - `phase_score_pressure_build = 0`
  - `phase_floor_failed_pressure_build = True`
  - `phase_floor_margin_pressure_build < 0`
  - `phase_eval_status_pressure_build = "hard_floor_failed"`

#### C2 — Hard-floor component unavailable
- Fixture: minimum basis met, but `expansion_progress_structural = None`
- Expected:
  - `phase_score_* = 0` for affected phase
  - `phase_floor_failed_* = True`
  - `phase_floor_margin_* = None`
  - `phase_eval_status_* = "hard_floor_failed"`

#### C3 — All floors fail for all phases
- Fixture: all relevant basis present, all phase floors violated
- Expected:
  - all three `phase_score_* = 0`
  - `market_phase = "none"`
  - `market_phase_gap = 0`
  - deterministic `market_phase_runner_up`

---

### Category D — Weighted-score goldens

For each positive phase, add at least one manually precomputed golden fixture where all required inputs are finite and all optional weighted-score inputs are present.

#### D1 — `pressure_build` full golden
- Expected:
  - positive `phase_score_pressure_build`
  - `phase_eval_status_pressure_build = "score_computed"`

#### D2 — `trend_resume` full golden
- Expected:
  - positive `phase_score_trend_resume`
  - `phase_eval_status_trend_resume = "score_computed"`

#### D3 — `transition_reclaim` full golden
- Expected:
  - positive `phase_score_transition_reclaim`
  - `phase_eval_status_transition_reclaim = "score_computed"`

All expected values must be manually precomputed, not copied from implementation.

---

### Category E — Phase-local dropout

#### E1 — `pressure_build` optional Tier-2 dropout
- Fixture: `base_integrity_simplified = None`, other weighted-score inputs present
- Expected:
  - phase score still computed
  - phase-local re-normalization used
  - zero reason = `"score_computed"`

#### E2 — `trend_resume` one optional Tier-2 input missing
- Fixture: `pullback_quality_simplified = None`, `reacceleration_strength_simplified` present
- Expected: score still computed with phase-local re-normalization

#### E3 — `trend_resume` optional weighted mass below floor
- Fixture:
  - `trend_strength = 70`
  - `reclaim_progress = 60`
  - `expansion_progress_structural = 40`
  - `pullback_quality_simplified = None`
  - `reacceleration_strength_simplified = None`
- Expected:
  - `phase_score_trend_resume = 0`
  - `phase_floor_failed_trend_resume = True`
  - `phase_floor_margin_trend_resume = 15`
    - computed as `min(70 - 55, 60 - 45, 65 - 40) = min(15, 15, 25) = 15`
  - `phase_eval_status_trend_resume = "hard_floor_failed"`

---

### Category F — Reduced resolution

#### F1 — Winning phase full resolution
- Fixture: winning phase uses only weighted-score inputs with `_reduced_resolution = False`
- Expected: no confidence cap

#### F2 — Winning phase reduced resolution through weighted-score input
- Fixture: winning phase uses at least one weighted-score input with `_reduced_resolution = True`
- Expected: `market_phase_confidence = min(top_score, reduced_resolution_confidence_cap)`

#### F3 — Floor-only reduced-resolution input
- Fixture: a floor-only input has `_reduced_resolution = True`, but all weighted-score inputs used by the winner have `_reduced_resolution = False`
- Expected: no reduced-resolution cap triggered by that floor-only input alone

---

### Category G — Global confidence floor and blended flag

#### G1 — Top score below global confidence floor
- Fixture: `top_score = 54`, `runner_up_score = 30`
- Expected:
  - `market_phase = "none"`
  - `market_phase_confidence = 54`
  - `market_phase_gap = 24`
  - `market_phase_blended = False`

#### G2 — Gap below phase-gap floor
- Fixture: top score = `72`, runner-up = `67`
- Expected:
  - positive `market_phase`
  - `market_phase_gap = 5`
  - `market_phase_blended = True`

---

### Category H — Tie-break and deterministic runner-up

#### H1 — Exact score tie, different floor margins
- Fixture: two phases with same score, different floor margins
- Expected: higher floor margin wins

#### H2 — Exact score tie, exact floor-margin tie
- Fixture: tied score and tied floor margin
- Expected: fixed priority order:
  - `pressure_build`
  - `trend_resume`
  - `transition_reclaim`

#### H3 — All-zero case
- Fixture: all three phase scores = `0`
- Expected:
  - `market_phase = "none"`
  - deterministic non-nullable `market_phase_runner_up`

---

### Category I — Freshness exclusion and null passthrough

#### I1 — Freshness passthrough, no phase influence
- Fixture: two otherwise identical inputs differing only in `freshness_distance_structural`
- Expected:
  - identical phase scores
  - identical `market_phase`
  - identical `market_phase_confidence`
  - passthrough freshness fields differ accordingly

#### I2 — `null` stays `null`
- Fixture: `freshness_distance_structural = None`, `freshness_distance_structural_not_evaluable = True`
- Expected:
  - output `freshness_distance_structural is None`
  - no coercion to `0` or `False`

---

### Category J — Output contract / determinism

#### J1 — Output field presence
- `compute_phase_interpretation(...)` returns `PhaseInterpretationBundle`
- all required fields present
- no storage access occurs during execution

#### J2 — Determinism
- identical `tier1_bundle` + identical `tier2_bundle` + identical `cfg`
- Expected: identical `PhaseInterpretationBundle`

---

### Category K — Config semantics

#### K1 — Missing root key falls back to defaults
- Fixture: config omits `cfg.phase.global_confidence_floor`
- Expected: default `55` is used

#### K2 — Partial nested override merges with defaults
- Fixture: config overrides only `cfg.phase.pressure_build.floor_compression`
- Expected: overridden compression floor used, other `pressure_build` keys retain canonical defaults

#### K3 — Invalid nested type
- Fixture: `cfg.phase.trend_resume` is a non-mapping value
- Expected: `ValueError` naming `cfg.phase.trend_resume`

#### K4 — Invalid numeric config value
- Fixture: `cfg.phase.phase_gap_floor = float("nan")`
- Expected: `ValueError` naming `cfg.phase.phase_gap_floor`

---

## Constraints / Invariants (must not change)

- [ ] Ticket 8 consumes only `Tier1AxisBundle`, `Tier2AxisBundle`, and `cfg`
- [ ] Ticket 8 does not consume `FeatureBundle`
- [ ] Ticket 8 does not access OHLCV or storage
- [ ] Ticket 8 implements exactly three positive phases plus `none`
- [ ] `freshness_distance_structural` is excluded from phase floors and phase weighted scores
- [ ] `market_phase_runner_up` remains deterministic and non-nullable
- [ ] `none` remains a valid classification result, not an error state
- [ ] minimum-basis failure remains diagnostically distinct from hard-floor failure
- [ ] reduced-resolution capping is derived internally from weighted-score inputs of the winning phase
- [ ] no invalidation / cycle / state / entry / ranking logic is introduced
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

## Preflight self-check

- [x] Current authoritative reference set identified
- [x] Drift collision with older T6/T7 `follow_ups` resolved explicitly
- [x] Missing vs invalid semantics made explicit
- [x] `null` vs `false` semantics made explicit
- [x] `not_evaluable` vs hard failure vs global-confidence `none` separated
- [x] Config merge vs invalid-value semantics made explicit
- [x] Tie-break and deterministic runner-up specified
- [x] Concrete tests added for config defaults, invalid values, null passthrough, determinism, and invalid public input type

---

## Metadata

```yaml
created_utc: "2026-04-20T00:00:00Z"
priority: P0
type: feature
owner: codex
depends_on: [6, 7]
gesamtkonzept_ref: "§19 Ticket 8"
related_issues: []
follow_ups:
  - "Ticket 9: implement invalidation + cycle logic using PhaseInterpretationBundle and axis bundles"
  - "Ticket 10: implement freshness + state machine using PhaseInterpretationBundle and axis bundles"
```
