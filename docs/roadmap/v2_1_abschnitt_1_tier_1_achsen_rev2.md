# v2.1 – Abschnitt 1: Tier-1-Achsen (überarbeitet)

Ziel dieses Abschnitts ist eine **formal umsetzbare Definition** der Tier-1-Achsen:
- exakte Inputs
- Normalisierungsfunktionen
- Aggregation
- Missing-Data-Verhalten
- Default-Anker
- Kalibrierungshinweise

Diese Achsen sind bewusst:
- **deterministisch**
- **direkt aus OHLCV, EMA, ATR, Bollinger ableitbar**
- **state-unabhängig**
- **kontextfrei normiert**

Die phasenspezifische Bedeutung kommt erst in Abschnitt 3.

---

# 1. Grundregeln für Tier-1-Achsen

## 1.1 Allgemeine Skala
Jede Tier-1-Achse liefert einen Wert in:

- `0 .. 100`

Interpretation:
- `0` = sehr schwach / ungünstig
- `50` = neutral / mittig
- `100` = sehr stark / günstig

---

## 1.2 Grundsatz: kontextfreie Normierung
Tier-1-Achsen werden **ohne Marktphasen-Kontext** normiert.

Beispiel:
- `trend_strength = 50` bedeutet nur „neutral bis mittel“
- es bedeutet **nicht automatisch**, dass das für `trend_resume` gut oder schlecht ist

Kontextabhängige Relevanz entsteht ausschließlich später durch:
- Phase-Floors
- Phase-Gewichte
- State-Transitions

**Regel:**  
Achsen repräsentieren rohe Strukturzustände.  
Phasenspezifische Relevanz wird ausschließlich durch Floors, Gewichte und Transition-Regeln bestimmt.

---

## 1.3 Standard-Normalisierungsfunktion

### Funktion `norm_linear_clamped(x, low, mid, high)`
Diese Funktion bildet einen Rohwert `x` auf `0..100` ab.

Regeln:
- wenn `x <= low` → `0`
- wenn `x >= high` → `100`
- wenn `x == mid` → `50`
- zwischen `low .. mid` linear auf `0 .. 50`
- zwischen `mid .. high` linear auf `50 .. 100`

### Formel
Für `x <= mid`:
- `score = 50 * (x - low) / (mid - low)`

Für `x > mid`:
- `score = 50 + 50 * (x - mid) / (high - mid)`

Danach:
- clamp auf `0..100`

### Sonderfall
Wenn `mid == low` oder `high == mid`:
- Config invalid
- Fail-fast bei Config-Validierung

---

## 1.4 Inverse Normalisierung

Für Größen, bei denen **niedriger besser** ist, wird die inverse Variante verwendet:

### Funktion `norm_linear_clamped_inv(x, low_good, mid, high_bad)`
Bedeutung:
- `x <= low_good` → `100`
- `x >= high_bad` → `0`
- `x == mid` → `50`

Diese Funktion ist für:
- Volatilitätsränge
- BB-Width-Ränge
- Distanz-/Alterungsmaße mit „kleiner ist frischer“
geeignet.

---

## 1.5 Stückweise lineare Normalisierung

Mehrere Achsen benötigen asymmetrische Stützpunkte. Dafür gilt zusätzlich:

### Funktion `norm_piecewise_linear(x, points)`
`points` ist eine aufsteigend sortierte Liste von Tupeln:
- `[(x0, y0), (x1, y1), ..., (xn, yn)]`

Regeln:
- wenn `x <= x0` → `y0`
- wenn `x >= xn` → `yn`
- für `xi < x < x(i+1)`:
  - lineare Interpolation zwischen `(xi, yi)` und `(x(i+1), y(i+1))`

### Anforderungen
- `x0 < x1 < ... < xn`
- `yi` müssen in `0..100` liegen
- bei ungültiger Punkteliste:
  - Config invalid
  - Fail-fast

### Hinweis
Jede Achse muss explizit angeben, ob sie:
- `norm_linear_clamped`
- `norm_linear_clamped_inv`
- oder `norm_piecewise_linear`
verwendet.

---

## 1.6 Aggregation
Standard-Aggregation für Achsen ist:

### `weighted_mean(scores, weights)`
- alle Subscores müssen in `0..100` liegen
- Gewichte müssen > 0 sein
- Summe der verwendeten Gewichte wird intern auf 1.0 normiert

