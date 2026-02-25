# Runtime Market Meta Export — MEXC + CMC Identity (Canonical)

## Machine Header (YAML)
```yaml
id: OUTPUT_RUNTIME_MARKET_META_EXPORT
status: canonical
output_kind: runtime_export_json
path_pattern: "snapshots/runtime/runtime_market_meta_YYYY-MM-DD.json"
timestamp_unit: ms
determinism:
  closed_candle_only: true
  no_lookahead: true
sources:
  - MEXC: exchange_info + tickers_24h
  - CMC: listings/marketcap + metadata(date_added)
links:
  - docs/canonical/DATA_SOURCES.md
  - docs/canonical/OUTPUT_SCHEMA.md
  - docs/canonical/MAPPING.md
```

## Ziel
Dieses Export-JSON liefert pro Daily-Run eine **vollständige, maschinenlesbare Market-/Identity-Metadatenbasis** für alle Coins, die nach Vorfilterung (Market Cap + MEXC-Verfügbarkeit) in der Analyse-Pipeline gelandet sind (also das “analysierte Universe”, nicht nur Top-N).

Hauptnutzen:
1) **Eindeutige Coin-Identifikation** (Ticker-Kollisionen vermeiden) für Research/News/Unlock/Onchain.
2) **Tradebarkeit/Execution auf MEXC** (Tick/Step/MinNotional/Precision/Status) für realistische Orderplanung.
3) **Reproduzierbarkeit** (As-Of, Datenquellen, Run-Meta).

## Ablageort & Naming
- Zielpfad: `snapshots/runtime/runtime_market_meta_YYYY-MM-DD.json`
- Datum bezieht sich auf den Run-Tag in **UTC**.

Atomic write (canonical):
- schreibe erst temp file, dann rename.

## Datenumfang
Enthält **alle Coins**, die nach:
- Market-Cap Universe Filter (CMC)
- MEXC Symbol verfügbar + tradable status
in die Analyse-Pipeline aufgenommen wurden.

## JSON Struktur (Schema)

### Top-Level
```json
{
  "meta": { "...": "..." },
  "universe": {
    "count": 0,
    "symbols": ["ABCUSDT", "..."]
  },
  "coins": {
    "ABCUSDT": { "...": "..." }
  }
}
```

---

## 1) `meta` — Run- & Snapshot-Metadaten (required)

### Felder
- `run_id` (string): eindeutige Run-ID (timestamp oder UUID)
- `asof_ts_ms` (int): As-Of epoch **ms** UTC (canonical master timestamp)
- `asof_iso_utc` (string, optional): RFC3339 UTC
- `generated_at_ts_ms` (int): Erzeugungszeitpunkt (ms)
- `mexc`:
  - `api_base` (string, optional)
  - `exchange_info_ts_ms` (int)
  - `tickers_24h_ts_ms` (int)
- `cmc`:
  - `listings_ts_ms` (int)
  - `source` (string): `"CoinMarketCap"`
- `config` (object, recommended):
  - `mcap_min_usd` (number)
  - `mcap_max_usd` (number)
  - `min_quote_volume_24h_usd` (number, if used)

### Zweck
- Reproduzierbarkeit & Vergleich mit späteren Daten.

---

## 2) `universe` — Index über alle analysierten Coins (required)
- `count` (int)
- `symbols` (array[string]): Liste aller MEXC Trading Pairs (primär `*USDT`), z.B. `TRBUSDT`.

Canonical ordering:
- `symbols` ist **lexicographically ascending** (stabil).

---

## 3) `coins` — Pro Coin: Identity + MEXC Rules + 24h Market Data (required)

Key ist immer das **MEXC trading pair** (z.B. `ABCUSDT`).

### 3.1 `identity` — eindeutige Coin-Identität (CMC) (required)
Required:
- `cmc_id` (int)
- `name` (string)
- `symbol` (string) — Coin ticker (z.B. `ABC`)
- `slug` (string)

Recommended:
- `tags` (array[string], optional)
- `category` (string, optional)
- `platform` (object|null):
  - `name` (string)
  - `symbol` (string)
  - `token_address` (string)
- `is_token` (bool)

Supply/Valuation (recommended if available):
- `market_cap_usd` (number)
- `circulating_supply` (number|null)
- `total_supply` (number|null)
- `max_supply` (number|null)
- `fdv_usd` (number|null)
- `fdv_to_mcap` (number|null)
- `rank` (int|null)

Notes:
- CMC-derived fields must follow `MAPPING.md` collision/override policy.

### 3.2 `mexc` — Handelsregeln & Microstructure (required)

#### 3.2.1 `symbol_info` (from exchange_info)
- `mexc_symbol` (string) e.g. `ABCUSDT`
- `base_asset` (string) e.g. `ABC`
- `quote_asset` (string) e.g. `USDT`
- `status` (string) e.g. `TRADING` (canonical normalized)
- `price_precision` (int|null)
- `quantity_precision` (int|null)

Constraints (critical for execution):
- `tick_size` (string|number|null)
- `step_size` (string|number|null)
- `min_qty` (number|null)
- `max_qty` (number|null)
- `min_notional` (number|null) — minimum order value in quote (USDT)
- `max_notional` (number|null)

Canonical rule:
- normalize provider field names to the stable names above.

#### 3.2.2 `ticker_24h` (from 24h ticker snapshot)
Required:
- `last_price` (number)
- `high_24h` (number)
- `low_24h` (number)
- `quote_volume_24h` (number) — in USDT
- `price_change_pct_24h` (number|null)

Recommended (if available):
- `bid_price` (number|null)
- `ask_price` (number|null)
- `mid_price` (number|null)
- `spread_pct` (number|null) — computed

Spread computation (canonical, if bid/ask available):
- `mid = 0.5*(bid + ask)`
- `spread_pct = ((ask - bid) / mid) * 100`

### 3.3 `quality` — data coverage flags (recommended)
- `has_scanner_features` (bool)
- `has_ohlcv` (bool)
- `missing_fields` (array[string])
- `notes` (string|null)

---

## Determinismusregeln
- Alle timestamps: epoch **ms** UTC.
- Stabile symbol ordering (lexicographic asc).
- Keine stillen Heuristiken: mapping collisions/unmapped werden in Reports behandelt (siehe `MAPPING.md`).
- Schreibvorgang atomar.

## Verhältnis zu anderen Outputs
- Scanner-Result (`YYYY-MM-DD.json`) enthält Features/Scores/Reasons.
- OHLCV snapshot (`ohlcv_snapshot.csv.gz`) enthält Candles.
- Dieser Export liefert **Identity + Execution constraints + 24h market status**.
