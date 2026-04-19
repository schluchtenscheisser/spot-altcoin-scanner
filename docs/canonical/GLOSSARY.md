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
Canonical identifier for the closed daily bar used by the daily discovery scan context. In the bootstrap contract this is a `YYYY-MM-DD` string for the most recently closed daily bar.

### `intraday_bar_id`
Canonical identifier for the closed intraday bar used by the intraday promotion scan context. In the bootstrap contract this is the UTC epoch-millisecond close timestamp of the most recently closed 4h bar.

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

### `bars_since_last_volume_shift_event` → `bars_since_last_volume_shift_4h`
Spec-to-implementation mapping: Abschnitt 1 §7.2 input `bars_since_last_volume_shift_event` is implemented in `RawFeatures4H` as `bars_since_last_volume_shift_4h`.

### `bars_since_last_structural_break_event` → `bars_since_last_structural_break_4h`
Spec-to-implementation mapping: Abschnitt 1 §7.2 input `bars_since_last_structural_break_event` is implemented in `RawFeatures4H` as `bars_since_last_structural_break_4h`.

### `daily_discovery_scan`
The daily scheduled scan that discovers candidates using the closed daily context and writes target-architecture outputs/persistence artifacts. Its runtime sequence is summarized in `RUNTIME_AND_OPERATIONS.md`.

### `intraday_promotion_scan`
The intraday scheduled scan that revisits previously discovered candidates and promotes or reclassifies them using closed intraday context. Its runtime sequence is summarized in `RUNTIME_AND_OPERATIONS.md`.

### `post_1d_activity_gate`
Hard gate after 1d fetch: evaluates last 14 closed daily bars (calendar window, missing bars count inactive) and blocks symbols with `failed` or `not_evaluable` from bypass/filter stages.

### `monitoring_bypass`
Deterministic 4h-fetch bypass for monitored symbols (`state_machine_state`, `decision_bucket`, or phase confidence). Bypass is applied before non-bypass cap and can exceed nominal cap.

### `pre_4h_candidate_filter`
Cheap 1d-only operational budget filter with exactly three OR-rules (`COMPRESSION`, `TREND`, `VOLUME`). No 4h-derived signals are allowed.

## Ticket 4 terms

- **cache_status**: one of `fresh`, `stale`, `missing`, `broken` for a `(symbol,timeframe,now)` cache state.
- **fetch_decision**: one of `skip`, `fetch_full`, `fetch_incremental` derived from cache status and missing-bar count.
- **cached_close_time_utc_ms**: cached latest closed-bar close timestamp for a symbol/timeframe.
- **closed-bar-only**: persistence constraint rejecting any bar beyond current canonical closed cutoff.
- **full fetch**: accepted window over last configured lookback closed bars ending at cutoff.
- **incremental fetch**: accepted window strictly newer than cached close and up to cutoff.
- **broken cache**: cache meta row exists but is unusable (non-`ok` status, null cached close, or bar/meta inconsistency).

### `feature_bundle`
Ticket-5 in-memory container that binds bar-clock references with `raw_1d`, optional `raw_4h`, and `raw_shared`.

### `companion_status_field`
Per-field status value named `{field_name}_status`, using closed enum: `ok`, `insufficient_history`, `gap_in_required_window`, `upstream_dependency_null`, `invalid_upstream_value`.

### `raw_shared`
Cross-timeframe raw-feature model computed from precomputed `RawFeatures1D` and optional `RawFeatures4H` (without direct OHLCV access).

## Ticket 6 terms

- **Tier1AxisBundle**: typed in-memory container for six Tier-1 axes plus per-axis evaluability/coverage metadata.
- **effective_weight_ratio**: retained pre-renormalization weight sum divided by original weight sum after missing-input dropout.
- **reduced_resolution**: axis computed after at least one required sub-input drops out.

## Ticket 7 terms

- **Tier2AxisBundle**: typed in-memory container for exactly three Tier-2-Simplified axes plus per-axis evaluability/coverage metadata.
- **two-path axis evaluation**: deterministic path selection rule where `data_4h_available=true` forces 4h-only evaluation and `data_4h_available=false` forces 1d fallback evaluation.
- **segmentation validity pre-gate**: `pullback_quality_simplified` gate requiring `impulse_high_price_tf > impulse_start_price_tf` on the selected timeframe before any weighted scoring begins.
- **_simplified suffix**: denotes the reduced Tier-2 axis family defined for Independence-Release Ticket 7, distinct from Tier-1 axes and from later phase/state interpretation layers.