### Missing-Data-Regel
Wenn einzelne Subinputs fehlen:
- ihr Gewicht wird entfernt
- verbleibende Gewichte werden neu normiert
- wenn das verbleibende Gesamtgewicht unter `cfg.axes.min_effective_weight_ratio` fällt:
  - Achse wird `null`
  - zusätzlicher Flag: `axis_<name>_not_evaluable = true`

Default:
- `min_effective_weight_ratio = 0.60`

---

## 1.7 Datendefinitionen
Alle Prozentfelder sind echte Prozentwerte, also:
- `+3.5` bedeutet `+3.5 %`
- `-2.0` bedeutet `-2.0 %`

Keine Rank01-Skalen in Tier-1-Endachsen.  
Falls Rohfeatures Rank01 sind, werden sie vorher auf Prozent umgerechnet:
- `rank_pct = rank01 * 100`

---

## 1.8 Default-Anker sind Startwerte
Alle unten definierten Anker sind:
- **Default-Startwerte**
- **konfigurierbar**
- **nach ersten Real-Runs zu kalibrieren**

Kalibrierungspflicht besteht insbesondere, wenn:
- zu viele Werte >85 clustern
- zu viele Werte <15 clustern
- die Achse reale Kandidaten nicht sauber trennt

Gerade bei volatilen MEXC-Altcoins sind die Defaults nur Startpunkte, keine endgültigen Marktanker.

---

# 2. Tier-1-Achse: `trend_strength`

## 2.1 Zweck
Misst die Stärke der aktuellen Trendstruktur über 1d und 4h.

Nicht gemeint ist:
- ob der Coin „kaufenswert“ ist
- nur: wie konstruktiv seine Trendlage relativ zu EMAs und EMA-Slopes ist

---

## 2.2 Rohinputs
Erforderliche Rohinputs:

- `close_vs_ema20_1d_pct`
- `close_vs_ema50_1d_pct`
- `close_vs_ema20_4h_pct`
- `close_vs_ema50_4h_pct`
- `ema20_slope_1d_pct_per_bar`
- `ema20_slope_4h_pct_per_bar`
- `ema20_vs_ema50_1d_pct`
- `ema20_vs_ema50_4h_pct`

### Definitionen
- `close_vs_ema20_1d_pct = ((close_1d / ema20_1d) - 1) * 100`
- analog für alle anderen Distanzgrößen
- `ema20_slope_1d_pct_per_bar = ((ema20_1d[t] / ema20_1d[t-1]) - 1) * 100`
- analog für 4h

---

## 2.3 Normalisierung

### A) Preis vs EMA
Für:
- `close_vs_ema20_1d_pct`
- `close_vs_ema50_1d_pct`
- `close_vs_ema20_4h_pct`
- `close_vs_ema50_4h_pct`

Default-Anker:
- `low = -10`
- `mid = 0`
- `high = +10`

Normierung:
- `score_close_vs_ema* = norm_linear_clamped(x, -10, 0, +10)`

---

### B) EMA20-Slope
Für:
- `ema20_slope_1d_pct_per_bar`
- `ema20_slope_4h_pct_per_bar`

Default-Anker:
- `low = -1.5`
- `mid = 0`
- `high = +1.5`

Normierung:
- `score_ema20_slope_* = norm_linear_clamped(x, -1.5, 0, +1.5)`

---

### C) EMA20 vs EMA50
Für:
- `ema20_vs_ema50_1d_pct`
- `ema20_vs_ema50_4h_pct`

Default-Anker:
- `low = -8`
- `mid = 0`
- `high = +8`

Normierung:
- `score_ema20_vs_ema50_* = norm_linear_clamped(x, -8, 0, +8)`

---

## 2.4 Aggregation

Gewichte:
- `0.20` `score_close_vs_ema20_1d`
- `0.15` `score_close_vs_ema50_1d`
- `0.15` `score_close_vs_ema20_4h`
- `0.10` `score_close_vs_ema50_4h`
- `0.10` `score_ema20_slope_1d`
- `0.10` `score_ema20_slope_4h`
- `0.10` `score_ema20_vs_ema50_1d`
- `0.10` `score_ema20_vs_ema50_4h`

### Formel
`trend_strength = weighted_mean(subscores, weights)`

---

## 2.5 Missing Data
Wenn 4h-Daten fehlen:
- 4h-Komponenten entfallen
- 1d-Gewichte werden re-normalisiert
- zusätzlicher Flag:
  - `trend_strength_reduced_resolution = true`

Wenn verbleibendes Gesamtgewicht < 0.60:
- `trend_strength = null`
- `axis_trend_strength_not_evaluable = true`

