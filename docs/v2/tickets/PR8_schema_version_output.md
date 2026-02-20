# PR8 — Schema Versioning: `schema_version` im Output + SCHEMA_CHANGES pflegen

## Kontext / Regel
Aus docs/AGENTS.md:
- Schema changes: bump `schema_version` + update `docs/SCHEMA_CHANGES.md`

Im Code ist aktuell kein eindeutiger `schema_version` Treffer im scanner/ Code sichtbar (möglicherweise fehlt es im finalen Output).

## Ziel
- Füge ein klares `schema_version` Feld in den finalen Output (Report/JSON) ein.
- Stelle sicher, dass bei schema-relevanten Änderungen die Version bumpbar ist.
- Ergänze `docs/SCHEMA_CHANGES.md` mit Eintrag, warum/was.

## Nicht-Ziele
- Kein Redesign des gesamten Output-Formats.
- Keine Änderung an Snapshot format, außer es ist explizit Teil des finalen Outputs.

## Fundstellen (zu ermitteln)
- Stelle im Code, wo finaler JSON/Report geschrieben wird (writer/exporter).
  - Suche nach json.dump / write_report / output_dir / report.json etc.
- Falls Snapshot auch “Output” ist, nur ergänzen wenn es “final user artifact” ist.

## Implementationshinweise
- `schema_version` als string oder int (wähle eine Form und halte sie stabil).
- Ein zentraler Ort (z. B. constants/config) ist besser als mehrfach hardcoden.

## Neue Tests (Test-first)
- Test, der einen minimalen Pipeline-Run oder Output-Writer in-memory ausführt und prüft:
  - output enthält `schema_version`
  - ist nicht leer
- Wenn es bereits Golden JSON gibt: Update golden fixtures entsprechend (nur in dieser PR).

## Doku
- `docs/SCHEMA_CHANGES.md` ergänzen:
  - Version bump
  - kurze Beschreibung der Felder

## Akzeptanzkriterien
- schema_version ist im Output vorhanden
- docs/SCHEMA_CHANGES.md aktualisiert
- Tests grün

## Abschluss- und Archiv-Schritt (Pflicht)
Nach Merge/Abschluss dieses Tickets:
1. Verschiebe **diese** Ticket-Datei nach `docs/legacy/v2/tickets/` (gleicher Dateiname).
2. Aktualisiere das Dokument `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`, so dass dieses für die nächste Session wieder den dann gültigen Zwischenstand aufweist. Beachte dabei, dass alle relevanten Informationen, die für eine neue Codex-Session ohne Wissensverlust erforderlich sind, in dem Dokument enthalten sind.
