# Produktanforderungen (v2) – Spot Altcoin Scanner

**Status:** Canonical v2 Produktanforderungen für GPT‑Codex  
**Datum:** 2026-02-18  
**Gültigkeit:** Dieses Dokument ist die **einzige** verbindliche „Produktanforderungen“-Quelle in v2 und **ersetzt** ältere/parallel benannte Varianten (z. B. `02 - Produktanforderungen (v2).md`) vollständig.

> **Auto‑Docs bleiben unverändert:** `docs/code_map.md` und `docs/GPT_SNAPSHOT.md` bleiben unter `docs/` (GitHub Actions). Sie sind **Ist‑Referenz**, nicht Requirements‑Quelle.

---

## 1. Zielbild

Der Spot Altcoin Scanner ist ein **Research‑Tool** (kein Trading‑Bot).  
Er identifiziert Altcoin‑Kandidaten, bei denen **kurzfristig** (typisch wenige Tage) eine **potenzielle** Rendite von **+10% bis +20%** plausibel ist (gelegentlich mehr) – ohne Garantie, ohne Orderausführung.

**Outputs pro Run:**
1. **Global Ranking (Top‑20)**: aggregiert über alle validen Setups (neu, zusätzlicher Tab)
2. **Setup‑Tabs (Top‑10 je Setup)**: Breakout / Pullback / Reversal (bleiben bestehen)
3. **Watchlist**: „fast valide“ Kandidaten mit Gründen/Triggern

**Wichtig:** Ein Coin erscheint im Global Ranking **maximal einmal** (`best_setup`).

---

## 2. Kernprinzipien (nicht verhandelbar)

1. **Gates vor Scores:** Universe‑Filter & Hard Gates passieren **vor** Scoring/Ranking.  
2. **Percent‑Rank Population:** `percent_rank` basiert auf **allen Midcap‑Kandidaten nach Hard Gates** mit gültiger OHLCV‑Historie, nicht nur Shortlist.  
3. **Rate‑Limit‑Schutz:** teure Calls (z. B. Orderbook/Slippage) werden **zweistufig** und nur für **Top‑K** durchgeführt.  
4. **Erklärbarkeit:** Report zeigt Score‑Komponenten, Flags und Begründungen (Reason‑Codes).  
5. **Paid Sources optional:** Bezahlte Quellen (z. B. Tokenomist) sind **optional** und dürfen die Korrektheit nicht blockieren.

---

## 3. Universum & Constraints

- **Börse:** MEXC Spot (USDT‑Paare)
- **Universe:** Midcaps (Market Cap **100M – 3B USD**)
- **Positionsgröße (Kontext):** typ. 5k–20k USDT → Tradeability‑Bewertung standardmäßig für **20k** (Slippage20k)
- **Zeithorizont:** wenige Tage
- **Risk‑Fenster:** 14 Tage (Unlocks/Delisting/Status)

### 3.1 Run‑Mode & Market‑Cap Daten (Entscheidung: Option 1)

- **`run_mode=standard`**: erfordert **CoinMarketCap (CMC) API Key** (Market‑Cap Snapshot). Ohne Key darf Standard‑Run nicht starten.
- **`run_mode=fast/offline/backtest`**: darf ohne CMC Key laufen (mit vorhandenen Snapshots/Cache), muss im Report markieren, wenn Market‑Cap‑Daten fehlen oder veraltet sind.

---

## 4. Harte Ausschlusskriterien (Hard Gates)

Ein Kandidat wird **vollständig ausgeschlossen**, wenn mindestens eines gilt:
- Liquidity Grade **D**
- `risk_flag` aus Kategorie „Hard Exclude“ (siehe Feature‑Spec)
- fehlende Mindesthistorie: Für jedes Setup sind in der Feature‑Spec konkrete Schwellenwerte (min_history_breakout_1d usw.) definiert. Erfüllt ein Coin diese Historie nicht, wird das Setup als invalid bewertet und der Coin erscheint maximal in der Watchlist mit dem Grund „insufficient history“, nicht in den Top‑Listen.
- **kein valides Setup** (Breakout/Pullback/Reversal) → Kandidat darf **nicht** in Top‑Listen erscheinen (nur Watchlist)

