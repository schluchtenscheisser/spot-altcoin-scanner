# Glossary — Independence-Release Bootstrap Terms (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_GLOSSARY
status: canonical
primary_architecture: independence_release
mode: bootstrap_reference
```

## Usage note
This bootstrap glossary only defines terms that can be stated safely without inventing deferred business logic. Where the authoritative Independence-Release Abschnittsdateien were referenced by the ticket but are not checked into this repository, the entry deliberately stays at reference level instead of creating speculative semantics.

## Terms

### `daily_bar_id`
Canonical identifier for the closed daily bar used by the daily discovery scan context. The exact formatting and persistence representation are to follow the authoritative Independence-Release Abschnittsdateien.

### `intraday_bar_id`
Canonical identifier for the closed intraday bar used by the intraday promotion scan context. The exact formatting and persistence representation are to follow the authoritative Independence-Release Abschnittsdateien.

### `setup_cycle_id`
Identifier that ties together the lifecycle of a setup across the target architecture. The bootstrap reserves the term; the strict construction rule remains defined by the authoritative Independence-Release planning documents.

### `market_phase`
Phase label produced by the future `scanner/phase/` module for target-architecture decisions. Bootstrap meaning: a canonical phase concept exists, but the specific domain and transitions are deferred.

### `state_machine_state`
Lifecycle state emitted by the future `scanner/state/` module. This bootstrap defines the term as an explicit state-machine concept without freezing the unresolved state domain.

### `decision_bucket`
Bucket-level decision outcome produced by the future `scanner/decision/` module. The term is reserved canonically; exact values are deferred until the corresponding decision ticket.

### `structural_break`
Structure-derived break condition referenced by the Independence-Release concept. This bootstrap acknowledges the term as architecture-relevant while leaving the exact trigger semantics to the authoritative source set.

### `bars_since_*`
Family of counters measured in the canonical **4h-bar unit** when used in the Independence-Release architecture. Individual members of the family must be defined by later canonical tickets before implementation.

### `daily_discovery_scan`
The daily scheduled scan that discovers candidates using the closed daily context and writes target-architecture outputs/persistence artifacts. Its runtime sequence is summarized in `RUNTIME_AND_OPERATIONS.md`.

### `intraday_promotion_scan`
The intraday scheduled scan that revisits previously discovered candidates and promotes or reclassifies them using closed intraday context. Its runtime sequence is summarized in `RUNTIME_AND_OPERATIONS.md`.
