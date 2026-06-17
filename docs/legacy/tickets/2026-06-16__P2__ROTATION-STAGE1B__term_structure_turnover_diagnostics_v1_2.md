# 2026-06-16 — ROTATION-STAGE1B — Term-Structure & Turnover Diagnostics (v1.2)

## Metadata
- Ticket ID: ROTATION-STAGE1B
- Title: Term-Structure, Persistence, Turnover & Survivorship Diagnostics on Stage-1 Outputs
- Status: archived - codex has already implemented this ticket.
- Priority: P2 (side project)
- Language: implementation and artifacts in English
- Depends on: ROTATION-STAGE1 (merged), Stage-1 Decision Note v1
- Documentation Impact: Variant A (standalone read-only analysis; no canonical contract change)
- Changelog v1.1→v1.2: scoped forbidden-output semantics to machine-readable
  keys/status/recommendation (resolves the `trade`/`trade count` contradiction);
  named the Stage-1 functions to reuse; made event-level reconstruction explicit;
  strengthened age-cohort tie-breaking; made the watchlist count portable.

## 1. Framing — DIAGNOSIS ONLY

This ticket investigates **why** the pre-registered Stage-1 primary test failed and
**whether** the demonstrated short-horizon scanner edge can plausibly fit the
accumulation-rotation concept. It is not a strategy build.

Hard non-goals (must appear verbatim in the output `.md`):

```text
No mechanical rotation backtest yet.
No TAO/BTC strategy validation yet.
No change of the pre-registered Stage-1 result (10d primary remains FAILED).
No decision-bearing switch from 10d to 1d/3d on the same dataset.
Stage 2 remains blocked until this ticket's central question is answered.
```

## 2. Central question

> Does any BTC-relative scanner edge survive at a horizon AND a turnover/cost profile
> compatible with the intended BTC-accumulation rotation concept (BTC default, switch
> only on clear alt superiority, hysteresis + min-hold, low turnover) — or is the edge
> structurally too short-horizon?

"Find a better comparator/horizon" is explicitly **not** the goal and must not be
pursued as result-shopping.

## 3. Inputs (read-only) and no-drift requirement

- Stage-1 outputs:
  `evaluation/rotation/stage1/2026-05-24T21-27-31Z/segment_relative_returns.parquet`,
  `btc_relative_edge_probe.json`, `probe_manifest.json`.
- Committed `enriched_replay_events.parquet` (same path as Stage-1) + the frozen
  Pre-1 history root, for event-level diagnostics.

**No-drift requirement.** Event-level relative returns must be computed by importing
and reusing the Stage-1 module's functions from `scripts.rotation.btc_relative_edge_probe`,
not reimplemented. Reuse at least (names per current `main`):

```text
load_close_series
available_history_symbols
resolve_history_symbols
add_returns
bootstrap_ci_by_week
bootstrap_raw_pooled_spread_ci
```

If any name differs on current `main`, import the actual Stage-1 implementation rather
than reimplementing it. If the relative-return functions cannot be imported at all,
fail fast (do not recompute differently). The CLI entry is guarded by
`if __name__ == "__main__": main()`, so importing must not trigger execution.

**No network:** no live exchange or web lookups of any kind.

## 4. Defaults (fixed unless explicitly overridden via CLI)

```text
horizons_days: [1, 3, 5, 10, 20]
primary_reference_horizon_days: 10        # reference only; NOT re-tested, NOT a gate
seed: 12345                               # same as Stage-1 default
min_count: 30                             # same as Stage-1 default
cost_bps_low / cost_bps_high: READ from Stage-1 probe.json `cost_context`
                                          # (cost_log_low / cost_log_high); fail fast if absent
tail_contributor_count: 5
age_cohorts: terciles of the survivorship age proxy over the in-scope event
             population; deterministic bin edges, documented in output;
             ties broken by ascending age value, then symbol, then
             as_of_daily_bar_id, then stable row order
```

Confirmed present in the canonical dataset/run (verified from the Stage-1 manifest):
`available_history_days_1d_at_event` (optional_field_availability=true) and
`cost_context.cost_log_low/high` in `probe.json`. Fallbacks below remain mandatory
for portability.

## 5. Diagnostic analyses

