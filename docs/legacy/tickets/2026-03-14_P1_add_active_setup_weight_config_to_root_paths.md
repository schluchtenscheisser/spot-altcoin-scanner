> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Add active setup-weight config blocks to `config/config.yml` using the implemented root-level paths

## Context / Source
- The setup-weight activation code has already been implemented in `scanner/pipeline/global_ranking.py`.
- Review of the current implementation confirms the exact config read paths are:
  - `phase_policy.setup_weights_active`
  - `setup_weights_by_category`
  - optional fallback mapping: `setup_id_to_weight_category_active`
- The current active `config/config.yml` does not contain the required root-level weight block, so the runtime falls back to default behavior:
  - `setup_weights_active` defaults to `false`
  - or weights resolve to default `1.0`
- As a result, recent runs show no meaningful ranking shift from the setup-weight feature even though the code exists.
- This ticket is intentionally narrow: it does **not** modify ranking code, formulas, or docs logic. It only adds the missing active config keys at the correct implemented paths.

## Goal
After this change:
- the active runtime config enables setup-weight application in global ranking
- breakout / pullback / reversal weights are read from the exact root-level keys that the implemented code already consumes
- future runs can be verified by observing `setup_weight` values of:
  - `1.0` for breakout
  - `0.9` for pullback
  - `0.8` for reversal
- no alternate `global_ranking.*` config tree is introduced

## Scope
Allowed files/modules to modify:
- `config/config.yml`
- `docs/canonical/CONFIGURATION.md` only if the active sample config/examples must be aligned to the already-implemented runtime paths
- `docs/canonical/CHANGELOG.md` if config examples or canonical activation notes are updated
- `docs/canonical/VERIFICATION_FOR_AI.md` only if verification examples explicitly reference the active config snippet

## Out of Scope
- No code changes in `scanner/pipeline/global_ranking.py`
- No changes to setup-weight formulas or ranking behavior
- No changes to score scales, tie-breakers, or top-20 selection logic
- No migration to a `global_ranking.*` config subtree
- No changes to setup-weight values beyond the explicitly requested activation values
- No changes to execution gates, risk model, confirmation logic, or timing logic

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/CONFIGURATION.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CHANGELOG.md`
- `docs/canonical/VERIFICATION_FOR_AI.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Before:
- runtime code reads setup-weight activation from root-level config paths
- active `config/config.yml` is missing the required root-level block
- runtime therefore behaves as if setup weights are disabled or weight values are missing, defaulting effectively to `1.0`

After:
- add the following root-level block to `config/config.yml`:

```yaml
phase_policy:
  setup_weights_active: true

setup_weights_by_category:
  breakout: 1.0
  pullback: 0.9
  reversal: 0.8
```

- do **not** nest this under `global_ranking`
- do **not** rename `breakout` to `breakout_trend`
- preserve existing unrelated config content and structure

Edge cases:
- If `phase_policy` already exists in `config/config.yml`, add/merge `setup_weights_active: true` into the existing block rather than duplicating the block.
- If `setup_weights_by_category` already exists, update it in place to the specified values rather than creating a second copy.
- If `setup_id_to_weight_category_active` already exists elsewhere, leave it untouched in this ticket unless a doc/example must mention its continued optional role.
- Missing unrelated keys remain unchanged; this ticket must not reformat or normalize unrelated config sections.

Backward compatibility impact:
- This is an activation/config-completion change, not a new feature introduction.
- Runtime behavior will intentionally change in subsequent runs because the already-implemented code path will now receive non-default values.
- No second config truth may be introduced.

## Codex Implementation Guardrails (No-Guesswork, Pflicht)
- **Config/Defaults:** Reuse the existing implemented runtime paths exactly as they are currently read in `scanner/pipeline/global_ranking.py`. Do not invent a new config subtree and do not rewrite code to match a different config structure.
- **Exact paths:** The ticket must use:
  - `phase_policy.setup_weights_active`
  - `setup_weights_by_category.breakout`
  - `setup_weights_by_category.pullback`
  - `setup_weights_by_category.reversal`
