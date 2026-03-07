# Pipeline — End-to-End Deterministic Flow (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_PIPELINE
status: canonical
phase: 1
stages:
  - universe_fetch
  - mapping
  - hard_gates
  - budgeted_pool_open
  - ohlcv_fetch
  - feature_engine
  - setup_validity_and_setup_score
  - tradeability_gate
  - risk_model
  - decision_layer
  - global_prioritization_and_rerank
  - output_render
stops_before_decision:
  - tradeability_class: UNKNOWN
  - setup_not_evaluable: true
determinism:
  closed_candle_only: true
  no_lookahead: true
  stable_sorting: true
```

## Purpose
Define the Phase-1 execution order and stop rules so downstream PRs implement one consistent pipeline contract.

## Stage contracts

### 1) Universe fetch
- Build deterministic spot-universe candidate list.
- Sort order MUST be explicit and stable (`symbol ASC` unless another canonical sort is documented).

### 2) Mapping
- Map exchange symbols to market-cap assets.
- Mapping collisions MUST be surfaced; no silent merge.

### 3) Hard gates (pre-shortlist guardrails)
- Apply hard constraints before expensive fetches and before ranking populations are finalized.
- Includes hard market-cap floor guardrail (`pre_shortlist_market_cap_floor_usd`) as defined in `BUDGET_AND_POOL_MODEL.md`.

### 4) Budgeted pool open
- Open a broader candidate pool early, then constrain expensive orderbook evaluation via budget controls.
- `shortlist_size` and `orderbook_top_k` are authoritative in `BUDGET_AND_POOL_MODEL.md`.

### 5) OHLCV fetch (closed candles only)
- Fetch required timeframes (Phase 1: 1D and 4H).
- Provider raw field is `closeTime`.
- Canonical normalized field for comparisons is `closeTime_ms`.
- Use only bars with `closeTime_ms <= asof_ts_ms`.

### 6) Feature engine
- Compute canonical features (EMA, ATR Wilder, ranks, etc.) per feature docs.
- Preserve nullable semantics where metrics are not evaluable.

### 7) Setup validity + setup score
- Determine setup validity and compute `setup_score`.
- `setup_score` is the decision-threshold score (not global prioritization).

### 8) Tradeability gate
- Compute `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL, FAIL, UNKNOWN}`.
- `UNKNOWN` represents not-evaluable/not-evaluated tradeability.
- `UNKNOWN` MUST stop here and MUST NOT reach Decision Layer.
- `orderbook_not_in_budget` is an explicit UNKNOWN/not-evaluated reason (outside orderbook budget), not a FAIL mapping.

### 9) Risk model
- Compute ATR-default stop and risk metrics (`stop_price_initial`, `risk_pct_to_stop`, `rr_to_tp10`, `rr_to_tp20`, `risk_acceptable`).
- Risk blockers from repo authority are applied (see `RISK_MODEL.md`).

### 10) Decision layer
- Decision domain is exactly `{ENTER, WAIT, NO_TRADE}`.
- Only fully evaluated candidates can become `WAIT`.
- `MARGINAL` is never ENTER-eligible.

### 11) Global prioritization and rerank
- `global_score` is used for prioritization among decision-eligible candidates.
- `global_score` MUST NOT override decision hard blockers.

### 12) Output rendering
- `trade_candidates` is source of truth for machine-readable decision outputs.
- Manifest metadata is produced separately; formats must not redefine business truth.

## Deterministic stop-path requirements
- `UNKNOWN` is neither `FAIL` nor `WAIT`; it is a pre-decision stop-path.
- No implicit coercion from nullability to booleans.
- No stage may silently reclassify `UNKNOWN` to `FAIL` or `WAIT`.

## Non-goals in Phase 1
- No portfolio manager.
- No mandatory exit automation.
- `TP10` / `TP20` are orientation targets only.
