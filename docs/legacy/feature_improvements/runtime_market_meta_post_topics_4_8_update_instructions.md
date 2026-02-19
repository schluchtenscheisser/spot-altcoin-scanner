# Anpassungsanleitung: `runtime_market_meta_YYYY-MM-DD.json` nach Umsetzung der Themen 4–8

Dieses Dokument beschreibt, **welche Änderungen** du an deinem neuen Export-JSON (`snapshots/runtime/runtime_market_meta_YYYY-MM-DD.json`) vornehmen solltest, **sobald** die Themen 4 bis 8 aus deiner Roadmap vollständig umgesetzt und gemerged sind. fileciteturn12file1 fileciteturn12file0

> Aktueller Status laut dir: Themen 1–3 sind bereits umgesetzt. Dieses Dokument ist für den späteren Schritt „Export-Überarbeitung“ gedacht.

---

## 0) Ausgangslage (Artifacts pro Run)

Du gibst bei Analysen künftig standardmäßig mit:
- `runtime_market_meta_YYYY-MM-DD.json` (neuer Export: CMC-Identität + MEXC Trading-Rules + 24h Ticker-Snapshot)
- `YYYY-MM-DD.json` (Scanner-Output: Features/Scores/Reasons, inkl. Meta)
- `ohlcv_snapshot.csv.gz` (OHLCV Snapshot, inkl. close_time & quote_volume nach Thema 3)

Die Themen 4–8 verändern primär **Feature-Semantik**, **Reproduzierbarkeit** und **Dokumentations-/Konventions-Standards**. fileciteturn12file6 fileciteturn12file1

---

## 1) Ziel der Anpassungen am Meta-Export

Nach Themen 4–8 soll der Meta-Export:
1) **Join- und Replay-sicher** mit `YYYY-MM-DD.json` und OHLCV-Snapshots sein (ein gemeinsamer As-Of-Anker, gleiche Versions-/Konfigurationsanker). fileciteturn12file1 fileciteturn12file19  
2) **Feature-Semantik-Wechsel** explizit machen (z. B. EMA-Init per SMA, Wilder-ATR, Lookback-Konventionen). fileciteturn12file1  
3) **QuoteVolume-/Baseline-Features** (Thema 7/6) indirekt stützen, indem die Datenbasis/Spaltenlage für OHLCV eindeutig dokumentiert ist. fileciteturn12file0 fileciteturn12file3  

---

## 2) Pflichtänderungen (empfohlen als „v1.1“ der Spezifikation)

### 2.1 `meta.asof_ts_ms` ergänzen (Single Source of Truth)
**Warum:** In deiner Pipeline ist `asof_ts_ms` der zentrale Zeitpunkt, um „last closed candle“ deterministisch zu bestimmen und Replays stabil zu machen. fileciteturn12file4

**Änderung:**
- Ergänze im Top-Level `meta`:
  - `asof_ts_ms` (int, Millisekunden seit Epoch)
  - `asof_iso` (string, ISO 8601 UTC) **optional**, aber praktisch für Debugging

**Regel:**
- `asof_ts_ms` ist maßgeblich; `asof_iso` ist nur Darstellung (muss denselben Zeitpunkt repräsentieren). fileciteturn12file4

**Join-Check:**
- `runtime_market_meta.meta.asof_ts_ms == YYYY-MM-DD.json.meta.asof_ts_ms` (beide Dateien müssen denselben Wert tragen). fileciteturn12file19

---

### 2.2 Version-/Konfigurationsanker angleichen
Nach Thema 8 sollen Konventionen (closed candle, as-of, baseline windows) sauber dokumentiert sein. fileciteturn12file0

**Änderung (Top-Level `meta` ergänzen):**
- `export_version` (string) – z. B. `"1.1"`
- `config_version` (string) – aus `ScannerConfig.config_version`
- `spec_version` (string) – aus `ScannerConfig.spec_version`
- `run_mode` (string) – aus `ScannerConfig.run_mode`

Diese Felder sind in der CodeMap/Config als Konzepte vorhanden. fileciteturn12file15

**Zweck:**
- Wenn sich Feature-Semantik ändert (Thema 4–6) und du Golden-Tests aktualisierst, kannst du alte Runs sauber einordnen. fileciteturn12file1

---

### 2.3 Referenz auf zugehörige Artefakte (Artifact Inventory)
Da mehrere Snapshots pro Run zusammengehören, ist ein „Inventory“ hilfreich.

