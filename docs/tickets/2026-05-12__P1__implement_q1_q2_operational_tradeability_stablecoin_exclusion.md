# Implement Q1/Q2 Operational Tradeability and Stablecoin/Cash-Proxy Exclusion

**Ticket ID:** T_Q1_Q2_OPERATIONAL_TRADEABILITY  
**Priority:** P1  
**Status:** Draft for implementation  
**Date:** 2026-05-12  
**Target schema:** `ir1.5`  
**Expected PR size:** Small/medium, one PR only  
**Primary owner:** Codex implementation  
**Review focus:** Diagnostics semantics, report counts, bucket/index behavior, Q1/Q2 documentation updates

---

## 1. Authoritative context

This ticket implements the locked Q1/Q2 decision:

- Q2: hard-exclude stablecoin/cash-proxy classes in the Universe-Classification-to-Decision path while preserving diagnostics visibility.
- Q1: keep `is_tradeable_candidate` semantics unchanged and add `is_operational_trade_candidate` as the final operational tradeability label.

Authoritative references for this ticket:

1. The v2.1 section documents and `independence_release_gesamtkonzept_final.md`
2. `docs/canonical/open_questions.md`, specifically Q1 and Q2
3. `docs/canonical/feature_enhancements.md`, specifically the operational tradeability field enhancement
4. `docs/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md` if already added, or the attached Q1/Q2 Decision Note if not yet committed
5. Existing repo implementation and current schema reality (`ir1.4` before this ticket)

If the current authoritative reference set, repo canonical documents, and existing code collide, the v2.1 reference set plus the locked Q1/Q2 decision wins. Existing repo documents remain valid only where they do not conflict with this ticket's explicit Q1/Q2 decision.

---

## 2. Problem statement

Two related issues must be resolved before T30 Forward-Return Evaluation can consume row-level diagnostics safely.

### Q1 problem

`is_tradeable_candidate` currently means bucket-/execution-scoped tradeability. It can remain `true` even when `candidate_excluded = true`, for example stablecoin/cash-proxy cases such as `USDPUSDT` in earlier Shadow-Live runs.

That creates a row-level false positive for consumers that treat `is_tradeable_candidate` as the final operative label.

### Q2 problem

Stablecoin/cash-proxy symbols can currently progress through enough of the pipeline to appear in actionable candidate contexts. `candidate_excluded = true` may be emitted, but there is no hard gate before final Decision/Bucket promotion.

This ticket resolves both issues without breaking the existing `is_tradeable_candidate` contract.

---

## 3. Decisions implemented by this ticket

### 3.1 Q2 decision — Universe-Classification-layer gate

Stablecoin/cash-proxy classes are excluded in the Universe-Classification-to-Decision path.

Categories covered by this ticket:

```text
stable_or_cash_proxy
fiat_proxy
wrapped_cash
```

For these categories:

```text
candidate_excluded = true
```

The symbol must remain visible in diagnostics, but must not appear in final actionable candidate outputs.

### 3.2 Q1 decision — New operational field

Do not redefine `is_tradeable_candidate`.

Add a new top-level boolean diagnostics field:

```text
is_operational_trade_candidate
```

Formula:

```python
is_operational_trade_candidate = (
    is_tradeable_candidate is True
    and candidate_excluded is not True
)
```

Semantic meaning:

```text
Final row-level operative tradeability label for analysis, T30, and execution-adjacent consumers.
```

---

## 4. Scope

### In scope

1. Enforce the stablecoin/cash-proxy exclusion gate after Universe Classification and before final actionable Decision/Bucket output.
2. Add top-level `is_operational_trade_candidate` to every `symbol_diagnostics.jsonl.gz` record.
3. Bump schema from `ir1.4` to `ir1.5` according to existing schema/versioning conventions.
4. Add report summary counts for operational tradeability alongside existing tradeability counts.
5. Preserve diagnostics visibility for excluded symbols.
6. Ensure final report candidate lists and candidate-oriented latest files do not include `candidate_excluded = true` symbols.
7. Keep T_EL2 Rule 3 unchanged: it checks top-level `candidate_excluded` directly.
8. Verify T_EL2 report segments remain correct, especially `good_location_but_not_tradeable`.
9. Update canonical/open-question and enhancement documentation.
10. Add tests for diagnostics, reports, Q1/Q2 semantics, and regression cases.

