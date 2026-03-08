# Shadow Calibration Preparation Report (Canonical)

## Machine Header (YAML)
```yaml
id: OUTPUT_SHADOW_CALIBRATION_PREP
status: canonical
output_kind: shadow_calibration_prep_report_json
path_pattern: "artifacts/shadow_calibration/shadow_calibration_prep_*.json"
phase: preparation_only
```

## Purpose
This output is a **preparation + recommendation artifact** for later shadow calibration work.

Hard constraints:
- It MUST NOT change productive scanner thresholds.
- It MUST NOT enable active calibration.
- It MUST remain an analysis/meta artifact, separate from runtime decision truth.
- Any recommended thresholds MUST remain shadow-only until an explicit future activation contract exists.

## Input
- Source file: evaluation dataset JSONL (`eval_*.jsonl`) as defined in `OUTPUTS/EVALUATION_DATASET.md`.
- Required source row types:
  - first row `type="meta"`
  - following `type="candidate_setup"` rows

## Required fields (report)
- `type = "shadow_calibration_prep_report"`
- `report_id` (deterministic id from CLI override or UTC timestamp)
- `generated_at_iso` (UTC)
- `source_run_id`
- `source_dataset_schema_version`
- `summary`
  - `candidate_rows`
  - `evaluable_rows`
  - `not_evaluable_rows`
  - `invalid_rows`
  - `invalid_ratio`
- `setup_type_summary`
- `invalid_examples`
- `calibration_state`
  - `active` MUST be `false`
  - `threshold_adjustment` MUST be `null`
- `shadow_recommendation`
  - `status` (`ready|insufficient_data|invalid_data`)
  - `recommended_thresholds`
    - `min_score_for_enter` (number or `null`)
    - `min_rr_to_tp10` (number or `null`)
  - `shadow_probabilities`
    - `overall.p_hit10_5d_est` (number or `null`)
    - `overall.p_hit20_5d_est` (number or `null`)
    - `by_setup[setup_type].p_hit10_5d_est` (number or `null`)
    - `by_setup[setup_type].p_hit20_5d_est` (number or `null`)
  - `constraints`
    - includes configured minimum sample constraints and hit-rate targets used for recommendation derivation
  - `notes` (machine-readable list)

## Data quality handling
- Missing required label fields (`hit10_5d`, `hit20_5d`, `mfe_5d_pct`, `mae_5d_pct`) are invalid and MUST be reported.
- Non-finite numeric values (`NaN`, `+inf`, `-inf`) in preparation inputs MUST be reported explicitly as invalid.
- Not-evaluable rows (e.g. nullable label fields remain `null`) MUST stay separate from invalid rows.

## Determinism
For identical input file and identical CLI arguments:
- `summary`, `setup_type_summary`, and `invalid_examples` MUST be deterministic.
- `shadow_recommendation` MUST be deterministic (same thresholds/probabilities/status).
- Ordering of `invalid_examples` MUST be stable.

## Strict / atomic behavior
If strict mode is enabled:
- Any invalid row MUST fail the run.
- The report file MUST NOT be written (no partial writes).

## Recommendation derivation requirements
- Recommendation derivation MUST use only evaluable rows with finite numeric values.
- Missing/insufficient evaluation basis MUST result in `null` recommendation fields (no implicit fallback to live defaults).
- `insufficient_data` and `invalid_data` MUST remain distinct statuses.
- If no score threshold satisfies configured sample and hit-rate constraints, `recommended_thresholds.min_score_for_enter` MUST be `null`.
- If `min_rr_to_tp10` cannot be derived from valid downside data, it MUST be `null`.
