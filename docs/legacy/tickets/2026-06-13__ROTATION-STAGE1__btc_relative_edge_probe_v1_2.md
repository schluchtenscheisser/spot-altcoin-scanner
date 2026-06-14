# 2026-06-13 — ROTATION-STAGE1 — BTC-Relative Scanner Edge Probe (v1.2)


## Metadata


- Ticket ID: ROTATION-STAGE1
- Title: BTC-Relative Scanner Edge Probe on Historical Replay Events
- Status: Draft for adversarial review (ChatGPT revised v1.2)
- Priority: P2 (side project; main scanner work paused)
- Language: implementation and artifacts in English
- Target PR size: 1 PR
- Primary owner: Codex implementation
- Created: 2026-06-13
- Review mode: adversarial review (Claude + ChatGPT) before merge
- Revision: v1.2 minor patch by ChatGPT, incorporating Claude review corrections on benchmark self-exclusion and same-calendar-date price alignment, plus v1.1 corrections on units, symbol/history mapping, exclusions, tier mapping, costs, and concentration handling


---


## 1. Purpose and framing


This ticket implements the **first** analysis stage of a separate, optional side
project: a candidate-rotation concept in which a portfolio is always invested in
either BTC or an altcoin, rotating based on scanner signal quality, with the goal
of growing the **BTC-denominated** stack rather than USD value.


**Stage 1 is an exploratory edge-existence probe, not a strategy backtest.**


Stage 1 answers exactly one core question:


> Did scanner events in higher signal-quality tiers historically produce positive
> forward log-returns **relative to BTC**, and is that effect a genuine signal
> effect rather than a market-breadth/alt-season artifact?


Stage 1 explicitly does **NOT**:


- validate any TAO/BTC-specific strategy,
- simulate rotation, position state, hysteresis, min-hold, or cooldown,
- derive any live trading rule,
- claim real MEXC order-book tradeability,
- recommend any trade.


This stage operates entirely as a standalone, read-only analysis script over an
already-produced historical replay dataset. It does not touch the live scanner,
the state machine, decision buckets, execution logic, or any canonical contract.

The full project sequence is: **Stage 1 (this ticket) → Stage 1b review →
Stage 2 candidate characterization → Stage 3 mechanical rotation backtest with
costs → Stage 4 OOS/robustness.** Nothing beyond Stage 1 is in scope here.


---


## 2. Authoritative references and authority rule


Authoritative reference set:


1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. The v2.1 addendum for future tickets and new chats.
4. `docs/canonical/AUTHORITY.md`, `_TICKET_PREFLIGHT_CHECKLIST.md`,
`WORKFLOW_CODEX.md`.
5. Implemented BACKTEST workstream reality:
  - `configs/replay_scenarios/hsq_replay_2025_05_to_2026_05_v1.yml`
  - `scripts/backtest/build_replay_event_dataset.py` (BACKTEST-MERGE-1)
  - the produced `enriched_replay_events.parquet`
  - `snapshots/history/ohlcv` (Pre-1 history root)


Authority rule: if the current authoritative reference set, existing repo
Authority/Canonical documents, and existing code collide, the current
authoritative reference set wins. Repo documents apply only insofar as they do
not contradict it. This ticket must not create a second competing documentation
or contract authority.


---


## 3. Input dataset (single source of truth for Stage 1)


The **only** event dataset for Stage 1 is the BACKTEST replay export:


```text
evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/<replay_id>/enriched_replay_events.parquet
```


Canonical known artifact:
`evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-27-
31Z/`


Scenario properties relevant here: `universe_mode: binance_spot_usdt_all`,
timeframes `1d`/`4h`, evaluation `2025-05-01 … 2026-05-17`,
`execution: disabled_historical_ohlcv_only`.

