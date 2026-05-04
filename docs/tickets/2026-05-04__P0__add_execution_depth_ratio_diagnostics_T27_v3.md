# T27: Add Execution Depth Ratio Diagnostics for Position-Size Policy Calibration

## Metadata

- Ticket ID: T27
- Title: Add Execution Depth Ratio Diagnostics for Position-Size Policy Calibration
- Status: Draft — ready for preflight review
- Priority: P0
- Language: Implementation and code artifacts in English
- Primary mode affected: Daily and Intraday scanner diagnostics / execution diagnostics
- Scope type: Diagnostics-only / data-enrichment ticket

---

## Authoritative reference set

1. The seven v2.1 specification section files.
2. `independence_release_gesamtkonzept_final.md`.
3. `v2_1_addendum_for_future_tickets_and_new_chats_updated.md`.
4. Current repo reality, especially:
   - `scanner/execution/grading.py`
   - `scanner/pipeline/liquidity.py`
   - `scanner/output/diagnostics.py`
   - `scanner/output/report_builder.py`
   - any schema/model files that define `symbol_diagnostics.jsonl.gz`
5. Existing implemented contracts from T12, T16, T21, T21.1, T22, T23, T24, T25, and T26.
6. T26 analysis output and findings.
7. The master preflight checklist for Codex-ready tickets.

The seven v2.1 section files remain the primary authority. `independence_release_gesamtkonzept_final.md` is secondary and must be interpreted consistently with the seven section files. This ticket is implementation guidance and may not override the v2.1 specs or the Gesamtkonzept.

---

## Purpose and motivation

T26 confirmed a material execution-depth bottleneck:

- 901 `fail` cases across the analyzed 8-day Shadow-Live window.
- 212 structurally actionable fail cases.
- 94 counterfactual `confirmed_candidates`.
- 118 counterfactual `early_candidates`.
- 318 `marginal` top-bucket cases with a strong priority-score/rank penalty.

However, T26 could not calibrate reduced-size execution thresholds because raw depth data was not present in diagnostics:

- `depth_ratio_derivable = False` for all fail cases.
- `available_depth_1pct_usdt` / `available_depth_usdt` was not available.
- `available_depth_ratio` was not available.
- spread/slippage diagnostic fields were not available.

Therefore, T27 must enrich execution diagnostics so later analysis can answer:

- Was a `fail` symbol barely below the depth threshold or far below it?
- Would the symbol have cleared at 75%, 50%, or 25% position size?
- Is depth the only bottleneck, or would spread/slippage still block the trade?
- How should `marginal` be calibrated by depth-ratio band in a later Spec-Ticket?

T27 must not implement reduced-size trading. It only exposes the diagnostics needed for later calibration.

---

## Non-goals

T27 must not change trading behavior.

Out of scope:

- No `fail -> marginal` promotion.
- No change to `execution_status_raw` semantics.
- No change to `execution_pass` semantics.
- No change to `execution_grade_t16` / execution-grade semantics.
- No change to T12 bucket rules.
- No change to T16 execution grader behavior except exposing already-computed or newly-computed diagnostic fields.
- No `tranche_ok` extension.
- No order splitting.
- No Market-Cap floor changes.
- No reduced-size trading policy.
- No entry/exit decision changes.
- No forward return, MFE, or MAE analysis.
- No migration from the current top-level diagnostics schema to a nested execution schema.

T27 is a diagnostics/data-enrichment ticket only.

---

## Current execution contract to preserve

The current T12/T16 execution contract remains unchanged:

| `execution_status_raw` | `execution_pass` | `execution_grade_t16` | Meaning |
|---|---:|---:|---|
| `direct_ok` | `True` | `100.0` | Fully tradable at standard position |
| `tranche_ok` | `True` | `75.0` | Fully tradable, benefits from tranching |
| `marginal` | `False` | `40.0` | Partially constrained; does not block candidate buckets |
| `fail` | `False` | `0.0` | Hard execution block |
| `unknown` | `None` | `null` | Orderbook stale/missing/no reliable contract |

Important invariant:

```text
Only execution_status_raw = "fail" hard-blocks early_candidates / confirmed_candidates.
marginal + execution_pass = False remains valid and must not be treated as a bug.
```

