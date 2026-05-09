# T_EL1b: Add 4h Entry-Location Feature Fields to Symbol Diagnostics

## Metadata

- **Ticket ID:** T_EL1b
- **Title:** Add 4h Entry-Location Feature Fields to `symbol_diagnostics.jsonl.gz`
- **Priority:** P1
- **Depends on:** T5 (raw features — fields computed here), T21 (diagnostics serialization), T27 (diagnostics schema ir1.1)
- **Downstream:** T_EL1 Step B (analysis), T_EL2 (Entry-Location Layer implementation)
- **Authoritative references:**
  - `2026-04-18__P0__raw_features_and_helper_metrics_final.md` (T5 — canonical source of all fields added here)
  - `2026-04-27__P0__diagnostics_serialization_evaluation_ready_ticket21_v4.md` (T21 — diagnostics output contract)
  - `2026-05-04__P0__add_execution_depth_ratio_diagnostics_T27_v3.md` (T27 — previous diagnostics schema version / enrichment reference)
  - `feature_request_entry_location_action_hint.md` (Entry-Location feature concept)

> This ticket is a diagnostics-only enrichment. No scanner logic, scoring, ranking, or trading behavior is modified.

---

## Context

The Entry-Location Feature Request identified `close_vs_ema20_4h_pct`, `bars_above_ema20_4h`, and related 4h raw fields as primary inputs to the planned Entry-Location Layer (T_EL2). T_EL1 Step A confirmed that none of these fields are currently present in `symbol_diagnostics.jsonl.gz`, even though all are already computed internally by T5 as part of the `FeatureBundle`.

Without these fields in the diagnostics output:
- T_EL1 Step B (empirical threshold calibration) cannot run.
- T_EL2 (Entry-Location Layer) cannot read the required inputs from the diagnostic pipeline.

This ticket exposes the already-computed T5 fields in the diagnostics output. No new computation is introduced.

---

## Fields to add

All six fields are computed by T5 and available in the `FeatureBundle`. Codex must verify the exact internal attribute names against the current T5 implementation before writing the serialization code. The canonical names from the T5 ticket are:

| Field name | T5 source | Type | Null condition |
|---|---|---|---|
| `close_vs_ema20_4h_pct` | `FeatureBundle.close_vs_ema20_4h_pct` | `float \| None` | `data_4h_available == False` or EMA not computable |
| `bars_above_ema20_4h` | `FeatureBundle.bars_above_ema20_4h` | `int \| None` | same |
| `dist_to_ema20_4h_pct_abs` | `FeatureBundle.dist_to_ema20_4h_pct_abs` | `float \| None` | same |
| `distance_to_last_structural_anchor_pct_abs` | `FeatureBundle.distance_to_last_structural_anchor_pct_abs` | `float \| None` | anchor not available |
| `distance_to_range_high_pct_abs` | `FeatureBundle.distance_to_range_high_pct_abs` | `float \| None` | range not computable |
| `bars_since_last_structural_break_4h` | `FeatureBundle.bars_since_last_structural_break_4h` | `int \| None` | no structural break detected in 4h history |

**Note on `distance_to_range_high_pct_abs`:** T5 documents this field as having an open definition question (see T5 ticket §open questions). Do not implement, infer, approximate, backfill, or rename `distance_to_range_high_pct_abs` in this ticket. If the current `FeatureBundle` does not expose a computed value, emit the field as `null` in `entry_location_inputs` for every symbol and add a code comment referencing the open T5 question.

---

## Output placement

The six fields are added as a new top-level sub-dict `entry_location_inputs` in `symbol_diagnostics.jsonl.gz`. The `entry_location_inputs` sub-dict is introduced as a new diagnostics namespace because these fields are a cohesive input family for the future Entry-Location Layer (T_EL2). This ticket does not move or restructure any existing diagnostics fields. Existing top-level fields, `axes`, `decision`, `state`, `phase`, `pattern`, and `invalidation` sub-dicts remain unchanged.