### Out of scope

Do not implement any of the following in this ticket:

- Do not change `is_tradeable_candidate` semantics or formula.
- Do not add Eligibility-layer stablecoin filtering.
- Do not change Override Map entries.
- Do not change State Machine logic.
- Do not change Entry Pattern logic.
- Do not change T_EL2 thresholds.
- Do not change T_EL2 override rule ordering.
- Do not resolve Q3 or any other open question.
- Do not implement T30.
- Do not add Forward-Return Evaluation.
- Do not commit diagnostics artifacts, Parquet, ZIP files, or large data.

---

## 5. Required behavior

## 5.1 Stablecoin/cash-proxy gate

When a symbol has:

```text
universe_category in {stable_or_cash_proxy, fiat_proxy, wrapped_cash}
```

then the pipeline must set:

```text
candidate_excluded = true
```

and the symbol must not be promoted into final actionable output buckets/lists:

```text
confirmed_candidates
early_candidates
watchlist
```

It may still appear in:

```text
discarded
candidate_excluded / excluded diagnostics segments
full symbol diagnostics
```

Use existing repo terms and structures where available.

Important distinction:

- Final report / candidate lists: `candidate_excluded = true` symbols must not appear in actionable candidate lists.
- Diagnostics: the symbol must remain visible with `candidate_excluded = true`, `universe_category`, and relevant exclusion reason/context.
- If the pipeline already computes pre-exclusion bucket context internally, that diagnostic context may be preserved, but final candidate lists must not include the symbol.

Do not implement retroactive historical migration. This applies to new runs after the implementation.

## 5.2 `candidate_excluded` path

Current diagnostics use top-level:

```python
rec["candidate_excluded"]
```

Do not read this from:

```python
rec["universe"]["candidate_excluded"]
```

unless the existing code has a compatibility reader that explicitly handles older schema versions. For new `ir1.5` output, the authoritative diagnostics field is top-level `candidate_excluded`.

## 5.3 New field: `is_operational_trade_candidate`

Emit for every symbol diagnostics record:

```text
is_operational_trade_candidate
```

Placement:

```text
top-level field in symbol_diagnostics.jsonl.gz
```

Type:

```text
bool, not nullable
```

Allowed values:

```text
true
false
```

Formula:

```python
is_operational_trade_candidate = (
    is_tradeable_candidate is True
    and candidate_excluded is not True
)
```

Do not use `bool(is_tradeable_candidate)` or `bool(candidate_excluded)` if either field can be nullable or non-bool. Use explicit identity-style checks.

Semantics:

- `true` means the symbol is final-operatively tradeable for row-level consumers.
- `false` means the symbol is not final-operatively tradeable, either because it is not bucket/execution tradeable or because it is candidate-excluded.

`is_operational_trade_candidate` must be the field T30 and future operative consumers use.

## 5.4 Preserve `is_tradeable_candidate`

Do not change existing `is_tradeable_candidate` semantics.

It remains bucket-/execution-scoped.

Report both fields where relevant:

```text
is_tradeable_candidate
is_operational_trade_candidate
```

This preserves auditability and avoids a breaking semantic change.

---

## 6. Report and candidate-list behavior

## 6.1 Candidate lists

Final report candidate lists must not include `candidate_excluded = true` symbols.

This applies at minimum to:

```text
confirmed_candidates
early_candidates
watchlist
latest_confirmed_candidates.json
latest_watchlist.json
```

Use the existing report/index writer semantics and preserve the previous no-op/diagnostics-only intraday fixes.