All analyses are descriptive magnitude diagnostics. None simulates positions, P&L,
or an equity curve. Every output row carries `analysis_role = diagnostic`.

**5.1 Term structure of the bucket ladder** (1/3/5/10/20d): tabulate
median/mean/hit/CI per tier per horizon. Descriptive only; does not re-rank or
re-select a primary horizon.

**5.2 Persistence vs mean-reversion (event-level).** `segment_relative_returns.parquet`
is aggregate-level and is **not** sufficient for event-level persistence. For
event-level diagnostics, Stage-1b must load the committed `enriched_replay_events.parquet`,
apply the **same** deterministic symbol resolution, benchmark self-exclusion, static
stablecoin denylist, and operational scope as Stage-1, and compute event-level returns
via Stage-1 `add_returns(...)`. Then, for confirmed/early events, quantify carry from
short to long horizons — share of events positive at 1d/3d that remain positive at 10d,
and sign-transition rates 1d→10d, 3d→10d, 10d→20d. Directly measures the decay recorded
in Stage 1.

**5.3 Cost break-even per holding period.** For each horizon `h`, in the same log
units as Stage-1:

```text
gross_edge_log(h)                 = median_relative_log_return at horizon h (confirmed tier, primary scope)
one_roundtrip_net_low(h)          = gross_edge_log(h) - cost_log_low
one_roundtrip_net_high(h)         = gross_edge_log(h) - cost_log_high
implied_max_rotations_per_year(h) = 365 / h
annualized_cost_drag_low(h)       = implied_max_rotations_per_year(h) * cost_log_low
annualized_cost_drag_high(h)      = implied_max_rotations_per_year(h) * cost_log_high
```

Mandatory caveat in output:

```text
This is not a position simulation and must not annualize P&L. It is only a
turnover-cost magnitude diagnostic. implied_max_rotations_per_year is an upper
bound on rotation frequency for an edge whose horizon is h, not a realized
trade count.
```

**5.4 Turnover / signal-frequency proxy:** confirmed-signal firing frequency (events
per symbol per week; universe-wide confirmed events per week). Report the distribution
and the median inter-signal gap. Combine with §5.3 `implied_max_rotations_per_year` to
state, qualitatively, whether harvesting the short-horizon edge is compatible with a
low-turnover hysteresis/min-hold design. No position state, no P&L.

**5.5 Same-date coverage diagnostic:** quantify the `watchlist` event distribution
over time (report the observed watchlist event count; for the canonical Stage-1 run the
expected count is 21), confirmed/watch same-date co-occurrence count, and document that
the same-date comparator was structurally underpowered. Output is an explanation, not a
replacement comparator.

**5.6 Survivorship — operational, not a caveat.**

Age proxy resolution (deterministic, in order):

```text
1. If `available_history_days_1d_at_event` exists, use it.
2. Else derive a deterministic proxy from the first available 1d OHLCV date per
   `history_symbol`, relative to `as_of_daily_bar_id` (days since first 1d bar).
3. If neither is possible, emit `survivorship_age_proxy_available=false` and skip
   age-stratified cuts with an explicit caveat. No live lookups.
```

Then: (a) stratify the confirmed-tier edge by age cohort (§4 terciles); (b) recompute
the confirmed-tier edge excluding the top `tail_contributor_count` contributors; (c)
recompute excluding the youngest cohort. Recompute, do not subtract from an aggregate.
Report whether the edge concentrates in recently-listed survivor names.

Delisting detection:

```text
Delisted / no-longer-present flags may only be derived from existing committed
manifests or Stage-1 artifacts. No live exchange/web lookup. If not detectable
from available artifacts, report `delisting_status_available=false`.
```

**5.7 Regime & liquidity stratification:** confirm whether the (short-horizon) edge is
conditional on `btc_regime_label` and `quote_volume_bucket`.

**5.8 OOS requirement (specification only, do NOT execute):** specify the held-out
validation design (time-window and/or symbol holdout, using existing `splits.*`
manifest infrastructure) that any future Stage-1c would require before a new
horizon/comparator could become decision-bearing. Explicitly document the
data-snooping risk of validating on this dataset.

## 6. Output

- `evaluation/rotation/stage1b/2026-05-24T21-27-31Z/term_structure_turnover_diagnostics.md`
  plus `.json` and supporting `.parquet`/`.csv`.
