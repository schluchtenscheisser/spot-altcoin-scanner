# Q1/Q2 Decision Note — Operational Tradeability and Stablecoin Exclusion

**Status:** Decision locked — ready for implementation ticket  
**Recommended repo path:** `docs/canonical/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md`  
**Date:** 2026-05-12  
**Resolves:** open_questions.md Q1 and Q2  
**Prerequisite for:** T30 Forward-Return Evaluation

---

## Background

Two related open questions have been deferred since early Shadow-Live operation:

**Q1:** `is_tradeable_candidate` does not account for `candidate_excluded` / universe exclusion. USDPUSDT demonstrated this live: `confirmed_candidates`, `is_tradeable_candidate=true`, `candidate_excluded=true` simultaneously.

**Q2:** Stablecoin/cash-proxy symbols are not hard-excluded before decision/bucket promotion. `USDPUSDT` and `TUSDUSDT` reached `confirmed_candidates` because no hard gate exists in the Universe-Classification-to-Decision path.

Both must be resolved before T30 consumes row-level diagnostics as authoritative tradeable labels.

---

## Decisions

### Q2: Stablecoin/cash-proxy exclusion layer

**Decision: Universe-Classification-Layer (Option B)**

Symbols with `universe_category in {stable_or_cash_proxy, fiat_proxy, wrapped_cash}` are hard-excluded before Decision/Bucket promotion.

Concrete behavior:
- `candidate_excluded = true` is set at Universe-Classification time for these categories
- Symbols remain fully visible in diagnostics with their `universe_category` and `candidate_excluded` flag
- Symbols are not promoted to `confirmed_candidates`, `early_candidates`, or `watchlist`
- Symbols may appear in a separate `candidate_excluded` count in report summaries
- **Bucket membership is not changed for already-promoted symbols** — the gate prevents future promotion, it does not retroactively reclassify

Explicitly out of scope for the first implementation:
- Eligibility-layer Defense-in-Depth (may be added later as a separate low-risk ticket)
- Changes to existing Override Map entries
- Changes to non-stablecoin `candidate_excluded` logic

Module ownership: Universe Classification layer (`scanner/universe/`), enforced before Decision Bucket assignment.

### Q1: Operational tradeability field

**Decision: New field `is_operational_trade_candidate` (Option B)**

`is_tradeable_candidate` retains its current semantics — execution- and bucket-scoped, unchanged. No existing consumer is broken.

New field:

```python
is_operational_trade_candidate = (
    is_tradeable_candidate == True
    AND candidate_excluded != True
)
```

Properties:
- Top-level field in `symbol_diagnostics.jsonl.gz` (consistent with `is_tradeable_candidate`)
- Boolean, not nullable — always emitted
- Schema version bump required (ir1.4 → ir1.5)
- T30 and all future operative consumers use `is_operational_trade_candidate` as the authoritative tradeable label
- Analysis scripts must not use `is_tradeable_candidate` alone as the operative filter after this schema version

### T_EL2 Rule 3 — no change

T_EL2 override Rule 3 remains:

```
candidate_excluded == True → entry_action_hint = monitor_only
```

Rule 3 stays on `candidate_excluded` directly, not on `is_operational_trade_candidate`. Reasons:
- The override sequence is semantically layered: Rule 3 = universe exclusion, Rule 4 = execution insufficiency. This distinction is preserved in `reason_codes` and is analytically valuable.
- Collapsing Rules 3 and 4 into a single `NOT is_operational_trade_candidate` check loses diagnostic granularity without any functional gain.
- The BULLISHUSDT/BULLUSDT edge case (Rule 2 firing before Rule 3) remains acceptable behavior — `avoid_chasing` is a stronger negative signal than `monitor_only`. Q1/Q2 resolution does not change this.

T_EL2 documentation must explicitly state: Rule 3 checks `candidate_excluded` (top-level field, ir1.3+) directly. It does not check `is_operational_trade_candidate`.

### Bucket behavior — unchanged, with explicit output semantics

Decision buckets (`confirmed_candidates`, `early_candidates`, `watchlist`, `late_monitor`, `discarded`) remain structurally unchanged. `candidate_excluded` symbols are prevented from being promoted into actionable output buckets by the upstream Q2 gate — not by retroactive state-machine reclassification.

Implementation distinction:

- **Final report / candidate lists:** `candidate_excluded=true` symbols must not appear in actionable candidate outputs such as `confirmed_candidates`, `early_candidates`, or `watchlist`.
- **Diagnostics:** symbols may remain visible with `candidate_excluded=true`, `universe_category`, exclusion reason, and any pre-exclusion context that is already available. Diagnostics must clearly emit `is_operational_trade_candidate=false`.

