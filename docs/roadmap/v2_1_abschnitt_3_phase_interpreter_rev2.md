# v2.1 – Abschnitt 3: Phase-Interpreter (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Definition** des Phase-Interpreters.

Der Phase-Interpreter übersetzt die in Abschnitt 1 und 2 definierten Achsen in eine interpretierbare Marktphase:

- `pressure_build`
- `trend_resume`
- `transition_reclaim`
- `none`

Wichtig:
- Die Achsen bleiben **kontextfrei**
- Die Marktphase ist **Interpretation**, nicht Ontologie
- Die Phasenzuweisung ist **deterministisch**
- Hard Floors und weiche Scores werden **streng getrennt**

---

# 1. Grundprinzipien des Phase-Interpreters

## 1.1 Rolle im Gesamtsystem
Der Phase-Interpreter liegt in:

- **Layer 3**

und verwendet als Inputs:
- Tier-1-Achsen aus Abschnitt 1
- Tier-2-Simplified-Achsen aus Abschnitt 2
- deren Evaluierbarkeits- und Resolution-Flags

Er erzeugt:
- `market_phase`
- `market_phase_confidence`
- `market_phase_runner_up`
- `market_phase_gap`
- `market_phase_blended`
- phasenspezifische Rohscores und Floor-Margins

---

## 1.2 Marktphasen
Für v2.1 gibt es genau drei positive Marktphasen:

- `pressure_build`
- `trend_resume`
- `transition_reclaim`

Zusätzlich:
- `none`

---

## 1.3 Zwei-Stufen-Logik je Phase
Jede Phase wird in zwei Schritten bewertet:

### Schritt A – Hard Floors
Wenn die Hard Floors einer Phase **nicht erfüllt** sind:
- `phase_score = 0`

### Schritt B – Weighted Score
Nur wenn die Floors erfüllt sind:
- wird ein gewichteter Phasenscore berechnet

Damit gilt:
- Floors = harte Zulässigkeit
- Score = Qualitätsbewertung innerhalb der zulässigen Phase

---

## 1.4 Kontextfreie Achsen, kontextabhängige Interpretation
Achsen wie:
- `trend_strength`
- `compression_strength`
- `reclaim_progress`

sind **kontextfrei normiert**.

Beispiel:
- `trend_strength = 50` ist nur ein mittlerer Trendwert
- seine Relevanz für `pressure_build` oder `trend_resume` entsteht erst über:
  - Floors
  - Gewichte

---

## 1.5 Keine Pflicht zur Phasenzuweisung
Ein Coin muss **nicht** zwangsläufig einer positiven Phase zugeordnet werden.

Wenn:
- keine Phase ihre Floors erfüllt
- oder der Top-Score unter dem globalen Confidence-Floor bleibt

dann gilt:
- `market_phase = none`

Das ist ausdrücklich gewollt.

---

# 2. Inputs des Phase-Interpreters

## 2.1 Tier-1-Achsen
- `trend_strength`
- `reclaim_progress`
- `compression_strength`
- `expansion_progress_structural`
- `volume_regime_shift`
- `freshness_distance_structural`

## 2.2 Tier-2-Simplified-Achsen
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

## 2.3 Meta-/Hilfsfelder
- `<axis>_not_evaluable`
- `<axis>_reduced_resolution`
- `<axis>_effective_weight_ratio`
- `data_4h_available`
- `data_resolution_class`

## 2.4 Designentscheidung zu `freshness_distance_structural`
Die Achse `freshness_distance_structural` wird im Phase-Interpreter **bewusst nicht** als Hard-Floor oder Score-Input verwendet.

Begründung:
- Der Phase-Interpreter soll **strukturelle Marktphasen** klassifizieren
- Timing- und Staleness-Effekte sollen **nicht** in Layer 3 die Marktphase unterdrücken
- Timing-bezogene Einschränkungen werden ausschließlich später in:
  - **Layer 4 – State Machine**
  behandelt, insbesondere über:
  - `freshness_distance_structural`
  - `freshness_distance_state`
  - state-spezifische `late` / `chased`-Übergänge

