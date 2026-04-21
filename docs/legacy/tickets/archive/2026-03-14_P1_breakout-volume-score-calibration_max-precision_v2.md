> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P1] Calibrate breakout volume and score scaling for breakout_trend_1_5d using fixed comparison set

## Context / Source (optional)
- Breakout detection is no longer structurally broken: the active `breakout_trend_1_5d` path now produces candidates again (`breakout_scored: 6` on the relevant 2026-03-14 run).
- The remaining operational issue is not detection but competitiveness: valid breakout candidates such as HYPE and C98 remain numerically weak versus pullback/reversal candidates and therefore rarely surface near the top of the global ranking.
- Prior analysis indicates that TRX is a separate risk-floor/design question (`risk_acceptable=false` via too-small stop distance) and must not be mixed into this ticket.
- This ticket is limited to breakout score calibration, with emphasis on breakout `volume_score`, breakout component scaling, and the breakout multiplier chain.
- Primary run context:
  - `reports/2026-03-14.md`
  - `reports/2026-03-14_2026-03-14_1773470654209.manifest.json`
- Relevant implementation paths:
  - `scanner/pipeline/scoring/breakout_trend_1_5d.py`
  - `scanner/pipeline/global_ranking.py`
  - `config/config.yml`

## Goal
Make the active breakout scorer produce scores that are numerically competitive with pullback/reversal for genuinely valid breakout setups, without relaxing execution/liquidity gates and without changing the separate breakout risk-floor policy.

Success means:
- HYPE/C98-like breakout rows no longer collapse into artificially weak scores primarily because of current breakout volume/score scaling.
- Breakout scores remain deterministic and bounded to `0..100`.
- Legitimate low-quality or illiquid breakout names remain weak or excluded.

