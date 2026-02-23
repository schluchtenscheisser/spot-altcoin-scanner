# Trade Model — 4H Immediate + Retest (Analytics-only, Canonical)

## Machine Header (YAML)
```yaml
id: TRADE_MODEL_4H_IMMEDIATE_RETEST
status: canonical
purpose: analytics_only
timeframe: 4h
determinism:
  closed_candle_only: true
  no_lookahead: true
entries:
  immediate:
    entry_rule: "open(next_4h_candle after last trigger candle close)"
  retest:
    entry_rule: "limit at breakout level, fill if low<=entry<=high on a retest-valid candle"
stops:
  atr_multiplier: 1.2
partials:
  target_r_multiple: 1.5
  size_pct: 40
trailing:
  activation: "after partial filled"
  exit_signal: "close_4h < ema20_4h"
time_stop:
  max_hold_hours: 168
priority_intracandle:
  order: ["STOP", "PARTIAL", "TRAIL"]
```

## 0) Scope
This document defines a deterministic *trade simulation* model used for analytics/backtest style evaluation. It must not affect live ranking unless explicitly referenced.

---

## 1) Inputs
Required per symbol:
- 4H OHLCV series (closed candles only)
- 4H EMA20 (standard EMA)
- ATR% (4H) and close_4h_last_closed for ATR absolute
- Breakout trigger candle indices and retest-valid candle indices (from setup logic)

---

## 2) Entry rules

### 2.1 Immediate entry
Definition:
- Identify the last trigger candle close for the setup (4H close above breakout level).
- Entry occurs at:
  - `entry = open(next_4h_candle)` after that trigger candle close.

### 2.2 Retest entry
Definition:
- `entry = breakout_level` (limit order at 1D structure level)
- Fill rule:
  - On the candle `j` where retest is valid, fill if:
    - `low_4h[j] <= entry <= high_4h[j]`
- If no fill occurs on the retest-valid candle, the trade is considered not entered.

---

## 3) Stop definition (both setups)
Compute ATR absolute on 4H:
- `atr_abs_4h = (atr_pct_4h_last_closed / 100) * close_4h_last_closed`

Stop:
- `stop = entry - 1.2 * atr_abs_4h`

---

## 4) Partial take-profit
Define R:
- `R = entry - stop`

Partial target:
- `partial_target = entry + 1.5 * R`

Partial size:
- `partial_size_pct = 40`

---

## 5) Trailing exit (only after partial active)
Activation:
- Trailing rules become active only after partial target is hit.

Exit signal:
- If a closed 4H candle satisfies:
  - `close_4h < ema20_4h`
then exit at:
- `exit = open(next_4h_candle)` after the signal candle close.

---

## 6) Time stop
Maximum holding time:
- `max_hold_hours = 168` (7 days)

If time reaches 168h after entry:
- exit at `open(next_4h_candle)` after the 168h boundary.

---

## 7) Intra-candle priority (deterministic)
Within a single 4H candle, events are resolved in this priority order:
1) STOP
2) PARTIAL
3) TRAIL

Rationale: conservative safety-first ordering, deterministic.

---

## 8) Outputs (canonical)
Per simulated trade:
- `entry_time`, `entry_price`
- `stop_price`
- `partial_target_price`, `partial_filled` (bool), `partial_time`
- `exit_time`, `exit_price`, `exit_reason` in {"stop", "trail", "time"}
- optional performance metrics: R-multiple, pct_return

---

## 9) Determinism constraints
- Only closed candles may generate signals.
- Execution prices are defined as opens of the next candle (except limit fill rule on retest-valid candle).
- No lookahead: the decision to enter/exit uses only information available at that candle close.
