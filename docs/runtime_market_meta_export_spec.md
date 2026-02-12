# Runtime Market Meta Export (MEXC + CMC Identity) — Spezifikation

## Ziel
Dieses Export-JSON liefert pro Daily-Run eine **vollständige, maschinenlesbare Markt-/Identitäts-Metadatenbasis** für alle Coins, die nach Vorfilterung (Market Cap + Plattform MEXC) vom Tool **analysiert** wurden.

Das Export-JSON ergänzt bestehende Artefakte:
- `YYYY-MM-DD.json` (Scanner-Ergebnis: Features/Scores/Reasons)
- `ohlcv_snapshot.csv.gz` (Kerzendaten, Level-/Pattern-Analyse)

**Hauptnutzen:**
1) **Eindeutige Coin-Identifikation** (Ticker-Kollisionen vermeiden) für News/Unlock/Onchain-Recherche.
2) **Tradebarkeit & Execution auf MEXC** (Tick/Step/MinNotional/Precision/Status) für realistische Entry/Stop/TP-Zonen und Orderplanung mit 5k–15k USDT.
3) **Reproduzierbarkeit** (Snapshot-Zeitpunkt, Datenquellen, Run-Info).

---

## Ablageort & Naming
- Zielpfad: `snapshots/runtime/runtime_market_meta_YYYY-MM-DD.json`
- Datum bezieht sich auf den Run-Tag (UTC).
- Datei wird **bei jedem Daily-Run** automatisch erzeugt.

---

## Datenumfang
Enthält **alle Coins**, die nach Vorfilter (Market Cap) und MEXC-Verfügbarkeit in die Analyse-Pipeline gelangt sind (also das „analysierte Universe“, nicht nur eine Top-N Shortlist).

---

## JSON-Struktur (Schema)

### Top-Level
```json
{
  "meta": { ... },
  "universe": {
    "count": 0,
    "symbols": ["ABCUSDT", "..."]
  },
  "coins": {
    "ABCUSDT": { ... },
    "XYZUSDT": { ... }
  }
}
```

---

## 1) `meta` — Run- & Snapshot-Metadaten

### Felder
- `run_id` (string): eindeutige Run-ID (z.B. Timestamp oder UUID)
- `asof_utc` (string, ISO 8601): Snapshot-Zeitpunkt des Runs in UTC (z.B. `2026-02-11T08:10:00Z`)
- `generated_at_utc` (string, ISO 8601): Zeitpunkt der Dateierzeugung
- `mexc`:
  - `api_base` (string, optional): genutzter API-Endpunkt/Host
  - `exchange_info_ts_utc` (string): Zeitpunkt des Exchange-Info Snapshots
  - `tickers_24h_ts_utc` (string): Zeitpunkt des 24h-Tickers Snapshots
- `cmc`:
  - `listings_ts_utc` (string): Zeitpunkt des CMC-Listings/Marketcap Snapshots
  - `source` (string): z.B. `CoinMarketCap`
- `config` (object, optional aber empfohlen):
  - `mcap_min_usd` (number)
  - `mcap_max_usd` (number)
  - `min_quote_volume_24h_usdt` (number, falls als Filter genutzt)
  - weitere relevante Thresholds (damit später nachvollziehbar ist, warum Coins im Universe sind)

### Zweck
- **Reproduzierbarkeit**: klarer Bezug, welcher Markt-/Regelstand zum Run verwendet wurde.
- **Abgleich**: späterer Vergleich mit Live-Daten (Abweichungen sichtbar).

---

## 2) `universe` — Index über alle analysierten Coins
### Felder
- `count` (int)
- `symbols` (array[string]): Liste aller MEXC-Handelspaare, primär `*USDT` (z.B. `TRBUSDT`)

### Zweck
- Schneller Überblick und Validierung, dass der Export das vollständige analysierte Universe enthält.

---

## 3) `coins` — Pro Coin: Identität + MEXC-Regeln + 24h-Marktstatus

Jeder Key in `coins` ist das **MEXC-Symbol**, z.B. `ABCUSDT`.

### 3.1 `identity` — Eindeutige Coin-Identität (CMC)
**Erforderliche Felder:**
- `cmc_id` (int)
- `name` (string)
- `symbol` (string) — Coin-Symbol (z.B. `ABC`)
- `slug` (string) — CMC-Slug (z.B. `abc-token`)
- `category` (string, optional): coin/token
- `tags` (array[string], optional): zur Einordnung/Narrative-Suche

**Chain/Contract (sehr empfohlen):**
- `platform` (object | null):
  - `name` (string) — z.B. `Ethereum`, `BNB Smart Chain`
  - `symbol` (string) — z.B. `ETH`, `BNB`
  - `token_address` (string) — Contract-Adresse, falls Token
- `is_token` (bool) — true wenn Contract vorhanden

**Supply/Valuation (empfohlen):**
- `market_cap_usd` (number)
- `circulating_supply` (number | null)
- `total_supply` (number | null)
- `max_supply` (number | null)
- `fdv_usd` (number | null) — FDV (Fully Diluted Valuation)
- `fdv_to_mcap` (number | null) — Verhältnis FDV/Market Cap (als Risikoindikator)
- `rank` (int | null)

