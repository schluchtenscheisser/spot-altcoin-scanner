# v2.1 – Abschnitt 2: Tier-2-Simplified-Achsen (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Definition** der drei Tier-2-Achsen in einer bewusst vereinfachten v2.1-Variante:

- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Diese Achsen sind:
- **nicht vollständig pattern-frei**
- aber mit einfachen, deterministischen Heuristiken definierbar
- klar als `_simplified` gekennzeichnet
- für v2.1 als Hilfsachsen für Phase-Interpreter und State Machine gedacht
- später verfeinerbar, ohne die Tier-1-Architektur zu brechen

---

# 1. Grundregeln für Tier-2-Simplified-Achsen

## 1.1 Zweck
Tier-2-Simplified-Achsen erfassen Strukturqualitäten, die in reinen Tier-1-Achsen nicht sauber genug abgebildet werden, aber für Marktphasen und Zustandswechsel relevant sind.

Sie sind bewusst:
- **heuristischer**
- **einfacher**
- **weniger universell robust**
als Tier 1.

## 1.2 Skala
Jede Achse liefert:
- `0 .. 100`

Interpretation:
- `0` = sehr schwach / unbrauchbar
- `50` = gemischt / mittel
- `100` = sehr stark / hochwertig

## 1.3 Kennzeichnung
Alle drei Achsen werden im Output und in der Spezifikation ausdrücklich mit `_simplified` geführt.

Das signalisiert:
- keine endgültige Musterlogik
- später austauschbar
- v2.1-kompatible Näherung

## 1.4 Datenbasis
Wo möglich, sollen diese Achsen auf bereits vorhandenen Tier-1-Features und einfachen OHLCV-Ableitungen aufbauen.

Keine diskretionären Chartmuster.  
Keine komplexe Swing-Engine.  
Keine ML- oder Clustering-Komponente in v2.1.

**Wichtig:**  
Einfache deterministische Segmentierungen auf Basis fixer Lookbacks sind zulässig, solange sie:
- ohne Swing-Pivot-Engine auskommen
- keine diskretionären Pattern-Regeln verwenden
- vollständig aus abgeschlossenen OHLCV-Bars ableitbar sind

## 1.5 Missing Data
Wenn 4h-Daten fehlen:
- vereinfachte Daily-only-Berechnung ist in begrenztem Umfang zulässig
- Achse wird dann mit:
  - `<axis>_reduced_resolution = true`
gekennzeichnet

Wenn die Minimalinputs nicht verfügbar sind:
- Achse = `null`
- `<axis>_not_evaluable = true`

---

# 2. Tier-2-Achse: `base_integrity_simplified`

## 2.1 Zweck
Misst, wie stabil und verwertbar eine Basis-/Range-Struktur aktuell ist.

Diese Achse soll **nicht** perfekte Base-Pattern erkennen, sondern pragmatisch beantworten:

- macht der Coin **keine neuen Tiefs**?
- hält sich der Kurs **geordnet** in einer verwertbaren Zone?
- schließen die Kerzen **eher konstruktiv** als chaotisch?
- ist die Basis **stabil genug**, um Pressure Build oder Transition Reclaim zu stützen?

---

## 2.2 Rohinputs

### Primäre Inputs
- `bars_since_last_new_low_4h`
- `range_width_12bars_4h_pct`
- `close_position_in_range_12bars_4h`
- `close_above_range_mid_ratio_12bars_4h`

### Fallback-/Daily-Inputs
- `bars_since_last_new_low_1d`
- `range_width_10bars_1d_pct`
- `close_position_in_range_10bars_1d`
- `close_above_range_mid_ratio_10bars_1d`

### Definitionen

#### A) `bars_since_last_new_low_*`
Anzahl abgeschlossener Bars seit dem letzten neuen Tief relativ zum Lookback-Fenster.

- Für 4h:
  - neues Tief = aktuelles Low unter allen vorherigen Lows der letzten 12 abgeschlossenen 4h-Bars
