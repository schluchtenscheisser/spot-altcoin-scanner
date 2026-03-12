# Risk Model — Phase-1 Defaults and Blockers (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RISK_MODEL
status: canonical
phase: 1
default_stop_model: atr_based
required_fields:
  - stop_price_initial
  - risk_pct_to_stop
  - rr_to_target_1
  - rr_to_target_2
  - risk_acceptable
risk_blocker_sources:
  - config/denylist.yaml
  - config/unlock_overrides.yaml
  - filters.py::_apply_risk_flags
```

## Scope
Defines Phase-1 risk semantics for entry decisions. This is not a portfolio-management or exit-automation module.

## Phase-1 default stop model
- Default initial stop is ATR-based.
- Setup scorers MAY emit optional context anchors (`invalidation_anchor_price`, `invalidation_anchor_type`, `invalidation_derivable`) for transparency/future extensions; these anchors do **not** replace ATR stop computation in Phase 1.
- `stop_price_initial` MUST be present when risk is evaluable.
- Setup-specific stop variants may be added later, but do not replace the Phase-1 default contract here.

## Required risk metrics
- `risk_pct_to_stop`: fractional downside from planned entry to `stop_price_initial`.
- `rr_to_target_1`: reward/risk ratio to setup `target_1`.
- `rr_to_target_2`: reward/risk ratio to setup `target_2`.
- `risk_acceptable`: boolean decision input derived from configured risk thresholds.

Nullable semantics:
- If a metric is not evaluable, value MUST be `null` (not coerced to `0`/`false`).

## Deterministic Phase-1 computation contract
For Long-Spot candidates, compute risk fields in this fixed order:
1. Determine planned entry (`entry_trigger`, or `entry_zone.center` for pullback setups).
2. Validate entry and ATR as positive finite numbers.
3. Compute `stop_price_initial = entry_price - atr_multiple * atr_value`.
4. Enforce long invariant: `stop_price_initial < entry_price`.
5. Compute `risk_pct_to_stop = ((entry_price - stop_price_initial) / entry_price) * 100`.
6. Compute `rr_to_target_1` and `rr_to_target_2` from configured orientation targets and absolute risk.
7. Compute `risk_acceptable` from configured bounds:
   - `min_stop_distance_pct <= risk_pct_to_stop <= max_stop_distance_pct`
   - `rr_to_target_1 >= min_rr_to_tp10`

Missing vs invalid semantics:
- Missing required inputs (entry/ATR/targets) => all required risk metrics remain `null`.
- Invalid required inputs (non-positive/NaN/non-numeric, or non-long stop invariant) => all required risk metrics remain `null`.
- Not-evaluable risk is not implicitly treated as `false`.

## Risk blocker authority
The following repo locations are authoritative for hard risk-blocking inputs:
- `config/denylist.yaml`
- `config/unlock_overrides.yaml`
- `filters.py::_apply_risk_flags()`

If a hard blocker applies, candidate cannot be `ENTER`.

## Target semantics
- `target_1` and `target_2` are setup-derived orientation targets for reward/risk computation.
- Fixed +10%/+20% target projections are not part of the canonical runtime contract.
- Targets DO NOT imply mandatory exits or automated take-profit behavior in Phase 1.