T27 may add diagnostic fields, but it must not reinterpret these statuses.

### Diagnostic field naming

The current diagnostics schema uses top-level execution fields. In diagnostic records, the current execution grade field is `execution_grade_t16`, not `execution_grade`.

If internal production code uses a canonical variable named `execution_grade`, that internal value maps to the top-level diagnostic field `execution_grade_t16`.

Do not introduce a new top-level `execution_grade` field in T27 unless the repo already emits one. Existing field names must remain backward-compatible.

---

## Scope

### In scope

Add execution-depth and spread/slippage diagnostics to `symbol_diagnostics.jsonl.gz` for all records where execution was attempted or where orderbook/tradeability evaluation is available.

Required diagnostic additions:

```text
available_depth_1pct_usdt
depth_threshold_1pct_usdt
available_depth_ratio
depth_ratio_band
recommended_position_factor_preview
execution_limiting_metric
spread_pct
estimated_slippage_bps
orderbook_snapshot_age_ms
```

Strongly preferred side-specific depth additions:

```text
bid_depth_1pct_usdt
ask_depth_1pct_usdt
depth_side_used
```

### Out of scope

- No policy decision based on these fields.
- No bucket changes.
- No rank changes.
- No config threshold changes unless already required to expose an existing configured value.
- No external API additions beyond already-used execution/orderbook fetches.
- No additional execution fetches for symbols that were not already selected for execution evaluation.
- No nested execution diagnostics schema migration.

---

## Pipeline placement

T27 affects the execution diagnostics/output path only.

The new fields must be computed or passed through in the execution/orderbook layer and emitted in `symbol_diagnostics.jsonl.gz`.

T27 must not expand the set of symbols for which execution data is fetched.

Execution data remains governed by the existing execution subset rules. If a symbol does not receive execution evaluation in the current run, the new execution diagnostic fields must be `null` or a documented non-evaluated enum value as specified below, not guessed.

Required pipeline invariant:

```text
T27 enriches diagnostics after execution/orderbook evaluation. It must not trigger additional orderbook fetches for symbols outside the current execution evaluation subset.
```

---

## Field definitions

### `available_depth_1pct_usdt`

Type:

```text
float | null
```

Meaning:

Total usable quote-depth in USDT within the current 1% execution depth window on the relevant execution side.

For spot long entries, the relevant side is normally the ask side. If the current implementation uses another convention, Codex must preserve the existing convention and document it in code comments/tests.

Rules:

- If orderbook is available and depth can be computed: numeric `>= 0.0`.
- If orderbook is missing/stale/not evaluated: `null`.
- If the computed value is `NaN`, `inf`, or `-inf`: treat as invalid and emit `null`.
- Do not coerce missing/invalid depth to `0.0`.

### `depth_threshold_1pct_usdt`

Type:

```text
float | null
```

Meaning:

The configured or effective minimum required 1% depth threshold used by the current execution gate.

Expected source:

```text
cfg.execution.min_depth_1pct_usd
```

Rules:

- Must reflect the actual threshold used in the run.
- If execution was not attempted and the threshold is still known from config, it may be emitted.
- If threshold cannot be determined, emit `null`.
- Non-finite threshold values are invalid and must not be emitted as numeric outputs.

### `available_depth_ratio`

Type:

```text
float | null
```

Formula:

```text
available_depth_ratio = available_depth_1pct_usdt / depth_threshold_1pct_usdt
```

Rules:

- Compute only if both numerator and denominator are finite and denominator > 0.
- If orderbook is available but depth is insufficient, this field must still be numeric, typically `< 1.0`.
- If orderbook is missing/stale/not evaluated: `null`.
- If denominator is missing, zero, negative, or non-finite: `null`.
- Do not coerce `null` to `0.0`.

Interpretation:

```text
available_depth_ratio >= 1.0  => depth gate clears at standard threshold
available_depth_ratio < 1.0   => depth gate does not clear at standard threshold
available_depth_ratio = null  => depth ratio not evaluable
```

### `depth_ratio_band`

Type:

```text
string | null
```

Allowed values:

```text
full
reduced_75
reduced_50
reduced_25
below_min
not_evaluable
```