Konsequenz:
- Ein Coin kann eine strukturell gültige Phase haben
- und trotzdem später im State-System als `late` oder `chased` enden

Das ist **beabsichtigt**.

---

# 3. Allgemeine Regeln für Floors und Missing Data

## 3.1 Hard-Floor-Regel
Wenn ein Floor-Input:
- `null`
- oder `not_evaluable = true`

ist, dann gilt der entsprechende Floor als **nicht erfüllt**.

Es gibt keine Imputation im Phase-Interpreter.

---

## 3.2 Tier-1-Vorrang
Tier-1-Achsen haben Vorrang vor Tier-2-Simplified-Achsen.

Konsequenz:
- Tier-2-Werte dürfen eine Phase **nicht alleine** tragen
- Tier-2-Werte dürfen nur ergänzen

## 3.3 Mindestanforderung für positive Phase
Eine positive Marktphase (`pressure_build`, `trend_resume`, `transition_reclaim`) darf nur vergeben werden, wenn:

- mindestens **2 Tier-1-Achsen mit Hard-Floor-Relevanz** für diese Phase evaluierbar sind
- und mindestens **1 davon** aus 4h-sensitiver Logik stammt, sofern die Phase auf Frühsignale angewiesen ist

### Vereinfachte Regel v2.1
- `pressure_build` erfordert evaluierbare:
  - `compression_strength`
  - `volume_regime_shift`
- `trend_resume` erfordert evaluierbare:
  - `trend_strength`
  - `reclaim_progress`
- `transition_reclaim` erfordert evaluierbare:
  - `reclaim_progress`
  - `volume_regime_shift` **oder** `trend_strength`

Wenn diese Minimalbasis nicht vorhanden ist:
- `phase_score = 0`

---

## 3.4 Reduced Resolution
Wenn eine Phase nur mit Daily-Fallbacks oder reduziertem Achsenraum bewertet wird:
- Phase darf grundsätzlich noch berechnet werden
- aber:
  - `market_phase_confidence_cap_reduced_resolution = 75`

Das verhindert übertriebene Sicherheit ohne 4h-Qualität.

---

# 4. Phase: `pressure_build`

## 4.1 Intention
`pressure_build` beschreibt Coins mit:
- Kompression
- brauchbarer Basis
- anziehendem Volumenregime
- noch nicht zu weit gelaufener Expansion

Typische Coins:
- PEPE vor sichtbarer Expansion

---

## 4.2 Hard Floors
Ein Coin erfüllt `pressure_build` nur, wenn alle folgenden Floors erfüllt sind:

- `compression_strength >= cfg.phase.pressure_build.floor_compression`
- `volume_regime_shift >= cfg.phase.pressure_build.floor_volume_shift`
- `expansion_progress_structural <= cfg.phase.pressure_build.max_expansion`

### Default-Startwerte
- `floor_compression = 60`
- `floor_volume_shift = 50`
- `max_expansion = 50`

### Hinweis
`max_expansion` ist bewusst **nicht zu eng** gewählt.  
Ein Coin darf bereits erste Expansion zeigen und trotzdem noch `pressure_build` sein.  
Das adressiert den Interaktionseffekt:
- hohe Kompression
- plus bereits beginnende Expansion

---

## 4.3 Phase-Floor-Margin
Für Tie-Break und Diagnose wird berechnet:

- `margin_compression = compression_strength - floor_compression`
- `margin_volume_shift = volume_regime_shift - floor_volume_shift`
- `margin_expansion = max_expansion - expansion_progress_structural`

Dann:
- `phase_floor_margin_pressure_build = min(margin_compression, margin_volume_shift, margin_expansion)`

