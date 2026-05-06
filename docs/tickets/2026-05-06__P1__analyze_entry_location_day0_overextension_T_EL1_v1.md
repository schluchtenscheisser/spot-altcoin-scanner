# T_EL1: Analyze Entry-Location / Day-0 Overextension from Shadow-Live Diagnostics

## Metadata

- Ticket ID: T_EL1
- Title: Analyze Entry-Location / Day-0 Overextension from Shadow-Live Diagnostics
- Status: Ready for implementation (Step A); Step B pending diagnostics extension
- Priority: P1
- Language: Implementation and code artifacts in English
- Primary mode affected: Offline analysis of Shadow-Live Daily diagnostic archives
- Authoritative pre-reading: Feature Request `feature_request_entry_location_action_hint.md`

---

## Authoritative reference set

1. Feature Request: `feature_request_entry_location_action_hint.md` (concept document for the Entry-Location / Action-Hint Layer).
2. The seven v2.1 specification section files, especially Abschnitt 4 (state machine, `distance_from_ideal_entry_after_confirmed`), Abschnitt 7 (decision buckets, `priority_score`).
3. `independence_release_gesamtkonzept_final.md`.
4. Implemented contracts from T5 (raw features including `close_vs_ema20_4h_pct`), T12 (decision buckets), T21/T27 (diagnostics schema).
5. Existing Shadow-Live Daily ZIP artifacts with T27-compatible diagnostics (3 available at ticket authoring time; additional artifacts to be collected per Step B).
6. The master preflight checklist for Codex-ready tickets.

---

## Purpose and motivation

The feature request for the Entry-Location / Action-Hint Layer identified a concrete operational gap: a candidate that is `confirmed_candidates` + `direct_ok` on Day 0 of its confirmed state currently receives no warning that its price may already be extended from the pattern trigger. The state machine metrics (`distance_from_ideal_entry_after_confirmed`, `freshness_distance_state_confirmed`) are null or uninformative on Day 0.

This ticket establishes the empirical basis required before any implementation ticket can be written. Specifically, it must answer:

1. What is the distribution of Day-0 confirmed candidates' structural proxy metrics (`expansion_progress_structural`, `freshness_distance_structural`) across runs?
2. Does the proxy distribution differ meaningfully by `entry_pattern` type?
3. What directional proxy-based warning signals can be observed from available structural fields, and which direct 4h fields are required before threshold candidates for `entry_location_status` classification (`ideal / acceptable / extended / chase`) can be empirically justified? (Step A produces field requirements and directional findings; calibrated thresholds are a Step B output only.)
4. Which additional fields must be added to `symbol_diagnostics.jsonl.gz` to enable direct 4h-EMA overextension measurement in future analysis runs?

**This ticket does not implement the Entry-Location Layer.** It produces analysis artifacts that form the basis for the implementation ticket (T_EL2).

---

## Critical pre-condition: diagnostics field availability

The fields proposed in the feature request as primary inputs to the entry-location computation (`close_vs_ema20_4h_pct`, `bars_above_ema20_4h`, `dist_to_ema20_4h_pct_abs`) are **not currently present** in `symbol_diagnostics.jsonl.gz`. They are computed internally by T5 but not written to the diagnostics output.

Additionally, `distance_from_ideal_entry_after_confirmed` (Abschnitt 4 §3D) is `None` for all Day-0 confirmed candidates in all available artifacts — by definition, since it measures drift relative to the confirmed-entry close, which has no prior bar on Day 0.

This means the analysis is split into two sequential steps:

**Step A — Proxy analysis (runnable immediately against existing 3 artifacts):** Uses available diagnostic fields as structural proxies to characterize the Day-0 confirmed population. Produces directional findings and identifies which direct 4h fields are needed.

**Step B — Direct 4h analysis (requires diagnostics extension + new artifact collection):** After Step A identifies the required fields, those fields are added to `symbol_diagnostics.jsonl.gz`. New artifacts are collected (minimum 3 runs with extended diagnostics). The analysis script is extended to use the direct 4h metrics and produce calibrated threshold candidates.

This ticket covers both steps. Codex implements Step A first, then Martin reviews and triggers Step B after the diagnostics extension is deployed.

---

