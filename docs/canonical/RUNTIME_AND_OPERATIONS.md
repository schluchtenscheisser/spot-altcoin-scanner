# Runtime and Operations — Independence-Release Operating Model (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RUNTIME_AND_OPERATIONS
status: canonical
persistence_foundation: sqlite
scan_types:
  - daily_discovery_scan
  - intraday_promotion_scan
```

## Persistence foundation
SQLite is the persistence foundation for the Independence-Release operating model. This bootstrap document defines the scan sequence only; database schema details are deferred.

## Daily Discovery Scan (Gesamtkonzept §10, steps 1–14)
1. Start the daily discovery run for the closed daily context.
2. Resolve the eligible universe for the run.
3. Load required market and history inputs for that universe.
4. Prepare target-architecture feature inputs from the closed daily context.
5. Evaluate the relevant structural/axis/phase prerequisites that are available at bootstrap level only as module boundaries.
6. Build or update candidate state for the daily discovery pass.
7. Apply the target-architecture entry qualification boundary for daily discovery candidates.
8. Produce decision-oriented candidate classifications for the daily pass.
9. Persist the daily run state to the SQLite-backed target architecture.
10. Write report artifacts into the canonical reports structure.
11. Write snapshot/history artifacts into the canonical snapshot structure.
12. Export evaluation-facing artifacts where required by the target directory model.
13. Record run metadata and operational diagnostics.
14. Close the daily discovery run as a deterministic, closed-bar-only cycle.

## Intraday Promotion Scan (Gesamtkonzept §10, steps 1–7)
1. Start the intraday promotion run for the closed intraday context.
2. Load the previously discovered candidate universe relevant for intraday review.
3. Refresh required intraday inputs using the target data boundary.
4. Re-evaluate promotion-relevant structure, phase, and state boundaries.
5. Update decision bucketing for candidates eligible for promotion or reclassification.
6. Persist and export the intraday promotion results into the target storage/output paths.
7. Close the intraday promotion run as a deterministic, closed-bar-only cycle.

## Operating constraints
- This bootstrap does not introduce live trading or automated order execution.
- Runtime logic for phase/state/entry remains deferred even though the operating model reserves those stages.
- All future implementations must preserve the documented separation between daily discovery and intraday promotion scans.
