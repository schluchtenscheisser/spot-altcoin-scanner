# AI Context Current — Independence Release

> Status: Current AI-context routing document  
> Scope: Independence Release / MEXC Spot Altcoin Scanner  
> Purpose: Prevent AI agents from using stale pre-Independence scanner assumptions.

---

## 1. What this document is

This document is a compact routing and context document for ChatGPT, Claude, Codex, and other AI-assisted workflows.

It explains:
- which documentation is authoritative for what purpose,
- which architecture is currently active,
- which older files are historical or legacy,
- which paths and assumptions must not be used as active Independence Release contracts.

This document is not a full current-state technical manual.

It does not override:
- current repository code,
- tests,
- schemas,
- workflows,
- run artifacts,
- v2.1 section documents,
- `independence_release_gesamtkonzept_final.md`,
- or future validated current-state canonical documentation.

If there is a conflict, flag it explicitly. Do not silently choose one source.

---

## 2. Current project status

The repository is now in the post-Independence-Release implementation phase.

Current implementation status:
- T1–T22 are implemented.
- T21.1 is implemented.
- Shadow-Live Daily is active / available.
- Daily Discovery and Intraday Promotion are the active scanner modes.
- T20 Smoke Test verifies technical executability.
- T21 / T21.1 make diagnostics evaluation-ready.
- T22 introduces the Shadow-Live workflow.

Current operational focus:
- Collect Shadow-Live Daily data.
- Review diagnostics.
- Validate evaluation-readiness.
- Do not create or assume new tickets unless Martin explicitly approves.

Known non-blocking state:
- `missing_intraday_cycle_context`

This state is currently known and non-blocking because Intraday Carry-Forward is not yet final productive behavior.

---

## 3. Authority hierarchy

Use the following hierarchy:

### Level 1 — Current repository reality

Includes:
- current code,
- tests,
- schemas,
- GitHub Actions workflows,
- generated run artifacts,
- diagnostics,
- manifests,
- reports,
- evaluation replay outputs.

This is the strongest source for what currently exists.

### Level 2 — Build-spec authority

Includes:
- the 7 v2.1 section documents,
- `independence_release_gesamtkonzept_final.md`.

These were the build specifications for the Independence Release.

They are not ordinary legacy scanner docs. They remain authoritative for domain intent and unresolved details where no newer current-state documentation or implementation contract supersedes them.

They should later be moved to a historical build-spec archive only after validated current-state canonical documentation exists.

Important exception:
- `open_questions.md` and `feature_enhancements.md` are maintained planning / tracking documents.
- They are not automatically part of the future build-spec archive move.
- Review them separately before any relocation, archival, or superseding decision.

Future current-state documentation note:
- `docs/canonical/DATA_MODEL.md` is expected to become the current-state documentation location for canonical cross-layer data fields such as `daily_bar_id: str (YYYY-MM-DD)`.
- If this file does not yet exist or has not yet been validated against repo reality, do not treat it as available authority.
- Until validated current-state canonical documentation exists, rely on current code/tests, run artifacts, v2.1 build-spec documents, and ticket contracts.

### Level 3 — Implementation history

Includes:
- tickets T1–T22,
- T21.1,
- review notes,
- implementation rationale.

Use these to understand how and why the current repo reached its present state.

### Level 4 — AI support artifacts

Includes:
- `docs/GPT_SNAPSHOT.md`,
- `docs/code_map.md`,
- this file.

These are AI onboarding and navigation aids. They are not independent domain authority.

### Level 5 — Historical / legacy reference

Includes:
- old scanner documentation,
- pre-Independence GPT snapshots,
- legacy pipeline docs,
- old output/ranking/scoring docs.

Use only for historical understanding unless Martin explicitly says otherwise.

---

## 4. Active architecture

The active Independence Release architecture is layered.

Active module families:

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

Core active concepts:
- Universe discovery
- Eligibility
- OHLCV history and cache policy
- Tier-1 axes
- Tier-2 simplified axes
- Phase Interpreter
- State Machine
- Structural and timing invalidation
- Setup Cycle handling
- Entry Pattern resolution
- Execution subset evaluation
- Decision Buckets
- Diagnostics serialization
- Evaluation Replay
- Daily Discovery Runner
- Intraday Promotion Runner
- Shadow-Live workflow

