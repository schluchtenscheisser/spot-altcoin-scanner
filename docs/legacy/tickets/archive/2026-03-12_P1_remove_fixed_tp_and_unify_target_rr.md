> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Remove fixed +10%/+20% take-profit projections and unify target-based RR naming

## Context / Source
- This ticket addresses a verified inconsistency between setup-internal risk fields and trade-candidate report fields.
- Current behavior uses setup-specific target levels in scoring/risk, but `scanner/pipeline/output.py` also computes separate fixed +10%/+20% TP projections and writes them into overlapping semantic fields.
- User decision: fixed `+10%` / `+20%` projections must be removed completely from formulas, field names, and docs. Only potential setup target levels remain authoritative.

## Goal
After this change, the codebase exposes only setup-target-based target/RR semantics. There must be no fixed-percentage TP projections in code, output fields, or canonical docs.

## Scope
Allowed files/modules to modify:
- `scanner/pipeline/output.py`
- `scanner/pipeline/scoring/trade_levels.py`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- relevant tests under `tests/`

## Out of Scope
- No change yet to stop derivation semantics (that is handled in a follow-up ticket).
- No tuning of config thresholds.
- No change to setup scoring formulas except field naming / report semantics cleanup.
- No unrelated schema cleanups beyond fields directly impacted by this ticket.

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- Output layer computes canonical/fixed TP prices from entry (`entry * 1.10`, `entry * 1.20`).
- Output layer publishes fixed-percentage RR fields with names that collide semantically with setup-target-based RR semantics.
- Report readers can see contradictory values for “rr_to_tp10/20”.

After:
- Remove fixed +10% and +20% TP projection code paths entirely.
- Remove any fields that represent fixed-percentage TP projections.
- Rename setup-target-based fields to canonical target-index semantics:
  - `rr_to_tp10` -> `rr_to_target_1`
  - `rr_to_tp20` -> `rr_to_target_2`
  - if price fields exist in outputs for targets, use `target_1_price`, `target_2_price`, `target_3_price`
- Reports/JSON/Excel/Markdown must expose only setup-target-derived target/RR fields.
- Canonical docs must describe only target-level semantics, not fixed percentage semantics.

Edge cases:
- If fewer than two setup targets exist, `rr_to_target_2` remains `null`; do not coerce to `false` or `0`.
- If targets are missing / malformed / non-finite, output fields remain nullable and must not produce synthetic fixed-percentage substitutes.
- Any consumer-facing field removal/rename must be reflected in canonical docs and tests.

Backward compatibility impact:
- This is a deliberate schema change. Old fixed-TP fields are removed rather than aliased.
- Do not silently preserve legacy aliases in outputs unless a canonical doc explicitly requires it. No such alias is requested here.

## Codex Implementation Guardrails (No-Guesswork)
- **Config/Defaults:** This ticket does not introduce new config keys. If existing config is read during touched paths, reuse central config/default handling. Missing key != invalid key.
- **Nullability:** `rr_to_target_1`, `rr_to_target_2`, and any target price fields are nullable. `null` means “not evaluable / unavailable”, not `false`.
- **No bool() coercion:** Do not coerce nullable numeric outputs through `bool(...)`.
- **Strict/Preflight:** If canonical docs or verification fixtures are updated, keep them in sync before marking done.
- **Not-evaluated vs failed:** Missing target derivation remains distinct from negative evaluation. No synthetic fallback targets may blur this distinction.
- **Determinism:** Preserve existing deterministic ordering/tie-break behavior. This ticket must not change ranking/sorting.
- **Repo reuse:** Reuse existing setup target derivation already present in scoring outputs; do not introduce a second truth.

## Implementation Notes
- In `scanner/pipeline/output.py`, remove helper logic that computes fixed canonical TP prices from entry.
- Remove any helper/functions dedicated to fixed 10% / 20% TP projections.
- Update trade-candidate building so reported RR fields are sourced exclusively from already-derived setup-target-based risk fields / target levels.
- If the output layer currently reconstructs RR independently, replace that with pass-through or deterministic derivation from setup target levels only.
- Update markdown/json/excel-facing naming consistently.
- Update any report formatting labels and section names that still mention TP10 / TP20 if those labels refer to fixed-percentage semantics.
- Audit docs for “+10%/+20%”, “TP10”, “TP20” where they mean fixed projections and remove/replace them.
- If docs still want ordinal targets, use “target_1/2/3”.

## Acceptance Criteria (deterministic)
1. No code path in `scanner/` computes fixed take-profit prices from `entry * 1.10` or `entry * 1.20`.
2. No user-facing output field in JSON/Markdown/Excel represents a fixed-percentage TP projection.
3. Output and report field names use target-index semantics (`target_1`, `target_2`, optionally `target_3`) rather than overloaded `tp10`/`tp20` names.
4. For any candidate with valid setup targets, reported RR fields are derived only from those setup targets.
5. For any candidate with missing / malformed / non-finite target values, the corresponding target/RR output fields remain `null` and no fixed fallback is introduced.
6. Canonical docs no longer describe fixed +10%/+20% TP logic anywhere as active behavior.
7. Existing deterministic ordering of candidates is unchanged by this ticket.
8. Tests cover field removal/rename and ensure no fixed-TP fallback remains.

## Default-/Edgecase-Abdeckung
- **Config Defaults (Missing key -> Default):** ✅ (N/A – ticket adds no config)
- **Config Invalid Value Handling:** ✅ (N/A – ticket adds no config)
- **Nullability / kein bool()-Coercion:** ✅ (AC: #5; Test: nullable target/RR fields stay `null`)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #5; Test: missing target data does not create synthetic RR)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no write-mode/preflight feature introduced)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (AC: #7; Test: stable ordering regression test)

## Tests (required)
- Unit:
  - Add/adjust tests that fail if fixed-percentage TP helper logic is still present in output derivation.
  - Test: candidate with valid setup targets exposes `rr_to_target_1` / `rr_to_target_2` and does not expose legacy fixed-TP fields.
  - Test: candidate with only one target yields `rr_to_target_2 = null`.
  - Test: malformed/non-finite targets yield nullable output fields, not numeric placeholders.
- Integration:
  - Regression fixture for a candidate like TRX-style case where setup-derived target RR appears consistently across output layers.
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` if output field names/schema examples change.
  - Update any golden JSON/report fixtures referenced by tests.

## Constraints / Invariants (must not change)
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges remain clamped to 0..100 where already specified
- No new fixed-percentage TP semantics introduced under a different alias

- [ ] Preserve existing pipeline stage boundaries
- [ ] Preserve existing decision thresholds/config behavior
- [ ] Preserve nullable semantics for unevaluable numeric fields

## Definition of Done
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if output examples/schema changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-12T00:00:00Z"
priority: P1
type: refactor
owner: codex
related_issues: []
```
