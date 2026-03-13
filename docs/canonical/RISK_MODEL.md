# Risk Model — Phase-1 Defaults and Blockers (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_RISK_MODEL
status: canonical
phase: 1
default_stop_model: invalidation_first_with_atr_fallback
required_fields:
  - stop_price_initial
  - stop_source
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

## Phase-1 stop model
- Default stop derivation is invalidation-first with ATR fallback.
- Deterministic stop-source priority:
  1. setup `invalidation` when present, finite, positive, and strictly below entry
  2. ATR fallback (`entry_price - atr_multiple * atr_value`) when derivable and strictly below entry
  3. else no evaluable stop (`null` fields)
- `stop_source` MUST be one of `invalidation`, `atr_fallback`, or `null`.
- `stop_price_initial` MUST be present when risk distance is evaluable.

## Required risk metrics
- `risk_pct_to_stop`: fractional downside from planned entry to `stop_price_initial`.
- `stop_source`: provenance marker for selected stop (`invalidation` vs `atr_fallback`).
- `rr_to_target_1`: reward/risk ratio to canonical `1R` target.
- `rr_to_target_2`: reward/risk ratio to canonical `2R` target.
- `risk_acceptable`: boolean decision input derived from configured risk thresholds.

Nullable semantics:
- If a metric is not evaluable, value MUST be `null` (not coerced to `0`/`false`).

## Deterministic Phase-1 computation contract
For Long-Spot candidates, compute risk fields in this fixed order:
1. Determine planned entry (`entry_trigger`, or `entry_zone.center` for pullback setups).
2. Resolve stop source with strict priority:
   - valid setup `invalidation` first
   - else valid ATR fallback
   - else non-evaluable risk path (`null` fields)
3. Enforce long invariant: `stop_price_initial < entry_price`.
4. Compute `risk_pct_to_stop = ((entry_price - stop_price_initial) / entry_price) * 100`.
5. Compute canonical target ladder from effective risk distance `R = entry_price - stop_price_initial`:
   - `target_1_price = entry_price + 1R`
   - `target_2_price = entry_price + 2R`
   - `target_3_price = entry_price + 3R`
6. Compute `rr_to_target_1=1.0`, `rr_to_target_2=2.0`, `rr_to_target_3=3.0` (floating-point tolerance) from that ladder.
7. Compute `risk_acceptable` from configured bounds:
   - `min_stop_distance_pct <= risk_pct_to_stop <= max_stop_distance_pct`
   - `rr_to_target_2 >= min_rr_to_target_1` (existing config key is preserved; evaluation checkpoint is target_2)

Missing vs invalid semantics:
- Missing required stop inputs (entry, valid invalidation, valid ATR fallback) => all required risk metrics remain `null`.
- Invalid stop inputs (non-positive/NaN/non-numeric invalidation, invalid ATR fallback, or non-long stop invariant) => fallback order applies deterministically, else `null` fields.
- If stop is evaluable, canonical targets are derived from `R` deterministically; RR and acceptability remain evaluable regardless of pre-existing setup target hints.
- Not-evaluable risk is not implicitly treated as `false`.

## Risk blocker authority
The following repo locations are authoritative for hard risk-blocking inputs:
- `config/denylist.yaml`
- `config/unlock_overrides.yaml`
- `filters.py::_apply_risk_flags()`

If a hard blocker applies, candidate cannot be `ENTER`.

## Target semantics
- Runtime targets are canonical `1R/2R/3R` orientation levels derived from the effective stop used for risk computation.
- Fixed +10%/+20% target projections are not part of the canonical runtime contract.
- Targets DO NOT imply mandatory exits or automated take-profit behavior in Phase 1.
