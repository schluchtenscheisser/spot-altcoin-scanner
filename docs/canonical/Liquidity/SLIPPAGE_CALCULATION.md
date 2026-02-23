# Liquidity — Slippage Calculation (Top-K Orderbook) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_SLIPPAGE_CALCULATION
status: canonical
top_k_input: 200
notional_usd_default: 20000
outputs:
  - spread_bps
  - slippage_bps
  - liquidity_insufficient_depth
determinism:
  rounding_decimals: 2
  mid_price: "0.5*(best_bid + best_ask)"
```

## 1) Inputs
- Orderbook bids/asks (Top-K levels), each level:
  - price
  - quantity (base)
- Notional in USD (default 20,000 USD)
- Mid price:
  - `mid = 0.5*(best_bid + best_ask)`

## 2) Spread
Canonical (bps):
- `spread_pct = ((best_ask / best_bid) - 1) * 100`
- `spread_bps = spread_pct * 100`
- Round to 2 decimals.

## 3) Slippage (BUY vs mid) — deterministic fill simulation
Goal: compute execution price for a BUY order sized by `notional_usd`.

### 3.1 Convert notional to target base quantity
- `target_base = notional_usd / mid`

### 3.2 Walk the ask side (ascending price)
For each ask level i:
- available_base_i
- price_i

Consume base quantity from the top until either:
- filled_base >= target_base  (success)
- ran out of levels (insufficient depth)

Compute weighted average execution price:
- `exec_price = sum(consumed_base_i * price_i) / sum(consumed_base_i)`

### 3.3 Slippage definition (bps)
- `slippage_pct = ((exec_price / mid) - 1) * 100`
- `slippage_bps = slippage_pct * 100`
- Round to 2 decimals.

## 4) Insufficient depth
If `filled_base < target_base` after processing top K asks:
- `liquidity_insufficient_depth = true`
- slippage is missing/invalid for grading and treated as worst in re-rank.

## 5) Notes
- This spec intentionally defines BUY-side slippage vs mid. If SELL-side is needed later, it must be explicitly specified (do not infer).
