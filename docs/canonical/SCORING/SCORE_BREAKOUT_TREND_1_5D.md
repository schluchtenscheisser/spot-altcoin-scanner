# SCORE_BREAKOUT_TREND_1_5D — Immediate + Retest (Canonical)

## Machine Header (YAML)
```yaml
id: SCORE_BREAKOUT_TREND_1_5D
status: canonical
setup_ids:
  - breakout_immediate_1_5d
  - breakout_retest_1_5d
timeframes:
  - 1d
  - 4h
determinism:
  closed_candle_only: true
  no_lookahead: true
universe_defaults:
  market_cap_usd: {min: 100_000_000, max: 10_000_000_000}
liquidity_gates:
  normal_quote_volume_24h_usd_min: 10_000_000
  btc_risk_off_quote_volume_24h_usd_min: 15_000_000
gates_1d:
  trend_gate: "(ema20_1d > ema50_1d) AND (close_1d > ema20_1d)"
  atr_chaos_gate: "atr_pct_rank_120_1d <= 0.80"
  momentum_gate: "r_7_1d > 0"
  overextension_hard_gate: "dist_ema20_pct_1d < 28.0"
trigger_4h:
  window_bars: 6
  breakout_level: "high_20d_1d"
retest_4h:
  tolerance_pct: 1.0
  window_bars: 12
weights_fixed:
  breakout_distance: 0.35
  volume: 0.35
  trend: 0.15
  bb_score: 0.15
multipliers:
  anti_chase: {start: 30, full: 60, min_mult: 0.75}
  overextension: {start: 12, strong: 20, hard_gate: 28}
  btc_regime:
    risk_on_definition: "(btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)"
    risk_off_multiplier: 0.85
```

## 0) Ziel
Kurzfristige Trendfolge-Setups (Hold 1–5 Tage), Breakout aus 1D-Struktur mit 4H-Bestätigung, inkl.:
- Immediate: Breakout bestätigt in der aktuellen “fresh” 4H-Window
- Retest: Breakout + Retest/Touch + Reclaim in definierter Zone

Alle Regeln sind deterministisch und verwenden ausschließlich **abgeschlossene** 1D/4H Candles.

---

## 1) Zeitindizes & Closed-Candle Realität
### 1.1 Indizes
- `t1d`: Index der **letzten abgeschlossenen** 1D Candle
- `t4h`: Index der **letzten abgeschlossenen** 4H Candle

Regel: Alle Referenzen auf “current” meinen **last closed**.

### 1.2 No Lookahead
Kein Feature, Gate oder Score darf Candles mit Index > `t1d` (1D) bzw. > `t4h` (4H) verwenden.

---

## 2) Universe & Setup-übergreifende Hard Gates

### 2.1 Market Cap Universe (CMC)
Canonical Default für diesen Setup-Typ:
- `100M <= market_cap_usd <= 10B`

### 2.2 Liquidity Gates (CMC quoteVol24h USD)
- Normal: `quote_volume_24h_usd >= 10_000_000`
- BTC Risk-Off Override: `quote_volume_24h_usd >= 15_000_000` (nur wenn BTC Risk-Off)

> Der genaue Feldname im Code kann abweichen; canonical meint Quote-Volumen in USD.

---

## 3) Setup-spezifische 1D Gates (Hard)

### 3.1 Trend Gate (1D)
Setup ist nur zulässig wenn:
- `ema20_1d > ema50_1d`
- `close_1d > ema20_1d`

### 3.2 ATR Chaos Gate (1D)
Setup ist nur zulässig wenn:
- `atr_pct_rank_120_1d <= 0.80`

**Definition `atr_pct_rank_120_1d`:**
- `atr_pct_1d[t] = atr_1d[t] / close_1d[t] * 100`
- Ranking wird als rolling percent_rank über die letzten 120 **abgeschlossenen** 1D Candles berechnet.
- Tie-Handling: average-rank (siehe `FEATURES/FEAT_PERCENT_RANK`)

### 3.3 Momentum Gate (1D)
Setup ist nur zulässig wenn:
- `r_7_1d > 0`

### 3.4 Overextension Hard Gate (1D)
Setup ist nur zulässig wenn:
- `dist_ema20_pct_1d < 28.0`

---

## 4) Breakout Level (1D Struktur)

### 4.1 Definition `high_20d_1d`
Sei `t1d` der Index der letzten abgeschlossenen 1D Candle.

