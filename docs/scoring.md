# Scoring Modules Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

This document specifies the three scoring modules used by the scanner:

1. Breakout Score
2. Trend Pullback Score
3. Reversal Score

Each scoring module must:
- operate independently
- normalize scores to [0, 100]
- decompose into weighted components
- apply contextual penalties
- output ranked candidates
- surface flags + reasons
- remain deterministic

There is **no global fused score**.

---

## 1.1 Canonical v1.3 Notes

The canonical implementation is in:
- `scanner/pipeline/scoring/breakout.py`
- `scanner/pipeline/scoring/pullback.py`
- `scanner/pipeline/scoring/reversal.py`

Critical canonical rules:
- Reversal base component consumes `base_score` from FeatureEngine directly (no scorer-side base detection).
- Missing/NaN/non-finite `base_score` is treated as `0` (never coerced to 100 by clamping side effects).
- Momentum scaling is continuous and linear: `clamp((r_7 / 10) * 100, 0, 100)`.
- Penalties/thresholds are config-driven via `scoring.*.penalties` and `scoring.*.momentum`.

---

## 2. Shared Scoring Principles

### 2.1 Independence

Each setup represents a distinct trading archetype.  
Mixing setup signals degrades performance.

### 2.2 Determinism

Same data + same config → same score.

### 2.3 Explainability

Scores must return:
- components
- weights
- penalties
- flags
- structured reasons

### 2.4 Normalization

Raw score ∈ [0, 1]  
Normalized score ∈ [0, 100]

### 2.5 Penalty System

Penalties reduce normalized score based on flags:

| Flag | Penalty |
|---|---|
| low_liquidity | strong |
| extreme_volatility | moderate |
| falling_knife | strong |
| late_stage_move | moderate |
| mapping_low_confidence | optional |
| regime_mismatch (optional future) | mild |

Penalties must be multiplicative, not subtractive.

Example:

```
S_final = S_raw * P_low_liquidity * P_late_stage * ...
```

### 2.6 Output Structure

Each score returns:

```json
{
  "score": float (0–100),
  "normalized": float (0–1),
  "rank": int,
  "components": { ... },
  "penalties": { ... },
  "flags": { ... },
  "metadata": { ... }
}
```

---

## 3. Breakout Score

### 3.1 Setup Definition

Breakout = range break + volume confirmation

Breakouts occur when price exceeds prior resistance, typically measured using:

- 20d high
- 30d high

Volume confirms conviction.

### 3.2 Required Inputs

From features:

- `close`
- `high_20d`, `high_30d`
- `ema20`, `ema50`
- `volume_spike_7d`
- `atr_pct`

### 3.3 Gates

Breakout gates:

```
close > high_20d or close > high_30d
```

Volume gate:

```
volume_spike_7d ≥ threshold (config, e.g. 1.5)
```

### 3.4 Overextension Check

To avoid late-stage moves:

```
oe_ema20 = close / ema20 - 1
overextended = oe_ema20 > limit (config, e.g. 25%)
```

Late-stage moves produce penalty, not exclusion.

### 3.5 Components

Example weights:

| Component | Weight |
|---|---|
| price_break | 0.40 |
| volume_confirmation | 0.40 |
| volatility_context | 0.20 |

Normalized subcomponents:

```
s_price = clip((close - high_20d) / (0.05*high_20d), 0, 1)
s_volume = clip((vol_spike - 1.0) / (min_spike - 1.0), 0, 1)
s_vol_ctx = clip(atr_limit / atr_pct, 0, 1)
```

### 3.6 Penalties

```
if extreme_volatility → penalty
if low_liquidity → penalty
if late_stage_move → penalty
```

### 3.7 Interpretation

Breakouts are high-momentum, fragile setups.

---

## 4. Trend Pullback Score

### 4.1 Setup Definition

Trend Pullback = trend continuation after retracement

Trend must be established before retracement.

### 4.2 Required Inputs

- `close`
- `ema20`, `ema50`
- HH/HL structure
- pullback %
- volume
- 4h refinement (optional)

