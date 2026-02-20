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
