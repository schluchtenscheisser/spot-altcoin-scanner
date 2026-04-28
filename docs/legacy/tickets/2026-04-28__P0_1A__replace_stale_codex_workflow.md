> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# Ticket 0.1A — Replace stale Codex workflow with Independence-safe workflow

## Status

Ready for Codex implementation.

## Objective

Replace `docs/canonical/WORKFLOW_CODEX.md` with an Independence Release-safe Codex workflow.

The current file still reflects the pre-Independence / legacy scanner workflow and incorrectly treats generated AI helper files and old canonical scoring/ranking/output docs as active authority. The new workflow must prevent Codex from using stale scanner assumptions, legacy pipeline modules, deprecated paths, or outdated scoring/ranking workflows when implementing future tickets.

This ticket is documentation-only.

---

## Background

Phase 0 has reset the AI context layer:

- `docs/AI_CONTEXT_CURRENT.md` now defines current AI-context routing.
- `docs/GPT_SNAPSHOT.md` has been regenerated for the current Independence Release context.
- The old GPT snapshot has been archived.
- The stale addendum has been marked superseded.

However, `docs/canonical/WORKFLOW_CODEX.md` still contains old Codex workflow rules. It currently routes Codex toward legacy concepts such as old scoring docs, global ranking, old output schema, and `VERIFICATION_FOR_AI.md`.

That is unsafe because Codex uses this file as a workflow base when implementing new tickets.

---

## Scope

Update only:

```text
docs/canonical/WORKFLOW_CODEX.md
```

No code changes.

No code-map generator changes.

No movement or archival of v2.1 build-spec files.

No broad documentation migration.

No rewrite of unrelated canonical documentation.

---

## Required outcome

`docs/canonical/WORKFLOW_CODEX.md` must become a current Codex implementation workflow for the post-T22 Independence Release repository.

It must clearly define:

1. Purpose and scope of the workflow.
2. Mandatory pre-read order.
3. Correct authority hierarchy.
4. Ticket role as task scope, not architecture override.
5. Active Independence Release module boundaries.
6. Legacy/reference-only module boundaries.
7. Canonical mode and `scan_mode` contracts.
8. Canonical artifact paths.
9. Allowed script / analysis output roots.
10. Deprecated paths and forbidden active assumptions.
11. Stop conditions.
12. Ticket lifecycle mechanics.
13. Completion checklist.
14. PR expectations.

---

## Required authority hierarchy

Replace the old authority hierarchy with this hierarchy:

### Level 1 — Current repository reality

Includes:

- current code,
- tests,
- schemas,
- GitHub Actions workflows,
- generated run artifacts,
- diagnostics,
- reports,
- manifests,
- evaluation replay outputs.

This is the strongest source for what currently exists.

### Level 2 — Build-spec authority where not superseded

Includes:

- the 7 v2.1 section documents,
- `independence_release_gesamtkonzept_final.md`.

These documents remain build-spec authority for domain intent and unresolved details where no newer current-state implementation contract or validated current-state documentation supersedes them.

They are not ordinary legacy scanner docs.

### Level 3 — Current ticket

The ticket defines:

- the concrete task,
- scope,
- acceptance criteria,
- requested files or behavior.

The ticket does not override architecture contracts.

If the ticket conflicts with current repository reality, current AI context, open questions, or implementation contracts, Codex must stop and surface the conflict.

### Level 4 — AI context helpers

Includes:

```text
docs/AI_CONTEXT_CURRENT.md
docs/GPT_SNAPSHOT.md
```

These are context and routing aids. They are not independent domain authority.

### Level 5 — Structural navigation

Includes:

```text
docs/code_map.md
```

The code map is generated structural navigation only.

It may list both active and legacy files. It must not be treated as architecture authority.

### Level 6 — Legacy / historical reference

Includes:

- old scanner docs,
- old pre-Independence snapshots,
- legacy pipeline docs,
- old scoring/ranking/output docs,
- archived ticket history.

Use only for historical understanding unless the ticket explicitly says otherwise and current repo reality supports it.

---

## Mandatory pre-read order

Codex must read, in this order, before implementing a ticket:

1. The current ticket.
2. `docs/AI_CONTEXT_CURRENT.md`.
3. `docs/GPT_SNAPSHOT.md`.
4. `docs/canonical/WORKFLOW_CODEX.md` — this document; re-read if newly updated.
5. `docs/code_map.md` as structural navigation only.
6. Relevant current source files.
7. Relevant tests, schemas, and workflows.
8. Relevant v2.1 build-spec sections only where the ticket touches domain logic not fully covered by current code/docs.
9. `open_questions.md` if the ticket touches unresolved domain logic.

Codex must not start coding before checking the current active-vs-legacy boundary.

---

## Active Independence Release module families

The workflow must identify these as active Independence Release module families:

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

The workflow must mention that active architecture includes:

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

## Legacy / reference-only module families

The workflow must clearly mark the following as legacy/reference-only unless current active code paths prove otherwise:

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

