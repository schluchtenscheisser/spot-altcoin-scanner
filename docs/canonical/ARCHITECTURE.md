# Architecture — Independence-Release Target Skeleton (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_ARCHITECTURE
status: canonical
primary_architecture: independence_release
legacy_runtime_status: separate_repo_reference_only
bootstrap_level: structure_plus_foundation
```

## Primary target statement
This repository is the bootstrap repository for the **Independence-Release** architecture. The duplicated legacy scanner implementation remains available only as reference material inside this repository; active target architecture work lands under the Independence-Release module structure below. The old scanner continues separately in the old repository.

## Target module structure (Gesamtkonzept §2.1)
```text
scanner/
├── universe/
├── data/
├── features/
├── axes/
├── phase/
├── state/
├── entry/
├── execution/
├── decision/
├── storage/
├── output/
├── runners/
└── evaluation/
```

## Module responsibilities (bootstrap summary from Gesamtkonzept §2.2)

### `scanner/universe/`
Owns the target-architecture universe definition and symbol population preparation that feeds the Independence-Release scans. Detailed selection logic is deferred to later tickets.

### `scanner/data/`
Owns provider-facing data access, loading contracts, and the normalization boundary between external market data and internal processing stages. The canonical Independence-Release `bar_clock.py` lives here because daily and 4h bar identifiers are infrastructure, not optional helpers.

#### `scanner/data/bar_clock.py`
This module is the canonical UTC bar clock for Independence-Release. It defines:
- `daily_bar_id(t)` as the `YYYY-MM-DD` identifier of the most recently closed daily bar,
- `intraday_bar_id(t)` as the UTC epoch-millisecond close time of the most recently closed 4h bar,
- `delta_closed_4h_bars(t_previous, t_current)` as the count of newly closed 4h bars in `(t_previous, t_current]`,
- `DAILY_SCAN_DELTA_BARS = 6` as the fixed daily-to-4h mapping.

All behavior is closed-bar-only, UTC-only, and deterministic at exact close boundaries.
Public input contract: raw numeric timestamps are interpreted as Unix epoch milliseconds, timezone-aware datetimes are accepted (normalized to UTC), and naive datetimes are rejected.

### `scanner/features/`
Owns reusable feature computation for the target architecture. This bootstrap does not define feature formulas; it only reserves the module boundary for later implementation.

### `scanner/axes/`
Owns axis-level market interpretation inputs used by the Independence-Release concept. The ticket establishes the directory only and does not define axis semantics yet.

### `scanner/phase/`
Owns market-phase determination used by the target architecture. Exact phase logic is intentionally deferred and must be specified in later tickets before implementation.

### `scanner/state/`
Owns state-machine evaluation for setup lifecycle handling in the new architecture. This bootstrap keeps the module boundary explicit without introducing runtime state logic.

### `scanner/entry/`
Owns entry qualification and trigger preparation for the target architecture. Ticket scope is limited to structure and documentation; no entry behavior is implemented here.

### `scanner/execution/`
Owns execution-adjacent abstractions for downstream decision consumption. The bootstrap does not introduce automated trading or live-order behavior.

### `scanner/decision/`
Owns decision bucketing and trade/no-trade style outputs in the Independence-Release architecture. Concrete rules are deferred to later canonical tickets.

### `scanner/storage/`
Owns persistence boundaries for Independence-Release. The initial foundation is SQLite infrastructure only: opening/creating the database, enabling WAL mode, tracking schema version via `PRAGMA user_version`, and creating the technical `run_metadata` table. Business tables such as `symbol_state`, `cycle_state`, and `cache_meta` are deferred to later tickets.

#### `scanner/storage/sqlite.py`
Provides connection/bootstrap helpers that create the database if required, enable WAL mode, and initialize the canonical schema idempotently.

#### `scanner/storage/schema.py`
Provides the schema-version contract and idempotent migration entrypoint for the infrastructure foundation. This ticket defines schema version tracking plus exactly one table, `run_metadata`.

### `scanner/output/`
Owns report and export generation for the target architecture, aligned with the canonical reports/output documents. File-level output contracts remain to be implemented later.

### `scanner/runners/`
Owns orchestration entrypoints for scheduled scans and related runtime jobs in the new architecture. This ticket creates only the structural landing zone.

### `scanner/evaluation/`
Owns replay, calibration, and evaluation workflows that consume target-architecture outputs and persisted history. Evaluation logic remains out of scope for this bootstrap.

## Legacy isolation note
Existing legacy modules such as `scanner/pipeline/`, `scanner/clients/`, and `scanner/utils/` may remain present for reference and technical reuse, but they are not the primary Independence-Release target path.

## AI Sparring Runtime (`tools/ai_sparring/`)

The repository includes a deterministic multi-round AI sparring runtime under `tools/ai_sparring/`.

- Roles are fixed to exactly two participants: `drafter` and `reviewer`.
- Supported providers are `fake`, `openai`, and `anthropic` behind one normalized provider interface.
- OpenAI integration uses the Chat Completions API for plain text generation only.
- Anthropic integration uses the Messages API for plain text generation.
- Round protocol is fixed as `draft_r -> review_r -> revision_r`.
- For each `mode`, the runtime resolves deterministic built-in prompt identifiers per role and persists them in `session.json`.
- Final summary generation is local-only from structured session state (no extra provider call).
- The runtime is operational tooling only and is explicitly decoupled from `scanner/` runtime logic.
- On `session.json.status == "completed"`, runtime executes exactly one additional ticket-drafter call and persists `ticket_draft.md` as an artifact.
- The runtime appends `## Generated Ticket Draft` to `final_summary.md`; failures are recorded as `Not generated: <reason>` without changing session completion state.
- `session.json` includes an additive top-level `ticket_draft` metadata block with deterministic generation/writeback fields.
- Repository mutation is isolated to a downstream writeback step/job; session execution itself remains artifact-focused.
- Writeback must create a branch + PR targeting `main` and never pushes directly to `main`.

