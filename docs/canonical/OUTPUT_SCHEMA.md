# Output Schema — Trade Candidates Source of Truth (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: v1.18
canonical_schema_version_ref: docs/canonical/CHANGELOG.md
outputs:
  - json
  - markdown
  - excel
source_of_truth_entity: trade_candidates
```

## Core contract
- `trade_candidates` is the canonical output Source of Truth (SoT) for candidate-level decision data.
- Markdown and Excel are renderings of the same truth; they must not redefine semantics.
- Run manifest metadata is separate from candidate rows.
- Shadow calibration preparation reports are analysis-only artifacts and MUST NOT alter runtime decision thresholds.
- Setup-specific scoring documents may define additional per-row fields, but they MUST NOT redefine this global minimum contract.

## Run manifest (required)
Required fields:
- `run_id`
- `timestamp_utc`
- `config_hash`
- `canonical_schema_version`
- `feature_flags`
- `pipeline_paths`
- `counts_per_stage`
- `shortlist_size_used`
- `orderbook_top_k_used`
- `data_freshness`
- `warnings`
- `duration_seconds`

Notes:
- `warnings` MUST be a machine-readable list and MAY be empty (`[]`), but MUST NOT be `null`.
- `canonical_schema_version` MUST be sourced from `docs/canonical/CHANGELOG.md`.
- Manifest metadata is operational and remains separated from `trade_candidates`.

- `pipeline_paths` MUST include:
  - `shadow_mode` (`legacy_only|new_only|parallel`)
  - `legacy_path_enabled` (bool)
  - `new_path_enabled` (bool)
  - `primary_path` (`legacy|new`)
  - `primary_path_source` (`config|default|derived`)
- `pipeline_paths` values must be deterministic from config and valid mode semantics.
- Contradictory mode/primary combinations MUST fail clearly and MUST NOT silently re-route truth sources.

## trade_candidates row contract
Minimum required fields:
- `rank`
- `symbol`
- `coin_name`
- `decision`
- `decision_reasons`
- `entry_price_usdt`
- `current_price_usdt`
- `distance_to_entry_pct`
- `entry_state`
- `stop_price_initial`
- `stop_source`
- `risk_pct_to_stop`
- `target_1_price`
- `target_2_price`
- `target_3_price`
- `rr_to_target_1`
- `rr_to_target_2`
- `best_setup_type`
- `setup_subtype`
- `setup_score`
- `global_score`
- `entry_ready`
- `entry_readiness_reasons`
- `tradeability_class`
- `execution_mode`
- `spread_pct`
- `depth_bid_1pct_usd`
- `depth_ask_1pct_usd`
- `slippage_bps_5k`
- `slippage_bps_20k`
- `risk_acceptable`
- `market_cap_usd`
- `btc_regime`
- `flags`

Deterministic ordering:
- Primary: `decision` priority `ENTER` > `WAIT` > `NO_TRADE`
- Secondary for `ENTER` and `WAIT`: `global_score` descending
- Stable tie-breakers: `symbol` ascending, then `best_setup_type` ascending

Price semantics (authoritative):
- `entry_price_usdt` MUST represent the planned setup entry anchor from `analysis.trade_levels`:
  - pullback: `entry_zone.center`
  - breakout/reversal: `entry_trigger`
- `current_price_usdt` MUST represent the current spot price (`price_usdt`) as a separate field.
- Both fields are nullable and MUST be `null` when missing, non-finite, non-positive, or otherwise not evaluable.
- `distance_to_entry_pct` MUST be computed as `((current_price_usdt / entry_price_usdt) - 1.0) * 100` when both prices are valid positive finite numbers; otherwise `null`.
- `entry_state` is a deterministic timing-state enum derived from `distance_to_entry_pct` and MUST be `null` when distance is `null`.
- Entry-state thresholds (V1):
  - `early`: `distance_to_entry_pct < -0.25`
  - `at_trigger`: `-0.25 <= distance_to_entry_pct <= +0.25`
  - `late`: `+0.25 < distance_to_entry_pct <= +3.00`
  - `chased`: `distance_to_entry_pct > +3.00`

Target / RR semantics (authoritative):
- `stop_source` MUST be `invalidation`, `atr_fallback`, or `null`.
- `stop_price_initial` MUST be derived from the selected `stop_source` and match risk-model stop selection deterministically.
- `target_1_price`/`target_2_price`/`target_3_price` MUST be the canonical `1R/2R/3R` ladder derived from effective risk distance `R = entry_price_usdt - stop_price_initial`.
- `rr_to_target_1` / `rr_to_target_2` / `rr_to_target_3` MUST be computed from canonical targets and absolute risk:
  - `rr_to_target_1 = (target_1_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - `rr_to_target_2 = (target_2_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
  - `rr_to_target_3 = (target_3_price - entry_price_usdt) / (entry_price_usdt - stop_price_initial)`
- For evaluable long setups, RR values are deterministically `1.0`, `2.0`, `3.0` (floating-point tolerance).
- If `stop_price_initial` is missing/invalid/non-positive or `stop_price_initial >= entry_price_usdt`, target and RR fields MUST be `null`.
- Target fields are orientation levels for RR evaluation only; they MUST NOT imply mandatory exits or automated take-profit behavior.

## Summary contract
- `summary` MUST include setup counters (`reversal_count`, `breakout_count`, `pullback_count`, `total_scored`, `global_top20_count`).
- `summary` MUST include deterministic entry-state diagnostics over `trade_candidates`:
  - `entry_state_counts_all`
  - `entry_state_counts_enter`
  - `entry_state_counts_wait`
  - `entry_state_counts_no_trade`
- Each entry-state-count object MUST contain exactly these keys: `early`, `at_trigger`, `late`, `chased`, `null`.
- `null` count represents not-evaluable/missing `entry_state`; it MUST NOT be coerced to any timing failure.

## Nullable rules (authoritative)
Whenever a field is semantically not evaluable, value MUST remain `null`.

Typical nullable fields include (non-exhaustive):
- `invalidation_anchor_price`
- `invalidation_anchor_type`
- `invalidation_derivable`
- `stop_price_initial`
- `stop_source`
- `risk_pct_to_stop`
- `rr_to_target_1`
- `rr_to_target_2`
- `entry_price_usdt`
- `current_price_usdt`
- `distance_to_entry_pct`
- `entry_state`
- `spread_bps`
- `slippage_bps`
- `global_volume_24h_usd`
- `turnover_24h`
- `mexc_share_24h`

No implicit bool/number coercion is allowed for nullable fields.

## decision_reasons contract
- `decision_reasons` must preserve deterministic reason identity and ordering.
- UNKNOWN-path reasons (e.g. `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget`) MUST remain distinct.
- Output-layer diagnostic timing reasons are additive-only and MUST NOT alter decision logic:
  - `entry_too_early` only when `entry_state=early`
  - `entry_late` only when `entry_state=late`
  - `entry_chased` only when `entry_state=chased`
- For `entry_state=at_trigger` or `entry_state=null`, no new timing reason may be appended.
- Existing reasons MUST be preserved; timing reasons are appended only if missing (deduplicated, stable order).
- Decision-layer late-entry reasons are canonical reason keys when guards fire:
  - `price_past_target_1` (hard block; decision forced to `NO_TRADE`)
  - `effective_rr_insufficient` (soft downgrade; decision forced to `WAIT`)

## entry_readiness_reasons contract
- `entry_readiness_reasons` must be a deterministic list of standardized reason keys (no free text).
- If `entry_ready=false`, the list must be non-empty.
- If `entry_ready=true`, the list must be empty.

## Trade-candidates vs run-manifest separation
- Candidate-truth lives in `trade_candidates`.
- Operational metadata (runtime, versions, provider set) lives in manifest.
- No format-specific output may contradict the JSON `trade_candidates` truth.

## Markdown rendering minimum contract
- Markdown MUST render candidate rows from `trade_candidates` only.
- Markdown MUST include sections `ENTER Candidates`, `WAIT Candidates`, and `Summary`.
- `WAIT Candidates` MUST include full `decision_reasons` from SoT (no renaming, shortening, or heuristic replacement).
- Missing optional fields in `trade_candidates` MUST be rendered as not-available values rather than causing render crashes.
- Invalid `trade_candidates` schema (e.g. wrong type for required fields) MUST fail clearly instead of silent correction.

## Excel rendering minimum contract
- Excel MUST render candidate rows from `trade_candidates` only.
- Excel MUST contain sheets `Trade Candidates`, `Enter Candidates`, and `Wait Candidates`.
- `Trade Candidates` MUST contain all rows from SoT in deterministic order.
- `Enter Candidates` and `Wait Candidates` MUST be pure filters on `decision` (`ENTER` / `WAIT`) over the same SoT rows.
- `decision` and `decision_reasons` MUST be preserved from SoT without heuristic shortening or semantic remapping.
- Missing optional fields in `trade_candidates` MUST render as empty/not-available cells, not as coerced `0`/`false`.
- Invalid `trade_candidates` schema (e.g. wrong type for required fields) MUST fail clearly instead of silent correction.

## Setup scorer V2 structured fields
Scorer rows may include setup-specific confirmation flags as additive machine-readable fields.
Allowed examples:
- breakout: `breakout_confirmed`
- pullback: `rebound_confirmed`, `retest_reclaimed`
- reversal: `reclaim_confirmed`, `retest_reclaimed`

When a confirmation is semantically not evaluable due to missing/invalid/non-finite inputs, the confirmation field MUST remain `null`.

Directional Volume preparation namespace (Phase-1 inactive, optional):
- Optional field: `directional_volume_preparation: object|null`
- Allowed nested keys (all optional, nullable):
  - `buy_volume_share: number|null`
  - `sell_volume_share: number|null`
  - `imbalance_ratio: number|null`
  - `lookback_bars: integer|null`
- Missing `directional_volume_preparation` is valid and means “not provided”.
- `null` means “not evaluated / not used” and MUST NOT be coerced to negative/false signals.
- Invalid nested values are invalid-contract input and must fail clearly, distinct from missing/null.
- This namespace is preparatory only and MUST NOT change Phase-1 decision/scoring behavior by itself.