- Do not edit `scanner/pipeline/*` as active Independence Release architecture unless the ticket explicitly requires it and current execution paths justify it.
- Do not reintroduce legacy `decision.py`, global ranking, legacy scoring, BTC-regime multipliers, or old output contracts as active Independence Release behavior.
- If the ticket appears to require legacy module edits, Codex must first verify whether the active Independence Release path actually uses those modules.

---

## Canonical mode and scan_mode contracts

The workflow must explicitly distinguish the two `scan_mode` contexts.

### SQLite / runner-level run metadata

Valid `run_metadata.scan_mode` values:

```text
daily_discovery
intraday_promotion
```

### Report / diagnostics output

Valid report and diagnostics `scan_mode` values:

```text
daily
intraday
```

Rules:

- Do not use `daily_discovery` or `intraday_promotion` as report/diagnostics output `scan_mode` values.
- Do not use `daily` or `intraday` as SQLite `run_metadata.scan_mode` values.
- Do not reintroduce legacy runtime modes as active Independence Release modes.

Deprecated / legacy active-mode assumptions:

```text
fast
standard
offline
backtest
```

---

## Canonical artifact paths

The workflow must include these current artifact contracts:

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
- The canonical manifest location is only under `snapshots/runs/...`.
- Shadow-Live outputs are GitHub Actions artifacts, not committed repository outputs.

---

## Canonical bar ID contracts

The workflow must include these field contracts:

### Daily

```text
daily_bar_id = YYYY-MM-DD
```

Type:

```text
str
```

### Intraday / 4h

```text
intraday_bar_id = YYYY-MM-DDTHH:00:00Z
intraday_cache_bar_id = YYYY-MM-DDTHH:00:00Z
```

Type:

```text
str
```

Rules:

- Intraday IDs are UTC.
- Intraday IDs are 4h-aligned.
- `intraday_bar_id = null` for Daily output records.
- Integer `intraday_bar_id` values must not pass output schema validation.

---

## Evaluation Replay contract

The workflow must state:

- Evaluation Replay reads from run artifacts.
- Evaluation Replay must not use live SQLite as its primary input.
- Point-in-time run artifacts are the expected evaluation source.

Expected sources include:

```text
run manifests
report JSON
diagnostics JSONL.GZ
snapshot/run artifacts
```

---

## No automatic order execution

The workflow must state:

- The scanner does not execute trades.
- Execution/orderbook modules evaluate tradeability and execution quality only.
- Codex must not introduce automatic market orders, limit orders, position management, portfolio management, or exchange-side order execution unless Martin explicitly approves a new scope.

---

## Deprecated paths and forbidden active assumptions

The workflow must include a forbidden-assumptions section.

Codex must not use these as active Independence Release contracts:

```text
reports/analysis/
reports/YYYY-MM-DD.md
report-side run.manifest.json
fast / standard / offline / backtest as active scanner modes
report/diagnostics scan_mode = daily_discovery
report/diagnostics scan_mode = intraday_promotion
SQLite run_metadata.scan_mode = daily
SQLite run_metadata.scan_mode = intraday
global_score as active decision contract
GLOBAL_RANKING_TOP20 as active output contract
legacy BTC-regime multiplier scoring
legacy base_score + multiplier scoring
legacy scanner pipeline as target architecture
docs/canonical/VERIFICATION_FOR_AI.md as active Independence verification workflow
automatic order execution
```

`docs/canonical/VERIFICATION_FOR_AI.md` belongs to the old scoring / verification architecture and must not be treated as an active Independence Release verification workflow. T20 Smoke Test and T21/T21.1 diagnostics evaluation-readiness replace that role structurally in the current architecture.

---

## Stop conditions

Codex must stop and surface the conflict before making changes if any of the following applies:

1. The ticket conflicts with current repository reality.
2. The ticket conflicts with `docs/AI_CONTEXT_CURRENT.md` or current implementation contracts.
3. The ticket asks to write active outputs to `reports/analysis/`.
4. The ticket introduces or requires report-side manifest files.
5. The ticket uses report/diagnostics `scan_mode = daily_discovery` or `intraday_promotion`.
6. The ticket uses SQLite `run_metadata.scan_mode = daily` or `intraday`.
7. The ticket edits `scanner/pipeline/*` as active architecture without explicit justification.
8. The ticket reintroduces legacy global ranking, `global_score`, BTC-regime multiplier scoring, or legacy base-score multiplier scoring.
9. The ticket relies on live SQLite as primary Evaluation Replay input.
10. The ticket introduces automatic order execution.
11. The ticket makes or implies a domain-logic decision that is still listed as open in `open_questions.md`.
12. The ticket treats `missing_intraday_cycle_context` as a blocker without explicit instruction.
13. The ticket implicitly requires Codex to invent new canonical-truth content that is not covered by the ticket scope, current repo reality, or the v2.1 build-spec — meaning Codex would be filling gaps by guessing.
14. The ticket implies archiving or moving the v2.1 build-spec documents before validated current-state canonical documentation exists.

When a stop condition is hit, Codex must not silently resolve it. Codex must report the conflict in the PR notes or stop before implementation, depending on the operating context.

