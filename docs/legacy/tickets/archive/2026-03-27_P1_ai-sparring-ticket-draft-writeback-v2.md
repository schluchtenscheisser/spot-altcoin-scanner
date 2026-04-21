> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] AI Sparring Ticket Drafts: generate `ticket_draft.md` and optional safe repo writeback via branch + PR

## Context / Source (optional)
Ticket 01 created the isolated tool scaffold and dry-run vertical slice.
Ticket 02 added real providers, context loading, and the structured session runtime with:
- `session.json`
- `session.md`
- `final_summary.md`

Ticket 03 adds an issue-based UI, but this ticket must remain usable even without the issue UI.
The core value in this ticket is:

1. generate a Codex-ready Markdown ticket draft from a **completed** sparring session
2. always persist that draft as a session artifact
3. optionally write the draft back into this repository via a **new branch + PR**
4. never push directly to `main`

This ticket is for **Codex**. Do not guess missing behavior. If something is not explicit here, keep it minimal and deterministic.

## Goal
After this change:

- every **completed** AI sparring session generates a `ticket_draft.md`
- the generated draft is included in the session output directory and referenced from `session.json`
- `final_summary.md` contains a dedicated `Generated Ticket Draft` section
- optional writeback (`--writeback`) creates:
  - a new branch
  - a new draft file under `docs/tickets/drafts/`
  - a PR against `main`

The repo must not be mutated unless writeback was explicitly requested.

## Scope
Allowed files/modules to change or add:

- `.github/workflows/ai-sparring.yml`
- `tools/ai_sparring/cli.py`
- `tools/ai_sparring/ticket_draft.py`
- `tools/ai_sparring/writeback.py`
- `docs/canonical/ARCHITECTURE.md`
- `tools/ai_sparring/tests/test_ticket_draft.py`
- `tools/ai_sparring/tests/test_writeback.py`
- `tools/ai_sparring/tests/test_ticket_draft_integration.py`
- `tools/ai_sparring/tests/test_writeback_integration.py`

You may add small helper modules under `tools/ai_sparring/` if needed, but do not expand beyond this feature slice.

## Out of Scope
Explicitly not part of this ticket:

- auto-merging PRs
- editing or updating previously generated draft files
- multi-repo writeback
- direct push to `main`
- issue-comment UI changes
- pointer-state changes from Ticket 03
- generating drafts for non-completed runtime sessions
- generating drafts for `failed_runtime` or `failed_partial` sessions
- changing scanner runtime behavior
- changing scanner output schema
- changing session round semantics from Ticket 02

## Canonical References (important)
List the canonical documents that define/are affected by this change.

- `docs/canonical/AUTHORITY.md`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/TEST_STRATEGY.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary).

- Before:
  - completed sparring sessions stop at `session.json`, `session.md`, and `final_summary.md`
  - no Codex-ready ticket draft is produced
  - no safe repo writeback path exists for generated ticket drafts

- After:
  - on a **completed** session, the runtime performs one additional provider call to generate a Codex-ready ticket draft
  - the generated draft is written as `ticket_draft.md`
  - `final_summary.md` appends a dedicated `Generated Ticket Draft` section containing the exact generated draft text
  - `session.json` records deterministic metadata for draft generation and optional writeback
  - if `--writeback` is enabled, a separate workflow job performs safe writeback through:
    - new branch
    - commit of exactly one generated file
    - PR against `main`

- Edge cases:
  - if ticket-draft generation fails, the session remains `completed` but draft status is recorded as failed
  - if writeback is not requested, the repo is not mutated
  - if writeback preflight fails, the repo is not mutated
  - if branch push succeeds but PR creation fails, the failure is recorded explicitly and no cleanup is attempted automatically
  - if the deterministic head branch already has an open PR to `main`, treat writeback as idempotent success and do not create a second PR

- Backward compatibility impact:
  - additive only
  - Ticket 02 session outputs remain valid
  - manual `workflow_dispatch` remains usable without writeback
  - Ticket 03 is not required for this ticket to work

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)

