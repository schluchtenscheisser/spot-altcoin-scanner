> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P1] Add late-entry guards for ENTER decisions using target-1 hard stop and effective RR from current price

## Context / Source (optional)
- The latest relevant run introduced an `ENTER` candidate that appears structurally valid at the original setup trigger but is no longer operationally valid at the current market price.
- Concrete motivating case: `TRUMPUSDT` was emitted as `ENTER` even though:
  - `entry_state = chased`
  - `current_price_usdt` was materially above `entry_price_usdt`
  - `current_price_usdt` was already above `target_2_price`
  - `current_price_usdt` was close to `target_3_price`
- This exposed a decision-layer gap:
  - current ENTER eligibility is still effectively based on setup readiness, tradeability, risk-acceptable status, and setup score
  - but not on whether the trade still has acceptable reward-to-risk from the **current price**
- Prior discussion concluded that the fix should **not** use a broad “`entry_state = chased` => no ENTER” rule and should **not** use an arbitrary chase-distance cap such as 1–3%.
- Instead, the agreed model is:
  1. hard block if price has already passed `target_1_price`
  2. otherwise evaluate an **effective RR** from current price to the canonical target/stop ladder
- This ticket is limited to decision-layer late-entry gating. It must not change existing setup scoring, tradeability, execution, stop derivation, or risk model semantics.

Relevant artifacts:
- latest run/report showing the invalid ENTER case
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `scanner/pipeline/decision.py`

## Goal
Prevent stale/chased setups from being emitted as `ENTER` when the live market price has already consumed too much of the planned reward path.

The intended behavior is:
- `NO_TRADE` when the current price has already reached or exceeded `target_1_price`
- otherwise, evaluate whether the trade still has acceptable reward-to-risk **from the current price**
- if current-price effective RR is insufficient, downgrade from potential `ENTER` to `WAIT`
- preserve valid near-trigger ENTERs that still have sufficient effective RR

