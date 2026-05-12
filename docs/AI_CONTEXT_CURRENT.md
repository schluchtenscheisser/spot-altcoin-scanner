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

```text
Implemented tickets: T1–T29, T21.1, T_EL1b, T_EL2

Shadow-Live is operational:
- Daily Discovery runs automatically via GitHub Actions at 01:30 UTC.
- Shadow-Live report persistence is automated for small plaintext report/index files.
- Persistence uses the daily run report as idempotency anchor.
- symbol_diagnostics.jsonl.gz, Excel, Parquet, ZIPs, raw OHLCV, snapshots,
  and other large artifacts remain artifact-only and are not committed.
- Current diagnostics/report schema version: ir1.3.

Current operational focus:
- Shadow-Live data accumulation with automated report/index persistence.
- T_EL2 Calibration Note after sufficient accumulated runs.
- Q1/Q2 decision: is_tradeable_candidate vs candidate_excluded semantics
  and stablecoin/cash-proxy handling.
- AI context hygiene before T30.
- T30 Forward-Return Evaluation planned, not started.
```

Known non-blocking state:
- `missing_intraday_cycle_context` — current status unverified after T_EL2 / ir1.3

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
- tickets T1–T29,
- T21.1,
- T_EL1b,
- T_EL2,
- review notes,
- implementation rationale.

Implementation history now includes T1–T29, T21.1, T_EL1b, T_EL2, the intraday/latest index semantics fix, and automated Shadow-Live report persistence. These tickets document implemented repo reality but do not supersede the v2.1 section files or Gesamtkonzept.

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
scanner/decision/entry_location.py
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
- `latest.json` may point to the latest run of any scan mode.
- `latest_daily.json` points to the latest Daily Discovery run.
- Candidate latest files point to latest candidate-producing outputs.
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
- Shadow-Live persists small plaintext report/index files to the repository after automated daily runs.
- Shadow-Live keeps `symbol_diagnostics.jsonl.gz`, Excel, Parquet, ZIPs, raw OHLCV, snapshots, and other large artifacts artifact-only.

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


## Current diagnostics and report schema

Current schema version: ir1.4 as of T_EL2, report persistence,
and the intraday/latest index semantics fix.

Diagnostics top-level fields include, among others:
- execution_size_class
- is_tradeable_candidate
- is_reduced_size_eligible
- recommended_position_factor
- execution_grade_effective
- candidate_excluded
- available_depth_ratio
- depth_ratio_band

Current ir1.3 diagnostics read `candidate_excluded` as a top-level field.
Do not read it from `universe.candidate_excluded` unless a future schema
explicitly changes this. Older conceptual documentation may reference
`universe.candidate_excluded`; treat that as historical only.

Report/index metadata fields include:
- no_op
- no_op_reason

`no_op` and `no_op_reason` are report-level metadata for no-op intraday runs.
They reuse existing intraday skip_reason values and are not general per-symbol
decision fields. Do not treat them as diagnostics top-level fields.

Nested diagnostics blocks:
- decision: decision_bucket, priority_score, candidate_segment, ...
- phase: market_phase, market_phase_confidence, ...
- state: state_machine_state, bars_since_confirmed_entered,
  bars_since_state_entered, ...
- pattern: entry_pattern, ...
- axes: tier-1 and tier-2 axis scores
- invalidation: invalidation state and anchors
- universe: universe classification fields
- entry_location_inputs: close_vs_ema20_4h_pct, dist_to_ema20_4h_pct_abs,
  bars_above_ema20_4h, distance_to_last_structural_anchor_pct_abs,
  bars_since_last_structural_break_4h, distance_to_range_high_pct_abs
- entry_location: entry_location_status, entry_action_hint,
  entry_location_reason_primary, entry_location_reason_codes,
  entry_location_inputs_used, range_high_proximity_warning

Critical access rule:
All nested fields must be accessed through their parent block.
Do not access decision, phase, state, pattern, axes, invalidation, universe,
entry_location_inputs, or entry_location fields at top level.
Top-level fields listed above are explicit schema exceptions.

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
no-op or diagnostics-only intraday runs may overwrite latest_confirmed_candidates.json or latest_watchlist.json
latest.json always points to a candidate-producing run
latest.json is the correct daily-candidate consumer entry point
manual ZIP artifact download is required for ordinary report/index access after report persistence
diagnostics_record_count > 0 means an intraday report produced candidate lists
```

Correct current report/index rules:
- `latest.json` = latest run of any scan mode; it may point to no-op or diagnostics-only intraday runs.
- `latest_daily.json` = canonical latest daily discovery run entry point.
- `latest_confirmed_candidates.json` and `latest_watchlist.json` = latest candidate-producing outputs; no-op and diagnostics-only intraday runs must not clear them.
- A present but empty candidate list means a candidate-producing run with zero candidates.
- An absent candidate-list key means that report did not produce that candidate list.

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
- diagnostics schema changes,
- report/index schema changes,
- report persistence policy changes,
- scan_mode / no-op semantics changes,
- artifact paths,
- manifest policy,
- evaluation replay inputs,
- Shadow-Live workflows,
- active-vs-legacy module boundaries,
- canonical bar ID semantics,
- no-trading boundary,
- current implementation status.

If this document becomes stale, mark it as stale immediately rather than letting AI agents rely on outdated context.
