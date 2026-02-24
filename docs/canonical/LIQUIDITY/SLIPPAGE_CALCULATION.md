# Liquidity — Slippage Calculation (Top-K Orderbook) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_SLIPPAGE_CALCULATION
status: canonical
top_k_input: 200
notional_usd_default: 20000
rounding:
  decimals: 2
  mode: "half_up"
  applies_to: ["spread_bps", "slippage_bps"]
liquidity_grade_thresholds_bps_default:
  A_max: 20
  B_max: 50
  C_max: 100
  D: "> C_max OR insufficient_depth"
outputs:
  - spread_bps
  - slippage_bps
  - liquidity_insufficient_depth
  - liquidity_grade
```

## 1) Inputs
- Orderbook bids/asks (Top-K levels), each level:
  - price
  - quantity (base)
- Notional in USD (default 20,000 USD)
- Mid price:
  - `mid = 0.5*(best_bid + best_ask)`

## 2) Spread (bps)
- `spread_pct = ((best_ask / best_bid) - 1) * 100`
- `spread_bps_raw = spread_pct * 100`
- `spread_bps = round_half_up(spread_bps_raw, 2)`

## 3) Slippage (BUY vs mid) — deterministic fill simulation
### 3.1 Convert notional to target base quantity
- `target_base = notional_usd / mid`

### 3.2 Walk the ask side (ascending price)
Consume base quantity from asks until filled or levels exhausted.

Weighted average execution price:
- `exec_price = sum(consumed_base_i * price_i) / sum(consumed_base_i)`

### 3.3 Slippage definition (bps)
- `slippage_pct = ((exec_price / mid) - 1) * 100`
- `slippage_bps_raw = slippage_pct * 100`
- `slippage_bps = round_half_up(slippage_bps_raw, 2)`

## 4) Insufficient depth
If `filled_base < target_base` after processing top K asks:
- `liquidity_insufficient_depth = true`
- `liquidity_grade = "D"`

## 5) Liquidity grade (A/B/C/D)
If `liquidity_insufficient_depth == true` → grade D.

Else grade is based on `slippage_bps`:
- A if `slippage_bps <= 20`
- B if `20 < slippage_bps <= 50`
- C if `50 < slippage_bps <= 100`
- D if `slippage_bps > 100`

## 6) Rounding rule (canonical)
`round_half_up(x, 2)` means:
- round to 2 decimals with halves rounded away from zero (not bankers rounding).
- rounding is applied to the final reported bps values only.

