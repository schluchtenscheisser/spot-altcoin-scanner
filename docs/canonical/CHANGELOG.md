# Changelog (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_CHANGELOG
status: canonical
canonical_schema_version: 6.2.0
canonical_schema_versioning: semver
canonical_schema_version_location: docs/canonical/CHANGELOG.md
```

## canonical_schema_version policy (SemVer)
`canonical_schema_version` is manually maintained and follows `MAJOR.MINOR.PATCH`.

- **MAJOR**: breaking canonical contract changes (field removals/renames, decision-domain changes, incompatible semantics).
- **MINOR**: backward-compatible canonical additions (new optional fields, new non-breaking reason codes, clarifications that add capability).
- **PATCH**: non-semantic fixes/wording corrections with no contract behavior change.

Rule: Every canonical contract change PR must evaluate version impact and update this value accordingly.


## 6.2.0 — Canonical R-multiple targets and risk gate alignment
- Canonicalized trade-level target derivation to `1R/2R/3R` from effective stop distance (`R = entry - stop`).
- Canonicalized RR acceptance checkpoint: configured `risk.min_rr_to_target_1` threshold is evaluated against `rr_to_target_2` (2R) while preserving config-key compatibility.
- Clarified nullable behavior: if stop is not evaluable, target/RR/risk-acceptability remain `null`; otherwise canonical target ladder and RR fields are deterministic.



## 6.1.1 — Risk config key canonicalization (`min_rr_to_target_1`)
- Canonicalized the Phase-1 RR threshold config key to `risk.min_rr_to_target_1` with deterministic precedence over legacy alias `risk.min_rr_to_tp10`.
- Clarified compatibility behavior: legacy alias remains readable for one migration phase, but canonical docs/config examples now use target-index naming.
- Clarified trade-level module responsibility wording to reflect downstream risk/decision preparation usage.


## 6.1.0 — Invalidation-first stop derivation with ATR fallback
- Canonicalized deterministic stop-source priority: setup `invalidation` first, then ATR fallback, else nullable stop/risk path.
- Added `stop_source` contract (`invalidation|atr_fallback|null`) to align risk outputs with setup truth.
- Clarified nullable evaluation behavior: evaluable stop/risk distance may coexist with nullable RR/acceptability when targets are not evaluable.

## 6.0.0 — Remove fixed TP10/TP20 output semantics (breaking)
- Breaking canonical output contract: removed fixed-percentage `tp10_price`/`tp20_price` and `rr_to_tp10`/`rr_to_tp20` runtime fields.
- Canonical trade-candidate semantics now use setup-target fields `target_1_price`, `target_2_price`, `target_3_price`, `rr_to_target_1`, and `rr_to_target_2`.
- Clarified nullability: missing/invalid/non-finite target data remains `null`; no synthetic fixed-percentage fallback is allowed.

## 5.7.0 — Entry timing output semantics
- Added optional `trade_candidates.distance_to_entry_pct` as deterministic percentage distance between `current_price_usdt` and `entry_price_usdt`.
- Added optional `trade_candidates.entry_state` enum (`early|at_trigger|late|chased`) with fixed V1 thresholds and nullability rules.
- Clarified these fields as interpretability-only output semantics that MUST NOT change decision/scoring/ranking behavior.

## 5.6.0 — Directional-volume preparation namespace (non-active)
- Added optional `trade_candidates.directional_volume_preparation` namespace for forward-compatible Directional Volume integration.
- Canonicalized explicit missing/null/invalid handling for preparatory directional-volume fields (missing valid, null valid, invalid values fail clearly).
- Clarified that preparatory directional-volume fields are Phase-1 inactive and must not alter decision/scoring behavior.

## 5.5.0 — Shadow-mode primary-path contract hardened
- Added canonical `shadow.primary_path` semantics with deterministic behavior across `legacy_only`, `new_only`, and `parallel`.
- Added required run-manifest `pipeline_paths` fields `primary_path` and `primary_path_source` for machine-readable switch transparency.
- Canonicalized mode/primary contradiction handling: clear validation error, no silent fallback and no hidden primary-path switch.

## 5.4.0 — Shadow-mode pipeline path manifest contract
- Added canonical shadow-mode operation contract (`legacy_only`, `new_only`, `parallel`) with deterministic default `parallel`.
- Added required run-manifest field `pipeline_paths` with `shadow_mode`, `legacy_path_enabled`, and `new_path_enabled`.
- Clarified that shadow mode is transition control only and does not introduce a second SoT beside `trade_candidates`.

## 5.3.0 — Run manifest minimum contract introduced
- Canonicalized a required standalone run manifest artifact separated from `trade_candidates`.
- Added required manifest minimum fields: `run_id`, `timestamp_utc`, `config_hash`, `canonical_schema_version`, `feature_flags`, `counts_per_stage`, `shortlist_size_used`, `orderbook_top_k_used`, `data_freshness`, `warnings`, `duration_seconds`.
- Clarified `warnings` as machine-readable list with empty-list (`[]`) default instead of `null`.


## 5.2.0 — trade_candidates canonical JSON SoT
- Canonicalized the required `trade_candidates` row minimum contract for Phase-1 candidate decisions and risk context.
- Added deterministic output ordering contract `ENTER > WAIT > NO_TRADE`, then `global_score` desc, then stable tie-breakers.
- Clarified separation between candidate SoT (`trade_candidates`) and technical run-manifest metadata.

## 5.1.0 — BTC regime V2 threshold modifier clarity
- Added explicit Phase-1 BTC regime state contract `{RISK_OFF, NEUTRAL, RISK_ON}` for decision integration.
- Canonicalized `NEUTRAL` baseline behavior and explicit `RISK_OFF` ENTER-threshold boost semantics.
- Added `btc_regime_state` as required candidate decision context field in output schema.

## 5.0.0 — Phase-1 contract realignment (breaking)
- Breaking canonical contract change: the Phase-1 architecture introduced in PR-01/PR-01.1 is now versioned as MAJOR because semantics changed incompatibly.
- `trade_candidates` row-minimum contract is explicitly anchored to `OUTPUT_SCHEMA.md`; setup-scoring docs may define additional setup fields but must not redefine global row minimums.
- `orderbook_not_in_budget` is fixed as `UNKNOWN` / not-evaluated stop-path (outside `orderbook_top_k` budget), distinct from fetched-but-invalid/malformed/stale payload outcomes.

## 4.2.1 — Canonical contracts tightened
- Added canonical contract docs for:
  - `PIPELINE.md`
  - `DECISION_LAYER.md`
  - `RISK_MODEL.md`
  - `LIQUIDITY/TRADEABILITY_GATE.md`
  - `BUDGET_AND_POOL_MODEL.md`
- Updated `OUTPUT_SCHEMA.md` to declare `trade_candidates` as Source of Truth and explicit nullable/decision reason rules.
- Formalized UNKNOWN/MARGINAL semantics and pre-decision UNKNOWN stop-path.

## 2026-02-23
- Established `docs/canonical/` as the canonical documentation root.
