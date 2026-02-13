# Thema 8 – Dokumentationskonsolidierung (Closed-Candle, Baselines, EMA/ATR, QuoteVolume)

Diese Datei bündelt die für Thema 8 bestätigten Konventionen in kompakter Form, um Konflikte in stark frequentierten Kern-Dokumenten zu vermeiden.

## 1) Closed-Candle / As-Of-Konvention
- Feature-Berechnung basiert auf der letzten **geschlossenen** Kerze `T`.
- Formal: `T = max(i where closeTime[i] <= asof_ts_ms)`.
- Falls kein `asof_ts_ms` gesetzt ist, wird der letzte verfügbare Kline-Index verwendet.

## 2) Lookback-/Baseline-Konvention
- Baselines schließen die aktuelle Kerze aus (keine Look-ahead-Verzerrung).
- Beispiele:
  - Volume-Baseline: `mean(volume[t-14 .. t-1])`
  - Breakout-Resistance: `max(high[t-lookback .. t-1])`

## 3) Indikator-Konventionen
- EMA: Initialisierung mit `SMA(period)`, danach rekursive EMA-Fortführung.
- ATR: Wilder-Definition (rekursive Glättung nach ATR-Initialisierung).

## 4) QuoteVolume-Konvention
- Wenn Kline-`quoteVolume` vorhanden ist, werden Quote-Features berechnet:
  - `volume_quote`
  - `volume_quote_sma_14`
  - `volume_quote_spike`
- Wenn nicht vorhanden, bleiben diese keys im Feature-Output aus.

## 5) Schema-/Historienhinweis
- Historische Schema-/Semantikänderungen sind in `docs/SCHEMA_CHANGES.md` dokumentiert.
- Diese Thema-8-Datei dient als kompakte, konfliktarme Referenz für die laufende Entwicklung.
