# Codex Workflow — Tickets → 1 PR, Canonical Docs First (Canonical)

## Machine Header (YAML)
```yaml
id: CANON_WORKFLOW_CODEX
status: canonical
audience:
  - gpt_codex
  - humans
ticket_inbox: docs/tickets
ticket_archive: docs/legacy/tickets
canonical_root: docs/canonical
autodocs_read_only:
  - docs/code_map.md
  - docs/GPT_SNAPSHOT.md
one_ticket_one_pr: true
last_updated_utc: "2026-02-25T20:29:01Z"
```

## 0) Ziel
Diese Arbeitsanweisung beschreibt den **verbindlichen Bearbeitungsprozess** für GPT-Codex:

- Codex holt **genau ein Ticket** aus `docs/tickets/`
- Codex bearbeitet es vollständig
- Codex erstellt **genau einen PR pro Ticket**
- Codex aktualisiert **Canonical Docs** konsequent nach dem Authority-Prozess
- Danach verschiebt Codex das Ticket nach `docs/legacy/tickets/`

**Wichtig:** Canonical Docs sind die Single Source of Truth. Tickets sind Arbeitsaufträge, keine Wahrheit.

---

## 1) Authority & Dokument-Hierarchie (verbindlich)
Codex muss diese Dokumente als Autorität behandeln:

1) `docs/canonical/AUTHORITY.md` (Precedence & Change Process)
2) `docs/canonical/INDEX.md` (Navigation; welche Canonical Docs existieren)
3) `docs/code_map.md` (read-only; Code-Struktur, nur Referenz)
4) `docs/GPT_SNAPSHOT.md` (read-only; Status/Referenz)

Precedence bei Konflikten:
- `docs/canonical/*` > `docs/*` (support) > auto-docs > `docs/legacy/*`

---

## 2) Ticket Lifecycle (Inbox → Archive)

### 2.1 Inbox
- Alle neuen Tickets liegen als Markdown unter: `docs/tickets/`
- Codex bearbeitet **immer das nächste Ticket** deterministisch:
  - sortiere Ticket-Dateinamen lexikographisch (ASCII) aufsteigend
  - nimm die erste Datei

### 2.2 Archive
- Nach erfolgreicher Bearbeitung (PR erstellt) wird das Ticket verschoben nach:
  - `docs/legacy/tickets/<original_filename>.md`

### 2.3 Ticket darf erst archiviert werden, wenn:
- PR ist erstellt
- PR enthält alle Code- und Doku-Änderungen
- Ticket-Checklist ist erfüllt (siehe Abschnitt 6)

---

## 3) 1 Ticket → 1 PR (verbindlich)
- Pro Ticket wird **genau ein** PR erstellt.
- Codex darf **niemals** mehrere Tickets in einem PR kombinieren.
- Wenn ein Ticket mehrere Themen enthält, bleibt es trotzdem 1 Ticket → 1 PR.

Branch Naming (canonical):
- `ticket/<ticket_slug>` oder `docs-ticket/<ticket_slug>`

PR Title (canonical):
- `Ticket: <ticket filename> — <short summary>`

PR Body (required):
- Link/Path zum Ticket
- „Docs impact summary“ (siehe Abschnitt 5.4)
- Welche Canonical Docs wurden geändert und warum
- Ob `VERIFICATION_FOR_AI.md` angepasst wurde (ja/nein)

---

## 4) Execution Order (Authority Process in PRs)

### 4.1 Schrittfolge (verbindlich)
Wenn das Ticket fachliche Logik, Parameter, Schwellenwerte, Scores, Rankings, Outputs oder Datenhandling ändert:

1) **Canonical Docs zuerst aktualisieren** (Requirement/Spec)
2) **Dann Code ändern** (Implementation)
3) **Dann Verification/Fixtures** aktualisieren (wenn relevant)
4) Danach **sanity checks** (Link-/Driftchecks)
5) PR erstellen
6) Ticket archivieren