- Für 1d:
  - analog für die letzten 10 abgeschlossenen 1d-Bars

#### B) `range_width_*_pct`
- `((highest_high - lowest_low) / close) * 100`
über das definierte Fenster

#### C) `close_position_in_range_*`
Relative Position des aktuellen Close innerhalb der Range:
- `0` = am Tief der Range
- `1` = am Hoch der Range

Formel:
- `(close - range_low) / max(range_high - range_low, epsilon)`

#### D) `close_above_range_mid_ratio_*`
Anteil der letzten N Bars, deren Close über der Mitte der jeweiligen Rolling-Range lag.

- Ausgabe: `0 .. 1`

---

## 2.3 Normalisierung

### A) Bars seit letztem neuen Tief
Interpretation:
- mehr Bars ohne neues Tief = bessere Base-Integrität

#### 4h
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(2, 25)`
- `(4, 50)`
- `(8, 80)`
- `(12, 100)`

#### 1d
Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 0)`
- `(2, 35)`
- `(4, 60)`
- `(7, 85)`
- `(10, 100)`

---

### B) Range-Breite
Interpretation:
- zu breite Range = schwächere Base
- zu enge bis moderate Range = bessere Base

#### 4h
Verwendet:
- `norm_linear_clamped_inv`

Default-Anker:
- `low_good = 4`
- `mid = 9`
- `high_bad = 18`

#### 1d
Verwendet:
- `norm_linear_clamped_inv`

Default-Anker:
- `low_good = 8`
- `mid = 15`
- `high_bad = 30`

---

### C) Close-Position in Range
Interpretation:
- Close in oberer Range-Hälfte ist konstruktiver

Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0.0, 0)`
- `(0.25, 20)`
- `(0.50, 50)`
- `(0.75, 80)`
- `(1.00, 100)`

---

### D) Ratio Close über Range-Mitte
Interpretation:
- je mehr Bars über der Mitte schließen, desto konstruktiver

Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0.00, 0)`
- `(0.25, 25)`
- `(0.50, 50)`
- `(0.75, 80)`
- `(1.00, 100)`

---

## 2.4 Aggregation

### Volle 4h-Berechnung
Gewichte:
- `0.30` Bars seit letztem neuen Tief
- `0.20` Range-Breite
- `0.25` Close-Position in Range
- `0.25` Ratio Close über Range-Mitte

Formel:
- `base_integrity_simplified = weighted_mean(subscores, weights)`

### Daily-only-Fallback
Wenn 4h fehlt, aber 1d vorhanden:
- gleiche Logik auf 1d
- Flag:
  - `base_integrity_simplified_reduced_resolution = true`

---

## 2.5 Missing Data
Wenn weder 4h noch ausreichende 1d-Daten verfügbar:
- `base_integrity_simplified = null`
- `axis_base_integrity_simplified_not_evaluable = true`

---

## 2.6 Kalibrierungshinweis
Diese Achse ist besonders sensitiv für:
- Lookback-Länge
- Range-Breiten-Anker
- Coin-Volatilität

Wenn zu viele Coins trotz chaotischer Struktur >70 erreichen:
- Range-Breiten-Anker strenger setzen
- Gewicht auf `bars_since_last_new_low` senken

---

# 3. Tier-2-Achse: `pullback_quality_simplified`

## 3.1 Zweck
Misst, ob ein laufender Rücksetzer eher **konstruktiv** oder **destruktiv** ist.

Die Achse ist besonders relevant für:
- `trend_resume`
- spätere `early_ready`- und `confirmed_ready`-Übergänge nach Pullback

Sie soll in v2.1 **kein perfektes Swing-Modell** abbilden, sondern pragmatisch beantworten:

- ist der Pullback **nicht zu tief**?
- ist er **nicht chaotisch**?
- läuft er mit **geringerem Volumen** als der vorherige Impuls?
- bleibt der Kurs an brauchbaren Trendankern?

---

## 3.2 Einfache Impuls-/Pullback-Segmentierung v2.1