Dann:
- `high_20d_1d = max(high_1d[t1d-20 .. t1d-1])`

Wichtig:
- Die aktuelle (letzte abgeschlossene) 1D Candle **t1d** ist **nicht** Teil des 20D-High-Fensters.
- Das verhindert Lookahead und “self-referential” Levels.

---

## 5) Trigger-Definition (4H lookback window)

### 5.1 Trigger Window (4H)
Sei `t4h` der Index der letzten abgeschlossenen 4H Candle.

Das Trigger-Fenster umfasst die letzten `N` abgeschlossenen 4H Candles mit
- `N = trigger_4h_lookback_bars`
- canonical default: `N = 30` (≈ 5 Tage)

Window:
- `[t4h-(N-1) .. t4h]`

### 5.2 Trigger Condition
- `triggered = any(close_4h[i] > high_20d_1d for i in [t4h-(N-1) .. t4h])`

Wenn `triggered == false`:
- Setup ist **invalid** (nicht in Top-Listen).

---

## 6) Retest Setup (Break-and-Retest)

### 6.1 Retest Zone
`retest_tolerance_pct = 1.0%` (default)

- `zone_low  = high_20d_1d * (1 - 0.01)`
- `zone_high = high_20d_1d * (1 + 0.01)`

### 6.2 Breakout-Indizes im Trigger Window
Im Trigger Window `[t4h-(N-1) .. t4h]`:
- `first_breakout_idx = first index i where close_4h[i] > high_20d_1d`
- `last_breakout_idx = last index i where close_4h[i] > high_20d_1d`

Usage:
- Immediate-Setup verwendet `last_breakout_idx` (jüngster Breakout im 5D-Fenster).
- Retest-Setup verwendet `first_breakout_idx` als Startpunkt des 12x4H-Fensters.

### 6.3 Retest Search Window
Suche in den nächsten 12 abgeschlossenen 4H Candles nach dem ersten Breakout:
- `j in [first_breakout_idx+1 .. first_breakout_idx+12]`

### 6.4 Retest Valid
Retest ist **valid**, wenn es ein `j` im Window gibt mit:
- Touch: `low_4h[j] >= zone_low AND low_4h[j] <= zone_high`
- Reclaim: `close_4h[j] >= high_20d_1d`

### 6.5 Retest Hard Invalidation
Retest ist **invalid**, wenn im Retest Window irgendeine Candle `k` gilt:
- `close_4h[k] < high_20d_1d`

---

## 7) Component Scores (0..100) & Formeln

> Alle Scores werden deterministisch berechnet und am Ende geclamped.

### 7.1 Breakout Distance Score (4H close vs 1D level)
Input:
- `dist_pct = ((close_4h_last_closed / high_20d_1d) - 1) * 100`

Piecewise-Kurve (canonical defaults):
- `floor = -5.0`
- `min_breakout = 2.0`
- `ideal_breakout = 5.0`
- `max_breakout = 20.0`

Mapping:
- Wenn `dist_pct <= floor` → `0`
- Wenn `floor < dist_pct < 0` → `30 * (dist_pct - floor) / (0 - floor)`
- Wenn `0 <= dist_pct < min_breakout` → `30 + 40 * (dist_pct / min_breakout)`
- Wenn `min_breakout <= dist_pct <= ideal_breakout` → `70 + 30 * (dist_pct - min_breakout) / (ideal_breakout - min_breakout)`
  - falls Nenner `<=0` → `100`
- Wenn `ideal_breakout < dist_pct <= max_breakout` → `100 * (1 - (dist_pct - ideal_breakout) / (max_breakout - ideal_breakout))`
  - falls Nenner `<=0` → `0`
- Sonst → `0`

### 7.2 Volume Score (combined spike)
Spikes:
- `spike_1d = volume_quote_spike_1d` (SMA exclude current closed candle)
- `spike_4h = volume_quote_spike_4h` (SMA exclude current closed candle)
- `spike_combined = 0.7*spike_1d + 0.3*spike_4h`

Mapping:
- Wenn `spike_combined < 1.5` → `0`
- Wenn `spike_combined >= 2.5` → `100`
- Sonst linear:
  - `((spike_combined - 1.5) / (2.5 - 1.5)) * 100`

