# Configuration Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

This document specifies the configurable parameters for the scanner.  
Configuration controls:

- pipeline behavior
- thresholds
- lookbacks
- penalties
- scoring weights
- run modes
- data source usage

Config must be:

- explicit
- deterministic
- versioned
- snapshot-captured

Config changes **affect backtest compatibility** and therefore must increment version.

---

## 2. Configuration Model

Configuration is stored as:

- `config.yml` (primary)
- environment variables (overrides)
- CLI arguments (optional, secondary)

Priority:

```
CLI > ENV > config.yml
```

---

## 3. Configuration Sections

Recommended structure:

```
general:
data_sources:
universe_filters:
exclusions:
mapping:
features:
scoring:
backtest:
logging:
```

---

## 4. General

```yaml
general:
  run_mode: "standard" # "standard", "fast", "offline", "backtest"
  timezone: "UTC"
  shortlist_size: 100
  lookback_days_1d: 120
  lookback_days_4h: 30
```

---

## 5. Data Sources

```yaml
data_sources:
  mexc:
    enabled: true
    max_retries: 3
    retry_backoff_seconds: 3

  market_cap:
    provider: "cmc"
    api_key_env_var: "CMC_API_KEY"
    max_retries: 3
    bulk_limit: 5000
```

Rate limit configuration should be static per provider.

---

## 6. Universe Filters

```yaml
universe_filters:
  market_cap:
    min_usd: 100000000 # 100M
    max_usd: 3000000000 # 3B
  volume:
    min_quote_volume_24h: 1000000
  history:
    min_history_days_1d: 60
  include_only_usdt_pairs: true
```

---

## 7. Exclusions

```yaml
exclusions:
  exclude_stablecoins: true
  exclude_wrapped_tokens: true
  exclude_leveraged_tokens: true
  exclude_synthetic_derivatives: true

  stablecoin_patterns: ["USD", "USDT", "USDC", "EURT"]
  wrapped_patterns: ["WETH", "WBTC", "st", "stk", "w"]
  leveraged_patterns: ["UP", "DOWN", "BULL", "BEAR", "3L", "3S"]
```

Pattern rules avoid false positives.

---

## 8. Mapping

```yaml
mapping:
  require_high_confidence: false
  overrides_file: "config/mapping_overrides.json"
  collisions_report_file: "reports/mapping_collisions.csv"
  unmapped_behavior: "filter" # or "warn"
```

Mapping stability is crucial for reproducibility.

---

## 9. Features

```yaml
features:
  timeframes:
    - "1d"
    - "4h"

  ema_periods:
    - 20
    - 50

  atr_period: 14

  high_low_lookback_days:
    breakout: 30
    reversal: 60

  volume_sma_period: 7
  volume_spike_threshold: 1.5

  drawdown_lookback_days: 365
```

Feature parameters affect scoring.

---

## 10. Scoring

> Note: The project currently contains some legacy keys for backward compatibility.
> The canonical scorer keys are those consumed in code (`scanner/pipeline/scoring/*.py`).

### 10.1 Breakout (canonical)

```yaml
scoring:
  breakout:
    enabled: true
    min_breakout_pct: 2
    ideal_breakout_pct: 5
    max_breakout_pct: 20
    min_volume_spike: 1.5
    ideal_volume_spike: 2.5
    breakout_curve:
      floor_pct: -5
      fresh_cap_pct: 1
      overextended_cap_pct: 3
    momentum:
      r7_divisor: 10
    penalties:
      overextension_factor: 0.6
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
```

---

### 10.2 Pullback (canonical)

```yaml
  pullback:
    enabled: true
    min_trend_strength: 5
    min_rebound: 3
    min_volume_spike: 1.3
    momentum:
      r7_divisor: 10
    penalties:
      broken_trend_factor: 0.5
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
```

---

### 10.3 Reversal (canonical)

```yaml
  reversal:
    enabled: true
    min_drawdown_pct: 40
    ideal_drawdown_min: 50
    ideal_drawdown_max: 80
    min_volume_spike: 1.5
    penalties:
      overextension_threshold_pct: 15
      overextension_factor: 0.7
      low_liquidity_threshold: 500000
      low_liquidity_factor: 0.8
```

---

## 11. Backtest

```yaml
backtest:
  enabled: true
  forward_return_days: [7, 14, 30]
  max_holding_days: 30
  entry_price: "close"
  exit_price: "close_forward"
  slippage_bps: 10
```

---

## 12. Logging

```yaml
logging:
  level: "INFO"
  file: "logs/scanner.log"
  log_to_file: true
```

---

## 13. Versioning

Configuration changes must increment:

- `config_version`
- `spec_version`

Format:

```yaml
version:
  config: 1.0
  spec: 1.0
```

---

## 14. Anti-Goofs (Important)

Config must **not**:

- contain fuzzy logic
- depend on ML
- rely on sentiment/news
- mix setup type parameters
- implicitly couple scoring modules
- silently change behavior across runs

---

## 15. Extensibility

Config must support additions without breaking v1:

- new scores
- new filters
- new penalties
- new timeframes
- new data sources

Backward compatibility is desirable but not required for v1.

---

## End of `config.md`
