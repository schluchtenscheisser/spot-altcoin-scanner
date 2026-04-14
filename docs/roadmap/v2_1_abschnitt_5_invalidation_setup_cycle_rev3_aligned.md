# v2.1 – Abschnitt 5: Invalidation + Setup Cycle im Detail (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Vertiefung** von:

- struktureller Invalidation
- timingbezogener Invalidation
- Setup-Cycle-Reset-Logik

Dieser Abschnitt präzisiert die in Abschnitt 4 verwendeten Begriffe und Regeln, damit:
- Transitionen eindeutig implementierbar sind
- `rejected` sauber von `late/chased` getrennt bleibt
- neue Setup-Zyklen deterministisch erkannt werden

---

# 1. Grundprinzipien

## 1.1 Zwei Arten von Invalidation
Für v2.1 gibt es genau zwei Invalidation-Arten:

### A) `structural_invalidation`
Bedeutung:
- Die zugrunde liegende Struktur ist gebrochen
- Das Setup ist **fachlich kaputt**
- Der Coin gehört nicht mehr in denselben aktiven Setup-Zyklus

### B) `timing_invalidation`
Bedeutung:
- Die Struktur kann noch intakt sein
- Aber die **Entry-Qualität** ist zeitlich oder preislich überholt
- Das Setup ist nicht kaputt, aber der primäre Einstieg ist vorbei

---

## 1.2 Konsequenzen
- `structural_invalidation` führt grundsätzlich zu:
  - `rejected`
- `timing_invalidation` führt grundsätzlich zu:
  - `late`
  - oder `chased`

---

## 1.3 Kein Vermischen
Ein Setup darf nicht gleichzeitig:
- strukturell invalidiert
- und nur timingseitig gealtert
behandelt werden.

Prüfreihenfolge:
1. strukturelle Invalidation
2. timingbezogene Invalidation

Wenn `structural_invalidation = true`, hat das immer Vorrang.

---

# 2. Definition `structural_invalidation`

## 2.1 Allgemeine Definition
`structural_invalidation = true`, wenn mindestens eine der folgenden Bedingungen gilt:

- die marktphasenrelevante Struktur bricht unter definierte Mindest-Hold-Niveaus
- die für den aktuellen Phasen-Typ zentrale Reclaim-/Trend-/Base-Logik geht verloren
- ein aktiver Setup-Zyklus verliert seine strukturelle Grundlage

Wichtig:
- Structural Invalidation bezieht sich auf **die Struktur**, nicht auf Ausführung, Timing oder Frische.

---

