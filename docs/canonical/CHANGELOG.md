# Changelog (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_CHANGELOG
status: canonical
canonical_schema_version: 5.2.0
canonical_schema_versioning: semver
canonical_schema_version_location: docs/canonical/CHANGELOG.md
```

## canonical_schema_version policy (SemVer)
`canonical_schema_version` is manually maintained and follows `MAJOR.MINOR.PATCH`.

- **MAJOR**: breaking canonical contract changes (field removals/renames, decision-domain changes, incompatible semantics).
- **MINOR**: backward-compatible canonical additions (new optional fields, new non-breaking reason codes, clarifications that add capability).
- **PATCH**: non-semantic fixes/wording corrections with no contract behavior change.

Rule: Every canonical contract change PR must evaluate version impact and update this value accordingly.


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
