# PR5 — Backtest E2-K: Kalender-Tage statt Snapshot-Index

## Problem
`scanner/pipeline/backtest_runner.py:run_backtest_from_snapshots()` nutzt Snapshot-Index-Offsets:
- t_trigger_max, t_hold werden als "Anzahl Snapshots" interpretiert.
Wenn Tage fehlen, wird Zeit komprimiert -> falsche Semantik.

## Ziel
- t_trigger_max und t_hold müssen als KALENDER-TAGE interpretiert werden.
- Wenn Snapshots fehlen, darf das nicht so aussehen als wären sie "passiert".
- Backtest soll deterministisch bleiben.

## Nicht-Ziele
- Keine Änderung an Score-Definitionen.
- Keine Änderung am SnapshotManager Output.

## Fundstellen
- scanner/pipeline/backtest_runner.py
  - run_backtest_from_snapshots(...)
  - _evaluate_candidate(...)

## Implementationshinweise (konkret)
- Baue eine Abbildung date->snapshot (bereits vorhanden: index_by_date).
- Für ein t0_date:
  - trigger window ist t0_date..t0_date+t_trigger_max (kalender) INKLUSIVE t0.
  - hold window beginnt am trigger_day+1 bis trigger_day+t_hold (kalender).
- Für fehlende Tage:
  - treat as "no data": skip day in evaluation (keine close/high).
  - Das reduziert die Chance zu triggern/hits korrekt, statt Zeit zu komprimieren.
- Nutze `datetime.date` Parsing aus ISO YYYY-MM-DD.

## Neue Tests (Test-first)
Neuer Testfile z. B. `tests/test_backtest_calendar_days.py`:
- Construct in-memory snapshots list mit Lücken:
  - 2026-01-01, 2026-01-02, 2026-01-05 (fehlend: 03,04)
- Konfig: t_trigger_max=3, t_hold=2
- Assert:
  - Mit kalenderlogik ist t_trigger_max window: 01..04 (Snapshots nur 01,02 vorhanden)
  - Index-basiert würde 01..(01+3)=01,02,05 -> das wäre falsch; Test soll sicherstellen, dass 05 NICHT im trigger window landet.
- Ähnlich für hold window.

## Akzeptanzkriterien
- Tests belegen Missing-days korrekt
- Bestehende Golden Tests (falls vorhanden) ggf. anpassen nur wenn fachlich notwendig
- CI grün