## 2.2 Inputs
- `market_phase`
- `trend_strength`
- `reclaim_progress`
- `compression_strength`
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`
- `phase_floor_margin_*`
- `market_phase`
- `market_phase_confidence`

---

## 2.3 Allgemeine globale Structural-Invalidation-Regeln

Ein Coin ist strukturell invalidiert, wenn mindestens eine Regel greift:

### Regel G1
- `market_phase = none`
- **nachdem** der Coin im aktuellen `setup_cycle_id` bereits einmal in einem aktiven positiven State war:
  - `watch`
  - `early_ready`
  - `confirmed_ready`
  - `late`

Wichtig:
- `market_phase = none` **ohne** zuvor aktiven/verfolgten Setup-Zyklus ist **keine** Structural Invalidation
- solche Coins werden in der finalen Implementierung gar nicht erst in die aktive State Machine aufgenommen
- `rejected` bleibt damit für ehemals aktive bzw. bereits bewusst verfolgte Setups reserviert

### Regel G2
- mindestens zwei phasenkritische Tier-1-Achsen werden `null` oder `not_evaluable`
- und damit ist die aktuelle Phase nicht mehr belastbar evaluierbar

### Regel G3
- die aktuelle Phase verliert ihren Floor nicht nur knapp, sondern deutlich unter definierte Hold-Schwellen

---

# 3. Phasenspezifische Structural Invalidation

# 3.1 Phase: `pressure_build`

## 3.1.1 Intention
`pressure_build` bleibt nur intakt, solange:
- Kompression nicht völlig kollabiert
- Basis nicht sichtbar zerfällt
- Volumen-/Strukturverbesserung nicht verschwindet

## 3.1.2 Structural-Invalidation-Regeln
`structural_invalidation = true`, wenn mindestens eine Regel greift:

### P1
- `compression_strength < cfg.invalidation.pressure_build.min_compression_hold`

Default:
- `min_compression_hold = 45`

### P2
- `base_integrity_simplified < cfg.invalidation.pressure_build.min_base_hold`

Default:
- `min_base_hold = 35`

### P3
- `volume_regime_shift < cfg.invalidation.pressure_build.min_volume_shift_hold`

Default:
- `min_volume_shift_hold = 30`

### Hinweis zu Expansion bei `pressure_build`
Eine sehr hohe `expansion_progress_structural` ist **keine structural invalidation** für `pressure_build`.

Begründung:
- starke Expansion ist in der Regel der **Erfolgsfall** der Vorlaufphase
- nicht der Bruch der Struktur
- der Fall wird deshalb **ausschließlich** über:
  - `expansion_progress_structural`
  - `freshness_distance_structural`
  - `freshness_distance_state_*`
  - `late/chased`
abgebildet, nicht über `rejected`

---

# 3.2 Phase: `trend_resume`

## 3.2.1 Intention
`trend_resume` bleibt nur intakt, solange:
- Trendstruktur nicht bricht
- Reclaim nicht kollabiert
- Resume-These nicht sichtbar scheitert

## 3.2.2 Structural-Invalidation-Regeln
`structural_invalidation = true`, wenn mindestens eine Regel greift:

### T1
- `trend_strength < cfg.invalidation.trend_resume.min_trend_hold`

Default:
- `min_trend_hold = 40`

### T2
- `reclaim_progress < cfg.invalidation.trend_resume.min_reclaim_hold`

Default:
- `min_reclaim_hold = 30`

### T3
- `pullback_quality_simplified` evaluierbar
- und `pullback_quality_simplified < cfg.invalidation.trend_resume.min_pullback_quality_hold`

Default:
- `min_pullback_quality_hold = 20`

### T4
- `reacceleration_strength_simplified` evaluierbar
- und `reacceleration_strength_simplified < cfg.invalidation.trend_resume.min_reaccel_hold`
- **nachdem** der Coin bereits mindestens einmal `early_ready` oder `confirmed_ready` war

Default:
- `min_reaccel_hold = 20`

### Persistenzhinweis zu T4
Diese Regel ist **state-history-abhängig** und erfordert persistente State-Felder über Scan-Zyklen hinweg, insbesondere:

- `bars_since_early_entered`
- `bars_since_confirmed_entered`

Beim ersten Scan eines Coins im aktuellen Zyklus ist diese Bedingung per Definition **nicht erfüllt**.

---

# 3.3 Phase: `transition_reclaim`

## 3.3.1 Intention
`transition_reclaim` bleibt nur intakt, solange:
- der Reclaim nicht vollständig verloren geht
- Basis und Strukturverbesserung nicht kollabieren

## 3.3.2 Structural-Invalidation-Regeln
`structural_invalidation = true`, wenn mindestens eine Regel greift:

### R1
- `reclaim_progress < cfg.invalidation.transition_reclaim.min_reclaim_hold`

Default:
- `min_reclaim_hold = 30`

### R2
- `base_integrity_simplified` evaluierbar
- und `base_integrity_simplified < cfg.invalidation.transition_reclaim.min_base_hold`

Default:
- `min_base_hold = 30`

### R3
- `volume_regime_shift < cfg.invalidation.transition_reclaim.min_volume_shift_hold`

Default:
- `min_volume_shift_hold = 25`

---

# 4. Definition `timing_invalidation`

## 4.1 Allgemeine Definition
`timing_invalidation = true`, wenn:
- die Struktur **nicht** kaputt ist
- aber die Setup-Frische oder der Move-Fortschritt so weit gealtert ist,
  dass ein frischer Primärentry nicht mehr angenommen werden soll

Timing Invalidation ist damit:
- **kein struktureller Defekt**
- sondern eine **Zeit-/Distanz-Entwertung**

---

## 4.2 Inputs
- `freshness_distance_structural`
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`
- `expansion_progress_structural`

---

## 4.3 Allgemeine Timing-Invalidation-Regeln

`timing_invalidation = true`, wenn mindestens eine Regel greift:

### Regel TI1
- `freshness_distance_state_early >= cfg.invalidation.timing.max_state_freshness`

Default:
- `max_state_freshness = 100`

### Regel TI2
- `freshness_distance_state_confirmed >= cfg.invalidation.timing.max_state_freshness`

Default:
- `max_state_freshness = 100`

### Regel TI3
- `expansion_progress_structural >= cfg.invalidation.timing.max_expansion_progress`

Default:
- `max_expansion_progress = 95`

### Regel TI4
- `freshness_distance_structural >= cfg.invalidation.timing.max_structural_freshness`
- **und** aktueller State ist mindestens `early_ready`

Default:
- `max_structural_freshness = 90`

---