Do not reintroduce any behavior where no-op or diagnostics-only intraday runs clear candidate-oriented latest files.

## 6.2 Summary counts

Do not rename or reinterpret existing `is_tradeable_candidate`-based counts.

Add operational counts alongside existing counts where relevant.

Prefer existing naming conventions. Check whether the current report uses *_count suffixes in counts_by_bucket or *_symbol_count in candidate_segments before choosing names, and be consistent with whichever pattern already exists. If no convention exists, use names similar to:

```text
operational_trade_candidate_count
confirmed_operational_trade_candidate_count
early_operational_trade_candidate_count
```

Required principle:

```text
Existing tradeable counts remain audit fields.
New operational counts represent final consumer-safe tradeability.
```

If the report currently has a `candidate_segments` or equivalent object, add operational counts there if that is the established report style.

## 6.3 Candidate-excluded reporting

If an existing count such as:

```text
candidate_excluded_symbol_count
```

is defined in report contracts or open questions, populate it according to the existing contract where feasible.

If implementing that count would expand scope materially, add a minimal count in the closest existing report summary area and document the exact field. Do not silently leave candidate-excluded symbols uncounted.

---

## 7. T_EL2 interactions

## 7.1 Rule 3 remains unchanged

Do not change T_EL2 override ordering or logic.

T_EL2 Rule 3 remains:

```text
candidate_excluded == True -> entry_action_hint = monitor_only
```

The rule checks top-level `candidate_excluded` directly.

Do not replace it with:

```text
NOT is_operational_trade_candidate
```

Reason:

- Rule 3 represents Universe Exclusion.
- Rule 4 represents execution/bucket insufficiency via `is_tradeable_candidate != True`.
- The distinction is analytically useful in `entry_location_reason_codes`.

The known edge case remains acceptable in this ticket:

```text
candidate_excluded = true
entry_location_status = chased_entry
-> Rule 2 may produce avoid_chasing before Rule 3 monitor_only
```

Do not reorder rules in this ticket.

## 7.2 `good_location_but_not_tradeable` segment regression check

T_EL2's `good_location_but_not_tradeable` segment includes a condition equivalent to:

```text
candidate_excluded != True
```

After the Q2 gate, stablecoin/cash-proxy symbols should no longer appear in actionable buckets, so this condition should remain functionally stable.

Add or update a regression test verifying that after this ticket:

1. `good_location_but_not_tradeable` is still populated for non-excluded symbols with good entry location but no operational tradeability.
2. `candidate_excluded = true` symbols do not enter `good_location_but_not_tradeable`.
3. The Q2 gate does not accidentally empty or corrupt the T_EL2 segment.

This is a required test case.

---

## 8. Schema versioning

Bump schema version:

```text
ir1.4 -> ir1.5
```

Update all required schema/version references according to existing repo conventions.

At minimum, check and update if present:

```text
docs/SCHEMA_CHANGES.md
report schema docs
diagnostics schema docs
golden fixtures / schema fixtures
any tests that assert schema_version
```

Schema change reason:

```text
Add top-level boolean is_operational_trade_candidate and enforce Q1/Q2 operational tradeability semantics.
```

Do not bump schema multiple times in this ticket.

---

## 9. Documentation updates

## 9.1 `open_questions.md`

Mark Q1 and Q2 as resolved.

Do not delete their history. Preserve the context and add resolution notes.

Suggested resolution for Q1:

```text
Resolved in <ticket/PR>: is_tradeable_candidate remains bucket-/execution-scoped. New top-level field is_operational_trade_candidate is the final operational tradeability label.
```

Suggested resolution for Q2:

```text
Resolved in <ticket/PR>: stable_or_cash_proxy, fiat_proxy, and wrapped_cash are hard-excluded in the Universe-Classification-to-Decision path while remaining visible in diagnostics.
```

## 9.2 `feature_enhancements.md`