Mapping:

```text
if available_depth_ratio is null:
    depth_ratio_band = "not_evaluable"

elif available_depth_ratio >= 1.00:
    depth_ratio_band = "full"

elif available_depth_ratio >= 0.75:
    depth_ratio_band = "reduced_75"

elif available_depth_ratio >= 0.50:
    depth_ratio_band = "reduced_50"

elif available_depth_ratio >= 0.25:
    depth_ratio_band = "reduced_25"

else:
    depth_ratio_band = "below_min"
```

This field is diagnostic only. It must not change execution status.

### `recommended_position_factor_preview`

Type:

```text
float | null
```

Allowed numeric values:

```text
1.00
0.75
0.50
0.25
0.00
```

Mapping:

```text
full          -> 1.00
reduced_75    -> 0.75
reduced_50    -> 0.50
reduced_25    -> 0.25
below_min     -> 0.00
not_evaluable -> null
```

Important:

This is a preview/calibration field only. It must not be used for live sizing, trading, bucket assignment, or execution-grade changes in T27.

### `execution_limiting_metric`

Type:

```text
string | null
```

Allowed values:

```text
depth_1pct
spread
slippage
stale_orderbook
missing_orderbook
unknown
none
not_evaluated
```

Meaning:

The primary metric that limited execution quality, if known.

Rules:

- `depth_1pct`: depth was the primary limiting metric.
- `spread`: spread was the primary limiting metric.
- `slippage`: estimated slippage was the primary limiting metric.
- `stale_orderbook`: orderbook was present but stale.
- `missing_orderbook`: no usable orderbook was available.
- `unknown`: execution failed or was constrained but the limiting metric cannot be determined.
- `none`: execution was evaluated and no limiting metric was detected.
- `not_evaluated`: execution was not attempted for this symbol.

If existing reason codes already encode this information, map from the existing reason code. Do not invent a conflicting reason taxonomy.

### `depth_ratio_band = "not_evaluable"` vs. `execution_limiting_metric = "not_evaluated"`

These two values intentionally answer different questions:

- `depth_ratio_band = "not_evaluable"` describes the metric result: the depth ratio could not be computed.
- `execution_limiting_metric = "not_evaluated"` describes the pipeline state: execution evaluation was not attempted for this symbol.

For `execution_attempted = False`, keep:

```text
depth_ratio_band = "not_evaluable"
execution_limiting_metric = "not_evaluated"
```

Do not introduce a second band value unless the allowed `depth_ratio_band` enum is explicitly changed in a future ticket.

### `spread_pct`

Type:

```text
float | null
```

Meaning:

Current bid/ask spread as a percentage of mid price.

Formula, if not already available:

```text
spread_pct = ((best_ask - best_bid) / mid_price) * 100
mid_price = (best_ask + best_bid) / 2
```

Rules:

- Compute only if best bid and best ask are finite, `best_bid > 0`, `best_ask > 0`, and `mid_price > 0`.
- If orderbook missing/stale/not evaluated: `null`.
- If values are invalid/non-finite: `null`.
- Do not coerce missing spread to `0.0`.

### `estimated_slippage_bps`

Type:

```text
float | null
```

Meaning:

Estimated slippage in basis points for the current standard execution notional, if available from current execution/orderbook logic.

Implementation requirement:

Codex must inspect the existing execution/liquidity code before emitting permanent `null` values. Check at minimum:

```text
scanner/pipeline/liquidity.py
scanner/execution/grading.py
related execution metric helpers
```

Rules:

- If current code already computes slippage, expose the computed value as `estimated_slippage_bps`.
- If the existing slippage metric is not already in basis points, convert it to basis points before emitting.
- If the existing slippage metric unit is unknown or cannot be verified, emit `null` and document the gap in a code comment and test.
- If no slippage metric exists, emit `null` and document in a code comment and test that slippage is currently not derivable without adding new simulation logic.
- Do not add a new expensive slippage simulation in T27.
- Do not add extra orderbook fetches.
- Non-finite values must emit `null`.

### `orderbook_snapshot_age_ms`

Type:

```text
int | null
```

Meaning:

Age of the orderbook snapshot used for execution evaluation, in milliseconds.