**Do NOT use the T30 / Shadow-Live dataset**
(`evaluation/exports/signal_event_metrics.parquet`).
The two datasets have different field contracts. In particular, T30/live fields
such as `is_operational_trade_candidate`, `candidate_excluded`,
`execution_size_class`, `decision_bucket`, `early_candidates`,
`confirmed_candidates` **must not be assumed present** in the BACKTEST dataset.
The BACKTEST dataset uses replay field names (`historical_signal_bucket`,
`event_type` with values such as `first_watch` / `first_early_ready` /
`first_confirmed_ready`).


Price history root for both legs (alt and BTC):


```text
snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/year=<YYYY>/month=
<MM>/*.parquet
```


`BTCUSDT` 1d closes must be present in this root. If they are not, the script
fails fast (see §11).

### 3.1 Deterministic history-symbol resolution

The event symbol identifier and the OHLCV history directory name are related but not
assumed identical. The script must resolve a per-row `history_symbol` deterministically:

1. If the event symbol exactly matches a directory under `snapshots/history/ohlcv/timeframe=1d/symbol=<SYMBOL>/`, use it.
2. Else, if the event symbol does **not** end with `USDT` and `<symbol>USDT` exists in the same history root, use `<symbol>USDT`.
3. Else mark that row/horizon unavailable and increment `missing_price_history_count`.

Do not guess other quote assets. Do not infer mappings from fuzzy symbol similarity.
The resolved `history_symbol` source (`exact`, `base_plus_usdt`, `unavailable`) must be counted in the manifest.


---


## 4. Mandatory schema-inspection step (before any metric)


Before computing anything, the script must inspect and **log** the actual columns
present in `enriched_replay_events.parquet`, and write that column inventory into
the output (`probe_manifest.json.dataset_columns`).


### 4.1 Required minimum fields (fail fast if any is missing)


```text
symbol                  (or the dataset's pair/symbol identifier)
as_of_daily_bar_id          (event date, YYYY-MM-DD)
event_type
historical_signal_bucket
```


If the symbol identifier column has a different name, the script must detect it
deterministically from a fixed candidate list documented in the ticket
(`symbol`, `pair`, `pair_symbol`) and log which it used; if none is found, fail.
This event symbol identifier is not automatically the OHLCV `history_symbol`;
history-symbol resolution follows §3.1.


### 4.2 Optional fields (degrade gracefully; never fail on absence)

```text
btc_regime_label
signal_day_quote_volume
median_quote_volume_30d
median_quote_volume_90d
quote_volume_bucket
available_history_days_1d_at_event
is_tradeable_candidate
forward_close_return_<N>d / has_forward_<N>d (cross-check only, see §5.4)
universe_category / any stablecoin/tokenized-stock exclusion flag
```


For each optional field that is absent: skip the segment or check that depends on
it, mark it `unavailable` in the output, and continue with the minimum viable
analysis. Absence of optional fields is never a hard failure.


### 4.3 No guessing of label strings


The script must not hardcode-assume the exact string values of `event_type` or
`historical_signal_bucket`. It must log the observed distinct values and apply the
fixed tier-mapping rule in §6, failing loudly only if the required tiers cannot be
identified by that rule.


---


## 5. BTC-relative forward log-return (computed from raw aligned closes)


### 5.1 Convention


For an event with date `t` (= `as_of_daily_bar_id`), symbol `A`, and horizon `N`
trading days (crypto trades daily; trading days = calendar days):


```text
r_rel_N(A, t) = log(P_A[t+N] / P_A[t]) - log(P_BTC[t+N] / P_BTC[t])
```


where `P_X[d]` is the 1d **close** of symbol `X` on date `d`, loaded from the
history root. Both legs are computed **fresh** from history-root closes using the
identical close-to-close convention. This guarantees no convention mismatch
between the alt leg and the BTC leg.


`t` is the close of the signal day (consistent with the dataset's
`signal_daily_close` semantics).

