# T_EL2 Entry Location — Post-Run Validation and Calibration Note v1

**Runs covered:** 3 Shadow-Live Daily runs after T_EL2 implementation  
**Dates:** 2026-05-10 evening, 2026-05-11 morning, 2026-05-11 evening  
**Schema versions:** ir1.3 and ir1.4  
**Status:** Provisional validation note — not a threshold-change ticket  
**Purpose:** Verify T_EL2 live behavior, document covered and uncovered matrix paths, and define recalibration triggers.

---

## 1. Scope and interpretation

This note validates the first T_EL2 live behavior after implementation. It is not an implementation ticket, not a config-change request, and not a final calibration.

T_EL2 v1 remains an informational Entry-Location / Action-Hint layer:

- no change to `priority_score`
- no change to bucket membership
- no change to tradeability gates
- no order execution
- no Q1/Q2 semantic resolution

Thresholds remain provisional until a broader accumulated run base is available.

---

## 2. Runs and artifact coverage

The validation covers three Shadow-Live Daily runs:

| Run | Approx. time | Schema | Notes |
|---|---|---|---|
| 2026-05-10 evening | post-T_EL2 | ir1.3 | first T_EL2 live validation run |
| 2026-05-11 morning | post-T_EL2 | ir1.3 | first `acceptable_if_strategy_allows` live case |
| 2026-05-11 evening | post-index/persistence fixes | ir1.4 | report persistence + no-op metadata visible |

Two additional artifact families are now produced with the Shadow-Live runs:

### `shadow-live-reports.zip`

Contains the persisted report/index tree, including for example:

- `index/latest.json`
- `index/latest_run.txt`
- `index/latest_daily.json`
- `index/latest_intraday.json`
- `index/latest_confirmed_candidates.json`
- `index/latest_watchlist.json`
- `index/latest_paths.json`
- `index/recent_runs.json`
- `daily/YYYY/MM/DD/report.json`
- `runs/YYYY/MM/DD/<run_id>/report.json`

Current CI artifact content may also include `symbol_diagnostics.jsonl.gz` under `reports/runs/...`.

This does **not** imply that diagnostics are committed to the repository. Repository persistence remains allowlist-based and must continue to exclude:

- `symbol_diagnostics.jsonl.gz`
- Excel files
- Parquet
- ZIPs
- raw OHLCV
- snapshots
- large/debug artifacts

### `shadow-live-state.zip`

Contains:

- `independence_release.sqlite`

This is useful for state and cycle analysis. It does not replace report/index persistence and does not by itself provide a forward-return evaluation dataset.

---

## 3. Implementation verification

### 3.1 Override sequence — live results

T_EL2 action-hint evaluation follows ordered first-match-wins semantics.

| Rule | Condition | Expected hint | Live result |
|---|---|---|---|
| 1 | `entry_location_status == not_evaluable` | `not_evaluable` | verified, 0 violations |
| 2 | `entry_location_status == chased_entry` | `avoid_chasing` | verified, 0 violations |
| 3 | `candidate_excluded == True` | `monitor_only` | 4 records bypassed by earlier Rule 2 |
| 4 | `is_tradeable_candidate != True` | `monitor_only` | verified, 0 violations |
| 5 | `decision_bucket == early_candidates` | `monitor_only` | verified, 0 violations |

#### Rule 3 bypass cases

Four records are `candidate_excluded=True` and `entry_location_status=chased_entry`:

- `BULLISHUSDT`
- `BULLUSDT`

Each appeared across two runs.

Current behavior:

```text
entry_location_status  = chased_entry
entry_action_hint      = avoid_chasing
candidate_excluded     = true
is_tradeable_candidate = false
```

This is not a harmful false-positive. `avoid_chasing` is a stronger negative signal than `monitor_only`, and all affected symbols are non-tradeable / discarded.

However, it surfaces a semantic ordering question:

- Should `candidate_excluded` always override `chased_entry`?
- Or is it useful to surface chase-risk even for excluded symbols?