Wenn irgendeine Margin < 0:
- Floors nicht erfüllt
- `phase_score_pressure_build = 0`

---

## 4.4 Weighted Score
Wenn Floors erfüllt sind, gilt:

Gewichte:
- `0.40` `compression_strength`
- `0.20` `base_integrity_simplified`
- `0.20` `volume_regime_shift`
- `0.20` `(100 - expansion_progress_structural)`

### Formel
`phase_score_pressure_build = weighted_mean(...)`

---

## 4.5 Missing-Data-Regeln
Wenn:
- `compression_strength = null`
- oder `volume_regime_shift = null`
- oder `expansion_progress_structural = null`

dann:
- Floors nicht erfüllbar
- `phase_score_pressure_build = 0`

`base_integrity_simplified` darf fehlen; dann wird sein Gewicht entfernt und re-normalisiert, solange die effektive Gewichtsquote >= 0.60 bleibt.

---

# 5. Phase: `trend_resume`

## 5.1 Intention
`trend_resume` beschreibt Coins mit:
- brauchbarer Trendstruktur
- konstruktivem Pullback
- beginnender Wiederbeschleunigung
- fortschreitendem Reclaim

Typische Coins:
- TAO
- teilweise RIVER

---

## 5.2 Hard Floors
Ein Coin erfüllt `trend_resume` nur, wenn alle folgenden Floors erfüllt sind:

- `trend_strength >= cfg.phase.trend_resume.floor_trend`
- `reclaim_progress >= cfg.phase.trend_resume.floor_reclaim`
- `expansion_progress_structural <= cfg.phase.trend_resume.max_expansion`

### Default-Startwerte
- `floor_trend = 55`
- `floor_reclaim = 45`
- `max_expansion = 65`

### Kalibrierungs-Checkpoint
Die Expansion-Floors sind in v2.1 bewusst großzügig gewählt, um frühe bis mittlere Fortsetzungsphasen nicht zu früh auszuschließen.

Nach ersten Shadow-Runs ist zu prüfen:
- wie `expansion_progress_structural` in der tatsächlichen Top-Population verteilt ist
- ob `max_expansion = 65` zu viele bereits gelaufene Resume-Cases zulässt

---

## 5.3 Phase-Floor-Margin
- `margin_trend = trend_strength - floor_trend`
- `margin_reclaim = reclaim_progress - floor_reclaim`
- `margin_expansion = max_expansion - expansion_progress_structural`

Dann:
- `phase_floor_margin_trend_resume = min(margin_trend, margin_reclaim, margin_expansion)`

Wenn irgendeine Margin < 0:
- Floors nicht erfüllt
- `phase_score_trend_resume = 0`

---

## 5.4 Weighted Score
Wenn Floors erfüllt sind:

Gewichte:
- `0.35` `trend_strength`
- `0.25` `pullback_quality_simplified`
- `0.20` `reacceleration_strength_simplified`
- `0.20` `reclaim_progress`

### Formel
`phase_score_trend_resume = weighted_mean(...)`

---

## 5.5 Missing-Data-Regeln
Wenn:
- `trend_strength = null`
- oder `reclaim_progress = null`
- oder `expansion_progress_structural = null`

dann:
- Floors nicht erfüllbar
- `phase_score_trend_resume = 0`

`pullback_quality_simplified` und `reacceleration_strength_simplified` dürfen fehlen; ihre Gewichte werden entfernt und re-normalisiert, solange die effektive Gewichtsquote >= 0.60 bleibt.

### Korrelationshinweis
`reacceleration_strength_simplified` teilt Rohinputs mit `trend_strength`.  
Die Doppelverwendung ist bewusst, aber im Kalibrierungsprozess zu beobachten.

---

# 6. Phase: `transition_reclaim`

## 6.1 Intention
`transition_reclaim` beschreibt Coins mit:
- fortgeschrittener Rückeroberung
- verbesserter Struktur
- noch nicht voll etabliertem Trend
- brauchbarer Basis und zunehmendem Volumenregime

