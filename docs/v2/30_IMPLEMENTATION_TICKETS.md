# Implementation Tickets (v2) – Canonical

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Grundregeln
- 1 PR pro Ticket (sofern Ticket nicht ausdrücklich bündelt)
- Erst Tests/Fixtures, dann Implementierung
- Keine stillen Schema‑Änderungen: `schema_version` bump + Eintrag in `docs/SCHEMA_CHANGES.md`

## Epic 1 – Global Ranking (Top‑20) zusätzlich zu Setup‑Tabs
### T1.1 – Global Ranking berechnen
- Aggregation über alle gültigen SetupResults
- `global_score = max(setup_score * setup_weight)` (Default 1.0/0.9/0.8)
- `best_setup_type`, `confluence`, Flags aggregieren
- Stable sorting bei ties (siehe Feature‑Spec)

### T1.2 – Excel Sheet „Global Top 20“
- neues Sheet nach Summary
- Setup‑Sheets bleiben unverändert (Top‑10 je Setup)

### T1.3 – JSON/Markdown: `global_top20` integrieren

## Epic 2 – Liquidity‑Stage (Proxy → Orderbook Top‑K → Re‑Rank)
### T2.1 – Proxy‑Liquidity Score
- Proxy: `quote_volume_24h`
- `proxy_liquidity_score` als percent_rank (log optional)

### T2.2 – Orderbook nur Top‑K (Default K=200)
- config: `liquidity.orderbook_top_k`
- Orderbook/Slippage nur für Top‑K
- fehlende Slippage = None

### T2.3 – Slippage‑Berechnung (20k USDT default)
- Mid aus best bid/ask
- VWAP_ask bis Notional erfüllt
- Output `slippage_bps`, `spread_bps` (oder pct) + `liquidity_grade`
- `liquidity_grade D` = Hard Exclude

### T2.4 – Re‑Rank Regel
- Score‑Skala nicht verändern
- Sort Key gemäß Feature‑Spec (Score desc, slippage asc, proxy desc)

## Epic 3 – Percent‑Rank Population Fix
### T3.1 – `percent_rank` Population = Hard‑Gate Universe
- sicherstellen: Population != Shortlist

### T3.2 – Mindesthistorie‑Gate implementieren
- Lese die in `config/config.yml` definierten `min_history_*`‑Parameter für jedes Setup (Breakout, Pullback, Reversal).
- Prüfe vor der Feature‑Berechnung, ob pro Symbol genügend abgeschlossene 1D‑ und 4H‑Kerzen vorhanden sind, um das Setup stabil zu berechnen. 
- Falls nicht, setze `is_valid_setup=False` und `reason_invalid="insufficient history"`. Solche Setups dürfen weder im Global Top‑20 noch in den Top‑10‑Listen auftauchen.
- Ergänze Unit‑ und Golden‑Tests gemäß 40_TEST_FIXTURES_VALIDATION (siehe „Historie‑Gate“), um valide und invalide Historien abzudecken.

## Epic 4 – Risk Flags (ohne Tokenomist)
### T4.1 – denylist/unlock_overrides
- Denylist hard exclude
- major unlock within 14d hard exclude; minor unlock soft penalty

## Epic 5 – Trade Levels (Output‑only)
### T5.1 – deterministische Levels implementieren
- `breakout_level_20` Feature (20D prior high)
- Levels in `analysis.trade_levels` je SetupResult
- keine Score‑Auswirkung

## Epic 6 – Discovery Tag
### T6.1 – Discovery Proxy
- primary: CMC `date_added` falls verfügbar
- fallback: `first_seen_ts` aus ältester 1D Candle
- Tag nur wenn valides Setup

## Epic 7 – Backtest (Analytics‑only, E2‑K)
### T7.1 – Backtest‑Runner erweitern
- Canonical Trigger/Entry gemäß Feature‑Spec (E2‑K)
- `T_hold=10`, thresholds 10/20, `T_trigger_max=5`
- keine Exit‑Logik

## Epic 8 – Tests & Consistency
### T8.1 – Indicator Tests (EMA/ATR)
### T8.2 – Top‑K Budget Test (Orderbook)
### T8.3 – Global Ranking Determinismus (Confluence + Einmaligkeit)
### T8.4 – Backtest Golden Fixtures

Reihenfolge empfohlen:
T0.1 → T1.* → T2.* → T3.1 → T3.2 → T4.1 → T5.1 → T6.1 → T7.1 → T8.*
