# T26: Analyze Execution Depth Bottleneck and Position-Sizing Policy Counterfactual

## Metadata

- Ticket ID: T26
- Title: Analyze Execution Depth Bottleneck and Position-Sizing Policy Counterfactual
- Status: Ready for analysis implementation
- Priority: P0
- Language: Implementation and code artifacts in English
- Primary mode affected: Offline analysis of Shadow-Live Daily diagnostic archives

---

## Authoritative reference set

1. The seven v2.1 specification section files, especially Abschnitt 7 (decision buckets).
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`.
4. Current repo reality, especially `scanner/execution/grading.py`, `scanner/pipeline/liquidity.py`, and `scanner/decision/` (T12 bucket logic).
5. Existing implemented contracts from T12, T16, T21, T21.1, T22, T23, T24, and T25.
6. The eight Shadow-Live Daily ZIP artifacts from GitHub Actions runs covering 2026-04-26 through 2026-05-03.
7. The master preflight checklist for Codex-ready tickets.

---

## Required pre-reading: current execution contract (T12/T16)

The following is the authoritative execution contract as implemented. The analysis script and all findings must be interpreted against this contract, not against intuitive expectations.

### Execution status taxonomy (T16)

| `execution_status_raw` | `execution_pass` | `execution_grade` (T12) | Meaning |
|------------------------|-----------------|------------------------|---------|
| `direct_ok`            | `True`          | `100.0`                | Fully tradable at standard position |
| `tranche_ok`           | `True`          | `75.0`                 | Fully tradable, benefits from tranching |
| `marginal`             | `False`         | `40.0`                 | Partially constrained; does NOT block buckets |
| `fail`                 | `False`         | `0.0`                  | Hard blocked; routes away from top buckets |
| `unknown`              | `None`          | —                      | Orderbook stale/missing; no contract produced |

### Diagnostic field mapping

| Diagnostic field | Canonical semantic |
|------------------|--------------------|
| `execution_status_raw` | maps to canonical `execution_status` |
| `execution_reason_raw` | maps to canonical `execution_reason` |

Throughout this ticket, `execution_status_raw` refers to the field as it appears in `symbol_diagnostics.jsonl.gz`. `execution_status` (without `_raw`) refers to the canonical internal semantic. Codex must use `execution_status_raw` when reading diagnostic input fields.

### Critical T12 invariant

**Only `execution_status = "fail"` triggers the hard candidate-bucket block.** `marginal` with `execution_pass = False` does not block `confirmed_candidates` or `early_candidates` — it reduces `priority_score` via `execution_grade = 40.0` in the post-execution scoring formula. This means:

- A `confirmed_ready` symbol with `execution_status = marginal` correctly lands in `confirmed_candidates` (not `late_monitor` or `watchlist`).
- A `confirmed_ready` symbol with `execution_status = fail` is routed away from `confirmed_candidates`.

### `tranche_ok` is a live status (not a future feature)

`tranche_ok` is fully implemented in `scanner/execution/grading.py`. It is already mapped to `execution_pass = True` and `execution_grade = 75.0` in T12. It must not be treated as hypothetical or future infrastructure.

### Handling of `unknown` and `not_attempted`

Records with `execution_status_raw = "unknown"` are not part of Diagnosepunkt A or B. They must be counted separately in a per-day diagnostic summary but no depth counterfactual or rank counterfactual is computed for them. They must not be treated as `fail` or `not_attempted`.

`not_attempted` is not an `execution_status_raw` value. It is a derived summary classification meaning no execution contract was produced for that symbol in that run (`execution_attempted = False`). It must appear only in summary count tables, not in Diagnosepunkt A or B records.

### `marginal + EXECUTION_OK bucket_reason + exec_pass=False` is correct behavior

Preliminary inspection of the diagnostic archives found records with `bucket_reason_primary = EARLY_EXECUTION_OK` and `execution_pass = False` simultaneously. This is not a contract bug. Per T12/T16 spec:

- `EARLY_EXECUTION_OK` as bucket_reason means "execution_status ≠ fail" — which is true for `marginal`.
- `execution_pass = False` is the correct value for `marginal` per T16.

Both fields are simultaneously correct. The analysis script must not flag this combination as anomalous.

---

## Purpose and motivation

Shadow-Live Daily runs from 2026-04-26 through 2026-05-03 (8 days) produce diagnostic data that allows the execution depth policy to be quantitatively evaluated. The current known behavior appears consistent with the implemented T12/T16 contract; T26 does not treat it as a bug unless the replay analysis reveals a reproducible inconsistency. The policy question is whether the current standard position notional is appropriately calibrated for the scanned universe, and whether the `execution_grade = 40.0` assigned to `marginal` adequately reflects the position-sizing constraint in bucket ranking.

### Preliminary empirical findings

The following findings are based on preliminary inspection of the diagnostic archives. **They are unverified and must be reproduced by this ticket's analysis script.** If the script produces different numbers, the script output is authoritative.

Preliminary per-day execution summary:

| Date       | Total | direct_ok | marginal | fail | not_attempted | confirmed (marg) | early (marg) |
|------------|-------|-----------|----------|------|---------------|------------------|--------------|
| 2026-04-26 | 1,822 | 14        | 122      | 100  | 1,579         | 13               | 14           |
| 2026-04-27 | 1,822 | 0         | 125      | 92   | 1,595         | 12               | 14           |
| 2026-04-28 | 1,822 | 7         | 134      | 104  | 1,571         | 21               | 14           |
| 2026-04-29 | 1,826 | 3         | 95       | 83   | 1,641         | 19               | 9            |
| 2026-04-30 | 1,823 | 2         | 123      | 96   | 1,600         | 17               | 14           |
| 2026-05-01 | 1,821 | 3         | 105      | 141  | 1,549         | 16               | 11           |
| 2026-05-02 | 1,813 | 3         | 130      | 132  | 1,531         | 17               | 8            |
| 2026-05-03 | 1,811 | 21        | 265      | 153  | 1,366         | 67               | 52           |

Preliminary observations (to be verified):
- All marginal+fail cases appear to share a single failure reason: `depth_1pct_insufficient`.
- A substantial number of marginal cases appear in `confirmed_candidates` and `early_candidates`.
- A subset of fail cases may be structurally actionable (would qualify for top buckets if execution cleared). This subset — fail cases that would otherwise reach `early_candidates` or `confirmed_candidates` — is what T26 must isolate.

### Illustrative motivation cases

**RUJIUSDT:** Preliminary review shows `execution_status_raw = fail` across all observed days, with `depth_1pct_insufficient` as reason. Never reached a top bucket. 7-day price performance: +84%. T26 must determine whether a smaller position notional would have cleared RUJI's depth gate.

**TAOUSDT (01.05.):** `execution_status_raw = marginal`, correctly landed in `early_candidates` per spec. Ranked last (#15/15) in its bucket. T26 must quantify how much of this rank depression was caused by `execution_grade = 40.0` vs `100.0`.

---

## Scope

### In scope

- Analysis script that processes all 8 Shadow-Live Daily `symbol_diagnostics.jsonl.gz` archives.
- **Diagnosepunkt A:** For `fail` cases — estimate whether a reduced position notional would have cleared the depth gate, and at what notional fraction.
- **Diagnosepunkt B:** For `marginal` cases in `confirmed_candidates` or `early_candidates` — quantify the `priority_score` depression caused by `execution_grade = 40.0` vs counterfactual grades, and the resulting rank displacement.
- Spread/slippage availability check (see dedicated section).
- Output: structured Markdown reports and JSONL data files as analysis artifacts.

### Out of scope

- No changes to T16 (execution grader), T12 (decision buckets), Abschnitt 7, or any other spec or implementation file.
- No `tranche_ok` extension or order-splitting logic.
- No Market-Cap floor changes.
- No forward return / MFE / MAE computation (see Limitations section).
- **Do not read T24 report fields.** These 8 runs predate T24 implementation. The analysis script must read `symbol_diagnostics.jsonl.gz` directly. Their `report.json` files may be read only for bucket ranking cross-reference (see Diagnosepunkt B). T24 block absence is not an error.

---

## Archive discovery and validation

The analysis script must locate archives deterministically. **Input is a directory containing the 8 downloaded GitHub Actions ZIP artifacts.** The script must inspect each ZIP directly and locate `symbol_diagnostics.jsonl.gz` inside it without requiring manual extraction. For each expected date from 2026-04-26 through 2026-05-03 (8 dates), the script must:

1. Search the configured input directory for a `symbol_diagnostics.jsonl.gz` file matching that date's canonical daily run path.
2. If any expected date is missing, the script must fail with a clear error listing which dates are absent before processing any data.
3. The script must log which archive path it used for each date.

This ensures the final analysis report is unambiguously tied to a known, complete input set.

---

## Diagnosepunkt A — Fail-class depth counterfactual

**Goal:** For each `fail` case in each daily run, estimate whether a reduced position notional would have cleared the depth gate, and at what fraction. Isolate the structurally actionable subset: fail cases whose state and phase would have qualified them for `early_candidates` or `confirmed_candidates` if their execution had been `marginal` instead of `fail`.

### Context: the grader's depth gate

`scanner/pipeline/liquidity.py` computes `tradeability_class` using `cfg.execution.min_depth_1pct_usd` as a hard floor. The depth ratio is:

```
available_depth_ratio = actual_available_depth_within_1pct / min_depth_1pct_usd
```

If `available_depth_ratio < 1.0`, the symbol fails the depth gate. The analysis assumes the depth gate scales linearly with notional (i.e., halving the notional halves the required depth). This assumption must be stated explicitly in the output report. If `compute_tradeability_metrics` in `scanner/pipeline/liquidity.py` does not scale linearly, the script must document this and adjust the counterfactual accordingly.

### `decision_bucket_without_execution_block` — exact replay specification

This field answers: "Which bucket would this symbol have been assigned to if its `execution_status` had been `marginal` instead of `fail`?"

**Computation rule:**

1. Take all fields from the diagnostic record as-is.
2. Override `execution_status_raw` from `"fail"` to `"marginal"`.
3. Override `execution_grade` from `0.0` to `40.0`.
4. Recompute `priority_score` using the T12 post-execution formula:
   ```
   priority_score = 0.30 * market_phase_confidence
                  + 0.35 * state_confidence
                  + 0.20 * entry_pattern_score
                  + 0.15 * 40.0
   ```
5. Replay the T12 bucket assignment using the overridden `execution_status` and recomputed `priority_score`. All other diagnostic fields remain unchanged.
6. The resulting bucket is `decision_bucket_without_execution_block`.

**Robustness rule for missing or non-finite score components:** If any of `market_phase_confidence`, `state_confidence`, or `entry_pattern_score` is `null`, missing, `NaN`, or non-finite in the diagnostic record, the script must set `replay_derivable = False` for that record, leave `decision_bucket_without_execution_block = null`, and include the record in a dedicated non-derivable summary. Non-finite values must not be silently coerced to `0.0`. Add `replay_derivable` (bool) to the required output fields.

**Implementation preference:** Reuse the existing T12 bucket assignment function if it can be imported without side effects. If not importable, implement an explicit minimal replay that mirrors the documented T12 logic and mark it as `# analysis-only replay`. Do not infer the counterfactual bucket from the current bucket label.

