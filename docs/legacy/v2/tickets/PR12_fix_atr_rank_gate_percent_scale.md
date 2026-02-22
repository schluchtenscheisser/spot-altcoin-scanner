# PR12 — Scoring: Fix ATR rank gate threshold to match 0–100 percent scale

## Kurze Erläuterung
`atr_pct_rank_120` wird im FeatureEngine auf einer **0–100 Skala** produziert ( `_calc_percent_rank` multipliziert mit 100; Tests erwarten z.B. 83.3333). Das Gate im Breakout Trend 1–5D vergleicht aber fälschlich gegen `0.80` (als wäre es 0..1). Dadurch werden fast alle Symbole fälschlich ausgeschlossen (typische Werte 40–90 sind >0.80). Fix: Gate muss auf der gleichen Skala arbeiten (`<= 80.0`).

## Scope
- Nur Breakout Trend 1–5D Gates korrigieren.
- Keine Änderung an `_calc_percent_rank` (Skala bleibt 0..100).
- Tests hinzufügen, damit Skalen-Mismatch nicht zurückkommt.

## Files to change
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `docs/v2/20_FEATURE_SPEC.md` **nur falls** dort fälschlich 0.80 steht (ansonsten nicht ändern)
- `tests/`

---

## Required code changes (exact)

### 1) ATR gate uses percent scale (0..100)
In `breakout_trend_1_5d.py` (Hard Gate):
- PASS if `atr_pct_rank_120_1d <= 80.0`
- FAIL if `atr_pct_rank_120_1d > 80.0`
- Boundary: `80.0` passes.

If the gate currently uses `0.80`, replace it with `80.0`.

### 2) Ensure config/spec consistency (optional)
If there is a config key like `max_rank` currently set to `0.80`, change it to `80.0` and update code accordingly.
If config already uses percent values, keep as-is.
The implementation must be consistent end-to-end: **use one scale only (0..100)**.

---

## Tests (tests-first)

### A) Boundary tests for percent scale
Add unit tests:
- `atr_pct_rank_120_1d = 80.0` -> must PASS
- `atr_pct_rank_120_1d = 80.0001` -> must FAIL
- `atr_pct_rank_120_1d = 50.0` -> must PASS

## Acceptance criteria
- Breakout Trend 1–5D candidates are not accidentally filtered out by scale mismatch.
- Tests pass.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