Recommendation: defer to the Q1/Q2 decision. Do not change T_EL2 v1 solely based on this observation.

---

## 4. Gate behavior

| Gate / flag | Total fires across 3 runs | Per-run breakdown |
|---|---:|---|
| `extreme_ema20_distance_outside_calibration_range` | 33 | ~11 per run |
| `missing_dist_to_ema20_4h_pct_abs` | 34 | ~11 per run |
| `range_high_proximity_warning = true` | 355 | 166 / 106 / 83 |

Assessment:

- Missing / invalid primary EMA20-distance inputs correctly produce `not_evaluable`.
- Extreme EMA20-distance values above the calibration guard correctly produce `not_evaluable`.
- `range_high_proximity_warning` is active and visible. It fires on approximately 6–9% of the full universe per run (~355 fires across ~5 400 records), confirming it is a common auxiliary signal rather than a rare exception.
- `range_high_proximity_warning` remains auxiliary only and does not alter `entry_location_status` or `entry_action_hint` in T_EL2 v1.

---

## 5. Matrix cell coverage

### 5.1 P1 Day-0 confirmed coverage

Total P1 records across the three validation runs: **24**.

| `entry_location_status` | Count | Share |
|---|---:|---:|
| `fresh_entry` | 8 | 33% |
| `acceptable_entry` | 5 | 21% |
| `extended_entry` | 7 | 29% |
| `chased_entry` | 4 | 17% |

| `entry_action_hint` | Count | Share |
|---|---:|---:|
| `monitor_only` | 19 | 79% |
| `avoid_chasing` | 4 | 17% |
| `acceptable_if_strategy_allows` | 1 | 4% |
| `buy_now_candidate` | 0 | 0% |
| `wait_for_pullback` | 0 | 0% |

### 5.2 Tested matrix cells

| Matrix cell | Status | Evidence |
|---|---|---|
| `fresh × reduced_25 → acceptable_if_strategy_allows` | live-tested | `XU3O8USDT`, 2026-05-11 morning |
| `chased × any → avoid_chasing` | live-tested | 4 P1 confirmed records |
| `observe_only × any → monitor_only` | live-tested | confirmed records with non-tradeable execution |
| `early_candidates × any → monitor_only` | live-tested | P3 records across validation runs |
| `not_evaluable → not_evaluable` | live-tested | 67 total records |

### 5.3 Not yet live-tested

| Matrix cell | Status |
|---|---|
| `fresh × full → buy_now_candidate` | not yet observed live |
| `acceptable × full → acceptable_if_strategy_allows` | not yet observed live |
| `extended × any → wait_for_pullback` in tradeable active space | not yet observed live |
| `acceptable × reduced_25 → wait_for_pullback` | not yet observed live |
| `fresh × reduced_75/50 → acceptable_if_strategy_allows` | not yet observed live |

The `buy_now_candidate` path has not produced a live output in these runs. This is currently a market/liquidity condition, not an implementation gap: no confirmed + tradeable + full + fresh candidate occurred in the validation window.

---

## 6. Key live case: XU3O8USDT

`XU3O8USDT` is the first observed non-`monitor_only` T_EL2 action case.

| Field | Value |
|---|---|
| Symbol | `XU3O8USDT` |
| Date | 2026-05-11 morning |
| `decision_bucket` | `confirmed_candidates` |
| `entry_location_status` | `fresh_entry` |
| `entry_action_hint` | `acceptable_if_strategy_allows` |
| `execution_status_raw` | `marginal` |
| `execution_size_class` | `reduced_25` |
| `is_tradeable_candidate` | `true` |
| EMA20 distance | ~1.01% |
| `range_high_proximity_warning` | `true` |

This validates the intended conservative mapping:

```text
confirmed + tradeable + fresh + reduced_25
→ acceptable_if_strategy_allows
```

It correctly does **not** become `buy_now_candidate`, because reduced-size eligibility remains an execution-quality constraint.

