> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Canonicalize risk config naming to `min_rr_to_target_1` and remove misleading `trade_levels` responsibility wording

## Context / Source
- The recent RR/target cleanup and invalidation-first stop alignment have been implemented and are active in current runs (`canonical_schema_version: 6.1.0`).
- Remaining repo-level inconsistencies still exist:
  1. risk config and some docs/code still use the legacy key name `risk.min_rr_to_tp10`, while runtime/output semantics now use target-index naming (`rr_to_target_1`, `rr_to_target_2`).
  2. `scanner/pipeline/scoring/trade_levels.py` still contains the misleading module description “output-only, no scoring impact”, although its risk fields are consumed by downstream decision logic.
- This ticket is intentionally narrow: it is for naming/semantic cleanup only, not for timing logic or threshold tuning.

## Goal
After this change:
- the canonical risk config key is `risk.min_rr_to_target_1`
- canonical docs, config examples, and code comments use target-index semantics consistently
- legacy `risk.min_rr_to_tp10` does not remain the primary truth
- `trade_levels.py` accurately describes its downstream role in risk/decision preparation

## Scope
Allowed files/modules to modify:
- `scanner/pipeline/scoring/trade_levels.py`
- `scanner/config.py`
- `config/config.yml`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/code_map.md`
- `docs/AGENTS.md` only if it explicitly documents the old key/semantics
- relevant tests under `tests/`

## Out of Scope
- No timing/entry-state changes
- No threshold value changes
- No stop-derivation changes
- No decision policy changes
- No removal of other legacy `tp10/tp20` historical references outside the exact config/docs/comment scope touched by this ticket unless they directly misdescribe active behavior

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- Active RR/risk semantics use `target_1` / `target_2`, but config still exposes `risk.min_rr_to_tp10`.
- Readers and future editors can misread the system as still anchored to “TP10” semantics.
- `trade_levels.py` advertises itself as output-only / not scoring-impacting, which is false or at least materially misleading.

After:
- Introduce and document the canonical config key:
  - `risk.min_rr_to_target_1`
- Keep `risk.min_rr_to_tp10` as a temporary backward-compatible alias for exactly one migration phase in code.
- Resolution order is explicit and deterministic:
  1. if `risk.min_rr_to_target_1` is present and valid, use it
  2. else if `risk.min_rr_to_tp10` is present and valid, use it as a legacy alias
  3. else use the existing default threshold value
- If both keys are present and both valid, `min_rr_to_target_1` wins.
- If both keys are present and the canonical key is valid but the legacy key is invalid, still use the canonical key; do not fail because of the losing legacy alias.
- If the canonical key is present but invalid, fail clearly even if the legacy key is valid. The canonical key is authoritative when present.
- Update `config/config.yml` examples to use `min_rr_to_target_1`.
- Update canonical docs and code-map references to use `min_rr_to_target_1`.
- Replace misleading module-level wording in `trade_levels.py` with an accurate description of its role in trade-level derivation and phase-1 risk field preparation for downstream consumers.

Edge cases:
- Missing key is not the same as invalid key.
- Partial nested `risk` overrides still follow the repo’s existing merge/default behavior; do not introduce block-replacement semantics unless central config already does so.
- Invalid numeric values (`None`, non-numeric strings, `NaN`, `inf`, `-inf`) must continue to fail clearly where current config validation expects numeric finite values.
- This ticket must not silently change the default threshold value.

Backward compatibility impact:
- Runtime remains backward compatible for one migration phase via the legacy alias.
- Canonical docs and sample config switch immediately to `min_rr_to_target_1`.
- No silent competing truths: canonical key is the only documented key after this ticket.

## Codex Implementation Guardrails (No-Guesswork, Pflicht)
- **Config/Defaults:** Reuse central config/default handling already present in `ScannerConfig` / config accessors. Do not invent ad-hoc defaults in a leaf module if a central accessor exists.
- **Missing vs Invalid:** Explicitly preserve the distinction:
  - missing canonical key
  - invalid canonical key
  - missing legacy alias
  - invalid legacy alias
  - both present
- **Merge vs Replace:** Nested `risk` overrides continue to follow existing repo behavior. Do not change config merge semantics in this ticket.
- **Canonical precedence:** `risk.min_rr_to_target_1` is authoritative whenever present.
- **Legacy alias behavior:** `risk.min_rr_to_tp10` is a compatibility alias only. It must not remain documented as canonical.
- **Nullability / bool coercion:** No new nullable output fields are introduced here. Do not use `bool(...)` to infer config presence or numeric validity.
- **Non-finite numerics:** `NaN`, `inf`, `-inf` remain invalid numeric config values and must not be normalized into accepted thresholds.
- **Not-evaluated vs failed:** This is a config-semantics ticket. Missing key may use default; invalid provided key must fail clearly per acceptance criteria below.
- **Determinism:** Same input config produces same resolved threshold every time. No warning/order ambiguity.
- **Repo reuse:** Reuse existing helpers and validation paths rather than introducing a second config reader for the same key.

## Implementation Notes
- In `scanner/pipeline/scoring/trade_levels.py`, stop reading `min_rr_to_tp10` as the primary conceptual key.
- Prefer moving the key resolution into central config access if practical and consistent with existing config architecture. If not practical within this PR, implement one deterministic resolution helper and reuse it.
- Update references in:
  - `config/config.yml`
  - canonical docs
  - any verification examples
  - code map
- Update the module docstring/comment in `trade_levels.py` so it clearly states that the module derives setup trade levels and phase-1 risk fields consumed by downstream output/decision layers.
- If there are tests or tools that still assert the old key name as canonical, update them.
- If warning infrastructure already exists for deprecated config keys, emit a deprecation warning when only the legacy alias is used. If no warning infrastructure exists, do not invent a large logging subsystem in this ticket; a small localized warning is acceptable only if already idiomatic in the repo.
- Do not rename runtime output fields in this ticket; those were already handled in prior tickets. This ticket is about config naming and descriptive text consistency only.

## Acceptance Criteria (deterministic)
1. The canonical documented risk config key is `risk.min_rr_to_target_1`; `risk.min_rr_to_tp10` is no longer documented as canonical in active docs/config examples.
2. If only `risk.min_rr_to_target_1` is present and valid, the runtime uses it.
3. If only `risk.min_rr_to_tp10` is present and valid, the runtime accepts it as a legacy alias and resolves the same threshold value.
4. If both keys are present and both are valid, the runtime uses `risk.min_rr_to_target_1`.
5. If `risk.min_rr_to_target_1` is present but invalid, config loading fails clearly even if `risk.min_rr_to_tp10` is also valid.
6. If `risk.min_rr_to_target_1` is absent and `risk.min_rr_to_tp10` is present but invalid, config loading fails clearly.
7. If both keys are absent, the existing default threshold value is used unchanged.
8. `trade_levels.py` no longer describes itself as “output-only, no scoring impact”; its description reflects that it prepares trade levels and downstream-consumed phase-1 risk fields.
9. Canonical docs and verification/examples are updated consistently with the new canonical config key.
10. Tests explicitly cover missing key, canonical key valid, legacy alias valid, canonical-vs-legacy precedence, and invalid numeric config values.

## Default-/Edgecase-Abdeckung (Pflicht)
- **Config Defaults (Missing key -> Default):** ✅ (AC: #7; Test: missing both keys uses existing default unchanged)
- **Config Invalid Value Handling:** ✅ (AC: #5/#6; Test: invalid canonical and invalid legacy alias fail clearly)
- **Nullability / kein bool()-Coercion:** ✅ (N/A for outputs; relevant for config presence detection only — Test: presence/absence checked explicitly, not via truthiness)
- **Not-evaluated vs failed getrennt:** ✅ (AC: #5/#6/#7; Test: missing key uses default, invalid key fails)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write mode feature introduced)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (N/A for ranking; relevant determinism is config precedence — AC: #4)

## Tests (required)
- Unit:
  - Test: config with only `risk.min_rr_to_target_1` resolves expected threshold.
  - Test: config with only `risk.min_rr_to_tp10` resolves expected threshold via legacy alias.
  - Test: config with both keys valid resolves canonical key value.
  - Test: config with canonical key invalid and legacy key valid fails clearly.
  - Test: config with canonical key missing and legacy key invalid fails clearly.
  - Test: config with both keys absent resolves the existing default unchanged.
  - Test: non-finite values (`NaN`, `inf`, `-inf`) are rejected for both canonical and legacy keys.
- Integration:
  - Regression test that a real risk-field derivation path uses the same resolved threshold regardless of whether config is supplied under canonical key or legacy alias.
- Golden fixture / verification:
  - Update `docs/canonical/VERIFICATION_FOR_AI.md` examples if config snippets or canonical field naming examples change.

## Constraints / Invariants (must not change)
- No timing logic changes
- No stop derivation changes
- No decision threshold value changes
- No changes to closed-candle-only / no-lookahead invariants
- No new competing risk-threshold keys beyond the temporary documented legacy alias behavior
- Existing default threshold numeric value must remain unchanged in this ticket

- [ ] Preserve existing nested config merge semantics
- [ ] Preserve existing default numeric threshold value
- [ ] Preserve existing runtime behavior when no relevant key is provided

## Definition of Done
- [ ] Implemented code/doc changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/`
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if examples changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-13T00:00:00Z"
priority: P1
type: refactor
owner: codex
related_issues: []
```
