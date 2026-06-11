# Architecture — Current-State Runtime Architecture (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_ARCHITECTURE
status: canonical
primary_architecture: current_state_daily_intraday
legacy_runtime_status: explicit_compatibility_boundaries
bootstrap_level: implemented_runtime_overview
```

## Purpose and scope

This document describes the implemented current-state Independence-Release scanner architecture at module-group level. It is a runtime and architecture map for the active Daily Discovery and Intraday Promotion scanner paths, not a field-level data model, report schema, diagnostics schema, or function-by-function API reference.

The primary evidence anchor is current repository reality, with the legacy boundary decisions from CODE-A1, CODE-A2, the legacy pipeline boundary decision note, CODE-FU-A, and CODE-FU-D applied where they explicitly classify compatibility paths.

Detailed field/report semantics remain out of scope here. Use the later/current data, report, snapshot, and schema documents for output fields, diagnostics fields, Entry-Location fields, T30 fields, schema-version details, and nullable/not-evaluated semantics.


## Current scanner module structure

The current runtime is implemented inside the `scanner/` package. The active and supporting module groups include:

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

Named paths in that package include `scanner/universe/`, `scanner/data/`, `scanner/features/`, `scanner/axes/`, `scanner/phase/`, `scanner/state/`, `scanner/entry/`, `scanner/execution/`, `scanner/decision/`, `scanner/storage/`, `scanner/output/`, `scanner/runners/`, and `scanner/evaluation/`.

## Active runtime entry points

The active scanner runtime enters through these files:

| Entry point | Current role |
|---|---|
| `scanner/main.py` | CLI/config input boundary. It accepts canonical input modes and compatibility aliases, normalizes them to a Daily or Intraday runner target, and dispatches to the active runner. |
| `scanner/runners/daily.py` | Active Daily Discovery runner. It owns the current daily closed-bar scan flow, run metadata write, per-symbol evaluation orchestration, report/diagnostics/manifest output, and persistence patching. |
| `scanner/runners/intraday.py` | Active Intraday Promotion runner. It owns the current 4h closed-bar promotion flow, provider-backed daily-context boundary, intraday refresh boundary, execution subset evaluation, report/diagnostics/manifest output, and intraday run metadata. |

The canonical scanner runtime architecture is therefore centered on `scanner/main.py` plus `scanner/runners/daily.py` and `scanner/runners/intraday.py`. Old input mode names can still reach this dispatch layer, but they do not create independent runtime architectures.

## Active Daily/Intraday runtime flow

### Daily Discovery flow

At module-group depth, the active Daily Discovery flow is:

1. `scanner/main.py` resolves the input mode to the Daily runner target.
2. `scanner/runners/daily.py` opens the SQLite persistence boundary and creates `run_metadata` with the Daily runner-level scan mode.
3. The runner resolves the run universe and OHLCV inputs through configured providers and supporting universe/data boundaries.
4. `scanner/features` builds closed-bar feature bundles for each symbol.
5. `scanner/axes` evaluates Tier-1 and Tier-2 axis bundles from feature inputs.
6. `scanner/phase` computes the phase interpretation from axis outputs.
7. `scanner/state` evaluates state-machine, invalidation, and setup-cycle context, including persisted prior state where available.
8. `scanner/entry` resolves entry-pattern context from phase, axes, state, and configuration thresholds.
9. `scanner/decision` assigns buckets and ranks decisions from phase/state/entry/execution-aware inputs.
10. `scanner/execution` selects and evaluates the execution subset and attaches active tradeability/execution metrics.
11. `scanner/output` builds run reports, daily reports, diagnostics, and run-output pathing.
12. `scanner/storage` persists run metadata and active state patches.
13. The runner writes the run manifest under the canonical snapshot run path.

### Intraday Promotion flow

At module-group depth, the active Intraday Promotion flow is:

1. `scanner/main.py` resolves the input mode to the Intraday runner target.
2. `scanner/runners/intraday.py` computes the closed daily and 4h bar context, opens SQLite, and creates `run_metadata` with the Intraday runner-level scan mode.
3. The runner resolves `intraday_context_provider` from configuration/injection; that provider is the current boundary for prior Daily context.
4. The default context provider returns no rows. A normal CLI `intraday_promotion` run without a configured provider therefore does not automatically load prior Daily candidates from storage.
5. When the provider yields no monitoring rows, the runner writes a no-op intraday report for the empty monitoring universe.
6. When provider-backed rows are available, the runner selects the monitoring universe from prior daily state, decision, phase, and freshness context.
7. The runner refreshes required intraday inputs where the latest 4h bar or stale-cache conditions require it.
8. Rows without attachable execution context are serialized with explicit skip diagnostics rather than being promoted silently.
9. `scanner/execution` selects/evaluates the intraday execution subset for attachable rows.
10. `scanner/decision` and output-facing row builders preserve bucket/ranking context for promotion outputs.
11. `scanner/output` writes intraday reports and diagnostics using report/diagnostics scan-mode values.
12. `scanner/storage` updates intraday run metadata.
13. The runner writes the intraday run manifest under the canonical snapshot run path.

## Active module groups and responsibilities

| Module group | Current responsibility |
|---|---|
| `scanner/features` | Builds deterministic, closed-bar feature bundles consumed by axes, phase, state, entry, decision, and diagnostics layers. |
| `scanner/axes` | Computes Tier-1 and Tier-2 axis interpretations from feature inputs. |
| `scanner/phase` | Converts axis outputs into phase interpretation used by state, entry, decision, and diagnostics. |
| `scanner/state` | Owns state-machine, invalidation, setup-cycle, and persisted-context evaluation for candidate lifecycle handling. |
| `scanner/entry` | Resolves entry-pattern context from validated upstream interpretation bundles and configuration thresholds. |
| `scanner/decision` | Owns bucket assignment, deterministic decision reasons, ranking, and decision-facing context assembly. |
| `scanner/execution` | Owns execution subset selection, execution grading, execution policy classification, and active tradeability metrics; active tradeability metrics live in `scanner/execution/tradeability_metrics.py`. |
| `scanner/output` | Owns report/diagnostics schemas, diagnostics serialization, report building, canonical output pathing, and output validation. |
| `scanner/storage` | Owns SQLite schema/migration boundaries, run metadata, state persistence patches, and persisted context loading. |

Supporting active module families that feed the runtime include `scanner/universe` for symbol classification/universe-admission support, `scanner/data` for UTC closed-bar clock and market-data boundaries, `scanner/clients` for provider clients, and `scanner/utils` for shared utilities. They support the active runtime but are not replacements for the runner-centered Daily/Intraday architecture.

## Data flow between module groups

The active scanner flow is intentionally layered:

```text
CLI/config input
  -> scanner/main.py
  -> scanner/runners/{daily,intraday}.py
  -> universe/data/provider inputs
  -> scanner/features
  -> scanner/axes
  -> scanner/phase
  -> scanner/state
  -> scanner/entry
  -> scanner/decision
  -> scanner/execution
  -> scanner/output
  -> scanner/storage + snapshots/runs manifests