## Step A: Proxy analysis script

### A.1 Input

- All available Shadow-Live Daily ZIP artifacts with T27-compatible diagnostics.
- For each artifact: `reports/runs/<date>/daily-<run_id>/symbol_diagnostics.jsonl.gz`.
- Do not use the `shadow-live-report.json` top-level file — it duplicates the daily report and does not add fields beyond what the diagnostics provide.

### A.2 Nested field access — mandatory

All diagnostic fields used in this script must be accessed via their correct sub-dict. The following mapping is authoritative:

| Field | Access path |
|---|---|
| `decision_bucket` | `rec['decision']['decision_bucket']` |
| `entry_pattern` | `rec['pattern']['entry_pattern']` |
| `entry_pattern_score` | `rec['pattern']['entry_pattern_score']` |
| `priority_score` | `rec['decision']['priority_score']` |
| `market_phase` | `rec['phase']['market_phase']` |
| `market_phase_confidence` | `rec['phase']['market_phase_confidence']` |
| `state_machine_state` | `rec['state']['state_machine_state']` |
| `bars_since_confirmed_entered` | `rec['state']['bars_since_confirmed_entered']` |
| `bars_since_early_entered` | `rec['state']['bars_since_early_entered']` |
| `bars_since_state_entered` | `rec['state']['bars_since_state_entered']` |
| `close_at_confirmed_entry_bar` | `rec['state']['close_at_confirmed_entry_bar']` |
| `distance_from_ideal_entry_after_confirmed` | `rec['state']['distance_from_ideal_entry_after_confirmed']` |
| `freshness_distance_state_confirmed` | `rec['state']['freshness_distance_state_confirmed']` |
| `expansion_progress_structural` | `rec['axes']['expansion_progress_structural']` |
| `freshness_distance_structural` | `rec['axes']['freshness_distance_structural']` |
| `reclaim_progress` | `rec['axes']['reclaim_progress']` |
| `pullback_quality_simplified` | `rec['axes']['pullback_quality_simplified']` |
| `reacceleration_strength_simplified` | `rec['axes']['reacceleration_strength_simplified']` |
| `volume_regime_shift` | `rec['axes']['volume_regime_shift']` |
| `structural_invalidation` | `rec['invalidation']['structural_invalidation']` |
| `timing_invalidation` | `rec['invalidation']['timing_invalidation']` |
| `execution_status_raw` | `rec['execution_status_raw']` (top-level, T27) |
| `execution_pass` | `rec['execution_pass']` (top-level) |
| `data_4h_available` | `rec['data_4h_available']` (top-level) |

**Do not attempt top-level access for any field listed under a sub-dict above.** Top-level access for these fields silently returns `None` or `KeyError` — it does not raise a visible error.

### A.3 Population filters

The analysis focuses on three populations:

**Population 1: Day-0 confirmed candidates (primary)**
```
decision_bucket == 'confirmed_candidates'
AND bars_since_confirmed_entered == 0
AND data_4h_available == True
```

**Population 2: Day-1+ confirmed candidates (staleness reference)**
```
decision_bucket == 'confirmed_candidates'
AND bars_since_confirmed_entered >= 1
AND data_4h_available == True
```

**Population 3: Early candidates (watch/early reference)**
```
decision_bucket == 'early_candidates'
AND bars_since_state_entered == 0
AND data_4h_available == True
```

Records where `data_4h_available == False` are excluded from all three populations and counted separately in a diagnostic summary.

### A.4 Proxy metrics to analyze

For each population, compute distributions of the following proxy fields (these are available in current diagnostics):

| Proxy field | Rationale |
|---|---|
| `expansion_progress_structural` | How far structural expansion has progressed (0–100); correlates with overextension risk |
| `freshness_distance_structural` | Staleness of the structural anchor (0–100); high value → pattern trigger is old |
| `reclaim_progress` | Completion of reclaim (0–100); relevant for `transition_reclaim` phase |
| `reacceleration_strength_simplified` | Move strength post-setup; high value + Day-0 → likely already moved |
| `volume_regime_shift` | Volume confirmation; high value = strong move |
| `pullback_quality_simplified` | Pullback quality before pattern; low value → no clean retracement yet |

