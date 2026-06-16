# Rotation Side-Project — Stage 1 Decision Note (v1, final)

- Date: 2026-06-16
- Status: Stage 1 complete. Verdict: **Yellow / Hold.**
- Scope: optional BTC↔alt accumulation-rotation side project. This note records the
  Stage-1 outcome and the decision. It does **not** authorize Stage 2.

## 0. Run provenance

| Field | Value |
|---|---|
| Probe output dir | `evaluation/rotation/stage1/2026-05-24T21-27-31Z/` |
| Probe `created_at_utc` | 2026-06-15T21:36:30Z |
| Artifact | `rotation-stage1-2026-05-24T21-27-31Z` (246 KB) |
| Artifact digest | `sha256:4d299558606c1685ee816ad012242cad9ac05878758fcb73c434a3b5ec0846…` (truncated in UI; paste full digest via the copy icon for a complete integrity anchor) |
| Dataset | committed `enriched_replay_events.parquet`, scenario `hsq_replay_2025_05_to_2026_05_v1`, `binance_spot_usdt_all`, 2025-05-01…2026-05-17, 1523 events |
| History asset | frozen Pre-1 `history-pre1-2026-05-20` / `pre1_history_2026-05-20.tar.gz` |
| Date-alignment | **Confirmed:** Stage-1 run executed on commit `f339b10`, which postdates PR #294 / `close_time_utc`-aligned history indexing fix |
| Workflow run | Run #2 — `https://github.com/schluchtenscheisser/spot-altcoin-scanner/actions/runs/27575527824` (workflow_dispatch, branch `main`, Success, 46m 13s) |
| Commit (main) | `f339b106706be75d5d9a81f605a82a952dc48939` (short `f339b10`; parent `0e3953c`; docs-only auto-commit `[skip ci]`, code state identical to parent) |

This provenance is recorded so it remains unambiguous whether the evaluated results
predate or postdate the `close_time_utc` date-alignment fix. They postdate it.

## 1. Pre-registered primary test — result

The single decision-bearing test fixed in advance (ROTATION-STAGE1 §6): same-date
`confirmed_candidates − watchlist` BTC-relative log-return spread at **10d**,
weekly-block bootstrap, dual gate.

| Field | Value |
|---|---|
| primary_estimator | `raw_pooled_fallback` (reduced robustness) |
| qualifying_date_count | 6 (below the required 20 → fallback triggered) |
| primary_spread_median | +2.85% |
| primary_spread_ci | [−3.41%, +6.63%] (crosses zero) |
| Gate A — genuine signal | **false** |
| Gate B — cost viability | true (raw confirmed 10d median +3.14% > cost-band high ≈0.80%) |
| **stage2_green_light** | **false** |
| date-demeaned residual diff (10d) | +0.39% |
| operational-scope median (10d) | −0.47%, hit-rate 47.7% |
| concentration_share_top_5 | 10.64% |
| edge_sign_stable_excluding_top5 | true |

**The pre-registered 10d primary test is NOT passed. This is the canonical Stage-1
outcome and is not revised by any secondary cut below.**

## 2. Data integrity

The probe passed all implemented data-integrity checks. Fresh-vs-precomputed
cross-check max deviation ≈1e-16 (all horizons), `missing_price_history_count` 0,
`unresolved_history_symbol_count` 0, all 1523 symbols resolved `exact`, tier mapping
from `historical_signal_bucket` (`confirmed_candidates` vs `watchlist`), benchmark
self-excluded 4 (BTC rows), stablecoin static denylist 15 (no `universe_category`
field present). The negative result is not a data artifact.

Note: passing all implemented integrity checks does **not** address survivorship,
which is a material data-basis limitation (see §3.5), not a technical fault.

## 3. Interpretation

**3.1 Positive finding — the scanner bucket carries short-horizon BTC-relative
information.** The full tier ladder is cleanly monotonic at short horizons:

- 1d: confirmed +5.2% > early +4.0% > late +2.7% > watch +1.2% > discarded −0.8%
- 3d: confirmed +5.1% > early +4.9% > late +1.8% > watch +0.4% > discarded −1.8%

A strict five-tier ordering with `discarded` reliably negative and confirmed/early
hit-rates of 86–89% is strong directional evidence that the scanner buckets carry
short-horizon BTC-relative information. This is a genuine positive result about the
scanner, independent of the rotation question. It is **not** a formally
pre-registered significance test and is not decision-bearing for the rotation.

**3.2 Decisive finding — adverse term structure.** The confirmed-tier BTC-relative
edge is front-loaded and decays:

| horizon | 1d | 3d | 5d | 10d | 20d |
|---|---|---|---|---|---|
| confirmed median | +5.2% | +5.1% | +3.8% | +3.1% | −1.9% |

The whole alt universe is −4.6% vs BTC at 20d. Relative outperformance mean-reverts
within ~2 weeks — the opposite of the persistent, low-turnover directional move that
the Mode-A accumulation-rotation concept (BTC default, switch only on clear alt
superiority, hysteresis + min-hold) was designed to harvest.

**3.3 Gate B is only weakly informative.** It compares one round-trip cost against a
10d hold. The edge actually lives at 1–3d; harvesting it implies near-daily rotation,
which multiplies turnover cost and breaks the hysteresis design. "Gate B true" does
not imply cost-robust rotation.

**3.4 Why the primary fell back.** `watchlist` has only 21 events across the whole
year, so same-date co-occurrence with `confirmed` is structurally rare (6 qualifying
dates). The same-date confirmed-vs-watch comparator was underpowered by design on
this dataset — a design lesson, not a scanner fault.

**3.5 Survivorship has a concrete face.** Top contributors are PENGU, PNUT, ETHFI,
BNT, EPIC — explosive 2024/25 names with median r_rel_10 of +24% to +61% on 3–9
events each. The median is robust and top-5 carry only 10.6%, but mean ≫ median
across the cross-section reveals a fat right tail of surviving winners; collapsed
counterparts are likely underrepresented or absent due to the current-listing
universe construction.

## 4. Decision

- **No Stage 2.** Mechanical rotation backtest is not justified.
- **No abandonment.** The scanner shows real short-horizon BTC-relative information.
- **Next: Stage-1b diagnostics** (ticket ROTATION-STAGE1B), strictly diagnostic.

## 5. Standing guardrails (carried into Stage-1b)

- The pre-registered 10d failure is the Stage-1 result. The 1d/3d strength is
  **exploratory and not decision-bearing**.
- No decision-bearing switch from 10d to 1d/3d **on this dataset** — that would be
  horizon-shopping / data-snooping. Any new horizon or comparator must be
  pre-registered and validated on held-out data.
- Stage 2 remains blocked until Stage-1b answers the central question below.

## 6. Reframed central question for Stage-1b

> Does any BTC-relative scanner edge survive at a horizon **and** a turnover/cost
> profile that is compatible with the intended BTC-accumulation rotation concept —
> or is the demonstrated scanner edge structurally too short-horizon for an
> accumulation rotation?