---

## 5. Reporting (Excel/JSON/Markdown)

### 5.1 Excel‑Workbook (Pflicht)

Tabs:
1) `Summary`  
2) `Global Top 20` (neu, aggregiert)  
3) `Reversal Setups` (Top‑10)  
4) `Breakout Setups` (Top‑10)  
5) `Pullback Setups` (Top‑10)

### 5.2 Inhalte pro Coin (Minimum)

- Symbol, Name, Price (USDT), Market Cap, 24h Quote Volume
- Setup‑Type + Setup‑Score + Global‑Score
- Score‑Komponenten (transparent)
- Liquidity: `spread_pct`, `slippage20k_pct`, `liquidity_grade`
- Risk: `risk_flags` (Liste), `manual_unlock_override` falls gesetzt
- Meta: Commit‑Hash, Config‑Hash, Schema‑Version, Run‑Mode, Universe‑Counts

### 5.3 Watchlist

„Fast valide“ Kandidaten mit:
- `reason_invalid`
- `entry_trigger`
- `invalidation_level`

---

## 6. Ranking‑Logik (High‑Level)

- Setups werden **zuerst** getrennt pro Pipeline gescored.
- Danach wird ein **globaler Score** berechnet und nach Setup priorisiert (Startgewichtung):
  - Breakout: **1.0**
  - Pullback: **0.9**
  - Reversal: **0.8**

### 6.1 Liquidity/Orderbook (Top‑K, verbindlich)

- Pre‑Ranking mit Proxy‑Liquidity (z. B. `quote_volume_24h`)
- Orderbook‑Fetch nur für **Top‑K** (Default **K=200**)  
- Re‑Rank nach Slippage‑Metrik → final **Top‑20**

**Korrektheit:** Für das Ziel „Top‑20“ ist das akzeptabel; Coins außerhalb Top‑K können nicht „hochgerankt“ werden, da Slippage unbekannt ist.

### 6.2 Kalibrierung (später, datengetrieben)

- Setup‑Gewichte und Schwellenwerte werden später datenbasiert kalibriert (Backtest‑Metriken: Hit‑Rates +10/+20 innerhalb 10 Tagen).
- Gewichtungen sind **Config‑getrieben** (kein Code‑Edit nötig).

---

## 7. Tokenomist (optional, Phase 1 nicht erforderlich)

Phase 1 muss **voll funktionsfähig** sein, wenn Tokenomist nicht genutzt wird.  
Stattdessen:
- manuelle Denylist
- manuelle Unlock‑Overrides

Tokenomist darf später nur „verfeinern“, nicht blockieren.

---

## 8. Discovery‑Tag (Phase 1, Free‑API freundlich)

Discovery ist **kein eigener Setup‑Typ**, sondern ein Tag/Bonus, wenn gleichzeitig ein valides Setup vorliegt.

Phase 1 nutzt nur vorhandene Quellen:
- `new_listing_tag`: CMC `date_added` ≤ konfigurierbarer Schwellenwert (z. B. 180 Tage)
- `anomaly_tag`: 4H/1D Volumen‑ oder Range‑Anomalie per Z‑Score/Percentile (Definition in Feature‑Spec)

---

## 9. Dokument‑Hierarchie (Codex verbindlich)

1. Feature‑Spec (v2)  
2. Implementation Tickets (v2)  
3. Produktanforderungen (dieses Dokument)  
4. Master Plan (v2)  
5. Auto‑Docs (`docs/code_map.md`, `docs/GPT_SNAPSHOT.md`) als Ist‑Referenz  
6. Legacy‑Dokus (Kontext)