Both legs must use the same calendar dates `t` and `t+N`. Do **not** use each
symbol's own N-th available bar. Across any data gap, per-symbol N-th-available
bar logic would misalign the alt and BTC legs and inject phantom relative returns.
If either leg lacks a close on the required calendar date, the row/horizon is
`unavailable` under §5.3.

### 5.2 Horizons


```text
N ∈ {1, 3, 5, 10, 20}
```


Primary horizon is `10` (see §6). Others are secondary/exploratory.


### 5.3 Missing / non-finite handling


For a given `(A, t, N)`:


- If `P_A[t]`, `P_A[t+N]`, `P_BTC[t]`, or `P_BTC[t+N]` is missing or non-finite,
 `r_rel_N` is `unavailable` for that row and horizon.
- Unavailable rows are counted per horizon and excluded from metrics. They are
 **never** zero-filled or imputed.
- A horizon is only reported for a segment if it has at least `--min-count` (default `30`)
 available rows; otherwise the segment-horizon cell is written with
 `passes_min_count = false` (rows still retained).


### 5.4 Cross-check against precomputed column (validation only)


If `forward_close_return_<N>d` and `has_forward_<N>d` exist in the dataset, the
script must validate that the freshly computed **alt** leg
`log(P_A[t+N]/P_A[t])` is approximately equal to `log(1 + forward_close_return_<N>d)`
for rows where `has_forward_<N>d == true`, within a documented tolerance.
Record the mismatch count and max abs deviation in the manifest. This is a
self-consistency check only; the freshly computed values are authoritative.
Cross-check mismatches above tolerance are logged as a warning, not a hard fail,
but the manifest must surface the count prominently.


---


## 6. Pre-registered primary test (declared BEFORE the run)


To avoid segment-level multiple testing, exactly **one** primary test is
pre-registered. All other cuts are secondary/exploratory and may not, on their
own, justify proceeding to Stage 2.


### 6.1 Tier mapping rule (fixed)

Identify the `confirmed_tier` and `watch_tier` deterministically. The script must first
log all distinct observed values for both `historical_signal_bucket` and `event_type`.

Label normalization rule:

```text
normalized_label = lower(label), with every non-alphanumeric run replaced by "_", stripped of leading/trailing "_"
```

Tier source preference:

1. Prefer `historical_signal_bucket` if both mapped tiers can be identified uniquely:
   - `confirmed_tier` = the unique normalized bucket label that contains `confirmed`
   - `watch_tier` = the unique normalized bucket label that contains `watch`
2. If either side is missing or ambiguous, fall back to exact `event_type` values:
   - `confirmed_tier := first_confirmed_ready`
   - `watch_tier := first_watch`
3. If the fallback values are also not both present, fail fast with the observed label inventory.

Ambiguous means more than one label matches either side. Do not silently choose among
multiple matches. The script logs the exact raw label strings mapped to both tiers and
which source (`historical_signal_bucket` or `event_type`) was used.

### 6.2 Primary estimator — same-date bucket spread


- Scope: pooled across all symbols passing the operational proxy filter (§7),
 all BTC regimes pooled, horizon `N = 10`.
- For each signal date `d` that contains **both** ≥1 `confirmed_tier` event and
 ≥1 `watch_tier` event:
 - `m_conf(d) = median over confirmed_tier events on date d of r_rel_10`
 - `m_watch(d) = median over watch_tier events on date d of r_rel_10`
 - `spread(d) = m_conf(d) - m_watch(d)`
- Primary statistic: **median of `spread(d)` across qualifying dates `d`**.
- Inference: block bootstrap over **weekly** blocks of dates (§8). Report 95% CI.


Rationale: differencing within the same date removes both BTC's own move (already
removed by the relative return) and the daily alt-season/market-breadth factor
common to all alts that day. This isolates the signal-tier effect.


### 6.3 Fallback if same-date pairs are too sparse