## 4.4 Konsequenzen
- `timing_invalidation = true` führt **nicht** zu `rejected`
- sondern zu:
  - `late`
  - oder `chased`
je nach State Machine-Prüfreihenfolge und Schweregrad

---

# 5. Verhältnis von `late`, `chased` und Timing Invalidation

## 5.1 `late`
`late` ist die Zone:
- zwischen frischem Setup
- und eindeutig gejagtem Setup

Typisch:
- State-Frische mittel bis hoch
- aber noch nicht maximal entwertet

## 5.2 `chased`
`chased` ist die Zone:
- klar überdehnt
- oder deutlich zu spät

Typisch:
- sehr hohe state-basierte Frische-Distanz
- oder sehr hohe Expansion

## 5.3 Direkter Sprung zu `chased`
Ein Coin kann direkt zu `chased` springen, wenn:
- die Alterung in einem Scan-Intervall stark genug ist
- und `qualifies_chased` vor `qualifies_late` greift

Das ist **beabsichtigt**.

---

# 6. Setup Cycle ID – Zweck und Persistenz

## 6.1 Zweck
`setup_cycle_id` trennt:
- alte, bereits invalidierte oder gejagte Gelegenheiten
von
- neuen, frisch aufgebauten Chancen im selben Symbol

## 6.2 Persistenz
`setup_cycle_id` ist pro Symbol persistent zu führen.

Bei jedem Lauf ist mindestens bekannt:
- `current_setup_cycle_id`
- `previous_setup_cycle_id`

## 6.3 Zyklusende
Ein Zyklus endet, wenn der State in:
- `rejected`
oder
- `chased`
übergeht

Dann wird gesetzt:
- `cycle_end_bar_index`
- `cycle_end_timestamp`

---

# 7. Neue-Zyklus-Erkennung

## 7.1 Grundidee
Ein neuer Zyklus beginnt nicht einfach, weil der Preis gefallen ist.  
Er beginnt erst, wenn:
- ein alter Move ausreichend zurückgesetzt wurde
- eine neue Struktur wieder entsteht
- eine Phase erneut Floors erfüllt

---

## 7.2 Harte Bedingungen für neuen Zyklus
Ein neuer Zyklus wird erkannt, wenn **alle** folgenden Bedingungen erfüllt sind:

### Z1 – Reset der Expansion
- `expansion_progress_structural <= cfg.cycle.reset_max_expansion`

Default:
- `reset_max_expansion = 15`

### Z2 – Mindestabstand zum letzten Zyklusende
- `bars_since_cycle_end >= cfg.cycle.min_bars_reset`

Default:
- `min_bars_reset = 3`

### Z3 – Erneute positive Struktur
Mindestens eine Phase erfüllt wieder alle ihre Hard Floors:
- `pressure_build`
- oder `trend_resume`
- oder `transition_reclaim`

### Z4 – Keine aktive strukturelle Invalidation mehr
- `structural_invalidation = false`

---

## 7.3 Optionaler zusätzlicher Reset-Filter
Für v2.1 optional konfigurierbar:

### Z5 – Reclaim-Reset
- `reclaim_progress` war seit Zyklusende mindestens einmal unter `cfg.cycle.reclaim_reset_floor`
- und steigt anschließend wieder über den Phase-Floor

Default:
- `reclaim_reset_floor = 20`

Hinweis:
- Diese Regel ist optional
- Standard v2.1 benötigt nur Z1–Z4

---

## 7.4 Konsequenz
Wenn neuer Zyklus erkannt:
- `setup_cycle_id += 1`
- `state_machine_state = watch`
- state-interne Frischezähler werden zurückgesetzt:
  - `bars_since_early_entered = null`
  - `bars_since_confirmed_entered = null`
  - `close_at_early_entry_bar = null`
  - `close_at_confirmed_entry_bar = null`
  - `freshness_distance_state_early = null`
  - `freshness_distance_state_confirmed = null`

---

# 8. Reset state-interner Felder

## 8.1 Reset bei `rejected`
Wenn State auf `rejected` wechselt:
- state-interne Frische bleibt historisch erhalten
- aber der Zyklus gilt als beendet

## 8.2 Reset bei `chased`
Wenn State auf `chased` wechselt:
- state-interne Frische bleibt historisch erhalten
- Zyklus gilt als beendet

## 8.3 Reset bei neuem Zyklus
Nur bei neuem Zyklus werden die state-internen Entry-Referenzen gelöscht.

---

# 9. Output-Felder für Invalidation und Cycle

Mindestens auszugeben:

## 9.1 Invalidation-Felder
- `structural_invalidation`
- `structural_invalidation_reason`
- `timing_invalidation`
- `timing_invalidation_reason`