Diese Achse verwendet eine **deterministische Mini-Segmentierung**, aber **keine Swing-Engine**.

### 4h-Definition
Betrachte die letzten 20 abgeschlossenen 4h-Bars.

#### Schritt 1: Impulsstart
- `impulse_start_idx` = Index des **tiefsten Close** innerhalb der letzten 20 abgeschlossenen 4h-Bars

#### Schritt 2: Impulshoch
- `impulse_high_idx` = Index des **höchsten High** innerhalb derselben 20 Bars

#### Schritt 3: Gültigkeit
Die Segmentierung ist nur gültig, wenn:
- `impulse_high_idx > impulse_start_idx`

Andernfalls gilt:
- kein sinnvoller Aufwärtsimpuls identifizierbar
- `pullback_quality_simplified = null`
- `axis_pullback_quality_simplified_not_evaluable = true`

#### Schritt 4: Pullback
Wenn gültig:
- `impulse_start_price = close[impulse_start_idx]`
- `impulse_high_price = high[impulse_high_idx]`
- `pullback_low_price = min(low[k])` für alle abgeschlossenen Bars `k` von `impulse_high_idx` bis `current_idx`
- `current_pullback_close = close[current_idx]`

### 1d-Fallback
Analog auf den letzten 15 abgeschlossenen 1d-Bars.

---

## 3.3 Rohinputs

### Primäre Inputs
- `pullback_depth_vs_last_impulse_pct_4h`
- `pullback_volume_ratio_4h`
- `close_vs_ema20_4h_pct`
- `lowest_low_vs_ema20_4h_pct`

### Fallback-/Daily-Inputs
- `pullback_depth_vs_last_impulse_pct_1d`
- `pullback_volume_ratio_1d`
- `close_vs_ema20_1d_pct`
- `lowest_low_vs_ema20_1d_pct`

### Definitionen

#### A) `pullback_depth_vs_last_impulse_pct_*`
Tiefe des Rücksetzers relativ zur Größe des letzten Aufwärtsimpulses.

Formel:
- `100 * (impulse_high_price - pullback_low_price) / max(impulse_high_price - impulse_start_price, epsilon)`

Interpretation:
- 0 = kein Rücksetzer
- 100 = kompletter Rücklauf des letzten Impulses
- >100 = Rücksetzer tiefer als der letzte Impuls

#### B) `pullback_volume_ratio_*`
Volumen im Pullback relativ zum Volumen im vorangegangenen Impuls.

Formel:
- `mean(volume[k]) for k in [impulse_high_idx .. current_idx] / max(mean(volume[k]) for k in [impulse_start_idx .. impulse_high_idx], epsilon)`

Interpretation:
- <1 = Pullback auf kleinerem Volumen = eher konstruktiv
- >1 = Pullback auf größerem Volumen = eher schwach

#### C) `close_vs_ema20_*_pct`
bereits definiert in Abschnitt 1

#### D) `lowest_low_vs_ema20_*_pct`
niedrigster Pullback-Low relativ zur EMA20

Formel:
- `((pullback_low_price / ema20_current) - 1) * 100`

---

## 3.4 Normalisierung

### A) Pullback-Tiefe
Interpretation:
- flach bis moderat = gut
- zu tief = schlecht

Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0, 70)`
- `(20, 100)`
- `(40, 75)`
- `(60, 40)`
- `(100, 0)`

**Hinweis:**  
Diese Kurve ist bewusst **nicht-monoton**.  
Ein moderater Pullback um etwa 20 % wird als optimal bewertet.  
Sowohl **kein Pullback** als auch **zu tiefer Pullback** werden abgewertet.

---

### B) Pullback-Volumen-Ratio
Interpretation:
- kleiner als 1 ist gut
- deutlich über 1 ist schlecht

Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0.3, 100)`
- `(0.6, 85)`
- `(1.0, 50)`
- `(1.3, 20)`
- `(1.8, 0)`

---

