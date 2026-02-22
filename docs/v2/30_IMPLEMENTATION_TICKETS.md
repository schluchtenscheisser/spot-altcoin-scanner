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

## Epic 9 — Breakout Trend (1–5 Tage) (Immediate + Retest) + BTC Regime + Reporting

Ziel: Neues Setup “Breakout Trend 1–5D” inkl. Volatility-Regime (ATR Rank Gate + BB Width Score), Anti-Chase, Overextension-Penalty, BTC-Regime (Risk-Off nur RS-Override) sowie neue Reports (Setup-Listen + Global Top20).

**Wichtig:** Tickets liegen unter `docs/v2/tickets/` und werden nach Merge nach `docs/legacy/v2/tickets/` verschoben (siehe Ticket-Ende, Pflicht-Schritt).

### PR0 — Docs-only: v2 Spec + Fixtures + Ticket-Queue
**Ticket:** `docs/v2/tickets/PR0_breakout_trend_1_5d_docs.md`
- Update:
  - `docs/v2/20_FEATURE_SPEC.md` (neuer Abschnitt “Breakout Trend 1–5D”)
  - `docs/v2/40_TEST_FIXTURES_VALIDATION.md` (Fixtures inkl. MORPHO 2026-02-21 + Negativfälle + Unit-Tabellen)
  - `docs/v2/30_IMPLEMENTATION_TICKETS.md` (dieser Epic-Block)
- Erzeuge Ticket-Queue (PR1–PR5) in `docs/v2/tickets/`
- **Keine** Code-Änderungen.

### PR1 — Feature Engine: Volume SMA Perioden + ATR Rank + BB Width(+Rank)
**Ticket:** `docs/v2/tickets/PR1_breakout_trend_1_5d_feature_engine.md`
- `features.volume_sma_periods.{1d,4h} = 20`
- `1d.atr_pct_rank_120`
- `4h.bb_width_pct`, `4h.bb_width_rank_120`
- Neue deterministische Unit-Tests (percent_rank, BB width, config parsing).

### PR2 — BTC Regime: Berechnung + prominente Ausgabe (Markdown/Excel/JSON)
**Ticket:** `docs/v2/tickets/PR2_breakout_trend_1_5d_btc_regime.md`
- BTCUSDT (MEXC) Regime:
  - Risk-On: `close_1d > ema50_1d` AND `ema20_1d > ema50_1d`
  - Risk-Off: sonst
  - Multipliers: Risk-On 1.0, Risk-Off 0.85 (Anwendung in PR3)
- Ausgabe:
  - Markdown: BTC Block ganz oben (vor Rankings)
  - Excel Summary: BTC Block in A1..B6
  - JSON: top-level `btc_regime`

### PR3 — Scoring: Breakout Trend 1–5D (Immediate + Retest) + Global Top20 Dedup
**Ticket:** `docs/v2/tickets/PR3_breakout_trend_1_5d_scoring.md`
- Neue Setup IDs:
  - `breakout_immediate_1_5d`
  - `breakout_retest_1_5d`
- Trigger:
  - 4H Close > 1D high_20d (exclude current 1D candle), freshness 6×4H
- Retest:
  - window 12×4H, zone ±1.0%, invalidation: any 4H close < level
- Gates:
  - Trend 1D, ATR rank gate, momentum gate (r7>0), overextension hard gate (<28)
- BTC Risk-Off Override:
  - liquidity >= 15M
  - RS override: (alt_r7-btc_r7)>=7.5 OR (alt_r3-btc_r3)>=3.5
  - btc_multiplier = 0.85
- Weights & Multipliers: exakt wie in `20_FEATURE_SPEC.md`
- Global Top20 dedup by symbol, tie -> Retest.

### PR4 — Backtest Runner: 4H Entry/Exit + Partial + Trail + Time Stop (7 Tage)
**Ticket:** `docs/v2/tickets/PR4_breakout_trend_1_5d_backtest.md`
- Immediate Entry: open(next 4H) nach Trigger-close
- Retest Entry: limit @ level, fill im retest-valid candle
- Stop: entry - 1.2*ATR_abs_4H
- Partial: 40% @ 1.5R
- Trailing erst nach Partial: exit signal close<EMA20(4H), fill open(next 4H)
- Time stop: 168h, fill open(next 4H)
- Intra-candle priority: STOP > PARTIAL > TRAIL
- Deterministische Backtest-Unit-Tests.

### PR5 — Reporting/Excel/Schema: Setup-Listen + Global Top20 + Schema bump
**Ticket:** `docs/v2/tickets/PR5_breakout_trend_1_5d_reporting_excel_schema.md`
- Reports:
  - Top 20 Immediate (1–5D)
  - Top 20 Retest (1–5D)
  - Global Top20 (dedup)
- BTC Block prominent vor Rankings (Markdown + Excel Summary)
- Schema bump + `docs/SCHEMA_CHANGES.md` update
- Tests: BTC block ordering + Excel A1 Header.

---

## Reihenfolge für Epic 9 empfohlen:
PR0 (Docs) → PR1 (Features) → PR2 (BTC Regime) → PR3 (Scoring) → PR4 (Backtest) → PR5 (Reporting/Schema)