If the number of qualifying same-date pairs `< --min-qualifying-dates`
(default `20`), the primary estimator degrades to the **raw pooled spread**
(median `r_rel_10` of all `confirmed_tier` events minus median `r_rel_10` of all
`watch_tier` events), explicitly flagged `primary_estimator = "raw_pooled_fallback"`
and `robustness = "reduced"`, accompanied by date and regime distribution
diagnostics for both tiers. In this case the date-demeaned variant (§6.4) becomes
the lead confound-control reference.


### 6.4 Strongest confound control — date-demeaned residuals


In addition to the primary, compute cross-sectional date-demeaned residuals:


```text
resid_N(A, t) = r_rel_N(A, t) - mean over all in-scope events on date t of r_rel_N
```


Report mean/median `resid_10` by tier and the `confirmed_tier - watch_tier`

residual difference with weekly-block bootstrap CI. This is dollar-neutral within
each day and is the cleanest test of "did this tier outperform the day's other
scanner events." It is reported as the strongest robustness reference but,
because it is one step removed from rotation economics, it is not the sole
decision metric.


### 6.5 Economic-viability gate — raw confirmed-tier level


Also report the raw pooled `confirmed_tier` BTC-relative level (median and mean
`r_rel_10`, weekly-block bootstrap CI). This carries alt-season beta and is
**context, not a clean edge**, but it is required because the rotation is a binary
TAO-vs-BTC bet: for rotation to be economically viable the confirmed-tier level
must clear the cost band (§9), not merely the spread.


### 6.6 Dual-gate decision rule (pre-registered)


A Stage-2 green light requires **both**:


- **Gate A (genuine signal):** primary spread (§6.2, or fallback §6.3) median > 0
 with 95% weekly-block-bootstrap CI lower bound > 0.
- **Gate B (cost viability):** raw `confirmed_tier` relative level (§6.5) median
 exceeds `cost_log_high`, the **upper** bound of the configured round-trip cost band converted to log-return units (§9).


If only Gate A passes: signal exists but may not survive costs → Stage 2 only to
investigate magnitude, not to trade. If only Gate B passes: level may be
alt-season beta, not signal → not a green light. If neither: broad
scanner-vs-BTC hypothesis is weak (see §12 interpretation grid).


---


## 7. Operational proxy filter (Stage 1 = proxy only, NOT order-book tradeability)

Stage 1 must not claim real MEXC order-book tradeability. The replay ran with
execution disabled; no depth/spread exists in the dataset.

The operational proxy filter is applied only with fields that actually exist.
Its purpose is to remove obvious non-rotation assets and optionally restrict the
analysis by historical liquidity proxies. It is **not** an execution verdict.

### 7.0 Benchmark self-exclusion (required)

Add config `--benchmark-symbol` with default `BTCUSDT`. The benchmark is loaded
solely as the BTC price leg for `r_rel_N` (§5) and must remain available for that
purpose.

Any event row whose resolved `history_symbol` equals `benchmark_symbol` must be
dropped from **all evaluated metric scopes**:

```text
primary scope
secondary scope
all-events system view
all segments
per-symbol exploratory splits
```

Rationale: for benchmark rows, the relative return is identically zero by
construction (`log(BTC/BTC) - log(BTC/BTC) = 0`). Including those rows would bias
pooled medians, hit rates, same-date bucket spreads, and date-demeaned residuals
toward zero.

Count dropped rows as `benchmark_self_excluded_count` in `probe_manifest.json`.
This exclusion is independent of the stablecoin/tokenized-stock denylist (§7.1)
and must run after deterministic `history_symbol` resolution (§3.1) but before
metric computation.

### 7.1 Exclusions

If a stablecoin / tokenized-stock / exclusion flag or `universe_category` exists,
exclude those symbols and report the count by exclusion source.

If no such field exists, apply a documented static stablecoin base-asset denylist and
mark `exclusion_source = "static_denylist"` in the output. The denylist applies to the
**base asset only**, never to the full USDT pair string.

