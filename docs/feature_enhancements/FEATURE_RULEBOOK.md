# FEATURE_RULEBOOK.md — Verbindliche Feature-Definitionen (für ChatGPT Codex)

Dieses Dokument stellt **präzise, fachliche Regeln** für die Berechnung der Features im Repository
`schluchtenscheisser/spot-altcoin-scanner` bereit.

**Oberstes Gebot:** *Inhaltlich korrekte Feature-Werte* (nicht nur “lauffähig”).  
**Zielgruppe:** ChatGPT Codex (arbeitet direkt im Repo, erstellt Commits/PRs).

> **Quellen-Priorität (bei Widerspruch):**
> 1) `improvements_existing_data.md` (wo explizit erweitert/ändert)  
> 2) `docs/features.md`, `docs/spec.md`, `docs/context.md`  
> 3) Code-Realität gemäß `docs/code_map.md` (Namen/Architektur/Call-Graph)

---

## 0) Verbindliche Default-Entscheidungen (fix)
Die folgenden Entscheidungen sind **final** und sollen von Codex verwendet werden (kein Raten).

### D1 — Closed Candle Definition (Snapshot-Time Vergleich)
- **Entschieden:** `closeTime <= asof_ts_ms` gilt als „geschlossen“

### D2 — Percentile Rank Definition
- **Entschieden:** percent_rank in `[0..100]` = Anteil der Werte `<= x` im Lookback (inkl. x), Tie-Handling via `<=`

### D3 — z-score Standardabweichung (ddof)
- **Entschieden:** `ddof=0` (Population-Std)

### D4 — Robuste Baseline für Volume (Baseline-Funktion)
- **Entschieden:** `trimmed_mean(window, trim=0.10)` (beide Seiten)  
  Fallback: median → mean

### D5 — Trigger-Zone “near_breakout” (x/y)
- **Entschieden (aggressiver, mehr Signale):**
  - **1d:** `near_breakout = breakout_dist in [-2.0, +1.0]`
  - **4h:** `near_breakout = breakout_dist in [-1.5, +0.7]`

### D6 — Volume-Confirmation Thresholds (vol_z / volume_spike)
- **Entschieden (OK):**
  - `volume_spike_strong = 2.5`  
  - `volume_spike_ok = 1.5`  
  - `vol_z_strong = 2.0`  
  - `vol_z_ok = 1.0`

### D7 — Drawdown-Key: Rename vs. Parallel-Keys (Schema v2)
- **Entschieden:** **Option A (breaking, sauber)** + Eintrag in `SCHEMA_CHANGES.md`  
  In `schema_version=v2` Key umbenennen:  
  `drawdown_from_ath` → `drawdown_from_window_high_close`

---

## 1) Datenmodell & Zeit-Indexierung (Global Rules)
Diese Regeln gelten für **alle** Features.

### 1.1 Candle-Felder (MEXC Kline)
Wir nutzen — sofern verfügbar — diese Felder:
- `openTime` (ms)  
- `open`, `high`, `low`, `close`  
- `volume` (Base-Volume)  
- `closeTime` (ms)  
- `quoteVolume` (Quote-Volume, bevorzugt für Liquidity/Volume-Baselines)

**Wichtig:** `quote_volume_24h` aus dem 24h-Ticker ist ein *rolling window* und darf nicht als “Tageskerze” verwechselt werden.

### 1.2 “As-Of Time” (Snapshot-Time)
Jeder Run definiert einen Timestamp:
- `asof_ts_ms = snapshotTime in ms (UTC)`

### 1.3 “T” = letzte geschlossene Kerze
Für jede Timeframe-Serie (`1d`, `4h`) gilt:
- `T = max{i | closeTime[i] <= asof_ts_ms}` (**D1**)

Alle “aktuellen” Werte in Features beziehen sich auf Index `T`, **niemals** auf die letzte gelieferte Kerze, wenn sie noch offen ist.

### 1.4 Baselines ohne “current candle”
Wenn eine Feature-Definition “Baseline ohne laufende Candle” verlangt, dann:
- Baseline-Fenster endet bei `T-1` (also **exklusive** current candle)

