# Output Schema — Trade Candidates Source of Truth (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: v1.14
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
- `stop_price_initial`
- `risk_pct_to_stop`
- `tp10_price`
- `tp20_price`
- `rr_to_tp10`
- `rr_to_tp20`
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

## Nullable rules (authoritative)
Whenever a field is semantically not evaluable, value MUST remain `null`.

Typical nullable fields include (non-exhaustive):
- `invalidation_anchor_price`
- `invalidation_anchor_type`
- `invalidation_derivable`
- `stop_price_initial`
- `risk_pct_to_stop`
- `rr_to_tp10`
- `rr_to_tp20`
- `spread_bps`
- `slippage_bps`
- `global_volume_24h_usd`
- `turnover_24h`
- `mexc_share_24h`

No implicit bool/number coercion is allowed for nullable fields.

## decision_reasons contract
- `decision_reasons` must preserve deterministic reason identity and ordering.
- UNKNOWN-path reasons (e.g. `orderbook_data_missing`, `orderbook_data_stale`, `orderbook_not_in_budget`) MUST remain distinct.

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
