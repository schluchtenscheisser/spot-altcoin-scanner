# PR1.1 — Fix ATR rank performance + suppress warm-up warning spam (FeatureEngine)

## Context / Problem
Current implementation of `atr_pct_rank_*` in `scanner/pipeline/features.py` is **O(n²)** per symbol because it loops over every candle and calls `_calc_atr_pct()` on growing prefixes. This also spams logs with repeated warm-up warnings (`insufficient candles for ATR14`) for the first 14 iterations of every symbol.

Goal: Make ATR rank computation **O(n)** per symbol and eliminate repeated warm-up warnings, **without changing the meaning** of ATR% or ATR rank.

## Scope
- Only touch `scanner/pipeline/features.py` and corresponding unit tests.
- No behavior changes to existing outputs except:
  - performance improvement
  - removal of repeated warm-up warnings caused by prefix recalculation
- Keep existing public feature keys unchanged.

## Files to change
- `scanner/pipeline/features.py`
- `tests/` (add or adjust tests accordingly)

---

## Required code changes (exact)

### 1) Add a new helper: `_calc_atr_pct_series(...)`
In `FeatureEngine`, add:

`def _calc_atr_pct_series(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> np.ndarray:`

**Output:**
- Returns a `np.ndarray` of length `len(closes)` containing ATR% per candle.
- For indices `< period`, values must be `np.nan` (warm-up).
- For indices `>= period`, values must be ATR% computed using **Wilder smoothing**, consistent with `_calc_atr_pct()`.

**Algorithm (must match existing `_calc_atr_pct` logic):**
1. If `len(highs) < period + 1` return an array of NaNs of length `len(closes)` (no logging inside this function).
2. Compute true range array `tr` (float) length `n` with:
   - `tr[0] = np.nan`
   - For `i in [1..n-1]`:
     - `tr[i] = max(highs[i]-lows[i], abs(highs[i]-closes[i-1]), abs(lows[i]-closes[i-1]))`
3. Compute ATR array `atr` length `n` with NaNs.
   - Initial ATR at index `period`:
     - `atr[period] = mean(tr[1:period+1])`
   - For `i in [period+1..n-1]` (Wilder):
     - `atr[i] = ((atr[i-1]*(period-1)) + tr[i]) / period`
4. Convert to ATR% series `atr_pct` length `n`:
   - For `i in [period..n-1]`:
     - If `closes[i] > 0`: `atr_pct[i] = (atr[i] / closes[i]) * 100`
     - Else `atr_pct[i] = np.nan`
   - For `i < period`: `np.nan`
5. Return `atr_pct`.

**Important:**
- Do not log warnings inside `_calc_atr_pct_series`.
- Keep `_calc_atr_pct()` intact (it may keep its current logging), but it must no longer be called in a per-prefix loop.

### 2) Replace the O(n²) loop for ATR rank in `_compute_timeframe_features` (1D block)
In `_compute_timeframe_features`, inside:

```py
if timeframe == "1d":
    atr_rank_lookback = self._get_atr_rank_lookback("1d")
    atr_series = np.full(len(closes), np.nan)
    for i in range(len(closes)):
        atr_series[i] = self._calc_atr_pct(symbol, highs[:i+1], lows[:i+1], closes[:i+1], 14)
    atr_rank_window = atr_series[-atr_rank_lookback:]
    f[f"atr_pct_rank_{atr_rank_lookback}"] = self._calc_percent_rank(atr_rank_window)
```

**Replace with:**
- `atr_rank_lookback = self._get_atr_rank_lookback("1d")`
- `atr_pct_series = self._calc_atr_pct_series(highs, lows, closes, 14)`
- `atr_rank_window = atr_pct_series[-atr_rank_lookback:]`
- `f[f"atr_pct_rank_{atr_rank_lookback}"] = self._calc_percent_rank(atr_rank_window)`

### 3) Keep percent-rank behavior unchanged
Do not change `_calc_percent_rank`. It currently returns a 0..100 scale. Keep that.

---

## Tests (tests-first)

### A) Series vs single-value equivalence (numeric)
Add a unit test that verifies:
- For a synthetic OHLC series with length >= `period + 5`:
  - `atr_pct_series = _calc_atr_pct_series(highs, lows, closes, 14)`
  - `atr_pct_series[-1]` equals `_calc_atr_pct(symbol, highs, lows, closes, 14)` within a small tolerance (e.g. `1e-9` or `1e-6`).
- Ensure `atr_pct_series[:14]` are NaN.

### B) No repeated warm-up warnings from rank computation
Add a test that runs `_compute_timeframe_features(... timeframe="1d" ...)` with a small dataset where warmup exists and assert via `caplog`:
- No more than **one** “insufficient candles for ATR14” warning is emitted for that symbol OR (preferred) **zero** warnings from the rank path, since `_calc_atr_pct_series` must not log.
  - (If existing code logs other warnings, scope your assertion to the specific ATR14 message substring.)

### C) Performance sanity (optional but useful)
Optional: a test that ensures `_calc_atr_pct_series` runs in linear time is hard to enforce in unit tests, so skip strict timing. The existence of no prefix loop is enough.

---

## Acceptance criteria
- ATR rank computation is **O(n)** per symbol (no per-prefix `_calc_atr_pct` loop remains).
- `atr_pct_rank_*` values remain semantically consistent with prior implementation.
- Warm-up warning spam for ATR14 is eliminated from ATR rank computation.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
