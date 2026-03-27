# Title
[P1] AI Sparring Issue UI: issue template, comment commands, and artifact-backed stepwise session control

## Context / Source (optional)
Ticket 01 created the isolated foundation and dry-run vertical slice.
Ticket 02 adds real providers, context loading, and deterministic session orchestration with `session.json`, `session.md`, and `final_summary.md`.

This ticket adds the **GitHub Issue-based user interface** for sparring sessions.

The goal is **not** to replace the manual `workflow_dispatch` flow from Ticket 02.
The goal is to add a second, repo-native UI where the user can:
- open an issue,
- start a session with a command,
- continue one round at a time,
- adjust focus between rounds,
- and stop the session from the issue thread.

This ticket is for **Codex**. Do not guess missing behavior. If something is not explicit here, keep it minimal and deterministic.

## Goal
After this change, a user can drive an AI sparring session from a GitHub issue thread using comment commands:

- `/sparring start`
- `/continue`
- `/focus <text>`
- `/stop`

The issue thread becomes the visible UI.
The technical state is intentionally split into two layers:
- the **workflow artifact from the previous run** is the source of truth for persisted session content (`session.json`, rounds, drafts, reviews, revisions, summaries)
- the latest issue comment pointer is the source of truth for lightweight session control-state (`status`, `current_focus`, `latest_run_id`, `latest_artifact_name`)

The issue comment only stores a **small hidden pointer payload** to the artifact plus the current control-state view.

The existing `workflow_dispatch` flow from Ticket 02 must continue to work unchanged.

## Scope
Allowed files/modules to change or add:

- `.github/ISSUE_TEMPLATE/ai-sparring-session.yml`
- `.github/workflows/ai-sparring-issue.yml`
- `tools/ai_sparring/cli.py`
- `tools/ai_sparring/session.py`
- `tools/ai_sparring/issue_driver.py`
- `tools/ai_sparring/issue_parser.py`
- `tools/ai_sparring/issue_state.py`
- `tools/ai_sparring/github_api.py`
- `tools/ai_sparring/output_writer.py`
- `tools/ai_sparring/tests/test_issue_parser.py`
- `tools/ai_sparring/tests/test_issue_state.py`
- `tools/ai_sparring/tests/test_issue_driver.py`
- `tools/ai_sparring/tests/test_issue_template_foundation.py`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/TEST_STRATEGY.md`

You may add small helper modules under `tools/ai_sparring/` if needed, but do not expand beyond the issue UI feature slice.

## Out of Scope
Explicitly not part of this ticket:

- ticket-draft generation
- repo writeback / branch creation / PR creation
- direct pushes to `main`
- changes under `scanner/`
- changes to scanner runtime behavior
- replacing the existing manual `workflow_dispatch` UI
- multi-issue sessions
- multi-repo sessions
- issue auto-start on issue creation
- slash commands in pull requests

## Canonical References (important)
List the canonical documents that define/are affected by this change.

- `docs/canonical/AUTHORITY.md`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/TEST_STRATEGY.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
Describe intended behavior (not implementation details unless necessary).

- Before:
  - AI sparring can be run manually through `workflow_dispatch`.
  - There is no issue-based UI.
  - There is no command parser for issue comments.
  - There is no resumable issue-thread session control.

- After:
  - A dedicated issue template exists for AI sparring sessions.
  - A dedicated issue workflow exists and listens to issue comments.
  - The user creates an issue from the template, then posts `/sparring start`.
  - The start command runs exactly **one round** and posts a structured bot comment.
  - `/continue` runs exactly **one additional round**.
  - `/focus <text>` updates the current focus for subsequent rounds but does **not** run a round.
  - `/stop` finalizes the session early and posts a final summary comment based on the latest persisted session artifact.
  - Session progression is visible in the issue thread.
  - The underlying technical state is resumed from the previous run artifact, not reconstructed from free-form comments.

- Edge cases:
  - unsupported or malformed slash commands do not mutate session state
  - commands on pull requests are ignored
  - `/continue`, `/focus`, and `/stop` fail clearly if no active issue session exists
  - `/sparring start` fails clearly if an active issue session already exists on the issue
  - terminal sessions (`completed`, `stopped`, `failed_runtime`, `failed_partial`) do not accept `/continue` or `/focus`
  - issue comments remain human-readable even though they contain a hidden machine pointer payload

- Backward compatibility impact:
  - additive only
  - `workflow_dispatch` remains supported
  - Ticket 02 session artifacts remain the source of truth for runtime state
  - no scanner outputs or scanner workflows change

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)

- **Separate workflow:** Create a dedicated workflow file:
  - `.github/workflows/ai-sparring-issue.yml`
  Do not overload the existing manual workflow with mixed trigger logic in this ticket.
- **Issue event scope:** The issue workflow uses `issue_comment` with the `created` activity type only.
- **Ignore pull requests:** The issue workflow must ignore issue comments that belong to pull requests.
- **One issue = one session:** This ticket supports at most one sparring session per issue.
- **Command position rule:** A slash command is recognized only if it is the first non-whitespace token in the comment body.
- **Supported commands exactly:**
  - `/sparring start`
  - `/continue`
  - `/focus <text>`
  - `/stop`
- **No command aliases** in this ticket.
- **No implicit start:** Opening an issue does not start a session. The session starts only when `/sparring start` is posted.
- **State source of truth:** The persisted session artifact from the latest successful state-bearing run is the source of truth.
- **Comment payload is pointer-only:** The issue comment must not contain the full cumulative session JSON as hidden payload. It must contain only a small machine-readable pointer payload sufficient to find and resume the latest session artifact.
- **Pointer payload contract:** Every bot state-bearing comment must end with exactly one hidden HTML comment in this form:
  `<!-- ai-sparring-state:v1:<base64-encoded-json> -->`
- **Pointer payload contents:** The decoded JSON must include at least:
  - `state_version`
  - `session_id`
  - `issue_number`
  - `status`
  - `rounds_requested`
  - `rounds_completed`
  - `current_focus`
  - `latest_run_id`
  - `latest_artifact_name`
- **Session id generation:** Because this ticket supports exactly one sparring session per issue, `session_id` must be deterministic and derived only from the issue number:
  - `issue-<issue_number>`
  Do not use timestamps, random suffixes, or per-run ids for `session_id` in this ticket.
- **Artifact source of truth:** The resumed persisted session content must come from the previous run artifact, not from issue comment prose.
- **Control-state source of truth:** The latest valid pointer payload is the source of truth for issue-session control-state:
  - `status`
  - `current_focus`
  - `latest_run_id`
  - `latest_artifact_name`
- **Status split is intentional:** For `/stop`, the pointer control-state changes to `status=stopped` without creating a new artifact. In that case the prior artifact may still contain its earlier runtime status such as `awaiting_continue`. This is valid in this ticket and must not be treated as an inconsistency.
- **Pointer run-id semantics:** `latest_run_id` in the pointer refers to the workflow run that produced the previously persisted state-bearing artifact. It must not be set to the current workflow run before resume logic resolves prior state.
- **Artifact resolution mechanism:** Resume logic must resolve the prior artifact via the GitHub REST API using:
  - `GET /repos/{owner}/{repo}/actions/runs/{run_id}/artifacts`
  - then the artifact download endpoint for the resolved artifact id
  Do not use `actions/download-artifact` for cross-run resume in this ticket.
- **Permissions:** The issue workflow must use the minimum permissions required for this design:
  - `contents: read`
  - `issues: write`
  - `actions: read`
- **Concurrency:** Serialize issue commands by issue number. Do not allow overlapping workflow runs for the same issue.
- **No repo writes:** This ticket must not write files back into the repository.
- **No new provider semantics:** Reuse the runtime/provider behavior from Ticket 02. This ticket adds UI/state control, not new LLM semantics.
- **No schema guessing:** If Ticket 02 exposed a `session.json` contract, resume logic must use that contract directly. Do not invent a second full runtime schema.
- **Issue-only focus semantics:** `/focus <text>` changes only the issue-session focus for subsequent rounds. It does not change provider assignments, model ids, context paths, or rounds requested.
- **Focus application:** When a focus is active, it must be appended deterministically to the next round’s user-level instruction context. Do not rewrite system prompts in this ticket.
- **Terminal states:** The following states are terminal:
  - `completed`
  - `stopped`
  - `failed_runtime`
  - `failed_partial`
- **Active state:** The only active resumable state in this ticket is:
  - `awaiting_continue`
- **Rounds requested contract:** `rounds_requested` comes from the parsed issue body `## Rounds` field and is the hard upper bound for the session.
- **Completion rule:** After each successfully executed round:
  - if `rounds_completed < rounds_requested`, the new status is `awaiting_continue`
  - if `rounds_completed == rounds_requested`, the new status is `completed`
