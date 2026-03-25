> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P0] Repair canonical authority boundaries and restore runnable README onboarding

## Context / Source
The deployed bootstrap ticket established the Independence-Release repo structure and created the new canonical documentation skeleton, but two documentation-contract defects remain:

1. legacy-track pipeline/output contracts still sit under `docs/canonical/` while `docs/canonical/AUTHORITY.md` still declares all `docs/canonical/*` content as single-source-of-truth, which re-promotes legacy architecture contracts as active Independence-Release requirements;
2. the top-level `README.md` no longer fulfills its onboarding role if it does not contain concrete install/config/run guidance for the currently runnable repository state.

This follow-up ticket repairs those defects without reopening the bootstrap scope broadly.

**Primary authoritative references for this ticket**
- `independence_release_gesamtkonzept_final.md` §1, §2.1, §4.1, §5, §19
- `docs/readme_guide.md`
- `docs/canonical/AUTHORITY.md`
- the deployed bootstrap ticket `2026-03-23__P0__bootstrap_independence_release_repo_cleanup.md`

`depends_on: [2026-03-23__P0__bootstrap_independence_release_repo_cleanup]`

## Goal
After this ticket is completed, the repository must have a deterministic and contradiction-free documentation authority model:

1. the 7 uploaded Abschnittsdateien plus `independence_release_gesamtkonzept_final.md` are explicitly treated as the fachliche authority for Independence-Release wherever the repo canonical docs summarize or operationalize them;
2. legacy scanner contracts that remain useful as reference do not continue to appear as active Independence-Release single-source-of-truth merely because they are physically located under `docs/canonical/`;
3. `README.md` is again a runnable onboarding document for the repository’s current executable state and clearly distinguishes current legacy runtime usage from the Independence-Release rebuild target;
4. no second competing documentation truth is introduced.

## Scope
Allowed changes for this ticket:

- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md` if needed to reflect repaired authority boundaries
- `docs/canonical/SCOPE.md` if needed to align wording with the repaired authority model
- legacy-track canonical docs that are currently misleadingly primary for Independence-Release, including if needed:
  - `docs/canonical/PIPELINE.md`
  - `docs/canonical/OUTPUT_SCHEMA.md`
  - `docs/canonical/DECISION_LAYER.md`
  - `docs/canonical/REPORTS.md`
  - other legacy-architecture contracts under `docs/canonical/**` that still claim primary applicability to the old scanner architecture
- `docs/legacy/**` for moves or archival stubs if needed
- `README.md`
- `docs/tickets/**` only as required by `docs/canonical/WORKFLOW_CODEX.md`

## Out of Scope
- Implementing or changing scanner business logic
- Rewriting the Independence-Release architecture docs beyond what is needed to repair authority boundaries
- Reintroducing old scanner architecture as the target model
- Changing runtime code, config parsing, bar clock logic, storage logic, or tests unrelated to documentation validation
- Inventing new business formulas, schemas, thresholds, or output contracts not already defined in the authoritative documents
- Manually editing `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`

## Canonical References (important)
- `independence_release_gesamtkonzept_final.md` §1, §2.1, §4.1, §5, §19
- `docs/readme_guide.md`
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/tickets/_TEMPLATE.md`
- `2026-03-23__P0__bootstrap_independence_release_repo_cleanup.md`

> If the current authoritative reference, Canonical, and existing code conflict, the authoritative reference wins. If additional clarification is needed, extend the ticket or ask the user rather than interpret.

## Proposed change (high-level)

### Before
- `docs/canonical/AUTHORITY.md` still states that all `docs/canonical/*` files are canonical single-source-of-truth.
- Some old scanner pipeline/output/decision contracts still live under `docs/canonical/` and can therefore be misread by Codex or future maintainers as active Independence-Release requirements.
- `README.md` may no longer contain concrete installation, configuration, and run instructions for the repository’s current runnable state.

### After
- The canonical authority model explicitly distinguishes:
  - authoritative Independence-Release fachliche basis: the 7 Abschnittsdateien + Gesamtkonzept,
  - repo-canonical operationalization docs for the new architecture,
  - legacy/reference contracts that remain useful but are not active Independence-Release SoT.
- Legacy-track contracts no longer remain silently primary merely because of path placement.
- `README.md` again contains concrete onboarding content for the currently runnable repo state and states clearly that the old runtime is legacy/reference while Independence-Release is the new target architecture.

### Edge cases
- A document may remain physically under `docs/canonical/` only if its scope is explicitly narrowed and it cannot be mistaken for active Independence-Release truth.
- If a legacy contract is still required for operating the pre-existing legacy runtime from this checkout, that does not make it authoritative for Independence-Release.
- README must not become a technical spec; it must remain onboarding-oriented per `docs/readme_guide.md`.
- Do not create ambiguous wording such as “canonical for legacy compatibility” without also specifying whether the file is active for Independence-Release, legacy-only, or superseded.

### Backward compatibility impact
This ticket changes documentation authority semantics and README onboarding only. It does not change scanner outputs or runtime logic directly, but it intentionally removes misleading documentation authority from legacy architecture contracts.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)

- **Docs-first:** Update `AUTHORITY.md` and any affected canonical index/scope framing before moving or relabeling legacy-track contracts.
- **No mixed truth:** There must be no state in which a legacy scanner contract is simultaneously marked or implied as active Independence-Release single-source-of-truth.
- **Explicit status wording:** Every touched legacy-track contract must end in one explicit state only:
  - active Independence-Release canonical,
  - legacy-reference only,
  - or superseded / replaced by a named document.
- **Path and status must agree:** Do not leave a file under a path or header state that implies stronger authority than its real role.
- **README remains onboarding:** Keep README concise and runnable. Do not turn it into a spec dump or changelog.
- **Current repo reality matters:** README instructions must reflect what can actually be installed/configured/run from the current checkout at the time of the PR.
- **No auto-doc edits:** `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` remain read-only.
- **No business-logic drift:** This ticket must not touch scanner runtime code.

## Implementation Notes

### Authority-model repair (mandatory)
Codex must remove the contradiction in which `docs/canonical/AUTHORITY.md` says all `docs/canonical/*` files are SoT while some files in that tree are intentionally legacy-only or compatibility-only.

Codex must choose one coherent repair strategy and apply it consistently across touched files:

#### Allowed strategy A — move legacy contracts out of `docs/canonical/`
- move legacy-only contracts to `docs/legacy/**` (preserving discoverability),
- update references/indexes accordingly,
- ensure no remaining canonical index points to them as active Independence-Release requirements.

#### Allowed strategy B — keep path, but explicitly narrow authority in a machine-readable and human-readable way
This strategy is allowed only if all of the following are true:
- `AUTHORITY.md` is updated so `docs/canonical/*` is no longer treated as a flat undifferentiated SoT bucket;
- the affected files themselves clearly state `legacy-reference only` or equivalent at the top;
- `INDEX.md` and any cross-references make clear that these files are not active Independence-Release requirements;
- there is no remaining wording that could reasonably cause Codex to treat them as active requirements for new tickets.

If strategy B cannot be made unambiguous, use strategy A instead.

### Files that must be checked explicitly
At minimum, inspect and classify the following if they exist:
- `docs/canonical/PIPELINE.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/REPORTS.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/AUTHORITY.md`

For each touched file, make its role explicit:
- `active_independence_release`
- `legacy_reference_only`
- `superseded_by:<path>`

These exact tags do not need to be exposed as YAML unless the file format already uses a machine header, but the semantic classification must be unambiguous in the file content.

### README repair (mandatory)
`README.md` must once again contain, at minimum:

1. a short repository description that distinguishes:
   - currently runnable repo state,
   - Independence-Release as target architecture,
   - legacy scanner/runtime status;
2. installation instructions;
3. configuration instructions;
4. run instructions with at least one concrete CLI example that matches current repo reality;
5. a short section explaining where to find canonical docs / deeper architecture docs;
6. output/report orientation at a high level;
7. optional note on scheduling if it can be stated truthfully from current repo reality.

README must not:
- restate formulas or deep spec details,
- contain fake future run instructions for not-yet-implemented Independence-Release runtime,
- omit concrete install/config/run information.

### Missing vs invalid semantics
This ticket changes documentation only, but it still must avoid semantic drift:

- missing legacy classification in a touched file is invalid; do not leave touched ambiguous files unclassified;
- missing README sections listed above is invalid;
- if a run mode or config instruction is no longer valid in the current repo, remove or replace it rather than leaving stale examples.

## Acceptance Criteria (deterministic)

1. `docs/canonical/AUTHORITY.md` no longer states or implies that every file under `docs/canonical/*` is automatically an active Independence-Release single-source-of-truth without scope distinction.
2. No touched legacy-track contract remains both:
   - located/presented as canonical primary truth,
   - and described as legacy/reference-only.
3. For every touched legacy-track contract, the file role is explicit and contradiction-free:
   - active Independence-Release canonical,
   - legacy-reference only,
   - or superseded by a named document/path.
4. `docs/canonical/INDEX.md` and any touched cross-references do not present legacy-only contracts as active Independence-Release requirements.
5. `README.md` contains concrete sections for installation, configuration, and running the repository, in accordance with `docs/readme_guide.md`.
6. `README.md` clearly distinguishes current runnable repo usage from the Independence-Release target architecture.
7. `README.md` does not contain fake or future-only commands for non-implemented Independence-Release runners.
8. `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` are not manually modified.
9. The PR archives the ticket in the same PR according to `docs/canonical/WORKFLOW_CODEX.md`.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)

- **Config Defaults (Missing key → Default):** ✅ N/A — no runtime config parsing is introduced
- **Config Invalid Value Handling:** ✅ N/A — no runtime config validation is introduced
- **Nullability / kein bool()-Coercion:** ✅ N/A — no runtime output fields are introduced
- **Not-evaluated vs failed getrennt:** ✅ covered at document-classification level — legacy-reference-only is not the same as active Independence-Release canonical
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ applicable at docs level — touched authority/index files must be updated in the same PR so no contradictory intermediate doc state is merged
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ N/A
- **Deterministische Sortierung/Tie-breaker:** ✅ N/A

## Tests (required if logic changes)

### Unit
- If the repo has a docs-validation or lint pattern, add/update a lightweight validation test or script assertion that fails when a touched legacy-track canonical file remains unclassified or when `AUTHORITY.md` still declares flat canonical precedence that contradicts file-level role classification.
- If no such pattern exists, add a minimal deterministic test or validation script under the repo’s existing test/tooling conventions.

### Integration
Add or update at least one deterministic documentation validation that checks:
- `README.md` contains installation, configuration, and run sections;
- `AUTHORITY.md` no longer declares flat undifferentiated canonical truth if legacy-only canonical-path files still exist;
- touched legacy-track files have explicit classification.

### Golden fixture / verification
Not required for business logic. A PR verification checklist or deterministic docs-validation script is sufficient.

## Constraints / Invariants (must not change)

- [ ] The 7 uploaded Abschnittsdateien plus `independence_release_gesamtkonzept_final.md` remain the fachliche authority for Independence-Release
- [ ] Legacy scanner docs do not regain implied primary authority for new Independence-Release tickets
- [ ] README remains an onboarding document, not a spec replacement
- [ ] No scanner runtime code is changed in this ticket
- [ ] `docs/code_map.md` remains read-only
- [ ] `docs/GPT_SNAPSHOT.md` remains read-only
- [ ] One PR, one documentation-repair change set only

## Preflight self-check
- [x] Current sole reference identified
- [x] Canonical collision check performed
- [x] No competing truth introduced
- [x] Missing vs invalid semantics made explicit where relevant
- [x] Deterministic acceptance criteria defined
- [x] Tests/validation expectations stated
