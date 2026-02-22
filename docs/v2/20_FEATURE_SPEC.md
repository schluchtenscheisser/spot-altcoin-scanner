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

## 5.4 Breakout Trend (1–5 Tage) — Immediate + Retest (NEU)

**Ziel:** Kurzfristige Trendfolge (Hold 1–5 Tage), Breakout aus Struktur mit Confirmation, aber mit Anti-Chase, Volatility-Regime und BTC-Regime Filter.

**Closed-Candle Reality:** Alle Berechnungen verwenden ausschließlich **abgeschlossene** 1D/4H Kerzen (keine Lookahead-Nutzung).

---

### 5.4.1 Universe & Hard Gates (Setup-übergreifend)

**Universe Filter (CMC):**
- Market Cap: **100M bis 10B USD**

**Liquidity Gates (CMC QuoteVol24h, USD):**
- Normal: `quote_volume_24h_usd >= 10_000_000`
- BTC Risk-Off Override: `quote_volume_24h_usd >= 15_000_000`

**Trend Gate (1D):**
- `ema20_1d > ema50_1d`
- `close_1d > ema20_1d`

**ATR Chaos Gate (1D):**
- `atr_pct_rank_120_1d <= 0.80`

**Momentum Gate (1D):**
- `r_7_1d > 0.0`

**Overextension Hard Gate (1D):**
- `dist_ema20_pct_1d < 28.0`

---

### 5.4.2 Neue/erweiterte Features (Phase v2)

#### A) Volume SMA Perioden pro Timeframe (Quote Volume)
Konfiguration (Default):
- `features.volume_sma_periods.1d = 20`
- `features.volume_sma_periods.4h = 20`

Berechnung (für Timeframe T in {1d,4h}):
- `quote_volume_sma_T = SMA(quote_volume_T, period, EXCLUDE current closed candle)`
- `volume_quote_spike_T = quote_volume_T_last_closed / quote_volume_sma_T`

#### B) ATR% Rank (1D)
- ATR(n) nach Wilder (n=14) wie in dieser Spec (Abschnitt 2.2).
- `atr_pct_1d[t] = atr_1d[t] / close_1d[t] * 100`
- `atr_pct_rank_120_1d = percent_rank(atr_pct_1d over last 120 closed 1D candles, current = last)`

**percent_rank Tie-Handling:** average rank bei gleichen Werten.  
Formel (deterministisch):
- `rank = (count_less + 0.5*count_equal) / N` in `[0..1]`.

#### C) Bollinger Band Width + Rank (4H)
Konfiguration (Default):
- `period = 20`, `stddev = 2.0`, Rank-Lookback 120

Berechnung für jede 4H Candle `t` (ab t>=19):
- `bb_middle[t] = SMA(close_4h[t-19..t])`
- `bb_std[t] = STD(close_4h[t-19..t], population std, ddof=0)`
- `bb_upper[t] = bb_middle[t] + 2.0 * bb_std[t]`
- `bb_lower[t] = bb_middle[t] - 2.0 * bb_std[t]`
- `bb_width_pct_4h[t] = ((bb_upper[t] - bb_lower[t]) / bb_middle[t]) * 100` (wenn bb_middle>0, sonst NaN)

Rank:
- `bb_width_rank_120_4h = percent_rank(bb_width_pct_4h over last 120 closed 4H candles, current = last)`

---

### 5.4.3 Struktur-Level (1D) und Trigger (4H)

#### Breakout Level (1D 20D High, exclude current 1D candle)
Sei `t1d` der Index der **letzten abgeschlossenen** 1D Candle.
- `high_20d_1d = max(high_1d over bars [t1d-20 ... t1d-1])`
- Wichtig: **Bar `t1d` ist ausgeschlossen** (no lookahead).

#### Fresh Trigger Window (4H)
Sei `t4h` der Index der **letzten abgeschlossenen** 4H Candle.
- Fresh Window: die letzten `6` abgeschlossenen 4H Candles: `[t4h-5 ... t4h]`
- `triggered = any(close_4h[i] > high_20d_1d for i in last 6 closed 4H candles)`
- Wenn `triggered == False` ⇒ Setup invalid (nicht in Top-Listen)