---

## Ticket lifecycle

Preserve the existing one-ticket / one-PR workflow unless repo reality says otherwise.

### Inbox

Tickets are located under:

```text
docs/tickets/
```

Codex should select the next ticket deterministically by lexicographic filename order, excluding:

```text
_TEMPLATE.md
docs/tickets/_in_progress/
```

### In progress

When Codex starts a ticket, move it to:

```text
docs/tickets/_in_progress/<original_filename>.md
```

### Archive

When implementation is complete, move the ticket to:

```text
docs/legacy/tickets/<original_filename>.md
```

Add this header if not already present:

```md
> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.
```

Do not use archived tickets as current architecture truth.

---

## 1 ticket → 1 PR

Preserve:

- one ticket per PR,
- no bundling unrelated tickets,
- branch naming:

```text
ticket/<ticket_slug>
```

PR title:

```text
Ticket: <ticket filename> — <short summary>
```

PR body must include:

- original ticket path,
- archived ticket path,
- implementation summary,
- docs impact summary,
- tests / verification performed,
- any stop-condition or contract checks performed.

---

## Execution order

For each ticket:

1. Read mandatory context.
2. Check active-vs-legacy boundary.
3. Check stop conditions.
4. Move ticket to `_in_progress`.
5. Implement changes.
6. Update relevant tests/schemas/docs only if required by ticket scope and current contracts.
7. Run targeted checks.
8. Move ticket to archive.
9. Prepare PR.

Important:

- Do not create new canonical documentation authority unless the ticket explicitly asks for it.
- If a validated current-state canonical doc exists and the ticket changes its contract, update it.
- If no validated current-state canonical doc exists, do not invent a new canonical truth silently.
- Use current code/tests, run artifacts, v2.1 build-spec authority, and ticket scope to determine the safe implementation path.
- Stop on conflicts instead of guessing.

---

## Completion checklist

Before PR, Codex must verify:

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

## Acceptance criteria

- `docs/canonical/WORKFLOW_CODEX.md` no longer lists `docs/code_map.md` or `docs/GPT_SNAPSHOT.md` as authoritative documents.
- `docs/canonical/WORKFLOW_CODEX.md` no longer routes active implementation work to old scoring/global-ranking/output verification docs as current Independence Release workflow.
- `docs/canonical/WORKFLOW_CODEX.md` clearly states that `docs/code_map.md` is generated structural navigation only.
- `docs/canonical/WORKFLOW_CODEX.md` clearly states that `docs/AI_CONTEXT_CURRENT.md` and `docs/GPT_SNAPSHOT.md` are AI context helpers only.
- `docs/canonical/WORKFLOW_CODEX.md` includes the correct authority hierarchy.
- `docs/canonical/WORKFLOW_CODEX.md` includes the mandatory pre-read order.
- `docs/canonical/WORKFLOW_CODEX.md` includes active and legacy module boundaries.
- `docs/canonical/WORKFLOW_CODEX.md` includes the two-context `scan_mode` contract.
- `docs/canonical/WORKFLOW_CODEX.md` includes canonical artifact paths.
- `docs/canonical/WORKFLOW_CODEX.md` includes allowed script / analysis output roots.
- `docs/canonical/WORKFLOW_CODEX.md` includes the forbidden assumptions list.
- `docs/canonical/WORKFLOW_CODEX.md` includes all stop conditions listed in this ticket.
- `docs/canonical/WORKFLOW_CODEX.md` preserves one-ticket / one-PR workflow unless repo reality requires otherwise.
- No files other than `docs/canonical/WORKFLOW_CODEX.md` are changed.

---

## Verification

Because this is documentation-only, verification is text-based.

Required checks:

1. Search `docs/canonical/WORKFLOW_CODEX.md` and confirm it does not treat these as active authority:
   - `docs/code_map.md`
   - `docs/GPT_SNAPSHOT.md`
   - `docs/canonical/VERIFICATION_FOR_AI.md`
   - `GLOBAL_RANKING_TOP20`
   - legacy scoring docs

2. Search `docs/canonical/WORKFLOW_CODEX.md` and confirm it contains:
   - `docs/AI_CONTEXT_CURRENT.md`
   - `daily_discovery`
   - `intraday_promotion`
   - `daily`
   - `intraday`
   - `reports/analysis/`
   - `snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`
   - `reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz`
   - `evaluation/exports/`
   - `artifacts/`
   - `reports/aux/`
   - `missing_intraday_cycle_context`
   - `open_questions.md`

3. Confirm no code files were changed.

4. Confirm `docs/code_map.md` was not manually edited in this ticket.

---

## Out of scope

- Updating `scripts/update_codemap.py`.
- Regenerating `docs/code_map.md`.
- Moving or archiving v2.1 section documents.
- Creating new current-state canonical docs.
- Updating `docs/AI_CONTEXT_CURRENT.md`.
- Updating `docs/GPT_SNAPSHOT.md`.
- Changing code, tests, schemas, workflows, or run artifacts.