Mark the operational tradeability field enhancement as implemented/resolved.

Preserve its historical context.

## 9.3 Q1/Q2 Decision Note

If not already committed, add the decision note at:

```text
docs/decisions/Q1_Q2_operational_tradeability_and_stablecoin_exclusion.md
```

If the repo uses another established decision-record path, use that path and keep the filename clear.

Do not place this decision note under `reports/aux`, because it is an architecture decision, not a run-derived calibration artifact.

## 9.4 T_EL2 docs

Update T_EL2-related docs only as needed to clarify:

```text
T_EL2 Rule 3 checks top-level candidate_excluded directly.
It does not check is_operational_trade_candidate.
```

Do not change T_EL2 thresholds or mapping.

## 9.5 Consumer docs

Update any relevant report/diagnostics docs to state:

```text
After ir1.5, T30 and operative consumers must use is_operational_trade_candidate instead of is_tradeable_candidate as the final operational label.
```

---

## 10. Tests required

Add or update tests covering the following.

### 10.1 Operational field formula

Given:

```python
is_tradeable_candidate = True
candidate_excluded = False
```

Expected:

```python
is_operational_trade_candidate is True
```

Given:

```python
is_tradeable_candidate = True
candidate_excluded = True
```

Expected:

```python
is_operational_trade_candidate is False
```

Given:

```python
is_tradeable_candidate = False
candidate_excluded = False
```

Expected:

```python
is_operational_trade_candidate is False
```

Given:

```python
is_tradeable_candidate = None
candidate_excluded = False
```

Expected:

```python
is_operational_trade_candidate is False
```

### 10.2 Top-level diagnostics field

Verify every diagnostics record emits:

```text
is_operational_trade_candidate
```

as a top-level boolean.

Verify no nested alias is required or introduced.

### 10.3 Stablecoin/cash-proxy gate

For a symbol with:

```text
universe_category = stable_or_cash_proxy
```

Expected:

```text
candidate_excluded = true
is_operational_trade_candidate = false
symbol does not appear in final confirmed_candidates / early_candidates / watchlist lists
symbol remains present in diagnostics
```

Repeat for:

```text
fiat_proxy
wrapped_cash
```

### 10.4 Preserve non-stablecoin behavior

For a non-excluded symbol that is tradeable:

```text
candidate_excluded = false
is_tradeable_candidate = true
```

Expected:

```text
is_operational_trade_candidate = true
```

and existing bucket behavior remains unchanged.

### 10.5 Report summary counts

Verify operational tradeability counts are added and use `is_operational_trade_candidate`.

Verify existing `is_tradeable_candidate`-based audit counts are not renamed or silently reinterpreted.

### 10.6 Candidate lists and latest files

Verify `candidate_excluded = true` symbols do not appear in:

```text
confirmed_candidates
early_candidates
watchlist
latest_confirmed_candidates.json
latest_watchlist.json
```

Do not change the previous no-op/diagnostics-only intraday behavior.

### 10.7 T_EL2 unchanged

Verify T_EL2 Rule 3 still checks `candidate_excluded` directly.

Verify no T_EL2 thresholds or override ordering changed.

Verify the known edge case remains deterministic:

```text
candidate_excluded = true
entry_location_status = chased_entry
-> avoid_chasing may still win via Rule 2
```

### 10.8 T_EL2 segment regression

Verify:

```text
good_location_but_not_tradeable
```

still includes non-excluded symbols with good entry location but no operational tradeability.

Verify it excludes:

```text
candidate_excluded = true
```

symbols.

### 10.9 Schema version

Verify schema version is now:

```text
ir1.5
```

for new diagnostics/reports.

### 10.10 Documentation tests/checks

Run existing documentation/schema checks if available.

---

## 11. Implementation guidance

## 11.1 Suggested order

