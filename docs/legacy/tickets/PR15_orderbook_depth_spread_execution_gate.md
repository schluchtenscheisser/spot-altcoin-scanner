> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# PR15 — Execution Gate: Orderbook spread + depth filters for 5k–10k USDT trades (MEXC)

## Kurze Erläuterung
`quote_volume_24h_usd` (MEXC-only) ist ein grober Proxy und kann für 5k–10k USDT Trades sowohl **zu restriktiv** sein (gute Setups werden weggeschnitten) als auch **zu lax** (hohes 24h Volumen, aber dünnes Book/hoher Spread). Für professionelle Ausführung ist ein Gate aus **Spread + Orderbook Depth** deutlich besser.

Ziel: Breakout-Kandidaten weiterhin listen (Discovery), aber eine **Execution-Eligible** Kennzeichnung / Gate basierend auf Orderbook-Qualität einführen.

## Scope
- Add deterministic orderbook-based metrics for each symbol:
  - `spread_pct`
  - `depth_bid_1pct_usd`, `depth_ask_1pct_usd`
  - optional: `depth_bid_0_5pct_usd`, `depth_ask_0_5pct_usd`
- Add an Execution Gate that marks rows as executable for 5k–10k trades.
- Do **not** remove existing volume gates in this PR; add execution gating as an additional layer.
- Add tests for calculation + gating behavior.

## Files to change
- `config/config.yml`
- `scanner/pipeline/features.py` **or** a new module under `scanner/pipeline/liquidity.py` (preferred if you want separation)
- `scanner/pipeline/scoring/breakout_trend_1_5d.py`
- `scanner/pipeline/output.py` (to print/emit the new fields)
- `scanner/pipeline/excel_output.py` (to include new columns)
- `tests/`

---

## Config changes (exact)
Add a new config block (defaults tuned for 5k–10k USDT trades):

```yaml
execution_gates:
  mexc_orderbook:
    enabled: true

    # Spread gate: (best_ask - best_bid) / mid * 100
    max_spread_pct: 0.15

    # Depth gates use USD notionals within a band around mid.
    # Each side must satisfy the minimum.
    bands_pct:
      - 0.5
      - 1.0

    min_depth_usd:
      "0.5": 80000
      "1.0": 200000
```

Notes:
- Values are **USD notionals** (USDT treated as USD).
- Gate condition uses `min(bid_depth, ask_depth)` per band.

---

## Data source & assumptions (exact)
- Use the existing MEXC orderbook snapshot already available in the pipeline (do not add a new API dependency).
- Use the same symbol naming as existing pipeline (`MORPHOUSDT` etc).
- Orderbook levels are assumed as lists of `(price, quantity)` in base units.
- Notional per level = `price * quantity`.

---

## Required code changes (exact)

### 1) Compute spread and depth metrics from orderbook
Implement a helper function (location: `scanner/pipeline/liquidity.py` preferred, otherwise `features.py`):

```python
def compute_orderbook_metrics(orderbook: dict, bands_pct: list[float]) -> dict:
    ...
```

**Inputs:**
- `orderbook["bids"]`: list of [price, qty] OR list of (price, qty)
- `orderbook["asks"]`: list of [price, qty] OR list of (price, qty)
- `bands_pct`: e.g. [0.5, 1.0]

**Definitions:**
- `best_bid = max(bids.price)`
- `best_ask = min(asks.price)`
- `mid = (best_bid + best_ask) / 2`

- `spread_pct = (best_ask - best_bid) / mid * 100` if `mid > 0` else NaN

Depth within ±X% around mid:
- For each `band` in `bands_pct`:
  - `bid_cutoff = mid * (1 - band/100)`
  - `ask_cutoff = mid * (1 + band/100)`
  - `depth_bid_{band}_usd = sum(price*qty for bid where price >= bid_cutoff)`
  - `depth_ask_{band}_usd = sum(price*qty for ask where price <= ask_cutoff)`

**Edge cases (exact):**
- If bids or asks missing/empty -> all metrics NaN and set `orderbook_ok = False`.
- If best_bid <= 0 or best_ask <= 0 -> metrics NaN and `orderbook_ok=False`.
- Must be deterministic and not raise.

Return dict must include keys:
- `spread_pct`
- `depth_bid_0_5pct_usd`, `depth_ask_0_5pct_usd`
- `depth_bid_1pct_usd`, `depth_ask_1pct_usd`
- `orderbook_ok` (bool)

### 2) Attach metrics to each scored row (Breakout Trend 1–5D)
In `scanner/pipeline/scoring/breakout_trend_1_5d.py`:
- For each produced setup row, include:
  - `spread_pct`
  - depth fields for 0.5% and 1.0%
  - `execution_gate_pass` (bool)
  - `execution_gate_fail_reasons` (list of strings)

### 3) Execution Gate logic (exact)
If `execution_gates.mexc_orderbook.enabled == true`, then:
- `execution_gate_pass` is true iff:
  - `orderbook_ok == True`
  - `spread_pct <= max_spread_pct`
  - For each band configured:
    - `min(depth_bid_band_usd, depth_ask_band_usd) >= min_depth_usd[band]`

Fail reasons enum strings (only these values allowed):
- `ORDERBOOK_MISSING`
- `SPREAD_TOO_WIDE`
- `DEPTH_TOO_LOW_0_5`
- `DEPTH_TOO_LOW_1_0`

If `enabled == false`:
- `execution_gate_pass = True`
- `execution_gate_fail_reasons = []`

### 4) Do not remove discovery candidates
In this PR, do not exclude rows from the report based on `execution_gate_pass`.
Instead:
- Keep listing them, but mark execution pass/fail in report + excel.
(You can implement a later PR to add an optional “execution_only” filter.)

### 5) Reporting & Excel output
- `scanner/pipeline/output.py`: include these fields/columns near the top of each row display:
  - `execution_gate_pass`, `spread_pct`, `depth_bid_1pct_usd`, `depth_ask_1pct_usd`
- `scanner/pipeline/excel_output.py`: add columns for:
  - `execution_gate_pass`, `spread_pct`
  - `depth_bid_0_5pct_usd`, `depth_ask_0_5pct_usd`
  - `depth_bid_1pct_usd`, `depth_ask_1pct_usd`

---

## Tests (tests-first)

### A) Metric calculation correctness
Create unit tests using a small synthetic orderbook:
- bids: [[99, 10], [98, 10]]
- asks: [[101, 10], [102, 10]]
Mid=100, spread_pct = 2.0
Depth within 1%:
- bid cutoff 99 -> include 99*10 = 990
- ask cutoff 101 -> include 101*10 = 1010
Assert exact outputs.

### B) Execution gate pass/fail
Configure thresholds in test:
- max_spread_pct=2.5
- min_depth_1pct_usd=900
Assert:
- gate passes (depth and spread ok)

Then set:
- max_spread_pct=1.0 -> gate fails with `SPREAD_TOO_WIDE`

Then set depth threshold too high -> fails with `DEPTH_TOO_LOW_1_0`.

### C) Row includes fields
Test that a scored breakout row includes:
- `execution_gate_pass`, `spread_pct`, `depth_*` keys present.

---

## Acceptance criteria
- Orderbook spread/depth metrics computed deterministically.
- Breakout Trend 1–5D rows include execution gate fields.
- Reports + Excel include the new execution fields.
- No rows are removed from discovery lists due to execution gate in this PR.
- `python -m pytest -q` passes.

## Close-out / Archive step (mandatory)
After merge:
1) Move this ticket file to `docs/legacy/v2/tickets/` (same filename).
2) Update `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`.
