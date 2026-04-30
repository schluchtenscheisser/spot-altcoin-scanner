> ARCHIVED (ticket): Implemented in PR for this ticket. Current truth is defined by repo reality, current implementation contracts, and relevant current documentation.

# Title
[P1] Add Universe Classification and Backward-Compatible Candidate Segmentation (Ticket 23)

Priority note: P1 is intentional. Shadow-Live operation is technically stable, and T23 is an output-usability / segmentation improvement rather than a run-blocking infrastructure fix. It is still the next highest-priority workstream before calibration changes.

## Context / Source

After four scheduled Shadow-Live runs, the scanner is technically stable:

- real MEXC full-universe Daily runs execute successfully,
- diagnostics are fully populated,
- Evaluation Replay reconstructs events,
- Execution diagnostics are invariant-complete,
- artifacts are uploaded correctly,
- no forbidden path writes occur.

The main operational issue is now output usability: raw candidate buckets contain stable/cash proxies, leveraged/margin-like products, tokenized stocks/ETFs, commodity/index proxies, wrapped/synthetic BTC proxies, and classic crypto assets in the same candidate lists.

This ticket adds deterministic universe classification and candidate-facing segmentation without changing the scanner's business logic.

```yaml
depends_on: [13, 21, 21.1]
```

Authoritative references:

- v2.1 section files and final Gesamtkonzept remain the primary functional authority.
- Ticket 13 output/report schema contract.
- Ticket 21 / 21.1 diagnostics serialization and invariant contracts.
- Ticket 22 Shadow-Live workflow and artifact contracts are operational context, not a functional dependency.
- Current `main` after Ticket 22.

If the current authoritative v2.1 reference set, existing repo canonical/authority documents, and existing code conflict, the current authoritative v2.1 reference set wins. Repo documents remain valid only insofar as they do not contradict that reference set.

---

## Goal

Add a deterministic, explainable universe classification layer and backward-compatible candidate segmentation so that reports can distinguish:

- classic crypto candidates,
- stable/cash proxies,
- leveraged/margin-like products,
- tokenized stocks/ETFs,
- commodity/index proxies,
- wrapped/synthetic BTC proxies,
- unknown/unclassified assets.

The goal is **report usability**, not strategy calibration.

T23 must remove obvious non-candidates such as stable/cash proxies and leveraged/margin-like products from candidate-facing views, while keeping investable non-classic assets such as tokenized stocks, commodities, and wrapped/synthetic BTC visible and candidate-capable.

---

## Non-goal

T23 must not decide whether tokenized stocks, commodities, wrapped BTC proxies, or unknown assets are good or bad trades.

Examples such as `COCAUSDT`, `INTCONUSDT`, `OIL(USOON)USDT`, `GOOGLONUSDT`, or `BTCBAMUSDT` must not be silently removed unless they fall into a deliberately excluded category such as `stable_or_cash_proxy` or `leveraged_or_margin_token`.

If a non-classic signal is detected but cannot be verified, the symbol must remain visible as `unknown` with low confidence and must not be blocked. If no specific non-classic rule or suspicious pattern matched, the symbol should be classified as low-confidence `classic_crypto` as defined below.

---

## Architectural decision

### Hard candidate exclusion, not hard pipeline exclusion

T23 introduces **candidate-facing exclusion**, not a new Eligibility or pipeline hard stop.

Stable/cash proxies and leveraged/margin-like products must be excluded from candidate-facing lists and segmented candidate views, but the raw pipeline output must remain available.

This is intentional:

- Raw bucket fields remain unchanged for auditability and backward compatibility.
- Diagnostics remain available for symbols that run through the pipeline.
- Existing Phase/State/Decision/Execution semantics remain unchanged.
- No T3 Eligibility thresholds are changed.

If an implementation later wants to use this classification as a cost optimization before expensive fetches, that must be a separate explicitly scoped ticket. Do not introduce such behavior in T23.

---

## T13 report-schema compatibility requirement

T23 extends reports **additively**.

Existing Ticket 13 report schema fields must remain backward-compatible and unchanged, including:

- existing raw bucket names,
- existing raw bucket counts,
- existing candidate item semantics,
- report locations,
- diagnostics path fields,
- manifest path fields.