Typische Coins:
- FET

---

## 6.2 Hard Floors
Ein Coin erfüllt `transition_reclaim` nur, wenn alle folgenden Floors erfüllt sind:

- `reclaim_progress >= cfg.phase.transition_reclaim.floor_reclaim`
- `volume_regime_shift >= cfg.phase.transition_reclaim.floor_volume_shift`
- `expansion_progress_structural <= cfg.phase.transition_reclaim.max_expansion`

### Default-Startwerte
- `floor_reclaim = 45`
- `floor_volume_shift = 45`
- `max_expansion = 55`

---

## 6.3 Phase-Floor-Margin
- `margin_reclaim = reclaim_progress - floor_reclaim`
- `margin_volume_shift = volume_regime_shift - floor_volume_shift`
- `margin_expansion = max_expansion - expansion_progress_structural`

Dann:
- `phase_floor_margin_transition_reclaim = min(margin_reclaim, margin_volume_shift, margin_expansion)`

Wenn irgendeine Margin < 0:
- Floors nicht erfüllt
- `phase_score_transition_reclaim = 0`

---

## 6.4 Weighted Score
Wenn Floors erfüllt sind:

Gewichte:
- `0.40` `reclaim_progress`
- `0.20` `base_integrity_simplified`
- `0.20` `volume_regime_shift`
- `0.20` `(100 - expansion_progress_structural)`

### Formel
`phase_score_transition_reclaim = weighted_mean(...)`

---

## 6.5 Missing-Data-Regeln
Wenn:
- `reclaim_progress = null`
- oder `volume_regime_shift = null`
- oder `expansion_progress_structural = null`

dann:
- Floors nicht erfüllbar
- `phase_score_transition_reclaim = 0`

`base_integrity_simplified` darf fehlen; dann Gewicht entfernen und re-normalisieren, solange effektive Gewichtsquote >= 0.60.

---

# 7. Phase-Confidence, Gap und `none`

## 7.1 Kandidaten-Scores
Nach Berechnung existieren:

- `phase_score_pressure_build`
- `phase_score_trend_resume`
- `phase_score_transition_reclaim`

Alle in `0 .. 100`

---

## 7.2 Top-Phase
- `top_phase = argmax(phase_scores)`
- `top_score = max(phase_scores)`

### 7.2.1 Normalfall für Confidence
Im Normalfall gilt:

- `market_phase_confidence = top_score`

Das heißt:
- Confidence ist zunächst identisch mit dem Top-Phasenscore
- spätere Caps oder Floors können diesen Wert nur begrenzen, nicht erhöhen

## 7.3 Runner-Up
- `runner_up_phase = zweithöchste Phase`
- `runner_up_score = zweithöchster Score`

## 7.4 Gap
- `market_phase_gap = top_score - runner_up_score`

---

## 7.5 Globaler Confidence-Floor
Wenn:
- `top_score < cfg.phase.global_confidence_floor`

dann:
- `market_phase = none`
- `market_phase_confidence = top_score`
- `market_phase_runner_up = runner_up_phase`
- `market_phase_blended = false`

### Default-Startwert
- `global_confidence_floor = 55`

---

## 7.6 Reduced-Resolution-Cap
Wenn:
- die Top-Phase nur in `reduced_resolution` bewertet wurde

dann:
- `market_phase_confidence = min(top_score, cfg.phase.reduced_resolution_confidence_cap)`

Default:
- `reduced_resolution_confidence_cap = 75`

---

# 8. Phase-Blending und Tie-Break

## 8.1 Blended-Flag
Wenn:
- `market_phase_gap < cfg.phase.phase_gap_floor`

dann:
- `market_phase_blended = true`

sonst:
- `market_phase_blended = false`

### Default-Startwert
- `phase_gap_floor = 8`

