> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Title
[P1] Canonical: Evaluation Dataset JSONL Spec + Snapshot Field Mapping

## Context / Source (optional)
- Roadmap fordert Evaluation Dataset Export aus Snapshot-History
- Wir brauchen canonical Mapping (No-Guesswork) von Snapshot JSON → Dataset Felder.
- Output soll JSONL sein, 1 Zeile = Candidate-Setup, plus meta-record als erste Zeile.

## Goal
Ein neues canonical Dokument definiert:
- JSONL Schema (meta record + candidate_setup record)
- Feldliste + Typen + Nullability
- Exakte Feldquellen per Pfad (JSONPath-ähnlich) aus Snapshots
- Run-ID Regeln, record_id Konstruktion, rank-Regeln, trigger-date/offset Regeln

## Scope
- docs/canonical/OUTPUTS/EVALUATION_DATASET.md
- ggf. docs/canonical/OUTPUT_SCHEMA.md (nur falls notwendig zur Registrierung eines neuen Output-Artefakts; optional aber empfohlen)

## Out of Scope
- Implementierung des Exporters
- E2 Modell Implementierung

## Canonical References (important)
- docs/canonical/BACKTEST/MODEL_E2.md
- docs/canonical/OUTPUT_SCHEMA.md (falls referenziert)
- docs/canonical/SCORING/*

## Proposed change (high-level)
Create docs/canonical/OUTPUTS/EVALUATION_DATASET.md mit:

A) File-Level:
- Format: JSONL
- First line: meta record `{ "type": "meta", ... }`
- Subsequent lines: `{ "type": "candidate_setup", ... }`

B) Candidate-Setup Record Identity:
- `record_id = "{run_id}:{t0_date}:{symbol}:{setup_type}:{setup_id}"`

C) run_id:
- Default: aus snapshot.meta.asof_iso (UTC) → "YYYY-MM-DD_HHMMZ"
- Override via CLI möglich (Exporter Ticket)

D) Records:
- 1 line = 1 Symbol × 1 Setup × 1 t0_date
- Exporter nimmt `setup_id` aus Scoring-Entry, fallback `setup_type`.

E) Mandatory Fields (nullable where stated):
- Identität: record_id, run_id, t0_date, symbol, setup_type, setup_id
- Snapshot metadata: snapshot_version (from snapshot.meta.version), asof_ts_ms (snapshot.meta.asof_ts_ms), asof_iso (snapshot.meta.asof_iso)
- Market/meta: market_cap_usd (snapshot.data.features[symbol].market_cap), quote_volume_24h_usd (snapshot.data.features[symbol].quote_volume_24h), liquidity_grade (snapshot.data.features[symbol].liquidity_grade)
- Regime: btc_regime (snapshot.meta.btc_regime, nullable for old snapshots)
- Scoring: score (from scoring entry), setup_rank, global_rank (Top20-only else null)
- E2 outcome (recompute): reason, t_trigger_date, t_trigger_day_offset, entry_price, hit_10, hit_20, hits (map), mfe_pct, mae_pct

F) Ranking Rules:
- setup_rank = 1-based index in snapshot.scoring.<setup_list> order
- global_rank: recompute compute_global_top20(...) from snapshot scoring lists; if entry in top20 by symbol => 1..20 else null

G) E2 thresholds:
- thresholds list configurable; always include 10 and 20
- Candidate record includes:
  - hit_10, hit_20 always present
  - hits map with keys as strings ("5","10",...) and bool values

H) Field Mapping Section:
- For each dataset field define exact source path, type, nullable.
- For fields that might not exist: set null, never infer.

## Acceptance Criteria (deterministic)
1) docs/canonical/OUTPUTS/EVALUATION_DATASET.md exists and fully defines JSONL schema with meta + candidate_setup records.
2) Document includes explicit mapping table (dataset field → snapshot path → type → nullable).
3) Document includes deterministic identity rules for run_id and record_id.
4) Document includes deterministic rank rules (setup_rank and global_rank Top20-only).
5) Document states exporter behavior when scoring lists are empty: emit zero candidate_setup records for that date.

## Tests (required if logic changes)
- Docs-only Ticket: keine Code-Tests.
- Reviewer-Check: Mapping enthält keine heuristischen Pfade; jeder Feldzugriff ist exakt.

## Constraints / Invariants (must not change)
- Determinismus, no lookahead
- JSONL: 1 record per line; stable ordering requirement wird im Implementierungs-Ticket getestet

## Definition of Done (Codex must satisfy)
(Reference: docs/canonical/WORKFLOW_CODEX.md)
- [ ] Canonical doc erstellt/aktualisiert gemäß Acceptance Criteria
- [ ] Falls OUTPUT_SCHEMA.md aktualisiert wird: schema change dokumentiert gemäß Projektkonvention
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR nach docs/legacy/tickets/ verschoben

---
## Metadata (optional)
```yaml
created_utc: "2026-02-27T00:00:00Z"
priority: P1
type: docs
owner: codex
related_issues: []
```