This means:
- Symbols excluded at Universe-Classification time never reach actionable output buckets.
- Symbols already present in older diagnostics with `candidate_excluded=true` and a non-discarded bucket are handled by `is_operational_trade_candidate=false` at the consumer level.
- No bucket schema changes, no state machine changes.

---

## Implementation scope

### What the implementation ticket must do

1. **Universe Classification layer**: enforce `candidate_excluded=true` for `universe_category in {stable_or_cash_proxy, fiat_proxy, wrapped_cash}` before Decision Bucket promotion. Symbols must not reach `confirmed_candidates`, `early_candidates`, or `watchlist`.

2. **New field `is_operational_trade_candidate`**: emit as top-level boolean in `symbol_diagnostics.jsonl.gz`. Formula: `is_tradeable_candidate == True AND candidate_excluded != True`.

3. **Schema version bump**: ir1.4 → ir1.5. Entry in `docs/SCHEMA_CHANGES.md`.

4. **Report summaries**: add operational tradeability counts alongside existing tradeability counts. Do not rename or silently reinterpret existing `is_tradeable_candidate`-based counts. New report fields should use an explicit `operational_*` naming pattern, for example `operational_trade_candidate_count`, `confirmed_operational_trade_candidate_count`, or the closest repo-consistent equivalents.

5. **T_EL2 documentation update**: add explicit note that Rule 3 checks `candidate_excluded` directly, not `is_operational_trade_candidate`.

5a. **T_EL2 segment validation**: verify that the `good_location_but_not_tradeable` segment remains correct after the Q2 gate. This segment already excludes `candidate_excluded == true`; stablecoin/cash-proxy symbols should no longer appear in actionable buckets, and this condition must continue to behave as intended.

6. **`open_questions.md` update**: mark Q1 and Q2 as resolved with references to this decision note and the implementation ticket.

7. **`feature_enhancements.md` update**: mark enhancement 6 (`is_operational_trade_candidate`) as resolved/implemented.

### What the implementation ticket must not do

- Change `is_tradeable_candidate` semantics or formula
- Change bucket membership rules or state machine logic
- Add Eligibility-layer stablecoin filter (separate future ticket if needed)
- Change T_EL2 override rule ordering or logic
- Change any non-stablecoin `candidate_excluded` handling
- Resolve Q3 or any other open question

---

## Consumer migration

After this implementation:

| Consumer | Before | After |
|---|---|---|
| T30 evaluation | must use ad-hoc filter `is_tradeable_candidate AND NOT candidate_excluded` | use `is_operational_trade_candidate` directly |
| Analysis scripts | same ad-hoc filter | same |
| T_EL2 Rule 3 | `candidate_excluded` check | unchanged |
| T_EL2 Rule 4 | `is_tradeable_candidate != True` check | unchanged |
| Report summaries | `is_tradeable_candidate`-based counts | add `is_operational_trade_candidate`-based counts alongside |

Scripts written against `ir1.4` or earlier that use `is_tradeable_candidate` alone remain functionally correct for symbols that were never stablecoin/cash-proxy candidates. For USDPUSDT-type symbols, they will produce different results after the Q2 gate is in place (symbols no longer promoted to actionable buckets).

---

## Repository placement

This decision note should be stored at:

```text
docs/canonical/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md
```

If `docs/canonical/decisions/` does not exist, create it as the canonical location for locked architecture decision notes. This file resolves `open_questions.md` Q1/Q2 and should be referenced from the Q1/Q2 implementation ticket, `open_questions.md`, and `feature_enhancements.md`.

## Open questions resolved by this decision

| Question | Resolution |
|---|---|
| Q1: `is_tradeable_candidate` vs `candidate_excluded` | Resolved: new field `is_operational_trade_candidate`; `is_tradeable_candidate` unchanged |
| Q2: Stablecoin/cash-proxy hard exclusion | Resolved: Universe-Classification-layer gate; Eligibility-layer deferred |

## Open questions not resolved by this decision

| Question | Status |
|---|---|
| Q3: `distance_to_range_high_pct_abs` formula | Remains open |
| Q6: `is_reduced_size_eligible` field rename | Remains open |
| All other open questions | Unchanged |

---

*Decision Note — Q1/Q2. Authors: Claude (adversarial review), ChatGPT (architecture). Final decision: Martin. 2026-05-12.*
