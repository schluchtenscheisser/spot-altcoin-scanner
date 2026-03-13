> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket for Codex — Single writer workflow for auto-docs

> Generated for repo `schluchtenscheisser/spot-altcoin-scanner`.
> Basis: `docs/tickets/_TEMPLATE.md`, `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`, `docs/AGENTS.md`,
> `.github/workflows/generate-gpt-snapshot.yml`, `.github/workflows/update-code-map.yml`.

---

## Title
[P1] Consolidate auto-doc writes into exactly one GitHub Actions workflow and one commit path

## Context / Source
- Today two workflows can write auto-generated docs on `main`:
  - `.github/workflows/generate-gpt-snapshot.yml`
  - `.github/workflows/update-code-map.yml`
- This creates a non-fast-forward failure path:
  1. `generate-gpt-snapshot.yml` commits `docs/GPT_SNAPSHOT.md` to `main`
  2. `update-code-map.yml` starts from an older event SHA / checkout base
  3. `update-code-map.yml` creates a local commit for `docs/code_map.md`
  4. push is rejected because `origin/main` moved meanwhile
- The target state is: exactly **one** workflow writes both auto-doc files, and no second workflow may auto-commit either file.

## Goal
After this change:
- exactly one workflow is allowed to write `docs/code_map.md` and `docs/GPT_SNAPSHOT.md`
- both files are generated in the same workflow run
- if changes are detected, both files are committed through a single auto-commit step
- the old second write path is removed so Codex/CI cannot reintroduce the race by accident

## Scope
Allowed files for this ticket:
- `.github/workflows/generate-gpt-snapshot.yml`
- `.github/workflows/update-code-map.yml`
- `scripts/update_codemap.py` (only if a small invocation/interface adjustment is required; otherwise leave unchanged)
- `docs/AGENTS.md` (only if needed to clarify the sole-writer workflow path; keep changes minimal)
- `docs/tickets/...` lifecycle moves per `docs/canonical/WORKFLOW_CODEX.md`

