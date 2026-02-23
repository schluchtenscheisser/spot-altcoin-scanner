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
These are defaults and must match config keys when `CONFIGURATION.md` is finalized.

### Breakout
- 1D: >= 30 closed candles
- 4H: >= 50 closed candles

### Pullback
- 1D: >= 60 closed candles
- 4H: >= 80 closed candles

### Reversal
- 1D: >= 120 closed candles
- 4H: >= 80 closed candles

## 4) Closed-candle buffer rule (implementation guard)
When fetching, the effective lookback should include a buffer so the last in-progress candle never affects the required minimum of closed candles.

## 5) Interaction with percent_rank
- Minimum-history invalid symbols are excluded from setup scoring.
- For `percent_rank`, the population rule is defined in `FEATURES/FEAT_PERCENT_RANK.md` and is based on eligibility + non-NaN feature values.