- **Draft generation trigger:** Generate `ticket_draft.md` only when the runtime session content status is exactly `completed`.
- **No draft for incomplete/failed sessions:** If `session.json.status` is not `completed`, do not create `ticket_draft.md`. Record skipped status in `session.json`.
- **Ticket-drafter provider/model:** Use the same provider and model as the session `drafter` participant from Ticket 02. Do not add a third provider role in this ticket.
- **One extra provider call only:** Draft generation uses exactly one additional provider call after successful session completion.
- **Template sources:** Always provide both of these files to the ticket-drafter call:
  - `docs/tickets/_TEMPLATE.md`
  - `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- **Draft-generation preflight:** Before the ticket-drafter provider call, validate that both template source files exist and are readable UTF-8 text files. If either file is missing or unreadable:
  - do not make the ticket-drafter provider call
  - set `ticket_draft.status = "failed"`
  - set `ticket_draft.path = null`
  - record a clear error reason in `session.json`
  - append `Not generated: <reason>` to `final_summary.md`
- **Draft output language:** The generated ticket draft must be in English.
- **Draft output format:** The provider must output Markdown only. No JSON wrapper. No surrounding explanation text.
- **Template alignment:** The generated ticket draft must follow the section structure from `docs/tickets/_TEMPLATE.md`.
- **Frontmatter is required:** The generated `ticket_draft.md` must start with YAML frontmatter.
- **Ticket-generation system prompt:** Implement one fixed built-in system prompt for the ticket-drafter call. Do not make this prompt user-configurable in this ticket.
- **Ticket-generation visibility:** The ticket-drafter input sees exactly:
  - original user prompt
  - selected mode
  - participants from `session.json`
  - ordered `context_sources`
  - completed `session.json`
  - completed `final_summary.md`
  - the final round `revision`
  - `docs/tickets/_TEMPLATE.md`
  - `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md`
- **No hidden full repo scan:** Do not auto-load extra repo files for the ticket-drafter beyond the explicit inputs above.
- **Core session truth split:** `session.json` remains the source of truth for runtime session content. This ticket may add a `ticket_draft` metadata block to `session.json`, but must not redefine prior session semantics from Ticket 02.
- **Writeback default:** `--writeback` defaults to false.
- **No direct push to main:** Writeback must always use a new branch and a PR to `main`.
- **Separate workflow job:** In GitHub Actions, writeback must happen in a separate downstream job from the session execution job.
- **Writeback preflight before git mutation:** Before creating a branch, commit, or push, validate:
  - `--writeback` is enabled
  - `ticket_draft.md` exists
  - the runtime session status is `completed`
  - the working tree is clean
  - the base branch is exactly `main`
  - the target path is inside `docs/tickets/drafts/`
- **Writeback branch/file naming:** Use deterministic names:
  - `session_id`:
    - if `session.json` already has top-level `session_id`, reuse it
    - else derive `session_id = "sess-" + sha256(canonical session.json bytes)[:12]`
  - `date_part = current UTC date at writeback time` formatted as `YYYY-MM-DD`
  - `slug = slugify(frontmatter.title)`:
    - lowercase ASCII
    - allowed chars `a-z`, `0-9`, `-`
    - collapse repeated `-`
    - trim leading/trailing `-`
    - max length `60`
  - branch name:
    - `ai-sparring/drafts/<date_part>-<slug>-<session_id>`
  - target repo path:
    - `docs/tickets/drafts/<date_part>-<slug>-<session_id>.md`
- **Writeback idempotency rule:** If the computed remote branch already exists and there is already an open PR from that head branch to `main`, treat writeback as idempotent success:
  - do not create a second PR
  - do not create a second commit
  - record the existing PR metadata in `session.json`
- **Branch collision rule:** If the computed remote branch exists but there is no open PR from that branch to `main`, fail writeback preflight with a clear status and do not mutate the repo.
- **PR creation mechanism:** Use the GitHub REST API for PR creation.
- **Writeback auth:** Use `GITHUB_TOKEN` in workflow runs. Do not require a PAT.
- **No automatic cleanup on partial remote success:** If push succeeds and PR creation fails, record the failure as `failed_after_push`, preserve branch/commit metadata if available, and do not attempt branch deletion automatically.
- **Issue UI independence:** Do not require Ticket 03 pointer/comment state to generate a ticket draft or perform writeback.

## Implementation Notes (optional but useful)

### CLI contract additions
Extend the existing Ticket 02 CLI so that:

- successful completed sessions always attempt ticket-draft generation
- `--writeback` is an optional boolean flag
- `--writeback` default is false

Example:

```bash
python -m tools.ai_sparring.cli \
  --prompt "review this design" \
  --drafter-provider openai \
  --reviewer-provider anthropic \
  --drafter-model gpt-5 \
  --reviewer-model claude-sonnet-4-5 \
  --mode ticket_review \
  --rounds 2 \
  --output-dir /tmp/ai-sparring \
  --writeback