Beispiel (volume baseline):
- `baseline = robust_mean(volume[T-14 .. T-1])`

---

## 2) Helper-Definitionen (verbindlich)
Codex implementiert Hilfsfunktionen so, dass Ergebnisse reproduzierbar sind.

### 2.1 Safe Division
- `safe_div(a,b)` → wenn `b==0` oder `NaN` → `NaN` (oder definierter Fallback), niemals Crash.

### 2.2 Returns
- Simple return: `r_n = (close[T] / close[T-n] - 1) * 100`
- Log return: `lr_n = 100 * ln(close[T] / close[T-n])`

### 2.3 EMA(p) mit SMA-Init
- Initialisierung: `ema[p-1] = mean(close[0..p-1])`
- Danach: `ema[t] = alpha*close[t] + (1-alpha)*ema[t-1]`
- `alpha = 2/(p+1)`
- Für Indizes `< p-1`: `ema` kann `NaN` sein (oder optional “warmup”).

### 2.4 Wilder ATR(p=14)
True Range:
- `TR[t] = max(high[t]-low[t], abs(high[t]-close[t-1]), abs(low[t]-close[t-1]))`

Wilder-ATR:
- `ATR[p] = mean(TR[1..p])` (Startwert)
- `ATR[t] = (ATR[t-1]*(p-1) + TR[t]) / p` für `t>p`

ATR%:
- `atr_pct[t] = (ATR[t] / close[t]) * 100`

### 2.5 Robust Mean (trimmed_mean)
- `trimmed_mean(values, trim=0.10)`:
  1) sortiere Werte
  2) schneide `trim` unten + `trim` oben ab
  3) bilde mean über Rest
- Mindestgröße: wenn nach Trimmen < 5 Werte übrig → fallback median → mean

### 2.6 z-score / percent_rank
- `z = (x - mean(hist)) / std(hist)` mit `ddof=0` (**D3**)
- `percent_rank(x, hist)` in `[0..100]` = `100 * count(hist <= x)/len(hist)` (**D2**)

---

## 3) Default-Parameter (wenn nicht anders angegeben)
Diese Defaults dienen der Deterministik; du kannst sie später pro Feature/TF feinjustieren.

### 3.1 Kline-Limits (für Lookbacks)
- `1d_limit = 365`
- `4h_limit = 900` (≈150 Tage, API-Limit typ. 1000)

### 3.2 Z-Score / Percentile Lookbacks
- Daily (`1d`) Standard: `lookback = 120`
- 4h Standard: `lookback = 360` (≈60 Tage)

### 3.3 Perioden
- EMA: `20`, `50`
- ATR: `14`
- Volume Baseline: `14`
- Breakout Lookbacks:
  - 1d: `20`, `30`
  - 4h: `30`, `60` (Default, aus “Zeitfenster-Konsistenz”)

---

# 4) Feature-Spezifikation (verbindlich)
Alle Formeln beziehen sich auf Index `T` (= last closed candle).

## 4.1 OHLC + Candle-Structure
**Inputs:** `open, high, low, close, volume` bei `T`

- `range_pct = (high[T] - low[T]) / close[T] * 100`
- `body_pct = abs(close[T] - open[T]) / close[T] * 100`
- `upper_wick_pct = (high[T] - max(open[T], close[T])) / close[T] * 100`
- `lower_wick_pct = (min(open[T], close[T]) - low[T]) / close[T] * 100`

**Volume-Einheit:**
- Wenn `quoteVolume` vorhanden: bevorzugt `volume_quote = quoteVolume[T]`
- Sonst: `volume_quote = NaN` und ggf. `quote_volume_24h` als separater Liquidity-Input (nicht Candle-Volume).

## 4.2 Returns
Für `n ∈ {1,3,7}`:
- `r_n = (close[T]/close[T-n] - 1) * 100`
- `lr_n = 100 * ln(close[T]/close[T-n])`

Volatility-normalized:
- `mom_n_atr = r_n / atr_pct[T]` (wenn `atr_pct[T]` gültig)