### C) Close vs EMA20
Interpretation:
- über EMA20 = konstruktiv
- knapp darunter = noch ok
- weit darunter = schwach

Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = -8`
- `mid = 0`
- `high = +8`

---

### D) Pullback-Low vs EMA20
Interpretation:
- Pullback-Low knapp an oder über EMA20 = gut
- deutlich darunter = schwach

Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = -10`
- `mid = -2`
- `high = +4`

---

## 3.5 Aggregation

### Volle 4h-Berechnung
Gewichte:
- `0.35` Pullback-Tiefe
- `0.25` Pullback-Volumen-Ratio
- `0.20` Close vs EMA20
- `0.20` Pullback-Low vs EMA20

Formel:
- `pullback_quality_simplified = weighted_mean(subscores, weights)`

### Daily-only-Fallback
Wenn 4h fehlt, aber 1d vorhanden:
- gleiche Logik auf 1d
- Flag:
  - `pullback_quality_simplified_reduced_resolution = true`

---

## 3.6 Missing Data
Wenn Pullback nicht sinnvoll identifizierbar ist oder Minimalinputs fehlen:
- `pullback_quality_simplified = null`
- `axis_pullback_quality_simplified_not_evaluable = true`

---

## 3.7 Kalibrierungshinweis
Diese Achse ist stark setup- und volatilitätsabhängig.  
Wenn Momentum-Coins zu oft wegen „zu flachem Pullback“ schlecht bewertet werden:
- linken Teil der Tiefenfunktion anheben
- oder Gewicht von Tiefe reduzieren

---

# 4. Tier-2-Achse: `reacceleration_strength_simplified`

## 4.1 Zweck
Misst, ob nach Stabilisierung oder Pullback wieder **echte Beschleunigung** einsetzt.

Diese Achse ist besonders wichtig für:
- `trend_resume`
- späte `early_ready`- und `confirmed_ready`-Übergänge
- Abgrenzung zwischen bloßem Bounce und echter Wiederaufnahme

Sie soll v2.1-seitig pragmatisch beantworten:

- schließt der Coin wieder über kurzfristigen Strukturmarken?
- steigt Volumen wieder an?
- stabilisiert sich die 4h-EMA-Slope?
- verbessert sich die kurzfristige Struktur sichtbar?

---

## 4.2 Rohinputs

### Primäre Inputs
- `close_vs_rolling_high_5_4h_pct`
- `volume_4h_current_vs_median10`
- `ema20_slope_4h_pct_per_bar`
- `close_vs_ema20_4h_pct`

### Fallback-/Daily-Inputs
- `close_vs_rolling_high_5_1d_pct`
- `volume_1d_current_vs_median10`
- `ema20_slope_1d_pct_per_bar`
- `close_vs_ema20_1d_pct`

### Definitionen

#### A) `close_vs_rolling_high_5_*_pct`
Close relativ zum Rolling-High der letzten 5 abgeschlossenen Bars

Formel:
- `((close / rolling_high_5_excl_current_anchor) - 1) * 100`

Interpretation:
- positiver Wert = Rebreak / Strukturverbesserung

#### B) `volume_*_current_vs_median10`
aktuelles Volumen relativ zum Median der letzten 10 Bars

#### C) `ema20_slope_*_pct_per_bar`
wie in Abschnitt 1

#### D) `close_vs_ema20_*_pct`
wie in Abschnitt 1

---

## 4.3 Normalisierung

### A) Close vs Rolling-High 5
Interpretation:
- unterhalb = schwach
- am Level = neutral
- darüber = Beschleunigung

Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = -4`
- `mid = 0`
- `high = +4`

---

### B) Volumen vs Median10
Interpretation:
- aktuelles Volumen steigt wieder an = positiv

Verwendet:
- `norm_piecewise_linear`

Default-Punkte:
- `(0.8, 10)`
- `(1.0, 40)`
- `(1.2, 65)`
- `(1.5, 85)`
- `(2.0, 100)`

---

### C) EMA20-Slope
Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = -1.0`
- `mid = 0`
- `high = +1.0`

