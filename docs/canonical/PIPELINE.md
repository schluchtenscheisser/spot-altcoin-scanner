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
  - tradeability_gate
  - ohlcv_fetch
  - feature_engine
  - setup_validity_and_setup_score
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
shadow_mode:
  default_mode: parallel
  allowed_modes: [legacy_only, new_only, parallel]
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

### 5) Tradeability gate
- Compute `tradeability_class ∈ {DIRECT_OK, TRANCHE_OK, MARGINAL, FAIL, UNKNOWN}` after orderbook evidence is attached.
- Only `DIRECT_OK`, `TRANCHE_OK`, and `MARGINAL` may continue to OHLCV/features/scoring.
- `FAIL` and `UNKNOWN` MUST stop here and MUST NOT trigger OHLCV fetches.
- `UNKNOWN` represents not-evaluable/not-evaluated tradeability.
- `orderbook_not_in_budget` is an explicit UNKNOWN/not-evaluated reason (outside orderbook budget), not a FAIL mapping.

### 6) OHLCV fetch (closed candles only)
- Fetch required timeframes (Phase 1: 1D and 4H) only for symbols that passed the tradeability gate.
- Provider raw field is `closeTime`.
- Canonical normalized field for comparisons is `closeTime_ms`.
- Use only bars with `closeTime_ms <= asof_ts_ms`.

### 7) Feature engine
- Compute canonical features (EMA, ATR Wilder, ranks, etc.) per feature docs.
- Preserve nullable semantics where metrics are not evaluable.

### 8) Setup validity + setup score
- Determine setup validity and compute `setup_score`.
- `setup_score` is the decision-threshold score (not global prioritization).
- Setup scorers may add optional context fields `invalidation_anchor_price`, `invalidation_anchor_type`, `invalidation_derivable`; these are additive and must not alter risk/decision semantics in Phase 1.

### 9) Risk model
- Compute invalidation-first stop with ATR fallback and risk metrics (`stop_price_initial`, `stop_source`, `risk_pct_to_stop`, `rr_to_target_1`, `rr_to_target_2`, `risk_acceptable`).
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

## Shadow mode / parallel operation (transition contract)
- Pipeline activation is controlled centrally by `shadow.mode`.
- Allowed modes are deterministic and mutually exclusive:
  - `legacy_only`: legacy outputs active, new decision-path outputs inactive
  - `new_only`: new decision-path outputs active, legacy outputs inactive
  - `parallel`: both outputs active in one run
- Missing `shadow.mode` MUST resolve to canonical default `parallel`.
- Invalid mode values MUST fail config validation clearly; no silent fallback.
- `new_only` and `parallel` require a semantically complete new path (tradeability + risk + decision all enabled).
- Run artifacts/manifest MUST expose active + primary path state explicitly (`legacy_path_enabled`, `new_path_enabled`, `primary_path`, `primary_path_source`, resolved mode).
- Primary-path semantics are deterministic:
  - `legacy_only` => `primary_path=legacy`
  - `new_only` => `primary_path=new`
  - `parallel` => `primary_path` is required semantically; missing runtime key MUST resolve to canonical default `legacy` and manifest MUST mark `primary_path_source=default`.
- Contradictory mode/primary combinations (e.g. `mode=legacy_only` with `primary_path=new`) MUST fail clear validation (no silent fallback).
- `trade_candidates` remains the target SoT; shadow mode is transitional control, not a second business truth.

## Non-goals in Phase 1
- No portfolio manager.
- No mandatory exit automation.
- `TP10` / `TP20` are orientation targets only.
