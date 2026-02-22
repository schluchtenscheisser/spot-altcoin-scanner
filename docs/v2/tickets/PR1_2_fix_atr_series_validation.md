# PR1.2 — Align `_calc_atr_pct_series` validation with `_calc_atr_pct` (drop anomalous negatives)

## Context / Problem
After PR1.1, 1D ATR-rank uses `_calc_atr_pct_series(...)`. Review found that `_calc_atr_pct_series` can emit **negative ATR% values** in data anomaly cases (e.g. NaN prev close combined with invalid high/low ordering).

Previously (prefix-based) the implementation called `_calc_atr_pct(...)` repeatedly, which enforces a validation rule:
- if computed ATR is negative, it returns **NaN** (and thus those observations are not ranked).

Now `_calc_atr_pct_series` can produce negative values and rank them, silently changing downstream semantics. We must restore the previous behavior: **invalid observations must become NaN**, never negative ATR%.

## Scope
- Only touch `scanner/pipeline/features.py` and unit tests.
- Do not change the ATR% definition for valid data.
- Ensure `_calc_atr_pct_series` produces the same validity behavior as `_calc_atr_pct` in anomaly cases.

## Files to change
- `scanner/pipeline/features.py`
- `tests/`

---

## Required code changes (exact)

### 1) Make TR computation anomaly-safe (per candle)
In `_calc_atr_pct_series(highs, lows, closes, period)`:

For each candle `i >= 1`, compute TR as follows:

**Hard invalidation rules (set `tr[i] = np.nan`):**
- If any of these is NaN: `highs[i]`, `lows[i]`, `closes[i-1]`.
- If `highs[i] < lows[i]` (invalid OHLC ordering).
- If any computed component is NaN.

**Otherwise compute components (float):**
- `c1 = highs[i] - lows[i]`
- `c2 = abs(highs[i] - closes[i-1])`
- `c3 = abs(lows[i] - closes[i-1])`
- `tr[i] = max(c1, c2, c3)`

Notes:
- `tr[0]` must remain `np.nan`.
- Do not log inside `_calc_atr_pct_series`.

### 2) Ensure Wilder ATR cannot become negative; if it does, output NaN
During ATR calculation:
- `atr[period] = mean(tr[1:period+1])` must use `np.nanmean` but ONLY if the window has **no NaNs**; otherwise set `atr[period] = np.nan`.
  - Exact rule: if `np.isnan(tr[1:period+1]).any()` then `atr[period] = np.nan`.

For Wilder smoothing `i = period+1..n-1`:
- If `atr[i-1]` is NaN or `tr[i]` is NaN -> `atr[i] = np.nan`.
- Else compute `atr[i] = ((atr[i-1]*(period-1)) + tr[i]) / period`.
- After computing: if `atr[i] < 0` then set `atr[i] = np.nan`.

This matches the intent of `_calc_atr_pct`: negative ATR is invalid.

### 3) Ensure ATR% cannot be negative; if it is, output NaN
When converting to ATR%:
- If `atr[i]` is NaN -> `atr_pct[i] = np.nan`
- Else if `closes[i] <= 0` -> `atr_pct[i] = np.nan`
- Else `atr_pct[i] = atr[i]/closes[i]*100`
- After computing: if `atr_pct[i] < 0` then set `atr_pct[i] = np.nan`

### 4) Leave `_calc_atr_pct(...)` unchanged
Do not modify `_calc_atr_pct` in this ticket. We only align the series method to match its validity semantics.

---

## Tests (tests-first)

### A) Negative/anomaly case produces NaN (regression test)
Add a unit test that constructs a tiny synthetic OHLC series with:
- At least `period+2` candles (period=14) OR use a smaller period (e.g. 3) for unit-test-only by directly calling `_calc_atr_pct_series(..., period=3)`.
- Include an anomaly candle where `high < low` OR where `close[i-1]` is NaN.
Assert:
- `_calc_atr_pct_series(...)[anomaly_index]` is NaN
- and no element in the returned series is negative:
  - `assert np.all((np.isnan(s)) | (s >= 0))`

### B) Rank path ignores invalid observations
Add a test that:
- builds `atr_pct_series` with some NaNs
- runs `_calc_percent_rank(window_with_nans)`
- asserts it returns a finite number when there are >=2 non-NaN values
- and returns NaN when insufficient non-NaN values exist
(Do not change `_calc_percent_rank`; this test just documents behavior.)

### C) Existing equivalence test still passes
Ensure the PR1.1 test “series last value equals `_calc_atr_pct`” still passes for valid data.

---

## Acceptance criteria
- `_calc_atr_pct_series` never emits negative ATR% values.
- Anomalous candles (NaN prev close, invalid high<low) result in `np.nan` ATR% at those indices (not ranked).
- `atr_pct_rank_*` semantics match pre-PR1.1 behavior for anomaly cases (invalid observations dropped).
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