Momentum persistence flags:
- `mom_persist = int(r_1>0) + int(r_3>0) + int(r_7>0)`  (0..3)

Acceleration (Default):
- `acc_1_3 = r_1 - (r_3/3)`
- `acc_3_7 = r_3 - (r_7*(3/7))`

Relative Strength (falls Benchmark-Klines verfügbar, gleiche TF & gleiche As-Of-Logik):
- `rs_n_btc = r_n(coin) - r_n(BTCUSDT)`
- `rs_n_eth = r_n(coin) - r_n(ETHUSDT)`

## 4.3 EMA, Slope, Regime, Reclaim
- `ema_20`, `ema_50` wie in 2.3
- `ema20_slope_pct = (ema20[T] / ema20[T-k] - 1) * 100`
  - Default `k`: 3 (1d), 6 (4h)  *(≈3 Tage in 4h)*

Regime:
- `bull_regime = ema20[T] > ema50[T]`
- `bear_regime = ema20[T] < ema50[T]`

Reclaim:
- `reclaim_ema20 = (close[T-1] < ema20[T-1]) and (close[T] > ema20[T])`
- `reclaim_ema50` analog

## 4.4 Distanz zu EMAs + Normalisierung
- `dist_ema20_pct = (close[T]/ema20[T] - 1) * 100`
- `dist_ema50_pct` analog

Normalisierung (Default Lookback aus 3.2, auf dist-Serie angewandt):
- `dist_ema20_z`, `dist_ema20_pct_rank`
- `dist_ema50_z`, `dist_ema50_pct_rank`

Kontext-Regel (Default):
- Distanz gilt als “bullish overextension” nur wenn:
  - `bull_regime` und `ema20_slope_pct > 0`

Overextension-Flag (Default):
- `overext_flag = (dist_ema20_pct_rank >= 95) and (vol_z >= vol_z_strong or volume_spike >= volume_spike_strong)`

## 4.5 ATR% + Regime
- `atr_pct[T]` nach Wilder (2.4)

Regime:
- `atr_z` über Lookback (3.2)
- `atr_pct_rank` über Lookback (3.2)

Volatility expansion:
- `atr_ratio = atr_pct[T] / mean(atr_pct[T-M..T-1])`
  - Default `M = 20`

## 4.6 Volume Baselines + Spikes
Baseline (ohne current candle, siehe 1.4):
- `volume_baseline_14 = trimmed_mean(volume[T-14..T-1], trim=0.10)` (**D4**)
- Wenn `quoteVolume` vorhanden: analog `quote_volume_baseline_14`

`volume_sma_14` (Semantik v2 empfohlen):
- **Semantik v2:** `volume_sma_14` = robuste Baseline (trimmed_mean)  
  *(Semantikänderung in `SCHEMA_CHANGES.md` dokumentieren.)*

`volume_spike`:
- `volume_spike = volume[T] / volume_baseline_14`

Robuste Spikes:
- `vol_hist = volume[T-lookback..T-1]` (Default: lookback 120/360)
- `vol_z = (volume[T] - mean(vol_hist)) / std(vol_hist)` (ddof=0)
- `vol_ratio = volume[T] / median(vol_hist)`

Preisbestätigung (Default):
- `volume_spike_valid = (r_1 > 0) or (close[T] > ema20[T]) or breakout_event_20`

Thresholds (**D6**):
- `volume_spike_strong = 2.5`, `volume_spike_ok = 1.5`
- `vol_z_strong = 2.0`, `vol_z_ok = 1.0`

## 4.7 Higher High / Higher Low (wick-robust)
Wick-robust variants (Default):
- `hh_close_20 = max(close[T-4..T]) > max(close[T-19..T-5])`
- `hl_close_20 = min(close[T-4..T]) > min(close[T-19..T-5])`

Strength:
- `hh_strength = (recent_max_close/prior_max_close - 1) * 100`
- `hl_strength = (recent_min_close/prior_min_close - 1) * 100`

Optional Swing/Fraktal “light” (wenn aktiviert):
- Swing High: `high[i] > high[i-1] and high[i] > high[i+1]`