Base-asset extraction rule:

```text
if pair endswith "USDT": base_asset = pair without the trailing "USDT" quote suffix
else: base_asset = pair
```

Default exact-match denylist:

```text
USDC, USDT, FDUSD, DAI, TUSD, USDE
```

Only exact configured base-asset matches are excluded. Do not infer exclusions from fuzzy
names, substrings, wrapped/pegged-looking names, or the presence of the `USDT` quote suffix.
For example, `XYZUSDT` must not be excluded merely because it ends with `USDT`.

### 7.2 Historical liquidity proxy

If `median_quote_volume_30d` exists, the script may apply `--min-quote-volume`.
Default: `--min-quote-volume 0`, meaning no hard liquidity exclusion by default.

If `quote_volume_bucket` exists, report bucket segments. If no volume proxy exists,
mark liquidity filter `unavailable` and run without it, flagged in output.

### 7.3 Existing `is_tradeable_candidate` field, if present

If `is_tradeable_candidate` exists in the BACKTEST dataset, treat it as a historical
replay proxy only and log its availability. Do not interpret it as MEXC orderbook
tradeability. It must not override the explicit Stage-1 caveat that no real depth,
spread, or slippage evidence exists in this dataset.

The primary test (§6) runs on the operational-proxy-filtered scope. An additional
unfiltered "all events" run is reported as a secondary system-level view.

---


## 8. Inference: date-/week-blocked bootstrap (mandatory)


Multi-day forward windows on daily-stepped events overlap, and events on the same
date are cross-sectionally correlated (alt-season breadth). Naive per-event
resampling drastically understates uncertainty.


Therefore all confidence intervals use a **block bootstrap over weekly blocks of
signal dates**:


- Resample whole ISO-week blocks of dates with replacement.
- All events within a resampled week move together.
- `--n-bootstrap` default `2000`, seeded (`--seed`, default `12345`) for
 determinism.
- Report 2.5% / 97.5% percentile CI for every headline statistic (primary spread,
 date-demeaned diff, raw confirmed level, per-regime where reported).


Per-event i.i.d. bootstrap is explicitly forbidden for headline statistics.


---


## 9. Cost break-even context (Stage 1 shows it; does NOT simulate it)

Display a configurable round-trip rotation cost band (`--cost-bps-low` default
`30`, `--cost-bps-high` default `80`, expressed in basis points of notional).
Note in the report that a rotation may execute via the direct ALT/BTC pair
(one trade) or via two USDT legs, and that the high end of the band is the
conservative two-leg assumption.

All return metrics in this ticket are log-returns. Therefore cost basis points must be
converted into log-return units before comparison:

```text
cost_log_low  = log(1 + cost_bps_low  / 10000)
cost_log_high = log(1 + cost_bps_high / 10000)
```

Gate B (§6.6) compares the raw `confirmed_tier` median `r_rel_10` against
`cost_log_high`, not directly against raw basis points.

For each horizon, present gross median relative edge alongside the cost band and a
qualitative `net_indication` ∈ {`below_cost`, `marginal`, `above_cost`}:

```text
below_cost = median_relative_log_return < cost_log_low
marginal   = cost_log_low <= median_relative_log_return <= cost_log_high
above_cost = median_relative_log_return > cost_log_high
```

This is magnitude context, not a P&L simulation, and must be labeled as such.

---


## 10. Required outputs

Write under:


```text
evaluation/rotation/stage1/<replay_id>/
```


Files:


```text
btc_relative_edge_probe.md       human-readable report (generated, not handwritten)
btc_relative_edge_probe.json     machine-readable summary
probe_manifest.json           run metadata, column inventory, config, validation
segment_relative_returns.parquet one row per (segment_group, segment_key, horizon)
segment_relative_returns.csv     same content as CSV
```

`probe_manifest.json` must include at least:

```text
dataset_columns
symbol_identifier_column_used
history_symbol_resolution_counts
benchmark_symbol
benchmark_self_excluded_count
optional_field_availability
config
validation
```


### 10.1 Required per-segment metrics


For each segment × horizon:


```text
event_count
unique_symbol_count
mean_relative_log_return
median_relative_log_return
hit_rate_vs_btc       (share of rows with r_rel_N > 0)
bootstrap_ci_low
bootstrap_ci_high
passes_min_count
```


Recommended additional:


```text
trimmed_mean_10pct
winsorized_mean_5pct
p25 / p75
```


### 10.2 Required concentration / robustness fields (primary scope)

```text
concentration_share_top_5_symbols       (top-5 symbols' share of summed positive r_rel_10)
edge_sign_stable_excluding_top5         (bool: does primary spread stay > 0 after removing top-5 symbols)
top_contributor_symbols                 (ranked list with per-symbol event_count and median r_rel_10)
```

`concentration_share_top_5_symbols` is computed over the operational-proxy-filtered
primary scope. If summed positive `r_rel_10 <= 0`, set:

```text
concentration_share_top_5_symbols = null
concentration_status = "not_applicable_no_positive_edge"
```

`edge_sign_stable_excluding_top5` must be computed by recomputing the primary estimator
after removing **all events** from the top-5 contributor symbols. Do not merely subtract
their contribution from an already-computed aggregate statistic.

`edge_sign_stable_excluding_top5 = false` is a strong warning that the apparent
pooled edge is a concentrated few-coin / survivorship effect, not a system edge.

### 10.3 Segments to compute


```text
ALL events (system view)
operational-proxy-filtered (primary scope)
by tier (confirmed_tier, watch_tier, and any intermediate tier present)
by btc_regime_label                 (if field present; else unavailable)
by quote_volume_bucket                  (if present; else unavailable)
tier × btc_regime_label              (if regime present)
per-symbol primary-scope splits (incl. TAO if present) (exploratory)
```


All non-primary segments are marked `analysis_role = "secondary_exploratory"` in
the output. The primary test row is marked `analysis_role = "primary"`.


### 10.4 Mandatory caveats (verbatim in the .md report)


```text
- This is an exploratory edge-existence probe, NOT a trading backtest.
- This is NOT a TAO/BTC-specific strategy validation.
- No live trading rule is derived from this stage.
- Results are conditional on the available historical universe and surviving listings
(survivorship bias present).
- Tradeability here is a historical liquidity/exclusion proxy only, NOT real MEXC order-book tradeability.
- Costs are shown as break-even context only; no rotation, turnover, or execution is
simulated.
- Forward windows overlap and same-date events are correlated; effective sample size
is far below the row count.
- Results reflect a single historical regime path (2025-05 to 2026-05); one realization,
not a distribution.
- Only the single pre-registered primary test (and the dual-gate rule) is decision-bearing;
all other cuts are exploratory.
```

---


## 11. Fail-fast rules


Hard fail (clear message, no partial metric output):


1. `enriched_replay_events.parquet` missing, empty, or unreadable.
2. Any §4.1 required minimum field missing.
3. Symbol identifier column not resolvable from the documented candidate list.
4. History root missing, or `BTCUSDT` 1d closes absent/empty.
5. `confirmed_tier` and `watch_tier` not both identifiable by the §6.1 rule.
6. `--min-count <= 0`, `--n-bootstrap <= 0`, invalid horizon list, or
  primary horizon `10` not in the horizon list.
7. `--cost-bps-low < 0`, `--cost-bps-high < --cost-bps-low`, or
  `--min-quote-volume < 0`.
8. `--benchmark-symbol` empty, non-string, or not resolvable in the 1d history root.


Graceful (continue, mark unavailable, count):


- Any optional field absent (§4.2).
- Per-row missing/non-finite prices (§5.3).
- Segments below `--min-count`.
- Liquidity proxy unavailable.
- Cross-check column absent or mismatching (warn + count).