- **Single-round special case:** If `rounds_requested == 1`, then `/sparring start` executes one round and must immediately produce terminal status `completed`, not `awaiting_continue`.

## Implementation Notes (optional but useful)

### Issue template contract
Create `.github/ISSUE_TEMPLATE/ai-sparring-session.yml` as a GitHub issue form.

The form must render an issue body that is parseable with exact section headings.
Use these headings exactly:

- `## Prompt`
- `## Mode`
- `## Rounds`
- `## Drafter Provider`
- `## Drafter Model`
- `## Reviewer Provider`
- `## Reviewer Model`
- `## Extra Context Paths`

The parser in this ticket must parse the issue body by these exact headings.
Do not rely on undocumented issue-form internals.

### Issue-template field rules
Required issue fields:
- `Prompt`
- `Mode`
- `Rounds`

`Rounds` is the requested total number of rounds for the whole issue session, not "rounds per workflow run".
In this ticket, each valid `/sparring start` or `/continue` executes exactly one round.

Optional issue fields:
- `Drafter Provider`
- `Drafter Model`
- `Reviewer Provider`
- `Reviewer Model`
- `Extra Context Paths`

If optional provider/model fields are omitted, use the Ticket 02 runtime defaults and validations.
Do not create a second independent default system in this ticket.

### Command grammar
Implement exact command parsing rules:

- `/sparring start`
  - no extra trailing tokens allowed
- `/continue`
  - no extra trailing tokens allowed
- `/focus <text>`
  - `<text>` is required
  - trim outer whitespace
  - reject empty result
  - store exactly the trimmed text
- `/stop`
  - no extra trailing tokens allowed

### Command state machine
No existing session on issue:
- `/sparring start` -> valid
- `/continue` -> invalid
- `/focus <text>` -> invalid
- `/stop` -> invalid

Active session (`awaiting_continue`):
- `/sparring start` -> invalid
- `/continue` -> valid
- `/focus <text>` -> valid
- `/stop` -> valid

Terminal session (`completed`, `stopped`, `failed_runtime`, `failed_partial`):
- `/sparring start` -> invalid
- `/continue` -> invalid
- `/focus <text>` -> invalid
- `/stop` -> invalid

Invalid commands must:
- not mutate state
- not upload a new artifact
- post a short bot comment explaining the allowed commands for the current state

### Artifact-backed resume contract
Use workflow artifacts as the technical state store for persisted session content.

### Session state split contract
This ticket intentionally uses two related but different state carriers:

1. **Persisted session content artifact**
   - contains the Ticket-02 runtime outputs such as:
     - `session.json`
     - `session.md`
     - `final_summary.md`
   - is the source of truth for:
     - completed rounds
     - drafts/reviews/revisions
     - persisted summaries
     - prior runtime failure details

2. **Issue comment pointer payload**
   - is the source of truth for:
     - latest issue-session control status
     - latest focus override
     - which prior run/artifact to resume from