---

## 7. Report-level T_EL2 candidate segments

The evening run report includes `entry_location_candidate_segments` at report level.

Observed segment counts in the 2026-05-11 evening report:

| Segment | Count |
|---|---:|
| `buy_now_candidates` | 0 |
| `early_watch_candidates` | 3 |
| `good_location_but_not_tradeable` | 1,502 |
| `tradeable_but_extended` | 0 |
| `wait_pullback_candidates` | 0 |

Interpretation:

- The largest diagnostic value of T_EL2 right now is separating good entry location from operational tradeability.
- `good_location_but_not_tradeable` is large because many symbols have acceptable/fresh location but fail liquidity, execution, bucket, or universe constraints.
- This confirms why `entry_location_status` and `entry_action_hint` must remain separate.

---

## 8. Threshold status

### 8.1 Global EMA20-distance thresholds

| Status | Threshold | Calibration basis | Confidence |
|---|---:|---|---|
| `fresh_entry` | `<= 2.5%` | 3 calibration runs + 3 validation runs; very few tradeables | Low |
| `acceptable_entry` | `> 2.5%` to `<= 5.5%` | same | Low |
| `extended_entry` | `> 5.5%` to `<= 8.5%` | same | Low |
| `chased_entry` | `> 8.5%` | upper-tail evidence is clearer | Low–Medium |
| `not_evaluable` | missing / invalid / `> 50%` | anomaly/robustness gate | Medium |

Assessment:

- Fresh and acceptable thresholds remain provisional.
- `chased_entry` has stronger directional support because the upper tail is well-populated with clearly overextended symbols.
- The only observed tradeable confirmed/fresh case is `XU3O8USDT` at ~1.01% EMA20 distance.

### 8.2 `continuation_breakout` override

| Status | Threshold | Confidence |
|---|---:|---|
| `fresh_entry` | `<= 3.5%` | Low |
| `acceptable_entry` | `> 3.5%` to `<= 7.0%` | Low |
| `extended_entry` | `> 7.0%` to `<= 10.0%` | Low |
| `chased_entry` | `> 10.0%` | Low–Medium |

Assessment:

- The override is directionally plausible.
- No tradeable `continuation_breakout` candidate has appeared yet in the observed live window.
- Do not add further pattern overrides yet.

### 8.3 Auxiliary thresholds

| Parameter | Value | Status |
|---|---:|---|
| `range_high_proximity_warning` trigger | `<= 0.5%` | active, auxiliary only |
| `extreme_value_not_evaluable` | `> 50%` | active, robust |

### 8.4 Not yet calibrated

The following remain explicitly not calibrated for status determination:

- `bars_above_ema20_4h`
- `distance_to_last_structural_anchor_pct_abs`
- `bars_since_last_structural_break_4h`
- `distance_to_range_high_pct_abs` as a status dimension
- pattern overrides for `ema_reclaim`, `early_reversal_break`, `resume_reclaim`, `base_reclaim`, `range_reclaim`

`distance_to_range_high_pct_abs` is currently used only for `range_high_proximity_warning`, not as a status or hint modifier.

---

## 9. Open finding: candidate_excluded vs chased_entry ordering

Observation:

```text
candidate_excluded     = true
entry_location_status  = chased_entry
entry_action_hint      = avoid_chasing
```

This occurred for `BULLISHUSDT` and `BULLUSDT` across two runs.

Current behavior:

- Rule 2 (`chased_entry → avoid_chasing`) fires before Rule 3 (`candidate_excluded → monitor_only`).
- The affected symbols are discarded and non-tradeable.
- No actionable false positive is produced.

Interpretation:

- If Q1/Q2 resolves `candidate_excluded` as a hard categorical exclusion that must dominate all later semantics, Rule 3 should move before Rule 2.
- If `candidate_excluded` remains a soft/contextual exclusion flag and `avoid_chasing` is considered useful diagnostic information, current behavior is acceptable.

