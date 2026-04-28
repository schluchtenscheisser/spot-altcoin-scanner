# GPT Snapshot — Independence Release Current Context

> Status: Current AI onboarding snapshot  
> Scope: Independence Release / MEXC Spot Altcoin Scanner  
> Last reviewed for: post-T1–T22 / T21.1 implementation state  
> Purpose: Fast context for ChatGPT, Claude, Codex and other AI-assisted development/review workflows.

---

## 1. Purpose of this snapshot

This file is a compact AI onboarding snapshot for the current Independence Release repository.

It is not the primary source of truth for domain logic. It summarizes the current implementation context, active architecture, deprecated assumptions, and operational boundaries so that AI agents do not accidentally rely on stale pre-Independence scanner concepts.

If this file conflicts with the current repository code, tests, current run artifacts, or the still-active v2.1 build specifications, do not infer silently. Flag the conflict and ask Martin for a decision.

---

## 2. Authority hierarchy

Use this hierarchy when resolving conflicts:

1. Current repository code, tests, schemas, workflows, and generated run artifacts.
2. The v2.1 section documents and `independence_release_gesamtkonzept_final.md`, as historical build specifications that remain authoritative where no newer current-state documentation or implementation contract supersedes them.
3. Ticket history T1–T22 / T21.1, as implementation history and rationale.
4. `docs/AI_CONTEXT_CURRENT.md`, as current AI-context routing and status guidance.
5. `docs/code_map.md`, as an auto-generated structural map only.
6. Archived legacy scanner documentation and archived pre-Independence snapshots, as historical reference only.

The v2.1 section documents and the Gesamtkonzept were the build specification for the Independence Release. They should not be treated as obsolete legacy scanner documentation. They should also not be treated as complete current-state documentation after T1–T22. They remain a build-spec authority until replaced by validated current-state canonical documentation.

`open_questions.md` and `feature_enhancements.md` are not part of the build-spec archive scope by default. They are maintained planning / tracking documents and must be reviewed separately before any relocation or archival decision.

---

## 3. Current implementation status

The repository has been migrated into the Independence Release architecture.

Implemented scope:
- T1–T22 are implemented.
- T21.1 is implemented.
- Shadow-Live Daily is active / available.
- Daily Discovery and Intraday Promotion are the active scanner modes.
- T20 Smoke Test verifies technical executability.
- T21 / T21.1 make diagnostics evaluation-ready.
- T22 introduces the Shadow-Live workflow.

Current operational focus:
- Shadow-Live Daily data collection.
- Diagnostics review.
- Evaluation-readiness validation.
- No new tickets unless explicitly approved by Martin.

Important limitation:
- Intraday Carry-Forward is not yet final productive behavior.
- `missing_intraday_cycle_context` is a known non-blocking state and must not be treated as a blocker or bug by default.

---

## 4. Active architecture overview

The Independence Release is a layered scanner architecture for MEXC spot altcoins.

High-level processing order:

1. Universe discovery and eligibility
2. OHLCV fetch and cache policy
3. Raw feature calculation
4. Tier-1 axes
5. Tier-2 simplified axes
6. Phase Interpreter
7. State Machine
8. Entry Pattern resolution
9. Execution / orderbook evaluation for reduced subsets
10. Decision Buckets and ranking
11. Reports, diagnostics, manifests and run artifacts
12. Evaluation Replay from run artifacts

The active target architecture is not the old legacy scoring pipeline.

---

## 5. Active module families

The following module families represent the active Independence Release architecture:

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

Key active concepts:
- Tier-1 axes
- Tier-2 simplified axes
- Phase Interpreter
- State Machine
- Invalidation and Setup Cycle logic
- Entry Patterns
- Decision Buckets
- Execution subset evaluation
- Daily Discovery Runner
- Intraday Promotion Runner
- Diagnostics serialization
- Evaluation Replay
- Shadow-Live workflow

---

## 6. Legacy / reference-only module families

The old scanner pipeline may still exist in the repository for historical, reference, or transitional reasons.

Treat the following as legacy/reference-only unless current code paths explicitly prove otherwise:

```text
scanner/pipeline/
scanner/pipeline/decision.py
scanner/pipeline/global_ranking.py
scanner/pipeline/scoring/
legacy scoring modules
legacy global ranking modules
legacy output modules
```

Do not use these as the active Independence Release architecture:
- legacy `decision.py`
- legacy global ranking
- legacy base score / multiplier scoring
- legacy BTC-regime scoring multiplier
- legacy report output assumptions
- legacy shortlist semantics

If an implementation task appears to require editing a legacy module, first verify whether the active Independence Release path actually uses it.

---

## 7. Canonical modes and scan_mode fields

There are two different `scan_mode` contexts. Do not conflate them.

### Runner-level / SQLite run metadata

SQLite `run_metadata.scan_mode` uses runner-level values:

```text
daily_discovery
intraday_promotion
```

These are the canonical runner-level / persisted run metadata values.

### Output-level / Report and diagnostics

Report and diagnostics output `scan_mode` uses compact output-level values:

```text
daily
intraday
```

