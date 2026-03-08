# Output Schema — Trade Candidates Source of Truth (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_OUTPUT_SCHEMA
status: canonical
schema_version: v1.10
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
- `commit_hash`
- `schema_version`
- `providers_used`
- `config_hash`
- `asof_ts_ms`

Optional:
- `config_version`
- `asof_iso_utc`

## trade_candidates row contract
Minimum required fields:
- `symbol`
- `setup_id`
- `setup_score`
- `global_score`
- `decision`
- `decision_reasons`
- `tradeability_class`
- `risk_acceptable`

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

## Trade-candidates vs run-manifest separation
- Candidate-truth lives in `trade_candidates`.
- Operational metadata (runtime, versions, provider set) lives in manifest.
- No format-specific output may contradict the JSON `trade_candidates` truth.