Never silently drop rows except by explicit, logged scope/segment filtering.


---


## 12. Pre-registered interpretation grid

| Observation | Interpretation |
|---|---|
| Gate A and Gate B both pass, stable excluding top-5, holds across >=2 regimes | Strong: Stage 2 justified |
| Gate A passes, Gate B fails | Genuine signal but likely below costs; Stage 2 for magnitude study only |
| Gate B passes, Gate A fails | Likely alt-season beta, not signal; NOT a green light |
| Neither gate passes | Broad scanner-vs-BTC hypothesis weak; a TAO-specific edge would now be a separate, much stricter single hypothesis with high overfitting/survivorship burden of proof |
| Edge present only in tiny/illiquid segments | Not tradeable |
| Edge present only in one BTC regime | Regime-conditional hypothesis only, not robust rotation |
| `edge_sign_stable_excluding_top5 = false` | Concentrated few-coin/survivorship effect, not a system edge |
| `concentration_share_top_5_symbols = null` because no positive edge exists | Concentration is not applicable; do not treat as diversified edge |
| Primary CI wide / crosses zero | Inconclusive; do not trade, do not advance on this alone |

Not all horizons need be positive. For rotation, 5d/10d/20d are more relevant than
1d; 1d is the most noise- and cost-prone.


---


## 13. Tests


Add focused tests under `tests/rotation/test_btc_relative_edge_probe.py`:


1. Fails when dataset path missing/empty.
2. Fails when a required minimum field is absent.
3. Resolves symbol identifier from alternatives and logs the choice.
4. Fails when `BTCUSDT` history is absent.
5. Relative log-return computed correctly on a synthetic fixture (known closes).
6. Missing/non-finite prices → row marked unavailable, counted, not zero-filled.
7. Tier mapping: prefers `historical_signal_bucket` when valid; falls back to
  `event_type`; fails when neither yields both tiers.
8. Same-date spread computed correctly on a fixture with overlapping dates.
9. Fallback to raw pooled spread triggers below `--min-qualifying-dates` and is
  flagged.
10. Date-demeaned residuals sum to ~0 within each date on a fixture.
11. Weekly-block bootstrap is deterministic under a fixed seed.
12. Concentration and `edge_sign_stable_excluding_top5` computed correctly on a
      fixture where one symbol dominates.
13. Optional-field absence degrades gracefully (no crash, marked unavailable).
14. Cross-check mismatch counted, not fatal.
15. Outputs written to the expected directory with required schema.
16. Mandatory caveats present verbatim in the generated `.md`.
17. Cost bps are converted to log-return units and `net_indication` thresholds are correct.
18. Static stablecoin denylist applies only to `base_asset`; `XYZUSDT` is not excluded merely because the quote suffix is `USDT`.
19. History-symbol resolution handles exact history directories, `<base>USDT` fallback, and unavailable rows deterministically.
20. Concentration metrics handle the no-positive-edge denominator case with `null` and `not_applicable_no_positive_edge`.
21. Benchmark event rows whose resolved `history_symbol == benchmark_symbol` are excluded from all metric scopes and counted in the manifest.
22. Same-calendar-date alignment is enforced: if either alt or BTC lacks the close on exact `t` or exact `t+N`, the row/horizon is unavailable instead of using each symbol's next available bar.


Run:


```bash
pytest -q tests/rotation/test_btc_relative_edge_probe.py
```


---


## 14. Acceptance criteria


- AC1: Script `scripts/rotation/btc_relative_edge_probe.py` exists, is CLI-runnable
 and importable.

- AC2: Reads only the BACKTEST `enriched_replay_events.parquet` and the history
 root; performs no network calls and does not read the T30/live dataset.
- AC3: Schema-inspection step logs actual columns; required minimum fields enforced;
 optional fields degrade gracefully.
