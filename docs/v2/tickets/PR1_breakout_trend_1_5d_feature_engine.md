# PR1 — Breakout Trend 1–5D: Feature Engine Extensions

## Scope
Implement feature additions required by Breakout Trend 1–5D:
- Volume SMA periods per timeframe: 1D=20, 4H=20
- `1d.atr_pct_rank_120`
- `4h.bb_width_pct`
- `4h.bb_width_rank_120`

## Files to change
- `config/config.yml`
- `scanner/pipeline/features.py`
- `tests/` (new unit tests)

## Config changes (exact)
Add or update:
```yaml
features:
  volume_sma_periods:
    1d: 20
    4h: 20
  # keep legacy key for compat; new logic must prefer volume_sma_periods
  volume_sma_period: 7

  bollinger:
    period: 20
    stddev: 2.0
    rank_lookback_bars:
      1d: 120
      4h: 120

  atr_rank_lookback_bars:
    1d: 120
```

## Exact feature definitions
### Volume SMA periods
Update `FeatureEngine._get_volume_period_for_timeframe(timeframe)` to resolve in this order:
1) `features.volume_sma_periods.<timeframe>`
2) else legacy `features.volume_sma_period`
3) else default 14

### ATR% rank (1D)
Compute `atr_pct_rank_120` as percent rank of `atr_pct` over last 120 closed 1D bars (ignore NaNs), using last element as current.
Store: `features["1d"]["atr_pct_rank_120"]`.

### Bollinger width (4H)
Using last closed 4H close series:
- period=20, std=2.0
- `bb_middle = SMA(close, 20, include_current=True)`
- `bb_std = std(close[-20:])` (population std ok; deterministic)
- `bb_upper = bb_middle + 2.0 * bb_std`
- `bb_lower = bb_middle - 2.0 * bb_std`
- `bb_width_pct = ((bb_upper - bb_lower) / bb_middle) * 100` if `bb_middle>0` else NaN
Store: `features["4h"]["bb_width_pct"]`.

### Bollinger width rank (4H)
Compute `bb_width_rank_120` as percent rank of `bb_width_pct` over last 120 closed 4H bars.
Store: `features["4h"]["bb_width_rank_120"]`.

## Tests (tests-first)
Add deterministic unit tests:
1) Percent-rank helper: duplicates, NaNs, insufficient history.
2) Bollinger width: synthetic close series produces expected width (use a tight numeric tolerance).
3) Config parsing: volume_sma_periods overrides legacy key for 1D and 4H.

## Acceptance criteria
- New keys exist in computed feature dicts:
  - `1d.atr_pct_rank_120`
  - `4h.bb_width_pct`
  - `4h.bb_width_rank_120`
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
