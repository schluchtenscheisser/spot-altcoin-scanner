> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket: Fix GPT snapshot sources + sync canonical schema version

## Title
[P1] GPT-Snapshot darf keine Legacy-Scoring-Doku ziehen; Canonical OUTPUT_SCHEMA muss Schema-Version v1.9 spiegeln

## Context / Source
In PR #95 wurde der GPT-Snapshot-Workflow so erweitert, dass `docs/legacy/scoring.md` in den Snapshot aufgenommen wird, weil `docs/scoring.md` nur ein Stub ist. Das verletzt die Canonical/Legacy-Trennung und kann KI-Modelle verwirren.
Zusätzlich wurde die Output-Schema-Version im Code auf `v1.9` (Meta-Version 1.9) erhöht, ohne dass `docs/canonical/OUTPUT_SCHEMA.md` diese Version explizit widerspiegelt.

## Goal
1) Der GPT-Snapshot enthält **Canonical** Doku als Wahrheit (insb. Scoring) und **keine Legacy-Docs** als Quelle.
2) `docs/canonical/OUTPUT_SCHEMA.md` ist konsistent zur im Code verwendeten Schema-Version `v1.9` / Meta-Version `1.9`.

## Scope
Erlaubte Änderungen:
- `.github/workflows/generate-gpt-snapshot.yml`
- `docs/canonical/OUTPUT_SCHEMA.md`
- optional: `docs/SCHEMA_CHANGES.md` (nur wenn nötig zur Korrektur/Ergänzung des Eintrags aus PR #95)
- optional: kleinere Docs/Kommentare, wenn sie direkt die obigen Änderungen erklären (kein Refactor)

Nicht erlaubt:
- Änderungen an Scoring-Logik oder anderen Features
- Änderungen, die die Schema-Version erneut bumpen
- Änderungen an Legacy-Inhalten (außer Entfernen ihrer Nutzung als Snapshot-Quelle)

## Out of Scope
- Kein weiteres Redesign des Snapshot-Systems
- Keine Änderung an `docs/scoring.md` (Stub kann bleiben)
- Kein Umbau der gesamten Doku-Struktur

## Canonical References
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/INDEX.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
- `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- `docs/canonical/LIQUIDITY/RE_RANK_RULE.md`
- `docs/canonical/WORKFLOW_CODEX.md`

## Proposed change (high-level)
### A) Snapshot Workflow
- Entferne die explizite Aufnahme von `docs/legacy/scoring.md` aus `generate-gpt-snapshot.yml`.
- Ersetze sie durch Canonical Scoring Quellen, mindestens:
  - `docs/canonical/SCORING/SCORE_BREAKOUT_TREND_1_5D.md`
  - `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
  - optional (empfohlen): `docs/canonical/INDEX.md` als Einstieg + weitere Top-Level Canonical (OUTPUT_SCHEMA, CONFIGURATION, VERIFICATION)
- Regel: Snapshot darf **nicht** aus `docs/legacy/*` ziehen.

### B) Canonical OUTPUT_SCHEMA sync
- Ergänze in `docs/canonical/OUTPUT_SCHEMA.md` explizit:
  - report/schema version `v1.9`
  - meta version `1.9`
- Stelle sicher, dass das deterministisch und eindeutig dokumentiert ist (kein “implementation-defined”).

## Implementation Notes
- Determinismus: Snapshot muss ausschließlich Canonical als Truth enthalten; Legacy bleibt historisch.
- Backward compatibility: Keine Änderung an bestehenden Outputfeldern; nur Dokumentation/Workflow-Quellen.
- Minimale Änderungen: Nur die betroffenen Dateien.

## Acceptance Criteria (deterministic)
1) `.github/workflows/generate-gpt-snapshot.yml` enthält **keine** Referenz mehr auf `docs/legacy/scoring.md` (und generell keine `docs/legacy/` Inputs).
2) Snapshot-Workflow inkludiert stattdessen Canonical Scoring Docs (mind. die beiden oben genannten).
3) `docs/canonical/OUTPUT_SCHEMA.md` dokumentiert klar `schema_version: v1.9` und `meta_version: 1.9` (oder äquivalente, eindeutige Felder).
4) Es gibt keine neuen Links von Canonical auf Legacy.
5) PR enthält exakt dieses Ticket (1 Ticket → 1 PR) und archiviert das Ticket nach `docs/legacy/tickets/`.

## Tests
- Unit: nicht erforderlich (nur Workflow + Docs), aber:
- Repo search check (must):
  - außerhalb `docs/legacy/` keine `docs/legacy/` Referenz im Snapshot Workflow
- Optional: Falls es einen bestehenden Snapshot-Test gibt, der Input-Dateien validiert, entsprechend anpassen.

## Constraints / Invariants (must not change)
- Closed-candle-only / no-lookahead Prinzipien bleiben unverändert
- Keine Änderung an Scoring-Logik oder Schwellen
- Keine erneute Schema-Version-Erhöhung

## Definition of Done (Codex must satisfy)
- [ ] Änderungen implementiert gemäß Acceptance Criteria
- [ ] Canonical docs aktualisiert (`docs/canonical/OUTPUT_SCHEMA.md`)
- [ ] PR erstellt: exakt **1 ticket → 1 PR**
- [ ] Ticket nach `docs/legacy/tickets/` verschoben (im selben PR)