---

## 2.6 Kalibrierungshinweis
Bei MEXC-Altcoins kann `close_vs_ema20` häufiger stark positiv sein.  
Wenn viele Coins dauerhaft im Bereich >85 clustern:
- obere Anker schrittweise anheben, z. B. auf `+15` oder `+20`

---

# 3. Tier-1-Achse: `reclaim_progress`

## 3.1 Zweck
Misst, wie weit ein Coin strukturell relevante Anker zurückerobert hat.

Das ist kein vollständiges Entry-Signal, sondern ein Fortschrittsmaß.

---

## 3.2 Rohinputs
Erforderliche Inputs:

- `close_vs_ema20_4h_pct`
- `close_vs_ema50_4h_pct`
- `close_vs_ema20_1d_pct`
- `close_vs_ema50_1d_pct`
- `close_vs_high20_4h_pct`
- `bars_above_ema20_4h`
- `bars_above_ema50_4h`
- `bars_above_ema20_1d`
- `bars_above_ema50_1d`
- `bars_above_high20_4h`

### Definition
- `close_vs_high20_4h_pct = ((close_4h / fixed_high20_break_anchor_4h) - 1) * 100`

### Semantik von `bars_above_*`
`bars_above_X` ist die Anzahl **konsekutiver abgeschlossener Bars** rückwärts ab dem aktuellen Bar, deren Close **oberhalb** des Ankers `X` liegt.

Beispiel:
- 2 Bars über EMA20
- dann 1 Bar darunter
- dann wieder 2 Bars darüber

→ `bars_above_ema20 = 2`  
Es zählt nur der aktuelle zusammenhängende Hold-Streak.

Wichtig:
- Referenzlevel muss deterministisch aus abgeschlossenen Bars stammen
- kein Lookahead

---

## 3.3 Subscore pro Anker

Jeder Anker erhält:
- Distanzscore
- Holdscore

### A) Distanzscore
Anker:
- 4h EMA20
- 4h EMA50
- 1d EMA20
- 1d EMA50
- 4h fixed high20 break anchor

Default-Anker Distanz:
- `low = -3`
- `mid = 0`
- `high = +3`

Formel:
- `anchor_distance_score = norm_linear_clamped(x, -3, 0, +3)`

---

### B) Holdscore
Bars über Anker werden diskret gemappt:

- `0 Bars -> 0`
- `1 Bar -> 40`
- `2 Bars -> 70`
- `>=3 Bars -> 100`

Formel:
- `holdscore = norm_piecewise_linear(x, [(0, 0), (1, 40), (2, 70), (3, 100)])`

Werte >3 werden auf 100 gecappt.

---

### C) Anchorscore
Gewichtung:
- `0.70 * distance_score`
- `0.30 * holdscore`

---

## 3.4 Aggregation über Anker

Gewichte:
- `0.25` 4h EMA20
- `0.20` 4h EMA50
- `0.20` 1d EMA20
- `0.15` 1d EMA50
- `0.20` 4h fixed high20 break anchor

### Formel
`reclaim_progress = weighted_mean(anchor_scores, weights)`

---

## 3.5 Missing Data
Wenn 4h-Daten fehlen:
- 4h EMA20
- 4h EMA50
- 4h fixed high20 break anchor
entfallen

Dann:
- Reclaim Progress wird rein auf 1d-Informationen reduziert
- Flag:
  - `reclaim_progress_reduced_resolution = true`

Wichtig:
- Coins ohne 4h-Daten können später **nicht `early_ready`** werden

---

## 3.6 Kalibrierungshinweis
Wenn die Distanz-Anker zu eng sind und viele Coins schon bei kleinen Reclaims >80 erreichen:
- High-Anker für Distanz auf `+4` oder `+5` anheben

---

# 4. Tier-1-Achse: `compression_strength`

## 4.1 Zweck
Misst die Verdichtung / Kontraktion einer Struktur vor potenzieller Expansion.

Hohe Werte bedeuten:
- enge Struktur
- reduzierte Volatilität
- potenziell gute Vorlaufphase

---

## 4.2 Rohinputs
- `bb_width_rank_120_4h_pct`
- `atr_pct_rank_120_1d_pct`
- `range_width_12bars_4h_vs_atr1d_pct`
- `std_return_rank_12bars_4h_pct`

### Definitionen
- `bb_width_rank_120_4h_pct`: Bollinger-Band-Breitenrang auf 0..100
- `atr_pct_rank_120_1d_pct`: ATR%-Rang auf 0..100
- `range_width_12bars_4h_vs_atr1d_pct = (range_width_last_12_4h / atr_1d) * 100`
- `std_return_rank_12bars_4h_pct`: Rang der 4h-Return-Volatilität