Rules:
- Do not use `daily_discovery` or `intraday_promotion` as values in report/diagnostics output `scan_mode`.
- Do not use `daily` or `intraday` as runner-level / SQLite `run_metadata.scan_mode` values.
- Always check which context a `scan_mode` field belongs to before changing code, schema, tests, or documentation.

Invalid / legacy active-mode assumptions:
- `fast`
- `standard`
- `offline`
- `backtest`

These may exist in old docs or historical files but are not active Independence Release runtime modes.

---

## 8. Canonical bar identifiers

Canonical Daily bar ID:

```text
daily_bar_id = YYYY-MM-DD
```

Canonical Intraday / 4h bar ID:

```text
intraday_bar_id = YYYY-MM-DDTHH:00:00Z
intraday_cache_bar_id = YYYY-MM-DDTHH:00:00Z
```

Rules:
- Bar IDs are strings in canonical output schemas.
- `daily_bar_id` is set for daily-context records.
- `intraday_bar_id = null` for Daily output records.
- `intraday_bar_id` is required as a canonical 4h-aligned UTC string for Intraday output records.
- Integer `intraday_bar_id` values must not be accepted in output schema validation.
- Intraday bar IDs are UTC.
- Intraday bar IDs are 4h-aligned.
- Do not use local-time or loosely formatted timestamps for canonical bar IDs.

Future documentation note:
- `docs/canonical/DATA_MODEL.md` is expected to become the current-state documentation location for canonical cross-layer field types such as `daily_bar_id: str (YYYY-MM-DD)`.
- Until that current-state document exists and is validated, use current code/tests plus the v2.1 build-spec and ticket contracts as authority.

---

## 9. Canonical artifact paths

Run manifest:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

Current diagnostics:

```text
reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz
```

OHLCV long-term history:

```text
snapshots/history/ohlcv/
```

Expected OHLCV partitioning pattern:

```text
snapshots/history/ohlcv/timeframe=<1d|4h>/symbol=<SYMBOL>/year=<YYYY>/month=<MM>/
```

Reports:

```text
reports/runs/YYYY/MM/DD/<run_id>/
reports/daily/YYYY/MM/DD/report.json
reports/index/
```

Allowed script / analysis output roots:

```text
evaluation/exports/
artifacts/
reports/aux/
```

Important:
- There are no report-side manifest files.
- `run.manifest.json` is canonical only under `snapshots/runs/...`.
- `reports/analysis/` is deprecated and must not be used as an active output path.
- Script and analysis outputs must not be written to `reports/analysis/`; use `evaluation/exports/`, `artifacts/`, or `reports/aux/` depending on artifact class.
- Shadow-Live writes outputs as GitHub Actions artifacts, not as committed repo artifacts.

---

## 10. Evaluation Replay

Evaluation Replay reads from run artifacts.

It must not depend on live SQLite as its primary input.

Expected source categories:
- run manifests
- report JSON
- diagnostics JSONL.GZ
- snapshot/run artifacts

Evaluation should preserve point-in-time semantics and avoid reconstructing decisions from mutable live state.

---

## 11. Diagnostics and reports

Diagnostics are intended to be evaluation-ready after T21 / T21.1.

Important expectations:
- Diagnostics are run-artifact based.
- Diagnostics should preserve enough per-symbol information for later evaluation.
- Diagnostics should not rely on deprecated `reports/analysis` output.
- Diagnostics output `scan_mode` must be `daily` or `intraday`.

---

## 12. Execution and trading boundary

The scanner does not perform automatic order execution.

Execution/orderbook logic evaluates tradeability and execution quality for reduced subsets. It does not place trades.

Do not introduce:
- automatic market orders
- automatic limit orders
- exchange-side execution
- position management
- portfolio management

unless Martin explicitly approves a new scope.

---

## 13. Deprecated paths and forbidden active assumptions

The following must not be used as active Independence Release assumptions:

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
automatic order execution
```

Use these instead for script / analysis outputs when appropriate:

```text
evaluation/exports/
artifacts/
reports/aux/
```

If deprecated assumptions appear in old docs, snapshots, comments, or generated maps, treat them as historical unless current active code and Martin-confirmed contracts say otherwise.

---

## 14. Current known non-blocking states

Known non-blocking state:

```text
missing_intraday_cycle_context
```

Interpretation:
- This can occur because Intraday Carry-Forward is not final productive behavior yet.
- It should be surfaced diagnostically.
- It should not automatically fail Shadow-Live Daily or invalidate the current implementation.

---

## 15. Maintenance rule

Update this snapshot after any pull request that changes one or more of:

- active runner entrypoints
- runner-level / SQLite `run_metadata.scan_mode`
- report/diagnostics output `scan_mode`
- artifact paths
- manifest policy
- diagnostics schema or serialization
- evaluation replay inputs
- Shadow-Live workflows
- active vs legacy module boundaries
- canonical bar ID semantics
- no-trading boundary
- major config structure
- current implementation status

If the snapshot is not updated after such a change, mark it stale rather than letting AI agents rely on outdated assumptions.