---

## 8.2 Tie-Break bei exaktem Gleichstand
Wenn mehrere Phasen exakt denselben `phase_score` haben:

### Tie-Break-Stufe 1
Höhere `phase_floor_margin` gewinnt

also max von:
- `phase_floor_margin_pressure_build`
- `phase_floor_margin_trend_resume`
- `phase_floor_margin_transition_reclaim`

### Tie-Break-Stufe 2
Wenn weiterhin Gleichstand:
- feste Prioritätsreihenfolge:

1. `pressure_build`
2. `trend_resume`
3. `transition_reclaim`

### Begründung
Diese Reihenfolge bevorzugt im Zweifel die Phase mit dem höchsten Optionalitätswert für frühe Beobachtung.

---

# 9. Output-Felder des Phase-Interpreters

Der Phase-Interpreter soll mindestens folgende Felder ausgeben:

- `market_phase`
- `market_phase_confidence`
- `market_phase_runner_up`
- `market_phase_gap`
- `market_phase_blended`

Zusätzlich je Phase:
- `phase_score_pressure_build`
- `phase_score_trend_resume`
- `phase_score_transition_reclaim`

Und:
- `phase_floor_margin_pressure_build`
- `phase_floor_margin_trend_resume`
- `phase_floor_margin_transition_reclaim`

Optional sinnvoll:
- `phase_floor_failed_pressure_build`
- `phase_floor_failed_trend_resume`
- `phase_floor_failed_transition_reclaim`

mit Bool-Logik für Debugging/Backtests

---

# 10. Regeln für `none`

## 10.1 `none` bei Floor-Failure
Wenn alle drei Phasen:
- Floors nicht erfüllen

dann:
- `market_phase = none`

## 10.2 `none` bei zu niedrigem Top-Score
Wenn:
- mindestens eine Phase Floors erfüllt
- aber `top_score < global_confidence_floor`

dann ebenfalls:
- `market_phase = none`

## 10.3 `none` bei unzureichender Datenbasis
Wenn die für positive Phasen notwendige Tier-1-Basis nicht evaluierbar ist:
- `market_phase = none`

Das ist besonders relevant bei:
- fehlenden 4h-Daten

---

# 11. Kalibrierungshinweise für Abschnitt 3

## 11.1 Floors sind Startwerte
Alle Floors in Abschnitt 3 sind:
- Startwerte
- konfigurierbar
- nach ersten Live-Runs zu kalibrieren

## 11.2 Überlappung der Phasen
Es ist ausdrücklich möglich, dass ein Coin:
- in zwei Phasen sinnvolle Scores erreicht

Das ist kein Fehler.  
Die Auflösung erfolgt über:
- Top-Score
- Gap
- Blended-Flag
- Tie-Break

## 11.3 Tier-2-Gewichte konservativ halten
Tier-2-Simplified-Achsen sollen Phasen **ergänzen**, nicht dominieren.

Wenn Backtests zeigen, dass Tier-2-Signale zu stark in die Phase ziehen:
- Gewichte reduzieren
- Floors stärker auf Tier 1 stützen

---

# 12. Zusammenfassung Abschnitt 3

Mit Abschnitt 3 ist der Phase-Interpreter formal definiert:

- positive Phasen:
  - `pressure_build`
  - `trend_resume`
  - `transition_reclaim`
- fallback:
  - `none`

Zusätzlich festgelegt:
- Hard Floors
- Weighted Scores
- Floor-Margins
- explizite Definition von `market_phase_confidence`
- bewusste Nicht-Nutzung von `freshness_distance_structural` in Layer 3
- Confidence
- Gap
- Blended-Flag
- Tie-Break
- `none`-Regeln
- Reduced-Resolution-Cap

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 4 – State Machine**:
- Zustände
- vollständige Transition-Tabelle
- Invarianten
- No-change-Fälle
- State-basierte Frische