Future documentation note:
- Full current-state architecture documentation should later live in validated canonical docs such as `docs/canonical/ARCHITECTURE.md`, `docs/canonical/DATA_MODEL.md`, `docs/canonical/RUNTIME_AND_OPERATIONS.md`, and related files.
- Do not assume those files already exist or are already validated unless repo reality confirms it.

---

## 5. Legacy / reference-only architecture

The old scanner pipeline may still exist in the repository.

Treat the following as legacy/reference-only unless current active code paths explicitly prove otherwise:

```text
scanner/pipeline/
scanner/pipeline/decision.py
scanner/pipeline/global_ranking.py
scanner/pipeline/scoring/
legacy output modules
legacy ranking modules
legacy scoring modules
```

Do not treat these as active Independence Release contracts:
- old `decision.py`,
- old global ranking,
- old base score / multiplier scoring,
- old BTC-regime multiplier,
- old shortlist-centered architecture,
- old report paths.

If an AI task appears to require editing these files, first verify whether the active Independence Release architecture actually uses them.

---

## 6. Canonical modes and scan_mode fields

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

Deprecated / legacy active-mode assumptions:
- `fast`
- `standard`
- `offline`
- `backtest`

---

## 7. Canonical bar IDs

Daily:

```text
daily_bar_id = YYYY-MM-DD
```

Intraday / 4h:

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
- UTC only.
- 4h-aligned.
- Closed-bar semantics.
- Do not use local-time or ambiguous timestamp strings for canonical bar IDs.

Future documentation note:
- `docs/canonical/DATA_MODEL.md` should later declare canonical cross-layer field types such as `daily_bar_id: str (YYYY-MM-DD)`.
- If that file does not exist yet, do not invent a parallel data-model authority.

---

## 8. Canonical artifact paths

Run manifest:

```text
snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json
```

Diagnostics:

```text
reports/runs/YYYY/MM/DD/<run_id>/symbol_diagnostics.jsonl.gz
```

OHLCV long-term history:

```text
snapshots/history/ohlcv/
```

Expected OHLCV partition shape:

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

Rules:
- No report-side manifest files.
- The canonical manifest is only under `snapshots/runs/...`.
- `reports/analysis/` is deprecated and must not be used as an active output path.
- Script and analysis outputs must not be written to `reports/analysis/`; use `evaluation/exports/`, `artifacts/`, or `reports/aux/` depending on artifact class.
- Shadow-Live writes artifacts as GitHub Actions artifacts, not as committed repository outputs.

---

## 9. Evaluation Replay

Evaluation Replay reads from run artifacts, not live SQLite.

Expected inputs:
- run manifests,
- reports,
- diagnostics,
- snapshot/run artifacts.

Do not reconstruct evaluation from mutable live state if point-in-time run artifacts are available.

---

## 10. No automatic order execution

The scanner does not execute trades.

Execution/orderbook modules evaluate tradeability, liquidity, slippage, and execution quality for reduced subsets.

Do not introduce or assume:
- automatic market orders,
- automatic limit orders,
- exchange-side execution,
- portfolio management,
- position management.

---

## 11. Deprecated paths and forbidden active assumptions

Do not use the following as active Independence Release contracts:

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

If these appear in old docs, old snapshots, comments, or generated maps, treat them as historical unless current repo reality and Martin-confirmed contracts say otherwise.

---

## 12. GPT Snapshot and Code Map handling

`docs/GPT_SNAPSHOT.md`:
- should describe the current Independence Release context,
- should be regenerated or reviewed after relevant pull requests,
- must not contain pre-Independence architecture as current truth.

`docs/code_map.md`:
- is an auto-generated structural map,
- may list both active and legacy files,
- does not itself decide which files are active architecture,
- must be interpreted using this document and current repo reality.

Archived snapshots:
- old snapshots belong under `docs/archive/ai_context/`,
- archived snapshots are historical only.

---

## 13. Maintenance rule

Update or review this document after any change to:

- active runner entrypoints,
- runner-level / SQLite `run_metadata.scan_mode`,
- report/diagnostics output `scan_mode`,
- report/diagnostics schema,
- artifact paths,
- manifest policy,
- evaluation replay inputs,
- Shadow-Live workflows,
- active-vs-legacy module boundaries,
- canonical bar ID semantics,
- no-trading boundary,
- current implementation status.

If this document becomes stale, mark it as stale immediately rather than letting AI agents rely on outdated context.
