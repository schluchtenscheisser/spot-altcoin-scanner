# Codex Workflow — Independence Release Ticket Execution (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_WORKFLOW_CODEX
status: canonical
audience:
  - gpt_codex
  - humans
ticket_inbox: docs/tickets
ticket_in_progress: docs/tickets/_in_progress
ticket_archive: docs/legacy/tickets
canonical_root: docs/canonical
ai_context_helpers:
  - docs/AI_CONTEXT_CURRENT.md
  - docs/GPT_SNAPSHOT.md
navigation_only:
  - docs/code_map.md
one_ticket_one_pr: true
archive_ticket_in_same_pr: true
last_updated_utc: "2026-04-28T00:00:00Z"
```

## 0) Purpose and Scope
This workflow defines the mandatory implementation process for Codex in the post-T22 Independence Release repository.

It exists to prevent accidental reuse of stale legacy scanner assumptions, deprecated module paths, old scoring/ranking contracts, and obsolete output conventions.

Core rules:
- one ticket at a time,
- one ticket → one PR,
- stop on architecture conflicts,
- do not guess missing canonical truth.

---

## 1) Authority Hierarchy (binding)

### Level 1 — Current repository reality (strongest)
Includes current code, tests, schemas, GitHub Actions workflows, generated run artifacts, diagnostics, reports, manifests, and evaluation replay outputs.

This level is the strongest source for what currently exists.

### Level 2 — Build-spec authority where not superseded
Includes:
- `independence_release_gesamtkonzept_final.md`
- the 7 v2.1 section documents

Use as domain-intent authority where no newer current-state implementation contract or validated current-state documentation supersedes it.

### Level 3 — Current ticket
The ticket defines concrete task scope, acceptance criteria, and requested files/behavior.

The ticket does not override architecture contracts.

If a ticket conflicts with current repo reality, AI context, open questions, or implementation contracts: stop and surface the conflict.

### Level 4 — AI context helpers (not independent domain authority)
- `docs/AI_CONTEXT_CURRENT.md`
- `docs/GPT_SNAPSHOT.md`

These are routing/context aids.

### Level 5 — Structural navigation only
- `docs/code_map.md`

Generated structural navigation only. It can list active and legacy paths and must not be treated as architecture authority.

### Level 6 — Legacy / historical reference
Includes old scanner docs, old pre-Independence snapshots, legacy pipeline docs, old scoring/ranking/output docs, and archived ticket history.

Use only for historical understanding unless ticket scope explicitly requires it and current repo reality supports it.

---

## 2) Mandatory Pre-Read Order (before implementation)
1. Current ticket.
2. `docs/AI_CONTEXT_CURRENT.md`.
3. `docs/GPT_SNAPSHOT.md`.
4. `docs/canonical/WORKFLOW_CODEX.md` (this file; re-read if updated).
5. `docs/code_map.md` (navigation only).
6. Relevant current source files.
7. Relevant tests, schemas, and workflows.
8. Relevant v2.1 build-spec sections only where ticket touches domain logic not fully covered by current code/docs.
9. `open_questions.md` if unresolved domain logic may be affected.

Do not start coding before checking the active-vs-legacy boundary.

---

## 3) Ticket Role and Architecture Guardrails
- A ticket is a task scope contract, not an architecture override.
- If ticket instructions contradict active implementation contracts, stop and report.
- Do not silently reinterpret unresolved domain logic.

---

## 4) Active Independence Release Module Boundaries
Treat these module families as active by default:

```text
scanner/axes/
scanner/clients/
scanner/data/
scanner/decision/
scanner/entry/
scanner/evaluation/
scanner/execution/
scanner/features/
scanner/output/
scanner/phase/
scanner/runners/
scanner/state/
scanner/storage/
scanner/universe/
scanner/utils/
```

Active architecture includes:
- Daily Discovery,
- Intraday Promotion,
- Phase Interpreter,
- State Machine,
- Invalidation and Setup Cycle logic,
- Entry Pattern resolution,
- Decision Buckets,
- Execution subset evaluation,
- Diagnostics serialization,
- Evaluation Replay,
- Shadow-Live workflow.

---

## 5) Legacy / Reference-Only Boundaries
Treat the following as legacy/reference-only unless active execution paths prove otherwise:

```text
scanner/pipeline/
scanner/pipeline/decision.py
scanner/pipeline/global_ranking.py
scanner/pipeline/scoring/
legacy output modules
legacy ranking modules
legacy scoring modules
```

Rules:
- Do not edit `scanner/pipeline/*` as active Independence architecture unless ticket scope explicitly requires it and current execution paths justify it.
- Do not reintroduce legacy `decision.py`, global ranking, legacy scoring, BTC-regime multiplier scoring, or old output contracts as active behavior.
- If ticket appears to require legacy edits, verify active path usage first.

---

## 6) Canonical Mode and `scan_mode` Contracts

### SQLite / runner-level run metadata
Canonical persisted/runtime `run_metadata.scan_mode` values in the current implementation:

```text
daily
intraday
```

### Report / diagnostics output
Canonical report and diagnostics `scan_mode` values in the current implementation:

```text
daily
intraday
```

Rules:
- `daily` and `intraday` are the canonical persisted/runtime/report/diagnostics scan_mode values in current repo reality.
- `daily_discovery` and `intraday_promotion` may be used only as conceptual runner/workflow labels in docs/discussion.
- Do not enforce `daily_discovery` or `intraday_promotion` as SQLite `run_metadata.scan_mode` values unless an explicit future migration updates schema, all writers, and tests.
- Do not use `daily_discovery` or `intraday_promotion` as report/diagnostics output `scan_mode` values.
- Do not reintroduce legacy runtime modes as active Independence modes.

Deprecated/legacy active-mode assumptions:

```text
fast
standard
offline
backtest
```

---

## 7) Canonical Artifact Paths

### Run manifest
```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

### Diagnostics
```text
reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz
```

### Daily report
```text
reports/daily/YYYY/MM/DD/report.json
```

### Run reports
```text
reports/runs/YYYY/MM/DD/<run_id>/
```

### Report indexes
```text
reports/index/
```

### OHLCV history
```text
snapshots/history/ohlcv/
```

Expected partition shape:
```text
snapshots/history/ohlcv/timeframe=<1d|4h>/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/
```

### Allowed script / analysis output roots
```text
evaluation/exports/
artifacts/
reports/aux/
```

Rules:
- Do not write active outputs to `reports/analysis/`.
- Do not create report-side manifest files.
- Canonical manifest location is under `snapshots/runs/...` only.
- Shadow-Live outputs are GitHub Actions artifacts and are not committed repository outputs.

---

## 8) Canonical Bar ID Contracts

### Daily
```text
daily_bar_id = YYYY-MM-DD
```
Type: `str`

### Intraday / 4h
```text
intraday_bar_id = YYYY-MM-DDTHH:00:00Z
intraday_cache_bar_id = YYYY-MM-DDTHH:00:00Z
```
Type: `str`

Rules:
- Intraday IDs are UTC.
- Intraday IDs are 4h-aligned.
- `intraday_bar_id = null` for Daily output records.
- Integer `intraday_bar_id` values must not pass output schema validation.

---

## 9) Evaluation Replay Contract
- Evaluation Replay reads from run artifacts.
- Evaluation Replay must not use live SQLite as primary input.
- Point-in-time run artifacts are expected evaluation sources.

Expected sources include:
- run manifests,
- report JSON,
- diagnostics JSONL.GZ,
- snapshot/run artifacts.

---

## 10) No Automatic Order Execution
- The scanner does not execute trades.
- Execution/orderbook modules evaluate tradeability and execution quality only.
- Do not introduce automatic market orders, limit orders, position management, portfolio management, or exchange-side execution unless Martin explicitly approves new scope.

---

## 11) Deprecated Paths and Forbidden Active Assumptions
Never use the following as active Independence contracts:

```text
reports/analysis/
reports/YYYY-MM-DD.md
report-side run.manifest.json
fast / standard / offline / backtest as active scanner modes
report/diagnostics scan_mode = daily_discovery
report/diagnostics scan_mode = intraday_promotion
SQLite run_metadata.scan_mode = daily_discovery
SQLite run_metadata.scan_mode = intraday_promotion
global_score as active decision contract
GLOBAL_RANKING_TOP20 as active output contract
legacy BTC-regime multiplier scoring
legacy base_score + multiplier scoring
legacy scanner pipeline as target architecture
docs/canonical/VERIFICATION_FOR_AI.md as active Independence verification workflow
automatic order execution
```

`docs/canonical/VERIFICATION_FOR_AI.md` belongs to the old scoring/verification architecture and is not an active Independence verification workflow. T20 Smoke Test and T21/T21.1 diagnostics evaluation-readiness replace this structurally.

---

## 12) Stop Conditions (must halt and surface)
Stop before making changes if any applies:
1. Ticket conflicts with current repository reality.
2. Ticket conflicts with `docs/AI_CONTEXT_CURRENT.md` or current implementation contracts.
3. Ticket asks for active outputs in `reports/analysis/`.
4. Ticket introduces or requires report-side manifest files.
5. Ticket uses report/diagnostics `scan_mode = daily_discovery` or `intraday_promotion`.
6. Ticket introduces `daily_discovery` or `intraday_promotion` as persisted SQLite `run_metadata.scan_mode` values without explicit schema, writer, and test migration scope.
7. Ticket edits `scanner/pipeline/*` as active architecture without explicit justification.
8. Ticket reintroduces legacy global ranking, `global_score`, BTC-regime multipliers, or legacy base-score multipliers.
9. Ticket relies on live SQLite as primary Evaluation Replay input.
10. Ticket introduces automatic order execution.
11. Ticket makes or implies a domain-logic decision still unresolved in `open_questions.md`.
12. Ticket treats `missing_intraday_cycle_context` as a blocker without explicit instruction.
13. Ticket implicitly requires inventing new canonical truth beyond ticket scope, repo reality, or v2.1 build-spec authority.
14. Ticket implies archiving or moving v2.1 build-spec documents before validated current-state canonical documentation exists.

Do not silently resolve stop conditions.

---

## 13) Ticket Lifecycle (Inbox → In Progress → Archive)

### Inbox
Tickets live under:

```text
docs/tickets/
```

Select next ticket deterministically by lexicographic filename order, excluding:

```text
_TEMPLATE.md
docs/tickets/_in_progress/
```

### In progress
At ticket start, move to:

```text
docs/tickets/_in_progress/<original_filename>.md
```

### Archive
After implementation completion, move to:

```text
docs/legacy/tickets/<original_filename>.md
```

Add this header if missing:

```md
> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.
```

Do not use archived tickets as current architecture truth.

---

## 14) 1 Ticket → 1 PR (required)
Preserve:
- one ticket per PR,
- no bundling unrelated tickets,
- branch naming: `ticket/<ticket_slug>`.

PR title:

```text
Ticket: <ticket filename> — <short summary>
```

PR body must include:
- original ticket path,
- archived ticket path,
- implementation summary,
- docs impact summary,
- tests/verification performed,
- stop-condition or contract checks performed.

---

## 15) Execution Order
For each ticket:
1. Read mandatory context.
2. Check active-vs-legacy boundary.
3. Check stop conditions.
4. Move ticket to `_in_progress`.
5. Implement changes.
6. Update tests/schemas/docs only if required by ticket scope and current contracts.
7. Run targeted checks.
8. Move ticket to archive.
9. Prepare PR.

Important:
- Do not create new canonical documentation authority unless ticket explicitly asks.
- If validated current-state canonical doc exists and contract changes, update it.
- If no validated current-state canonical doc exists, do not invent canonical truth silently.
- Use current code/tests, run artifacts, v2.1 build-spec authority, and ticket scope.
- Stop on conflicts instead of guessing.

---

## 16) Completion Checklist
Before PR:
- [ ] Ticket moved to `_in_progress`.
- [ ] Mandatory context read.
- [ ] Active-vs-legacy boundary checked.
- [ ] Stop conditions checked.
- [ ] Code changes limited to ticket scope.
- [ ] No deprecated output paths introduced.
- [ ] No forbidden `scan_mode` usage introduced.
- [ ] No report-side manifest introduced.
- [ ] No legacy scoring/ranking contract reintroduced.
- [ ] No automatic order execution introduced.
- [ ] Tests or targeted checks run where applicable.
- [ ] Relevant docs updated only where applicable.
- [ ] Ticket archived in `docs/legacy/tickets/`.
- [ ] PR body includes docs impact and verification summary.

---

## 17) PR Expectations
Each ticket PR must be self-contained and should explain:
- what changed,
- why the change matches current architecture,
- which contracts were validated,
- which checks were run,
- whether any stop condition was considered and ruled out.

If no canonical docs changed, explicitly state why not.
