# PR3 — Unlock Overrides: defensive Parsing von days_to_unlock

## Problem
In `scanner/pipeline/filters.py` wird `days_to_unlock` via `int(days_to_unlock)` geparsed.
Ungültige Werte (None, "", "7d", "soon") führen zum Crash.

## Ziel
- Unlock overrides dürfen die Pipeline nicht crashen.
- Ungültige Einträge werden ignoriert:
  - Log warning (inkl. symbol + original value)
  - Override wird für dieses Symbol nicht angewendet
- Gültige Werte (0, positive ints als string/int) funktionieren weiterhin.

## Nicht-Ziele
- Kein Redesign des override Formats.
- Keine Änderung an default `config/unlock_overrides.yaml` (ist aktuell leer).

## Fundstellen
- scanner/pipeline/filters.py
  - parsing/loop über unlock overrides

## Implementationshinweise
- Parsing helper:
  - try: days = int(value)
  - except (TypeError, ValueError): invalid -> warn + continue
  - optional: days < 0 ebenfalls invalid
- Log:
  - logger.warning("Invalid days_to_unlock for %s: %r", symbol, value)

## Neue Tests (Test-first)
Neuer Test (z. B. `tests/test_unlock_overrides_parsing.py`):
- Übergib overrides mit mix:
  - valid: "7", 0, 14
  - invalid: None, "", "7d", -3
- Assert:
  - invalid entries werden ignoriert (keine Exception)
  - valid entries werden angewendet (Filter-/Unlock-Entscheidung erwartbar)
- Test muss ohne Dateien auskommen: overrides als Dict/List direkt einspeisen.

## Akzeptanzkriterien
- Keine Exception bei invalid overrides
- Warn-Logs vorhanden (nicht zwingend im Test prüfen)
- Tests grün

## Abschluss- und Archiv-Schritt (Pflicht)
Nach Merge/Abschluss dieses Tickets:
1. Verschiebe **diese** Ticket-Datei nach `docs/legacy/v2/tickets/` (gleicher Dateiname).
2. Aktualisiere das Dokument `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`, so dass dieses für die nächste Session wieder den dann gültigen Zwischenstand aufweist. Beachte dabei, dass alle relevanten Informationen, die für eine neue Codex-Session ohne Wissensverlust erforderlich sind, in dem Dokument enthalten sind.