Recommendation: do not change T_EL2 v1 now. Defer the ordering decision to the Q1/Q2 semantic decision.

---

## 10. Artifact and persistence validation

### 10.1 Report persistence

The current report persistence setup is functioning:

- small report/index files are produced and persisted
- `latest_run.txt` is part of the index set
- no-op / diagnostics-only intraday runs do not clear candidate-specific latest files
- `latest_daily.json` remains the daily consumer entry point
- `latest.json` may point to the latest run of any scan mode, including no-op intraday

### 10.2 No-op intraday metadata

In the ir1.4 run, intraday no-op metadata is visible:

```json
{
  "no_op": true,
  "no_op_reason": "empty_monitoring_universe"
}
```

This confirms the report/index semantics fix is visible at report level.

### 10.3 State artifact

`shadow-live-state.zip` contains `independence_release.sqlite`.

Verified state database contents:

| Table | Rows |
|---|---:|
| `run_metadata` | 24 |
| `state_machine_context` | 1,255 |
| `ohlcv_bars` | 0 |
| `ohlcv_cache_meta` | 0 |
| `symbol_metadata` | 0 |
| `symbol_run_decisions` | 0 |

Interpretation:

- `run_metadata` (24 rows) and `state_machine_context` (1,255 rows) confirm active Shadow-Live state persistence across runs.
- `ohlcv_bars`, `ohlcv_cache_meta`, `symbol_metadata`, and `symbol_run_decisions` are empty — consistent with current Shadow-Live architecture where OHLCV and per-symbol decisions are not persisted in SQLite.
- Useful for state/cycle inspection.
- Not sufficient by itself for T30 forward-return evaluation.
- Does not replace report persistence or future evaluation exports.

---

## 11. Recalibration trigger

Recalibrate T_EL2 thresholds when **any** of the following conditions is met:

1. First live `buy_now_candidate` occurrence.
2. At least 10 accumulated valid ir1.3/ir1.4+ Daily runs with automated report persistence.
3. Repeated `direct_ok/full` tradeable candidates across multiple runs.
4. A clear market-regime shift that materially changes the distribution of EMA20-distance among confirmed/tradeable candidates.

Until then:

- keep global EMA thresholds unchanged
- keep only the `continuation_breakout` pattern override
- keep secondary fields diagnostic-only for v1 status determination
- keep `distance_to_range_high_pct_abs` auxiliary only
- do not add new pattern overrides

---

## 12. Follow-up implications

Recommended next steps remain:

1. Continue Shadow-Live accumulation through automated report persistence.
2. Revisit T_EL2 thresholds after the recalibration trigger is met.
3. Resolve Q1/Q2 before T30:
   - `is_tradeable_candidate` vs `candidate_excluded`
   - stablecoin / cash-proxy exclusion
   - whether an operational tradeability field is required
4. Keep `AI_CONTEXT_CURRENT.md` updated after major semantics changes.
5. Start T30 Forward-Return Evaluation only after report persistence, Q1/Q2 semantics, and context hygiene are clean.

---

## 13. Final assessment

T_EL2 v1 is technically validated across the first three live runs.

Validated:

- nested `entry_location` output
- status and hint enums
- ordered override behavior
- not-evaluable gates
- `range_high_proximity_warning` as auxiliary signal
- `acceptable_if_strategy_allows` for fresh + reduced-size tradeable candidate
- report-level T_EL2 candidate segments
- no-op intraday report/index behavior after the latest fixes

Not yet validated by live occurrence:

- `buy_now_candidate`
- `wait_for_pullback` in active tradeable confirmed space
- `acceptable × full`
- tradeable `continuation_breakout` override behavior

Threshold status:

- provisional
- usable for continued Shadow-Live monitoring
- not yet statistically validated
- no config change recommended now

---

*Calibration Note v1 — based on 3 Shadow-Live Daily runs (ir1.3/ir1.4), 2026-05-10 to 2026-05-11. Analysis date: 2026-05-12.*