```

Daily runs traverse the full feature/axes/phase/state/entry/decision/execution/output/storage chain for the run universe. Intraday runs consume prior Daily context only through an injected/configured `intraday_context_provider`; the default provider returns an empty context, causing the empty-monitoring-universe no-op path rather than automatic storage-backed promotion. When provider-backed rows exist, intraday runs refresh 4h-dependent inputs where required and evaluate promotion/execution context for the selected monitoring subset.

This document does not define individual field meanings inside reports, diagnostics, Entry-Location payloads, T30 outputs, or schema versions. Those semantics belong to the data/report/snapshot documentation layer.

## Active evaluation/replay boundary

The active evaluation and replay infrastructure is primarily under `scanner/evaluation/*`. It includes evaluation export support, forward-return evaluation, historical replay, history loading, replay adapters, scenario handling, replay state stores, and related evaluation history utilities.

Current scanner evaluation/replay documentation should treat `scanner/evaluation/*` as the active evaluation namespace. It should not use the legacy snapshot exporter or legacy backtest helper as evidence for current Daily/Intraday ranking or current Independence evaluation architecture.

`scanner/tools/export_evaluation_dataset.py` is not part of the active `scanner/evaluation/*` infrastructure. CODE-FU-B owns it as standalone legacy snapshot evaluation export tooling.

## Legacy and compatibility boundaries

The current repository still contains legacy, compatibility, and historical reconstruction paths. These paths must be documented with explicit boundaries so they are neither accidentally promoted to active Daily/Intraday architecture nor incorrectly described as completely unused.

| Path / component | Current classification |
|---|---|
| `scanner.pipeline.liquidity` | Previous active dependency removed by CODE-FU-A; active tradeability metrics now live under `scanner/execution/tradeability_metrics.py` |
| `scanner/execution/tradeability_metrics.py` | Active current-state target path for execution/tradeability metrics |
| `scanner.pipeline.global_ranking.compute_global_top20` | Legacy |
| `scanner.backtest.e2_model` | Legacy compatibility helper tied to legacy snapshot exporter |
| `scanner/tools/export_evaluation_dataset.py` | Standalone legacy snapshot evaluation export tooling, not active `scanner/evaluation/*` infrastructure |
| `scanner/tools/backfill_snapshots.py --mode full` | Compatibility-only / historical reconstruction path |
| `scanner.pipeline.run_pipeline` | Not active v2.1 Daily/Intraday runtime |
| `scanner.pipeline.scoring/*` | Relevant only in old/full backfill compatibility path, not active Daily/Intraday runtime |
| old mode names `standard`, `fast`, `offline`, `backtest` | Compatibility aliases only; not independent runtime modes |

## Explicit `scanner/pipeline/*` boundary

`scanner/pipeline/*` is not the current Daily/Intraday runtime architecture. It remains only where explicitly retained as legacy/compatibility or historical reconstruction support.

Consequences for architecture documentation:

- Do not describe `scanner.pipeline.run_pipeline` as the active scanner runtime.
- Do not describe `scanner.pipeline.global_ranking.compute_global_top20` as current Daily/Intraday ranking logic.
- Do not describe `scanner.pipeline.scoring/*` as active Daily/Intraday scoring logic.
- Do not describe all `scanner/pipeline/*` files as dead or nonexistent; some retained paths support compatibility tooling and historical reconstruction.
- Use `scanner/execution/tradeability_metrics.py` as the active execution/tradeability metrics path.

## Pointers to deeper semantics

Use this document for current runtime architecture and module-group responsibilities only. For deeper semantics, use the dedicated canonical documents when they are validated for current state:

- data model and schema details: `docs/canonical/DATA_MODEL.md` and `docs/SCHEMA_CHANGES.md`;
- report and diagnostics field details: `docs/canonical/REPORTS.md`;
- snapshot/replay artifact details: `docs/canonical/SNAPSHOTS.md`;
- documentation authority and precedence: `docs/canonical/AUTHORITY.md` and `docs/canonical/INDEX.md`.