### 7.3 Trend Score (Option A)
Voraussetzung: Trend Gate ist erfüllt (sonst Setup invalid).
- `trend_score = 70`
- `+15` wenn `close_4h_last_closed > ema20_4h_last_closed`
- `+15` wenn `ema20_4h_last_closed > ema50_4h_last_closed`
- cap: `trend_score = min(trend_score, 100)`

### 7.4 BB Score (Compression Bonus)
Input:
- `r = bb_width_rank_120_4h` im Percent-Scale `[0..100]`
- Defensive compatibility: wenn `r <= 1.0`, dann `rank_pct = r*100`

Mapping auf `rank_pct`:
- Wenn `rank_pct <= 20` → `100`
- Wenn `20 < rank_pct <= 60` → linear `100 -> 40`:
  - `100 - (rank_pct - 20) * (100-40) / (60-20)`
- Wenn `rank_pct > 60` → `0`

### 7.5 Base Score (fixed weights)
Fixed weights:
- breakout_distance: `0.35`
- volume: `0.35`
- trend: `0.15`
- bb_score: `0.15`

- `base_score = 0.35*breakout_distance_score + 0.35*volume_score + 0.15*trend_score + 0.15*bb_score`

---

## 8) Multipliers (applied at end)

### 8.1 Anti-Chase Multiplier (based on r_7_1d)
Parameters:
- start = 30
- full = 60
- min_mult = 0.75

Piecewise:
- Wenn `r_7_1d < 30` → `1.0`
- Wenn `30 <= r_7_1d <= 60` → linear `1.0 -> 0.75`
- Wenn `r_7_1d > 60` → `0.75`

### 8.2 Overextension Multiplier (based on dist_ema20_pct_1d)
Parameters:
- penalty_start = 12
- strong = 20
- hard_gate = 28 (bereits in Gates)

Piecewise:
- Wenn `d < 12` → `1.0`
- Wenn `12 <= d <= 20` → linear `1.0 -> 0.85`
- Wenn `20 < d < 28` → linear `0.85 -> 0.70`
- Wenn `d >= 28` → invalid (Hard Gate)

### 8.3 BTC Regime Multiplier (forced)
BTC Risk-On Definition:
- `btc_risk_on = (btc_close_1d > btc_ema50_1d) AND (btc_ema20_1d > btc_ema50_1d)`

Wenn `btc_risk_on == true`:
- `btc_multiplier = 1.0`

Wenn `btc_risk_on == false` (Risk-Off):
- `rs_override = ((alt_r7_1d - btc_r7_1d) >= 7.5) OR ((alt_r3_1d - btc_r3_1d) >= 3.5)`
- `liq_ok = quote_volume_24h_usd >= 15_000_000`
- `btc_multiplier = 0.85` wenn `rs_override AND liq_ok`, sonst `0.75`
- Kandidat bleibt immer gelistet (kein Hard-Exclude durch BTC-Regime)

---

## 9) Final Score
- `final_score = clamp(base_score * anti_chase_multiplier * overextension_multiplier * btc_multiplier, 0..100)`

---

## 10) Setup IDs & Output-Pflichtfelder

### 10.1 Setup IDs
- `breakout_immediate_1_5d`
- `breakout_retest_1_5d`

### 10.2 Pflichtfelder pro Row (JSON/MD/Excel)
Mindestens:
- `setup_id`
- `base_score`, `final_score`
- Level & Distanz: `high_20d_1d`, `dist_pct`
- Volume: `volume_quote_spike_1d`, `volume_quote_spike_4h`, `spike_combined`
- ATR: `atr_pct_rank_120_1d`
- BB: `bb_width_pct_4h`, `bb_width_rank_120_4h`
- Multipliers: `anti_chase_multiplier`, `overextension_multiplier`, `btc_multiplier`
- BTC Regime Flags: `btc_state`, `btc_rs_override`, `btc_liq_ok_risk_off`
- Gates/Flags: `triggered`, `retest_valid`, `retest_invalidated` (wo relevant)

### 10.3 Dedup (global)
Wenn ein Symbol beide Setups erfüllt:
- Retest wird bevorzugt (Tie-break).
Global Top-N dedup & Setup-Gewichte sind in `GLOBAL_RANKING_TOP20.md` zu definieren.

---

## 11) Test/Fixture Anker
Golden fixtures & deterministische Tabellen liegen in:
- `docs/canonical/VERIFICATION_FOR_AI.md`
