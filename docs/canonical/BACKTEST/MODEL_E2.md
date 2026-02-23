# Backtest Model (E2) — Trigger/Entry/Hit (Analytics-only, Canonical)

## Machine Header (YAML)
```yaml
id: BACKTEST_MODEL_E2
status: canonical
purpose: analytics_only
determinism:
  closed_candle_only: true
  no_lookahead: true
default_parameters:
  T_hold_days: 10
  thresholds_pct: [10, 20]
  T_trigger_max_days: 5
entry_price_field: close
evaluation_fields_optional:
  - mfe_pct
  - mae_pct
```

## 0) Scope
This backtest model exists for calibration/analysis and must not affect live ranking unless explicitly referenced by a scoring document.

Canonical constraints:
- Closed-candle-only
- No lookahead (future candles must not influence trigger detection or features used at trigger time)

---

## 1) Definitions
Let:
- `t0` be the evaluation start day index (1D closed candle index).
- `close[t]`, `high[t]`, `low[t]` are 1D OHLCV values from closed candles.
- `T_trigger_max_days` default = 5
- `T_hold_days` default = 10
- thresholds: `+10%`, `+20%` (configurable list)

### 1.1 Closed-candle rule
All references to day indices are closed 1D candles only.
No intraday candles are used in E2 (unless explicitly extended later).

---

## 2) Trigger search window
A setup has a trigger condition (setup-specific). E2 does not define the trigger condition itself; it defines how to *evaluate* once a trigger condition is supplied.

Canonical trigger search:
- Search for the first day `t_trigger` within:
  - `t_trigger ∈ [t0 .. t0 + T_trigger_max_days]`
  such that `trigger_condition(t_trigger) == true`.

If no trigger occurs in that window:
- Mark as `no_trigger`.

---

## 3) Entry price
If a trigger day exists:
- `entry_price = close[t_trigger]`

(If a different entry price policy is used in code, it must be explicitly specified in canonical docs. E2 default is close.)

---

## 4) Hold window & hits
Hold window starts after trigger day and covers the next `T_hold_days` days:

- `hold_window = [t_trigger+1 .. t_trigger+T_hold_days]`

For each threshold `x` in `thresholds_pct`:
- Define target price:
  - `target_x = entry_price * (1 + x/100)`
- Define hit:
  - `hit_x = (max(high[t] for t in hold_window) >= target_x)`

Canonical notes:
- The high values are from closed daily candles; this implies the price could have traded above the target intraday, captured by daily high.
- No lookahead is respected because the evaluation uses only days after the trigger.

---

## 5) Optional MFE/MAE (if computed)
If computed, define relative to entry_price, over the same hold window:

- `mfe_pct = (max(high[t] for t in hold_window) / entry_price - 1) * 100`
- `mae_pct = (min(low[t] for t in hold_window) / entry_price - 1) * 100`

If hold_window is empty (insufficient future history):
- `hit_x`, `mfe_pct`, `mae_pct` are undefined (NaN) and should be reported as insufficient evaluation horizon.

---

## 6) Output fields (canonical)
Per evaluated setup instance:
- `t0` (evaluation start day index or timestamp)
- `t_trigger` (or null)
- `entry_price` (or null if no trigger)
- `hit_10` / `hit_20` (or for general thresholds list)
- optional: `mfe_pct`, `mae_pct`
- `reason` in {"ok", "no_trigger", "insufficient_forward_history"}

---

## 7) Determinism requirements
- Trigger detection must be based only on data up to and including `t_trigger`.
- Evaluation uses only hold-window candles and does not influence live scores.
- Any change in parameters must be reflected in `docs/canonical/CONFIGURATION.md` if it becomes a default.