- **Missing vs invalid:** This ticket is a config-file completion task, not a config-validation redesign. Missing unrelated keys stay untouched. Do not broaden scope into validation logic changes.
- **Merge vs replace:** Partial nested edits in `config/config.yml` must be field-wise merged into existing blocks. Do not replace the entire `phase_policy` block if other keys are present.
- **No alternate truth:** Do not add `global_ranking.setup_weights`, `global_ranking.phase_policy`, or any alias block in `config/config.yml`.
- **No semantic renaming:** Use `breakout`, `pullback`, `reversal` exactly, because the implemented lookup uses the `setup_type` loop key values.
- **Determinism:** The final YAML content must be stable and unambiguous; no duplicate keys and no parallel weight blocks.
- **Repo reuse:** If canonical docs/examples already mention a different inactive or legacy naming, update only as necessary to avoid contradiction with the implemented runtime path.

## Implementation Notes
- Inspect the existing `config/config.yml` structure before editing.
- If `phase_policy:` already exists, insert/update only:
  - `setup_weights_active: true`
- Add/update the root-level `setup_weights_by_category:` mapping with:
  - `breakout: 1.0`
  - `pullback: 0.9`
  - `reversal: 0.8`
- Preserve YAML ordering/style as much as practical; do not perform repo-wide formatting churn.
- If docs are updated, ensure they match the actual implemented code path rather than the previously discussed but non-implemented `global_ranking.*` idea.

## Acceptance Criteria (deterministic)
1. `config/config.yml` contains `phase_policy.setup_weights_active: true` at the root-level path used by the current implementation.
2. `config/config.yml` contains a root-level `setup_weights_by_category` block with exactly:
   - `breakout: 1.0`
   - `pullback: 0.9`
   - `reversal: 0.8`
3. No `global_ranking.*` setup-weight block is introduced by this ticket.
4. No duplicate `phase_policy` block or duplicate `setup_weights_by_category` block is created.
5. Existing unrelated keys in `config/config.yml` remain unchanged.
6. If canonical config examples/docs are touched, they match the implemented root-level runtime path.
7. The resulting config is sufficient for a subsequent run to emit non-default `setup_weight` values such as:
   - `1.0` for breakout rows
   - `0.9` for pullback rows
   - `0.8` for reversal rows

## Default-/Edgecase-Abdeckung (Pflicht)
- **Config Defaults (Missing key -> Default):** ✅ (AC: #1/#2/#7; Test: before/after config snippet shows that missing active keys are now explicitly set and no runtime-default-only behavior remains for these fields)
- **Config Invalid Value Handling:** ✅ (N/A – ticket does not change validation logic; values written are valid finite positive floats)
- **Nullability / kein bool()-Coercion:** ✅ (N/A – no nullable output logic changed by this ticket)
- **Not-evaluated vs failed getrennt:** ✅ (N/A – no gating/decision-state logic changed)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – no strict write-mode feature introduced)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A – not relevant)
- **Deterministische Sortierung/Tie-Breaker:** ✅ (N/A for ranking code; relevant determinism here is unique, non-duplicated config keys per AC: #3/#4)

## Tests (required)
- Unit:
  - N/A – this ticket performs config-file activation only, no logic change in Python code.
- Integration:
  - Add/update one lightweight verification step or documented manual verification note in `docs/canonical/VERIFICATION_FOR_AI.md` if that file already tracks run-level verification:
    - after this config change, a subsequent run should show non-default `setup_weight` values by setup type
- Golden fixture / verification:
  - If config examples or verification examples are documented canonically, update them to the implemented root-level path.
  - Manual verification target for the next run:
    - at least one reversal row shows `setup_weight: 0.8`
    - at least one pullback row shows `setup_weight: 0.9`
    - breakout rows retain `setup_weight: 1.0`

## Constraints / Invariants (must not change)
- No Python ranking code changes
- No score formula changes
- No new config subtree under `global_ranking`
- No renaming of setup categories away from `breakout`, `pullback`, `reversal`
- No unrelated config refactors

- [ ] Preserve existing config structure outside the touched keys
- [ ] Preserve implemented runtime lookup paths exactly
- [ ] Preserve all unrelated ranking/decision behavior

## Definition of Done
- [ ] Updated `config/config.yml` per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` only if examples/verification needed alignment
- [ ] Updated `docs/canonical/VERIFICATION_FOR_AI.md` if verification examples changed
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-14T00:00:00Z"
priority: P1
type: bugfix
owner: codex
related_issues: []
```