1. Locate Universe Classification output and current `candidate_excluded` assignment.
2. Add the stable/cash category gate before final Decision/Bucket promotion.
3. Add `is_operational_trade_candidate` computation in diagnostics/report model construction.
4. Add report summary operational counts.
5. Ensure candidate lists exclude `candidate_excluded = true` symbols.
6. Verify T_EL2 segments still work.
7. Bump schema to `ir1.5`.
8. Update docs.
9. Add tests.
10. Run the test suite.

## 11.2 Existing helpers

Reuse existing helpers and report-building structures where possible.

Do not introduce a second universe-classification truth.

Do not introduce a second candidate-exclusion flag.

Do not duplicate report filtering logic if there is already a central candidate-list builder.

---

## 12. Numeric / nullability / bool robustness

`candidate_excluded` may be absent or nullable in old fixtures. For `ir1.5` output, it should be present top-level.

Operational formula must treat only explicit `True` as true:

```python
is_tradeable_candidate is True
candidate_excluded is not True
```

Do not use truthy/falsy coercion.

Examples:

```python
candidate_excluded = None -> treated as not explicitly excluded
is_tradeable_candidate = None -> not operationally tradeable
```

`is_operational_trade_candidate` itself is not nullable and must always be emitted as `true` or `false`.

---

## 13. Acceptance criteria

1. Schema version for new runs is `ir1.5`.
2. Every diagnostics record emits top-level boolean `is_operational_trade_candidate`.
3. `is_tradeable_candidate` semantics are unchanged.
4. `is_operational_trade_candidate` uses the exact formula `is_tradeable_candidate is True AND candidate_excluded is not True`.
5. Stable/cash categories set `candidate_excluded = true`.
6. Stable/cash categories do not appear in final actionable candidate lists.
7. Excluded symbols remain visible in diagnostics.
8. Report summaries include operational tradeability counts alongside existing tradeability/audit counts.
9. Existing tradeability counts are not renamed or silently reinterpreted.
10. T_EL2 Rule 3 still checks top-level `candidate_excluded` directly.
11. T_EL2 ordering and thresholds are unchanged.
12. `good_location_but_not_tradeable` remains correctly populated for non-excluded non-operational symbols.
13. `candidate_excluded = true` symbols are not counted in `good_location_but_not_tradeable`.
14. `open_questions.md` marks Q1/Q2 resolved with decision references.
15. `feature_enhancements.md` marks the operational tradeability field as implemented/resolved.
16. Q1/Q2 Decision Note is committed under a decision-doc path if not already present.
17. Existing no-op/diagnostics-only intraday latest-index semantics remain intact.
18. Required tests pass.
19. Existing test suite passes.

---

## 14. Definition of Done

This ticket is complete when:

- Code implements Q1/Q2 behavior.
- Reports and diagnostics serialize `ir1.5` correctly.
- Documentation reflects that Q1/Q2 are resolved.
- T30 has a clear field to consume: `is_operational_trade_candidate`.
- Stablecoin/cash-proxy symbols are no longer actionable candidates but remain diagnostically visible.
- T_EL2 behavior remains unchanged except for downstream consistency with the new operational field.
- Tests prove the stable/cash gate, operational field, report counts, candidate lists, and T_EL2 segment regression.

---

## 15. Commands to run

Run the relevant targeted tests and then the broader suite.

At minimum, run:

```bash
python -m pytest -q
```

If the repo has targeted report/diagnostics/schema tests, run those explicitly as well and report the exact commands and results.

---

## 16. Post-implementation handoff requested from Codex

After implementation, report:

1. Files changed.
2. Exact schema version behavior.
3. Where `is_operational_trade_candidate` is computed.
4. Where the stable/cash gate is enforced.
5. Which report fields were added.
6. How candidate lists exclude `candidate_excluded = true`.
7. Confirmation that T_EL2 Rule 3 still checks `candidate_excluded` directly.
8. Confirmation that `good_location_but_not_tradeable` was regression-tested.
9. Test commands and results.
10. Any behavior intentionally left unchanged.