**Critical precision:** Many `fail` cases land in `watchlist` because their `state_machine_state` is `watch`, not because of the execution block. For these symbols, `decision_bucket_without_execution_block` will still be `watchlist` even after the replay — the execution block was not the reason for their bucket assignment. The script must not conflate "execution-unblocked" with "promoted to top bucket." Only record as structurally actionable those symbols where the replay produces `early_candidates` or `confirmed_candidates`.

### `recommended_position_factor` — exact mapping rule

```
if depth_ratio_derivable = False:
    recommended_position_factor = null
    tradable_at_75pct = null
    tradable_at_50pct = null
    tradable_at_25pct = null

elif available_depth_ratio >= 1.00:
    recommended_position_factor = 1.00  # should not appear in fail cases; guard only

elif available_depth_ratio >= 0.75:
    recommended_position_factor = 0.75
    tradable_at_75pct = True
    tradable_at_50pct = True
    tradable_at_25pct = True

elif available_depth_ratio >= 0.50:
    recommended_position_factor = 0.50
    tradable_at_75pct = False
    tradable_at_50pct = True
    tradable_at_25pct = True

elif available_depth_ratio >= 0.25:
    recommended_position_factor = 0.25
    tradable_at_75pct = False
    tradable_at_50pct = False
    tradable_at_25pct = True

else:  # available_depth_ratio < 0.25
    recommended_position_factor = 0.00
    tradable_at_75pct = False
    tradable_at_50pct = False
    tradable_at_25pct = False
```