**Änderung (Top-Level `meta` ergänzen):**
- `artifacts` (object):
  - `scanner_json` (string) – erwarteter Dateiname, z. B. `"2026-02-11.json"`
  - `ohlcv_snapshot` (string) – z. B. `"ohlcv_snapshot.csv.gz"`
  - optional: `marketcap_snapshot` (string), falls du es weiter führst

**Optional (sehr nützlich):**
- `sha256` pro Artifact (string) – wenn du spätere Replays wirklich identisch machen willst.

**Zweck:**
- Schnelle Plausibilisierung, dass die richtigen Dateien zusammen verwendet werden.

---

## 3) Optionale Änderungen (nur wenn du die entsprechenden Themen tatsächlich umsetzt)

### 3.1 `quality` ausbauen für QuoteVolume-Features (Thema 7)
Thema 7 baut auf QuoteVolume-Feldern in den Rohdaten auf und fordert Dokumentation. fileciteturn12file0

**Optionale Ergänzungen:**
- Run-global (unter `meta`):
  - `ohlcv_columns` (array[string]) – z. B. `["open_time","close_time","open","high","low","close","volume","quote_volume","timeframe","symbol"]`
- Oder pro Coin (unter `coins[...].quality`):
  - `has_ohlcv_quote_volume` (bool)

**Zweck:**
- Sofort sichtbar, ob QuoteVolume-basierte SMA/Spikes überhaupt sauber ableitbar sind. fileciteturn12file3 fileciteturn12file0

---

### 3.2 Benchmark-/Relative-Strength (RS) Meta (wenn umgesetzt)
`improvements_existing_data.md` schlägt RS vs BTC/ETH über dieselbe API vor (keine neue Quelle). fileciteturn12file17

Wenn du RS-Features wirklich implementierst und diese in `YYYY-MM-DD.json` auftauchen, ist es sinnvoll, im `runtime_market_meta` zu dokumentieren:

**Optionale Ergänzung (Top-Level `meta`):**
- `benchmarks` (object), z. B.:
  - `btc_symbol`: `"BTCUSDT"`
  - `eth_symbol`: `"ETHUSDT"`
  - `timeframes`: `["1d","4h"]`

**Zweck:**
- Eindeutige Referenz, gegen welche Serien RS berechnet wurde (für Replays/Debug).

---

## 4) Migrationsstrategie (empfohlen)

### 4.1 Rückwärtskompatibilität
- Behalte den bestehenden Coin-Payload (`coins[SYMBOL].identity`, `coins[SYMBOL].mexc`) unverändert.
- Ergänze ausschließlich neue Meta-Felder.
- Bump `export_version` von `1.0` → `1.1`.

So brechen keine Downstream-Consumer, die nur `coins[...]` lesen.

### 4.2 Validierung/Tests (kurz)
Nach der Umstellung:
1) **Two-run-stability**: Zwei Runs kurz nacheinander am selben Tag → `asof_ts_ms` kann abweichen, aber die last-closed-Candle-Logik muss deterministisch bleiben (Thema 2/8). fileciteturn12file4 fileciteturn12file0  
2) **Join-Check**: `asof_ts_ms` in `runtime_market_meta` und `YYYY-MM-DD.json` identisch. fileciteturn12file19  
3) **Schema-Check**: Pflichtfelder vorhanden, keine leeren `cmc_id`/`slug` bei Coins.

---

## 5) Konkrete ToDo-Liste, wenn du „Themen 4–8 fertig“ meldest

1) `runtime_market_meta` Meta-Block erweitern:
   - `asof_ts_ms` (+ optional `asof_iso`)
   - `export_version`, `config_version`, `spec_version`, `run_mode`
   - `artifacts` Inventory (inkl. Dateinamen; optional Hashes)

2) Exporter-Implementation:
   - `asof_ts_ms` aus derselben Quelle nehmen, die auch `YYYY-MM-DD.json` nutzt (Pipeline-Run-Context). fileciteturn12file4

3) Docs/DoD:
   - `docs/spec.md`/`docs/features.md` sollen die Konventionen definieren (Thema 8) und du spiegelst die Version/Run-Mode im Export. fileciteturn12file0

4) Regression:
   - Golden Sample aktualisieren und `export_version` bumpen.

---

## 6) Ergebnis
Nach diesen Anpassungen ist dein Meta-Export:
- eindeutig joinbar (As-Of Timestamp),
- versioniert (Feature-Semantik nachvollziehbar),
- replay-/debug-freundlich (Artifacts Inventory, optional Hashes),
- kompatibel mit QuoteVolume-/Baseline-Konventionen und Dokumentations-Standards (Thema 6–8). fileciteturn12file1
