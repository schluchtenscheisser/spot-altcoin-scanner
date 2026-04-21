> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-19 Run Manifest einführen

## Context / Source
- Die aktuelle alleinige Referenz verlangt in Epic 9 neben `trade_candidates` ein separates technisches Run Manifest.
- Das Manifest ist kein Trading-Output, sondern ein Operabilitäts-Artefakt zur Nachvollziehbarkeit, Vergleichbarkeit und späteren Migration/Shadow-Mode-Auswertung.
- Es muss klar von `trade_candidates` getrennt sein und pro Run konsistent erzeugt werden.

## Goal
Ein separates Run Manifest wird pro Run erzeugt und ausgegeben, das mindestens:
- Run-Identität,
- Zeitstempel,
- Config-/Schema-Bezug,
- Feature-Flag-Zustand,
- Counts pro Pipeline-Stufe,
- Budget-Nutzung,
- Data-Freshness,
- Warnungen/Degradierungen,
- Laufzeit
technisch nachvollziehbar dokumentiert.

## Scope
- `scanner/pipeline/output.py` oder neue Datei `scanner/pipeline/manifest.py`
- ggf. enge, direkte Anbindung in `scanner/pipeline/__init__.py`, um Stage-Counts/Warnings/Freshness zusammenzuführen
- manifest-nahe Tests unter `tests/`