Because `/focus` and `/stop` do not create new artifacts in this ticket, pointer control-state may legitimately be newer than the last artifact content state.

For each state-bearing run (`/sparring start` or `/continue`), upload an artifact with a deterministic name:

`ai-sparring-issue-<issue_number>-r<rounds_completed>`

Examples:
- `ai-sparring-issue-123-r1`
- `ai-sparring-issue-123-r2`

Each such artifact must contain at least:
- `session.json`
- `session.md`
- `final_summary.md`

For `/continue`:
- find the latest bot state-bearing comment on the issue
- decode its pointer payload
- use the pointer's `latest_run_id` and `latest_artifact_name` to resolve the previous state-bearing artifact
- list artifacts for that prior workflow run via the GitHub REST API
- download the resolved prior artifact by artifact id
- load `session.json`
- resume by executing exactly one additional round
- upload a new artifact for the new step
- post a new visible round comment with a new pointer payload

For `/focus <text>`:
- find the latest bot state-bearing comment on the issue
- decode its pointer payload
- validate that the session is active
- update only `current_focus` in the new pointer payload
- preserve the prior `latest_run_id` and `latest_artifact_name` unchanged
- post a new bot comment acknowledging the updated focus
- upload no new artifact

For `/stop`:
- find the latest bot state-bearing comment
- decode its pointer payload
- resolve the latest session artifact referenced by the pointer
- load `session.json`
- generate/post a final issue comment from the existing session data
- do not execute a new LLM round
- do not upload a new artifact
- preserve the prior `latest_run_id` and `latest_artifact_name` unchanged
- set pointer control-state `status=stopped`
- `/stop` changes only pointer control-state; it does not mutate the persisted artifact contents

### Workflow / job design
Create a dedicated workflow triggered by:

```yaml
on:
  issue_comment:
    types: [created]
```

Required workflow-level behavior:
- ignore pull requests
- parse the incoming comment
- no-op for non-command comments
- serialize by issue number using `concurrency`
- use minimal permissions
- upload artifacts for state-bearing runs

Recommended concurrency shape:

```yaml
concurrency:
  group: ai-sparring-issue-${{ github.event.issue.number }}
  cancel-in-progress: false
```

### Comment rendering contract
For `/sparring start` and `/continue`, the bot must post one Markdown comment in this order:

1. `## AI Sparring`
2. `Session: <session_id>`
3. `Status: awaiting_continue|completed|failed_runtime|failed_partial`
4. `Round: <rounds_completed>/<rounds_requested>`
5. `### Draft`
6. `### Review`
7. `### Revision`
8. `### Delta`
9. `### Focus`
10. `### Next commands`

Then append the hidden state pointer payload as the final line.

For `/stop`, the bot must post one Markdown comment in this order:

1. `## AI Sparring Final Summary`
2. `Session: <session_id>`
3. `Status: stopped`
4. `Rounds completed: <n>/<requested>`
5. `### Final Summary`
6. `### Focus`
7. `### Closed session`

Then append the hidden state pointer payload as the final line.

### Comment truncation contract
To avoid unsafe comment growth, apply deterministic truncation to visible content only.

Per visible section:
- `Draft`
- `Review`
- `Revision`
- `Final Summary`

cap rendered content to `12000` characters per section.
If truncation occurs, append this exact suffix:

`[truncated for issue display; full content remains in workflow artifact]`

Do not truncate the persisted artifact files.

### Issue driver contract
Implement the issue UI as a Python-driven flow, not as shell-only glue.

A valid design is:
- parse issue/comment input in Python
- call existing session/orchestration logic from Ticket 02
- call GitHub REST APIs from Python for:
  - listing issue comments
  - posting issue comments
  - listing artifacts for the prior workflow run referenced by `latest_run_id`
  - downloading the resolved prior artifact by artifact id

Do not require a personal access token.
Use `GITHUB_TOKEN`.