```

### Ticket-drafter prompt contract
Implement one built-in fixed system prompt for ticket-draft generation that instructs the provider to:

- produce a Codex-ready implementation ticket in English
- follow `docs/tickets/_TEMPLATE.md`
- avoid unstated assumptions
- make defaults, validation rules, and edge cases explicit
- write deterministic acceptance criteria
- include tests
- output Markdown only

### Template preflight contract
Before the ticket-drafter provider call, validate:

- `docs/tickets/_TEMPLATE.md` exists and is readable
- `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` exists and is readable

If either check fails:

- do not call the provider
- do not create `ticket_draft.md`
- keep the runtime session content status unchanged
- set `ticket_draft.status = "failed"`
- set `ticket_draft.path = null`
- append `Not generated: <reason>` in `final_summary.md`

### Generated files on successful completed session
On successful draft generation, the output directory must contain:

- `session.json`
- `session.md`
- `final_summary.md`
- `ticket_draft.md`

### `ticket_draft.md` contract
`ticket_draft.md` must begin with YAML frontmatter and contain at least:

```yaml
---
title: "<generated ticket title>"
generated_by: ai-sparring
session_id: "<existing or derived session id>"
status: draft
source_models:
  - "<drafter_provider>:<drafter_model>"
  - "<reviewer_provider>:<reviewer_model>"
---
```

The Markdown body must follow the repo ticket template structure.

### `final_summary.md` append contract
Append an exact top-level section:

```md
## Generated Ticket Draft
```

Immediately below that heading, include the exact contents of `ticket_draft.md` after a blank line.

If draft generation fails or is skipped, append instead:

```md
## Generated Ticket Draft