Rules:

- If snapshot timestamp and run/evaluation timestamp are available, compute age in milliseconds.
- If the source calculation yields a float, round or floor consistently to an integer millisecond value before emitting.
- If not derivable: `null`.
- Negative ages are invalid and must emit `null`.
- Non-finite values must emit `null`.

### `bid_depth_1pct_usdt`

Type:

```text
float | null
```

Meaning:

USDT bid-side depth within 1% of best bid or relevant reference price.

Rules:

- Emit if available or cheap to compute from the existing orderbook snapshot.
- Otherwise `null`.

### `ask_depth_1pct_usdt`

Type:

```text
float | null
```

Meaning:

USDT ask-side depth within 1% of best ask or relevant reference price.

Rules:

- For spot buy entries, this is usually the more relevant depth field.
- Emit if available or cheap to compute from the existing orderbook snapshot.
- Otherwise `null`.

### `depth_side_used`

Type:

```text
string | null
```

Allowed values:

```text
ask
bid
combined
unknown
not_evaluated
```

Meaning:

Which depth side was used to compute `available_depth_1pct_usdt`.

Rules:

- Use `ask` if spot-entry ask depth is used.
- Use `combined` only if the existing implementation already uses combined depth.
- Use `unknown` if depth is numeric but side cannot be determined.
- Use `not_evaluated` if execution was not attempted.
- Use `null` only if the symbol diagnostics layer cannot determine this field at all.

---

## Required behavior by execution state

### Execution attempted and orderbook available

For symbols where execution was attempted and orderbook data is available:

```text
available_depth_1pct_usdt       numeric or null only if invalid
depth_threshold_1pct_usdt       numeric if config available
available_depth_ratio           numeric if numerator/denominator valid
depth_ratio_band                mapped from available_depth_ratio
recommended_position_factor_preview mapped from depth_ratio_band
spread_pct                      numeric if derivable
estimated_slippage_bps          numeric if existing logic provides it, else null
orderbook_snapshot_age_ms       numeric int if derivable
execution_limiting_metric       mapped from evaluation result/reason
```

### Execution attempted and depth insufficient

For `execution_status_raw = "fail"` with `execution_reason_raw = "depth_1pct_insufficient"`:

```text
available_depth_1pct_usdt       must be numeric if orderbook was available
available_depth_ratio           must be numeric if threshold is valid
depth_ratio_band                usually reduced_75/reduced_50/reduced_25/below_min
recommended_position_factor_preview must be mapped accordingly
execution_limiting_metric       "depth_1pct"
```

This is the core T27 requirement.

### Execution attempted but orderbook missing/stale

For missing/stale orderbook:

```text
available_depth_1pct_usdt       null
available_depth_ratio           null
depth_ratio_band                "not_evaluable"
recommended_position_factor_preview null
execution_limiting_metric       "missing_orderbook" or "stale_orderbook"
```

### Execution status unknown

For `execution_status_raw = "unknown"`:

```text
execution_limiting_metric       "unknown"
available_depth_1pct_usdt       numeric if orderbook data is available and valid, otherwise null
available_depth_ratio           numeric if depth and threshold are valid, otherwise null
depth_ratio_band                mapped from available_depth_ratio, otherwise "not_evaluable"
recommended_position_factor_preview mapped from depth_ratio_band, otherwise null
spread_pct                      numeric if derivable, otherwise null
estimated_slippage_bps          numeric if existing logic provides it and unit is verified/converted to bps, else null
orderbook_snapshot_age_ms       numeric int if derivable, otherwise null
```

`unknown` must not be treated as `fail` and must not be treated as `not_attempted`. It means no reliable execution contract was produced, but diagnostic metrics may still be emitted if they are safely derivable from the available orderbook data.

### Execution not attempted

For `execution_attempted = False`:

```text
available_depth_1pct_usdt       null
available_depth_ratio           null
depth_ratio_band                "not_evaluable"
recommended_position_factor_preview null
execution_limiting_metric       "not_evaluated"
spread_pct                      null
estimated_slippage_bps          null
orderbook_snapshot_age_ms       null
```

`depth_threshold_1pct_usdt` may be emitted from config if readily available, otherwise `null`.

---