Niedriger ist hier meist besser.

---

## 4.3 Normalisierung

### A) BB-Width-Rank
- `score_bb_width = norm_linear_clamped_inv(x, 10, 50, 100)`

Interpretation:
- sehr niedriger Rank = hohe Kompression

---

### B) ATR%-Rank 1d
- `score_atr_rank = norm_linear_clamped_inv(x, 10, 50, 100)`

---

### C) Range vs ATR
Default-Anker:
- `low_good = 50`
- `mid = 100`
- `high_bad = 200`

Formel:
- `score_range_vs_atr = norm_linear_clamped_inv(x, 50, 100, 200)`

---

### D) Std-Return-Rank 4h
- `score_std_return = norm_linear_clamped_inv(x, 10, 50, 100)`

---

## 4.4 Aggregation
Gewichte:
- `0.35` `score_bb_width`
- `0.25` `score_atr_rank`
- `0.25` `score_range_vs_atr`
- `0.15` `score_std_return`

### Formel
`compression_strength = weighted_mean(subscores, weights)`

---

## 4.5 Missing Data
Wenn 4h-Daten fehlen:
- `bb_width_rank_120_4h_pct`
- `range_width_12bars_4h_vs_atr1d_pct`
- `std_return_rank_12bars_4h_pct`
entfallen

Dann bleibt nur ATR-Rank 1d übrig. Das ist **zu wenig** für robuste Kompression.

Regel:
- wenn nur ATR-Rank verbleibt:
  - `compression_strength = null`
  - `axis_compression_strength_not_evaluable = true`

---

## 4.6 Kalibrierungshinweis
MEXC-Altcoins können schon strukturell breiter sein.  
Wenn `range_vs_atr` zu selten gute Werte liefert:
- Good-/Mid-/Bad-Anker empirisch anpassen

### Interaktionshinweis
`compression_strength` und `expansion_progress_structural` können gleichzeitig erhöht sein.  
Das ist **gewollt** und beschreibt Übergangsphasen zwischen Kompression und beginnender Expansion.  
Die Auflösung dieses Spannungsfelds erfolgt **nicht** in Layer 2, sondern später im Phase-Interpreter durch Floors und Gewichte.

---

# 5. Tier-1-Achse: `expansion_progress_structural`

## 5.1 Zweck
Misst, wie weit ein Move strukturell bereits fortgeschritten ist.

Hoher Wert heißt:
- mehr Expansion bereits gelaufen
- geringere Frische
- höheres Risiko für `late/chased`

---

## 5.2 Rohinputs
Nur strukturelle Inputs, keine State-Abhängigkeit:

- `move_from_last_structural_break_pct`
- `bars_since_last_structural_break_4h`
- `dist_to_base_mid_pct`
- `dist_to_ema20_4h_pct_abs`

### Diskrete Definition des `last_structural_break_4h`
Ein **struktureller Break** ist in v2.1 definiert als:

Ein 4h-Bar `t_break`, dessen Close **erstmals** über dem bis dahin gültigen `rolling_high_20_4h` schließt, **nachdem zuvor mindestens 3 abgeschlossene 4h-Bars** mit Close **unter** diesem damaligen `rolling_high_20_4h` lagen.

Wichtig:
- Der Breakanker ist **fixiert auf das Ereignis**
- er läuft **nicht** mit dem Rolling-Window mit
- damit wird ein diskretes Break-Event erkannt, kein gleitendes Dauer-Update

### Abgeleitete Größen
- `fixed_structural_break_anchor_4h`
  - das zum Break-Zeitpunkt gültige `rolling_high_20_4h`
- `break_close_4h`
  - Close des Break-Bars
- `move_from_last_structural_break_pct`
  - prozentuale Distanz aktueller Close zu `break_close_4h`
- `bars_since_last_structural_break_4h`
  - Anzahl abgeschlossener 4h-Bars seit `t_break`
- `dist_to_base_mid_pct`
  - Distanz zur Mitte der letzten strukturellen Base/Range
- `dist_to_ema20_4h_pct_abs`
  - Absolutdistanz in Prozent

---

## 5.3 Normalisierung

### A) Move vom Break
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(3, 30)`
- `(6, 60)`
- `(10, 100)`

---

### B) Bars seit Break
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(1, 20)`
- `(2, 40)`
- `(4, 70)`
- `(6, 100)`

