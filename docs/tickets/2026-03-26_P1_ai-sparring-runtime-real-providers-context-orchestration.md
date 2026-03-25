# Title
[P1] AI Sparring Runtime: real providers, repo context loading, and deterministic multi-round session orchestration

## Context / Source (optional)
Ticket 01 established the isolated `tools/ai_sparring/` scaffold, the canonical roadmap path, a manual GitHub Actions entry point, deterministic dry-run artifacts, and a fake provider.

This ticket turns that foundation into a **real end-to-end sparring runtime** by adding:
- real provider integrations,
- deterministic repo context loading,
- and a fully specified multi-round session orchestration contract.

This ticket is for **Codex**. Do not guess. If behavior is not explicitly specified here, keep the implementation minimal, deterministic, and compatible with Ticket 01.

## Goal
After this change, the repository contains a working **real-provider AI sparring runtime** that can be executed from both:
- local CLI
- manual GitHub Actions workflow (`workflow_dispatch`)

The runtime must:
- support `fake`, `openai`, and `anthropic` providers behind one shared interface,
- load a fixed default repo context plus optional explicitly selected repo files,
- run a deterministic round-based protocol:
  - drafter -> reviewer -> revision
- preserve completed protocol state if a later provider call fails,
- and write stable session artifacts with a documented contract.

This ticket must **not** add issue-comment control or repo writeback.

## Scope
Allowed files/modules to change or add:

- `.github/workflows/ai-sparring.yml`
- `.env.example`
- `requirements.txt`
- `requirements-dev.txt`
- `tools/ai_sparring/cli.py`
- `tools/ai_sparring/session.py`
- `tools/ai_sparring/context_loader.py`
- `tools/ai_sparring/output_writer.py`
- `tools/ai_sparring/providers/__init__.py`
- `tools/ai_sparring/providers/base.py`
- `tools/ai_sparring/providers/fake_provider.py`
- `tools/ai_sparring/providers/openai_provider.py`
- `tools/ai_sparring/providers/anthropic_provider.py`
- `tools/ai_sparring/errors.py`
- `tools/ai_sparring/retry.py`
- `tools/ai_sparring/tests/test_cli_runtime.py`
- `tools/ai_sparring/tests/test_context_loader_runtime.py`
- `tools/ai_sparring/tests/test_providers.py`
- `tools/ai_sparring/tests/test_session_orchestration.py`
- `tools/ai_sparring/tests/test_session_contract.py`
- `docs/canonical/ARCHITECTURE.md`
- `docs/canonical/RUNTIME_AND_OPERATIONS.md`
- `docs/canonical/TEST_STRATEGY.md`

You may add small helper modules under `tools/ai_sparring/` if needed, but do not expand beyond this feature slice.

## Out of Scope
Explicitly not part of this ticket:

- issue-comment-driven session control
- issue templates
- `/continue`, `/focus`, or `/stop` commands
- ticket draft generation
- branch creation or PR creation
- repo writeback of generated drafts
- any changes under `scanner/`
- any changes to scanner runtime behavior
- any changes to scanner output schema or pipeline logic
- automatic repo-wide file discovery
- vector search / embeddings / semantic retrieval
- streaming UI
- background unattended loops outside the explicit requested round count

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
  - Ticket 01 supports only a deterministic fake-provider dry run.
  - The workflow does not support real model providers.
  - Context loading is limited to the fixed default sources.
  - There is no specified real multi-round sparring contract.

- After:
  - The runtime supports three providers:
    - `fake`
    - `openai`
    - `anthropic`
  - A session uses exactly two participant roles:
    - `drafter`
    - `reviewer`
  - Each role is bound to one provider and one model identifier.
  - The runtime supports a deterministic round protocol:
    1. drafter generates a draft
    2. reviewer critiques that draft
    3. drafter produces a revision
  - The runtime loads default repo context sources and optional extra repo-relative files.
  - Session artifacts record the full structured protocol.
  - Preflight failures produce **zero** output files.
  - Runtime/provider failures after preflight preserve already completed protocol state and write failed session artifacts.

