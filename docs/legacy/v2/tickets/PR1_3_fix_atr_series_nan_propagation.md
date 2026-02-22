# PR1.3 — Prevent NaN propagation in `_calc_atr_pct_series` (match scalar `_calc_atr_pct` behavior)

## Short explanation
The current `_calc_atr_pct_series` initialization requires the first ATR window (first `period` TR values) to contain **no NaNs**. If there is **any** early anomaly (e.g. one NaN high/low), `atr[period]` becomes NaN and the Wilder smoothing loop propagates NaN forward (`atr[i]` stays NaN because `atr[i-1]` is NaN).

This causes a regression:
- `atr_pct_rank_*` becomes NaN for otherwise valid series
- while scalar `_calc_atr_pct` still returns a finite value because it uses `np.nanmean(tr[:period])` for initialization.

Goal: Make `_calc_atr_pct_series` handle early NaNs like the scalar path: **do not drop the whole series** due to one early NaN; keep rank coverage consistent.

## Scope
- Only touch `scanner/pipeline/features.py` and unit tests.
- Do not change ATR% for fully-valid data.
- Fix NaN handling so series behavior aligns with scalar `_calc_atr_pct` for “some NaNs present” cases.

## Files to change
- `scanner/pipeline/features.py`
- `tests/`

---

## Required code changes (exact)

### 1) Change initial ATR seeding to use `np.nanmean` (like scalar)
In `_calc_atr_pct_series(...)`, the initial ATR seed at index `period` must be computed as:

- `seed_window = tr[1:period+1]`
- `atr[period] = np.nanmean(seed_window)`

**Rules:**
- If `np.isnan(atr[period])` (i.e. all NaN in seed_window) then leave `atr[period] = np.nan`.
- If `atr[period] < 0` then set `atr[period] = np.nan` (validation retained).
- Remove any gate of the form “if any NaN in seed window then atr[period]=NaN”. That gate caused the regression.

This must match `_calc_atr_pct` which initializes using mean over the first `period` TR values while tolerating NaNs via `nanmean`.

### 2) Update Wilder smoothing to avoid NaN cascade
For `i in range(period+1, n)`:

- If `np.isnan(atr[i-1])`:
  - **Do not** permanently propagate NaN.
  - Instead attempt to **re-seed** ATR at `i` using the most recent `period` TR values:
    - `seed_window = tr[max(1, i-period+1): i+1]` (length <= period)
    - `seed = np.nanmean(seed_window)`
    - If `seed` is NaN -> `atr[i] = np.nan`
    - Else `atr[i] = seed`
- Else if `np.isnan(tr[i])`:
  - Keep last ATR unchanged: `atr[i] = atr[i-1]`  (missing TR should not kill the series)
- Else:
  - Standard Wilder update:
    - `atr[i] = ((atr[i-1] * (period - 1)) + tr[i]) / period`

After any assignment:
- If `atr[i] < 0` -> set `atr[i] = np.nan`

Notes:
- This preserves continuity and prevents a single early NaN from killing the entire ATR history.
- This keeps semantics consistent with the scalar path which tolerates missing TRs via `nanmean` during seeding.

### 3) ATR% conversion stays as in PR1.2 (no negatives)
Keep PR1.2 rules:
- If `atr[i]` is NaN -> `atr_pct[i] = NaN`
- If `closes[i] <= 0` -> NaN
- Else `atr_pct[i] = atr[i]/closes[i]*100`
- If `atr_pct[i] < 0` -> NaN

### 4) Do not change `_calc_atr_pct(...)`
Leave scalar function unchanged. This ticket aligns series behavior to it.

---

## Tests (tests-first)

### A) Early NaN does not kill the series (regression)
Create a test using a small `period` (e.g. `period=3`) by calling `_calc_atr_pct_series(..., period=3)` directly.

Arrange:
- Build OHLC arrays length >= 8
- Insert exactly one NaN in an early TR component (e.g. `highs[2] = np.nan`), but ensure later candles are valid.

Assert:
- `atr_pct_series` has NaNs during warm-up as expected, but **later indices** (e.g. last index) are **finite**.
- `atr_pct_series` contains no negative values.

### B) Series last value matches scalar for “some NaNs” case
Arrange:
- Same dataset as in A but with `period=3`.
- Compute scalar last value by calling `_calc_atr_pct(symbol, highs, lows, closes, period=3)`.
- Compute series last value with `_calc_atr_pct_series(..., period=3)[-1]`.

Assert:
- If scalar returns a finite number, series last value must match within tolerance.
- If scalar returns NaN, series may be NaN too (no stricter requirement).

### C) Rank remains computable if enough non-NaNs exist
Arrange:
- Take the last `lookback` window of `atr_pct_series` with some NaNs but >=2 finite values.
Assert:
- `_calc_percent_rank(window)` returns a finite number (not NaN).

---

## Acceptance criteria
- A single early NaN in TR history no longer forces all subsequent ATR/ATR% values to NaN.
- `_calc_atr_pct_series(...)[-1]` matches scalar `_calc_atr_pct(...)` for cases where scalar is finite, including “some NaNs present” datasets.
- `atr_pct_rank_*` coverage regains consistency (no unnecessary NaN ranks).
- No negative ATR or ATR% values are emitted.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