## Out of Scope
- Kein Markdown-Renderer (kommt in PR-20)
- Kein Excel-Renderer (kommt in PR-21)
- Keine formatübergreifenden Consistency-Tests (kommt in PR-22)
- Keine Änderung der Trading-SoT `trade_candidates` jenseits sauberer Trennung
- Keine Migration-/Feature-Flag-Logik selbst (kommt in PR-23/24), nur deren Dokumentation im Manifest
- Keine neue Decision-/Risk-/Tradeability-Logik

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CHANGELOG.md`

## Proposed change (high-level)
Before:
- Run-Metadaten sind nicht als separates, kanonisch definiertes Operabilitäts-Artefakt verfügbar.
- Nachvollziehbarkeit von Budgetauslastung, Stage-Counts, Feature-Flags und Datenfrische ist eingeschränkt oder verstreut.

After:
- Pro Run wird ein separates Manifest erzeugt.
- Das Manifest ist klar von `trade_candidates` getrennt.
- Mindestinhalt:
  - `run_id`
  - `timestamp_utc`
  - `config_hash`
  - `canonical_schema_version`
  - `feature_flags`
  - `counts_per_stage`
  - `shortlist_size_used`
  - `orderbook_top_k_used`
  - `data_freshness`
  - `warnings`
  - `duration_seconds`
- Das Manifest kann als separates JSON-Objekt und/oder separate Datei ausgegeben werden, aber nicht in `trade_candidates` vermischt.

Edge cases:
- partielle Degradierung / einzelne Fetch-Probleme => `warnings` dokumentieren
- Stage wird übersprungen oder reduziert => `counts_per_stage` muss trotzdem konsistent bleiben
- `feature_flags` unvollständig in Config => zentrale Defaults / explizite Normalisierung anwenden
- `canonical_schema_version` fehlt oder ist ungültig => klarer Fehler oder explizit definierter Fallback gemäß Canonical, nicht stillschweigend
- leere Warning-Liste bleibt leere Liste, nicht `null`, sofern Canonical Listenform vorsieht

Backward compatibility impact:
- Neues separates Operabilitäts-Artefakt.
- Keine Änderung der Trading-SoT außer klarer Trennung.
- Spätere Migrationstickets können sich auf dieses Manifest stützen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Manifest-Felder und deren Rollen exakt nach Canonical/aktueller Referenz.
- **Manifest ≠ Trading-Output:** Keine Trading-Wahrheit in das Manifest verschieben; keine Manifest-Felder in `trade_candidates` mischen.
- **Deterministische Form:** Bei identischem Run-Zustand müssen Inhalt und Feldstruktur stabil sein; nur echte Zeit-/ID-Felder dürfen naturgemäß variieren.
- **`canonical_schema_version` korrekt behandeln:** Wert stammt aus kanonischer Quelle (`docs/canonical/CHANGELOG.md` bzw. zugehöriger Canonical-Ablage); nicht frei erfinden.
- **Feature-Flags explizit:** `enabled/disabled`-Zustände müssen vollständig abgebildet sein; keine impliziten Lücken.
- **Counts pro Stage konsistent:** Keine negativen, nicht plausible oder uneinheitlichen Zählungen.
- **Warnings maschinenlesbar:** stabile Liste von Strings/Objekten, kein unstrukturierter Fließtext.
- **Missing vs invalid trennen:** Fehlende optionale Teile des Manifests ≠ ungültige Pflichtfelder.
- **Keine stillen Fallbacks bei Hash/Version/Flags:** Entweder sauber aus Quelle ableiten oder klar fehlschlagen.
- **Keine Dateinamenkollisionen:** Falls als Datei geschrieben wird, Namespace und Run-ID eindeutig und reproduzierbar definieren.

## Implementation Notes (optional but useful)
- Prüfe, ob `output.py` bereits Run-bezogene Metadaten sammelt; wenn nicht, neue `manifest.py` kann sauberer sein.
- `run_id` sollte eindeutig, aber nicht willkürlich sein; timestamp-basierte IDs sind laut Referenz vorgesehen.
- `counts_per_stage` sollte die tatsächlichen Pipeline-Stufen widerspiegeln, nicht historische oder geschätzte Werte.
- `data_freshness` sollte Timestamps oder gleichwertige strukturierte Frischeangaben enthalten, keine unstrukturierten Kommentare.
- `warnings` kann degradierte Fälle wie Rate-Limits, Partial-Fetches, stale Daten oder Soft-Degradierungen enthalten.

## Acceptance Criteria (deterministic)
1) Pro Run wird ein separates Manifest erzeugt, entweder als separates JSON-Objekt oder als eigene Datei, klar getrennt von `trade_candidates`.

2) Das Manifest enthält mindestens:
   - `run_id`
   - `timestamp_utc`
   - `config_hash`
   - `canonical_schema_version`
   - `feature_flags`
   - `counts_per_stage`
   - `shortlist_size_used`
   - `orderbook_top_k_used`
   - `data_freshness`
   - `warnings`
   - `duration_seconds`

3) `run_id` ist eindeutig pro Run und in einer konsistenten, dokumentierten Form erzeugt.

4) `canonical_schema_version` wird aus der kanonischen Quelle abgeleitet und nicht frei im Code erfunden.

5) `feature_flags` dokumentiert den Zustand aller relevanten aktiv/inaktiv-Flags vollständig.

6) `counts_per_stage` bildet die tatsächlichen Pipeline-Stufen konsistent und plausibel ab.

7) `warnings` ist maschinenlesbar und kann leer sein, ohne auf `null` oder unstrukturierten Fließtext zu kollabieren.

8) Das Manifest ist von `trade_candidates` getrennt; keines der beiden Objekte übernimmt die Rolle des anderen.

9) Wenn das Manifest als Datei geschrieben wird, ist der Dateiname kollisionssicher und klar dem Run zuordenbar.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (Feature-Flags / optionale Manifestteile nutzen zentrale Defaults oder klar definierte Standardwerte)
- **Config Invalid Value Handling:** ✅ (ungültige schema/version/flag-relevante Eingaben erzeugen klaren Fehler statt stiller Degradierung)
- **Nullability / kein bool()-Coercion:** ✅ (`warnings`, `data_freshness` und optionale Felder behalten ihre vorgesehene Struktur; keine implizite truthiness-Mutation)
- **Not-evaluated vs failed getrennt:** ✅ (Partial Failures / Warnings werden nicht als erfolgreiche Stage-Counts maskiert)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (Manifest-Schreibpfad darf keine halben/korrupten Artefakte hinterlassen)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (AC #3, #9)
- **Deterministische Sortierung / Tie-breaker:** ✅ (N/A für Kandidatensortierung; Manifest-Feldstruktur selbst bleibt stabil)

## Tests (required if logic changes)
- Unit:
  - Manifest enthält alle Mindestfelder
  - `feature_flags` vollständig und strukturiert
  - `warnings` bleibt leere Liste statt `null`, wenn keine Warnungen vorliegen
  - `canonical_schema_version` wird aus kanonischer Quelle übernommen
  - `counts_per_stage` plausibel und konsistent
  - `run_id`/Dateiname kollisionssicher formatiert

- Integration:
  - vollständiger Run erzeugt Manifest getrennt von `trade_candidates`
  - Manifest enthält echte Stage-Counts des Runs
  - Partial-Failure/Warning-Fall erscheint im Manifest
  - identischer strukturierter Runzustand erzeugt gleiches Feldschema

- Golden fixture / verification:
  - Snapshot/Golden-Files nur dort ergänzen/aktualisieren, wo das Manifest als neues separates Artefakt bewusst eingeführt wird
  - keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] Manifest bleibt getrennt von `trade_candidates`
- [ ] `trade_candidates` bleibt Trading-SoT
- [ ] `canonical_schema_version` stammt aus kanonischer Quelle
- [ ] `feature_flags` und `counts_per_stage` bleiben maschinenlesbar
- [ ] keine Scope-Ausweitung auf Markdown/Excel/Migration-Logik
- [ ] keine stillen Fallbacks bei Version/Hash/Flags
- [ ] keine Dateinamenkollisionen, falls Dateiausgabe implementiert wird

## Definition of Done (Codex must satisfy)
- [ ] Manifest-Implementierung gemäß Acceptance Criteria vorhanden
- [ ] Tests gemäß Ticket ergänzt/aktualisiert
- [ ] Trennung Manifest vs `trade_candidates` explizit abgesichert
- [ ] IDs / Version / Warnings / Counts robust und maschinenlesbar
- [ ] Keine Scope-Überschreitung in Markdown/Excel/Migration
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
