# Feature Enhancements — Deferred Topics (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_FEATURE_ENHANCEMENTS
status: canonical
```

## Purpose
This file lists **bewusst verschobene Themen** for the Independence-Release architecture. It starts empty by design; new entries should be added only when a future ticket explicitly defers an enhancement instead of implementing it.
Bootstrap placeholder text was `none yet` before deferred entries were added.

## Deferred enhancements
- **State confidence penalty for “narrow margins” — operationalization and calibration**
  - Source context: Abschnitt 4 defines a `-5` penalty when the current state rests on “narrow margins”, but the concept is not yet operationalized.
  - Current interim handling: treated as `0` / not applied until the concept is specified.
  - Future enhancement scope:
    - define what exactly qualifies as “narrow”
    - decide whether the margin is measured against phase floors, state admission thresholds, or both
    - decide whether the rule is phase-specific, state-specific, or global
    - specify how multiple near-threshold conditions combine
    - calibrate the penalty empirically on real run populations before activation

- **Spec consistency pass for rule tables vs enum / reason-code lists**
  - Source context: the Ticket-12 preparation exposed at least one mismatch between an explicit bucket-assignment rule and the corresponding standard reason-code list.
  - Future enhancement scope:
    - run a systematic consistency audit across Gesamtkonzept and section files
    - verify that explicit rules, enum families, reason-code lists, and examples stay aligned
    - resolve inconsistencies centrally before they propagate into future tickets

- **Standardized nullable-numeric handling for decision / ranking paths**
  - Source context: Ticket-12 work exposed that nullable numeric inputs in decision and ranking paths are easy to mis-handle, especially across gated, non-gated, demotion, and catch-all paths.
  - Future enhancement scope:
    - define a clearer architecture-level policy for nullable numeric inputs by path category
    - document which paths must reject, which may floor, and which must preserve nullability
    - keep the policy narrow and explicit rather than relying on helper-local conventions

- **Standardized demotion / fallback scoring pattern in the decision layer**
  - Source context: execution-fail demotions and other fallback paths proved easy to route incorrectly through candidate-style scoring logic.
  - Future enhancement scope:
    - define a canonical scoring pattern for demotion, unresolved, and catch-all paths
    - make explicit which score-building helpers are allowed in those paths
    - reduce the chance that future decision tickets or implementations accidentally reuse the wrong scoring path

- **More explicit ranking-input contract pattern for decision outputs**
  - Source context: Ticket-12 required several iterations to make the ranking input contract fully explicit, especially around `symbol`, tie-break fields, and the distinction between decision output and ranking-ready records.
  - Future enhancement scope:
    - define a reusable canonical pattern for ranking-ready records
    - standardize which fields must be present for deterministic ranking
    - reduce repeated clarification effort in later tickets touching ranking or downstream reporting
