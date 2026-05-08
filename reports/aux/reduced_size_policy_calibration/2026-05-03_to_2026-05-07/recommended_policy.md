# Recommended T29 Policy

Fail policy status: recommended.

## Target 10k config values

| key | value |
| --- | --- |
| notional_total_usdt | 10000 |
| notional_chunk_usdt | 5000 |
| max_tranches | 2 |
| depth_buffer_multiple | 10 |
| derived_min_depth_1pct_usdt | 100000 |

## Runtime status semantics

direct_ok: full-size tradeable.

tranche_ok: existing behavior unchanged; no order-splitting extension in T29.

marginal: split by execution_size_class / recommended_position_factor.

fail: hard no-trade.

unknown: no trade / not safely evaluable.

## Recommended fields

execution_size_class values: full, reduced_75, reduced_50, reduced_25, observe_only, blocked, not_evaluable.

recommended_position_factor mapping: full=1.00, reduced_75=0.75, reduced_50=0.50, reduced_25=0.25, observe_only=0.00, blocked=0.00, not_evaluable=null.

Do not remove marginal + below_min from structural buckets in T29. Keep them visible in reports, but clearly mark them as execution_size_class = observe_only and not tradeable.

Use the existing full-trade slippage threshold for reduced-size candidates unless T29 has stronger evidence. Slippage data is only partially available. T28 does not justify loosening slippage thresholds for reduced-size candidates.

Recommended grade mapping for T29: balanced, because it preserves tradeable-class differentiation while keeping reduced_25 conservative and observe_only penalized.

Based on the five T27-capable runs, fail remains out of scope for reduced-size execution and should stay hard-blocked in the T29 policy proposal. This is because no fail record reaches reduced_25 under the target 10k scenario.

## Limitations

1. No profitability conclusion. T28 does not evaluate forward returns, MFE, MAE, or realized trade performance.
2. Five-run sample. The analysis uses five T27-capable Shadow-Live Daily runs. It is sufficient for first policy calibration but should be revisited after more runs.
3. Slippage partial availability. Slippage is not available for all records. Missing slippage must not be interpreted as good execution.
4. No fail policy generalization beyond current evidence. Fail remains hard-blocked for T29 based on current evidence; future materially different liquidity regimes may warrant re-analysis.
5. No order-splitting change. T28 does not evaluate or modify tranche_ok or order-splitting behavior.
