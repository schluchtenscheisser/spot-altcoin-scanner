## Implementation Notes
### Ticket-Autor Checklistle (No-Guesswork, Pflicht bei Code-Tickets)

> Ziel: Codex soll nicht interpretieren müssen. Deshalb müssen Defaults, Missing-Keys, Nullability und „nicht evaluiert“ vs. „evaluiert aber fehlgeschlagen“ explizit im Ticket stehen und getestet werden.

#### A) Defaults / Config-Semantik (Pflicht, wenn Config gelesen/validiert wird)
- [x] **Kein raw-dict Default drift:** N/A – keine Config betroffen
- [x] **Missing vs Invalid getrennt:** N/A – keine Config Keys
- [x] **Keine „silent fallbacks“:** N/A – keine Fallback-Logik

#### B) Nullability / Schema / Output (Pflicht, wenn Outputs betroffen sind)
- [x] **Nullable Felder explizit:** N/A – keine Schema/Output-Felder
- [x] **Kein bool()-Coercion:** N/A

#### C) Edgecases, die oft übersehen werden (Pflicht, wenn relevant)
- [x] **Nicht evaluiert ≠ evaluiert aber fail:** N/A
- [x] **Namespace/Kollisionen:** N/A (nur Dateimoves im Repo)
- [x] **Strict/Preflight Atomizität:** N/A

#### D) Tests (Pflicht bei Logikänderungen)
- [x] Mindestens 1 Test: Missing key → Default greift (oder bewusstes Fail) — N/A
- [x] Mindestens 1 Test: Invalid value → klarer Fehler/Reason — N/A
- [x] Mindestens 1 Test: Edgecase — N/A

---

## Title
[P3] Legacy-Tickets aufräumen: alle *.md nach docs/legacy/tickets/archive verschieben

## Context / Source (optional)
- Wiederkehrende Repo-Hygiene: Der Ordner `docs/legacy/tickets/` soll regelmäßig geleert werden, indem alte Ticket-Markdown-Dateien ins Archiv verschoben werden.

## Goal
Alle Markdown-Dateien (`*.md`), die **direkt** in `docs/legacy/tickets/` liegen, sollen nach `docs/legacy/tickets/archive/` verschoben werden, damit `docs/legacy/tickets/` für aktuelle/aktive Inhalte sauber bleibt.

## Scope
Betroffene Pfade/Dateien:
- Quelle: `docs/legacy/tickets/*.md` (nur Dateien, **keine** Unterordner-Rekursion)
- Ziel: `docs/legacy/tickets/archive/`

## Out of Scope
- Keine Änderungen am Inhalt der Tickets.
- Keine Umbenennungen (nur Verschieben).
- Keine Verschiebung von Nicht-Markdown-Dateien.
- Keine Rekursion in Unterordner (nur Top-Level von `docs/legacy/tickets/`).
- Keine Änderungen außerhalb von `docs/legacy/tickets/` und `docs/legacy/tickets/archive/`.

## Canonical References (important)
- `docs/tickets/_TEMPLATE.md` (Ticket-Format)

## Proposed change (high-level)
- Before:
  - `docs/legacy/tickets/` enthält eine Menge `*.md` Dateien (legacy Tickets).
- After:
  - `docs/legacy/tickets/` enthält **keine** `*.md` Dateien mehr (Top-Level).
  - Alle zuvor dort vorhandenen `*.md` Dateien befinden sich unter `docs/legacy/tickets/archive/` (gleiche Dateinamen).
- Edge cases:
  - Wenn `docs/legacy/tickets/archive/` nicht existiert: Ordner anlegen.
  - Wenn keine `*.md` Dateien im Quellordner existieren: No-op (ohne Fehler).
  - Dateien, die bereits in `docs/legacy/tickets/archive/` liegen, bleiben unangetastet.
  - Dateien, die nicht im Top-Level liegen (z. B. `docs/legacy/tickets/some/subdir/x.md`), bleiben unangetastet.
- Backward compatibility impact:
  - Links/Verweise auf Pfade können sich ändern. **Kein** automatisches Link-Rewrite in diesem Ticket (bewusst out-of-scope). Das Ziel ist reines Archivieren.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
> Dieses Ticket ist eine reine Datei-Operation. Trotzdem bitte deterministisch und reproduzierbar vorgehen.

- Verwende **git-basierte** Moves (`git mv`), damit die Historie sauber bleibt.
- Verschiebe **nur** Dateien, die dieses Pattern erfüllen:
  - `docs/legacy/tickets/*.md` (Top-Level, keine Unterordner)
- Zielpfad ist **immer**:
  - `docs/legacy/tickets/archive/<DATEINAME>.md`
- Lege `docs/legacy/tickets/archive/` bei Bedarf an.
- Keine weiteren Änderungen (kein Formatieren, kein Umbenennen, kein Inhalt anfassen).

## Implementation Notes (optional but useful)
Beispiel (nur als Orientierung, nicht zwingend 1:1 so umsetzen):
- `mkdir -p docs/legacy/tickets/archive`
- für jede Datei in `docs/legacy/tickets/*.md`:
  - `git mv "<file>" "docs/legacy/tickets/archive/<basename>"`

## Acceptance Criteria (deterministic)
1) **Alle** Dateien, die zum Start `docs/legacy/tickets/*.md` matchen, existieren danach unter `docs/legacy/tickets/archive/` mit identischem Dateinamen.  
2) `docs/legacy/tickets/` enthält danach **keine** `*.md` Dateien mehr (Top-Level).  
3) `docs/legacy/tickets/archive/` existiert nach der Änderung.  
4) Es gibt **keine** weiteren Änderungen außerhalb dieser Pfade (prüfbar via `git status` / Diff).  
5) Wenn keine Dateien matchen, läuft der Vorgang ohne Fehler durch und erzeugt keine unnötigen Diffs (außer ggf. Ordneranlage, falls erforderlich).

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (N/A)
- **Config Invalid Value Handling:** ✅ (N/A)
- **Nullability / kein bool()-Coercion:** ✅ (N/A)
- **Not-evaluated vs failed getrennt:** ✅ (N/A)
- **Strict/Preflight Atomizität:** ✅ (N/A)
- **ID/Dateiname Namespace-Kollisionen:** ✅ (N/A)
- **Deterministische Sortierung/Tie-breaker:** ✅ (N/A)

## Tests (required if logic changes)
- Unit: N/A
- Integration: N/A
- Golden fixture / verification: N/A

## Constraints / Invariants (must not change)
- Keine Inhaltsänderungen an den `.md` Dateien.
- Keine Verschiebung von Dateien außerhalb des definierten Globs.
- Keine Rekursion.

---

## Definition of Done (Codex must satisfy)
(Reference: `docs/canonical/WORKFLOW_CODEX.md`)

- [ ] Dateien gemäß Scope per `git mv` verschoben
- [ ] Keine weiteren Änderungen außerhalb der betroffenen Pfade
- [ ] Ticket nach PR-Erstellung nach `docs/legacy/tickets/` verschoben (N/A – dieses Ticket IST bereits Legacy/Housekeeping; nur anwenden, falls euer Workflow das verlangt)

---

## Metadata (optional)
```yaml
created_utc: "2026-03-01T00:00:00Z"
priority: P3
type: docs
owner: codex
related_issues: []
```
