# Architecture — Independence-Release Target Skeleton (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_ARCHITECTURE
status: canonical
primary_architecture: independence_release
legacy_runtime_status: separate_repo_reference_only
bootstrap_level: structure_only
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
Owns provider-facing data access, loading contracts, and the normalization boundary between external market data and internal processing stages. Concrete provider logic remains deferred.

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
Owns persistence boundaries, especially the future SQLite foundation and storage coordination with snapshot/history material. Schema details are intentionally deferred.

### `scanner/output/`
Owns report and export generation for the target architecture, aligned with the canonical reports/output documents. File-level output contracts remain to be implemented later.

### `scanner/runners/`
Owns orchestration entrypoints for scheduled scans and related runtime jobs in the new architecture. This ticket creates only the structural landing zone.

### `scanner/evaluation/`
Owns replay, calibration, and evaluation workflows that consume target-architecture outputs and persisted history. Evaluation logic remains out of scope for this bootstrap.

## Legacy isolation note
Existing legacy modules such as `scanner/pipeline/`, `scanner/clients/`, and `scanner/utils/` may remain present for reference and technical reuse, but they are not the primary Independence-Release target path.
