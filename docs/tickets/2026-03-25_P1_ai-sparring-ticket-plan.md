# AI Sparring Workbench — Recommended Ticket Sequence

This sequence is intentionally split into small, Codex-friendly tickets.
Each ticket should map to exactly **1 ticket -> 1 PR**.

## Recommended order

### Ticket 01 — Foundation + dry-run vertical slice
Create the isolated tool scaffold, canonical roadmap path, draft ticket folder, manual GitHub Actions workflow, fake provider, deterministic artifact outputs, and tests.

### Ticket 02 — Real provider integrations
Add OpenAI and Anthropic providers behind a shared provider interface, secrets handling, retry/error classification, and tests with mocked HTTP/API clients.

### Ticket 03 — Repo context loading
Add configurable context loading for:
- `docs/AGENTS.md`
- `docs/code_map.md`
- `docs/canonical/ROADMAP.md`
- selected code files
- selected test files

Include allowlist rules, size limits, and deterministic ordering.

### Ticket 04 — Session orchestration
Add round-based orchestration between provider A and provider B, including:
- round state
- visible deltas
- final summary
- strict preflight before writes

### Ticket 05 — GitHub Issue / comment-driven UI
Add issue-based session start and comment commands such as:
- `/continue`
- `/focus tests`
- `/focus architecture`
- `/stop`

### Ticket 06 — Ticket draft generation
Generate a Markdown ticket draft from the completed sparring session and attach it as:
- artifact
- session summary section
- optional file payload

### Ticket 07 — Repo writeback via branch + PR
Add optional safe writeback:
- create branch
- write draft file under `docs/tickets/drafts/`
- open PR

Do **not** push directly to `main`.

## Notes

- Ticket 01 should stay **artifact-only** and **fake-provider-only**.
- Ticket 02 should add real APIs, but still no issue-comment loop.
- Ticket 07 should be the first ticket that writes back into the repo.