For each proxy field, compute per population:
- Median, P25, P75, P90, P95
- Distribution histogram (10 buckets, 0–100)
- Breakdown by `entry_pattern` (top 5 patterns by frequency)
- Breakdown by `market_phase`

### A.5 Named candidate lookup

For each of the following named candidates, extract their full proxy profile across all available run dates where they appear in Population 1:

- `RENDERUSDT`
- `DOTUSDT`
- `AVAXUSDT`
- `DOGEUSDT`
- `PEPEUSDT`

For each named candidate per run: output a single-row summary with all proxy fields, `priority_score`, `entry_pattern`, `market_phase`, `execution_status_raw`.

### A.6 Pattern-specific breakdown

For Population 1, compute per `entry_pattern` type (separate table):

| Pattern | Count | median(expansion_progress) | median(freshness_dist_struct) | median(reclaim_progress) | median(reaccel_strength) |
|---|---|---|---|---|---|
| `early_reversal_break` | ... | ... | ... | ... | ... |
| `resume_reclaim` | ... | ... | ... | ... | ... |
| `ema_reclaim` | ... | ... | ... | ... | ... |
| `shallow_pullback` | ... | ... | ... | ... | ... |
| `continuation_breakout` | ... | ... | ... | ... | ... |
| _(other)_ | ... | ... | ... | ... | ... |

### A.7 Day-0 volume and frequency summary

Per run (across all available artifacts):

| Run date | Total confirmed | Day-0 confirmed | Day-1+ confirmed | Day-0 fraction | Day-0 direct_ok | Day-0 marginal |
|---|---|---|---|---|---|---|
| ... | ... | ... | ... | ... | ... | ... |

This establishes the scale of the problem: how many candidates per day are Day-0 and thus currently unwarned.

### A.8 Step A output files

All output files written to `reports/aux/entry_location_analysis/`:

| File | Content |
|---|---|
| `step_a_population_distributions.md` | Per-population proxy distributions, histograms, pattern breakdown |
| `step_a_named_candidates.md` | Named candidate profiles (RENDER, DOT, AVAX, DOGE, PEPE) |
| `step_a_day0_volume_summary.md` | Per-run Day-0 count table |
| `step_a_findings_and_field_requirements.md` | Key findings + explicit list of fields to add to diagnostics for Step B |

`step_a_findings_and_field_requirements.md` must include a table structured as follows:

| Field name | Source module (T-ticket) | Reason needed | Priority |
|---|---|---|---|
| `close_vs_ema20_4h_pct` | T5 raw features | Primary overextension indicator | Must-have |
| `bars_above_ema20_4h` | T5 raw features | 4h velocity proxy | Must-have |
| `dist_to_ema20_4h_pct_abs` | T5 raw features | Absolute distance variant | Must-have |
| _(additional fields identified by analysis)_ | ... | ... | ... |

The presence of `distance_to_last_structural_anchor_pct_abs`, `distance_to_range_high_pct_abs`, and `bars_since_last_structural_break_event` in T5 raw features must be verified by code inspection during Step A. If confirmed present, add them to the field requirements table. If absent or not computed, note that they require new computation.

---

## Step B: Direct 4h analysis (post-diagnostics extension)

Step B is not a separate ticket. It extends the same analysis script after the following pre-conditions are met:

1. A diagnostics extension ticket (T_EL1b or folded into T_EL2 Step 0) has added the required 4h fields to `symbol_diagnostics.jsonl.gz`.
2. At minimum 3 new Shadow-Live Daily runs have been collected with the extended diagnostics.

**Codex must implement the Step B code paths as guarded/conditional logic.** At script startup, the script checks whether the required 4h fields (`close_vs_ema20_4h_pct`, `bars_above_ema20_4h`, `dist_to_ema20_4h_pct_abs`) are present in the loaded diagnostics records. If these fields are absent or all-null across the loaded artifacts, Step B is skipped with an explicit log message:

```
[T_EL1 Step B] Required 4h fields not found in diagnostics. Step B skipped.
Step A completed successfully. Re-run after diagnostics extension and new artifact collection.
```

Step A must complete successfully regardless of whether Step B runs. A missing Step B is not a script failure.

