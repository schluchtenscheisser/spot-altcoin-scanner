> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Align setup target derivation with structural invalidation stops and evaluate `risk_acceptable` against `rr_to_target_2`

## Context / Source
- Recent fixes restored the active breakout path and unlocked execution gates for at least one real breakout candidate (HYPE), so the next dominant blocker is now visible in the live runs.
- Current runs still produce `0 ENTER / 0 WAIT / 20 NO_TRADE` or similarly near-empty actionable output, even after:
  - breakout series wiring fix
  - breakout execution-gate depth relaxation for HYPE-class names
- The newly exposed pattern is consistent across setup types:
  - structural `stop_source: "invalidation"` is used
  - `risk_pct_to_stop` is often large
  - `rr_to_target_1` is frequently unattractive even when execution and tradeability are otherwise acceptable
- Concrete examples from recent runs:
  - HYPE breakout: `execution_gate_pass: true`, `tradeability_class: DIRECT_OK`, but `risk_pct_to_stop ≈ 13.30%`, `rr_to_target_1 ≈ 0.53`, `risk_acceptable: false`
  - TAO reversal: very large stop distance and low RR to target 1
  - RENDER / DEEP / AVAX / ASTER show the same pattern: structural invalidation stop combined with comparatively near target 1 yields weak RR
- This ticket is intentionally **not** a generic threshold-tuning ticket. It addresses the underlying modeling conflict:
  - one source of truth for stop = structural invalidation (already established)
  - but target derivation is still often too close relative to that stop, making RR internally coherent yet strategically unusable
- The ticket makes an explicit operational decision to avoid a merely architectural but ineffective fix:
  - canonical targets become `1R / 2R / 3R`
  - `risk_acceptable` is evaluated against `rr_to_target_2`, not `rr_to_target_1`
- Rationale:
  - `target_1 = 1R` is definitional break-even-style symmetry and is too weak as the primary acceptance hurdle
  - `target_2 = 2R` is the economically meaningful first acceptance checkpoint in the new R-multiple model
- Existing stop-quality protection already exists elsewhere in the system and must remain in force:
  - the current ATR corridor / stop-distance guard remains the primary protection against pathological deep-stop trades
  - this ticket must not weaken or replace that protection

## Goal
After this change:
- setup targets and RR are derived from a coherent model relative to the effective stop source
- `rr_to_target_1` / `rr_to_target_2` become economically meaningful across breakout, pullback, and reversal
- the scanner no longer combines deep structural invalidation stops with target ladders that are systematically too near to produce viable RR
- target derivation remains setup-specific in terms of entry/invalidation context and does **not** fall back to deprecated fixed `+10%/+20%` semantics
- `risk_acceptable` is evaluated against `rr_to_target_2` (the 2R checkpoint), not `rr_to_target_1`