- Edge cases:
  - missing API key for a selected real provider fails in preflight
  - missing required model identifier for a selected real provider fails in preflight
  - invalid extra context path fails in preflight
  - duplicate context paths are de-duplicated deterministically
  - a provider failure in round 2 or later preserves round 1 output
  - retry occurs only for transient failures, never for auth/config/validation failures

- Backward compatibility impact:
  - additive only
  - fake-provider flow from Ticket 01 remains supported
  - no scanner runtime behavior changes
  - no scanner report/schema changes

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)

- **Provider APIs:** Use:
  - OpenAI **Responses API**
  - Anthropic **Messages API**
- **Official SDKs:** Use the official Python SDKs for both providers if available in `requirements.txt`. Do not build custom direct-HTTP clients unless the SDK blocks a required behavior.
- **Explicit retry wrapper:** Implement one explicit retry wrapper in repo code. Do not rely only on SDK implicit retries.
- **Retry schedule:** exactly 3 attempts total with delays:
  - before attempt 2: 5 seconds
  - before attempt 3: 15 seconds
  - no fourth attempt
  - the previously discussed `45s` delay is intentionally **not** used in this ticket because there are only 3 attempts total
- **Transient failures:** retry only for:
  - connection errors
  - timeouts
  - HTTP 429
  - HTTP 5xx
- **Fatal failures:** do not retry for:
  - missing API key
  - missing model id
  - invalid request / validation error
  - authentication / authorization failure
  - unsupported provider
  - malformed local input/context path
- **Provider roles:** A session has exactly two roles:
  - `drafter`
  - `reviewer`
- **Round semantics:** For each round `r`:
  1. `draft_r`
  2. `review_r`
  3. `revision_r`
- **Input visibility rules:**
  - `draft_1` sees:
    - original user prompt
    - selected mode
    - loaded context files
  - `review_r` sees:
    - original user prompt
    - selected mode
    - loaded context files
    - `draft_r`
  - `revision_r` sees:
    - original user prompt
    - selected mode
    - loaded context files
    - `draft_r`
    - `review_r`
  - `draft_(r+1)` sees:
    - original user prompt
    - selected mode
    - loaded context files
    - `revision_r`
- **No hidden full-history replay:** Do not send the entire full session history to every provider call unless explicitly required above.
- **Final summary:** Generate `final_summary.md` locally from structured session data. Do not make an extra provider call for the final summary in this ticket.
- **Preflight before first API call:** Validate:
  - CLI/workflow arguments
  - provider names
  - required model ids
  - required API keys for selected real providers
  - required default context files
  - extra context path validity and size limits
  before the first provider call.
- **Preflight failure atomicity:** If preflight fails, write **zero** output files.
- **Runtime failure persistence:** If preflight succeeded and a later provider call fails:
  - preserve all completed successful protocol steps
  - write `session.json`, `session.md`, and `final_summary.md`
  - mark session status accordingly
- **No scanner coupling:** Do not import from `scanner/` unless needed only for harmless path resolution. Prefer no scanner imports.
- **No repo writeback:** This ticket only produces local/session artifacts and workflow artifacts. No commits, no branches, no PRs.

## Implementation Notes (optional but useful)

### CLI contract
Extend the CLI so it can be called as:

```bash
python -m tools.ai_sparring.cli \
  --prompt "review this design" \
  --mode ticket_review \
  --rounds 2 \
  --drafter-provider openai \
  --drafter-model "<openai-model-id>" \
  --reviewer-provider anthropic \
  --reviewer-model "<anthropic-model-id>" \
  --context-path docs/canonical/ARCHITECTURE.md \
  --context-path tools/ai_sparring/cli.py \
  --output-dir /tmp/ai-sparring
```

### CLI defaults
Use these defaults if omitted:

- `--mode=ticket_review`
- `--rounds=1`
- `--drafter-provider=fake`
- `--reviewer-provider=fake`

### CLI validation
Rules:

- `prompt` is required and must be non-empty after stripping
- `mode` must be one of:
  - `ticket_review`
  - `implementation_planning`
  - `roadmap_review`
- `rounds` must be an integer in range `1..3`
- `drafter-provider` and `reviewer-provider` must each be one of:
  - `fake`
  - `openai`
  - `anthropic`
- if provider is `fake`, model id is optional and ignored in persisted contract as `null`
- if provider is `openai` or `anthropic`, the corresponding model id is required
- if `drafter-provider=openai` or `reviewer-provider=openai`, `OPENAI_API_KEY` is required
- if `drafter-provider=anthropic` or `reviewer-provider=anthropic`, `ANTHROPIC_API_KEY` is required
- `output-dir` is required
- each `--context-path` must be:
  - repo-relative
  - inside repository root
  - a regular file
  - UTF-8 decodable text
  - no larger than `153600` bytes (150 KiB)

### Context loading contract
The default context source list is always loaded first in this exact order:

1. `docs/AGENTS.md`
2. `docs/code_map.md`
3. `docs/canonical/ROADMAP.md`

Optional additional context files:
- are supplied with repeated `--context-path`
- are normalized to repo-relative POSIX-style paths
- are sorted lexicographically after normalization
- are appended after the default sources
- are de-duplicated while preserving first occurrence

No globbing in this ticket.
No automatic repo scan in this ticket.

### Provider interface contract
Normalize provider output to one internal contract so orchestration is provider-agnostic.

Each successful provider call must return at least:

- `provider`
- `model`
- `text`
- `attempts_used`
- `request_id` (if available from SDK/response, else `null`)

### Session state contract
`session.json` must contain at least:

```json
{
  "session_version": 2,
  "status": "completed",
  "mode": "ticket_review",
  "prompt": "review this design",
  "rounds_requested": 2,
  "rounds_completed": 2,
  "participants": {
    "drafter": {"provider": "openai", "model": "X"},
    "reviewer": {"provider": "anthropic", "model": "Y"}
  },
  "context_sources": [
    {"path": "docs/AGENTS.md", "bytes": 123},
    {"path": "docs/code_map.md", "bytes": 456},
    {"path": "docs/canonical/ROADMAP.md", "bytes": 789}
  ],
  "rounds": [
    {
      "index": 1,
      "draft": {...},
      "review": {...},
      "revision": {...},
      "delta_summary": "..."
    }
  ],
  "error": null
}
```

`status` must be one of:
- `completed`
- `failed_runtime`
- `failed_partial`

Use:
- `completed` when all requested rounds complete
- `failed_runtime` when preflight succeeded but no successful protocol step was recorded before failure
- `failed_partial` when at least one successful protocol step was recorded before failure

### Delta summary contract
For each completed round, persist a small deterministic local `delta_summary` string.
Do not make an extra provider call for delta generation.
A simple implementation is acceptable, for example a metadata-based summary that states:
- round index
- whether review and revision exist
- source provider/model pairs

### Workflow contract
Extend `.github/workflows/ai-sparring.yml` to support real-provider sessions with `workflow_dispatch` inputs:

- `prompt` (required)
- `mode` (default `ticket_review`)
- `rounds` (default `1`)
- `drafter_provider` (default `fake`)
- `drafter_model` (optional)
- `reviewer_provider` (default `fake`)
- `reviewer_model` (optional)
- `context_paths` (optional multiline string; one repo-relative path per line)

Workflow must:
- checkout repo
- setup Python
- install requirements and dev requirements
- pass secrets via environment
- run the CLI
- upload the generated output artifacts