## Missing vs invalid vs failed semantics

T27 must preserve these distinctions:

```text
not_evaluated:
  execution was not attempted for this symbol.

not_evaluable:
  execution/orderbook evaluation was attempted or expected, but the diagnostic metric cannot be computed from available data.

failed:
  execution was evaluated and the metric failed a threshold, e.g. available_depth_ratio < 1.0.

marginal:
  current T16/T12 marginal status; still not a pass, still not a hard candidate bucket block.
```

Required invariant:

```text
Nicht evaluierbar / nicht bewertet und fachlich negativ bewertet sind getrennte Zustände und müssen im Code getrennt erhalten bleiben.
```

Do not collapse missing, stale, not attempted, and failed depth into the same numeric value.

---

## Numeric robustness

T27 adds numeric diagnostic fields. Therefore:

```text
Non-finite numeric values (`NaN`, `inf`, `-inf`) are invalid / not evaluable inputs and must not be emitted as numeric-looking outputs.
```

Rules:

- `None`, missing keys, `NaN`, `inf`, `-inf` must result in `null` for derived numeric diagnostic fields.
- Division by zero or quasi-zero threshold must result in `available_depth_ratio = null`.
- Empty orderbook must not become depth `0.0` unless the existing execution logic explicitly treats an empty but valid orderbook as zero depth.
- If empty orderbook means missing/unusable orderbook in current code, emit `null` and `execution_limiting_metric = "missing_orderbook"` or `"unknown"`.

---

## Output schema changes

### `symbol_diagnostics.jsonl.gz`

T27 must add new fields top-level to each symbol diagnostic record, consistent with the current diagnostics schema.

T27 must not move existing execution fields into a nested `execution` object.

Existing top-level fields that must remain top-level and unchanged:

```text
execution_attempted
execution_status_raw
execution_reason_raw
execution_pass
execution_grade_t16
```

T27 is not a schema migration ticket. A future schema migration may consolidate execution diagnostics into a nested object, but T27 must preserve current consumer compatibility.

Required top-level example:

```json
{
  "symbol": "RUJIUSDT",
  "execution_attempted": true,
  "execution_status_raw": "fail",
  "execution_reason_raw": "depth_1pct_insufficient",
  "execution_pass": false,
  "execution_grade_t16": 0.0,

  "available_depth_1pct_usdt": 1234.56,
  "depth_threshold_1pct_usdt": 5000.0,
  "available_depth_ratio": 0.246912,
  "depth_ratio_band": "below_min",
  "recommended_position_factor_preview": 0.0,
  "execution_limiting_metric": "depth_1pct",

  "spread_pct": 0.18,
  "estimated_slippage_bps": null,
  "orderbook_snapshot_age_ms": 850,

  "bid_depth_1pct_usdt": 900.0,
  "ask_depth_1pct_usdt": 1234.56,
  "depth_side_used": "ask"
}
```

Minimum requirement:

- New fields must be present top-level in `symbol_diagnostics.jsonl.gz`.
- Existing top-level execution fields must not be removed, renamed, moved, or shadowed.
- All existing consumers, including T26, must continue to read the old fields without schema changes.

### `report.json`

T27 does not require adding all new fields to compact `report.json`.

If the report already contains compact execution summaries, Codex may add aggregate counts only if low-risk. Do not bloat `report.json` with per-symbol depth fields unless current report schema already supports it.

Required:

```text
symbol_diagnostics.jsonl.gz is the canonical full diagnostics sink for these fields.
```

---

## T26 compatibility update

T27 must update the existing T26 analysis script so it can consume the new post-T27 fields.

Required script update:

```text
scripts/analyze_execution_depth_shadow_live.py
```

If the actual T26 script path differs, update the real T26 script path found in the repo.

Required field reads:

```python
avail = r.get("available_depth_1pct_usdt")
if avail is None:
    avail = r.get("available_depth_usdt")  # backward-compatible fallback only

thresh = r.get("depth_threshold_1pct_usdt")
```

Rules:

- Prefer `available_depth_1pct_usdt`.
- Keep fallback to `available_depth_usdt` only for compatibility with older ad-hoc analysis outputs if present.
- Use `depth_threshold_1pct_usdt` as the threshold field.
- Update T26 tests so a post-T27 diagnostic record with `available_depth_1pct_usdt` and `depth_threshold_1pct_usdt` produces `depth_ratio_derivable = True`.