### Failure behavior
- If command parsing fails before any resume/start work, do not upload a new artifact.
- If `/sparring start` fails during issue-body validation, do not upload a new artifact.
- If `/continue` cannot resolve the prior pointer payload or prior artifact, post a clear bot error comment and do not upload a new artifact.
- If a resumed round fails after loading prior session state, preserve the new runtime status from Ticket 02 (`failed_runtime` or `failed_partial`) in the new state-bearing comment and upload the new artifact for that failed run.
- If `/stop` cannot resolve prior state, post a clear bot error comment and do not upload a new artifact.

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.

1) The repository contains `.github/ISSUE_TEMPLATE/ai-sparring-session.yml` and the generated issue body is parseable by exact headings:
   - `## Prompt`
   - `## Mode`
   - `## Rounds`
   - `## Drafter Provider`
   - `## Drafter Model`
   - `## Reviewer Provider`
   - `## Reviewer Model`
   - `## Extra Context Paths`

2) The repository contains a dedicated issue workflow `.github/workflows/ai-sparring-issue.yml` triggered by `issue_comment` with activity type `created`.

3) The issue workflow ignores comments on pull requests and does not run session logic for them.

4) Non-command comments produce no state mutation and no new workflow artifact.

5) `/sparring start` on a valid issue with no existing issue session runs exactly one round, uploads exactly one new state-bearing artifact, and posts exactly one new bot comment containing:
   - the visible round rendering
   - one hidden `ai-sparring-state:v1` pointer payload

6) If `rounds_requested == 1`, a successful `/sparring start` produces terminal status `completed`. If `rounds_requested > 1`, a successful `/sparring start` produces non-terminal status `awaiting_continue`.

7) `/continue` on an active issue session runs exactly one additional round, uploads exactly one new state-bearing artifact, and posts exactly one new bot comment containing:
   - the visible round rendering
   - one hidden `ai-sparring-state:v1` pointer payload

8) When a successful `/continue` makes `rounds_completed == rounds_requested`, the new status becomes `completed` and further `/continue` commands are rejected as terminal-session commands.

9) `/focus <text>` on an active issue session updates `current_focus`, posts exactly one new bot comment with the updated pointer payload, and uploads **zero** new artifacts.

10) `/focus <text>` does not execute a new LLM round, and the updated pointer preserves the same `latest_run_id` and `latest_artifact_name` as the immediately preceding valid state pointer.

11) `/stop` on an active issue session posts exactly one final summary bot comment with terminal control-state status `stopped` and uploads **zero** new artifacts.

12) After `/stop`, the latest pointer payload has `status=stopped` while `latest_run_id` and `latest_artifact_name` still reference the same prior state-bearing artifact that existed before `/stop`.

13) The decoded pointer payload in every state-bearing bot comment contains at least:
   - `state_version`
   - `session_id`
   - `issue_number`
   - `status`
   - `rounds_requested`
   - `rounds_completed`
   - `current_focus`
   - `latest_run_id`
   - `latest_artifact_name`

14) `session_id` is deterministically `issue-<issue_number>` for the whole issue session, and does not change across `/focus`, `/continue`, or `/stop`.

15) The source of truth for `/continue` resume is the artifact referenced by the latest valid pointer payload, not the free-form visible comment prose.

16) Resume logic resolves the prior artifact using the pointer's previous `latest_run_id`, not the current workflow run id.

17) The latest valid pointer payload is the source of truth for issue-session control-state fields:
   - `status`
   - `current_focus`
   - `latest_run_id`
   - `latest_artifact_name`
   while the referenced artifact remains the source of truth for persisted session content from prior executed rounds.

18) The issue workflow uses permissions no broader than:
   - `contents: read`
   - `issues: write`
   - `actions: read`

19) The issue workflow serializes commands by issue number with `cancel-in-progress: false`.

20) On an issue with no active session, `/continue`, `/focus <text>`, and `/stop` do not mutate state, do not upload a new artifact, and post a clear bot error comment.

21) On an issue with an active session, a second `/sparring start` does not mutate state, does not upload a new artifact, and posts a clear bot error comment.