Not generated: <reason>
```

### `session.json` extension contract
Extend `session.json` with a top-level `ticket_draft` block:

```json
{
  "ticket_draft": {
    "status": "generated",
    "provider": "openai",
    "model": "gpt-5",
    "session_id": "sess-abc123def456",
    "path": "ticket_draft.md",
    "title": "AI Sparring Issue UI: ...",
    "writeback": {
      "requested": false,
      "status": "not_requested",
      "branch": null,
      "target_path": null,
      "pull_request_number": null,
      "pull_request_url": null,
      "commit_sha": null,
      "error": null
    }
  }
}
```

Allowed `ticket_draft.status` values in this ticket:
- `generated`
- `skipped_not_completed`
- `failed`

Path/nullability rule in this ticket:
- if `ticket_draft.status == "generated"`, `ticket_draft.path = "ticket_draft.md"`
- if `ticket_draft.status != "generated"`, `ticket_draft.path = null`

Allowed `ticket_draft.writeback.status` values in this ticket:
- `not_requested`
- `skipped_no_draft`
- `preflight_failed`
- `existing_pr`
- `pr_opened`
- `failed_before_push`
- `failed_after_push`
- `branch_exists_without_pr`

### Writeback git/PR contract
When `--writeback` is enabled and draft generation succeeded:

1. compute deterministic `session_id`, branch name, and target path
2. perform writeback preflight
3. check whether the remote head branch already exists
4. if an open PR from that branch to `main` exists:
   - record `existing_pr`
   - stop without new mutation
5. otherwise:
   - create new local branch from `main`
   - write exactly one file to the computed target path
   - commit exactly that file
   - push the branch
   - create a PR against `main` via GitHub REST API

### Commit / PR text contract
Use deterministic text:

- commit message:
  - `Add AI sparring ticket draft: <filename>`
- PR title:
  - `Add AI sparring ticket draft: <generated ticket title>`

- PR body:
  ```md
  This PR was generated by ai-sparring.

  - session_id: <session_id>
  - source draft artifact: ticket_draft.md
  - source mode: <mode>
  - source models:
    - <drafter_provider>:<drafter_model>
    - <reviewer_provider>:<reviewer_model>

  This PR contains a generated draft ticket for review.
  ```

### Canonical architecture doc update
Update `docs/canonical/ARCHITECTURE.md` to document, at minimum:

- ticket-draft generation as a post-session step after runtime completion
- optional writeback as a separate downstream job
- the separation between runtime session execution and repo mutation
- the invariant that writeback never pushes directly to `main`

### Workflow contract
Update the manual `workflow_dispatch` sparring workflow so that:

- the session job still runs with minimal read-only permissions
- draft generation happens in the session job after session completion
- artifact upload includes `ticket_draft.md` when generated
- there is a separate conditional writeback job that runs only when writeback is requested
- the writeback job uses permissions:
  - `contents: write`
  - `pull-requests: write`

### Operational precondition for PR creation
Assume the repository is configured so that GitHub Actions is allowed to create pull requests with `GITHUB_TOKEN`.

If PR creation fails with a permission-related API error, record the failure in `session.json.ticket_draft.writeback` and surface a clear error in the workflow logs. Do not retry PR creation on permission failures.

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.

1) When a runtime session completes with `session.json.status == "completed"`, the tool makes exactly one additional ticket-drafter provider call and writes `ticket_draft.md`.

2) `ticket_draft.md` begins with YAML frontmatter and contains a Markdown body aligned to `docs/tickets/_TEMPLATE.md`.

3) `final_summary.md` contains a top-level `## Generated Ticket Draft` section.

4) `session.json` contains a top-level `ticket_draft` block with:
   - `status`
   - `provider`
   - `model`
   - `session_id`
   - `path`
   - `title`
   - `writeback`

5) If `session.json.status != "completed"`, the tool does not create `ticket_draft.md`, records `ticket_draft.status = "skipped_not_completed"`, and records `ticket_draft.writeback.status = "skipped_no_draft"` when writeback was requested.

6) If either `docs/tickets/_TEMPLATE.md` or `docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md` is missing or unreadable at draft-generation time, the tool does not call the ticket-drafter provider, the runtime session remains completed, `ticket_draft.status = "failed"`, `ticket_draft.path = null`, and `final_summary.md` contains `Not generated: <reason>`.

7) If the ticket-drafter provider call fails after the runtime session already completed, the session remains completed, `ticket_draft.status = "failed"`, `ticket_draft.path = null`, `ticket_draft.md` is absent, and `final_summary.md` contains `Not generated: <reason>`.

8) Without `--writeback`, the repo working tree and remote state are not mutated, and `ticket_draft.writeback.status = "not_requested"`.

9) With `--writeback`, the workflow uses a separate downstream writeback job with:
   - `contents: write`
   - `pull-requests: write`

10) With `--writeback`, the computed target path is exactly under `docs/tickets/drafts/` and the computed branch name starts with `ai-sparring/drafts/`.

11) If writeback preflight fails before any git mutation, `ticket_draft.writeback.status = "preflight_failed"` and no branch, commit, push, or PR is created.

12) If the computed remote branch already exists and there is already an open PR from that head branch to `main`, the tool records `ticket_draft.writeback.status = "existing_pr"` and does not create a second commit or PR.

13) If the computed remote branch exists and there is no open PR from that head branch to `main`, the tool records `ticket_draft.writeback.status = "branch_exists_without_pr"` and does not mutate the repo.

14) If writeback succeeds end-to-end, exactly one new file is committed at the computed target path, exactly one branch is pushed, exactly one PR is opened against `main`, and `ticket_draft.writeback.status = "pr_opened"`.