Volume confirm (Default):
- `hh_valid = hh_close_20 and (vol_z >= vol_z_ok or volume_spike >= volume_spike_ok)`
- `hl_valid` analog

## 4.8 Breakout Distance + Events (ohne current candle)
Für lookback L ∈ {20,30} (1d) oder {30,60} (4h):

Resistance:
- `prior_high_L = max(high[T-L..T-1])`
- `prior_close_high_L = max(close[T-L..T-1])` (wick-robuster)

Distance:
- `breakout_dist_L = (close[T]/prior_high_L - 1) * 100`

Events:
- `breakout_event_L = close[T] > prior_high_L`
- `false_break_L = (high[T] > prior_high_L) and (close[T] < prior_high_L)`
- `near_breakout_L = breakout_dist_L in [-x, +y]` (**D5**)

Near-breakout zones (**D5**):
- **1d:** `[-2.0, +1.0]`
- **4h:** `[-1.5, +0.7]`

Volume confirmation:
- `breakout_confirmed_L = breakout_event_L and (vol_z >= vol_z_ok or volume_spike >= volume_spike_ok)`

## 4.9 Drawdown (Semantik korrekt, Schema v2)
**Schema v2 Rename (D7):**
- `drawdown_from_window_high_close`

Definition:
- `peak = max(high[0..T])` (oder window-peak, wenn Lookback gewählt)
- `drawdown_from_window_high_close = (close[T]/peak - 1) * 100` *(negativ oder 0)*

Optional multiple windows (empfohlen, additiv):
- `drawdown_20`, `drawdown_60`, `drawdown_120` je TF

## 4.10 Base Score (nur 1d, Default)
Base ist ein “Kontraktions-/Bodenbildungs”-Proxy. Ziel: **ruhiger** Preis, **keine neuen Lows**, sinkende ATR/Volume.

Komponenten (Defaults, skalierbar 0..100):
1) **No-new-lows (robust):**
   - Segmentiere die letzten 60 Tage in 3 Segmente à 20 Tage.
   - Nutze je Segment `q20_close = quantile(close, 0.20)` als “robustes Low”.
   - Score hoch, wenn das letzte Segment kein neues q20_low macht.

2) **Volatilitätskontraktion:**
   - `atr_ratio_10_30 = mean(atr_pct[T-10..T]) / mean(atr_pct[T-30..T-1])`
   - Ziel: < 1.0

3) **Volumen-Kontraktion:**
   - `vol_ratio_10_30 = mean(volume[T-10..T]) / mean(volume[T-30..T-1])`
   - Ziel: < 1.0

4) **Range-Rank:**
   - `range_pct_rank` über Lookback (3.2)
   - `range_score = 100 * (1 - range_pct_rank/100)`

**Default Aggregation (empfohlen):**
- `base_score = mean([no_new_lows_score, contraction_atr_score, contraction_vol_score, range_score])`

---

## 5) Edge Cases & Fehlende Daten (verbindlich)
- Wenn zu wenig Historie für eine Kennzahl:
  - Feature = `NaN` (oder `None`, konsistent im Repo), aber Key bleibt vorhanden.
- Wenn `quoteVolume` fehlt:
  - quote-basierte Features = `NaN` und Baselines verwenden Base-Volume.
- Kein Crash wegen Division durch 0, leere Fenster oder NaNs.

---

## 6) Validierung: Minimal-Testset (Pflicht in PRs)
Codex soll pro Thema mindestens:
- **Golden Fixture** (kleiner OHLCV-Satz) + erwartete Werte
- **Invarianten:**
  - current candle ist closed
  - baseline excludes current candle
  - Wilder-ATR nicht negativ
  - EMA-Init korrekt (SMA-start)
- **Referenz-Check** (mind. für EMA oder ATR) mit dokumentiertem Mini-Beispiel

---

## 7) Schema & Dokumentation (Pflicht)
Wenn Semantik/Keys/Output sich ändern:
- `schema_version` erhöhen
- Eintrag in `SCHEMA_CHANGES.md`
- Update in `docs/features.md` / `docs/spec.md` (wenn Definitionen betroffen)
