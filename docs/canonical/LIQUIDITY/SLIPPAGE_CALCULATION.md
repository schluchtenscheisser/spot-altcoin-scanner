# Liquidity — Slippage & Spread Calculation (Top-K Orderbook) (Canonical)

## Machine Header (YAML)
```yaml
id: LIQ_SLIPPAGE_CALCULATION
status: canonical
top_k_input: 200
notional_usdt_default: 20000
mid_price: "0.5*(best_bid + best_ask)"
spread_definition:
  denominator: mid
rounding:
  decimals: 6
  mode: "half_even"   # Python round()
  applies_to: ["spread_bps", "slippage_bps"]
liquidity_grade_thresholds_bps_default:
  A_max: 20
  B_max: 50
  C_max: 100
  D: "> C_max OR insufficient_depth"
```

## Spread (bps) — mid denominator
- `spread_bps_raw = ((best_ask - best_bid) / mid) * 10_000`
- `spread_bps = round_half_even(spread_bps_raw, 6)`

## Slippage (BUY vs mid)
- `target_base = notional_usdt / mid`
- walk asks; compute `exec_price` weighted average
- `slippage_bps_raw = ((exec_price / mid) - 1) * 10_000`
- `slippage_bps = round_half_even(slippage_bps_raw, 6)`

## Liquidity grade
- D if insufficient depth OR slippage_bps > 100
- C if 50 < slippage_bps <= 100
- B if 20 < slippage_bps <= 50
- A if slippage_bps <= 20
