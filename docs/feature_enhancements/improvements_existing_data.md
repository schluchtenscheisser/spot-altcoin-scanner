# Verbesserungen mit bestehenden Rohdaten (MEXC + CoinMarketCap)

## Global (gilt für alle Features)
- **Nur geschlossene Kerzen verwenden**
  - `T = last_index_where(closeTime < snapshotTime)` (nicht stumpf `[-1]`)
  - Bei Snapshot `04:10 UTC`: i.d.R. `4h`-Kerze bis `04:00 UTC` geschlossen; `1d`-Kerze vom Vortag (`00:00 UTC`) geschlossen.
- **Kline-Felder erweitern (ohne neue Quelle)**: `open`, `closeTime`, ggf. `quoteVolume` aus der Kline-Response mitziehen (laut API vorhanden, aktuell nicht genutzt).
- **Rolling-24h Ticker-Daten nicht mit Candle-„Day“ verwechseln**
  - `quote_volume_24h` ist rolling (Fenster endet am Snapshot) → als eigener Input behandeln.
- **Robuste Statistik statt „pure mean/min/max“**, wo Ausreißer häufig sind (Volumen, Wicks):
  - Median/trimmed mean, z-score, percentile rank (über Lookback).
- **Lookback-Limits erhöhen (ohne neue Quelle)**, wenn du Percentiles/z-scores willst:
  - `1d` limit z.B. 365; `4h` limit z.B. 720–1000 (sofern API-Limit erlaubt).
- **Benchmark-Serien über gleiche API** (keine neue Quelle): BTCUSDT/ETHUSDT klines ziehen → Relative-Strength Features (RS) vs BTC/ETH.

---

## Feature: `close` / `high` / `low` / `volume`
- **Indexierung auf letzte geschlossene Kerze**: `close = close[T]`, etc.
- **Erweitern um Candle-Struktur (aus OHLC)**
  - `range_pct = (high[T]-low[T]) / close[T] * 100`
  - `body_pct = abs(close[T]-open[T]) / close[T] * 100`
  - `upper_wick_pct = (high[T]-max(open[T],close[T])) / close[T] * 100`
  - `lower_wick_pct = (min(open[T],close[T]) - low[T]) / close[T] * 100`
- **Volumen in Quote-Einheit bevorzugen**, wenn Kline-`quoteVolume` verfügbar; sonst `quote_volume_24h` als Liquidity-Prox y nutzen.
- **Liquidity-Filter** (aus bestehenden Daten):
  - Mindestschwelle `quote_volume_24h` (USDT) + ggf. Mindestpreis `price_usdt` (Slippage/Fees).

---

## Feature: `r_1` / `r_3` / `r_7` (Returns)
- **Nur geschlossene Kerzen**: `close[T]` vs `close[T-n]`.
- **Log-Returns ergänzen**:
  - `lr_n = 100 * ln(close[T]/close[T-n])`
- **Volatilitäts-normalisierte Returns** (mit ATR):
  - `mom1_atr = r_1 / atr_pct`, analog für `r_3`, `r_7`
- **Return-z-score / Percentile** (über Lookback, z.B. 120d / 360x4h):
  - `r_1_z = (r_1 - mean(r_1_hist)) / std(r_1_hist)`
- **Momentum-Konsistenz / Persistence**
  - z.B. Flags: `r_1>0`, `r_3>0`, `r_7>0` (oder gewichtete Summe)
- **Acceleration**
  - z.B. `acc = r_1 - (r_3/3)` oder `r_3 - (r_7*(3/7))`
- **Relative Strength vs BTC/ETH (gleiche API)**
  - `rs_7_btc = r_7(coin) - r_7(BTC)`; analog `rs_1`, `rs_3`.

---

## Feature: `ema_20` / `ema_50` (EMA = Exponential Moving Average)
- **Initialisierung verbessern**
  - Start mit `SMA(p)` der ersten `p` Werte statt `data[0]` (reduziert Start-Bias)
- **EMA-Slope ergänzen**
  - `ema20_slope_pct = (ema20[T]/ema20[T-k] - 1)*100` (k passend pro TF)
- **Trend-Stacking / Regime**
  - `ema20 > ema50` (bull regime), `ema20 < ema50` (bear regime)
- **Cross-/Reclaim-Events**
  - `reclaim_ema20 = (close[T-1] < ema20[T-1]) and (close[T] > ema20[T])`
  - analog für `ema50`
- **Overextension relativ bewerten**
  - Percentile/z-score von `dist_ema20_pct` (siehe nächstes Feature)

---

## Feature: `dist_ema20_pct` / `dist_ema50_pct`
- **Nur geschlossene Kerzen**: `dist = (close[T]/ema - 1)*100`
- **Distanz-Regime normalisieren**
  - `dist_z = (dist - mean(dist_hist)) / std(dist_hist)`
  - `dist_pct_rank` über Lookback
- **Kontext erzwingen (Trend vs Overextension)**
  - Distanz nur „bullish“, wenn `ema20 > ema50` und `ema20_slope > 0`
  - Overextension-Flag, wenn `dist_pct_rank` sehr hoch + `volume_spike` extrem (Blow-off-Risiko)

---

## Feature: `atr_pct` (ATR = Average True Range, TR = True Range)
- **Wilder-ATR statt SMA-ATR**
  - `ATR_t = (ATR_{t-1}*(p-1) + TR_t)/p` (p=14)