## 9.2 Cycle-Felder
- `setup_cycle_id`
- `new_cycle_detected`
- `cycle_end_bar_index`
- `cycle_end_timestamp`
- `bars_since_cycle_end`

## 9.3 Diagnostische Bool-Felder
Optional, aber sehr nützlich:
- `phase_floor_recovered_since_cycle_end`
- `expansion_reset_condition_met`
- `reclaim_reset_condition_met`

---

# 10. Priorisierte Reason-Codes

Zur Implementierung sollten Reason-Codes geschlossen und deterministisch sein.

## 10.1 Structural Invalidation Reason Codes
- `PHASE_TO_NONE`
- `INSUFFICIENT_TIER1_SUPPORT`
- `PRESSURE_BUILD_COMPRESSION_BREAK`
- `PRESSURE_BUILD_BASE_BREAK`
- `PRESSURE_BUILD_VOLUME_BREAK`
- `TREND_RESUME_TREND_BREAK`
- `TREND_RESUME_RECLAIM_BREAK`
- `TREND_RESUME_PULLBACK_FAILURE`
- `TREND_RESUME_REACCEL_FAILURE`
- `TRANSITION_RECLAIM_RECLAIM_BREAK`
- `TRANSITION_RECLAIM_BASE_BREAK`
- `TRANSITION_RECLAIM_VOLUME_BREAK`

## 10.2 Timing Invalidation Reason Codes
- `STATE_FRESHNESS_EARLY_MAXED`
- `STATE_FRESHNESS_CONFIRMED_MAXED`
- `EXPANSION_PROGRESS_MAXED`
- `STRUCTURAL_FRESHNESS_MAXED`

## 10.3 Cycle Reason Codes
- `NEW_CYCLE_AFTER_RESET`
- `NEW_CYCLE_AFTER_REJECTION`
- `NEW_CYCLE_AFTER_CHASED`

---

# 11. Entscheidungsregeln bei Mehrfachtreffern

## 11.1 Mehrere Structural-Regeln gleichzeitig
Wenn mehrere strukturelle Regeln gleichzeitig greifen:
- `structural_invalidation = true`
- `structural_invalidation_reason` nimmt den **höchst priorisierten** Code

### Prioritätsreihenfolge
1. `PHASE_TO_NONE`
2. `INSUFFICIENT_TIER1_SUPPORT`
3. phasenspezifische Reclaim-/Trend-Breaks
4. Base-/Compression-/Volume-Breaks
5. Reaccel-/Pullback-Breaks

## 11.2 Mehrere Timing-Regeln gleichzeitig
Wenn mehrere timingbezogene Regeln greifen:
- `timing_invalidation = true`
- Reason ist der schwerste Trigger in Reihenfolge:

1. `EXPANSION_PROGRESS_MAXED`
2. `STATE_FRESHNESS_CONFIRMED_MAXED`
3. `STATE_FRESHNESS_EARLY_MAXED`
4. `STRUCTURAL_FRESHNESS_MAXED`

---

# 12. Kalibrierungshinweise

## 12.1 Hold-Schwellen konservativ starten
Structural-Hold-Schwellen sollten eher konservativ gewählt werden, damit:
- normale Schwankung nicht zu schnell `rejected` auslöst

## 12.2 Timing-Schwellen an Scan-Frequenz koppeln
Wenn der Intraday-Scan später nicht alle 4h, sondern z. B. alle 6h läuft:
- Freshness-Schwellen müssen ggf. angepasst werden

## 12.3 Cycle-Reset streng genug halten
Wenn neue Zyklen zu früh erkannt werden:
- `reset_max_expansion` weiter senken
- `min_bars_reset` erhöhen
- optionalen Reclaim-Reset aktivieren

---

# 13. Zusammenfassung Abschnitt 5

Mit Abschnitt 5 sind formal vertieft:

- `structural_invalidation`
- `timing_invalidation`
- `setup_cycle_id`
- neue Zyklus-Erkennung
- Reset state-interner Felder
- Reason-Codes und Priorisierung

Zusätzlich festgelegt:
- klare Trennung zwischen strukturellem Defekt und Timing-Entwertung
- deterministische Regeln je Marktphase
- bei `pressure_build` ist starke Expansion **kein** structural break
- `trend_resume`-Regel T4 ist explizit persistenzabhängig
- deterministischer Neustart eines Setup-Zyklus

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 6 – Daily vs Intraday Update Policy**:
- was wird wann berechnet
- Cache-Regeln
- welche Felder intraday neu laufen
- welche Felder nur daily aktualisiert werden