Acceptance requirement:

```text
T26 can be rerun after T27 and derive depth ratios from the new top-level fields.
```

---

## Backward compatibility

T27 must preserve existing diagnostics consumers.

Rules:

- Existing fields must not be removed.
- Existing meanings must not be changed.
- Existing top-level execution fields must not be moved into nested structures.
- New fields are appended top-level.
- T26 analysis script must still run after T27 and must be updated to discover the new depth fields.
- Existing T24/T25 report behavior must not break.

---

## Config handling

T27 should use existing execution config.

Expected existing key:

```text
cfg.execution.min_depth_1pct_usd
```

If the actual repo key differs, use the existing repo key and document the mapping in code/tests.

No new config keys are required for T27.

If a new config key is unavoidable, it must follow these rules:

```text
Partial overrides in the new config block are field-wise merged with central defaults; missing subkeys are not invalid.
Invalid config values fail fast with a clear error.
```

But preference is: no new config.

---

## Determinism

T27 must be deterministic.

Required invariant:

```text
With identical input orderbook, identical config, and identical run timestamp metadata, diagnostic field outputs are identical.
```

No field may depend on dict/set iteration order.

If multiple limiting metrics are violated and existing code does not already define priority, use this deterministic order for `execution_limiting_metric`:

```text
missing_orderbook
stale_orderbook
depth_1pct
spread
slippage
unknown
none
```

If current production code already has a canonical reason priority order, use that instead and test it.

---

## Tests

Add or update tests for the following cases.

### Depth diagnostics

- Orderbook available, depth above threshold:
  - `available_depth_1pct_usdt` numeric
  - `depth_threshold_1pct_usdt` numeric
  - `available_depth_ratio >= 1.0`
  - `depth_ratio_band = "full"`
  - `recommended_position_factor_preview = 1.0`

- Orderbook available, depth ratio `0.80`:
  - `depth_ratio_band = "reduced_75"`
  - `recommended_position_factor_preview = 0.75`

- Orderbook available, depth ratio `0.60`:
  - `depth_ratio_band = "reduced_50"`
  - `recommended_position_factor_preview = 0.50`

- Orderbook available, depth ratio `0.30`:
  - `depth_ratio_band = "reduced_25"`
  - `recommended_position_factor_preview = 0.25`

- Orderbook available, depth ratio `0.10`:
  - `depth_ratio_band = "below_min"`
  - `recommended_position_factor_preview = 0.0`

- `execution_status_raw = "fail"` with `execution_reason_raw = "depth_1pct_insufficient"`:
  - depth fields still emitted and numeric if orderbook data exists
  - `execution_limiting_metric = "depth_1pct"`

### Missing / not evaluable

- Execution not attempted:
  - depth fields null
  - `depth_ratio_band = "not_evaluable"`
  - `recommended_position_factor_preview = null`
  - `execution_limiting_metric = "not_evaluated"`

- Missing orderbook:
  - depth fields null
  - `execution_limiting_metric = "missing_orderbook"`

- Stale orderbook:
  - depth fields null unless current code still computes stale metrics for diagnostics
  - `execution_limiting_metric = "stale_orderbook"`

### Numeric robustness

- `available_depth_1pct_usdt = NaN`:
  - emitted as `null`
  - no JSON `NaN`

- threshold `0`, `None`, `NaN`, `inf`:
  - `available_depth_ratio = null`
  - no exception unless config validation should fail earlier

- best bid/ask invalid:
  - `spread_pct = null`

- negative `orderbook_snapshot_age_ms`:
  - emitted as `null`

- float source for orderbook age:
  - emitted as integer milliseconds

### Side-specific depth

- Spot-entry ask-side depth:
  - `ask_depth_1pct_usdt` populated when available
  - `depth_side_used = "ask"`

- If current implementation uses combined depth:
  - `depth_side_used = "combined"`
  - test documents current behavior

### Slippage discovery

- If existing code exposes slippage:
  - `estimated_slippage_bps` is populated from the existing metric