## Scope
Allowed modules/files to change:
- `scanner/pipeline/decision.py`
- `config/config.yml`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/VERIFICATION_FOR_AI.md` if decision verification behavior changes

Optional but allowed if needed for verification only:
- tests for decision-layer late-entry gating
- fixture/golden verification files used by the current test suite

## Out of Scope
- Any change to setup scoring formulas
- Any change to execution gate logic or thresholds
- Any change to tradeability classification
- Any change to stop derivation, ATR fallback, invalidation anchor logic, or `risk_acceptable`
- Any change to existing entry-state thresholds (`early`, `at_trigger`, `late`, `chased`)
- Any new fixed chase-distance threshold in percent
- Any global ranking redesign
- Any portfolio/hold/rotation logic

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Schema / versioning note
- Schema version bump is out of scope for this ticket and handled separately.
- This ticket may introduce:
  - a new config key for the late-entry effective-RR threshold
  - new `decision_reasons` values (`price_past_target_1`, `effective_rr_insufficient`)
- Codex must not choose or infer a canonical schema-version bump as part of this ticket unless a separate canonical versioning ticket explicitly requires it.

## Empirical verification case (mandatory)
Use the latest motivating `TRUMPUSDT` reversal ENTER case as the primary regression case for this ticket.

Required semantic expectations for that case:
- if `current_price_usdt >= target_1_price`, the candidate must not remain `ENTER`
- the candidate must be downgraded by the new late-entry guard, not by unrelated changes to:
  - scoring
  - execution
  - tradeability
  - risk model
- verification must document before/after values for:
  - `entry_price_usdt`
  - `current_price_usdt`
  - `target_1_price`
  - `target_2_price`
  - `stop_price_initial`
  - `entry_state`
  - `decision`
  - `decision_reasons`

Allowed substitution rule:
- Substitution is forbidden unless the motivating `TRUMPUSDT` case is unavailable in the selected fixture/run slice.
- If unavailable, the implementation must:
  1. document the absence explicitly,
  2. use the nearest equivalent case where a candidate is emitted as `ENTER` while current price has already consumed a substantial part of the target path,
  3. record exactly which substitute was used and why.
- Silent substitution is not allowed.

## Proposed change (high-level)
Add two decision-layer late-entry guards, evaluated in this order, for candidates that would otherwise qualify for `ENTER`.

- Before:
  - a candidate can become `ENTER` based on:
    - entry-eligible tradeability
    - entry-ready setup
    - acceptable risk
    - setup score meeting ENTER threshold
  - but the decision layer does not sufficiently test whether the trade still has acceptable reward-to-risk from **current price**
- After:
  - **Guard 1 — hard target-1 stop**
    - if `current_price_usdt >= target_1_price`, the candidate must not be `ENTER`
    - resulting decision: `NO_TRADE`
    - required reason key: `price_past_target_1`
  - **Guard 2 — effective RR from current price**
    - if Guard 1 does not fire, compute effective RR from current price using the canonical current stop/target ladder
    - if effective RR is below configured threshold, the candidate must not be `ENTER`
    - resulting decision: `WAIT`
    - required reason key: `effective_rr_insufficient`
- Backward compatibility impact:
  - some current `ENTER` candidates will become `WAIT` or `NO_TRADE`
  - output schema remains stable unless new explicit machine-readable fields are added and documented canonically
  - entry-state semantics remain unchanged; this ticket does not redefine `chased`

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)
- **Primary fix locus:** `scanner/pipeline/decision.py` is the primary implementation locus. This ticket is a decision-layer guard change, not a scoring or risk-model change.
- **Do not use `entry_state = chased` as a hard ENTER blocker.** That is intentionally out of scope because `chased` is too broad and includes small/benign deviations above trigger.
- **Do not introduce a new fixed chase-distance threshold.** No 1%, 2%, 3%, or similar hard cap may be added in this ticket.
- **Guard order is mandatory:**
  1. evaluate `price_past_target_1`
  2. only if Guard 1 does not fire, evaluate `effective_rr_insufficient`
- **Decision semantics are mandatory:**
  - `price_past_target_1` => `NO_TRADE`
  - `effective_rr_insufficient` => `WAIT`
- **Effective RR definition for this ticket is explicit:**
  - use canonical `current_price_usdt` as the live price anchor
  - use canonical `stop_price_initial` as the effective stop anchor
  - use canonical `target_2_price` as the effective RR checkpoint for ENTER gating, matching current Phase-1 risk semantics that evaluate RR on target 2 rather than target 1
  - compute:
    - numerator = `target_2_price - current_price_usdt`
    - denominator = `current_price_usdt - stop_price_initial`
    - `effective_rr_to_target_2 = numerator / denominator`
- **Threshold behavior is explicit:**
  - compare `effective_rr_to_target_2` against a dedicated config threshold for this decision guard
  - default value for `effective_rr_enter_threshold`: `1.3`
    - this matches existing `min_rr_to_target_2` semantics
    - it must be introduced as a separate key to allow independent later calibration
  - missing key => documented default `1.3`
  - invalid value => clear failure
- **Nullability / non-evaluable behavior is explicit:**
  - if any required input for Guard 1 or Guard 2 is missing, non-finite, non-positive where positivity is required, or otherwise not evaluable, the guard result must remain non-evaluable and must not silently coerce to pass/fail
  - non-evaluable late-entry guard data must not silently create a hard blocker
- **Not-evaluated vs failed:** keep these distinct
  - “late-entry guard not evaluable” is not the same as “effective RR insufficient”
  - “price past target 1” is a hard late-entry failure
- **Repo reality:** reuse existing canonical fields already present in trade-candidate rows (`current_price_usdt`, `target_1_price`, `target_2_price`, `stop_price_initial`, etc.) rather than inventing parallel truth sources.
- **Determinism:** with identical inputs and identical config, decision results and reason ordering must remain identical.

## Implementation Notes (optional but useful)
- Current canonical schema already separates:
  - `entry_price_usdt` (planned setup entry anchor)
  - `current_price_usdt` (live spot price)
  - `distance_to_entry_pct`
  - `entry_state`
  - canonical target ladder (`target_1_price`, `target_2_price`, `target_3_price`)
  - canonical stop (`stop_price_initial`)
- This ticket must preserve those semantics and only add decision logic on top.
- Current canonical risk semantics already use `rr_to_target_2` as the main RR checkpoint. This ticket must mirror that intent for live-price late-entry gating by using `effective_rr_to_target_2` from current price.
- If new machine-readable output fields are added (for example `effective_rr_to_target_2`), they must be documented in `docs/canonical/OUTPUT_SCHEMA.md`. If not added, tests must still verify the behavior via decisions and reasons.
- Reason ordering must remain deterministic and compatible with existing reason-order logic in the decision layer.

## Acceptance Criteria (deterministic)
1) A candidate with `current_price_usdt >= target_1_price` can no longer be emitted as `ENTER`.

2) When AC #1 fires, the resulting decision is exactly `NO_TRADE` and `decision_reasons` contains `price_past_target_1`.

3) For a candidate where `current_price_usdt < target_1_price` but `effective_rr_to_target_2` from current price is below configured threshold, the candidate can no longer be emitted as `ENTER`.

4) When AC #3 fires, the resulting decision is exactly `WAIT` and `decision_reasons` contains `effective_rr_insufficient`.

5) A candidate that remains near trigger and still has sufficient `effective_rr_to_target_2` from current price may still be emitted as `ENTER`; this ticket must not degrade all positive `late` or all `chased` states categorically.

6) The motivating `TRUMPUSDT` case no longer appears as `ENTER` after this change, and the downgrade is caused by the new late-entry guard rather than by unrelated scoring, execution, tradeability, or risk changes.

7) Existing `risk_acceptable` semantics remain unchanged; this ticket must not alter stop derivation, canonical RR ladder construction, or the pre-existing risk model.

8) Guard evaluation is deterministic and preserves stable reason ordering for identical inputs/config.

9) Missing or non-finite inputs required for late-entry guard evaluation remain distinguishable from true guard failures and are not silently coerced into `price_past_target_1` or `effective_rr_insufficient`.

10) Canonical decision-layer docs and output-schema docs are updated if any new config key or machine-readable field is introduced.

## Default-/Edgecase-Coverage (required for code tickets)
> Mark explicitly what this ticket covers. Every ✅ must point to acceptance criteria/tests. Every ❌ must be either “not relevant” or a separate follow-up.

- **Config Defaults (Missing key -> Default):** ✅ (AC #10; test required for any new late-entry RR threshold key)
- **Config Invalid Value Handling:** ✅ (AC #10; invalid threshold value must fail clearly; test required)
- **Nullability / no bool()-coercion:** ✅ (AC #9; test required)
- **Not-evaluated vs failed separated:** ✅ (AC #9; test required)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (N/A — decision/scoring ticket, no write pipeline/preflight changes)
- **ID/Filename Namespace Collisions:** ✅ (N/A — no runtime ID/file generation logic changed)
- **Deterministic sorting / tie-breakers:** ✅ (AC #8; test required)

## Tests (required if logic changes)
- Unit:
  - test: `current_price_usdt >= target_1_price` forces `NO_TRADE` with reason `price_past_target_1`
  - test: candidate below `target_1_price` but below effective-RR threshold becomes `WAIT` with reason `effective_rr_insufficient`
  - test: candidate near trigger with sufficient effective RR still remains eligible for `ENTER`
  - test: `entry_state = chased` alone does **not** force downgrade if the new late-entry guards do not fire
  - test: missing-key/default behavior for the new effective-RR threshold config
  - test: invalid threshold config value fails clearly
  - test: missing/non-finite `current_price_usdt`, `target_1_price`, `target_2_price`, or `stop_price_initial` does not silently coerce into a false guard failure
  - test: deterministic reason ordering when late-entry reasons are appended
- Integration:
  - regression test or fixture verification for the motivating `TRUMPUSDT` case showing before/after decision change from `ENTER` to non-ENTER
  - regression case proving at least one valid near-trigger candidate can still be `ENTER`
- Golden fixture / verification:
  - update `docs/canonical/VERIFICATION_FOR_AI.md` if decision verification behavior or expected fixtures change

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only semantics remain unchanged
- [ ] No lookahead is introduced
- [ ] Existing entry-state thresholds (`early`, `at_trigger`, `late`, `chased`) remain unchanged
- [ ] Existing risk-model stop derivation remains unchanged
- [ ] Existing canonical target ladder semantics remain unchanged
- [ ] Existing execution gate logic and thresholds remain unchanged
- [ ] Existing tradeability classification remains unchanged
- [ ] Stable deterministic ordering with explicit tie-breakers remains intact
- [ ] `WAIT` remains reserved for fully evaluated candidates per canonical decision-layer semantics

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` if logic/params/outputs changed
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if any scoring/threshold/decision verification behavior changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-14T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