---

### 5.4.4 Retest-Setup (Break-and-Retest)

**Retest Tolerance:** `retest_tolerance_pct = 1.0`

Zone:
- `zone_low  = high_20d_1d * (1 - 0.01)`
- `zone_high = high_20d_1d * (1 + 0.01)`

**Retest Window:** `12` 4H Candles (48h) nach dem ersten Trigger
1) Bestimme `first_breakout_idx` = frühester 4H Index innerhalb der letzten 6 4H Bars, für den `close_4h > high_20d_1d`.
2) Retest Search Window: `j in [first_breakout_idx+1 ... first_breakout_idx+12]`

**Retest Valid (für eine Candle j im Window):**
- `low_4h[j] >= zone_low AND low_4h[j] <= zone_high` (Touch)
- UND `close_4h[j] >= high_20d_1d` (Reclaim)

**Retest Invalidation (Hard):**
- Wenn irgendeine Candle im Retest Window gilt:
  - `close_4h[k] < high_20d_1d` ⇒ Retest Setup invalid (nicht listen)

---

### 5.4.5 Score Komponenten (0..100) + Gewichte

#### A) Breakout Distance Score (4H close vs 1D level)
Input:
- `dist_pct = ((close_4h_last_closed / high_20d_1d) - 1) * 100`

**Exakt gleiche Kurve wie bestehender BreakoutScorer** (scanner/pipeline/scoring/breakout.py):
- Parameter (Defaults):
  - floor = -5.0
  - min_breakout = 2.0
  - ideal_breakout = 5.0
  - max_breakout = 20.0

Score Funktion (stückweise, deterministisch):
- wenn `dist <= floor`: 0
- wenn `floor < dist < 0`: `30 * (dist - floor) / (0 - floor)`
- wenn `0 <= dist < min`: `30 + 40 * (dist / min)`
- wenn `min <= dist <= ideal`: `70 + 30 * (dist - min) / (ideal - min)` (wenn denom<=0 => 100)
- wenn `ideal < dist <= max`: `100 * (1 - (dist - ideal) / (max - ideal))` (wenn denom<=0 => 0)
- sonst: 0

#### B) Volume Score (combined spike)
Spikes:
- `spike_1d = volume_quote_spike_1d` (SMA20 exclude current)
- `spike_4h = volume_quote_spike_4h` (SMA20 exclude current)
- `spike_combined = 0.7*spike_1d + 0.3*spike_4h`

Mapping:
- wenn `spike_combined < 1.5`: 0
- wenn `spike_combined >= 2.5`: 100
- sonst linear: `(spike_combined - 1.5) / (2.5 - 1.5) * 100`

#### C) Trend Score (Option A)
Voraussetzung: Trend Gate (1D) muss true sein (sonst invalid).
- `trend_score = 70`
- `+15` wenn `close_4h_last_closed > ema20_4h_last_closed`
- `+15` wenn `ema20_4h_last_closed > ema50_4h_last_closed`
- cap: 100

#### D) BB Score (Compression Bonus)
Input: `r = bb_width_rank_120_4h` in `[0..1]`
- wenn `r <= 0.20`: 100
- wenn `0.20 < r <= 0.60`: linear 100 → 40
  - `100 - (r - 0.20) * (100-40) / (0.60-0.20)`
- wenn `r > 0.60`: 0

#### Gewichte (fix)
- breakout_distance: 0.35
- volume: 0.35
- trend: 0.15
- bb_score: 0.15

`base_score = sum(weight_i * component_i)`

---

### 5.4.6 Multipliers (am Ende anwenden)

#### Anti-Chase Multiplier (r_7_1d)
Parameter:
- start = 30
- full = 60
- min_mult = 0.75

Stückweise:
- wenn `r_7_1d < 30`: 1.0
- wenn `30 <= r_7_1d <= 60`: linear 1.0 → 0.75
- wenn `r_7_1d > 60`: 0.75

