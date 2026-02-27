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

### 1.2 Parameter aliases
Canonical parameter aliases (equivalent names):
- Trigger window: `T_trigger_max`, `t_trigger_max`, `T_trigger_max_days`, `t_trigger_max_days`
- Hold window: `T_hold`, `t_hold`, `T_hold_days`, `t_hold_days`

Conflict rule:
- If multiple aliases for the same parameter are provided with different values, evaluation must fail with a clear `ValueError` (no silent fallback).

Threshold parsing:
- `thresholds_pct` missing or `null` → use defaults `[10, 20]`.
- Allowed input types: list/tuple/set of numeric-like values.
- Scalar values (`int`, `float`, `str`) are invalid and must raise `ValueError` with a clear message (e.g. `thresholds_pct must be list-like or null`).

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

Data availability rule for trigger search window (`t0 .. t0 + T_trigger_max_days`):
- Missing days or missing single `close[t]` values inside the window are allowed and must be skipped.
- If there is no single evaluable day in the full search window with numeric `close[t]`, mark as `missing_price_series`.

---

## 3) Entry price
If a trigger day exists:
- `entry_price = close[t_trigger]`

(If a different entry price policy is used in code, it must be explicitly specified in canonical docs. E2 default is close.)

Entry validity rule:
- If `entry_price` is null or `entry_price <= 0`, mark as `invalid_entry_price`.
- `invalid_entry_price` must only be evaluated when a trigger exists (`t_trigger != null`).
- If no trigger exists in the trigger window, the reason remains `no_trigger` (unless a higher-precedence reason matches).

Setup-specific trade-level requirements (required input metadata):
- `breakout` setup:
  - requires `trade_levels.entry_trigger` (`numeric > 0`) **or** `trade_levels.breakout_level_20` (`numeric > 0`)
- `reversal` setup:
  - requires `trade_levels.entry_trigger` (`numeric > 0`)
- `pullback` setup:
  - requires `trade_levels.entry_zone.lower` and `trade_levels.entry_zone.upper`
  - both must be numeric and `> 0`
  - must satisfy `lower <= upper`

Trade-level validity classification:
- `missing_trade_levels`: at least one required field for the setup type is absent.
- `invalid_trade_levels`: required field exists but is null, non-numeric, `<= 0`, or logically inconsistent (e.g., `lower > upper`).

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

Forward history completeness rule (strict):
- For all days in `hold_window = [t_trigger+1 .. t_trigger+T_hold_days]`, both `high[t]` and `low[t]` must exist and be valid numerics.
- If any day in the hold window is missing, or `high[t]`/`low[t]` is missing for any day, mark as `insufficient_forward_history`.

---

## 5) Optional MFE/MAE (if computed)
If computed, define relative to entry_price, over the same hold window:

- `mfe_pct = (max(high[t] for t in hold_window) / entry_price - 1) * 100`
- `mae_pct = (min(low[t] for t in hold_window) / entry_price - 1) * 100`

If hold_window is empty (insufficient future history):
- `hit_x`, `mfe_pct`, `mae_pct` are undefined (NaN) and should be reported as insufficient evaluation horizon.

Nullable outcome rule:
- For `reason` in {
  `insufficient_forward_history`,
  `missing_price_series`,
  `missing_trade_levels`,
  `invalid_trade_levels`,
  `invalid_entry_price`,
  `no_trigger`
  }
  all outcome fields remain nullable: `hit_10`, `hit_20`, `hits`, `mfe_pct`, `mae_pct`.
- For `reason = ok`, `hit_10`, `hit_20`, and entries in `hits` are booleans.

---

## 6) Output fields (canonical)
Per evaluated setup instance:
- `t0` (evaluation start day index or timestamp)
- `t_trigger` (or null)
- `entry_price` (or null if no trigger)
- `hit_10` / `hit_20` (or for general thresholds list)
- optional: `mfe_pct`, `mae_pct`
- `reason` in {
  - `ok`
  - `no_trigger`
  - `insufficient_forward_history`
  - `missing_price_series`
  - `invalid_entry_price`
  - `missing_trade_levels`
  - `invalid_trade_levels`
}

Reason precedence (exactly one final `reason` value per evaluated setup):
1. `missing_price_series`
2. `invalid_entry_price`
3. `missing_trade_levels`
4. `invalid_trade_levels`
5. `no_trigger`
6. `insufficient_forward_history`
7. `ok`

Normative interpretation of precedence:
- Apply checks in the listed order and assign the first matching reason.
- `no_trigger` is valid only if no higher-priority data-quality/validity reason matched.
- `ok` is valid only if a trigger was found and the strict forward history rule is satisfied.

---

## 7) Determinism requirements
- Trigger detection must be based only on data up to and including `t_trigger`.
- Evaluation uses only hold-window candles and does not influence live scores.
- Any change in parameters must be reflected in `docs/canonical/CONFIGURATION.md` if it becomes a default.
