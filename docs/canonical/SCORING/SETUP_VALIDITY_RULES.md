# Setup Validity Rules — `is_valid_setup`, Minimum History, Watchlist (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_SETUP_VALIDITY
status: canonical
invalid_behavior:
  top_lists: exclude
  watchlist: optional_include_with_reason
reasons_canonical:
  - insufficient_history
  - failed_gate
  - risk_flag
  - btc_risk_off_ineligible
minimum_history_defaults:
  breakout: { "1d": 30, "4h": 50 }
  pullback: { "1d": 60, "4h": 80 }
  reversal: { "1d": 120, "4h": 80 }
setup_id_to_history_key:
  breakout_immediate_1_5d: breakout
  breakout_retest_1_5d: breakout
```

## 1) `is_valid_setup` contract
- If `is_valid_setup == false`:
  - must not appear in Top lists/rankings
  - may appear in watchlist only if a stable reason is provided

## 2) Canonical reasons
Reasons must be deterministic strings (stable keys), e.g.:
- `insufficient_history:<tf>`
- `failed_gate:<gate_name>`
- `risk_flag:<flag_name>`
- `btc_risk_off_ineligible`

## 3) Minimum history thresholds (defaults)
These defaults must match `CONFIGURATION.md`.

### Breakout (used by Breakout Trend 1–5d)
- 1D: >= 30 closed candles
- 4H: >= 50 closed candles

### Pullback
- 1D: >= 60 closed candles
- 4H: >= 80 closed candles

### Reversal
- 1D: >= 120 closed candles
- 4H: >= 80 closed candles

## 4) Closed-candle buffer rule (implementation guard)
Effective lookback includes a buffer so the last in-progress candle never affects the required minimum of closed candles.

## 5) Interaction with percent_rank
Population definitions remain as specified in feature docs.