## Scope
Allowed modules/files to change:
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `config/config.yml`
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/VERIFICATION_FOR_AI.md` if scoring curves / thresholds / expected verification behavior change

Optional but allowed if needed for verification only:
- tests covering breakout scorer behavior
- fixture/golden verification files used by the current test suite

## Out of Scope
- Any change to `risk_acceptable`, stop derivation, ATR fallback, or breakout-specific stop-floor policy
- Any change to execution gates, tradeability classes, orderbook depth thresholds, spread thresholds, or slippage thresholds
- Any change to pullback/reversal scoring formulas unless required only for cross-setup regression verification
- Any change to decision-layer thresholds (`min_score_for_wait`, `min_score_for_enter`, BTC risk-off enter boost)
- Any change to setup weights or global ranking setup category weights as a workaround for breakout under-scaling
- Any new setup category, new ranking channel, or broad global-ranking redesign

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Empirical comparison set (mandatory, no free substitution)
Use the 2026-03-14 relevant run family as the primary verification set.

Required symbols and roles:
- Breakout calibration targets:
  - `HYPE`
  - `C98`
- Breakout execution/liquidity fail controls:
  - `JST`
  - `KERNEL`
- Pullback comparison controls:
  - `TAO`
  - `GRT`
  - `ALGO`

Role semantics:
- `HYPE` is the required positive breakout calibration target with acceptable tradeability/execution behavior.
- `C98` is a required breakout score-calibration target, but it must remain interpreted as an execution/liquidity-gated case if that gate state is unchanged in the selected verification fixture.
- `JST` and `KERNEL` are the required negative controls for legitimate breakout execution/liquidity failure behavior.
- `TAO`, `GRT`, and `ALGO` are the required comparison controls for strong non-breakout candidates that currently compete for visibility/ranking.

Allowed substitution rule:
- Substitution is forbidden unless a required symbol is absent from the selected fixture/run slice.
- If a required symbol is absent, the implementation must:
  1. document that absence explicitly in test/verification notes,
  2. keep the same category intent,
  3. select the nearest equivalent symbol from the same 2026-03-14 run family,
  4. record which substitution was used and why.
- Silent substitution is not allowed.

## Proposed change (high-level)
Describe and implement a breakout-score calibration that fixes the current under-scaling of valid breakout candidates, with special attention to breakout volume contribution and the multiplicative compression chain.

- Before:
  - `breakout_trend_1_5d` computes a weighted base score from:
    - breakout distance
    - volume
    - trend
    - BB compression
  - then compresses the result through:
    - anti-chase multiplier
    - overextension multiplier
    - BTC multiplier
  - in practice, valid or otherwise structurally interesting breakouts such as HYPE/C98 can end with low final scores even when breakout confirmation is present.
- After:
  - the breakout scorer must be recalibrated so that valid breakout setups are not numerically under-ranked solely because the current breakout volume/score curve is too harsh or the breakout end-scale is too compressed.
  - the implementation may adjust one or more of:
    - breakout volume score curve
    - breakout component weighting
    - breakout base-score composition
    - breakout multiplicative compression behavior
  - but it must not change:
    - setup validity rules
    - execution gate logic
    - decision-layer thresholds
    - stop/risk semantics
- Edge cases:
  - missing or non-finite numeric breakout inputs must stay explicitly handled and must not create fake strength
  - candidates that fail execution/liquidity for legitimate reasons must remain weak or excluded
  - BTC risk-off may still penalize breakouts, but not so strongly that a valid breakout is systematically uncompetitive versus weaker pullback/reversal candidates
- Backward compatibility impact:
  - breakout score distribution will change by design
  - output schema must remain stable unless explicitly documented in canonical docs
  - any canonical description of breakout scoring behavior must be updated if formulas/thresholds/curves change

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)
- **Primary fix locus:** `_volume_score` in `scanner/pipeline/scoring/breakout_trend_1_5d.py` is currently a `@staticmethod` with hardcoded values `1.5` (threshold) and `2.5` (ideal); it does not read the breakout scoring config. This is the primary fix-point for this ticket.
- **Config/Defaults:** If config values are read or validated, use the same central defaults/semantics as the active config path. Missing key != invalid unless explicitly specified otherwise.
- **Config decision for this ticket is explicit:** Introduce config-backed breakout volume calibration keys rather than leaving the breakout volume thresholds hardcoded. This ticket exists to enable empirical recalibration without a fresh code PR for every threshold revision.
- **Required config behavior if new keys are introduced:**
  - missing-key behavior: fall back to the documented canonical defaults
  - invalid-value behavior: fail clearly rather than silently coercing
  - nested override behavior: follow current central config semantics; do not introduce ad-hoc raw-dict fallback logic
- **Partial nested overrides:** For any breakout scoring config block touched by this ticket, partial nested overrides must be treated consistently with current central config semantics. Do not introduce ad-hoc raw-dict fallback logic.
- **Numerics:** Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid/not evaluable inputs and must not survive into numeric-looking outputs.
- **Nullability:** Do not coerce semantically nullable fields via implicit `bool(...)`. `None` must remain distinct from `False` when the field semantics require that distinction.
- **Not-evaluated vs failed:** “Not evaluated / not derivable” must remain distinct from “evaluated and weak/failed”. This ticket must not collapse missing/unavailable breakout inputs into a negative breakout score reason that looks like a true failed evaluation.
- **Determinism:** With identical inputs and identical config, breakout scores and ordering must remain identical. Stable tie-break behavior must remain intact.
- **Repo reality:** Reuse existing breakout scorer helpers and the current `breakout_trend_1_5d` path. Do not create a second competing breakout scorer path under a new name.
- **Pipeline boundaries:** This ticket changes breakout scoring only. It must not silently modify tradeability, risk, decision, or execution-stage behavior.
- **No silent category drift:** The intent is score calibration, not strategy redefinition. Breakout candidates that are structurally invalid must not be converted into valid setups by this ticket.
- **No symbolic drift in verification:** The required comparison set above is mandatory. Do not replace it with ad-hoc alternatives unless the explicit substitution rule is triggered.

## Implementation Notes (optional but useful)
- Current active implementation:
  - base score in `scanner/pipeline/scoring/breakout_trend_1_5d.py` is currently built from:
    - breakout distance score
    - volume score
    - trend score
    - BB score
  - final score is then compressed by:
    - anti-chase multiplier
    - overextension multiplier
    - BTC multiplier
- `_volume_score` in `breakout_trend_1_5d.py` is currently a `@staticmethod` with hardcoded values `1.5` (threshold) and `2.5` (ideal) and does not read config. This is the primary fix-point.
- The implementation must explicitly determine and document which layer caused the observed under-scaling in the fixed comparison set:
  - volume curve only
  - base score composition
  - multiplier chain
  - or a combination
- If new config-backed breakout volume thresholds are introduced, they must be documented in canonical configuration/scoring docs and in verification guidance.
- Global ranking weighting (`phase_policy.setup_weights_active`, `setup_weights_by_category`) is not the primary target of this ticket and must not be used as the first-line workaround.

## Acceptance Criteria (deterministic)
1) Using the fixed 2026-03-14 comparison set, `HYPE` and `C98` receive materially higher breakout `final_score` values than before, and the increase is attributable to documented breakout scorer calibration rather than to execution, decision, or risk changes.

2) For `C98`, if `execution_gate_pass` remains `False` in the selected verification fixture, the ticket is still considered correct as long as:
   - breakout score calibration raises the breakout scoring fields as intended, and
   - `C98` remains blocked by the unchanged execution/liquidity gate rather than by silent gating changes.

3) Using the fixed 2026-03-14 comparison set, `JST` and `KERNEL` do not become valid high-ranking breakout candidates solely because of this ticket.

4) Using the fixed 2026-03-14 comparison set, `HYPE` becomes numerically more competitive against the comparison controls `TAO`, `GRT`, and `ALGO`, and the verification output documents the before/after comparison explicitly.

5) The breakout scorer remains deterministic: with identical inputs and identical config, the produced breakout score, base score, multipliers, and sorted breakout result order are identical across repeated runs.

6) The final breakout score remains clamped to `0..100`, and non-finite numeric inputs do not propagate into `score`, `base_score`, `final_score`, or component outputs.

7) Missing/non-evaluable breakout inputs remain distinguishable from evaluated-but-weak breakout cases; this ticket must not collapse “not evaluable” into “failed breakout quality”.

8) The implementation preserves the current boundary that this ticket does not change:
   - `risk_acceptable`
   - stop derivation
   - execution gate pass/fail behavior
   - tradeability classification
   - decision thresholds
   - setup category weights

9) Canonical breakout-scoring documentation is updated to match the new active breakout score behavior if any formula, weighting, or curve behavior changes.

10) `docs/canonical/VERIFICATION_FOR_AI.md` is updated if the scorer’s expected verification behavior, calibration fixtures, or score interpretation changes.

## Default-/Edgecase-Coverage (required for code tickets)
> Mark explicitly what this ticket covers. Every ✅ must point to acceptance criteria/tests. Every ❌ must be either “not relevant” or a separate follow-up.

- **Config Defaults (Missing key -> Default):** ✅ (AC #9/#10; required if new config-backed breakout volume keys are introduced)
- **Config Invalid Value Handling:** ✅ (If config-backed breakout volume keys are added, invalid numeric values must fail clearly; test required)
- **Nullability / no bool()-coercion:** ✅ (AC #6/#7; test required)
- **Not-evaluated vs failed separated:** ✅ (AC #7; test required)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (N/A — scoring-only ticket, no write pipeline/preflight changes)
- **ID/Filename Namespace Collisions:** ✅ (N/A — ticket does not create runtime IDs/files in application logic)
- **Deterministic sorting / tie-breakers:** ✅ (AC #5; test required)

## Tests (required if logic changes)
- Unit:
  - breakout scorer test proving the calibrated `HYPE` fixture yields a higher final breakout score than before while preserving `0..100` bounds
  - breakout scorer test proving the calibrated `C98` fixture yields a higher final breakout score than before while preserving `0..100` bounds, without changing the unchanged execution/liquidity gate interpretation
  - test proving config-backed breakout volume thresholds are read by the breakout scorer rather than ignored by the existing `_volume_score` path
  - test for invalid/non-finite breakout numeric inputs (`NaN`, `inf`, `-inf`) proving they do not propagate into numeric outputs
  - test for “not evaluable” vs “evaluated but weak” separation where breakout inputs are missing/invalid
  - deterministic repeat-order test for breakout candidate sorting / tie-break behavior
  - one missing-key/default test and one invalid-value failure test for any new config-backed breakout volume threshold keys
- Integration:
  - scorer/regression verification on a relevant fixture/run slice containing exactly these required symbols when available:
    - `HYPE`
    - `C98`
    - `JST`
    - `KERNEL`
    - `TAO`
    - `GRT`
    - `ALGO`
  - verification must include an explicit before/after table or structured comparison for:
    - breakout score
    - base score
    - breakout volume score
    - anti-chase multiplier
    - overextension multiplier
    - BTC multiplier
    - final score
    - `execution_gate_pass`
- Golden fixture / verification:
  - update `docs/canonical/VERIFICATION_FOR_AI.md` if score curves/threshold behavior changes
  - update any golden expected values used by the existing verification suite
  - include explicit substitution notes if any required symbol is unavailable

## Constraints / Invariants (must not change)
- [ ] Closed-candle-only semantics remain unchanged
- [ ] No lookahead is introduced
- [ ] Breakout score range remains clamped to `0..100`
- [ ] Stable deterministic ordering with explicit tie-breakers remains intact
- [ ] Execution gate logic and thresholds remain unchanged
- [ ] Risk/stop semantics remain unchanged
- [ ] Decision-layer thresholds remain unchanged
- [ ] Setup category weights remain unchanged
- [ ] Output schema field names remain unchanged unless canonical docs are explicitly updated

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` if logic/params/outputs changed
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if any scoring/threshold/curve behavior changed
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
