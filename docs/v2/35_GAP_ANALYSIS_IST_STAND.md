# Gap-Analyse (Ist-Stand) gegen Canonical v2

**Status:** Arbeitsdokument (aus Repo-Scan abgeleitet)  
**Datum:** 2026-02-19

## Ziel
Diese Analyse vergleicht den aktuellen Code-Stand mit den verbindlichen v2-Tickets aus `docs/v2/30_IMPLEMENTATION_TICKETS.md` und dient als Startpunkt für die Umsetzung in Ticket-PRs.

## Executive Summary
- **Grundlagen vorhanden:** Basis-Pipeline (Universe → Filter → Shortlist → OHLCV → Features → Setup-Scoring → Reports) läuft.
- **Teilweise vorhanden:** EMA/ATR-Referenztests und CMC-Key-Validierung für `run_mode=standard`.
- **Hauptlücken:** Global Ranking (Top-20), Liquidity-Stage (Orderbook Top-K + Slippage/Grade), percent_rank-Population, setup-spezifisches Mindesthistorie-Gate, Risk Flags, Discovery-Tag, Trade-Levels (v2-deterministisch), E2-K-Backtest.

## Methodik (kurz)
- Code- und Test-Scan per `rg`/`sed` in `scanner/`, `tests/`, `config/`.
- Abgleich gegen Ticket-Epics T1–T8.

---

## Ticket-Gap-Matrix

### Epic 1 – Global Ranking (Top-20)
- **T1.1 Global Ranking berechnen:** **Nicht umgesetzt**
  - Keine Aggregation über mehrere Setups pro Coin (`global_score`, `best_setup_type`, `confluence`) im Pipeline-Code.
- **T1.2 Excel Sheet „Global Top 20“:** **Nicht umgesetzt**
  - Excel enthält aktuell Summary + 3 Setup-Sheets, aber kein Global-Tab.
- **T1.3 JSON/Markdown `global_top20`:** **Nicht umgesetzt**
  - Markdown/JSON werden setup-separat erzeugt, kein globales Top-20-Feld.

### Epic 2 – Liquidity-Stage (Proxy → Orderbook Top-K → Re-Rank)
- **T2.1 Proxy-Liquidity Score:** **Nicht umgesetzt (v2-Definition)**
  - Es existiert volumenbasierte Shortlist-Logik, aber kein expliziter `proxy_liquidity_score` als percent_rank.
- **T2.2 Orderbook nur Top-K:** **Nicht umgesetzt**
  - Keine `liquidity.orderbook_top_k`-Konfiguration, keine Top-K Orderbook-Stufe.
- **T2.3 Slippage-Berechnung + Liquidity Grade:** **Nicht umgesetzt**
  - Keine berechneten Felder `slippage_bps/spread_bps/liquidity_grade`.
- **T2.4 Re-Rank Regel:** **Nicht umgesetzt**
  - Sortierung nach v2-Keys (score desc, slippage asc, proxy desc) nicht implementiert.

### Epic 3 – Percent-Rank Population & Mindesthistorie
- **T3.1 `percent_rank` Population = Hard-Gate-Universe:** **Nicht umgesetzt**
  - Kein `percent_rank`-Mechanismus in Feature-/Scoring-Pipeline gefunden.
- **T3.2 Mindesthistorie-Gate je Setup:** **Nicht umgesetzt (nur globales 1D-Gate vorhanden)**
  - Aktuell nur globales `min_history_days_1d` im OHLCV-Fetch/Filter, jedoch nicht setup-spezifisch (Breakout/Pullback/Reversal, 1D+4H) mit `reason_invalid="insufficient history"`.

### Epic 4 – Risk Flags (ohne Tokenomist)
- **T4.1 denylist/unlock_overrides:** **Nicht umgesetzt**
  - Keine Verarbeitung von `config/denylist.yaml` / `config/unlock_overrides.yaml` oder Hard/Soft-Exclude-Flags im Core-Flow.

### Epic 5 – Trade Levels (Output-only)
- **T5.1 deterministische Levels:** **Nicht umgesetzt**
  - Keine v2-konforme Berechnung/Serialisierung von `analysis.trade_levels` (inkl. `breakout_level_20`) in den Setup-Ergebnissen.

### Epic 6 – Discovery Tag
- **T6.1 Discovery Proxy:** **Nicht umgesetzt**
  - Kein Tagging via `date_added` / `first_seen_ts` mit Valid-Setup-Bindung erkennbar.

### Epic 7 – Backtest (E2-K)
- **T7.1 Backtest-Runner erweitern:** **Nicht umgesetzt**
  - `backtest_runner.py` ist aktuell nur ein Docstring/Stub ohne E2-K-Logik (`T_hold=10`, `T_trigger_max=5`, `hit_10`, `hit_20`).

### Epic 8 – Tests & Consistency
- **T8.1 Indicator Tests (EMA/ATR):** **Teilweise umgesetzt**
  - Referenztests für EMA/ATR vorhanden.
- **T8.2 Top-K Budget Test:** **Nicht umgesetzt**
- **T8.3 Global Ranking Determinismus:** **Nicht umgesetzt**
- **T8.4 Backtest Golden Fixtures:** **Nicht umgesetzt**
- **Historie-Gate-Fixtures:** **Nicht umgesetzt**

---

## Positiv: bereits vorhandene v2-nahe Bausteine
1. **Pipeline-Grundgerüst** ist stabil und modular aufgebaut (guter Anker für ticketweises Refactoring).
2. **Config-Validierung** erzwingt bereits CMC-Key in `run_mode=standard`.
3. **Indikator-Basis (EMA/ATR)** plus Referenztests existieren und können für Drift-Guard weiterverwendet werden.

## Kritische Abweichungen mit hoher Priorität
1. **Fehlendes Global Ranking** (Produkt-Output unvollständig).
2. **Keine Liquidity-Stage mit Orderbook Top-K** (Rate-Limit-/Tradeability-Anforderung nicht erfüllt).
3. **Kein setup-spezifisches Mindesthistorie-Gate + percent_rank-Universe** (Ranking-Logik weicht von v2-Kernprinzipien ab).

---

## Empfohlene Umsetzung ab jetzt (in Ticket-Reihenfolge)
1. **T3.2 zuerst vorbereiten (Tests first):**
   - Unit + Golden Fixtures für `insufficient history` je Setup (1D/4H).
   - Danach Setup-Gates implementieren (`is_valid_setup`, `reason_invalid`).
2. **T1.1/T1.2/T1.3 umsetzen:**
   - Global Aggregator (`global_score`, `best_setup_type`, `confluence`) + Output in Markdown/JSON/Excel.
3. **T2.1–T2.4 umsetzen:**
   - Proxy-Score, Orderbook Top-K, Slippage/Grade, deterministischer Re-Rank.
4. **Dann T4/T5/T6**, anschließend **T7** und abschließend **T8-Härtung**.

## Offene Entscheidungen für die nächste Runde
- Exakte Datenstruktur für `global_top20` im JSON-Schema.
- Standort und API der künftigen Liquidity-Stage (eigene Pipeline-Komponente vs. Integration in Shortlist/Scoring).
- Einheitliches Modell für `is_valid_setup` + `reason_invalid` (pro SetupResult, inkl. Watchlist-Export).
