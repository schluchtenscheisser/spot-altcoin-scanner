# PR2 — Closed-Candle Gate: None => insufficient history (Reversal Scoring)

## Problem
In `scanner/pipeline/scoring/reversal.py` liefert `_closed_candle_count(...)` in einigen Fällen `None`.
Die Gate-Logik behandelt derzeit nur `closed_candles < min_history` als insufficient,
aber `None` rutscht durch und Kandidaten werden gescored, obwohl Historie unklar/fehlend ist.

## Ziel
- Wenn `_closed_candle_count(...)` `None` liefert:
  - Kandidat muss als "insufficient_history" behandelt werden (keine normalen Scores).
  - Das Verhalten soll konsistent zum Fall `closed_candles < min_history` sein.
- Logging: gerne debug/info/warn, aber deterministisch und nicht noisy.

## Nicht-Ziele
- Keine Änderungen an mathematischen Score-Formeln selbst.
- Keine Änderung an der Definition von `min_history_*` in dieser PR (kommt in PR4).

## Fundstellen
- scanner/pipeline/scoring/reversal.py
  - _closed_candle_count(...)
  - Stelle, wo `min_history_reversal_1d` geprüft wird und early-exit passiert.

## Implementationshinweise
- Gate-Bedingung so ändern, dass gilt:
  - if closed_candles is None: insufficient_history
  - elif closed_candles < min_history: insufficient_history
  - else: normaler Pfad
- Entscheide, wie "insufficient_history" im Rückgabeformat repräsentiert ist (bestehende Konvention beibehalten).

## Neue Tests (Test-first)
Neuer Unit-Test (z. B. `tests/test_reversal_closed_candle_gate.py`):
- Konstruiere minimalen Input, der `_closed_candle_count` zu `None` führt:
  - z. B. last_closed_idx < 0 oder fehlende required series
- Assert:
  - scoring Ergebnis markiert insufficient_history (so wie beim < min_history Fall)
  - keine "normalen" Scores werden erzeugt (je nach Outputstruktur: Score None/0 + reason flag)
- Zusatztet:
  - Fall closed_candles == min_history => nicht insufficient.

## Akzeptanzkriterien
- Neue Tests vorhanden und grün
- Bestehende Tests grün
- Verhalten: None => insufficient_history
