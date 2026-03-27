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