15) If branch push succeeds but PR creation fails, `ticket_draft.writeback.status = "failed_after_push"` and `session.json` records branch and commit metadata if available.

16) The generated draft file path and branch name are deterministic from:
   - UTC date at writeback time
   - generated ticket title slug
   - existing or derived `session_id`

17) The manual `workflow_dispatch` sparring flow from Ticket 02 continues to work with `--writeback=false`.

18) This ticket does not require Ticket 03 issue-session control-state to generate drafts or perform writeback.

## Default-/Edgecase-Abdeckung (required for code tickets)

- **Config Defaults (Missing key -> Default):** ✅ (AC: #8, #17 ; Test: `test_writeback_defaults_to_not_requested`)
- **Config Invalid Value Handling:** ✅ (AC: #6, #11, #13 ; Test: `test_missing_ticket_template_fails_without_provider_call`, `test_writeback_preflight_fails_outside_allowed_target_path`, `test_existing_branch_without_pr_fails_cleanly`)
- **Nullability / no bool() coercion:** ✅ (AC: #4, #6, #7 ; Test: `test_ticket_draft_writeback_metadata_uses_null_for_absent_fields`)
- **Not-evaluated vs failed separated:** ✅ (AC: #5, #6, #7, #11, #15 ; Test: `test_skipped_not_completed_vs_failed_template_preflight_vs_failed_generation_vs_failed_after_push_are_distinct`)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (AC: #6, #11 ; Test: `test_missing_ticket_template_fails_without_provider_call`, `test_writeback_preflight_failure_mutates_no_git_state`)
- **ID/filename Namespace collisions (if relevant):** ✅ (AC: #12, #13, #16 ; Test: `test_branch_and_target_path_are_deterministic_and_collision_handled`)
- **Deterministic sorting / tie-breakers:** ✅ (AC: #2, #16 ; Test: `test_generated_frontmatter_and_title_slug_are_deterministic_for_fixed_inputs`)

## Tests (required if logic changes)
- Unit:
  - `test_completed_session_generates_ticket_draft`
  - `test_non_completed_session_skips_ticket_draft`
  - `test_missing_ticket_template_fails_without_provider_call`
  - `test_failed_ticket_generation_preserves_completed_session`
  - `test_ticket_draft_frontmatter_is_present`
  - `test_final_summary_embeds_generated_ticket_draft`
  - `test_session_json_contains_ticket_draft_block`
  - `test_writeback_defaults_to_not_requested`
  - `test_ticket_draft_writeback_metadata_uses_null_for_absent_fields`
  - `test_existing_branch_with_open_pr_is_idempotent_success`
  - `test_existing_branch_without_pr_fails_cleanly`
  - `test_branch_and_target_path_are_deterministic_and_collision_handled`
  - `test_writeback_preflight_failure_mutates_no_git_state`

- Integration:
  - CLI run with mocked provider clients where a completed session produces `ticket_draft.md`
  - CLI run with missing template/checklist file where no ticket-drafter provider call occurs and draft status is `failed`
  - CLI run with failed ticket-drafter call where runtime session remains completed and draft status is `failed`
  - writeback integration against a temporary git repo + temporary bare remote, with mocked GitHub PR-creation API
  - writeback integration where push succeeds and mocked PR creation fails, verifying `failed_after_push`

- Golden fixture / verification:
  - Not required in this ticket
  - Do not update scanner scoring verification docs

## Constraints / Invariants (must not change)
Examples:
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges clamp to 0..100
- Timestamp unit = ms

- [x] No direct push to `main`
- [x] No scanner runtime changes
- [x] No issue-pointer-state dependency
- [x] Draft generation is additive to the Ticket 02 runtime contract
- [x] Writeback is optional and disabled by default
- [x] Writeback happens in a separate workflow job from session execution

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Did not change scanner runtime logic or outputs
- [ ] Did not introduce direct writes to `main`
- [ ] Manual sparring workflow still works with writeback disabled
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-27T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