## Scope
Allowed files/modules to modify:
- `scanner/pipeline/scoring/trade_levels.py`
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`
- `scanner/pipeline/decision.py` only if field consumption must be updated to stay aligned with the new target derivation semantics; do not change unrelated decision policy thresholds in this ticket
- `scanner/config.py` only if existing RR-threshold field consumption must be rewired to target_2 evaluation while preserving current config/default semantics
- `config/config.yml` only if examples/comments must reflect the new evaluation target semantics
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- relevant tests under `tests/`

## Out of Scope
- No execution-gate changes
- No liquidity/tradeability threshold changes
- No timing / entry-state classification changes
- No alteration of canonical stop precedence established previously (`invalidation` first, ATR fallback second)
- No reintroduction of fixed-percentage TP semantics under any alias
- No new `max_stop_distance_pct` or alternate stop-distance guard in this ticket
- Optional config-key renaming from `min_rr_to_target_1` to `min_rr_to_target_2` is **not required** in this ticket; existing key wiring may be preserved if the new evaluation target is documented and implemented deterministically

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- Effective stop is already derived coherently (`invalidation` first, ATR fallback second).
- Target ladders remain setup-specific, but in many real runs the distance from entry to target 1 is too small relative to the effective stop distance.
- As a result, `rr_to_target_1` is frequently too low across otherwise valid breakout/pullback/reversal candidates.
- `risk_acceptable` is therefore dominated by a structurally weak first target ladder rather than by a coherent stop-target architecture.

After:
- Keep the current stop-source contract:
  1. valid structural invalidation below entry wins
  2. ATR fallback only when invalidation is unavailable / unusable
- Update target derivation so that the first and subsequent targets are coherent with the effective stop distance actually used for RR evaluation.
- Canonical behavior to implement:
  - derive targets from the **effective stop risk distance** (R-multiple ladder), not from a ladder that can drift arbitrarily close relative to that stop
  - preserve setup-specific entry and invalidation semantics
  - preserve setup-specific subtype/context, but normalize target sizing against the selected risk distance
- Canonical target policy:
  - `target_1_price` corresponds to **1R**
  - `target_2_price` corresponds to **2R**
  - `target_3_price` corresponds to **3R**
  where `1R = entry_price - effective_stop_price` for long setups
- `rr_to_target_1` / `rr_to_target_2` / `rr_to_target_3` then become definitionally 1.0 / 2.0 / 3.0 whenever the target ladder is evaluable and valid for long setups.
- Explicit decision for operational effectiveness:
  - `risk_acceptable` is evaluated against `rr_to_target_2`, not `rr_to_target_1`
  - the existing configured minimum RR threshold is applied to the target_2 checkpoint in this ticket unless a canonical doc already specifies a different mechanism
- Existing stop-quality protection remains in force:
  - the current ATR corridor / stop-distance guard remains the primary stop-quality filter
  - this ticket must not weaken, remove, or silently bypass that protection

Edge cases:
- If effective stop is missing / invalid / not below entry, targets cannot be derived from R-multiples and all target/RR fields remain `null`.
- If the computed risk distance is non-finite, non-positive, or effectively zero, target derivation remains unevaluable and returns nullable outputs.
- If setup-specific context wants to preserve an auxiliary/reference level (e.g. retest band, prior structure), it may remain in analysis metadata only; it must not replace the canonical displayed/evaluated target ladder unless specified in canonical docs.
- Breakout immediate and breakout retest must both use the same canonical target derivation contract once entry and effective stop are known.
- This ticket is long-only only; do not invent short-side semantics if the repo is currently long-only.

Backward compatibility impact:
- Target prices will change for many setups.
- RR fields will change materially and intentionally.
- `risk_acceptable` semantics will change intentionally: primary RR acceptance is now checked against `target_2` / `2R`.
- This is a canonical behavior change and must be documented.
- Old setup-specific target ladders must not survive silently as parallel truths in output fields.

## Codex Implementation Guardrails (No-Guesswork, Pflicht)
- **Config/Defaults:** This ticket must reuse existing central config/default handling. It introduces no new required config keys. If any optional config key is consulted, missing key != invalid key and central defaults must be reused rather than raw-dict ad-hoc fallbacks.
- **Nested override semantics:** If any existing `trade_levels` or `risk` config block is read while implementing this change, partial nested overrides continue to merge with central defaults per current repo behavior. Do not silently switch merge-vs-replace semantics.
- **Canonical stop precedence:** Effective stop selection remains unchanged:
  1. valid structural invalidation below entry
  2. ATR fallback only if invalidation unavailable/unusable
  3. else stop/risk/targets remain `null`
- **Risk acceptance decision:** `risk_acceptable` must be evaluated against `rr_to_target_2`. `rr_to_target_1` remains definitional 1.0 in the canonical R-multiple model and must not remain the primary acceptance hurdle after this ticket.
- **Stop-quality guard remains unchanged:** The existing ATR corridor / stop-distance guard remains the primary stop-distance protection. No new `max_stop_distance_pct` check or alternate stop-distance filter is introduced in this ticket.
- **Numerical robustness:** Non-finite numeric inputs (`NaN`, `inf`, `-inf`) and non-positive risk distances are unevaluable and must not yield numeric-looking targets or RR fields.
- **Nullability:** `target_1_price`, `target_2_price`, `target_3_price`, `rr_to_target_1`, `rr_to_target_2`, `rr_to_target_3`, `risk_pct_to_stop`, and `risk_acceptable` are nullable where the underlying stop/entry/risk distance is not evaluable. `null` means “not evaluable”, not “false”.
- **No bool() coercion:** Do not collapse nullable numeric/tri-state fields via truthiness.
- **Not-evaluated vs failed:** A setup with missing/invalid stop derivation is distinct from a setup with evaluated-but-unattractive RR. These states must remain separable in fields and tests.
- **No fixed-percentage TP fallback:** Do not reintroduce `entry * 1.10`, `entry * 1.20`, or similar percentage targets anywhere in active scoring/output logic.
- **Determinism:** For identical input feature rows and identical config, effective stop, target ladder, RR fields, and `risk_acceptable` must be identical run-to-run.
- **Repo reuse:** Reuse existing trade-level and phase-1 risk-field plumbing. Do not create a parallel target/RR pipeline for one setup type only.

## Implementation Notes
- The preferred place to normalize canonical target derivation is `scanner/pipeline/scoring/trade_levels.py`, because that is already the convergence point for trade levels and risk-field derivation.
- Preserve setup-specific entry and invalidation generation in each scorer (`breakout_trend_1_5d.py`, `pullback.py`, `reversal.py`) unless a scorer currently hardcodes a canonical target ladder that conflicts with this ticket.
- Recommended implementation shape:
  1. determine effective stop price using existing invalidation-first logic
  2. compute risk distance `risk_abs = entry_price - effective_stop_price`
  3. if `risk_abs` is finite and > 0, derive:
     - `target_1_price = entry_price + 1 * risk_abs`
     - `target_2_price = entry_price + 2 * risk_abs`
     - `target_3_price = entry_price + 3 * risk_abs`
  4. compute RR fields from these canonical targets
  5. derive `risk_acceptable` using the configured minimum RR threshold against `rr_to_target_2`
- If any scorer currently stores old setup-specific targets in `analysis.trade_levels.targets`, update that representation so output and decision consume the same canonical target ladder.
- If auxiliary/legacy target levels are still useful for research, keep them only as clearly non-canonical metadata (for example `analysis.reference_levels`) and do not surface them as the primary targets in outputs.
- Update canonical docs so they no longer imply that target ladders differ arbitrarily by setup type once effective stop selection is fixed.
- If the existing config key name still reads as `min_rr_to_target_1` (or legacy equivalent), it may remain temporarily as a compatibility key, but the docs must explicitly state that in this ticket the configured minimum RR is applied to the `target_2` checkpoint. No silent semantic drift without documentation.

## Acceptance Criteria (deterministic)
1. For every evaluable long setup with valid entry and effective stop below entry, the canonical target ladder is:
   - `target_1_price = entry + 1R`
   - `target_2_price = entry + 2R`
   - `target_3_price = entry + 3R`
   where `R = entry - effective_stop`.
2. For every evaluable long setup, `rr_to_target_1 == 1.0`, `rr_to_target_2 == 2.0`, and `rr_to_target_3 == 3.0` within floating-point tolerance derived from the canonical target ladder.
3. `risk_acceptable` is evaluated using the same effective stop and the same canonical target ladder shown in outputs, and the primary RR acceptance check is applied to `rr_to_target_2`, not `rr_to_target_1`.
4. If effective stop is missing, invalid, non-finite, not below entry, or implies non-positive `R`, then target prices and RR fields remain `null` and `risk_acceptable` remains `null`.
5. No active code path derives primary targets from fixed-percentage gain formulas.
6. Breakout, pullback, and reversal setups all expose the same canonical target semantics once entry and effective stop are known.
7. Existing stop-source precedence (`invalidation`, then `atr_fallback`) remains unchanged.
8. The existing ATR corridor / stop-distance guard remains active and unchanged; this ticket does not remove or bypass it.
9. Canonical docs are updated to describe the target ladder as R-multiple based, to state explicitly that `risk_acceptable` uses `rr_to_target_2`, and to distinguish unevaluable (`null`) from evaluated-but-unacceptable outcomes.
10. Tests cover at least one breakout, one pullback, and one reversal fixture through the real trade-level/risk-field path.

## Default-/Edgecase-Abdeckung (Pflicht)
- **Config Defaults (Missing key -> Default):** ✅ (No new required config key; existing central defaults remain in force; AC: #7/#9; Test: config-less/default path still evaluates against target_2 deterministically)
- **Config Invalid Value Handling:** ✅ (If existing config RR threshold key is invalid/non-finite, behavior must follow current central validation or fail clearly; AC: #3/#9; Test: invalid threshold value fails clearly if current config path already requires finite numeric input)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #4/#9; Test: unevaluable stop/risk leaves target/RR/risk fields `null`, not `false`/`0`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #4/#9; Test: missing/invalid stop path remains distinct from evaluated-but-risk-unacceptable path)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write-mode feature introduced)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #1/#2/#3; Test: identical inputs reproduce identical targets/RR values and identical risk_acceptable evaluation)

## Tests (required)
- Unit:
  - Test valid breakout trade levels with entry and structural invalidation -> canonical `1R/2R/3R` targets and RR values `1.0/2.0/3.0`, with `risk_acceptable` evaluated against `rr_to_target_2`.
  - Test valid pullback trade levels with entry-zone-derived entry and structural invalidation -> canonical `1R/2R/3R` targets and RR values `1.0/2.0/3.0`, with `risk_acceptable` evaluated against `rr_to_target_2`.
  - Test valid reversal trade levels with entry trigger and structural invalidation -> canonical `1R/2R/3R` targets and RR values `1.0/2.0/3.0`, with `risk_acceptable` evaluated against `rr_to_target_2`.
  - Test invalidation missing -> ATR fallback stop still yields canonical `1R/2R/3R` targets if ATR fallback valid.
  - Test invalid/non-finite stop inputs (`NaN`, `inf`, `-inf`) -> all target/RR/risk fields remain `null`.
  - Test zero or negative risk distance -> all target/RR/risk fields remain `null`.
  - Test nullable tri-state fields are not coerced to `false`.
  - Test existing configured minimum RR threshold is applied to `rr_to_target_2`, not `rr_to_target_1`.
- Integration:
  - Regression test using a breakout fixture through the real scorer path to confirm output `analysis.trade_levels.targets` and top-level target/RR fields match the canonical R-multiple ladder.
  - Regression test using one pullback and one reversal fixture through the real scorer path to confirm the same.
  - Regression test that `risk_acceptable` is computed from the displayed canonical targets rather than a hidden alternate ladder, and that the acceptance hurdle is `rr_to_target_2`.
  - Regression test that the existing ATR corridor / stop-distance guard still blocks pathological deep-stop cases exactly as before.
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` examples and any target/RR fixture expectations if sample outputs change.

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- Effective stop precedence remains `invalidation` first, ATR fallback second
- Deterministic ordering with stable tie-breakers
- No fixed-percentage TP semantics reintroduced
- No execution-gate or liquidity-threshold changes in this ticket
- No timing / entry-state classification changes in this ticket
- Existing ATR corridor / stop-distance guard remains unchanged

- [ ] Preserve existing stop-source precedence exactly
- [ ] Preserve existing config/default resolution behavior
- [ ] Preserve long-only semantics unless canonical docs explicitly specify otherwise

## Definition of Done
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if target/RR examples changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-13T00:00:00Z"
priority: P0
type: bugfix
owner: codex
related_issues: []
```
