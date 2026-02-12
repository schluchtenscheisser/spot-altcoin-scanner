# Feature Engine Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

The Feature Engine converts raw OHLCV + ticker inputs into **structured technical features** used by scoring modules.

Features must be:

- deterministic
- time-consistent
- numerically stable
- snapshot-compatible
- interpretable
- minimally dependent on parameter tuning

The Feature Engine does **not** make trading decisions; it prepares the signal inputs.

---

## 2. Timeframes

v1 uses two core timeframes:

- **1d** (daily): primary structure/timeframe of the scanner
- **4h** (intra-day refinement)

Optional future timeframes:

- **1h** (timing/signal amplification)
- **1w** (macro context)

Timeframes must not be mixed in the same feature without explicit definition.

### Time-index convention (closed candles)

All feature values are computed from the **last closed candle** `T` (not blindly from the latest array row).

- `T = max(i where closeTime[i] <= asof_ts_ms)`
- If no `asof_ts_ms` is provided, current runtime uses the last available kline index.

This convention prevents intrabar drift and keeps snapshots replayable.

---

## 3. Lookback Requirements

Minimum recommended lookbacks:

| Feature | Lookback |
|---|---|
| Trend / EMA | 60–120 days |
| Drawdown / ATH | 120–365 days |
| Reversal Base | 30–60 days |
| Breakout Highs | 20–30 days |
| Volume SMA | 7–14 days |
| ATR Volatility | 14–30 days |

Lookbacks must be configurable via `config.yml`.

For volume baseline features (e.g. `volume_sma_14` used for `volume_spike`), the baseline is computed excluding the current candle: `mean(volume[t-14 .. t-1])`.

---

## 4. Input Data Requirements

Feature computation requires:

- OHLC: `open`, `high`, `low`, `close`
- Volume: `volume`
- Derived: `quote_volume` (from ticker data)
- Timestamps: aligned to UTC
- No missing candles

Missing candles must be either:
- forward-filled (preferred for 4h gaps)
- linear-filled (not preferred)
- or asset excluded if too incomplete

---

## 5. Price-Based Features

### 5.1 Returns

Returns are computed windowed and normalized:

```
r_n = close[t] / close[t-n] - 1
```

v1 windows:
- `r_1d`
- `r_3d`
- `r_7d`

Optional future:
- `r_14d`, `r_30d`

Returns computed both on 1d and 4h basis (4h for near-term changes).

---

### 5.2 Highs & Lows

Compute for `n ∈ {20, 30}`:

```
high_n = max(high[t-n .. t])
low_n = min(low[t-n .. t])
```

Used for breakout logic + pullbacks + context.

**Baseline convention (Thema 6):**
For breakout baselines, resistance/support windows are computed **excluding the current candle** (`t`).

```
prior_high_n = max(high[t-n .. t-1])
prior_low_n  = min(low[t-n .. t-1])
```

This avoids look-ahead bias in baseline features such as breakout distance.

---

### 5.3 ATH + Drawdown (Context)

ATH computed over long window, e.g.:

```
ath_price = max(close[0 .. t])
drawdown = close[t] / ath_price - 1
```

Used for reversal gating and base formation, not exclusion.

---

### 5.4 HH/HL Structure (Directional Structure)

Directional structure on 1d:

```
higher_low = low[t] > low[t-k]
higher_high = high[t] > high[t-k]
```

Used for trend + reversal confirmation.

Optional context:
- consecutive HH/HL counts
- structure strength factor

---

## 6. Trend Features

### 6.1 EMA

Compute:
- `ema20`
- `ema50`

On both 1d and 4h.

Implementation convention (current):
- EMA initialization starts with `SMA(period)` (not first-value bootstrap)
- then recursive EMA update is applied over the remaining candles

Trend inference:

```
trend_up = close > ema50 and ema50 increasing
trend_down = close < ema50 and ema50 decreasing
```

Trend is used for pullback/trend gating.

---

### 6.2 Slope

Slope may be computed via log regression:

```
slope = slope_of(log(close))
```

Used indirectly; not mandatory for v1 scoring.

---

## 7. Volatility Features

Volatility measured via ATR:

```
atr = ATR(14)
atr_pct = atr / close
```

Implementation convention (current):
- ATR uses **Wilder smoothing** after ATR initialization
- `atr_pct` is derived from this Wilder ATR and is expected to be non-negative

Used for:
- breakout context
- reversal stability
- penalty for extreme volatility

Optional: realized volatility windows (future).

---

## 8. Volume Features

Volume features include:

- raw volume
- volume SMA (7, 14 days)
- volume spike factor:

```
vol_spike = volume_today / volume_sma7
```

Volume assists:

| Setup | Role |
|---|---|
| Breakout | confirmation |
| Pullback | rebound strength |
| Reversal | base → reclaim confirmation |

Volume spikes must normalize across assets via SMA.

---

## 9. Pullback Features

Pullback requires:

1. established trend (↑)
2. retracement from recent highs
3. rebound attempt

Retracement measured:

```
pullback_pct = (recent_high - close) / recent_high
```

Rebound detected via HH/HL + volume + EMA recapture.

---

## 10. Reversal Features

Reversal decomposed into:

1. **Drawdown Context**  
   coin must be down significantly from ATH

2. **Base Detection**  
   base low + no new lows for `k` days

3. **Reclaim**  
   EMA20/EMA50 recapture + r_3d > threshold

4. **Volume Confirmation**  
   vol spike vs SMA

Reversal is stricter than “oscillator oversold” signals.

---

## 11. Breakout Features

Breakout decomposed into:

1. **High Break**

```
close > high_20 or close > high_30
```

2. **Volume Confirmation**

```
vol_spike ≥ threshold
```

3. **Overextension Check**

```
close / ema20 within limit
```

Breakout does not require drawdown context.

---

## 12. Liquidity Features

Ticker-based 24h quote volume is used for:

- shortlist selection
- low liquidity penalty
- backtest weighting (future)

Must be in USDT terms.

---

## 13. Flags (Derived from Features)

Feature engine must generate flags such as:

| Flag | Meaning |
|---|---|
| low_liquidity | poor tradeability |
| extreme_volatility | ATR too high |
| falling_knife | new lows + high volume |
| late_stage_move | overextended breakout |
| mapping_low_confidence | unreliable binding |

Flags affect scoring and reporting.

---

## 14. Output Format (Feature Layer)

Features must be stored per-asset per-day in JSON:

Recommended:

```
features[timeframe][feature_name]
```

Example:

```
features["1d"]["ema20"]
features["4h"]["r_4h"]
```

---

## 15. Determinism Requirements

- no stochastic components
- no random thresholds
- no forward-looking leak
- snapshot reproducibility mandatory

---

## 16. Exclusions (What Features Are Not)

Feature layer must **not** include:

- RSI, MACD, stochastic oscillators (v1)
- multi-timeframe fusion signals (v1)
- sentiment
- onchain data
- news data
- model-based predictions

These belong to future extensions and bias the scanner away from pure structural signals.

---

## 17. Integration

Feature Engine feeds:
- scoring modules
- backtests
- reports
- snapshots

It does not pull data from scoring.

---

## 18. Quote Volume (Thema 7)

If Kline `quoteVolume` is present, compute:
- `volume_quote`
- `volume_quote_sma_14` (baseline excludes current candle)
- `volume_quote_spike`

If unavailable, quote-volume keys are omitted.

---

## End of `features.md`