- The `.md` must restate the §1 non-goals verbatim.

### 6.1 Allowed conclusion vocabulary

The report must answer the central question using exactly one of:

```text
diagnostic_assessment:
  - compatible_evidence_absent
  - compatible_evidence_weak
  - compatible_evidence_inconclusive
  - compatible_evidence_promising_but_oos_required
```

### 6.2 Forbidden output semantics (hard fail if emitted)

Forbidden **machine-readable output keys, status values, or recommendation semantics**:

```text
approved
green_light
stage2_green_light
stage2_approved
deploy
rotation_recommendation
trade_recommendation
live_trade
execute_trade
```

No field named or semantically equivalent to the above. No simulated rotation P&L or
equity curve.

Benign explanatory phrases such as "trade count", "no live trading rule", or "not a
trading backtest" are allowed when used only in caveats or explanatory prose. The hard
fail applies to machine-readable keys/status values and recommendation semantics, not
to benign caveat text.

## 7. Fail-fast / guards

- Missing required Stage-1 files (`btc_relative_edge_probe.json`, `probe_manifest.json`,
  `segment_relative_returns.parquet`) → fail fast.
- `cost_context` absent from Stage-1 `probe.json` → fail fast.
- Stage-1 relative-return functions not importable → fail fast (no reimplementation).
- Any forbidden machine-readable key/status/recommendation field (§6.2) present → fail fast.
- Missing optional age field → graceful skip with `survivorship_age_proxy_available`
  fallback (§5.6), not a crash.
- No network access; deterministic under fixed seed/inputs; reuse Stage-1 bootstrap
  conventions where CIs are produced.
- No-lookahead: forward returns are labels only; never drive any selection.

## 8. Acceptance criteria

- AC1: Standalone script `scripts/rotation/stage1b_term_structure_turnover.py`,
  CLI-runnable; no scanner/replay/backtest/state/decision/execution/canonical-doc change.
- AC2: Reuses the named Stage-1 functions (§3) for event-level relative returns; no
  reimplementation.
- AC3: Produces analyses §5.1–§5.8 with explicit `analysis_role = diagnostic`.
- AC4: Output carries §1 non-goals verbatim; uses only §6.1 vocabulary; contains no
  §6.2 forbidden machine-readable semantics.
- AC5: Cost/turnover formulas implemented exactly per §5.3; turnover-cost caveat present.
- AC6: Survivorship handled operationally (age-stratified + tail-excluded + youngest-
  cohort-excluded edge, all recomputed), with the §5.6 fallback chain.
- AC7: OOS design specified but not executed.
- AC8: Deterministic; tests (§9) pass.

## 9. Tests (`tests/rotation/test_stage1b_*`)

1. Missing required Stage-1 file → fail fast.
2. `cost_context` absent → fail fast.
3. Missing optional age field → graceful skip (no crash), `survivorship_age_proxy_available=false`.
4. Age proxy fallback path (first-1d-bar derivation) computes deterministically on a fixture.
5. Cost-log formulas (§5.3) correct on a fixture with known inputs.
6. `implied_max_rotations_per_year` = 365/h exactly.
7. Forbidden machine-readable key/status/recommendation field present in machine-readable
   outputs → test fails. Benign caveat prose containing phrases such as "trade count"
   must **not** fail the test.
8. No P&L / equity-curve artifact generated.
9. `diagnostic_assessment` value is one of the §6.1 enum.
10. Deterministic output under fixed seed.
11. No live/web/network access (mock asserts no outbound calls).
12. Every output row carries `analysis_role = diagnostic`.
13. Persistence sign-transition rates (§5.2) correct on a fixture.
14. Tail-excluded and youngest-cohort-excluded edges recomputed (not subtracted) on a fixture.

## 10. Reviewer checklist (adversarial review must verify)

1. Is the FAILED 10d primary test cleanly respected and never revised?
2. Is 1d/3d strength prevented from being re-sold as a new success?
3. Are turnover and costs genuinely accounted for (not just gross edge)?
4. Is survivorship taken operationally seriously, not just mentioned?
5. Does Stage 2 remain explicitly blocked until Stage-1b is answered?
```