### 4.3 Trend Gate

Trend is up if:

```
close > ema50 (1d)
ema50 rising or flat
```

### 4.4 Pullback Detection

Compute:

```
recent_high = max(high over 20–30d)
pullback_pct = (recent_high - close) / recent_high
```

Configurable limits:

```
min_pullback_pct
max_pullback_pct (e.g. 25%)
```

### 4.5 Rebound Detection

Rebound conditions:

- HH over prior HL
- or reclaim above ema20
- or positive 3-day momentum

Optional 4h confirmation:
- ema20/ema50 cross
- volume uptick
- HH/HL on 4h

### 4.6 Components

Example weights:

| Component | Weight |
|---|---|
| trend_quality | 0.40 |
| pullback_quality | 0.40 |
| rebound_signal | 0.20 |

Component logic:

```
s_trend = f(close>ema50, ema50_slope, HH/HL_count)
s_pullback = f(pullback_pct range)
s_rebound = f(ema_reclaim + r_3d + vol_spike)
```

### 4.7 Penalties

- low liquidity
- late stage (if pullback shallow + extended trend)
- extreme volatility

### 4.8 Interpretation

Pullbacks are lower-volatility, medium-risk setups.

---

## 5. Reversal Score

### 5.1 Setup Definition

Reversal = downtrend → base → reclaim + volume

This setup captures structural transitions from bear to bull state.

### 5.2 Required Inputs

- drawdown from ATH
- base low & no-new-lows window
- volume SMA & spike
- reclaim vs EMA20/EMA50
- 3-day return
- volatility context

### 5.3 Gates (Strict)

Reversal gates:

**Gate 1: Drawdown**

```
min_dd ≤ drawdown ≤ max_dd
e.g. -40% ≤ dd ≤ -90%
```

**Gate 2: Base**

```
base_low = min(low over base_lookback)
no new lows for ≥ K days
```

**Gate 3: Reclaim**

```
close > ema20 (min 1 day)
optional: close > ema50
```

Volume Gate:

```
vol_spike ≥ threshold (e.g. 1.5)
```

### 5.4 Components

Example weights:

| Component | Weight |
|---|---|
| base_structure | 0.30 |
| reclaim_signal | 0.40 |
| volume_confirmation | 0.30 |

Normalized subcomponents:

```
s_base = g(days_without_new_low)
s_reclaim = g(close/ema20, close/ema50, r_3d)
s_vol = g(vol_spike)
```

### 5.5 Penalties

- falling_knife (strong penalty)
- extreme_volatility
- low_liquidity

### 5.6 Interpretation

Reversals are high-risk, high-reward setups and must be surfaced early.

---

## 6. Ranking

Each score produces:

- sorted list
- deterministic ordering
- stable tiebreaks via:
  1. score
  2. normalized
  3. market cap (optional descending)
  4. ticker (alphabetical)

Ranking must not change across runs for identical input.

---

## 7. Backtest Compatibility

Scores are snapshot-stored for backtesting.  
Forward returns must reference the score valid on day `t`.

---

## 8. Scoring Anti-Goals

Scoring must not:

- mix setup types
- use sentiment/news (v1)
- use ML/AI predictions
- incorporate execution logic
- overfit thresholds
- guess mapping

---

## 9. Tuning Philosophy

Tuning is done via:
- backtests
- hit/miss review
- qualitative inspection
- cluster performance analysis

No hyperparameter grid search in v1.

---

## 10. Future Extensions

Future scores may include:

- breakout fakeout detection
- sideways acceptance signals
- capitulation reversal scoring
- regime-based weighting
- risk-adjusted scoring
- volume signature profiles

v1 provides the structural foundation.

---

---

## 11. Phase Appendix Reference

Phase-specific scoring additions are maintained in:
- `docs/feature_improvements/PHASE_APPENDIX_FEATURES_SCORING.md`

This keeps high-traffic core docs conflict-stable while preserving exact phase semantics.
