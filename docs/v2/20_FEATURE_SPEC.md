# Feature‑Spezifikation (v2) – Spot Altcoin Scanner

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## 0. Scope & Non‑Negotiables
Diese Spec ist deterministisch: wenn etwas nicht definiert ist, ist es **nicht erlaubt**.

Fixe Entscheidungen (Phase 1):
- Global Top‑20 zusätzlich zu Setup‑Tabs
- Potenzialdefinition: +10% bis +20% (keine Exit/TP‑Automatisierung)
- `percent_rank`‑Population = alle Midcaps nach Hard Gates mit gültiger OHLCV‑Historie
- Orderbook/Slippage: Proxy‑Pre‑Rank → Fetch nur Top‑K (Default 200) → Re‑Rank
- Tokenomist: optional, Phase 1 muss ohne funktionieren
- EMA Standard (`alpha=2/(n+1)`), ATR nach Wilder
- `run_mode=standard` erfordert CMC‑API‑Key (Option 1)

## 1. Daten & Timeframes
- **1D OHLCV**: Trend/Regime, Base/Drawdown, ATR/EMA, Momentum‑Kerngrößen
- **4H OHLCV**: Entry‑Trigger/Feinlogik
- **Orderbook**: Spread/Slippage für Tradeability (nur Top‑K)

## 2. Indikatoren (verbindlich)
### 2.1 EMA(n) Standard
- `alpha = 2/(n+1)`
- Für `t < n-1`: EMA = NaN
- Für `t = n-1`: EMA = SMA der ersten n Closes
- Danach rekursiv.

### 2.2 ATR(n) Wilder
TR:
`TR[t] = max(high[t]-low[t], abs(high[t]-close[t-1]), abs(low[t]-close[t-1]))`
Seed:
`ATR[n] = mean(TR[1..n])`
Smoothing:
`ATR[t] = (ATR[t-1]*(n-1) + TR[t]) / n`
`ATR_pct = ATR/close * 100`

## 3. Cross‑Section Normalisierung
`percent_rank` ist verpflichtend für relevante Features.
Population: **alle Midcap‑Kandidaten nach Hard Gates** mit gültigem Feature‑Wert (kein NaN).

Tie‑Handling: average rank.

## 4. Risk Flags (Phase 1)
### 4.1 Datenquellen
- `config/denylist.yaml` (Hard Exclude)
- `config/unlock_overrides.yaml` (major/minor, 14 Tage)
- MEXC Status (deposit/withdraw suspended, delisting risk)
- Tokenomist optional (Phase >1)

### 4.2 Kategorien
Hard Exclude:
- `regulatory_warning`
- `credible_scam_allegations`
- `major_unlock_within_14d`
- `deposit_withdraw_suspended`
- `delisting_risk`
- `liquidity_grade_d`

Soft (Penalty):
- `minor_unlock_within_14d`

## 5. Setups (valid/invalid)
Die exakten Gate‑Regeln pro Setup müssen in Code als `is_valid_setup` implementiert werden.
Wenn `is_valid=False` → nie in Top‑Listen, nur Watchlist.

Historie‑Gate: Jedes Setup erfordert eine minimale Anzahl abgeschlossener Kerzen, um Indikatoren und Level stabil zu berechnen. Diese Schwellenwerte sind pro Setup definiert. Erreicht ein Symbol die für das Setup erforderliche 1D‑ oder 4H‑Historie nicht, wird `is_valid_setup=False` gesetzt und der Kandidat kann nur in der Watchlist erscheinen (Grund „insufficient history“).

### 5.1 Breakout
- Kontext 1D Trend ok
- Trigger 4H Close > definierter Breakout‑Level (Range/Level)
- Volumenbestätigung (z. B. `vol_spike_rank >= thr`)
- Anti‑Chase schützt vor Overextension

#### Mindesthistorie
Für dieses Setup muss eine ausreichend lange Datenbasis vorliegen:
- **1D‑Historie:** mindestens 30 abgeschlossene 1D‑Kerzen (20‑Tage‑Hoch plus Puffer).  
- **4H‑Historie:** mindestens 50 abgeschlossene 4H‑Kerzen, damit EMA‑Trigger und Volumenanstiege zuverlässig berechnet werden können.  
Coins mit kürzerer Historie werden als `is_valid_setup=False` markiert.

### 5.2 Pullback
- 1D Trend ok
- Retrace in Zone (EMA20/EMA50 4H) ohne Breakdown
- Re‑Acceleration bestätigt

#### Mindesthistorie
- **1D‑Historie:** mindestens 60 abgeschlossene 1D‑Kerzen (EMA20/EMA50 plus Puffer).  
- **4H‑Historie:** mindestens 80 abgeschlossene 4H‑Kerzen.  
Ist die Historie kürzer, wird das Setup als invalid bewertet.

