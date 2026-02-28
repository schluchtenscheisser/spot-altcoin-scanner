# Pipeline — End-to-End Deterministic Flow (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_PIPELINE
status: canonical
stages:
  - universe_fetch
  - mapping
  - hard_gates
  - cheap_pass_shortlist
  - ohlcv_fetch
  - feature_engine
  - setup_validity
  - setup_scoring
  - liquidity_rerank
  - output_render
determinism:
  closed_candle_only: true
  stable_sorting: true
```

## 1) Stage: Universe fetch (MEXC)
Goal: Obtain candidate trading symbols (spot pairs).
- Canonical intent: focus on spot pairs quoted in USDT.

Outputs:
- `symbols_universe` (deterministically ordered or explicitly sorted)

## 2) Stage: Mapping (Exchange symbol -> Market-cap asset)
Goal: link exchange symbols to market-cap universe assets.
- Mapping must be deterministic.
- Collisions must be detected and surfaced (not silently resolved).
- Overrides are allowed and version-controlled.

Outputs:
- `mapped_assets` (with confidence/metadata)
- `mapping_collisions_report` (if any)

## 3) Stage: Hard gates
Applied before expensive computations and before `percent_rank` populations are formed.
Canonical hard gates include:
- Market cap range (default: 100M..10B USD; per-setup may override)
- Liquidity gates (Universe hard gate):
  - Primary path (turnover available): require all of
    - `turnover_24h >= min_turnover_24h`
    - `mexc_quote_volume_24h_usdt >= min_mexc_quote_volume_24h_usdt`
    - `mexc_share_24h >= min_mexc_share_24h`
  - Fallback path (turnover unavailable): require only
    - `mexc_quote_volume_24h_usdt >= min_mexc_quote_volume_24h_usdt`
  - Per-symbol invalid values (negative / NaN / non-castable) fail deterministically.
- Risk flags (denylist, deposit/withdraw suspended, delisting risk, major unlock within 14d, liquidity grade D, etc.)
- Minimum history requirements per setup/timeframe
  - Closed-candle counts are derived from `meta.last_closed_idx` as `count = idx + 1`.
  - If `last_closed_idx` for a required timeframe is missing/invalid (`None`), history is insufficient and the symbol is rejected for that setup.
  - Boundary rule: `count == min_history` is sufficient (reject only when `count < min_history`).

Output:
- `eligible_universe` (this is the canonical `percent_rank` population baseline)

## 4) Stage: Cheap pass shortlist (optional)
Purpose: reduce expensive OHLCV/orderbook calls while remaining deterministic.
Canonical rule:
- Cheap pass must not redefine `percent_rank` population; it only reduces fetch workload.

Output:
- `shortlist_symbols`

## 5) Stage: OHLCV fetch (1D + 4H)
- Fetch OHLCV for required timeframes (canonical: 1D, 4H).
- Apply closed-candle-only policy:
  - only candles with `closeTime <= asof_ts_ms` are used

Output:
- `ohlcv_1d`, `ohlcv_4h`

## 6) Stage: Feature engine
Compute canonical features:
- EMA standard
- ATR Wilder + ATR%
- Volume SMA and spikes (exclude current candle for SMA)
- BB width% and rolling rank
- ATR% rolling rank (1D)
- percent_rank (cross-section; population = eligible universe after hard gates)

Output:
- per-symbol feature set (with NaN rules)

## 7) Stage: Setup validity
Compute per-setup validity:
- `is_valid_setup` plus explicit reason for invalidity.

Canonical:
- invalid setups never appear in Top lists.
- optional: invalid setups may appear in watchlist with reason.

## 8) Stage: Setup scoring
Compute per-setup component scores, multipliers, final score (0..100).
Canonical setup scorer:
- Breakout Trend 1–5d (Immediate + Retest)

Output:
- `setup_score_rows`

## 9) Stage: Liquidity & re-rank
- Proxy pre-rank by quote volume
- Fetch orderbook for top candidates (Top-K levels)
- Compute spread/slippage
- Re-rank deterministically (score desc, slippage asc, proxy desc, symbol asc)

Output:
- `reranked_rows`

## 10) Stage: Output rendering
Produce outputs:
- JSON (machine)
- Markdown (human-readable summary, consistent with JSON)
- Excel (tabular export)

Also include a run manifest:
- commit hash
- config hash/version
- schema version
- as-of
- providers used
