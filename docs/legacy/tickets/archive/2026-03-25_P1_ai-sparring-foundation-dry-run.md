> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] AI Sparring Foundation: isolated scaffold, canonical roadmap path, and artifact-only dry-run workflow

## Context / Source (optional)
We want to build an AI sparring workbench inside this repository, but as an isolated development tool rather than part of the scanner runtime path.

This first ticket must create a **small, deterministic, testable vertical slice** that proves:
- the repo-local tool layout,
- the default canonical context sources,
- a manual GitHub Actions entry point,
- deterministic session artifacts,
- and a safe foundation for later provider integration.

This ticket is for **Codex**. Do not guess missing behavior. If something is not explicit here, keep the scope minimal and deterministic.

## Goal
After this change, the repository contains a working **foundation** for AI sparring sessions that can be executed in a **dry-run / fake-provider mode** from both:
- local CLI
- manual GitHub Actions workflow (`workflow_dispatch`)

The tool must:
- live outside `scanner/`,
- read a fixed default set of repo context files,
- write deterministic session artifacts,
- upload those artifacts in GitHub Actions,
- and require **no real LLM API keys** in this ticket.

## Scope
Allowed files/modules to change or add:

- `.github/workflows/ai-sparring.yml`
- `tools/ai_sparring/__init__.py`
- `tools/ai_sparring/cli.py`
- `tools/ai_sparring/session.py`
- `tools/ai_sparring/context_loader.py`
- `tools/ai_sparring/output_writer.py`
- `tools/ai_sparring/providers/__init__.py`
- `tools/ai_sparring/providers/base.py`
- `tools/ai_sparring/providers/fake_provider.py`
- `tools/ai_sparring/.gitignore`
- `docs/canonical/ROADMAP.md`
- `docs/canonical/INDEX.md`
- `docs/tickets/drafts/.gitkeep`
- `tools/ai_sparring/tests/test_cli.py`
- `tools/ai_sparring/tests/test_context_loader.py`
- `tools/ai_sparring/tests/test_output_writer.py`
- `tools/ai_sparring/tests/test_docs_foundation.py`

You may add small helper modules under `tools/ai_sparring/` if needed, but do not expand beyond this feature slice.

## Out of Scope
Explicitly not part of this ticket:

- real OpenAI API integration
- real Anthropic API integration
- issue-comment-driven session control
- repo writeback of ticket drafts
- branch creation or PR creation
- any changes under `scanner/`
- any changes to scanner runtime behavior
- any changes to scanner output schema or pipeline logic
- any background loop between real models

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
  - There is no isolated AI sparring tool path in the repo.
  - There is no canonical roadmap file at a stable path.
  - There is no dedicated draft-ticket folder for future generated tickets.
  - There is no manual GitHub Actions entry point for AI sparring sessions.
  - There is no deterministic dry-run vertical slice for session artifacts.

- After:
  - `tools/ai_sparring/` exists as an isolated tool path.
  - `docs/canonical/ROADMAP.md` exists as the stable canonical roadmap path.
  - `docs/canonical/INDEX.md` includes the new roadmap document.
  - `docs/tickets/drafts/` exists.
  - A manual workflow `.github/workflows/ai-sparring.yml` exists.
  - A local CLI exists and supports fake-provider dry runs.
  - Running the tool writes deterministic session artifacts:
    - `session.json`
    - `session.md`
    - `final_summary.md`
  - GitHub Actions uploads the generated artifacts.

- Edge cases:
  - invalid CLI/workflow values fail during preflight, before any output files are written
  - missing default context files fail during preflight, before any output files are written
  - fake-provider execution must not require any secrets
  - output directory content must be deterministic for the same input and fake provider

- Backward compatibility impact:
  - additive only
  - no scanner runtime behavior changes
  - no existing report/schema changes
  - no existing workflow behavior changes

## Codex Implementation Guardrails (No-Guesswork, required for code tickets)

- **Config/defaults:** This ticket does **not** introduce scanner config parsing. Do not read `ScannerConfig`. Use explicit CLI/workflow argument defaults defined in this ticket only.
- **Default context sources:** The default context source list is exactly:
  1. `docs/AGENTS.md`
  2. `docs/code_map.md`
  3. `docs/canonical/ROADMAP.md`
- **No implicit repo-wide scan:** Do not auto-load arbitrary files from the repo. Only the explicit default context source list above is loaded in this ticket.
- **Fake provider only:** The provider implementation in this ticket is a deterministic fake provider. No real HTTP/API calls.
- **Preflight before writes:** Validate arguments and required context source paths before creating any output files.
- **No partial writes:** If preflight fails, no `session.json`, `session.md`, or `final_summary.md` may be created.
- **Determinism:** The fake provider output must be deterministic for the same input. Do not use random output.
- **No scanner coupling:** Do not import from `scanner/` unless needed only for harmless path resolution. Prefer no scanner imports at all.
- **No direct main-branch mutations:** This ticket only writes local/session artifacts and uploads workflow artifacts. No repo writeback logic.
- **Workflow permissions:** Keep the new workflow minimal. It must not contain a commit/push step.

## Implementation Notes (optional but useful)

### CLI contract
Implement a CLI entry point callable as:

```bash
python -m tools.ai_sparring.cli \
  --prompt "review this design" \
  --provider fake \
  --mode ticket_review \
  --rounds 1 \
  --output-dir /tmp/ai-sparring
```

### CLI defaults
Use these defaults if omitted:

- `--provider=fake`
- `--mode=ticket_review`
- `--rounds=1`

### CLI validation
Rules:

- `prompt` is required and must be non-empty after stripping
- `provider` must be one of the implemented providers in this ticket: `fake`
- `mode` must be one of:
  - `ticket_review`
  - `implementation_planning`
  - `roadmap_review`
- `rounds` must be an integer in range `1..3`
- `output-dir` is required

### Fake provider behavior
The fake provider must produce deterministic content that is obviously synthetic, for example:
- echo mode
- summary based on prompt and loaded context metadata
- no randomness
- no timestamps inside content payloads unless explicitly provided from outside

### Session artifacts
The output directory must contain exactly these files on success:

- `session.json`
- `session.md`
- `final_summary.md`

`session.json` must include at least:
- `provider`
- `mode`
- `rounds`
- `prompt`
- `context_sources` (ordered list of file paths)
- `status`
- `messages` (deterministic fake-provider output content)

`session.md` must be a readable Markdown rendering of the session.

`final_summary.md` must contain a compact summary suitable for human review.

### GitHub Actions workflow
Create a manual workflow:

- trigger: `workflow_dispatch`
- inputs:
  - `prompt` (required)
  - `mode` (default `ticket_review`)
  - `rounds` (default `1`)
- provider in this ticket is fixed to `fake`
- workflow must:
  - checkout repo
  - setup Python
  - install repo requirements and dev requirements
  - run the CLI
  - upload the generated artifacts

### Canonical roadmap file
Create:

- `docs/canonical/ROADMAP.md`

It can be a minimal placeholder in this ticket, but it must:
- exist
- be human-readable
- state that it is the stable canonical roadmap path for future AI sparring context loading

Also update:
- `docs/canonical/INDEX.md`

so the roadmap file is discoverable from the canonical index.

## Acceptance Criteria (deterministic)
Write these as verifiable statements. No “usually”, “roughly”, “should”.

1) Running the CLI with the fake provider and valid inputs succeeds and writes exactly:
   - `session.json`
   - `session.md`
   - `final_summary.md`
   into the requested output directory.

2) `session.json` contains the default ordered context source list:
   - `docs/AGENTS.md`
   - `docs/code_map.md`
   - `docs/canonical/ROADMAP.md`

3) If `--rounds` is outside `1..3`, the CLI exits with a clear validation error and does not create any of the three output files.

4) If any default context source file is missing, the CLI exits during preflight with a clear error and does not create any of the three output files.

5) `.github/workflows/ai-sparring.yml` can be triggered manually and uploads the generated output as a workflow artifact.

6) `docs/canonical/ROADMAP.md` exists and `docs/canonical/INDEX.md` references it.

7) No files under `scanner/` are added or modified by this ticket.

## Default-/Edgecase-Abdeckung (required for code tickets)

- **Config Defaults (Missing key → Default):** ✅ (AC: #1 ; Test: `test_cli_defaults_use_fake_mode_and_rounds`)
- **Config Invalid Value Handling:** ✅ (AC: #3 ; Test: `test_cli_rejects_invalid_rounds`)
- **Nullability / no bool() coercion:** ✅ (N/A — this ticket does not introduce nullable semantic fields or bool coercion logic)
- **Not-evaluated vs failed separated:** ✅ (N/A — fake-provider-only foundation ticket; no external evaluation/fetch state exists yet)
- **Strict/Preflight Atomicity (0 Partial Writes):** ✅ (AC: #3, #4 ; Test: `test_preflight_failure_writes_no_output_files`)
- **ID/filename Namespace collisions (if relevant):** ✅ (N/A — output directory is explicitly provided by caller; this ticket does not auto-generate session root paths)
- **Deterministic sorting / tie-breakers:** ✅ (AC: #2 ; Test: `test_context_sources_are_in_fixed_order`)

## Tests (required if logic changes)
- Unit:
  - `test_cli_defaults_use_fake_mode_and_rounds`
  - `test_cli_rejects_invalid_rounds`
  - `test_preflight_failure_writes_no_output_files`
  - `test_context_sources_are_in_fixed_order`
  - `test_fake_provider_output_is_deterministic`
  - `test_docs_foundation_roadmap_exists_and_index_references_it`

- Integration:
  - CLI invocation test that writes the three expected files into a temp directory and verifies content shape

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
- [x] No real network/API calls are introduced
- [x] Workflow remains manual-only (`workflow_dispatch`)
- [x] No commit/push step is added to the new workflow
- [x] Foundation is additive and isolated under `tools/ai_sparring/`

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Implemented code changes per Acceptance Criteria
- [ ] Updated canonical docs under `docs/canonical/` for the new roadmap path and index entry
- [ ] Did **not** modify scanner runtime logic or outputs
- [ ] PR created: exactly **1 ticket -> 1 PR**
- [ ] Ticket moved to `docs/legacy/tickets/` after PR is created

---

## Metadata (optional)
```yaml
created_utc: "2026-03-25T00:00:00Z"
priority: P1
type: feature
owner: codex
related_issues: []
```