Note: `recommended_position_factor` represents the minimum notional fraction that would clear the depth gate, quantized to the nearest defined level. It does not guarantee that other execution metrics (spread, slippage) would also pass at that notional. This assumption must be stated in the output report.

### Required output fields per fail case

```
symbol
date
replay_derivable                          # bool: False if any score component was null/non-finite; bucket replay not performed
decision_bucket_actual
decision_bucket_without_execution_block
structurally_actionable                   # bool: decision_bucket_without_execution_block in {early_candidates, confirmed_candidates}
state_machine_state
market_phase
market_phase_confidence
entry_pattern
entry_pattern_score
priority_score_actual
priority_score_counterfactual_marginal    # recomputed with execution_grade = 40.0
execution_status_raw                      # = "fail"
execution_reason_raw
available_depth_usdt                      # float or null
depth_threshold_1pct_usdt                # float: cfg.execution.min_depth_1pct_usd threshold used in this run
available_depth_ratio                     # float or null
clearing_notional_fraction                # float or null: available_depth_ratio (continuous)
recommended_position_factor               # 0.75 | 0.50 | 0.25 | 0.00 | null
tradable_at_75pct                         # bool or null
tradable_at_50pct                         # bool or null
tradable_at_25pct                         # bool or null
depth_ratio_derivable                     # bool
```