### 5.3 Reversal
- hoher Drawdown + Base/Compression
- Reclaim (EMA/Level) bestätigt
- kein Blow‑Off

#### Mindesthistorie
- **1D‑Historie:** mindestens 120 abgeschlossene 1D‑Kerzen, damit Drawdown, Basen und ATR stabil berechnet werden können.  
- **4H‑Historie:** mindestens 80 abgeschlossene 4H‑Kerzen.  
Unterschreitet ein Coin diese Schwelle, wird er für dieses Setup ausgeschlossen.

## 6. Liquidity/Slippage (Phase 1)
### 6.1 Proxy‑Pre‑Ranking
Proxy: `quote_volume_24h` (MEXC).  
`proxy_liquidity_score` = monotone Funktion (z. B. log‑scaled percent_rank).

### 6.2 Orderbook Slippage (Top‑K)
- Nur Top‑K nach Proxy‑Pre‑Ranking (Default K=200)
- Notional: default **20_000 USDT** (configurable)
- Output:
  - `spread_bps` (oder `spread_pct`)
  - `slippage_bps` (BUY vs Mid) und optional `slippage_pct`
  - `liquidity_grade` A/B/C/D (D = Hard Exclude)
  - Flag `liquidity_insufficient` wenn Tiefe nicht reicht

### 6.3 Re‑Ranking Regel (deterministisch, Phase 1)
Wir verändern die Score‑Skala (0–100) **nicht**. Sortierung erfolgt:
1) `global_score`/`setup_score` **absteigend**
2) `slippage_bps` **aufsteigend** (fehlend = +∞)
3) `proxy_liquidity_score` **absteigend**

## 7. Global Ranking (Top‑20)
Setup‑Gewichte (Default, konfigurierbar):
- Breakout 1.0, Pullback 0.9, Reversal 0.8

Je Symbol:
- `global_score = max(setup_score * setup_weight)`
- `best_setup_type` = argmax
- `confluence` = Anzahl gültiger Setups

Ein Coin erscheint im Global Top‑20 max. einmal.

## 8. Discovery‑Tag (Phase 1)
Discovery ist Tag/Bonus, nur wenn valides Setup vorliegt.

Deterministische Regel:
- Wenn CMC `date_added` verfügbar → `age_days = asof - date_added`
- sonst fallback: `first_seen_ts` = älteste 1D‑OHLCV Candle im Cache/Fetch
- `discovery = (age_days <= discovery_max_age_days)` (Default 180)

## 9. Trade Levels (Output‑only)
Trade‑Levels sind **Info‑Output**, nicht Teil des Scores.

Deterministische Level‑Definitionen (Phase 1):
- Breakout: `entry_trigger = breakout_level_20 = max(high[-21:-1])` (20D prior high), `invalidation = min(entry_trigger, ema20_1d)`, Targets = entry_trigger + k*ATR (k=1,2,3)
- Pullback: `entry_zone` um EMA20_4H (pb_tol config), `invalidation = ema50_4H` (deterministisch), Targets = EMA20 + k*ATR
- Reversal: `entry_trigger = ema20_1d`, `invalidation = base_low`, Targets = entry_trigger + k*ATR

## 10. Evaluation/Backtest (Analytics‑only, E2‑K)
Backtest dient der **Kalibrierung**, nicht dem Live‑Ranking.

Parameter:
- `T_hold = 10`
- thresholds: +10%, +20%
- `T_trigger_max = 5`

Canonical Trigger/Entry (E2‑K):
- Trigger wird über **1D Close** gesucht innerhalb `[t0 .. t0+T_trigger_max]` (Setup‑spezifische Trigger‑Condition).
- `entry_price = close[trigger_day]`
- Hits: `hit_10`, `hit_20` wenn `max(high[trigger_day+1 .. trigger_day+T_hold])` Schwellen erreicht.
- Optional: `mfe_pct`, `mae_pct`.

## 11. Konfiguration
Alle Parameter/Gewichte/Thresholds in **`config/config.yml`**.
Separate Config‑Files nur für manuelle Listen (denylist/unlock_overrides).

### Mindesthistorie pro Setup (Defaultwerte, konfigurierbar)
min_history_breakout_1d: 30
min_history_breakout_4h: 50
min_history_pullback_1d: 60
min_history_pullback_4h: 80
min_history_reversal_1d: 120
min_history_reversal_4h: 80
Diese Parameter müssen im Code aus config/config.yml gelesen und bei jeder Setup‑Prüfung angewendet werden.