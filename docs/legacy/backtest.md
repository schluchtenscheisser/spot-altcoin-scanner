# Backtest Specification
Version: v1.0  
Language: English  
Audience: Developer + GPT

---

## 1. Purpose

The Backtest Engine evaluates the effectiveness of the scanner's **setup-specific scores** by computing **forward returns** on stored snapshots.

Backtesting is required for:

- validation of scoring assumptions
- tuning weights & thresholds
- identifying false positives/negatives
- empirical setup performance
- iterative refinement of the scanner

The engine does **not** evaluate execution or portfolio strategies in v1.

---

## 2. Core Principle

Backtesting must be:

- **snapshot-driven**
- **deterministic**
- **reproducible**
- **setup-specific**
- **version-aware**

Backtests run on historical snapshots, not live queries.

---

## 3. Forward Return Definition

Forward returns are computed based on:

```
entry_price = close[t]
exit_price = close[t + k_days]
return_k = exit_price / entry_price - 1
```

v1 forward windows:

- +7d
- +14d
- +30d

Values must be configurable.

---

## 4. Data Source for Prices

Forward pricing must use:
- OHLCV snapshot history if present
- or re-fetch if snapshot lacking (optional)
- never forward-fill based on today's price

Snapshots must store entry-day close prices.

---

## 5. Backtest Workflow

Workflow:

```
for each snapshot in history:
  for each setup type (breakout, pullback, reversal):
    select ranked candidates
    compute forward returns
    store results
```

Optional filters:
- top N per setup
- score threshold
- liquidity threshold

---

## 6. Evaluation Metrics

Metrics computed per setup:

- hit rate
- median return
- mean return
- % positive returns
- tail loss (p10, p25)
- tail gain (p75, p90)
- sample size
- distribution analysis

Hit rate definition is setup-specific and must be configurable.

Example:

```
hit = forward_30d > +20%
```

---

## 7. Per-Setup Performance Rationale

Setup performance must be evaluated separately:

| Setup | Expected Behavior |
|---|---|
| Breakout | high variance / short horizon |
| Pullback | moderate variance / medium horizon |
| Reversal | highest tail upside / medium horizon |

Performance merging destroys signal integrity.

---

## 8. Rank-Based Analysis

Rank effects must be measured:

Example:

```
top 1
top 3
top 5
top 10
```

Expected:
- higher rank → higher expected forward returns
- monotonicity desirable but not required

---

## 9. Parameter Effects

Backtest must record config/spec version to allow:

- tuning scoring weights
- tuning penalties
- adjusting lookbacks
- adjusting volume thresholds

Parameter tuning is manual in v1.

---

## 10. Visualization (Optional v1)

Optional but desirable plots:

- score vs forward return
- rank vs forward return
- distribution histograms
- drawdown vs reversal outcome

These can be added in v2.

---

## 11. Execution & Portfolio (Excluded in v1)

Excluded:

- stop losses
- TP/SL rules
- leverage
- portfolio sizing
- multi-asset allocation
- execution slippage beyond simple bps
- commissions

These belong to future portfolio/strategy modules.

---

## 12. Determinism Requirements

Backtests must:

- not mutate snapshots
- not use future data
- not leak forward information
- not depend on random order
- be reproducible under config/version lock

---

## 13. Version Awareness

Backtest must store:

```
spec_version
config_version
snapshot_version
```

Version changes must invalidate performance comparisons unless aligned.

---

## 14. End Condition

Backtests must support:

- rolling evaluation
- full-history evaluation
- by-setup evaluation
- by-rank evaluation
- by-period evaluation

---

## 15. Extensibility

Future extensions:

- execution engine
- regime detection
- optimization of thresholds
- scoring calibration
- ML-assisted ranking
- tail-risk modeling
- Think risk/return frontier rather than raw returns

---

## End of `backtest.md`