Existing consumers that read the original T13 fields must continue to work unchanged.

New classification/segmentation data must be added under dedicated additive blocks, for example:

```text
universe_classification
candidate_segments
excluded_candidate_summary
category_counts_by_bucket
```

Do not replace existing bucket fields with segmented structures. Do not rename existing bucket fields. Do not change the meaning of existing counts.

A separate convenience output such as `universe_classification.json` may be added only if useful, but it is not required and must not become the sole source of classification data.

---

## Categories

T23 defines this exact initial category set:

```text
classic_crypto
stable_or_cash_proxy
leveraged_or_margin_token
tokenized_stock_or_etf
commodity_or_index_proxy
wrapped_or_synthetic_btc
unknown
```

Do not add `meme_or_community_token` in T23. Meme/community classification is deferred because it lacks a deterministic criterion without an external taxonomy or explicit manual mapping.

Add a note to `docs/canonical/feature_enhancements.md` or the current canonical feature-enhancement location that meme/community-token classification is a deferred enhancement.

---

## Category semantics

### `classic_crypto`

Meaning:

- Standard crypto asset/token listing that is not classified into a more specific non-classic category and did not trigger an unverified non-classic/suspicious pattern.

`classic_crypto` is the **positive residual default** in T23. If no specific non-classic rule matched and no stock-like, commodity-like, stable/cash, leveraged/margin, or wrapped/synthetic-BTC signal was detected, classify the symbol as:

```text
universe_category = classic_crypto
universe_category_confidence = low
universe_category_reason = no_non_classic_rule_matched
candidate_excluded = false
candidate_exclusion_reason = null
```

This is intentionally different from `unknown`. Reserve `unknown` for symbols where a non-classic signal was detected but could not be confirmed, for example `stock_like_symbol_pattern_detected_unverified`.

It does **not** mean:

- guaranteed high quality,
- liquid,
- executable,
- non-meme,
- safe to trade.

`classic_crypto` remains candidate-capable.

### `stable_or_cash_proxy`

Meaning:

- Asset whose base is intended to track a fiat/cash-like value or stablecoin peg, for example `TUSD`, `USDP`, `FDUSD`, `USD1`, `USDM`, or equivalent explicitly configured symbols.

It does **not** mean:

- the symbol is invalid on MEXC,
- the symbol should necessarily be removed from all raw diagnostics,
- the scanner failed.

`stable_or_cash_proxy` is candidate-excluded in T23.

### `leveraged_or_margin_token`

Meaning:

- Leveraged, inverse, margin-like, bull/bear, or multiplier product whose price behavior is structurally different from a normal spot asset.

Examples include configurable patterns such as:

```text
3K*
3L*
3S*
*BULL*
*BEAR*
```

Pattern matching must apply to the base symbol, not the quote suffix.

`leveraged_or_margin_token` is candidate-excluded in T23.

### `tokenized_stock_or_etf`

Meaning:

- Tokenized stock, ETF, equity proxy, or similar listing, usually identified by an exact override or a conservative known-equity ticker rule.

Examples may include explicitly configured symbols such as:

```text
NVDAONUSDT
GOOGLONUSDT
AMDONUSDT
PBRONUSDT
```

Do not classify ambiguous `*ONUSDT` symbols as high-confidence stock tokens unless the prefix is known or explicitly configured.

`tokenized_stock_or_etf` remains candidate-capable in T23.

### `commodity_or_index_proxy`

Meaning:

- Commodity, index, or macro proxy token, for example explicitly configured symbols such as `OIL(USOON)USDT`.

Do not guess. Symbols such as `COCAUSDT` must not be classified as commodity unless an explicit override or reliable rule exists. Otherwise classify as `unknown` with low confidence.

`commodity_or_index_proxy` remains candidate-capable in T23.

### `wrapped_or_synthetic_btc`

Meaning:

- Wrapped, bridged, synthetic, or derivative BTC-like proxy, for example an explicitly configured symbol such as `BTCBAMUSDT`.

It remains candidate-capable in T23.

### `unknown`

Meaning:

- A non-classic or suspicious signal was detected, but classification evidence is insufficient to assign a specific category.

Examples:

- stock-like naming pattern detected but prefix is not in a known-equity/ETF override list,
- commodity-like ticker suspected but not explicitly configured,
- ambiguous wrapper/synthetic signal without a deterministic rule.

`unknown` is **not** the default for every unmatched ordinary symbol. For unmatched symbols with no specific non-classic/suspicious signal, use low-confidence `classic_crypto` with reason `no_non_classic_rule_matched`.

`unknown` does **not** mean invalid. It must not block or degrade pipeline throughput.

`unknown` remains candidate-capable in T23.

---

## Classification output fields

Classification must produce, per symbol:

```text
universe_category
universe_category_confidence
universe_category_reason
candidate_excluded
candidate_exclusion_reason
```

Allowed `universe_category_confidence` values:

```text
high
medium
low
```

Allowed `candidate_excluded` values:

```text
true
false
```

`candidate_exclusion_reason` is nullable.

Null semantics:

```text
candidate_exclusion_reason = null
```

means the symbol is not candidate-excluded.

Do not use truthiness for presence checks. `false`, `0`, `0.0`, and empty strings must not be silently converted into missing values where the field semantics differ.

---

## Candidate exclusion rule

Only these categories are candidate-excluded in T23:

```text
stable_or_cash_proxy
leveraged_or_margin_token
```

All other categories remain candidate-capable:

```text
classic_crypto
tokenized_stock_or_etf
commodity_or_index_proxy
wrapped_or_synthetic_btc
unknown
```

Candidate-excluded means:

- do not include in candidate-facing views,
- include in excluded-candidate summary,
- retain raw bucket information unchanged,
- retain diagnostics classification information.

Candidate-excluded does **not** mean:

- remove from raw report fields,
- change Decision Bucket assignment,
- change priority score,
- change Execution grading,
- change Evaluation Replay semantics.

---

## Classification logic

Implement deterministic classification in a dedicated module, for example:

```text
scanner/universe/classification.py
```

or an equivalent existing universe/reporting module if repo structure indicates a better fit. Do not duplicate parallel classification logic in multiple modules.

### Required precedence

Classification must use this precedence order:

1. Exact symbol override map.
2. Stable/cash exact base-symbol list.
3. Leveraged/margin base-symbol pattern list.
4. Tokenized stock/ETF exact overrides or conservative known-prefix rule.
5. Commodity/index exact overrides.
6. Wrapped/synthetic BTC exact overrides.
7. Fallback.

Exact overrides must win over pattern rules.

### Exact override map

The implementation must support a deterministic exact override map keyed by full symbol.

Example shape:

```yaml
symbol_classification_overrides:
  TUSDUSDT:
    category: stable_or_cash_proxy
    confidence: high
    reason: exact_override_stable
  NVDAONUSDT:
    category: tokenized_stock_or_etf
    confidence: high
    reason: exact_override_tokenized_stock
  OIL(USOON)USDT:
    category: commodity_or_index_proxy
    confidence: high
    reason: exact_override_commodity_proxy
```

The exact storage location may follow existing config conventions, but do not create ad-hoc scattered constants if a central config/module pattern exists.

### Stable/cash exact list

Classify by base symbol extracted from the trading pair.

Initial exact base examples:

```text
TUSD
USDP
FDUSD
USD1
USDM
```

If the implementation adds additional stable/cash entries, they must be explicitly listed and tested.

### Leveraged/margin pattern list

Pattern matching must operate on the base symbol, not the full quote-pair string unless the helper correctly strips quote suffixes first.

Initial configurable patterns may include:

```text
^3K
^3L
^3S
BULL
BEAR
```

Do not over-generalize patterns that could hit normal symbols accidentally.

### Tokenized stock/ETF rule

Do not classify all `*ONUSDT` symbols blindly as `tokenized_stock_or_etf` with high confidence.

Allowed approaches:

- exact override map, or
- known-equity-prefix list + `ONUSDT` suffix heuristic.

If `*ONUSDT` matches a stock-like pattern but the prefix is not known, classify as:

```text
universe_category = unknown
universe_category_confidence = low
universe_category_reason = stock_like_symbol_pattern_detected_unverified
candidate_excluded = false
```

### Commodity/index rule