### B.1 Additional fields (once available in diagnostics)

The script is extended to use:
- `close_vs_ema20_4h_pct` — primary overextension indicator
- `bars_above_ema20_4h` — 4h velocity proxy
- `dist_to_ema20_4h_pct_abs` — absolute distance variant
- Any additional fields confirmed by Step A code inspection

### B.2 Threshold candidate derivation

For Population 1 (Day-0 confirmed), compute `close_vs_ema20_4h_pct` distribution per `entry_pattern`. Propose threshold candidates for `entry_location_status` classification:

| `close_vs_ema20_4h_pct` range | Proposed `entry_location_status` | Justification |
|---|---|---|
| [0, T_ideal) | `ideal` | Near EMA20, clean entry |
| [T_ideal, T_acceptable) | `acceptable` | Slightly extended |
| [T_acceptable, T_extended) | `extended` | Meaningful extension |
| [T_extended, ∞) | `chase` | Do not chase |

Threshold values (T_ideal, T_acceptable, T_extended) must be derived from the empirical distribution, not assumed. They are the primary output of Step B.

Pattern-specific threshold candidates must be proposed if the distribution differs significantly across patterns (e.g. `early_reversal_break` vs `shallow_pullback`). "Significantly" means P75 values differ by more than 2 percentage points.

### B.3 Step B output files

Additional files in `reports/aux/entry_location_analysis/`:

| File | Content |
|---|---|
| `step_b_4h_distributions.md` | Direct 4h metric distributions per pattern |
| `step_b_threshold_candidates.md` | Proposed threshold values with statistical justification |
| `step_b_named_candidates_extended.md` | Named candidates with direct 4h metrics |

---

## Scope

### In scope

- Analysis script reading `symbol_diagnostics.jsonl.gz` from all available T27-compatible artifacts.
- Proxy-field distributions for Day-0 confirmed, Day-1+ confirmed, and Day-0 early populations.
- Named candidate profiles (RENDER, DOT, AVAX, DOGE, PEPE).
- Code inspection: verify presence of structural anchor distance fields in T5 raw feature pipeline.
- Field requirements table for the diagnostics extension.
- Step B extension (triggered after diagnostics extension + new artifact collection).

### Out of scope

- Implementing `entry_location_status` or `entry_action_hint` fields. That is T_EL2.
- Modifying `priority_score` formula. That requires a separate spec update.
- Modifying decision bucket membership. Bucket semantics are unchanged.
- Forward-return analysis. Requires T18 evaluation infrastructure; deferred.
- ATR-scaled thresholds. Deferred to post-implementation enhancement.
- Any live policy change.

---

## Output path conventions

Per T19 conventions, all analysis outputs are written to `reports/aux/entry_location_analysis/`. No files are committed to the repo. No existing report schema files are modified.

---

## Acceptance criteria

### Step A

1. Script runs without error against all available T27-compatible artifacts.
2. `step_a_population_distributions.md` contains per-population distributions for all 6 proxy fields, with per-pattern breakdown.
3. `step_a_named_candidates.md` contains full profiles for RENDER, DOT, AVAX, DOGE, PEPE across all available run dates where they appear in Population 1.
4. `step_a_day0_volume_summary.md` shows per-run Day-0 vs Day-1+ counts.
5. `step_a_findings_and_field_requirements.md` contains the field requirements table with code-inspected presence status for each field.
6. All field accesses use the correct sub-dict paths from §A.2. No top-level access for sub-dict fields.
7. `None` / null values in proxy fields are counted and reported separately; they are not treated as 0 or excluded silently.
8. `data_4h_available == False` records are excluded from all three populations and counted in the diagnostic summary.

### Step B (after pre-conditions met)

9. Script correctly reads the extended 4h fields from new artifacts.
10. If required 4h fields are absent or all-null, script logs the explicit skip message and exits cleanly with Step A outputs intact. It does not raise an error or produce empty Step B output files.
11. `step_b_threshold_candidates.md` proposes empirically grounded threshold values with the statistical basis shown (P25/P50/P75/P90 per pattern).
12. Pattern-specific thresholds are proposed where justified; universal thresholds are proposed otherwise.
13. Threshold table is in a format directly usable as config defaults in T_EL2.
