# PR6 — FeatureEngine: Guard ATR seed/reseed `nanmean` on all-NaN windows (no warning spam)

## Short explanation
Your new ATR reseed logic calls `np.nanmean(...)` on windows that can be **all NaN** (common with sparse/malformed OHLC). NumPy emits `RuntimeWarning: Mean of empty slice` for each such call, which can spam logs/stderr and can fail CI in environments treating warnings as errors. Fix: detect “all-NaN” windows and skip `nanmean` (set ATR to NaN) before calling it. Apply to both initial seed and reseed paths.

## Scope
- Only: `scanner/pipeline/features.py` and tests.
- No change to valid-data ATR% values.
- Preserve: “no negative ATR/ATR%” rule and anomaly-to-NaN behavior.

## Files to change
- `scanner/pipeline/features.py`
- `tests/`

---

## Required code changes (exact)

### 1) Initial seed: guard `np.nanmean`
In `_calc_atr_pct_series(...)`, when computing the initial seed at index `period`:
- `seed_window = tr[1:period+1]`
- If `np.isnan(seed_window).all()` -> set `atr[period] = np.nan` **without calling** `np.nanmean`.
- Else `atr[period] = np.nanmean(seed_window)`
- After computing, keep existing validation:
  - if `atr[period] < 0` -> `np.nan`

### 2) Reseed: guard `np.nanmean`
In the reseed path (when `atr[i-1]` is NaN and you try to reseed using a recent TR window):
- `reseed_window = tr[start:i+1]` (whatever your implementation uses)
- If `reseed_window.size == 0` -> `atr[i] = np.nan`
- Else if `np.isnan(reseed_window).all()` -> `atr[i] = np.nan` **without calling** `np.nanmean`.
- Else `seed = np.nanmean(reseed_window)` and use it.
- Keep existing validation:
  - if `atr[i] < 0` -> `np.nan`

### 3) No warnings
Do not use `warnings.filterwarnings` globally. Fix must be by guarding the call.

---

## Tests (tests-first)

### A) No RuntimeWarning on all-NaN seed window
Create a unit test that calls `_calc_atr_pct_series(..., period=3)` with TR seed window all NaN.
Example arrangement (one simple way):
- `highs[1] = np.nan`, `lows[1] = np.nan`, and/or invalid `high<low` so `tr[1]` becomes NaN
- Ensure `tr[1:4]` all NaN (seed window)
Assert:
- No `RuntimeWarning` is raised (use `pytest.warns(None)` or `warnings.catch_warnings(record=True)`).
- Output array is returned and contains NaNs as expected.

### B) No RuntimeWarning on all-NaN reseed window
Create a unit test where ATR becomes NaN and reseed window is all NaN for some i, then later valid bars exist.
Assert:
- No `RuntimeWarning` is raised.
- Later valid bars can still yield finite ATR% if the data allows.

---

## Acceptance criteria
- No `RuntimeWarning: Mean of empty slice` is emitted from ATR seed or reseed.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