- **ATR-Regime (z-score / Percentile)**
  - `atr_z = (atr_pct - mean(atr_hist)) / std(atr_hist)`
- **Volatility-Expansion**
  - `atr_ratio = atr_pct[T] / mean(atr_pct_hist_last_M)` (M=20–30)
- **Timeframe-Normalisierung**
  - Score getrennt je TF; nicht Daily-ATR% direkt mit 4h-ATR% mischen ohne Normalisierung.

---

## Feature: `volume_sma_14` (SMA = Simple Moving Average)
- **Nur geschlossene Kerzen**: Baseline ohne laufende Candle.
- **Robuste Baseline**
  - `volume_med_14 = median(volume[T-13..T])`
  - oder `trimmed_mean` (z.B. obere/untere 10% abschneiden)
- **Quote-Volumen bevorzugen**
  - Wenn Kline-QuoteVolume verfügbar: SMA in Quote-Einheit
  - Sonst ergänzend `quote_volume_24h` als zweites Volumenmaß.

---

## Feature: `volume_spike`
- **Nur geschlossene Kerzen**
  - `volume_spike = volume[T] / baseline(T-1)` (Baseline ohne aktuelle Kerze)
- **Robuster Spike**
  - `vol_z = (volume[T] - mean(vol_hist)) / std(vol_hist)`
  - `vol_ratio = volume[T] / median(vol_hist)`
- **Preisbestätigung koppeln**
  - Spike nur werten, wenn `r_1 > 0` oder `close[T] > ema20[T]` oder Breakout-Event (siehe `breakout_dist_*`)
- **TF-spezifische Thresholds**
  - separate Regeln für `1d` vs `4h`.

---

## Feature: `hh_20` (Higher High)
- **Wick-robuster**
  - Alternative: `hh_close_20 = max(close[T-4..T]) > max(close[T-19..T-5])`
  - oder Body-High (mit `open`)
- **Stärke statt Bool**
  - `hh_strength = (recent_max/prior_max - 1)*100`
- **Swing/Fraktal-Filter (light)**
  - Swing High nur zählen, wenn `high[i] > high[i-1]` und `high[i] > high[i+1]`
- **Volume-Confirm**
  - `hh` nur „valid“, wenn `volume_spike`/`vol_z` > Schwelle.

---

## Feature: `hl_20` (Higher Low)
- **Wick-robuster**
  - `hl_close_20 = min(close[T-4..T]) > min(close[T-19..T-5])`
  - oder Body-Low (mit `open`)
- **Stärke statt Bool**
  - `hl_strength = (recent_min/prior_min - 1)*100`
- **Noise-Filter**
  - `hl` nur werten, wenn `atr_pct` nicht extrem hoch (Stop-hunt-Phase) oder wenn Base-Regime aktiv (`base_score` hoch).

---

## Feature: `breakout_dist_20` / `breakout_dist_30`
- **Resistance ohne aktuelle Kerze**
  - `prior_high = max(high[T-lookback .. T-1])`
  - `breakout_dist = (close[T]/prior_high - 1)*100`
- **Close-basierte Resistance (wick-robuster)**
  - `prior_close_high = max(close[T-lookback .. T-1])`
- **Event vs Distanz trennen**
  - `breakout_event = close[T] > prior_high`
  - `near_breakout = breakout_dist in [-x, +y]` (Trigger-Zone)
- **False-Breakout-Flag**
  - `false_break = (high[T] > prior_high) and (close[T] < prior_high)`
- **Volume-Confirmation**
  - Breakout nur „hoch“ bewerten, wenn `vol_z`/`volume_spike` > Schwelle.
- **Zeitfenster-Konsistenz**
  - lookback ggf. je TF separat tunen (z.B. 20/30 daily ok; 4h evtl. 30/60).

---

## Feature: `drawdown_from_ath`
- **Semantik korrigieren (ist window-high, nicht echtes ATH)**
  - Rename: `drawdown_from_window_high_close`
- **Peak auf High statt Close**
  - `peak = max(high[0..T])` (oder Lookback-window)
  - `drawdown = (close[T]/peak - 1)*100`
- **Mehrere Windows**
  - `drawdown_20`, `drawdown_60`, `drawdown_120` (je TF passend)
- **Längere Historie via gleiche API**
  - Limits erhöhen → „ATH“-Proxy näher am echten ATH.

---

## Feature: `base_score` (nur `1d`)
- **Robustere „no new lows“-Logik**
  - statt `min(low)` optional `min(close)` oder Quantil (z.B. 20%-Quantil) pro Segment
- **Volatilitätskontraktion integrieren**
  - `atr_ratio_10_30 = mean(atr_pct last10) / mean(atr_pct last30)` (soll < 1 sein)
- **Volumen-Kontraktion integrieren**
  - `vol_ratio_10_30 = mean(volume last10) / mean(volume last30)` (soll < 1 sein)
- **Range-Metrik verbessern**
  - statt Close-Range linear in Score: percentile/z-score von `range_pct` oder ATR-basierte Range
- **Score-Skalierung nicht linear**
  - `base_score = 100 * (1 - percentile(range_pct))` (innerhalb eigener Historie)
- **Optional: Base auch auf `4h`**
  - gleiche Logik, aber längere Lookbacks (z.B. 60–90 4h-Kerzen) + Zeitfenster-Normalisierung.