**Zweck**
- **Disambiguierung**: Verhindert Ticker-Verwechslungen bei News/Unlocks/Onchain.
- **Unlock-/Emissionsrisiko-Kontext**: FDV/MCAP (Market Cap) und Supply-Daten geben Sensitivität gegenüber Unlocks.

---

### 3.2 `mexc` — Handelsregeln & Mikrostruktur
#### 3.2.1 `symbol_info` (aus Exchange Info)
**Erforderliche Felder (sofern von MEXC geliefert):**
- `mexc_symbol` (string) — z.B. `ABCUSDT`
- `base_asset` (string) — `ABC`
- `quote_asset` (string) — `USDT`
- `status` (string) — z.B. `ENABLED`/`TRADING`/`HALTED` (abhängig von API)
- `price_precision` (int | null)
- `quantity_precision` (int | null)

**Filters/Constraints (kritisch für Execution):**
- `tick_size` (number | string | null) — kleinstmöglicher Preisschritt
- `step_size` (number | string | null) — kleinstmöglicher Mengenschritt
- `min_qty` (number | null)
- `max_qty` (number | null)
- `min_notional` (number | null) — Minimum Order Value in Quote (USDT)
- `max_notional` (number | null)

> Hinweis: Falls MEXC andere Feldnamen nutzt, mappe sie intern, aber exportiere **stabile, einheitliche** Namen wie oben.

#### 3.2.2 `ticker_24h` (aus 24h Ticker Snapshot)
**Erforderliche Felder:**
- `last_price` (number)
- `high_24h` (number)
- `low_24h` (number)
- `quote_volume_24h` (number) — in USDT
- `price_change_pct_24h` (number | null)

**Sehr empfohlen (für Spread/Execution):**
- `bid_price` (number | null)
- `ask_price` (number | null)
- `spread_pct` (number | null) — berechnet: (ask-bid)/mid * 100
- `mid_price` (number | null)

**Optional (wenn verfügbar):**
- `trades_24h` (int | null)
- `base_volume_24h` (number | null)

**Zweck**
- **Tradebarkeit**: Spread, Volumen, Status, Mindestgrößen.
- **Orderplanung für 5k–15k USDT**: Tick/Step/MinNotional + Spread sind notwendig, um Entry/Stop/TP realistisch zu setzen.

---

### 3.3 `quality` — Datenqualität & Coverage (optional, empfohlen)
- `has_scanner_features` (bool) — ob der Coin im `YYYY-MM-DD.json` Features/Scores hat
- `has_ohlcv` (bool) — ob OHLCV vorhanden ist
- `missing_fields` (array[string]) — falls kritische Felder fehlen (z.B. `tick_size`, `min_notional`, `token_address`)
- `notes` (string | null)

**Zweck**
- Verhindert stille Lücken; ermöglicht gezielte Nachbesserung in der Pipeline.

---

## Beispiel: Coin-Objekt (gekürzt)
```json
{
  "identity": {
    "cmc_id": 12345,
    "name": "Example Token",
    "symbol": "EXM",
    "slug": "example-token",
    "tags": ["defi"],
    "platform": {
      "name": "Ethereum",
      "symbol": "ETH",
      "token_address": "0x1234..."
    },
    "is_token": true,
    "market_cap_usd": 450000000,
    "fdv_usd": 900000000,
    "fdv_to_mcap": 2.0,
    "circulating_supply": 50000000,
    "total_supply": 100000000,
    "max_supply": 100000000,
    "rank": 180
  },
  "mexc": {
    "symbol_info": {
      "mexc_symbol": "EXMUSDT",
      "base_asset": "EXM",
      "quote_asset": "USDT",
      "status": "TRADING",
      "price_precision": 6,
      "quantity_precision": 1,
      "tick_size": "0.000001",
      "step_size": "0.1",
      "min_qty": 1,
      "min_notional": 5
    },
    "ticker_24h": {
      "last_price": 0.012345,
      "high_24h": 0.0132,
      "low_24h": 0.0111,
      "quote_volume_24h": 12500000,
      "price_change_pct_24h": 6.8,
      "bid_price": 0.012344,
      "ask_price": 0.012346,
      "mid_price": 0.012345,
      "spread_pct": 0.016
    }
  },
  "quality": {
    "has_scanner_features": true,
    "has_ohlcv": true,
    "missing_fields": []
  }
}
```

---

## Implementierungsnotizen (kurz)
- Erzeuge den Export **nach** Universe-Filterung (Market Cap) und **nach** MEXC-Verfügbarkeitscheck (Symbol vorhanden/trading).
- Hole CMC-Identitätsdaten aus deinem bestehenden CMC-Listings/Marketcap-Snapshot.
- Hole MEXC `exchange_info` einmal pro Run und mappe pro Symbol in `symbol_info`.
- Hole MEXC `24h_tickers` einmal pro Run und mappe pro Symbol in `ticker_24h`.
- Berechne `spread_pct` nur, wenn bid/ask vorhanden.
- Schreibe die Datei atomar (temp file -> rename), damit keine halbfertigen Snapshots entstehen.