### Required summary statistics

- Total fail cases: overall, per day, per actual bucket, per state.
- Count where `depth_ratio_derivable = True` vs `False`.
- If depth data available: distribution of `recommended_position_factor` across all fail cases.
- Count of `structurally_actionable = True` cases (the RUJI-class subset).
- Among structurally actionable cases: distribution by `decision_bucket_without_execution_block`, by `recommended_position_factor`, by `entry_pattern`.
- Count of fail cases where `recommended_position_factor = 0.00` (hard-blocked even at 25%).

---

## Diagnosepunkt B — Marginal-class priority impact

**Goal:** For each `marginal` case that reached `confirmed_candidates` or `early_candidates`, quantify the `priority_score` depression caused by `execution_grade = 40.0` vs a set of counterfactual execution grades, and determine the resulting rank displacement within its bucket.

### Rank computation

Rank is determined by sorting all symbols in the same bucket on the same run day by `priority_score` descending, with symbol ascending as the deterministic tie-breaker (unless T12 defines a different canonical tie-breaker, in which case reuse it).

**Rank computation source:** Compute rankings from `symbol_diagnostics.jsonl.gz` directly using the above sort rule, not from `report.json` bucket lists. Daily `report.json` bucket lists may be truncated and must not be used as the ranking source. If `report.json` is read for any other purpose in this ticket, truncation must be explicitly handled.

### Counterfactual execution grades

Diagnosepunkt B computes rank displacement for the following counterfactual `execution_grade` values:

| Counterfactual | Interpretation |
|----------------|----------------|
| `40.0` | Baseline: current `marginal` grade (actual) |
| `50.0` | Hypothetical reduced-size grade, conservative |
| `60.0` | Hypothetical reduced-size grade, moderate |
| `75.0` | Hypothetical reduced-size grade, equivalent to `tranche_ok` |
| `100.0` | Counterfactual `direct_ok` (maximum possible) |

