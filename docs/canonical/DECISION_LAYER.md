# Decision Layer — ENTER / WAIT / NO_TRADE (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_DECISION_LAYER
status: canonical
decision_domain:
  - ENTER
  - WAIT
  - NO_TRADE
requires_fully_evaluated_for_wait: true
unknown_reaches_decision_layer: false
```

## Decision domain
`decision ∈ {ENTER, WAIT, NO_TRADE}` only.

## Score-role separation (authoritative)
- `setup_score`: decision-threshold score for ENTER/WAIT eligibility.
- `global_score`: prioritization/context score among already decision-eligible candidates.

`global_score` MUST NOT be used as primary truth to bypass hard blockers from tradeability/risk/setup readiness.

## Entry prerequisites (minimum)
A candidate can be `ENTER` only if all are true:
1. Tradeability is evaluable and entry-eligible (`DIRECT_OK` or `TRANCHE_OK`).
2. Setup is entry-ready (including reversal/reclaim requirements where applicable).
3. Risk is evaluable and acceptable (`risk_acceptable = true`).
4. `setup_score` meets configured ENTER threshold.

Risk consistency rules:
- Decision evaluation MUST use the same effective stop as risk computation (`stop_price_initial` selected by `stop_source`), with no alternate hidden stop model.
- `risk_acceptable` RR gating is evaluated on `rr_to_target_2` (2R checkpoint), not on `rr_to_target_1`.

## WAIT semantics
- `WAIT` applies only to fully evaluated candidates.
- Typical WAIT causes: valid setup but below ENTER threshold, timing/confirmation pending, or `MARGINAL` execution quality.
- `UNKNOWN` can never become `WAIT`.

## NO_TRADE semantics
Use `NO_TRADE` for hard blockers/non-eligibility (e.g., `FAIL`, denied risk, invalid setup).


## BTC regime decision modifier (Phase 1)
- Allowed BTC regime states are exactly `{RISK_OFF, NEUTRAL, RISK_ON}`.
- `NEUTRAL` is baseline behavior.
- `RISK_ON` does not lower ENTER thresholds in Phase 1.
- In `RISK_OFF`, Decision Layer increases ENTER threshold by configured `btc_regime.risk_off_enter_boost`.
- If a candidate would be `ENTER` at baseline but fails only due to `RISK_OFF` threshold boost, decision becomes `WAIT` with reason `btc_regime_caution`.
- Decision rows must expose `btc_regime_state` explicitly for transparent context.


## Late-entry guards for ENTER (Phase 1)
For candidates that would otherwise qualify as `ENTER`, the decision layer applies deterministic late-entry guards in this exact order:

1. **Hard target-1 stop**
   - If `current_price_usdt >= target_1_price`, the candidate MUST be downgraded to `NO_TRADE` with reason `price_past_target_1`.
2. **Effective RR guard from current price**
   - Otherwise compute `effective_rr_to_target_2 = (target_2_price - current_price_usdt) / (current_price_usdt - stop_price_initial)`.
   - If `effective_rr_to_target_2 < decision.min_effective_rr_to_target_2_for_enter`, the candidate MUST be downgraded to `WAIT` with reason `effective_rr_insufficient`.

Guard-evaluation semantics:
- Missing/invalid/non-finite inputs for guard evaluation are non-evaluable and MUST NOT be coerced into guard failures.
- `entry_state=chased` alone is not a hard blocker.
- Late-entry guards MUST NOT change stop derivation, risk model acceptance semantics, setup scoring, or tradeability semantics.

## Explicit exclusions
- Reversal without reclaim is not entry-ready.
- Phase 1 does not define hold/rotate/portfolio orchestration decisions.


## Scorer V2 readiness inputs
For setup scorers, decision-relevant readiness MUST be emitted as structured fields (no free-text inference):
- `entry_ready: bool`
- `entry_readiness_reasons: list[str]`
- `setup_subtype: str` (deterministic, from a stable setup-specific value set)

Readiness contract:
- `entry_ready=false` requires a non-empty `entry_readiness_reasons` list.
- `entry_ready=true` requires `entry_readiness_reasons=[]` (no negative readiness reasons).

Setup-specific confirmations (when applicable):
- Breakout: `breakout_confirmed: bool | null`
- Pullback: `rebound_confirmed: bool | null`, `retest_reclaimed: bool | null`
- Reversal: `reclaim_confirmed: bool | null`, `retest_reclaimed: bool | null`

Hard rule: reversal without confirmed reclaim MUST be `entry_ready=false` with readiness reason `retest_not_reclaimed`.

Missing/invalid/non-finite inputs are a non-evaluable path and must not be silently coerced to a valid confirmation signal.
- Optional preparatory fields (e.g. `directional_volume_preparation`) may be carried for forward-compatibility but MUST NOT influence Phase-1 ENTER/WAIT/NO_TRADE decisions until explicitly canonicalized.