#### Overextension Multiplier (dist_ema20_pct_1d)
Parameter:
- penalty_start = 12
- strong = 20
- hard_gate = 28

Stückweise:
- wenn `d < 12`: 1.0
- wenn `12 <= d <= 20`: linear 1.0 → 0.85
- wenn `20 < d < 28`: linear 0.85 → 0.70
- wenn `d >= 28`: invalid (Hard Gate)

#### BTC Regime Multiplier (zwingend)
BTC Risk-On Definition:
- `btc_risk_on = (btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)`

Wenn `btc_risk_on == True`:
- `btc_multiplier = 1.0`

Wenn `btc_risk_on == False` (Risk-Off):
- Symbol ist nur eligible, wenn zusätzlich:
  - `quote_volume_24h_usd >= 15_000_000`
  - RS Override true:
    - `(alt_r7_1d - btc_r7_1d) >= 7.5` OR `(alt_r3_1d - btc_r3_1d) >= 3.5`
- Wenn eligible: `btc_multiplier = 0.85`
- sonst: invalid

#### Final Score (0..100)
`final_score = clamp(base_score * overextension_multiplier * anti_chase_multiplier * btc_multiplier, 0..100)`

---

### 5.4.7 Setup IDs & Output Pflichtfelder

**Setup IDs:**
- `breakout_immediate_1_5d`
- `breakout_retest_1_5d`

**Pflichtfelder pro Row (in JSON/Markdown/Excel):**
- `setup_id`
- `base_score`, `final_score`
- `high_20d_1d`, `dist_pct`
- `volume_quote_spike_1d`, `volume_quote_spike_4h`, `spike_combined`
- `atr_pct_rank_120_1d`
- `bb_width_pct_4h`, `bb_width_rank_120_4h`
- `overextension_multiplier`, `anti_chase_multiplier`, `btc_multiplier`
- Komponenten-Scores: `breakout_distance_score`, `volume_score`, `trend_score`, `bb_score`
- Gates/Flags: `triggered`, `retest_valid`, `retest_invalidated` (wo relevant)

**Global Top20 Dedup:**
- Pro Symbol nur 1 Eintrag (höchstes final_score)
- Tie-break: Retest bevorzugen

---

### 5.4.8 Trade/Backtest Modell (4H, deterministisch)

**Immediate Entry (Backtest/Analytics):**
- Entry: `open(next_4h_candle after the last breakout trigger candle close)`

**Retest Entry (Backtest/Analytics):**
- Entry: Limit at `high_20d_1d`
- Fill: in retest-valid candle if `low <= entry <= high`

**Stop (beide Setups):**
- `atr_abs_4h = atr_pct_4h_last_closed / 100 * close_4h_last_closed`
- `stop = entry - 1.2 * atr_abs_4h`

**Partial:**
- `R = entry - stop`
- `partial_target = entry + 1.5 * R`
- `partial_size_pct = 40`

**Trailing (erst nach Partial aktiv):**
- Exit Signal: `close_4h < ema20_4h`
- Fill: `open(next_4h_candle)` nach dem Close-Signal

**Time Stop:**
- Max Hold: 168h (7 Tage)
- Exit: `open(next_4h_candle)` nach Ablauf der 168h

**Intra-Candle Priority (deterministisch):**
STOP > PARTIAL > TRAIL

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
- min_history_breakout_1d: 30
- min_history_breakout_4h: 50
- min_history_pullback_1d: 60
- min_history_pullback_4h: 80
- min_history_reversal_1d: 120
- min_history_reversal_4h: 80

Diese Parameter müssen im Code aus config/config.yml gelesen und bei jeder Setup‑Prüfung angewendet werden.

Implementierungsregel (Closed-Candle Realität): Für 1D soll der OHLCV-Fetch mindestens einen zusätzlichen Puffer-Bar laden (`effective_lookback_1d = configured_lookback_1d + 1`), damit trotz ggf. offener letzter Tageskerze die konfigurierten `min_history_*_1d`-Schwellen über abgeschlossene Kerzen erreichbar und deterministisch prüfbar bleiben.
