> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# PR14 — Breakout Trend 1–5D: restore candidate coverage (5D trigger window + Risk-Off listing + BB-rank scaling)

## Why this PR (critical verification summary)
You currently see **no breakout candidates** primarily because the implementation is too restrictive for the intended 1–5 day holding period:
1) Breakout trigger search is limited to the **last 6×4H closes (~24h)**, which excludes valid “day 2–5” breakouts and continuations.
2) In **BTC Risk-Off**, `_btc_multiplier()` returns `None` unless both liquidity>=15M and RS override are satisfied, which **hard-excludes** most symbols (contrary to the intended “still list in risk-off” behavior).
3) `bb_width_rank_120_4h` is produced as a **percent scale (0..100)** by the FeatureEngine percent-rank helper, but `_bb_score()` treats it as **0..1**, collapsing BB scoring to near-zero for normal ranks.

This PR changes the logic to match the strategy intent you confirmed:
- **1) list candidates for up to 5 days after breakout**
- **2) in BTC Risk-Off still list candidates** (downweight, not exclude)

## Scope
- Focus: `scanner/pipeline/scoring/breakout_trend_1_5d.py` (+ config + tests).
- No changes to FeatureEngine math.
- No changes to other setups unless required by shared config parsing.

## Files to change
- `config/config.yml`
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `tests/`

---

## Required changes (exact)

### 1) Add configurable 4H trigger lookback for Breakout Trend 1–5D (default = 30 bars)
In `config/config.yml` under:
```yaml
scoring:
  breakout_trend_1_5d:
```
Add:
```yaml
    trigger_4h_lookback_bars: 30   # 30×4H = 5 days
```
(If the block already exists, append this key.)

### 2) Expand breakout trigger detection to last N bars (N=trigger_4h_lookback_bars)
In `BreakoutTrend1to5DScorer`:
- Store `self.trigger_4h_lookback_bars` from config (default 30).
- Replace the hardcoded “last 6 bars” behavior in `_find_first_breakout_idx(...)` with last N bars:
  - `start = max(0, len(closes) - self.trigger_4h_lookback_bars)`
  - Scan indices `start .. len(closes)-1` and collect indices where `close > high_20d_1d`.
  - If none -> return `None` (no breakout in last 5 days)
  - Return BOTH:
    - `first_breakout_idx` = earliest index in that window where close>level
    - `last_breakout_idx` = latest index in that window where close>level
Implementation detail:
- Replace `_find_first_breakout_idx` with `_find_breakout_indices(...) -> tuple[first_idx,last_idx] | None`.
- `score_symbol` must use:
  - immediate setup uses **last_breakout_idx** (most recent breakout close within 5 days)
  - retest logic uses **first_breakout_idx** (start of the retest window)

### 3) Retest logic remains 12×4H after first breakout, but must not depend on “fresh 6 bars”
Keep the retest window exactly as currently implemented:
- Search `j in [first_breakout_idx+1 .. first_breakout_idx+12]`
- Zone = ±1% around `high_20d_1d`
- Invalid if any `close < level` in window
No other changes besides using the updated `first_breakout_idx`.

### 4) BTC Risk-Off must downweight (never hard-exclude)
Change `_btc_multiplier(...)` behavior:

**Current behavior (to remove):**
- In Risk-Off: return `None` when liquidity < 15M or RS override false -> excludes symbol entirely

**New behavior (exact):**
- If `btc_regime` missing OR `state == "RISK_ON"` -> return `1.0`
- If `state == "RISK_OFF"`:
  - Compute `rs_override = (alt_r7 - btc_r7) >= 7.5 OR (alt_r3 - btc_r3) >= 3.5`
  - Compute `liq_ok = quote_volume_24h >= self.min_24h_risk_off` (15M default)
  - Return:
    - `0.85` if `rs_override` AND `liq_ok`
    - `0.75` otherwise
- Never return `None` from `_btc_multiplier()`

Also:
- Add output fields to every produced row:
  - `btc_state` (string, from btc_regime.state or "UNKNOWN")
  - `btc_rs_override` (bool)
  - `btc_liq_ok_risk_off` (bool)

### 5) Fix BB-rank scaling to match percent-rank outputs (0..100)
`bb_width_rank_120_4h` comes from percent-rank helper and is expected in **0..100**.
Update `_bb_score(rank)` to treat rank as percent:
- If the incoming `rank` is in 0..1 (defensive), scale it to percent:
  - if `rank <= 1.0`: `rank_pct = rank * 100.0`
  - else `rank_pct = rank`
- Use these thresholds in percent terms:
  - `rank_pct <= 20.0` -> 100
  - `20.0 < rank_pct <= 60.0` -> linear 100 → 40
  - `rank_pct > 60.0` -> 0
(Exactly equivalent to the original 0.2/0.6 logic, but on the correct scale.)

### 6) Keep all existing hard gates unchanged (except BTC kill removal)
Do not change:
- Trend gate: `close_1d > ema20_1d` AND `ema20_1d > ema50_1d`
- ATR gate: `atr_pct_rank_120_1d <= 80.0`
- Momentum gate: `r_7_1d > 0`
- Overextension hard gate: `dist_ema20_pct_1d < 28`
Only change candidate coverage by:
- trigger lookback expansion
- BTC risk-off downweight instead of exclusion
- BB-rank scaling

---

## Tests (tests-first)

### A) Trigger window expansion (5 days)
Create a unit test with synthetic 4H closes such that:
- Breakout happened 4 days ago (i.e., index within last 30 bars), but not within last 6 bars.
Assert:
- `score_symbol` returns at least the immediate row (non-empty), i.e. not filtered out solely due to “not fresh 6 bars”.

### B) BTC Risk-Off does not exclude
Arrange:
- `btc_regime.state="RISK_OFF"`
- `quote_volume_24h` below 15M OR RS override false
Assert:
- `score_symbol` still returns rows (immediate at least)
- Returned row includes `btc_multiplier == 0.75` (default risk-off downweight)
- `btc_state`, `btc_rs_override`, `btc_liq_ok_risk_off` fields exist

### C) BB score scaling works for percent ranks
Assert:
- `_bb_score(20.0) == 100`
- `_bb_score(40.0) == 70`
- `_bb_score(60.0) == 40`
- `_bb_score(61.0) == 0`
Also check defensive path:
- `_bb_score(0.4)` behaves like 40% (≈70)

---

## Acceptance criteria
- Breakout candidates can appear again during Risk-Off regimes (not hard-excluded), but are downweighted.
- Breakouts within the last **5 days** can be listed (not only last 24h).
- BB scoring uses correct rank scale (0..100), no silent collapse.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