### `.env.example`
Update `.env.example` to include additive placeholders for:
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`

Do not commit real secrets.

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.

1) Running the CLI with:
   - `drafter-provider=openai`
   - `reviewer-provider=anthropic`
   - valid model ids
   - valid API keys
   - valid context inputs
   succeeds and writes:
   - `session.json`
   - `session.md`
   - `final_summary.md`

2) The default context source list in `session.json` is always ordered exactly:
   - `docs/AGENTS.md`
   - `docs/code_map.md`
   - `docs/canonical/ROADMAP.md`
   before any optional extra context files.

3) Optional extra `--context-path` values are normalized, lexicographically sorted, de-duplicated, and appended after the default sources.

4) If a selected real provider is missing its required API key, the CLI exits during preflight with a clear validation error and writes **zero** output files.

5) If a selected real provider is missing its required model id, the CLI exits during preflight with a clear validation error and writes **zero** output files.

6) If any extra context path is outside repo root, missing, not text-decodable, or exceeds `153600` bytes, the CLI exits during preflight with a clear validation error and writes **zero** output files.

7) A completed 2-round session persists, for each round, exactly:
   - `draft`
   - `review`
   - `revision`
   - `delta_summary`

8) If a transient provider error occurs and then succeeds on a later retry within the allowed retry budget, the session completes successfully and the recorded provider call shows `attempts_used > 1`.

9) If a fatal provider error occurs after preflight and before any successful protocol step, session artifacts are still written and `session.json` has `status=failed_runtime`.

10) If a fatal or exhausted-transient provider error occurs after at least one successful protocol step, session artifacts are still written and `session.json` has `status=failed_partial` with all earlier successful protocol data preserved.

11) `final_summary.md` is generated locally from structured session data and does not require an additional provider API call.

12) The manual GitHub Actions workflow supports real-provider runs and uploads the produced artifacts.

13) Fake-provider execution from Ticket 01 continues to work after this ticket.

## Default-/Edgecase-Abdeckung (required for code tickets)

- **Config Defaults (Missing key -> Default):** ✅ (AC: #2, #3, #13 ; Test: `test_cli_runtime_defaults_keep_fake_providers`)
- **Config Invalid Value Handling:** ✅ (AC: #4, #5, #6 ; Test: `test_missing_api_key_fails_preflight`, `test_missing_model_id_fails_preflight`, `test_invalid_context_path_fails_preflight`)
- **Nullability / no bool() coercion:** ✅ (AC: #1, #7 ; Test: `test_fake_provider_model_persists_as_null`)
- **Not-evaluated vs failed separated:** ✅ (AC: #9, #10 ; Test: `test_failed_runtime_vs_failed_partial_statuses`)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (AC: #4, #5, #6 ; Test: `test_preflight_failure_writes_no_output_files`)
- **ID/filename Namespace collisions (if relevant):** ✅ (N/A — output directory is explicitly provided by caller; this ticket does not auto-generate session root paths)
- **Deterministic sorting / tie-breakers:** ✅ (AC: #2, #3 ; Test: `test_context_sources_have_stable_ordering`)

## Tests (required if logic changes)
- Unit:
  - `test_cli_runtime_defaults_keep_fake_providers`
  - `test_missing_api_key_fails_preflight`
  - `test_missing_model_id_fails_preflight`
  - `test_invalid_context_path_fails_preflight`
  - `test_context_sources_have_stable_ordering`
  - `test_fake_provider_model_persists_as_null`
  - `test_retry_retries_only_transient_failures`
  - `test_provider_contract_normalizes_request_id_and_attempts`
  - `test_round_protocol_is_draft_review_revision`
  - `test_failed_runtime_vs_failed_partial_statuses`

- Integration:
  - CLI run with mocked OpenAI and Anthropic SDK clients that completes 2 rounds and verifies the `session.json` contract
  - CLI run where round 2 fails after round 1 completed and verifies `failed_partial`
  - CLI run where first provider call fails fatally and verifies `failed_runtime`

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

- [x] No files under `scanner/` are changed
- [x] No real network/API calls are executed in tests
- [x] Workflow remains manual-only (`workflow_dispatch`)
- [x] No commit/push step is added to the workflow
- [x] Fake-provider fallback remains available
- [x] No repo writeback logic is introduced

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` for architecture/runtime/test behavior of `tools/ai_sparring/`
- [ ] Did **not** modify scanner runtime logic or outputs
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-26T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