- If existing code does not expose slippage:
  - `estimated_slippage_bps = null`
  - test documents that slippage is not currently derivable without adding new simulation logic

### Diagnostics schema

- `symbol_diagnostics.jsonl.gz` includes all required new fields top-level.
- Existing top-level execution fields remain present and unchanged.
- No nested `execution` object is introduced by T27.
- T26 analysis script can read the new depth fields.
- No per-symbol depth fields are required in compact `report.json`.

### No policy change

- Existing `execution_status_raw` remains unchanged for all tested scenarios.
- Existing `execution_pass` remains unchanged.
- Existing `execution_grade_t16` remains unchanged.
- Existing bucket assignment remains unchanged.
- `marginal + execution_pass = False` remains valid.

---

## Acceptance criteria

- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `available_depth_1pct_usdt`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `depth_threshold_1pct_usdt`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `available_depth_ratio`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `depth_ratio_band`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `recommended_position_factor_preview`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `execution_limiting_metric`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `spread_pct`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `estimated_slippage_bps`.
- [ ] `symbol_diagnostics.jsonl.gz` includes top-level `orderbook_snapshot_age_ms` as `int | null`.
- [ ] `bid_depth_1pct_usdt`, `ask_depth_1pct_usdt`, and `depth_side_used` are emitted top-level if derivable from the existing orderbook snapshot; otherwise they are present as `null` / `unknown` / `not_evaluated` according to the rules above.
- [ ] Existing top-level fields `execution_attempted`, `execution_status_raw`, `execution_reason_raw`, `execution_pass`, and `execution_grade_t16` are not removed, renamed, moved, or shadowed.
- [ ] No nested `execution` diagnostics object is introduced by T27.
- [ ] For `depth_1pct_insufficient` fail records with available orderbook, `available_depth_ratio` is numeric and `< 1.0`.
- [ ] For missing/stale/not-attempted records, depth ratio is `null`, not `0.0`.
- [ ] No non-finite numeric values are emitted in JSON outputs.
- [ ] Existing execution statuses, passes, grades, bucket assignments, and priority scores are unchanged by T27.
- [ ] T26 can be rerun after T27 and derive depth ratios from the new top-level fields.
- [ ] T26 script is updated to read `available_depth_1pct_usdt` and `depth_threshold_1pct_usdt`.
- [ ] Tests cover depth bands, missing/stale orderbook, numeric robustness, schema emission, slippage discovery, T26 compatibility, and no-policy-change invariants.
- [ ] No live external API calls are added beyond existing scanner execution/orderbook calls.
- [ ] No additional execution fetches are triggered for symbols outside the existing execution subset.

---

## Invariants

- T27 is diagnostics-only.
- T27 must not change scanner decisions.
- T27 must not change execution status semantics.
- T27 must not change bucket rules.
- T27 must not change ranking rules.
- T27 must not change position sizing.
- T27 must not implement reduced-size trading.
- T27 must preserve missing vs failed vs not evaluated.
- T27 must preserve existing T12/T16 behavior.
- T27 must preserve the current top-level diagnostics schema.
- `symbol_diagnostics.jsonl.gz` is the canonical sink for full per-symbol execution diagnostics.

---

## Follow-on after T27

After T27 is implemented and 5–10 new Shadow-Live daily runs have been collected, run a follow-on analysis ticket:

```text
T28: Calibrate Reduced-Size Execution Policy from Depth Ratio Diagnostics
```

T28 should evaluate:

- How many structurally actionable fail cases have `available_depth_ratio >= 0.75`.
- How many have `available_depth_ratio >= 0.50`.
- How many have `available_depth_ratio >= 0.25`.
- How many remain `< 0.25`.
- Whether spread/slippage would still block reduced-size trades.
- Whether `execution_grade_t16 = 40.0` for `marginal` is too punitive.
- Whether `execution_grade_t16` should depend on `recommended_position_factor_preview`.
- Whether a future Spec-Ticket should define:
  - `marginal` as reduced-size-tradable.
  - `fail` as not tradable even at minimum defined position floor.
  - a production `recommended_position_factor`.
  - depth-ratio-based execution-grade calibration.

No T28/Tiered-Execution policy is part of T27.
