> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Make stop/risk derivation invalidation-first with ATR fallback and align risk outputs to setup truth

## Context / Source
- This ticket follows the cleanup of conflicting fixed-TP semantics.
- Current `scanner/pipeline/scoring/trade_levels.py` derives `stop_price_initial` primarily from `entry - atr_multiple * atr_value`, even when a setup-specific structural invalidation is already available.
- This creates inconsistent risk semantics: setup analysis shows an invalidation level, while risk/decision may use a different stop.
- User decision: implement the previously proposed model:
  - use setup invalidation as the authoritative stop when present and derivable
  - fall back to ATR-derived stop only when invalidation is unavailable
  - keep naming aligned to target-index semantics

## Goal
After this change, risk, stop, target, RR, and decision use one consistent source of truth:
- entry from setup trade levels
- stop from setup invalidation when available, else ATR fallback
- targets from setup target levels
- risk acceptance derived only from that unified stop/target model

## Scope
Allowed files/modules to modify:
- `scanner/pipeline/scoring/trade_levels.py`
- setup scorers that populate trade levels, if required only to normalize invalidation fields:
  - `scanner/pipeline/scoring/reversal.py`
  - `scanner/pipeline/scoring/pullback.py`
  - `scanner/pipeline/scoring/breakout.py`
  - `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `scanner/pipeline/decision.py` (only if field-name alignment requires it; do not change decision policy)
- `scanner/pipeline/output.py` (only for field pass-through/report labels already aligned in prior ticket)
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- relevant tests under `tests/`

## Out of Scope
- No threshold tuning (`min_rr`, `max_stop_distance_pct`, etc.) in this ticket.
- No change to ranking or scoring formulas apart from stop/risk derivation source.
- No addition of trailing-stop, dynamic exit, or multi-stop behavior.
- No broad schema redesign beyond fields required to expose consistent stop origin / target-index semantics.

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- `stop_price_initial` is ATR-derived even when setup invalidation exists.
- Risk acceptance can reject a setup based on a stop that is not the setup’s structural invalidation.
- Reported setup invalidation and effective stop may disagree.

After:
- Stop derivation becomes:
  1. use setup invalidation if present, finite, positive, and strictly below entry
  2. else use ATR fallback (`entry - atr_multiple * atr_value`) if derivable and strictly below entry
  3. else keep stop/risk fields `null`
- Risk fields use target-index naming:
  - `rr_to_target_1`
  - `rr_to_target_2`
- `risk_acceptable` is derived only from:
  - selected stop source
  - risk distance bounds
  - setup target 1 RR threshold
- Expose stop provenance explicitly in outputs, e.g.:
  - `stop_source: "invalidation" | "atr_fallback" | null`
- If invalidation exists but is malformed / non-finite / not below entry, treat it as unavailable for stop derivation and continue to ATR fallback; do not silently call malformed data “valid invalidation”.

Edge cases:
- Pullback setup with zone center entry and missing invalidation -> ATR fallback allowed.
- Invalidation equal to or above entry -> invalid as stop source; use ATR fallback if available.
- Non-finite invalidation (`NaN`, `inf`, `-inf`) -> invalid as stop source.
- Missing targets -> RR fields remain `null`; `risk_acceptable` remains `null` if RR cannot be evaluated.
- Missing ATR and missing valid invalidation -> all stop/risk fields remain `null`.
- `null` means not evaluable, not failed.

Backward compatibility impact:
- Effective stop values may change for setups where invalidation exists.
- This is an intentional logic change and must be documented canonically.
- Do not preserve old ATR-first behavior behind hidden fallback or undocumented toggle.

## Codex Implementation Guardrails (No-Guesswork)
- **Config/Defaults:** Reuse central/default config handling already used by risk config readers. Missing keys use existing defaults. Invalid values still produce clear errors where current code already enforces that.
- **Missing vs Invalid:** Distinguish:
  - invalidation missing
  - invalidation present but invalid / non-finite / not usable
  - invalidation present and usable
  This distinction must be testable.
- **Nullability:** `stop_price_initial`, `risk_pct_to_stop`, `rr_to_target_1`, `rr_to_target_2`, `risk_acceptable`, and `stop_source` are nullable where data is not evaluable. Do not coerce `null` to `false`.
- **No bool() coercion:** Tri-state fields must preserve `null`.
- **Not-evaluated vs failed:** “Could not evaluate stop/risk” must remain distinct from “evaluated and unacceptable”.
- **Determinism:** Preserve deterministic ranking/order; no randomness or unstable dict/set iteration.
- **Repo reuse:** Reuse existing setup `invalidation` field from trade levels. Do not introduce a parallel invalidation truth.
- **No silent fallback drift:** Fallback order is strict and documented: invalidation first, then ATR fallback, then `null`.

## Implementation Notes
- In `compute_phase1_risk_fields(...)`:
  - resolve entry from setup trade levels as before
  - resolve invalidation from `trade_levels`
  - validate invalidation usability:
    - numeric finite
    - positive
    - strictly below entry for long setups
  - choose stop source deterministically
  - compute risk metrics from the chosen stop only
- Add explicit `stop_source` field to returned risk fields.
- Rename RR fields inside risk derivation and downstream consumers to target-index naming.
- If downstream output/report code still formats old RR names, update it in the same PR only as required for consistency with the new canonical names.
- Decision logic should continue consuming the same semantic concept (`risk_acceptable`), but field-name updates must be reflected where needed.
- Canonical docs must describe invalidation-first semantics and fallback order explicitly.

## Acceptance Criteria (deterministic)
1. If a setup has a valid structural invalidation below entry, `stop_price_initial` equals that invalidation and `stop_source == "invalidation"`.
2. If structural invalidation is missing or unusable, and ATR fallback yields a valid stop below entry, `stop_price_initial` equals the ATR-derived stop and `stop_source == "atr_fallback"`.
3. If neither structural invalidation nor ATR fallback yields a valid stop, `stop_price_initial`, `risk_pct_to_stop`, `rr_to_target_1`, `rr_to_target_2`, `risk_acceptable`, and `stop_source` are all `null`.
4. `risk_acceptable` is computed only from the selected stop source plus setup target levels; it is never computed from a stop different from the effective `stop_price_initial`.
5. Non-finite invalidation or target values (`NaN`, `inf`, `-inf`) do not survive into numeric-looking outputs and instead result in nullable fields / fallback behavior per spec.
6. `null` risk fields remain `null`; they are not implicitly coerced into `false`, `0`, or fail reasons that imply successful evaluation.
7. Canonical docs describe invalidation-first / ATR-fallback stop semantics and the new/retained field names.
8. Tests cover missing invalidation, invalid invalidation, valid invalidation, missing ATR, and non-finite numeric inputs.

## Default-/Edgecase-Abdeckung
- **Config Defaults (Missing key -> Default):** ✅ (AC: #2/#3; Test: existing ATR fallback/default config path still works)
- **Config Invalid Value Handling:** ✅ (AC: #8; Test: preserve clear error behavior for invalid risk config values if touched)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #3/#6; Test: all unevaluable fields remain `null`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #3/#6; Test: no false-negative coercion when stop cannot be derived)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write mode added)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #8; Test: unchanged ordering regression)

## Tests (required)
- Unit:
  - Test valid invalidation below entry -> chosen as stop, `stop_source == "invalidation"`.
  - Test invalidation missing -> ATR fallback chosen when valid.
  - Test invalidation present but `NaN`/`inf`/`-inf` -> ignored, ATR fallback used if valid.
  - Test invalidation >= entry -> ignored, ATR fallback used if valid.
  - Test no valid invalidation and no valid ATR fallback -> all risk outputs `null`.
  - Test `risk_acceptable` remains `null` when target derivation is unavailable.
  - Test nullable tri-state fields are not coerced to `false`.
- Integration:
  - Regression test for a TRX-style fixture where report/setup no longer disagree about effective stop/RR semantics.
  - Regression test ensuring decision reasons do not claim risk unattractive based on a hidden alternate stop.
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` examples/expectations if any sample outputs change.

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges remain clamped to 0..100 where already specified
- Decision policy thresholds are not changed by this ticket
- Long-only stop validity remains “strictly below entry”

- [ ] Preserve existing config semantics/defaults
- [ ] Preserve existing pipeline boundaries
- [ ] Preserve decision threshold values and ordering logic

## Definition of Done
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if logic/output examples changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-12T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