- AC4: BTC-relative forward log-returns computed fresh from aligned closes for both
 legs using deterministic `history_symbol` resolution and exact same-calendar-date
 alignment for `t` and `t+N`; missing/non-finite handled per §5.3; optional cross-check performed.
- AC5: Tier mapping follows §6.1 deterministically, including label normalization, ambiguity rejection, and logged mapped labels.
- AC6: Pre-registered primary same-date spread (10d) computed with weekly-block
 bootstrap CI; fallback path implemented and flagged.
- AC7: Date-demeaned residual variant and raw confirmed-level variant computed.
- AC8: Dual-gate decision rule evaluated and reported.
- AC9: Benchmark self-exclusion is applied before metrics and counted; operational proxy filter applied with existing fields only; static denylist applies only to base assets; tradeability framed strictly as historical proxy.
- AC10: Cost break-even context displayed per horizon in log-return units; no simulation.
- AC11: All required metrics, concentration fields including null-denominator handling, benchmark-self-exclusion manifest counts, and segments produced; primary vs secondary roles labeled.
- AC12: Mandatory caveats present verbatim in the `.md` report.
- AC13: Fail-fast and graceful rules behave per §11.
- AC14: Deterministic outputs under fixed seed and inputs.
- AC15: Tests in §13 pass; no live scanner / replay / backtest behavior changed.


---


## 15. Definition of Done


- Implementation merged as a standalone analysis script (no scanner/replay change).
- Focused pytest passes.
- A real run against
 `evaluation/backtest/exports/hsq_replay_2025_05_to_2026_05_v1/2026-05-24T21-
27-31Z/enriched_replay_events.parquet`
 plus the history root succeeds and produces all §10 outputs.
- The generated `.md` clearly states this is an exploratory edge probe and carries
 all mandatory caveats and the dual-gate result.
- Stage 1b review (Claude + ChatGPT) can read the outputs and decide on Stage 2.


---


## 16. Determinism and no-lookahead


- Identical inputs + identical CLI + identical seed → identical outputs except
 `created_at_utc`.
- Forward returns are evaluation labels only and must not influence segment
 membership, scope filters, tier mapping, or any ranking field. Only report
 sorting may use them.

- Deterministic sort for `segment_relative_returns`:
 `analysis_role ASC, segment_group ASC, horizon ASC, passes_min_count DESC,
median_relative_log_return DESC NULLS LAST, segment_key ASC`.


---


## 17. Documentation Impact (mandatory section)


**Variant A — no canonical documentation impact.**


Justification: this ticket adds a standalone, read-only analysis script under
`scripts/rotation/` and writes analysis artifacts under `evaluation/rotation/stage1/`.
It changes no canonical contract, schema, runtime path, state semantics, report
schema, or decision logic. It introduces no precedence claim. The generated `.md`
report is self-documenting. No `AUTHORITY.md`, `DATA_MODEL.md`, `REPORTS.md`,
`SNAPSHOTS.md`, or spec section is affected.


If Stage 1 results lead to Stage 2+, a separate decision note under
`docs/decision_notes/` may be created at that point; that is out of scope here.


`.gitignore` should prevent accidental commits of generated Parquet/CSV under
`evaluation/rotation/stage1/**` (compact `.md`/`.json` notes may follow existing
report-persistence policy). Do not ignore the script or tests.


---


## 18. Preflight checklist result


- Real repo/field names not assumed: enforced via mandatory schema-inspection
 step (§4) and explicit forbiddance of T30/live field assumptions (§3).
- Numeric / nullable / non-evaluable cases handled explicitly (§5.1, §5.3, §7.0, §9, §10.2, §11).
- Deterministic behavior specified (§8 seed, §16 sort).
- Stop/scope boundaries explicit (§1 non-goals, §11 fail-fast).
- No live scanner / replay / backtest semantics changed (§14 AC15, §15).
- Documentation Impact section present (§17, Variant A with justification).
- Single pre-registered primary test to control multiple testing (§6).