### AI Sparring Issue UI (additive control plane)

The runtime also supports an issue-thread UI via `.github/workflows/ai-sparring-issue.yml`.

- Trigger source is `issue_comment` (`created`) and pull-request comments are ignored.
- Supported command grammar is exact and first-token based:
  - `/sparring start`
  - `/continue`
  - `/focus <text>`
  - `/stop`
- One issue maps to one deterministic session id: `issue-<issue_number>`.
- Persisted runtime content (`session.json`, `session.md`, `final_summary.md`) remains artifact-backed.
- Issue comment control-state is carried by one hidden pointer payload line:
  `<!-- ai-sparring-state:v1:<base64-encoded-json> -->`.
- Pointer control-state and artifact runtime-state are intentionally split; `/focus` and `/stop` update pointer-state without creating a new artifact.

### `scanner/universe/` (Ticket 3 update)
The module now owns the deterministic chain: pre-1d eligibility -> post-1d activity gate -> monitoring bypass -> pre-4h candidate filter -> non-bypass cap ranking.

## Ticket 4 OHLCV Fetch + Cache (transitional SQLite)

Ticket 4 adds `scanner/data/cache_policy.py` and `scanner/data/ohlcv_fetch.py` as deterministic primitives for `(symbol, timeframe, now)` cache decisions and closed-bar-only persistence for `1d`/`4h` OHLCV. The persistence authority for this ticket scope is SQLite (`ohlcv_bars`, `ohlcv_cache_meta`) with atomic writes and conflict-strict history immutability. This is explicitly transitional for OHLCV history; Ticket 14 defines the migration path toward the long-term history target. 

## Ticket 5 additive architecture contract (raw features layer)

`scanner/features/` now owns the deterministic raw feature layer with these modules:
- `scanner/features/raw_1d.py`
- `scanner/features/raw_4h.py`
- `scanner/features/shared.py`
- `scanner/features/models.py`
- `scanner/features/bundle.py`

Fixed build order in `build_feature_bundle(...)` is `compute_raw_1d -> compute_raw_4h -> compute_raw_shared -> FeatureBundle`.

Ticket-5 scope remains below axes/phase/state and excludes normalization utilities.

## Ticket 6 additive architecture contract (Tier-1 axes)

`scanner/axes/` now owns Ticket-6 deterministic Tier-1 computation:
- `scanner/axes/normalization.py` (pure normalization helpers)
- `scanner/axes/models.py` (`Tier1AxisBundle` typed in-memory contract)
- `scanner/axes/tier1.py` (`compute_tier1_axes(feature_bundle, cfg)`).

Scope boundary: Tier-1 consumes only `FeatureBundle` + `cfg.axes` and remains storage-free.

## Ticket 7 additive architecture contract (Tier-2-Simplified axes)

`scanner/axes/` now additionally owns Ticket-7 deterministic Tier-2-Simplified computation:
- `scanner/axes/tier2.py` (`compute_tier2_axes(feature_bundle, cfg)`)
- `scanner/axes/models.py` (`Tier2AxisBundle` typed in-memory contract).

Tier-2-Simplified scope is exactly three axes:
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Execution contract:
- input boundary is strictly `FeatureBundle` + `cfg.axes` (no `Tier1AxisBundle`, no OHLCV, no storage);
- all three axes use deterministic two-path selection (`data_4h_available=true -> 4h path only`, otherwise 1d fallback);
- no automatic 4h-to-1d fallthrough when 4h path has partial dropout;
- `pullback_quality_simplified` enforces segmentation validity (`impulse_high_price_tf > impulse_start_price_tf`) as a pre-gate before scoring.

## Ticket 8 additive architecture contract (Phase interpreter)

`scanner/phase/` now owns deterministic Layer-3 phase interpretation:
- `scanner/phase/models.py` (`PhaseInterpretationBundle` typed in-memory contract)
- `scanner/phase/interpreter.py` (`compute_phase_interpretation(tier1_bundle, tier2_bundle, cfg)`).

Scope boundary:
- consumes exactly `Tier1AxisBundle`, `Tier2AxisBundle`, and `cfg.phase`;
- computes exactly three positive phases plus `none`;
- no raw features, no OHLCV, no storage, no state/invalidation/entry/ranking logic.

## Ticket 9 additive architecture contract (state invalidation + cycle pre-state)

`scanner/state/` now owns Layer-4 pre-state computation via:
- `scanner/state/models.py` (`PersistedStateCycleContext`, `InvalidationCycleBundle`)
- `scanner/state/invalidation.py` (`compute_invalidation_and_cycle(...)` public entrypoint)
- `scanner/state/cycle.py` (cycle reset/new-cycle resolution helper).

Scope boundary:
- consumes only `PhaseInterpretationBundle`, `Tier1AxisBundle`, `Tier2AxisBundle`, persisted typed context, and `cfg`;
- computes structural/timing invalidation + setup-cycle resolution;
- performs no persistence writes and no final state assignment (reserved for Ticket 10).