These grades are **analysis-only** and must not be interpreted as proposed spec values. Their purpose is to inform the follow-on Spec-Ticket's calibration of a future `recommended_position_factor`-based grade mapping.

### Required output fields per marginal confirmed/early case

```
symbol
date
decision_bucket
state_machine_state
market_phase
market_phase_confidence
state_confidence
entry_pattern
entry_pattern_score
priority_score_actual                        # with execution_grade = 40.0
priority_score_cf_50                         # counterfactual with execution_grade = 50.0
priority_score_cf_60                         # counterfactual with execution_grade = 60.0
priority_score_cf_75                         # counterfactual with execution_grade = 75.0
priority_score_cf_100                        # counterfactual with execution_grade = 100.0
rank_actual                                  # rank within bucket, actual scores
rank_cf_50
rank_cf_60
rank_cf_75
rank_cf_100
rank_displacement_cf_100                     # rank_cf_100 - rank_actual (negative = better rank)
```

### Required summary statistics

- Distribution of `priority_score_delta` (cf_100 − actual) across all marginal confirmed/early cases.
- Distribution of `rank_displacement_cf_100`: how many symbols would rank ≥5 positions better if they were `direct_ok`.
- For each counterfactual grade: mean and median rank displacement.
- Count of marginal confirmed/early cases that ranked last or in the bottom quartile of their bucket.

---

## Spread and slippage availability check

Our prior discussions agreed that slippage thresholds for reduced-size trades must not be set before the data is inspected. The analysis script must:

1. Check whether `symbol_diagnostics.jsonl.gz` contains spread and/or slippage fields (e.g., `spread_pct`, `slippage_bps`, or equivalent).
2. If present: for `fail` and `marginal` cases, summarize how many would also violate current spread/slippage thresholds, separately from the depth constraint.
3. If absent: document this gap explicitly in the analysis report, and flag it as a required data addition for the follow-on Spec-Ticket.

This check is required. It determines whether depth is truly the sole bottleneck or whether spread/slippage would introduce a secondary gate at reduced notional.

---

## Limitations (required section in analysis_report.md)

The following limitations must be explicitly stated in the output report. They are not deficiencies of T26; they define what T26 does and does not prove.

1. **Profitability is not assessed.** T26 determines whether the execution depth policy is a bottleneck and how large the affected candidate set is. It does not determine whether reduced-size candidates would have been profitable. MFE, MAE, and forward return analysis require a follow-on evaluation ticket.

2. **Depth-to-notional scaling assumption.** The counterfactual assumes the depth gate scales linearly with position notional. If `compute_tradeability_metrics` does not scale linearly, the `clearing_notional_fraction` estimates are approximate and must be treated as lower bounds only.

3. **Single-metric counterfactual.** The depth counterfactual holds all other execution metrics (spread, slippage) constant. A symbol that clears the depth gate at reduced notional may still fail spread or slippage checks. The spread/slippage availability check section determines whether this is measurable from available diagnostic data.

4. **Pre-T24 data.** These 8 archives predate T24 implementation. T24 execution-aware report fields are absent. Analysis findings apply to the pre-T24 diagnostic schema only.

5. **Preliminary summary statistics.** The per-day numbers in the Background section of this ticket are preliminary and unverified. The script's output is authoritative.

---

## Data source clarification

These 8 Shadow-Live runs were executed before T24 was implemented. Their `report.json` files do not contain T24 execution-aware fields.

- **Primary data source for all execution fields:** `symbol_diagnostics.jsonl.gz`.
- **`report.json` may be read** only to cross-reference canonical bucket rankings if needed. Treat all `report.json` bucket lists as potentially truncated and do not use them as ranking source (see Diagnosepunkt B).
- **Do not attempt to read T24 fields** from `report.json`. Their absence is not a schema failure.

