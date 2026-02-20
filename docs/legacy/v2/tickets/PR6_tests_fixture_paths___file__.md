# PR6 — Tests: Fixture Paths robust (Path relativ zu __file__)

## Problem
Mindestens ein Test nutzt `Path("tests/golden/fixtures/...")` und hängt vom CWD ab.
Beispiel: `tests/test_t81_indicator_ema_atr.py`

## Ziel
- Alle Tests sollen fixtures über `Path(__file__).resolve()` referenzieren.
- Tests laufen stabil unabhängig vom working directory.

## Nicht-Ziele
- Keine Änderung an Fixture-Inhalten.
- Keine Änderung an Testlogik außer Pfadbau.

## Fundstellen (start)
- tests/test_t81_indicator_ema_atr.py
  - FIXTURE_PATH = Path("tests/golden/fixtures/....json")

## Vorgehen
- Ersetze durch:
  - `BASE = Path(__file__).resolve().parent`
  - `FIXTURE_PATH = BASE / "golden" / "fixtures" / "...json"`
  - oder `Path(__file__).resolve().parent / "golden" / ...` je nach Struktur.

## Neue Tests
Hier reicht die Änderung selbst; optional:
- Mini-Test, der CWD ändert und die betroffenen Tests weiterhin lädt (nur falls sinnvoll).
In der Regel genügt: bestehende Tests werden dadurch robuster und bleiben grün.

## Akzeptanzkriterien
- Tests grün
- Keine CWD-Abhängigkeit mehr

## Abschluss- und Archiv-Schritt (Pflicht)
Nach Merge/Abschluss dieses Tickets:
1. Verschiebe **diese** Ticket-Datei nach `docs/legacy/v2/tickets/` (gleicher Dateiname).
2. Aktualisiere das Dokument `docs/v2/Zwischenstand und Ticket-Status (Canonical v2).md`, so dass dieses für die nächste Session wieder den dann gültigen Zwischenstand aufweist. Beachte dabei, dass alle relevanten Informationen, die für eine neue Codex-Session ohne Wissensverlust erforderlich sind, in dem Dokument enthalten sind.