Werte >6 werden auf 100 gecappt.

---

### C) Distanz zur Base-Mitte
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(3, 35)`
- `(6, 65)`
- `(10, 100)`

---

### D) Absolutdistanz zu 4h EMA20
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(2, 30)`
- `(5, 65)`
- `(8, 100)`

---

## 5.4 Aggregation
Gewichte:
- `0.40` Move vom Break
- `0.20` Bars seit Break
- `0.20` Distanz zur Base-Mitte
- `0.20` Distanz zu 4h EMA20

### Formel
`expansion_progress_structural = weighted_mean(subscores, weights)`

---

## 5.5 Missing Data
Wenn 4h fehlt:
- Achse nicht robust evaluierbar

Regel:
- `expansion_progress_structural = null`
- `axis_expansion_progress_not_evaluable = true`

Keine Daily-only Approximation.

---

## 5.6 Kalibrierungshinweis
Diese Achse ist besonders volatilitätssensitiv.  
Die Default-Anker müssen sehr wahrscheinlich nach Coin-Verteilung und Zeitfenster nachgezogen werden.

---

# 6. Tier-1-Achse: `volume_regime_shift`

## 6.1 Zweck
Misst, ob Volumen qualitativ in ein aktiveres Regime kippt.

Nicht gemeint ist:
- ob das Volumen „hoch“ ist
sondern:
- ob sich die Volumenstruktur verbessert

---

## 6.2 Rohinputs
- `volume_quote_spike_1d`
- `volume_quote_spike_4h`
- `volume_spike_persistence_4h`
- `volume_4h_current_vs_median10`

### Definitionen
- `volume_quote_spike_* = current_volume / rolling_sma_volume_excl_current`
- `volume_spike_persistence_4h`
  - Anteil der letzten `N = 4` abgeschlossenen 4h-Bars mit
    `volume_quote_spike_4h >= cfg.volume.persistence_spike_threshold`
  - Ausgabe auf `0..1`
- `volume_4h_current_vs_median10`
  - aktuelles 4h-Volumen relativ zum Median der letzten 10 abgeschlossenen 4h-Bars

Default:
- `cfg.volume.persistence_spike_threshold = 1.2`

---

## 6.3 Normalisierung

### A) 1d Spike
Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = 0.9`
- `mid = 1.2`
- `high = 2.0`

---

### B) 4h Spike
Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = 0.9`
- `mid = 1.2`
- `high = 2.0`

---

### C) Spike-Persistenz
Verwendet:
- `norm_piecewise_linear`

Input `0..1`

Default-Punkte:
- `(0.00, 0)`
- `(0.25, 30)`
- `(0.50, 60)`
- `(0.75, 85)`
- `(1.00, 100)`

---

### D) Current vs Median10
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0.8, 0)`
- `(1.0, 40)`
- `(1.3, 70)`
- `(1.8, 100)`

---

## 6.4 Aggregation
Gewichte:
- `0.25` 1d Spike
- `0.35` 4h Spike
- `0.20` Persistenz 4h
- `0.20` Current vs Median10

### Formel
`volume_regime_shift = weighted_mean(subscores, weights)`

---

## 6.5 Missing Data
Wenn 4h fehlt:
- nur 1d Spike bleibt

Das ist für Regimewechsel zu wenig.

Regel:
- `volume_regime_shift = null`
- `axis_volume_regime_shift_not_evaluable = true`

---

## 6.6 Kalibrierungshinweis
Bei kleinen Altcoins können 4h-Spikes sehr häufig sein.  
Wenn 4h-Spikes zu inflationär hohe Scores liefern:
- Mid/High-Anker anheben, z. B. auf `1.4` / `2.5`

---

# 7. Tier-1-Achse: `freshness_distance_structural`

## 7.1 Zweck
Misst die strukturelle Frische eines Setups **ohne State-Abhängigkeit**.

Diese Achse beantwortet:
- wie nah ist der Preis noch an frischen strukturellen Ankern?

Nicht gemeint ist:
- wie lange ein Coin schon in `early` oder `confirmed` ist  
Das ist später `freshness_distance_state`.

---

## 7.2 Rohinputs
- `distance_to_last_structural_anchor_pct_abs`
- `distance_to_range_high_pct_abs`
- `bars_since_last_volume_shift_event`
- `bars_since_last_structural_break_event`

### Definition von `last_structural_anchor`
Für v2.1 ist der strukturelle Frische-Anker **einheitlich** definiert als:

- `fixed_structural_break_anchor_4h`  
  also der in Abschnitt 5 definierte fixierte Breakanker des letzten strukturellen Break-Ereignisses

Zusätzlich darf `distance_to_range_high_pct_abs` separat einfließen, aber der primäre strukturelle Anker bleibt phasenneutral identisch.

Damit bleibt die Achse kontextfrei.

---

## 7.3 Normalisierung

### A) Distanz zum strukturellen Anker
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(1, 25)`
- `(2, 50)`
- `(3, 75)`
- `(5, 100)`

