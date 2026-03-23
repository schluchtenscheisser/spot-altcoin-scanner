# Runtime and Operations — Independence-Release Operating Model (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RUNTIME_AND_OPERATIONS
status: canonical
persistence_foundation: sqlite
scan_types:
  - daily_discovery_scan
  - intraday_promotion_scan
bar_clock_policy: utc_closed_bar_only
```

## Persistence foundation
SQLite is the persistence foundation for the Independence-Release operating model. The runtime layer uses SQLite for infrastructure metadata first; business tables are introduced only when later tickets define their fields canonically.

## Canonical UTC bar semantics
All bar-clock behavior is UTC-only. Local timezone conversion is forbidden. Exact close boundaries are inclusive: if `t` equals a daily or 4h close timestamp exactly, the bar that closes at `t` is treated as closed.

### Daily bar schedule
- Exchange: MEXC
- Daily close: `00:00:00.000 UTC`
- A bar for date `D` opens at `D 00:00 UTC` and closes at `(D + 1 day) 00:00 UTC`
- `daily_bar_id(t)` returns the date `D` of the most recently closed daily bar

| Input timestamp (UTC) | Most recent daily close `<= t` | Closed bar date | `daily_bar_id` |
|---|---|---|---|
| `2026-03-24T00:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-24T00:00:00.001Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-24T12:00:00.000Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |
| `2026-03-23T23:59:59.999Z` | `2026-03-23T00:00:00Z` | `2026-03-22` | `2026-03-22` |
| `2026-03-24T23:59:59.999Z` | `2026-03-24T00:00:00Z` | `2026-03-23` | `2026-03-23` |

### 4h bar schedule
- Close times: `00:00`, `04:00`, `08:00`, `12:00`, `16:00`, `20:00 UTC`
- `intraday_bar_id(t)` returns the UTC epoch-millisecond close time of the most recently closed 4h bar

| Input timestamp (UTC) | Most recent 4h close `<= t` | `intraday_bar_id` |
|---|---|---|
| `2026-03-24T04:00:00.000Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T04:00:00.001Z` | `2026-03-24T04:00:00Z` | `1774324800000` |
| `2026-03-24T03:59:59.999Z` | `2026-03-24T00:00:00Z` | `1774310400000` |
| `2026-03-24T08:30:00.000Z` | `2026-03-24T08:00:00Z` | `1774339200000` |

### Closed-bar delta semantics
`delta_closed_4h_bars(t_previous, t_current)` counts 4h close boundaries in the half-open interval `(t_previous, t_current]`.

| `t_previous` | `t_current` | Result |
|---|---|---|
| `2026-03-24T00:00:00Z` | `2026-03-24T04:00:00Z` | `1` |
| `2026-03-24T00:00:00Z` | `2026-03-24T08:00:00Z` | `2` |
| `2026-03-24T00:00:01Z` | `2026-03-24T04:00:00Z` | `1` |
| `2026-03-24T04:00:00Z` | `2026-03-24T04:00:00Z` | `0` |
| `2026-03-24T00:00:00Z` | `2026-03-25T00:00:00Z` | `6` |

### Fixed daily-to-4h mapping
`DAILY_SCAN_DELTA_BARS = 6` is canonical. Future daily/intraday coordination must use this constant instead of recomputing or introducing alternative mappings.

### Invalid timestamp handling
- `None` is invalid and raises `TypeError`
- `NaN`, `inf`, and `-inf` are invalid numeric timestamps and raise `ValueError`
- Unsupported types raise `TypeError`

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