22) On a terminal session, `/continue`, `/focus <text>`, and `/stop` do not mutate state, do not upload a new artifact, and post a clear bot error comment.

23) Visible issue comments truncate only the rendered sections according to the `12000`-character-per-section rule, while the artifact files remain untruncated.

24) The existing `workflow_dispatch` sparring workflow from Ticket 02 continues to work after this ticket.

## Default-/Edgecase-Abdeckung (required for code tickets)

- **Config Defaults (Missing key -> Default):** ✅ (AC: #1, #24 ; Test: `test_issue_start_uses_ticket02_runtime_defaults_when_optional_fields_missing`)
- **Config Invalid Value Handling:** ✅ (AC: #20, #21, #22 ; Test: `test_invalid_command_for_state_posts_error_without_artifact`, `test_issue_body_missing_required_heading_fails_start`)
- **Nullability / no bool() coercion:** ✅ (N/A — this ticket does not introduce new nullable runtime semantics in the session artifact schema)
- **Not-evaluated vs failed separated:** ✅ (AC: #7, #15, #16, #17 ; Test: `test_resume_uses_prior_artifact_and_preserves_runtime_failure_status`)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (AC: #4, #20, #21, #22 ; Test: `test_invalid_command_writes_no_artifact`)
- **ID/filename Namespace collisions (if relevant):** ✅ (AC: #5, #6, #13, #15, #17 ; Test: `test_artifact_names_are_step_scoped_and_concurrency_group_is_issue_scoped`)
- **Deterministic sorting / tie-breakers:** ✅ (AC: #13, #15 ; Test: `test_latest_valid_pointer_comment_is_selected_deterministically`)

## Tests (required if logic changes)
- Unit:
  - `test_issue_template_foundation_renders_expected_headings`
  - `test_parse_issue_body_by_exact_headings`
  - `test_parse_commands_with_first_token_rule`
  - `test_focus_requires_nonempty_text`
  - `test_pointer_payload_roundtrip_base64_contract`
  - `test_latest_valid_pointer_comment_is_selected_deterministically`
  - `test_invalid_command_for_state_posts_error_without_artifact`
  - `test_issue_body_missing_required_heading_fails_start`
  - `test_issue_start_uses_ticket02_runtime_defaults_when_optional_fields_missing`
  - `test_artifact_names_are_step_scoped_and_concurrency_group_is_issue_scoped`
  - `test_focus_preserves_prior_run_id_and_artifact_name`
  - `test_stop_sets_pointer_status_without_new_artifact`
  - `test_single_round_start_transitions_directly_to_completed`
  - `test_rounds_requested_becomes_completion_upper_bound`

- Integration:
  - simulated `/sparring start` issue-comment event -> one round comment + one artifact pointer payload
  - simulated `/continue` issue-comment event -> resumes from referenced artifact and posts next round
  - simulated issue-comment resume -> uses pointer's previous `latest_run_id`, not current workflow run id
  - simulated `/focus tests` issue-comment event -> updates pointer state and posts ack without artifact
  - simulated `/stop` issue-comment event -> posts final summary without artifact, preserves the prior artifact reference, and changes only pointer status to `stopped`
  - simulated pull-request comment event -> ignored by issue session logic

- Golden fixture / verification:
  - not required in this ticket
  - do not update scanner scoring verification docs

## Constraints / Invariants (must not change)
Examples:
- Closed-candle-only
- No lookahead
- Deterministic ordering with stable tie-breakers
- Score ranges clamp to 0..100
- Timestamp unit = ms

- [x] No files under `scanner/` are changed
- [x] Ticket 02 manual `workflow_dispatch` flow remains available
- [x] No repo writeback logic is introduced
- [x] Issue sessions are serialized per issue number
- [x] Persisted session content for resume comes from artifacts, not free-form comments
- [x] Pull requests are ignored by this issue UI

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` for issue-based sparring workflow behavior
- [ ] Did **not** modify scanner runtime logic or outputs
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