---

### B) Distanz zum Range-High
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(1, 30)`
- `(2, 55)`
- `(4, 100)`

---

### C) Bars seit Volume-Shift-Event
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(1, 20)`
- `(2, 40)`
- `(4, 70)`
- `(6, 100)`

---

### D) Bars seit strukturellem Break-Event
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(1, 20)`
- `(2, 40)`
- `(4, 70)`
- `(6, 100)`

---

## 7.4 Aggregation
Gewichte:
- `0.35` Distanz zum strukturellen Anker
- `0.25` Distanz zum Range-High
- `0.20` Bars seit Volume-Shift
- `0.20` Bars seit Break-Event

### Formel
`freshness_distance_structural = weighted_mean(subscores, weights)`

---

## 7.5 Missing Data
Wenn 4h fehlt:
- strukturelle Frische kann nur eingeschränkt beurteilt werden

Regel:
- Achse darf mit reduzierter Aussagekraft berechnet werden, falls mindestens zwei Inputs verfügbar sind
- zusätzlicher Flag:
  - `freshness_distance_structural_reduced_resolution = true`

Wenn weniger als zwei Inputs:
- `freshness_distance_structural = null`

---

## 7.6 Kalibrierungshinweis
Für schnelle Meme-Coins sind 2–3 Bars oft schon „alt“.  
Für trägere Mid-Caps ist das noch frisch.  
Diese Achse wird fast sicher später nach Volatilitätsklasse differenziert werden müssen.

---

# 8. Gemeinsames Missing-Data-Verhalten über alle Tier-1-Achsen

## 8.1 Output-Felder pro Achse
Jede Achse soll neben dem Score auch liefern:

- `<axis_name>`
- `<axis_name>_not_evaluable`
- `<axis_name>_reduced_resolution`
- `<axis_name>_effective_weight_ratio`

Beispiel:
- `trend_strength`
- `trend_strength_not_evaluable`
- `trend_strength_reduced_resolution`
- `trend_strength_effective_weight_ratio`

---

## 8.2 4h-Daten-Invariante
Es gilt global:

- `data_4h_available = false`  
  → `early_ready` später nicht zulässig

Diese Regel wirkt nicht hier in Layer 1/2, sondern später in der State Machine.

---

## 8.3 Keine Imputation
Für v2.1 gilt:
- keine Approximation von 4h aus 1d
- keine künstliche Interpolation fehlender Strukturinputs

Nur:
- Gewichtsumlage
- Reduced-Resolution-Flags
- oder Not-Evaluable

---

## 8.4 Konsequenz fehlender 4h-Daten
Coins mit `data_4h_available = false` werden in der Regel maximal folgende Tier-1-Achsen belastbar evaluieren können:
- `trend_strength`
- `reclaim_progress`
- eingeschränkt `freshness_distance_structural`

Dagegen sind typischerweise nicht belastbar:
- `compression_strength`
- `expansion_progress_structural`
- `volume_regime_shift`

Die Phase-Interpretation wird für solche Coins daher häufig:
- `none`
- oder nur eine reduzierte, tägliche Grobeinschätzung liefern

Das ist **beabsichtigt**:  
Ohne 4h-Daten ist die strukturelle Aussagekraft zu gering für robuste Frühsignale.

---

# 9. Zusammenfassung Abschnitt 1

Mit Abschnitt 1 sind die sechs Tier-1-Achsen formal definiert:

- `trend_strength`
- `reclaim_progress`
- `compression_strength`
- `expansion_progress_structural`
- `volume_regime_shift`
- `freshness_distance_structural`

Und zusätzlich festgelegt:
- Standard-Normalisierung
- zusätzliche `norm_piecewise_linear`
- Aggregationsregeln
- Missing-Data-Verhalten
- Kalibrierungshinweise
- keine State-Abhängigkeiten in Layer 2

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 2 – Tier-2-Simplified-Achsen**:
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Darauf baut dann Abschnitt 3, der Phase-Interpreter, sauber auf.
