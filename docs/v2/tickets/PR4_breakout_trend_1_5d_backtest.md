# PR4 — Breakout Trend 1–5D: Backtest Runner (4H entry/exit, partial+trail, time stop)

## Scope
Extend `scanner/pipeline/backtest_runner.py` to backtest the two new setups using 4H rules:
- Immediate entry: open(next 4H) after trigger candle close
- Retest entry: limit at breakout level, filled in retest-valid candle
- Stop: `stop = entry - 1.2 * ATR_abs_4h`
- Partial: 40% at 1.5R
- Trailing: activate only after partial; exit when 4H close < EMA20(4H); exit at open(next 4H)
- Time stop: 168h (7 days); exit at open(next 4H) after expiry
- Intra-candle priority: STOP > PARTIAL > TRAIL

## Files to change
- `scanner/pipeline/backtest_runner.py`
- `tests/`

## Tests (tests-first)
Deterministic synthetic 4H series tests validating:
- STOP > PARTIAL > TRAIL priority in same candle
- trailing only active after partial
- time stop exit at open(next 4H) after 168h

## Acceptance criteria
- Backtest supports both new setup IDs.
- Deterministic tests pass.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
