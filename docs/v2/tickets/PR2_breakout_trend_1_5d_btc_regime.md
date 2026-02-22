# PR2 — Breakout Trend 1–5D: BTC Regime Computation + Exposure

## Scope
Compute BTC regime once per run (BTCUSDT from MEXC) and expose it prominently:
- Markdown report: BTC block at the very top.
- Excel summary sheet: BTC block at the top (A1..B6).
- JSON report: top-level `btc_regime` object.

## Files to change
- `scanner/pipeline/regime.py` (new)
- `scanner/pipeline/__init__.py`
- `scanner/pipeline/output.py`
- `scanner/pipeline/excel_output.py`
- `tests/`

## Exact regime logic (no interpretation)
Let BTC 1D features be computed like any other symbol:
- `btc_risk_on = (btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)`

If risk-on:
- `state = "RISK_ON"`
- `multiplier_risk_on = 1.00`

Else:
- `state = "RISK_OFF"`
- `multiplier_risk_off = 0.85`

Report payload must include:
```json
"btc_regime": {
  "state": "RISK_ON" | "RISK_OFF",
  "multiplier_risk_on": 1.0,
  "multiplier_risk_off": 0.85,
  "checks": {
    "close_gt_ema50": true/false,
    "ema20_gt_ema50": true/false
  }
}
```

## BTC block placement (hard requirement)
### Markdown
At very top, before rankings:
- Header: `BTC Regime`
- Fields: state, multiplier_risk_on, multiplier_risk_off, checks

### Excel Summary (explicit cells)
- `A1="BTC Regime"`
- `A2="State"`, `B2=<state>`
- `A3="Multiplier (Risk-On)"`, `B3=1.00`
- `A4="Multiplier (Risk-Off)"`, `B4=0.85`
- `A5="close>ema50"`, `B5=<bool>`
- `A6="ema20>ema50"`, `B6=<bool>`

## Tests (tests-first)
- Unit test risk-off: close < ema50 -> RISK_OFF
- Unit test risk-on: close>ema50 and ema20>ema50 -> RISK_ON
- Markdown test: BTC block appears before Global Top20 header
- Excel test: Summary sheet `A1 == "BTC Regime"`

## Acceptance criteria
- BTC regime is computed and attached to report payloads.
- BTC block placement is correct in markdown and excel.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge of this ticket:
1) Move **this** ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md` so the next Codex session can continue without context loss.
