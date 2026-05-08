# [P0] Prevent Duplicate Daily-Bar State Aging on Re-Runs

## Metadata

- **Ticket ID:** T28-pre-2 (follow-up to T28-pre / PR #230)
- **Priority:** P0 — current Shadow-Live state is contaminated; all multi-day analysis (T28, T_EL1 Step B) is blocked until this is fixed and state is reset
- **Depends on:** T28-pre / PR #230 (state persistence — must be merged and deployed)
- **Authoritative references:**
  - Current `main` after PR #230
  - `.github/workflows/independence-shadow-live.yml`
  - `scripts/run_independence_shadow_live.py`
  - `scanner/data/bar_clock.py` (`daily_bar_id` definition — T1)
  - v2.1 Abschnitt 4 (state machine, `bars_since_*` semantics)
  - v2.1 Abschnitt 6 (daily/intraday update policy)
  - `independence_release_gesamtkonzept_final.md`

> If existing implementation and this ticket conflict, the v2.1 specification and the established T1/T22/PR #230 contracts take precedence.

---

## Context

### What PR #230 fixed

State persistence between GitHub Actions runs is now working. The `shadow-live-state` artifact is produced correctly, the restore logic functions, and `bars_since_confirmed_entered` now carries over between runs. This was confirmed empirically: overlapping confirmed symbols showed `bars_since_confirmed_entered = 6` on the second run of the same day.

### The new problem revealed

Two Shadow-Live runs executed on the same calendar day, both referencing `daily_bar_id = 2026-05-06`. Both runs advanced state aging as if a new daily bar had closed between them:

```
Run 1 (daily_bar_id = 2026-05-06): bars_since_confirmed_entered = 0
Run 2 (daily_bar_id = 2026-05-06): bars_since_confirmed_entered = 6
```

No new daily bar had closed. The aging increment is spurious.

The following day's run compounded the error:

```
Run 3 (daily_bar_id = 2026-05-07): bars_since_confirmed_entered = 12
```

Correct value after one genuine new bar: `6`. Actual value: `12`. The contamination is now baked into the persisted state.

### Why this happens

The state machine increments `bars_since_*` counters and recomputes `freshness_distance_*` metrics on every run, unconditionally. It has no mechanism to detect that the current run's `daily_bar_id` is identical to the `daily_bar_id` used in the previous state-aging step. Before PR #230 this was invisible because state was never persisted; now that persistence works, this gap surfaces.

### Spec gap

v2.1 Abschnitt 4 and Abschnitt 6 do not contain an explicit idempotency rule for re-runs on the same `daily_bar_id`. This ticket closes that gap at the implementation level. A corresponding spec clarification should be noted for the next spec revision.

### Current state of Shadow-Live data

The persisted SQLite state is contaminated. `bars_since_confirmed_entered` values are approximately doubled relative to their correct values. Symbols that should still be `confirmed` have been incorrectly promoted to `late` or `chased`, or invalidated. All Shadow-Live runs until the state is reset and this fix is deployed produce unreliable signal data.

---

## Goal

State aging — specifically the increment of `bars_since_*` counters and recomputation of `freshness_distance_*` metrics — must only occur when the current run's `daily_bar_id` differs from the `daily_bar_id` recorded in the persisted state at the previous aging step.

A re-run on the same `daily_bar_id` must be state-aging-idempotent: it reads the existing state, produces diagnostics and reports, but does not modify any aging counter or freshness metric.

Additionally, a manual `reset_state` mechanism must be available via `workflow_dispatch` to allow flushing contaminated state and starting clean.

---

## Behavioral specification

### Idempotency guard

The state machine must persist `last_aging_daily_bar_id` alongside all state records. Before applying state aging for any symbol in a given run:

1. Read `last_aging_daily_bar_id` from the persisted state for that symbol (or the run-level record if stored globally).
2. Compare against the current run's `daily_bar_id` (from `bar_clock.daily_bar_id(run_utc_timestamp)`).
3. If they are equal: **skip all aging increments** for that symbol. Aging-related persisted values carry through unchanged. The run may still recompute current market-data-driven outputs such as axes, phase, state confidence, entry pattern, invalidation, execution, decision bucket, and priority score.
4. If they differ (or no prior value exists): apply aging normally, then write the current `daily_bar_id` as the new `last_aging_daily_bar_id`.

**New symbols:** For symbols with no prior persisted state, `last_aging_daily_bar_id` must be written with the current `daily_bar_id` at the point of initial state record creation — not deferred to the next run. This ensures that a same-day re-run does not treat a newly discovered symbol as "no prior aging marker" and incorrectly apply aging a second time within the same daily bar.

**Affected fields — must not increment on same-bar re-run:**

| Field | Location |
|---|---|
| `bars_since_state_entered` | state sub-dict |
| `bars_since_early_entered` | state sub-dict |
| `bars_since_confirmed_entered` | state sub-dict |
| `freshness_distance_state_early` | state sub-dict |
| `freshness_distance_state_confirmed` | state sub-dict |

**Fields that must remain stable on same-bar re-run:**

| Field | Invariant |
|---|---|
| `close_at_early_entry_bar` | Not re-set; value from initial early entry preserved |
| `close_at_confirmed_entry_bar` | Not re-set; value from initial confirmed entry preserved |

**Fields that may update on same-bar re-run** (they reflect current market data, not accumulated age):

- All T1–T7 axis scores (`market_phase_confidence`, `state_confidence`, `entry_pattern_score`, etc.)
- `execution_status_raw`, `execution_pass`, all T27 depth/spread fields
- `decision_bucket`, `priority_score`
- `structural_invalidation`, `timing_invalidation`

A same-bar re-run must produce a valid, complete report. It is not a no-op — only aging increments are suppressed.

### `last_aging_daily_bar_id` storage

`last_aging_daily_bar_id` is stored in the SQLite state table alongside the existing state fields. It is a `TEXT` column (`YYYY-MM-DD`), nullable. Schema migration must be idempotent (existing T1 migration framework applies).

Alternatively, if the existing schema stores a run-level `daily_bar_id` that is already queryable per symbol, Codex may use that field if it provides equivalent semantics — but must explicitly document the choice and verify correctness against the idempotency guard logic above.

### `reset_state` workflow dispatch input

Add a boolean `workflow_dispatch` input `reset_state` (default: `false`) to `independence-shadow-live.yml`.

When `reset_state = true`:

1. The restore step is skipped entirely. No prior `shadow-live-state` artifact is downloaded.
2. The run starts with an empty SQLite database.
3. `state_restore_status = cold_start_reset` is written to the run manifest.
4. After a successful run, a new clean `shadow-live-state` artifact is produced (replacing the contaminated one).

When `reset_state = false` (default): existing restore behavior from PR #230 applies unchanged.

`reset_state = true` must not affect any other workflow behavior. Reports, diagnostics, and all other artifacts are produced normally.

---

## Scope

### In scope

1. Add `last_aging_daily_bar_id` column to the SQLite state schema (idempotent migration).
2. Implement the idempotency guard in the state machine update logic: compare current `daily_bar_id` against `last_aging_daily_bar_id` before applying any aging increment.
3. Write `last_aging_daily_bar_id` after successful aging for each symbol.
4. Add `reset_state` boolean input to `.github/workflows/independence-shadow-live.yml`.
5. Implement `reset_state` logic in `scripts/run_independence_shadow_live.py` or the workflow steps: skip restore, set `state_restore_status = cold_start_reset`.
6. `cold_start_reset` added as a valid value for `state_restore_status` in the run manifest.

### Out of scope

- Changing any scoring, ranking, or decision bucket logic.
- Modifying the `shadow-live-state` artifact format beyond what is required for the idempotency guard.
- Intraday state aging idempotency (daily only in this ticket).
- Backfilling or correcting the currently contaminated state (the `reset_state` mechanism handles this operationally).
- Formal v2.1 spec update (tracked separately; this ticket closes the implementation gap).

---

## Deployment and reset procedure

After this ticket is merged, the following sequence must be executed to restore a clean Shadow-Live baseline:

**Step 1 — Reset run:**
Trigger `independence-shadow-live.yml` via `workflow_dispatch` with `reset_state = true`.
Expected outcome: `state_restore_status = cold_start_reset`, clean state artifact produced.

**Step 2 — Same-bar idempotency verification (optional but recommended):**
Trigger a second manual run on the same day (same `daily_bar_id`).
Expected outcome: `state_restore_status = restored`, all `bars_since_*` values identical to Step 1 output.

**Step 3 — Next genuine daily bar:**
Wait for the next scheduled run (or trigger manually after the daily bar closes).
Expected outcome: overlapping confirmed symbols show `bars_since_confirmed_entered` incremented by exactly 6 (one daily bar = 6 × 4h bars) relative to Step 1 values.

Only after Step 3 is verified are Shadow-Live runs considered reliable for T28 and T_EL1 Step B.

---

## Acceptance criteria

1. A symbol with `bars_since_confirmed_entered = N` in the persisted state produces `bars_since_confirmed_entered = N` (unchanged) in a re-run on the same `daily_bar_id`.
2. `close_at_confirmed_entry_bar` and `close_at_early_entry_bar` are not reset on a same-bar re-run.
3. A re-run on the same `daily_bar_id` produces a complete, valid report (not a no-op — full scan runs, diagnostics written, artifacts uploaded).
4. A run on a new `daily_bar_id` increments `bars_since_confirmed_entered` by the correct bar-delta for overlapping confirmed symbols.
5. `reset_state = true` via `workflow_dispatch` causes the restore step to be skipped, the run to start with an empty DB, and `state_restore_status = cold_start_reset` to appear in the run manifest.
6. `reset_state = false` (default) leaves PR #230 restore behavior completely unchanged.
7. Schema migration adding `last_aging_daily_bar_id` is idempotent: running it on an existing database does not corrupt existing state records.
8. After the three-step reset procedure above, overlapping confirmed symbols on the third run show `bars_since_confirmed_entered` incremented by exactly 6 relative to the reset run's value.