Wenn Codex glaubt, dass keine Canonical Doku betroffen ist:
- Muss er das explizit im PR Body begründen: `Docs not required because: ...`

---

## 5) Canonical Docs Update Rules

### 5.1 Determinism Pflicht
Canonical muss deterministisch sein:
- closed-candle-only
- no lookahead
- klare Tie-Handling / NaN-Policies
- keine „implementation-defined“ Defaults in Canonical

### 5.2 Welche Canonical Dateien typischerweise betroffen sind
**Routing (Faustregeln):**
- Setup Logik/Score (Breakout etc.): `docs/canonical/SCORING/*.md`
- Global Ranking / Dedup / Sort: `docs/canonical/SCORING/GLOBAL_RANKING_TOP20.md`
- Liquidity / Slippage / Grades / Re-rank: `docs/canonical/LIQUIDITY/*.md`
- Features (EMA/ATR/Rank/Volume): `docs/canonical/FEATURES/*.md`
- Outputs (Felder/Manifest/Trade levels): `docs/canonical/OUTPUT_SCHEMA.md` und ggf. `docs/canonical/OUTPUTS/*`
- Providers / As-Of / closed candles: `docs/canonical/DATA_SOURCES.md`
- Mapping / Collisions / Overrides: `docs/canonical/MAPPING.md`
- Backtest models: `docs/canonical/BACKTEST/*.md`

### 5.3 Verification Pflicht (wenn Verhalten ändert)
Wenn ein Ticket eine Rechenlogik/Schwelle/Curve/Score beeinflusst:
- `docs/canonical/VERIFICATION_FOR_AI.md` muss angepasst werden:
  - Expected values ergänzen/ändern
  - Boundary cases aktualisieren
  - Comparison rule darf nicht aufweichen

### 5.4 PR “Docs impact summary” (required)
Im PR Body muss ein Abschnitt stehen:

- `Docs impact summary:`
  - `Canonical docs updated:` (Liste)
  - `What changed:` (knapp: thresholds/formulas/fields)
  - `Verification updated:` yes/no (+ welche fixtures)

---

## 6) Ticket Completion Checklist (must satisfy before archive)
Für jedes Ticket muss Codex vor dem Verschieben nach Legacy sicherstellen:

- [ ] Code implementiert Ticket-Anforderungen
- [ ] Canonical Docs aktualisiert (wenn fachliche Änderung)
- [ ] `VERIFICATION_FOR_AI.md` aktualisiert (wenn scoring/logic geändert)
- [ ] Keine neuen `docs/v2/` Referenzen außerhalb legacy
- [ ] Keine Links auf `docs/legacy/*` aus Canonical (außer bewusst als legacy markiert)
- [ ] PR erstellt (1 Ticket → 1 PR)
- [ ] Ticket nach `docs/legacy/tickets/` verschoben

---

## 7) “Next Ticket” Command Contract (für dich als Operator)
Du musst Codex nur sagen:

> „Hole dir das nächste Ticket aus `docs/tickets/` und bearbeite es. Halte dabei die Anweisungen aus `docs/canonical/WORKFLOW_CODEX.md` ein.“

Codex muss dann:
1) nächstes Ticket deterministisch auswählen
2) Workflow befolgen
3) PR erstellen
4) Ticket archivieren

---

## 8) Recommended Ticket Format (optional, aber hilfreich)
Tickets in `docs/tickets/` sollten enthalten:

- Titel
- Kontext / Ziel
- Akzeptanzkriterien (bullet list, deterministisch)
- Betroffene Module (optional, falls bekannt)
- „Docs likely affected“ (optional; Codex entscheidet final dennoch selbst via Routing)

Tickets müssen **nicht** `AUTHORITY.md` erwähnen — Codex holt sich die Regeln aus diesem Workflow-Dokument.

---

## 9) Non-goals
- Tickets sind keine dauerhafte Doku
- Legacy ist nicht autoritativ
- Codex soll keine Spez “erraten”; wenn unklar, muss er im PR Body eine Frage als TODO/Blocker notieren (aber canonical nicht verwässern)