T25 reads T24 report fields for post-T24 runs. T26 reads diagnostics for pre-T24 runs. These are separate concerns and must not be conflated.

---

## Output artifacts

Under `reports/aux/execution_depth_analysis/2026-04-26_to_2026-05-03/` (per T19/T25 canonical output conventions). The date-range suffix ensures multiple analysis runs do not overwrite each other.

| File | Content |
|------|---------|
| `fail_cases_full.jsonl` | One record per fail case across all 8 runs, all Diagnosepunkt A fields |
| `marginal_candidate_cases_full.jsonl` | One record per marginal confirmed/early case, all Diagnosepunkt B fields |
| `summary_fail_depth_counterfactual.md` | Aggregated Diagnosepunkt A statistics |
| `summary_marginal_priority_impact.md` | Aggregated Diagnosepunkt B statistics including all counterfactual grades |
| `analysis_report.md` | Full narrative combining both diagnosepunkte, spread/slippage check, and Limitations section |

---

## Acceptance criteria

- [ ] All 8 daily diagnostic archives are discovered and processed; script fails clearly if any expected date is missing.
- [ ] Preliminary empirical numbers are reproduced or corrected by the script output.
- [ ] `fail_cases_full.jsonl` contains one record per fail symbol per run day; count is verified against daily diagnostic totals.
- [ ] `marginal_candidate_cases_full.jsonl` contains one record per marginal confirmed/early symbol per run day.
- [ ] `decision_bucket_without_execution_block` is computed via T12 bucket replay (not inferred from current bucket label).
- [ ] `recommended_position_factor` follows the exact mapping rule defined in this ticket.
- [ ] `replay_derivable = False` records are included in a non-derivable summary; score components are never coerced from null/non-finite to 0.0.
- [ ] `tradable_at_*` fields are set to `null` when `depth_ratio_derivable = False`.
- [ ] All five counterfactual execution grades (40, 50, 60, 75, 100) are computed for Diagnosepunkt B.
- [ ] Rank computation uses `symbol_diagnostics.jsonl.gz` as source with deterministic sort; `report.json` bucket lists are not used as ranking source.
- [ ] Spread/slippage availability check is completed and result documented.
- [ ] `analysis_report.md` contains the Limitations section as specified.
- [ ] Output files produced under `reports/aux/execution_depth_analysis/2026-04-26_to_2026-05-03/`; not committed back to repository.
- [ ] The script does not attempt to read T24 report fields; their absence is not treated as an error.

---

## Invariants

- T26 reads `symbol_diagnostics.jsonl.gz` as primary data source.
- T26 reads `report.json` only for supplementary cross-reference, not for T24 fields.
- T26 does not write under `reports/runs/**` or `reports/analysis/`.
- T26 output path is `reports/aux/execution_depth_analysis/2026-04-26_to_2026-05-03/`.
- T26 does not call MEXC or any live external API.
- T26 does not modify any scanner runtime module.
- `marginal + EXECUTION_OK bucket_reason + exec_pass=False` is correct per T12/T16 spec and must not be flagged as anomalous.

---

## Follow-on ticket (not part of this ticket)

Upon completion of T26 analysis, a separate Spec-Ticket will be drafted:

**Tiered Execution / Position-Size-Aware Execution Policy**

Indicative scope (subject to T26 findings):

- Introduce `recommended_position_factor` (float: 1.0, 0.75, 0.50, 0.25, 0.0) into the execution contract and diagnostics.
- Expose `available_depth_usdt` and `available_depth_ratio` in `symbol_diagnostics.jsonl.gz`.
- Define explicit depth-ratio thresholds for fail→marginal promotion at reduced notional.
- Redefine `fail` explicitly as "not tradable even at minimum defined position floor."
- Update `execution_grade` mapping for `marginal` based on T26 sensitivity analysis.
- Update Abschnitt 7 documentation to reflect explicit position-sizing semantics.
- Slippage threshold for reduced-notional trades: determined by T26 findings.
- `tranche_ok` extension / order-splitting: explicitly out of scope.