## Out of Scope
- No change to the content model or semantics of `docs/code_map.md`
- No change to the content model or semantics of `docs/GPT_SNAPSHOT.md`
- No change to scanner logic, scoring, ranking, canonical formulas, or output schema
- No new reusable workflow abstraction
- No manual editing of the generated auto-doc files themselves

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/WORKFLOW_CODEX.md`
- `docs/AGENTS.md`

## Mandatory authority sentence
> Wenn die aktuelle alleinige Referenz, Canonical und bestehender Code kollidieren, gewinnen die autoritativen Vorgaben. Bei zusätzlichem Klärungsbedarf Ticket ergänzen oder User fragen statt interpretieren.

## Proposed change (high-level)
Before:
- `generate-gpt-snapshot.yml` writes `docs/GPT_SNAPSHOT.md`
- `update-code-map.yml` writes `docs/code_map.md`
- `update-code-map.yml` is additionally triggered by `workflow_run` after `gpt-snapshot`
- both workflows can perform commits to `main`

After:
- `generate-gpt-snapshot.yml` becomes the **only** writer workflow for both auto-doc files
- the workflow must:
  1. checkout `main` with full history
  2. generate `docs/code_map.md`
  3. generate `docs/GPT_SNAPSHOT.md`
  4. detect changes across both files
  5. create at most one commit touching `docs/code_map.md` and/or `docs/GPT_SNAPSHOT.md`
- `.github/workflows/update-code-map.yml` must no longer auto-commit to `main`
- Preferred implementation for this ticket: remove the old write-path entirely by deleting `.github/workflows/update-code-map.yml`
- If deletion would break an explicitly referenced repository contract, then fallback is allowed only as:
  - keep the file, but disable all automatic write triggers and remove its commit/push step so it can no longer write either auto-doc on `main`
- Edge cases:
  - if neither file changed, no commit is created
  - if only one of the two files changed, the single writer workflow still commits via the same one-step commit path
  - if `origin/main` moved during the run, the workflow must exit without attempting a stale push

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Config/Defaults:** ✅ N/A – this ticket does not read or validate scanner config.
- **Nullability:** ✅ N/A – no nullable schema/output field semantics are changed.
- **Strict/Preflight:** ✅ N/A – there is no `--strict-*` CLI path in scope.
- **Not-evaluated vs failed:** ✅ N/A – no evaluation taxonomy is changed.
- **Determinismus:** The workflow behavior must be deterministic:
  - one workflow is the sole writer
  - one commit step only
  - no second automatic writer may remain
- **No guessing about file ownership:** After implementation, ownership is explicit:
  - sole writer workflow: `.github/workflows/generate-gpt-snapshot.yml`
  - generated targets: `docs/code_map.md`, `docs/GPT_SNAPSHOT.md`
- **No silent fallback implementation choices:** Use the preferred implementation unless it is technically impossible in-repo:
  1. extend `generate-gpt-snapshot.yml` to generate both files
  2. delete `.github/workflows/update-code-map.yml`
  3. keep one auto-commit step for both files together

## Implementation Notes
Codex must implement the following exact behavior unless a repo-local technical constraint makes one item impossible:

1. **Use `generate-gpt-snapshot.yml` as the sole writer**
   - Keep this file as the canonical auto-doc writer workflow.
   - Do not create a third writer workflow name/path for this ticket.

2. **Generate `docs/code_map.md` inside `generate-gpt-snapshot.yml`**
   - Add a step before snapshot generation that runs:
     - `python scripts/update_codemap.py`
   - Reuse the existing Python setup in the workflow.
   - Do not change the semantic output format of `docs/code_map.md`.

3. **Generate `docs/GPT_SNAPSHOT.md` in the same job/run**
   - Keep the existing snapshot generation logic in this workflow.
   - The snapshot may continue to include references to `docs/code_map.md`.

4. **Single commit step**
   - Replace the current snapshot-only commit step with one auto-commit step that covers both files:
     - `docs/code_map.md`
     - `docs/GPT_SNAPSHOT.md`
   - Commit message must clearly indicate both auto-docs are updated in one pass.
   - Only one `stefanzweifel/git-auto-commit-action@v5` step may remain across the active auto-doc writer path.

5. **Remove the second automatic write path**
   - Preferred: delete `.github/workflows/update-code-map.yml`
   - If deletion is not viable because another active workflow directly depends on the file name existing, then keep the file but make it non-writing:
     - remove `workflow_run` and `push` triggers that lead to auto-commits
     - remove any `git-auto-commit-action` usage from it
     - remove permissions/steps that push to `main`

6. **Stale-branch protection immediately before commit**
   - Add an explicit freshness check immediately before the auto-commit step.
   - Required behavior:
     - run `git fetch origin main --quiet`
     - compare current checked-out HEAD with `origin/main`
     - if they differ, log a clear skip message and exit 0 before attempting auto-commit
   - This check is required even after unifying to one writer, so a normal external push to `main` during the run cannot produce another non-fast-forward failure.

7. **Do not keep `workflow_run` chaining for auto-doc writes**
   - After implementation there must be no `workflow_run`-driven auto-doc commit chain from snapshot workflow to code-map workflow.

8. **Permissions**
   - Keep `contents: write` only where needed for the sole writer workflow.
   - Remove write permissions from the deprecated second path if that file remains.

## Acceptance Criteria (deterministic)
1. Exactly one workflow in `.github/workflows/` remains capable of automatically committing `docs/code_map.md` and/or `docs/GPT_SNAPSHOT.md` to `main`.
2. `.github/workflows/generate-gpt-snapshot.yml` generates both `docs/code_map.md` and `docs/GPT_SNAPSHOT.md` in the same job run.
3. The active auto-doc writer path contains exactly one auto-commit step, and that step covers both generated files.
4. `.github/workflows/update-code-map.yml` is either deleted, or it remains in the repo but has no automatic write trigger and no commit/push capability.
5. There is no remaining `workflow_run` chain that causes a second workflow to auto-commit `docs/code_map.md` after `gpt-snapshot`.
6. If `origin/main` changes after workflow start but before commit, the active workflow exits cleanly without attempting a stale push.
7. If neither generated file changes, no commit is created.
8. If one or both generated files change, at most one commit is created by the sole writer workflow for that run.
9. The implementation does not manually edit `docs/code_map.md` or `docs/GPT_SNAPSHOT.md`; both remain generated artifacts only.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (N/A – Ticket liest keine Config)
- **Config Invalid Value Handling:** ✅ (N/A – Ticket validiert keine Config)
- **Nullability / kein bool()-Coercion:** ✅ (N/A – keine Output-/Schema-Nullability betroffen)
- **Not-evaluated vs failed getrennt:** ✅ (N/A – keine Status-/Evaluationstaxonomie betroffen)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (N/A – keine `--strict-*`-Semantik im Scope)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (AC: #1, #4, #5, #8)
- **Deterministische Sortierung/Tie-breaker:** ✅ (N/A – kein Ranking/Sorting-Contract betroffen; deterministischer Workflow-Pfad über AC #1, #3, #8)

## Tests (required if logic changes)
- Unit:
  - N/A – no Python domain logic change is required by this ticket.
- Integration:
  - Verify in workflow YAML / PR diff that only one active auto-commit step remains for auto-doc writes.
  - Verify in workflow YAML / PR diff that `generate-gpt-snapshot.yml` contains the code-map generation step before snapshot generation.
  - Verify in workflow YAML / PR diff that `update-code-map.yml` is deleted or rendered non-writing.
  - Verify in workflow YAML / PR diff that a freshness check exists immediately before the commit step.
- Golden fixture / verification:
  - PR diff must show that the single auto-commit step includes both `docs/code_map.md` and `docs/GPT_SNAPSHOT.md`.
  - If a sample run link is available in the PR, it must show no second workflow attempting to push `docs/code_map.md`.

## Constraints / Invariants (must not change)
- [ ] `docs/code_map.md` remains an auto-generated read-only file
- [ ] `docs/GPT_SNAPSHOT.md` remains an auto-generated read-only file
- [ ] No change to canonical business logic or scoring behavior
- [ ] No change to closed-candle / no-lookahead invariants
- [ ] No manual content edits to the generated auto-doc files
- [ ] Exactly 1 ticket → 1 PR
- [ ] Ticket is archived in the same PR per `docs/canonical/WORKFLOW_CODEX.md`

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)
- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` if and only if Codex determines a canonical workflow/process contract must be clarified
- [ ] `docs/canonical/VERIFICATION_FOR_AI.md` unchanged unless Codex can justify a direct relevance
- [ ] PR created: exactly **1 ticket → 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

## Metadata
```yaml
created_utc: "2026-03-13T00:00:00Z"
priority: P1
type: refactor
owner: codex
related_issues: []
```
