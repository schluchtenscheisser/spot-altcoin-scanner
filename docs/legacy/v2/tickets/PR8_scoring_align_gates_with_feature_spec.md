# PR8 — Scoring: Align Breakout Trend 1–5D hard gates with canonical feature spec

## Short explanation
`scanner/pipeline/scoring/breakout_trend_1_5d.py` currently uses different hard gates than the canonical spec in `docs/v2/20_FEATURE_SPEC.md`:
- Trend gate uses `close_1d > ema50_1d` but spec requires `close_1d > ema20_1d` (and `ema20_1d > ema50_1d`).
- ATR gate rejects when `atr_pct_rank_120 < 0.5`, but spec requires `atr_pct_rank_120_1d <= 0.80` (i.e., reject when >0.80).
This materially changes eligibility and ranking results. Fix must match the doc exactly.

## Scope
- Only adjust gating logic to match spec.
- Add tests to prevent drift.

## Files to change
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `tests/`

---

## Required code changes (exact)

### 1) Trend gate
In `score_symbol` (or equivalent):
Replace trend validation with:
- `ema20_1d > ema50_1d`
- `close_1d > ema20_1d`
If either fails -> symbol/setup invalid.

### 2) ATR gate
Replace ATR validation with:
- PASS if `atr_pct_rank_120_1d <= 0.80`
- FAIL if `atr_pct_rank_120_1d > 0.80`
(Ensure boundary `0.80` passes.)

### 3) Do not introduce new gates
Do not add additional filters in this PR.

---

## Tests (tests-first)

### A) Trend gate correctness
Construct a minimal feature dict:
- Case 1: `close_1d > ema20_1d`, `ema20_1d > ema50_1d` -> must pass
- Case 2: `close_1d <= ema20_1d` -> must fail
- Case 3: `ema20_1d <= ema50_1d` -> must fail

### B) ATR gate boundary correctness
- `atr_pct_rank_120_1d = 0.80` -> must pass
- `atr_pct_rank_120_1d = 0.800001` -> must fail

---

## Acceptance criteria
- Gating logic matches `docs/v2/20_FEATURE_SPEC.md` exactly.
- Tests pass.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