---

### D) Close vs EMA20
Verwendet:
- `norm_linear_clamped`

Default-Anker:
- `low = -6`
- `mid = 0`
- `high = +6`

---

## 4.4 Aggregation

### Volle 4h-Berechnung
Gewichte:
- `0.35` Close vs Rolling-High 5
- `0.25` Volumen vs Median10
- `0.20` EMA20-Slope
- `0.20` Close vs EMA20

Formel:
- `reacceleration_strength_simplified = weighted_mean(subscores, weights)`

### Daily-only-Fallback
Wenn 4h fehlt, aber 1d vorhanden:
- gleiche Logik auf 1d
- Flag:
  - `reacceleration_strength_simplified_reduced_resolution = true`

Wichtig:
- Daily-only-Reacceleration ist schwächerer Evidenzgrad
- spätere Early-Promotion bleibt dennoch 4h-pflichtig

---

## 4.5 Missing Data
Wenn Minimalinputs fehlen:
- `reacceleration_strength_simplified = null`
- `axis_reacceleration_strength_simplified_not_evaluable = true`

---

## 4.6 Kalibrierungshinweis
Wenn zu viele Coins wegen kleiner Rebreaks bereits hohe Werte erreichen:
- High-Anker für `close_vs_rolling_high_5` anheben
- Gewicht auf Volumenkomponente reduzieren oder strenger machen

**Hinweis zur Korrelation mit Tier 1:**  
`reacceleration_strength_simplified` teilt Rohinputs mit `trend_strength`, insbesondere:
- `ema20_slope_*`
- `close_vs_ema20_*`

Das ist zulässig, erhöht aber die Korrelation beider Achsen.  
Im Phase-Interpreter von Abschnitt 3 muss diese Doppelverwendung über Gewichte bewusst berücksichtigt werden.

---

# 5. Gemeinsame Regeln für Tier-2-Simplified-Achsen

## 5.1 Output-Felder pro Achse
Jede Tier-2-Achse soll neben dem Score auch liefern:

- `<axis_name>`
- `<axis_name>_not_evaluable`
- `<axis_name>_reduced_resolution`
- `<axis_name>_effective_weight_ratio`

Beispiel:
- `base_integrity_simplified`
- `base_integrity_simplified_not_evaluable`
- `base_integrity_simplified_reduced_resolution`
- `base_integrity_simplified_effective_weight_ratio`

---

## 5.2 Verhältnis zu Tier 1
Tier-2-Simplified-Achsen:
- ersetzen Tier 1 **nicht**
- ergänzen Tier 1 **nur**
- werden später im Phase-Interpreter und in der State Machine niedriger priorisiert als harte Tier-1-Signale

## 5.3 Keine vollständige Mustererkennung
Für v2.1 gilt:
- keine echte Swing-Engine
- keine diskretionären Pattern
- keine automatisierte Chartmusterklassifikation
- nur einfache, deterministische Näherungen

## 5.4 Hinweis zu Daily-Fallbacks
Tier-2-Simplified-Achsen können teilweise als Daily-Fallback berechnet werden.  
Das bedeutet **nicht**, dass sie ohne Tier-1-Achsen allein robuste Marktphasen tragen sollen.

Die Entscheidung, ob:
- Tier-2-Achsen ohne ausreichende Tier-1-Achsen
überhaupt für eine Phase-Zuweisung ausreichen, wird erst in Abschnitt 3 explizit geregelt.

---

# 6. Zusammenfassung Abschnitt 2

Mit Abschnitt 2 sind die drei Tier-2-Simplified-Achsen formal definiert:

- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Und zusätzlich festgelegt:
- klare Vereinfachung als `_simplified`
- exakte Inputs
- Normalisierung
- Aggregation
- Missing-Data-Verhalten
- Kalibrierungshinweise

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 3 – Phase-Interpreter**:
- Hard Floors
- Phase-Scores
- Confidence
- Gap
- Tie-Break
- `none`-Regel