```json
{
  "symbol": "ASTERUSDT",
  "schema_version": "ir1.2",
  ...
  "entry_location_inputs": {
    "close_vs_ema20_4h_pct": 6.14,
    "bars_above_ema20_4h": 4,
    "dist_to_ema20_4h_pct_abs": 6.14,
    "distance_to_last_structural_anchor_pct_abs": 8.32,
    "distance_to_range_high_pct_abs": null,
    "bars_since_last_structural_break_4h": 3
  },
  ...
}
```

All six fields must be present for every symbol record. Symbols where a field is not computable carry `null` — not `0`, not omitted.

---

## Schema version

Bump `schema_version` from `ir1.1` to `ir1.2`. This follows the T27 versioning pattern. No migration of existing artifacts is required — older artifacts retain `ir1.1` and are read by analysis scripts with version-aware handling where needed.

---

## Null and non-finite value handling

- `None` / `null`: expected and valid for all six fields when data is unavailable. Must serialize as JSON `null`.
- `NaN`, `inf`, `-inf`: must not appear in output. If T5 produces a non-finite float for any field, serialize as `null` and log a warning. Do not propagate non-finite values to the diagnostics file.
- `data_4h_available == False`: all fields that depend on 4h-derived structure must be `null`. Codex must not synthesize daily fallbacks for any field in this ticket. If the current T5 implementation already emits a non-null value for a field when `data_4h_available == False`, preserve the T5 value only if the T5 implementation explicitly documents that the field is daily-compatible; otherwise serialize `null` and add a code comment explaining the conservative choice.

---

## Scope

### In scope

1. Add `entry_location_inputs` sub-dict with the six fields to the diagnostics serializer.
2. Bump `schema_version` to `ir1.2`.
3. Verify T5 internal attribute names and note any discrepancies from the names listed in this ticket.
4. Verify and document whether `distance_to_range_high_pct_abs` is computed or stub/None in the current T5 implementation.
5. Non-finite guard for all six fields.

### Out of scope

- Implementing `entry_location_status`, `entry_action_hint`, or any Entry-Location Layer logic. That is T_EL2.
- Modifying any T5 computation. This ticket only reads from the existing `FeatureBundle`.
- Changing any existing diagnostics fields or their placement.
- Adding these fields to the report JSON (`shadow-live-report.json`). Diagnostics only.
- Implementing `distance_to_range_high_pct_abs` if it is currently a stub.

---

## Acceptance criteria

1. All six fields appear in `entry_location_inputs` for every symbol record in `symbol_diagnostics.jsonl.gz`.
2. `schema_version` is `ir1.2`.
3. Symbols with `data_4h_available == False` have `null` for all six fields in `entry_location_inputs`.
4. No `NaN`, `inf`, or `-inf` values appear anywhere in `entry_location_inputs`.
5. `null` is used (not `0`, not omitted) for fields that are not computable for a given symbol.
6. If ASTERUSDT, RENDERUSDT, or any `early_reversal_break` symbol with `data_4h_available == True` appears in a test fixture or live artifact, `close_vs_ema20_4h_pct` must be serialized from the `FeatureBundle` and must not be omitted or replaced with `null` without a valid null condition. The sign of the value is not an acceptance criterion — correct serialization from T5 is.
7. **Record with full 4h data:** `entry_location_inputs` exists, all six keys are present, no key is omitted.
8. **Record without 4h data (`data_4h_available == False`):** all six fields in `entry_location_inputs` are `null`; no field is omitted.
9. **Non-finite guard:** any `NaN`, `inf`, or `-inf` produced by T5 for any of the six fields serializes as `null` in the diagnostics output.
10. **Stub field:** if `distance_to_range_high_pct_abs` is not computed by T5, the key is still present in `entry_location_inputs` with value `null`.
11. **Schema version:** every symbol diagnostic record in the output file carries `schema_version = "ir1.2"`.
12. **Backward compatibility:** any existing diagnostics tests expecting `ir1.1` are updated intentionally or made version-aware. No test is silently broken.
