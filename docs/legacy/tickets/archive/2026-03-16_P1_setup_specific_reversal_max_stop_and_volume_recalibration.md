> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Setup-specific reversal max stop distance and breakout_trend_1_5d volume threshold recalibration

## Context / Source (optional)
This ticket packages the next agreed product change after the recent diagnosis work:

- Reversal setups are currently blocked too aggressively by the global `risk.max_stop_distance_pct` bound.
- The current `scoring.breakout_trend_1_5d.volume_score_min_spike` / `volume_score_full_spike` thresholds are too strict relative to observed candidates and should be recalibrated.
- The ATR extraction-path issue in the external diagnosis script was acknowledged separately and is **not** part of this product ticket.

Prior analysis concluded that the highest-leverage product change is to allow a wider stop-distance budget for **reversal** setups only, starting at **20%**, while leaving other setup types unchanged for now.

## Goal
After this change:

1. Reversal setups use a setup-specific `risk.max_stop_distance_pct = 20.0`.
2. Breakout and pullback setups keep the canonical/default `risk.max_stop_distance_pct = 12.0` unless explicitly overridden.
3. `scoring.breakout_trend_1_5d.volume_score_min_spike` becomes `1.0`.
4. `scoring.breakout_trend_1_5d.volume_score_full_spike` becomes `1.4`.
5. Phase-1 risk evaluation and config validation behave deterministically for both scalar and setup-specific stop-distance config.
6. Canonical docs and AI verification docs are updated in the same PR if scoring thresholds / config semantics change.

## Scope
Allowlist of files/modules that may need changes:

- `config/config.yml`
- `scanner/config.py`
- `scanner/pipeline/scoring/trade_levels.py`
- `tests/test_config_v421.py`
- `tests/test_pr09_phase1_risk_fields.py`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`

## Out of Scope
- Any ATR extraction-path or aggregation fix in external diagnosis scripts
- Any architecture rewrite of risk computation
- Any decision-layer threshold change beyond the explicit config changes in this ticket
- Any additional widening beyond `reversal = 20.0`
- Any new setup type or taxonomy change

## Canonical References (important)
List the canonical documents that define/are affected by this change.
(Do not link to legacy as authority.)

- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary).

- Before:
  - `risk.max_stop_distance_pct` is treated as one global scalar threshold.
  - Reversal setups are rejected by the same max-stop rule as breakout/pullback setups.
  - `breakout_trend_1_5d` volume scoring uses stricter thresholds (`1.2` / `2.2` in current runtime config).
- After:
  - `risk.max_stop_distance_pct` may be configured either as:
    - a scalar numeric value, or
    - a setup-specific mapping with at least `default`, plus optional setup overrides such as `reversal`, `pullback`, `breakout`
  - For this ticket, runtime config must be changed to:
    - `risk.max_stop_distance_pct.default = 12.0`
    - `risk.max_stop_distance_pct.reversal = 20.0`
    - `risk.max_stop_distance_pct.pullback = 12.0`
    - `risk.max_stop_distance_pct.breakout = 12.0`
  - `compute_phase1_risk_fields(setup_type, ...)` must resolve the correct max-stop threshold based on `setup_type`.
  - `scoring.breakout_trend_1_5d.volume_score_min_spike = 1.0`
  - `scoring.breakout_trend_1_5d.volume_score_full_spike = 1.4`
- Edge cases:
  - Missing `risk.max_stop_distance_pct` still uses canonical/default semantics.
  - Missing setup-specific override falls back to `default`.
  - Invalid mapping values must fail config validation with clear field-specific errors.
  - If `default` is missing from a setup-specific mapping, config validation must fail.
- Backward compatibility impact:
  - Existing scalar `risk.max_stop_distance_pct` configs remain valid and keep current semantics.
  - Existing code paths that only read scalar config must be updated to use central accessor/lookup logic instead of raw dict assumptions.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Config/Defaults:** If config values are read or validated, use **ScannerConfig defaults** or a single central accessor/lookup rule. Missing key is **not** invalid unless explicitly specified here.
- **Partial nested overrides:** For setup-specific `risk.max_stop_distance_pct`, treat the mapping as a **fieldwise merge with defaults**, not as full replacement. Missing setup-specific subkeys fall back to `default`. Missing top-level key falls back to canonical default.
- **Required mapping key:** If `risk.max_stop_distance_pct` is configured as an object, `default` is required. A mapping without `default` is invalid.
- **Invalid values:** Non-numeric, non-finite, negative, or otherwise invalid threshold values must produce a clear validation error. Do not silently normalize invalid config.
- **Nullability:** Do not introduce implicit `bool(...)` coercion for nullable risk fields. Existing nullable Phase-1 risk fields remain nullable.
- **Not-evaluated vs failed:** This ticket does not introduce a new status taxonomy. Preserve existing separation semantics where risk is non-evaluable (`null`) versus negatively evaluated (`False`) when risk is evaluable.
- **Determinism:** Identical input + identical config must produce identical risk acceptance and scoring behavior.
- **Repo reality:** Reuse existing helpers and validation structure; do not introduce a parallel config truth outside canonical docs and central config accessors.

## Implementation Notes (optional but useful)
- `scanner/pipeline/scoring/trade_levels.py` is the primary consumer that must stop assuming a single scalar global `max_stop_distance_pct`.
- `scanner/config.py` currently holds canonical config access/validation logic and should remain the single source for default semantics.
- Because a scoring threshold changes, update `docs/canonical/VERIFICATION_FOR_AI.md` with the new expected values / verification points for `breakout_trend_1_5d` volume behavior.

## Acceptance Criteria (deterministic)
1) `config/config.yml` defines `risk.max_stop_distance_pct` as a mapping with:
   - `default: 12.0`
   - `reversal: 20.0`
   - `pullback: 12.0`
   - `breakout: 12.0`

2) `config/config.yml` defines:
   - `scoring.breakout_trend_1_5d.volume_score_min_spike: 1.0`
   - `scoring.breakout_trend_1_5d.volume_score_full_spike: 1.4`

3) Runtime/config access supports both forms for `risk.max_stop_distance_pct`:
   - scalar numeric value
   - setup-specific mapping with required `default`

4) When `compute_phase1_risk_fields("reversal", ...)` evaluates a stop distance above `12.0` and at or below `20.0`, `risk_acceptable` may evaluate `True` if all other risk constraints pass.

5) When `compute_phase1_risk_fields("pullback", ...)` or `compute_phase1_risk_fields("breakout", ...)` evaluates the same stop distance above `12.0`, `risk_acceptable` remains `False` unless their applicable max-stop threshold is explicitly overridden above `12.0`.

6) If `risk.max_stop_distance_pct` is missing entirely, the canonical/default max-stop behavior remains `12.0`.

7) If `risk.max_stop_distance_pct` is configured as an object without `default`, config validation fails with a field-specific error.

8) If `risk.max_stop_distance_pct.default` or any setup-specific override is non-numeric, non-finite, or negative, config validation fails with a field-specific error.

9) Existing scalar configs such as `risk.max_stop_distance_pct: 15.0` remain valid and preserve scalar semantics.

10) Phase-1 risk nullable semantics remain unchanged:
   - non-evaluable risk fields remain `null`
   - evaluable but failing risk fields remain explicit booleans / numeric values per existing contract

11) Canonical docs are updated in the same PR to reflect:
   - setup-specific config semantics for `risk.max_stop_distance_pct`
   - the new `breakout_trend_1_5d` volume thresholds
   - any verification expectations affected by the scoring-threshold change

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

> Markiere explizit, was dieses Ticket abdeckt. Jeder ✅ braucht einen Verweis auf Acceptance Criteria/Test(s).
> Jeder ❌ muss entweder “nicht relevant” sein oder als Follow-up Ticket eingeplant werden.

- **Config Defaults (Missing key → Default):** ✅ (AC: #3, #6 ; Test: missing `risk.max_stop_distance_pct` uses default `12.0`)
- **Config Invalid Value Handling:** ✅ (AC: #7, #8 ; Test: missing `default`, non-numeric/negative value)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #10 ; Test: existing nullable risk-fields test remains passing)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #10 ; Test: existing non-evaluable risk-path test remains passing)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no write-path / strict-preflight behavior is changed by this ticket)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A – ticket changes no filename/id generation logic)
- **Deterministische Sortierung/Tie-breaker:** ✅ (N/A – ticket changes no ranking sort/tie-break logic; scoring threshold update must remain deterministic)

## Tests (required if logic changes)
- Unit:
  - Add/extend config-validation tests for scalar and mapping forms of `risk.max_stop_distance_pct`
  - Add/extend Phase-1 risk-field tests to prove setup-specific `reversal` max-stop acceptance versus `pullback` / `breakout` rejection at the same stop distance
  - Keep/verify existing nullable risk-field tests still pass unchanged
- Integration:
  - None required unless an existing integration suite already covers config loading + scoring/risk end-to-end for these paths
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` for the changed `breakout_trend_1_5d` volume thresholds
  - If an existing golden verification covers these exact thresholds, update it deterministically

## Constraints / Invariants (must not change)
Examples:
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges clamp to 0..100
- Timestamp unit = ms

- [ ] Closed-candle-only behavior must not change
- [ ] No-lookahead behavior must not change
- [ ] Existing deterministic ordering / tie-break behavior must not change
- [ ] Existing Phase-1 target ladder semantics (`1R/2R/3R`) must not change
- [ ] Existing nullable risk output contract must not change
- [ ] This remains exactly **1 ticket → 1 PR**

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` because logic/parameters change
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` because scoring thresholds change
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-16T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
