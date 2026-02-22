# PR13 — Backtest metrics: Count trades from executed entries, not triggered fallback

## Kurze Erläuterung
Die aktuelle Fallback-Logik setzt in manchen Fällen `trades = triggered`, obwohl keine Ausführung stattfand (z.B. Retest invalidiert vor Fill: `triggered=True`, `entry_price=None`, `trade_status="NO_TRADE"`). Dadurch werden `trades_count` und `trade_rate_on_signals` aufgeblasen und Experimente werden systematisch zu “optimistisch”. Fix: Trades nur zählen, wenn ein Entry tatsächlich ausgeführt wurde (Execution), nicht wenn nur ein Signal/Trigger vorlag.

## Scope
- Nur `scanner/pipeline/backtest_runner.py` und Tests.
- Output-Struktur beibehalten, aber Metriken korrekt ableiten.

## Files to change
- `scanner/pipeline/backtest_runner.py`
- `tests/`

---

## Required code changes (exact)

### 1) Define what counts as an executed trade
A row counts as an executed trade iff:
- `trade_status == "TRADE"`
OR (if you don't have that flag consistently):
- `entry_price is not None` AND `entry_time is not None` AND `position_size > 0` (or equivalent)

Do **not** treat `triggered==True` as executed trade.

### 2) Fix summary metrics
In the backtest summary computation:
- `signals_count` = number of setup rows evaluated (triggered candidates).
- `trades_count` = count of rows where executed trade condition is true.
- `trade_rate_on_signals = trades_count / signals_count` (guard division by zero).

Remove any logic equivalent to `if not has_trade_status: trades = triggered`.

### 3) Keep NO_TRADE rows in outputs
NO_TRADE rows still contribute to `signals_count`, but not to `trades_count`.

---

## Tests (tests-first)

### A) Triggered NO_TRADE does not count as trade
Arrange 1 row:
- `triggered=True`, `trade_status="NO_TRADE"`, `entry_price=None`
Assert:
- `signals_count == 1`
- `trades_count == 0`
- `trade_rate_on_signals == 0.0`

### B) Executed TRADE counts
Add a second row:
- `trade_status="TRADE"` and `entry_price` non-None
Assert:
- `signals_count == 2`
- `trades_count == 1`
- `trade_rate_on_signals == 0.5`

## Acceptance criteria
- Backtest summary counts executed trades only.
- Trigger-only / invalidated / not-filled rows do not inflate trade metrics.
- Tests pass.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