Use exact overrides only in T23 unless a deterministic existing data source exists in the repo.

Do not guess commodity classification from a ticker alone.

### Fallback and residual default

Fallback must distinguish ordinary unmatched symbols from ambiguous non-classic/suspicious symbols.

If no specific non-classic rule matched and no stock-like, commodity-like, stable/cash, leveraged/margin, or wrapped/synthetic-BTC signal was detected, classify as low-confidence `classic_crypto`:

```text
universe_category = classic_crypto
universe_category_confidence = low
universe_category_reason = no_non_classic_rule_matched
candidate_excluded = false
candidate_exclusion_reason = null
```

Reserve `unknown` for symbols where a non-classic or suspicious signal was detected but could not be confirmed:

```text
universe_category = unknown
universe_category_confidence = low
universe_category_reason = stock_like_symbol_pattern_detected_unverified
candidate_excluded = false
candidate_exclusion_reason = null
```

Do not silently classify suspicious patterns as `classic_crypto`. Do not candidate-exclude `unknown`.

---

## Report requirements

### Existing raw fields remain unchanged

Existing raw bucket fields in `report.json` must remain unchanged and continue to represent the original Decision Bucket outputs.

Do not remove stable/leveraged symbols from raw buckets.

### New additive report blocks

Add new blocks under stable dedicated keys. Recommended minimum:

```json
{
  "universe_classification": {
    "category_counts_total": {},
    "category_counts_by_bucket": {},
    "candidate_exclusion_counts_by_bucket": {},
    "candidate_excluded_symbol_count": 0
  },
  "candidate_segments": {
    "tradable_buckets": {},
    "excluded_candidate_buckets": {},
    "segmented_tradable_buckets": {}
  }
}
```

Exact nesting may vary if repo conventions require it, but the following semantics are mandatory:

- raw buckets remain unchanged,
- tradable/candidate-facing buckets exclude only `stable_or_cash_proxy` and `leveraged_or_margin_token`,
- excluded candidate buckets contain excluded raw candidates grouped by exclusion category or reason,
- segmented tradable buckets group remaining candidates by `universe_category`,
- category counts are available overall and by raw bucket.

### Candidate item fields

Candidate items in new segmented/tradable views must include, at minimum:

```text
symbol
decision_bucket
priority_score
execution_status_raw
execution_pass
universe_category
universe_category_confidence
universe_category_reason
candidate_excluded
candidate_exclusion_reason
```

If an execution field is not available for a symbol, preserve existing null/missing semantics. Do not convert not-evaluated Execution into `fail`.

### Count invariants

For each active bucket:

```text
raw_bucket_count = tradable_bucket_count + excluded_candidate_bucket_count
```

For each active bucket:

```text
tradable_bucket_count = sum(segmented_tradable_bucket_counts_by_category)
```

Active buckets for these invariants:

```text
confirmed_candidates
early_candidates
watchlist
late_monitor
```

`discarded` may have classification counts but does not need a candidate-facing segmented view unless existing report conventions make it natural.

---

## Diagnostics requirements

Add a new diagnostics block per symbol:

```json
{
  "universe": {
    "universe_category": "unknown",
    "universe_category_confidence": "low",
    "universe_category_reason": "no_classification_rule_matched",
    "candidate_excluded": false,
    "candidate_exclusion_reason": null
  }
}
```

This is a conscious additive diagnostics schema extension.

Requirements:

- Preserve all existing T21/T21.1 diagnostics blocks and invariants.
- Do not add informal top-level mirrors for universe classification unless an existing schema pattern requires it.
- The `universe` block must be present for every Daily diagnostics record.
- Intraday diagnostics may include the block if the classification is available without Daily-only recomputation. Do not add Daily-only recompute to Intraday just to populate this block.
- JSON serialization must be explicit field-by-field. Do not use uncontrolled `dataclasses.asdict()` for diagnostics serialization.
- Use `is not None` checks where presence matters; never use `value or default` for semantic fields.

---

## Shadow-Live report expectations

After T23, Shadow-Live reports should make it possible to answer:

- how many raw confirmed candidates existed,
- how many were candidate-excluded as stable/leveraged,
- how many tradable confirmed candidates remain,
- which tradable confirmed candidates are classic crypto,
- which tradable confirmed candidates are tokenized stocks/ETFs,
- which tradable confirmed candidates are commodity/index proxies,
- which tradable confirmed candidates are wrapped/synthetic BTC proxies,
- which tradable confirmed candidates are unknown.

This must be visible without manually inspecting every symbol diagnostics row.

---

## Documentation requirements

Update canonical docs where appropriate, likely:

```text
docs/canonical/REPORTS.md
docs/canonical/feature_enhancements.md
```

Document:

- category set,
- category semantics,
- candidate exclusion semantics,
- raw vs tradable/segmented report distinction,
- backward compatibility with existing raw report fields,
- deferred meme/community-token classification.

Do not create a second competing report authority. If an existing report schema doc exists, extend it consistently.

---

## Scope

### In scope

- Deterministic universe classification module/helper.
- Exact override map support.
- Stable/cash proxy exact list.
- Leveraged/margin token pattern list.
- Conservative tokenized stock/ETF classification using exact overrides or known-prefix list.
- Commodity/index exact overrides.
- Wrapped/synthetic BTC exact overrides.
- Ordinary unmatched symbols fall back to low-confidence `classic_crypto` with reason `no_non_classic_rule_matched`.
- Suspicious but unverified symbols fall to low-confidence `unknown` and are not candidate-excluded.
- New additive diagnostics `universe` block.
- New additive report blocks for classification and candidate segmentation.
- Candidate-facing exclusion only for `stable_or_cash_proxy` and `leveraged_or_margin_token`.
- Tests for classification, diagnostics serialization, report segmentation, and count invariants.
- Documentation updates.

### Out of scope

- Eligibility hard filtering.
- T3 Eligibility threshold changes.
- Universe Discovery changes.
- OHLCV fetch gating changes.
- Phase Interpreter changes.
- State Machine changes.
- Decision Bucket assignment changes.
- `DecisionBucket` enum changes.
- Priority score changes.
- Execution grading or threshold changes.
- Evaluation metric changes.
- Intraday carry-forward context.
- Meme/community-token classification.
- ML-based taxonomy.
- External taxonomy integration unless already available in current repo and deterministic.
- Hard-excluding tokenized stocks/ETFs.
- Hard-excluding commodities/index proxies.
- Hard-excluding wrapped/synthetic BTC proxies.
- Hard-excluding unknown.

---

## Tests

Add focused tests. Suggested areas:

### Classification helper tests

- Exact override wins before pattern.
- Stable/cash exact base list classifies `TUSDUSDT`, `USDPUSDT`, `FDUSDUSDT`, `USD1USDT`, `USDMUSDT` as `stable_or_cash_proxy` and candidate-excluded.
- Leveraged/margin pattern classifies representative `3K*`, `3L*`, `3S*`, `*BULL*`, `*BEAR*` base symbols as `leveraged_or_margin_token` and candidate-excluded.
- Tokenized stock exact override classifies e.g. `NVDAONUSDT` without candidate exclusion.
- Unverified `*ONUSDT` pattern without known prefix does not become high-confidence tokenized stock; it falls to `unknown` or a low-confidence unverified reason, not candidate-excluded.
- Commodity exact override classifies `OIL(USOON)USDT` without candidate exclusion.
- Ambiguous `COCAUSDT` is not classified as commodity unless explicitly overridden.
- `classic_crypto` residual default is low-confidence and not candidate-excluded.
- `unknown` is reserved for suspicious/unverified symbols, low-confidence, and not candidate-excluded.

### Report segmentation tests

- Raw bucket counts remain unchanged after segmentation.
- Stable/leveraged symbols remain present in raw buckets if they were assigned by Decision, but are absent from tradable/candidate-facing buckets.
- Tokenized stock/ETF, commodity/index proxy, wrapped/synthetic BTC, classic crypto, and unknown remain in tradable/candidate-facing buckets.
- For each active bucket:

  ```text
  raw = tradable + excluded
  ```

- For each active bucket:

  ```text
  tradable = sum(segmented_tradable_by_category)
  ```

- Candidate items in segmented views contain classification fields.
- Existing T13 raw report fields remain readable by existing tests.

### Diagnostics tests

