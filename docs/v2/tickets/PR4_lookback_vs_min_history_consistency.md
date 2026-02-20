# PR4 — lookback_days_1d vs min_history_*: Konsistenz & Closed-Candle Realität

## Problem
Konfig hat z. B.:
- lookback_days_1d: 120
- min_history_reversal_1d: 120
Wenn die aktuelle Tageskerze offen ist, gibt es oft nur 119 closed candles.
Das kann dazu führen, dass Scoring fast immer "insufficient" ist oder inkonsistent wirkt.

## Ziel
Definiere eine klare Regel und implementiere sie so, dass sie testbar und stabil ist.

### Soll-Regel (präzise)
- `min_history_*_1d` bezieht sich auf CLOSED candles.
- Wenn lookback X Kerzen lädt, muss garantiert sein, dass mindestens `min_history` CLOSED Kerzen verfügbar sind.
- Lösung soll deterministisch sein und ohne Austausch der Datenquelle funktionieren.

## Akzeptierte Lösungsansätze (wähle minimal-invasive)
A) Erhöhe effektiv geladenen Lookback für 1D um +1 (oder +2) damit closed>=min_history robust erfüllt ist.
B) Passe `min_history_*` Defaults automatisch an (z. B. min_history = min(min_history, lookback-1)) — nur wenn in v2 Spezifikation erlaubt.
C) Gate-Logik berücksichtigt offen/closed sauber und dokumentiert das im Output.

## Nicht-Ziele
- Keine Änderung an der Gesamt-Strategie/Signals.
- Keine Änderung am Snapshot-Format.

## Fundstellen (wahrscheinlich betroffen)
- scanner/config.py oder config loader
- pipeline feature history fetch (wo lookback angewendet wird)
- scoring modules, die min_history prüfen (reversal/breakout/pullback)

## Neue Tests (Test-first)
- Schreibe Tests, die das konkrete Off-by-one Szenario nachstellen:
  - Dataset mit 120 values, aber last candle gilt als "open", so dass closed_count=119
- Assert:
  - Nach Fix gilt: bei konfig (lookback=120, min_history=120) ist scoring NICHT permanent insufficient, sondern Regel erfüllt (z. B. durch lookback+1 oder sauberer closed selection).
- Falls du lookback+1 implementierst: Test, dass tatsächlich eine zusätzliche Kerze angefragt/verarbeitet wird (ohne Netzwerk; über stubbed history provider).

## Doku
- Wenn eine neue Regel entsteht, ergänze sie in v2 Doku (wo passend, z. B. docs/v2/20_FEATURE_SPEC.md) – nur minimal.

## Akzeptanzkriterien
- Neue Tests grün
- Verhalten konsistent: closed>=min_history ist realistisch erreichbar
- Keine unerwarteten Regressionen in anderen Tests