- Every Daily diagnostics record includes `universe` block.
- `candidate_exclusion_reason=null` is preserved for non-excluded symbols.
- `candidate_excluded=false` is preserved and not treated as missing.
- Existing T21/T21.1 diagnostics invariants still pass.

### Regression tests

- Existing output/report tests remain green.
- Existing diagnostics serialization tests remain green.
- Existing evaluation replay tests remain green.
- Existing Shadow-Live workflow/orchestrator tests remain green.

Required final command:

```bash
pytest -q
```

---

## Acceptance criteria

- New deterministic universe classification exists in one canonical implementation location.
- Category set is exactly:
  - `classic_crypto`
  - `stable_or_cash_proxy`
  - `leveraged_or_margin_token`
  - `tokenized_stock_or_etf`
  - `commodity_or_index_proxy`
  - `wrapped_or_synthetic_btc`
  - `unknown`
- No `meme_or_community_token` category is introduced in T23.
- Stable/cash proxies are candidate-excluded.
- Leveraged/margin tokens are candidate-excluded.
- Tokenized stocks/ETFs remain candidate-capable.
- Commodity/index proxies remain candidate-capable.
- Wrapped/synthetic BTC proxies remain candidate-capable.
- Unknown remains candidate-capable.
- Raw bucket fields and counts remain backward-compatible and unchanged.
- Additive report blocks expose classification counts and segmented candidate views.
- Per-bucket count invariants hold:
  - `raw = tradable + excluded`
  - `tradable = sum(segmented tradable categories)`
- Daily diagnostics include a `universe` block for every symbol.
- T21/T21.1 diagnostics invariants remain valid.
- No Eligibility threshold changes are introduced.
- No Phase/State/Decision/Execution logic changes are introduced.
- No Evaluation metric changes are introduced.
- Documentation records raw vs segmented report semantics.
- Deferred meme/community-token classification is recorded in feature enhancements.
- Full test suite passes.

---

## Anti-requirements

Codex must not:

- hard-filter tokenized stocks/ETFs out of the pipeline,
- hard-filter commodity/index proxies out of the pipeline,
- hard-filter wrapped/synthetic BTC proxies out of the pipeline,
- hard-filter unknown assets,
- remove stable/leveraged symbols from raw bucket outputs,
- change existing raw bucket names,
- change existing raw bucket count semantics,
- modify `DecisionBucket` enum values,
- change priority scoring,
- change Execution grading,
- change Eligibility thresholds,
- add OHLCV fetch gating,
- introduce Intraday carry-forward context,
- introduce meme/community-token heuristics,
- guess ambiguous commodity or stock classifications without an explicit rule,
- use uncontrolled `dataclasses.asdict()` for diagnostics serialization,
- use truthiness where `False`, `0`, `0.0`, or `null` semantics matter,
- create a second competing report schema authority,
- break existing T13/T21/T22 tests.

---

## Suggested implementation sequence

1. Inspect current report builder/schema and diagnostics serialization code.
2. Identify the existing T13 raw report fields and tests that must remain unchanged.
3. Implement a single deterministic universe classification helper/module.
4. Add configuration/static maps for exact overrides and rule lists using existing config conventions where possible.
5. Add unit tests for classification precedence and fallback behavior.
6. Add additive diagnostics `universe` serialization.
7. Add report segmentation blocks without modifying raw bucket fields.
8. Add report count invariant tests.
9. Update canonical docs and feature enhancements.
10. Run targeted output/diagnostics/evaluation/shadow-live tests.
11. Run full `pytest -q`.
12. In the PR description, explicitly state:
    - category set,
    - candidate-excluded categories,
    - candidate-capable non-classic categories,
    - backward-compatibility approach for T13 raw report fields,
    - diagnostics schema addition,
    - tests run.

---

## Definition of Done

- Implementation is complete within stated scope.
- Existing raw report consumers remain backward-compatible.
- Candidate-facing reports exclude only stable/cash proxies and leveraged/margin tokens.
- Tokenized stocks, commodities, wrapped/synthetic BTC, classic crypto, and unknown assets remain visible and candidate-capable.
- Diagnostics and reports expose classification reason and confidence.
- Full test suite passes.
- Ticket is archived according to repo workflow.
