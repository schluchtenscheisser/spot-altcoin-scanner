# v2.1 – Abschnitt 4: State Machine (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Definition** der State Machine.

Die State Machine liegt in:
- **Layer 4**

Sie verarbeitet:
- Marktphase aus Abschnitt 3
- Tier-1- und Tier-2-Achsen
- strukturelle und timingbezogene Invalidation
- state-basierte Frische

Und erzeugt:
- `state_machine_state`
- `state_confidence`
- `state_transition_reason`
- state-bezogene Frische- und Altersfelder

---

# 1. Zweck und Grundprinzipien

## 1.1 Zweck
Die State Machine bewertet **nicht**, welche Marktphase vorliegt, sondern:

- wie **reif** die Gelegenheit ist
- ob sie bereits **früh interessant**
- **bestätigt**
- **zu spät**
- oder **ungültig** ist

Sie löst damit das binäre Problem:
- nicht nur `entry_ready = true/false`
- sondern ein strukturierter Reifegrad-Zustand

---

## 1.2 Zustände
Für v2.1 existieren genau diese Zustände:

- `watch`
- `early_ready`
- `confirmed_ready`
- `late`
- `chased`
- `rejected`

Zusätzlich technisch relevant:
- `watch_new_cycle` wird **nicht** als eigener Endzustand geführt
- sondern als `watch` mit neuer `setup_cycle_id`

---

## 1.3 Reihenfolge
Die State Machine läuft **nach** dem Phase-Interpreter und **vor** Entry-Pattern-Resolution.

Reihenfolge:
1. Eligibility
2. Tier-1-Achsen
3. Tier-2-Achsen
4. Phase-Interpreter
5. **State Machine**
6. Entry-Pattern
7. Execution
8. Decision

---

## 1.4 Grundsatz
Die State Machine operiert auf:
- Achsen
- Phase
- Frische
- Invalidation
- Auflösungsqualität

Nicht auf:
- Orderbuch
- Slippage
- finaler Entscheidung
- Entry-Pattern-Label

---

# 2. Inputs der State Machine

## 2.1 Strukturelle Inputs
- `market_phase`
- `market_phase_confidence`
- `market_phase_gap`
- `market_phase_blended`
- alle Tier-1-Achsen
- alle Tier-2-Simplified-Achsen

## 2.2 Frische-Inputs
- `freshness_distance_structural`
- `expansion_progress_structural`

## 2.3 Datenqualitäts-Inputs
- `data_4h_available`
- `data_resolution_class`
- `<axis>_not_evaluable`
- `<axis>_reduced_resolution`

## 2.4 State-interne Inputs
- `prev_state_machine_state`
- `prev_setup_cycle_id`
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`

Diese Felder werden innerhalb der State Machine selbst geführt oder aus dem letzten Lauf persisted.

---

# 3. State-basierte Frische

## 3.1 Trennung von struktureller und state-basierter Frische
Es existieren zwei Frische-Dimensionen:

### A) `freshness_distance_structural`
aus Abschnitt 1  
- state-unabhängig
- Layer 2
- struktureller Abstand zu frischen Ankern

### B) `freshness_distance_state`
nur in Layer 4  
- abhängig vom erreichten State
- misst Alterung **seit** Early- oder Confirmed-Übergang

---

## 3.2 Definition der state-internen Distanzfelder

### A) `close_at_early_entry_bar`
Der Close des abgeschlossenen Bars, in dem der Coin **erstmals** in den State `early_ready` übergeht.

### B) `close_at_confirmed_entry_bar`
Der Close des abgeschlossenen Bars, in dem der Coin **erstmals** in den State `confirmed_ready` übergeht.

### C) `distance_from_ideal_entry_after_early`
Formel:
- `((current_close / close_at_early_entry_bar) - 1) * 100`

Wenn der Coin noch nie `early_ready` war:
- `null`

### D) `distance_from_ideal_entry_after_confirmed`
Formel:
- `((current_close / close_at_confirmed_entry_bar) - 1) * 100`

Wenn der Coin noch nie `confirmed_ready` war:
- `null`

### Hinweis
Die Felder basieren **nicht** auf Entry-Pattern-Outputs aus Layer 5.  
Sie sind rein state-intern und damit zirkularitätsfrei.

---

## 3.3 Berechnung `freshness_distance_state_early`
Wenn State noch nie `early_ready` war:
- `null`

Sonst:
- gewichtete Kombination aus:
  - Bars seit Early
  - Distanz seit Early

### Default-Normalisierung Bars
Verwendet:
- `norm_piecewise_linear`

Punkte:
- `(0, 0)`
- `(1, 20)`
- `(2, 40)`
- `(4, 70)`
- `(6, 100)`

### Default-Normalisierung Distanz
Verwendet:
- `norm_piecewise_linear`

Punkte:
- `(0, 0)`
- `(1, 25)`
- `(2, 50)`
- `(3, 75)`
- `(5, 100)`

### Aggregation
- `0.50` Bars-Komponente
- `0.50` Distanz-Komponente

---

## 3.4 Berechnung `freshness_distance_state_confirmed`
Wenn State noch nie `confirmed_ready` war:
- `null`

Sonst gleiche Logik mit:
- `bars_since_confirmed_entered`
- `distance_from_ideal_entry_after_confirmed`

---

# 4. State-Confidence

## 4.1 Definition
`state_confidence` ist ein eigener Wert in:
- `0..100`

Er beschreibt:
- wie gut der **aktuelle State** durch Phase und Achsen gestützt ist

## 4.2 Normalfall
Initial gilt:
- `state_confidence = market_phase_confidence`

Danach kann der Wert durch:
- Reduced Resolution
- späte Frische
- Blended Phase
- Grenzfallnähe an State-Schwellen

nach unten begrenzt werden

## 4.3 Confidence-Penalties
Default-Penalties:
- wenn `market_phase_blended = true` → `-5`
- wenn `data_resolution_class != full_1d_4h` → `-10`
- wenn aktueller State auf knappen Margins beruht → `-5`
- clamp auf `0..100`

---

# 5. Hard Invarianten der State Machine

Diese Regeln gelten strikt:

## 5.1 Nicht erlaubte Rücksprünge
- `late -> confirmed_ready` ist **nicht erlaubt**
- `chased -> late` ist **nicht erlaubt**
- `chased -> confirmed_ready` ist **nicht erlaubt**
- `chased -> early_ready` ist **nicht erlaubt**
- `rejected -> early_ready` ist **nicht direkt erlaubt**
- `rejected -> confirmed_ready` ist **nicht direkt erlaubt**

## 5.2 Neuer Zyklus erforderlich
Ein Coin in:
- `chased`
- `rejected`

kann nur über **neue `setup_cycle_id`** wieder in einen aktiven Zustand zurückkehren.

Dann beginnt er wieder bei:
- `watch`

## 5.3 `early_ready` benötigt 4h
Es gilt hart:
- `data_4h_available = false`
  → `early_ready` **nicht erlaubt**

## 5.4 `confirmed_ready` ohne 4h
`confirmed_ready` darf in v2.1 in `daily_only` nur dann erreicht werden, wenn:
- Phase = `trend_resume` oder `transition_reclaim`
- `market_phase_confidence >= cfg.state.confirmed.daily_only_min_phase_confidence`

Default:
- `daily_only_min_phase_confidence = 70`

Für `pressure_build` bleibt:
- ohne 4h kein `confirmed_ready`

## 5.5 Direkte Transition `watch -> confirmed_ready`
Die direkte Transition:

- `watch -> confirmed_ready`

ist in v2.1 **bewusst erlaubt**.

Begründung:
- Der Scanner kann einen Coin erstmals sehen, wenn er bereits alle Confirmed-Bedingungen erfüllt
- insbesondere im Daily Discovery Scan ist es möglich, dass `early_ready` zeitlich nie beobachtet wurde
- den Coin künstlich erst in `watch` oder `early_ready` zu halten, wäre fachlich falsch

Konsequenz:
- die State Machine modelliert primär den **aktuellen Reifegrad**
- nicht zwingend jede historisch durchlaufene Zwischenstufe

---

# 6. State-spezifische Eintrittsbedingungen

## 6.1 `watch`
Ein Coin ist `watch`, wenn:
- `market_phase != none`
- keine strukturelle Invalidation vorliegt
- keine Early-/Confirmed-/Late-/Chased-Bedingung greift

`watch` ist der Default-Aktivzustand.

---

## 6.2 `early_ready`

### Allgemeine Bedingungen
- `market_phase != none`
- `data_4h_available = true`
- keine strukturelle Invalidation
- `freshness_distance_structural <= cfg.state.early.max_structural_freshness`

Default:
- `max_structural_freshness = 65`

### Phasenspezifische Bedingungen

#### A) `pressure_build`
- `compression_strength >= cfg.state.early.pressure_build.min_compression`
- `volume_regime_shift >= cfg.state.early.pressure_build.min_volume_shift`
- `expansion_progress_structural <= cfg.state.early.pressure_build.max_expansion`

Defaults:
- `min_compression = 65`
- `min_volume_shift = 55`
- `max_expansion = 45`

#### B) `trend_resume`
- `trend_strength >= cfg.state.early.trend_resume.min_trend`
- `reclaim_progress >= cfg.state.early.trend_resume.min_reclaim`
- `reacceleration_strength_simplified >= cfg.state.early.trend_resume.min_reaccel`

Defaults:
- `min_trend = 55`
- `min_reclaim = 40`
- `min_reaccel = 50`

#### C) `transition_reclaim`
- `reclaim_progress >= cfg.state.early.transition_reclaim.min_reclaim`
- `volume_regime_shift >= cfg.state.early.transition_reclaim.min_volume_shift`

Defaults:
- `min_reclaim = 45`
- `min_volume_shift = 45`

---

## 6.3 `confirmed_ready`

### Allgemeine Bedingungen
- `market_phase != none`
- keine strukturelle Invalidation
- `freshness_distance_structural <= cfg.state.confirmed.max_structural_freshness`

Default:
- `max_structural_freshness = 55`

### Phasenspezifische Bedingungen

#### A) `pressure_build`
- `data_4h_available = true`
- `reclaim_progress >= cfg.state.confirmed.pressure_build.min_reclaim`
- `compression_strength >= cfg.state.confirmed.pressure_build.min_compression`
- `volume_regime_shift >= cfg.state.confirmed.pressure_build.min_volume_shift`
- `expansion_progress_structural <= cfg.state.confirmed.pressure_build.max_expansion`

Defaults:
- `min_reclaim = 55`
- `min_compression = 60`
- `min_volume_shift = 55`
- `max_expansion = 50`

#### B) `trend_resume`
- `reclaim_progress >= cfg.state.confirmed.trend_resume.min_reclaim`
- `trend_strength >= cfg.state.confirmed.trend_resume.min_trend`
- `reacceleration_strength_simplified >= cfg.state.confirmed.trend_resume.min_reaccel`

Defaults:
- `min_reclaim = 50`
- `min_trend = 60`
- `min_reaccel = 55`

#### C) `transition_reclaim`
- `reclaim_progress >= cfg.state.confirmed.transition_reclaim.min_reclaim`
- `trend_strength >= cfg.state.confirmed.transition_reclaim.min_trend_after_reclaim`

Defaults:
- `min_reclaim = 55`
- `min_trend_after_reclaim = 50`

---

## 6.4 `late`
Ein Coin wird `late`, wenn:
- keine strukturelle Invalidation vorliegt
- aber der aktive frische Entry-Zustand zeitlich oder preislich gealtert ist

Trigger:
- `freshness_distance_state_early >= cfg.state.late.min_state_freshness`
oder
- `freshness_distance_state_confirmed >= cfg.state.late.min_state_freshness`

Default:
- `min_state_freshness = 60`

Zusätzlich darf `late` auch gesetzt werden, wenn:
- Confirmed-Bedingungen nicht mehr erfüllt sind
- die Phase aber noch intakt ist

---

## 6.5 `chased`
Ein Coin wird `chased`, wenn:
- keine strukturelle Invalidation vorliegt
- aber der Move klar zu weit fortgeschritten ist

Trigger:
- `freshness_distance_state_early >= cfg.state.chased.min_state_freshness`
oder
- `freshness_distance_state_confirmed >= cfg.state.chased.min_state_freshness`
oder
- `expansion_progress_structural >= cfg.state.chased.min_expansion_progress`

Defaults:
- `min_state_freshness = 85`
- `min_expansion_progress = 80`

### Hinweis
Ein Coin kann in v2.1 direkt von:
- `watch`
- `early_ready`
- `confirmed_ready`

nach `chased` springen, wenn die Chased-Schwellen in einem Scan-Intervall direkt erreicht oder überschritten werden.

Das ist **beabsichtigt**.  
Der Zwischenstatus `late` wird in solchen Fällen übersprungen, weil die State Machine den **aktuellen** Reifegrad abbildet, nicht zwingend jede hypothetische Zwischenstufe.

---

## 6.6 `rejected`
Ein Coin wird `rejected`, wenn:
- strukturelle Invalidation vorliegt
- oder kein positiver State zulässig bleibt
- oder Phase = `none` und kein neuer Zyklus aktiv ist

---

# 7. Strukturelle und timingbezogene Invalidation

## 7.1 Structural Invalidation
`structural_invalidation = true`, wenn mindestens eine Regel erfüllt ist.

### Allgemeine Regeln
- `market_phase = none` nach zuvor aktivem Zyklus
- relevante Floor-Achsen kollabieren deutlich unter Minimalniveau
- Reclaim fällt klar zurück
- Trendstruktur bricht sichtbar

### Vereinfachte v2.1-Regeln je Phase

#### `pressure_build`
- `compression_strength < cfg.invalidation.pressure_build.min_compression_hold`
oder
- `base_integrity_simplified < cfg.invalidation.pressure_build.min_base_hold`

Defaults:
- `min_compression_hold = 45`
- `min_base_hold = 35`

#### `trend_resume`
- `trend_strength < cfg.invalidation.trend_resume.min_trend_hold`
oder
- `reclaim_progress < cfg.invalidation.trend_resume.min_reclaim_hold`

Defaults:
- `min_trend_hold = 40`
- `min_reclaim_hold = 30`

#### `transition_reclaim`
- `reclaim_progress < cfg.invalidation.transition_reclaim.min_reclaim_hold`

Default:
- `min_reclaim_hold = 30`

---

## 7.2 Timing Invalidation
`timing_invalidation = true`, wenn:
- keine strukturelle Invalidation vorliegt
- aber der Coin zu alt oder zu weit gelaufen ist

Trigger:
- `freshness_distance_state_early >= 100`
oder
- `freshness_distance_state_confirmed >= 100`
oder
- `expansion_progress_structural >= 95`

Timing Invalidation führt nicht zu `rejected`, sondern zu:
- `late`
oder
- `chased`

### Hinweis
In der Prüfreihenfolge wird `chased` **vor** `late` geprüft.  
Dadurch kann ein Coin bei starkem Aging in einem einzigen Scan-Schritt direkt:
- von `early_ready` nach `chased`
- oder von `confirmed_ready` nach `chased`

springen.

Das ist **konsistent und beabsichtigt**.

---

# 8. Setup Cycle ID

## 8.1 Zweck
Die `setup_cycle_id` verhindert chaotische Rücksprünge aus:
- `rejected`
- `chased`

## 8.2 Neue Zyklus-Erkennung
Ein neuer Zyklus beginnt, wenn:

- `expansion_progress_structural <= cfg.cycle.reset_max_expansion`
- und `bars_since_cycle_end >= cfg.cycle.min_bars_reset`
- und mindestens eine positive Phase ihre Floors wieder erfüllt

Defaults:
- `reset_max_expansion = 15`
- `min_bars_reset = 3`

Dann:
- `setup_cycle_id += 1`
- State startet neu als `watch`

---

# 9. Vollständige Transition-Tabelle

## 9.1 Notation
Format:
- `[current_state, trigger_condition] -> new_state`

Reihenfolge der Prüfung:
1. neuer Zyklus?
2. strukturelle Invalidation?
3. chased?
4. late?
5. confirmed?
6. early?
7. watch / no change

---

## 9.2 Transition-Matrix

### Aus `watch`

- `[watch, new_cycle_detected] -> watch`
- `[watch, structural_invalidation] -> rejected`
- `[watch, phase_none_without_prior_active_cycle] -> not_admitted / no_active_state`
- `[watch, qualifies_confirmed_ready] -> confirmed_ready`
- `[watch, qualifies_early_ready] -> early_ready`
- `[watch, otherwise] -> watch`

### Aus `early_ready`

- `[early_ready, new_cycle_detected] -> watch`
- `[early_ready, structural_invalidation] -> rejected`
- `[early_ready, qualifies_chased] -> chased`
- `[early_ready, qualifies_late] -> late`
- `[early_ready, qualifies_confirmed_ready] -> confirmed_ready`
- `[early_ready, loses_early_but_phase_intact] -> watch`
- `[early_ready, otherwise] -> early_ready`

### Aus `confirmed_ready`

- `[confirmed_ready, new_cycle_detected] -> watch`
- `[confirmed_ready, structural_invalidation] -> rejected`
- `[confirmed_ready, qualifies_chased] -> chased`
- `[confirmed_ready, qualifies_late] -> late`
- `[confirmed_ready, loses_confirmed_but_phase_intact] -> late`
- `[confirmed_ready, otherwise] -> confirmed_ready`

### Aus `late`

- `[late, new_cycle_detected] -> watch`
- `[late, structural_invalidation] -> rejected`
- `[late, qualifies_chased] -> chased`
- `[late, otherwise] -> late`

### Aus `chased`

- `[chased, new_cycle_detected] -> watch`
- `[chased, otherwise] -> chased`

### Aus `rejected`

- `[rejected, new_cycle_detected] -> watch`
- `[rejected, otherwise] -> rejected`


### Implementierungshinweis zu `market_phase = none`
Die verkürzte Frühfassung `phase_none -> rejected` wird in der finalen v2.1-Implementierung **nicht** mehr allgemein verwendet.

Stattdessen gilt:
- `market_phase = none` **ohne** zuvor aktiven/verfolgten Setup-Zyklus
  - führt zu **keiner Aufnahme** in die aktive State Machine
- `market_phase = none` **nach** zuvor aktivem/verfolgtem Setup-Zyklus
  - läuft über Abschnitt 5 als `structural_invalidation`
  - und damit deterministisch nach `rejected`

---

## 9.3 No-Change-Fälle
No-Change ist explizit erlaubt in:
- `watch -> watch`
- `early_ready -> early_ready`
- `confirmed_ready -> confirmed_ready`
- `late -> late`
- `chased -> chased`
- `rejected -> rejected`

Wenn keine höher priorisierte Transition greift, bleibt der Zustand unverändert.

---

# 10. Deterministische Trigger-Definitionen

## 10.1 `qualifies_early_ready`
True, wenn:
- alle allgemeinen und phasenspezifischen Early-Bedingungen aus 6.2 erfüllt

## 10.2 `qualifies_confirmed_ready`
True, wenn:
- alle allgemeinen und phasenspezifischen Confirmed-Bedingungen aus 6.3 erfüllt

## 10.3 `qualifies_late`
True, wenn:
- Late-Trigger aus 6.4 erfüllt

`timing_invalidation = true` verhindert `late` **nicht** grundsätzlich, sondern markiert nur den oberen Rand der Alterungsskala.  
Da `chased` in der Prüfreihenfolge vor `late` kommt, gewinnt bei extremer Alterung automatisch `chased`.

## 10.4 `qualifies_chased`
True, wenn:
- Chased-Trigger aus 6.5 erfüllt

## 10.5 `loses_early_but_phase_intact`
True, wenn:
- aktueller State = `early_ready`
- `qualifies_early_ready = false`
- `market_phase != none`
- `structural_invalidation = false`

## 10.6 `loses_confirmed_but_phase_intact`
True, wenn:
- aktueller State = `confirmed_ready`
- `qualifies_confirmed_ready = false`
- `market_phase != none`
- `structural_invalidation = false`

## 10.7 `phase_none_without_prior_active_cycle`
True, wenn:
- `market_phase = none`
- und der Coin im aktuellen oder zuletzt bekannten Setup-Kontext noch nie in einem aktiven positiven State war:
  - `watch`
  - `early_ready`
  - `confirmed_ready`
  - `late`

Konsequenz:
- der Coin wird nicht in einen aktiven State aufgenommen
- dies ist **keine** reguläre Transition nach `rejected`
- `rejected` bleibt für ehemals aktive bzw. bereits verfolgte Setups reserviert

---

# 11. Output-Felder der State Machine

Mindestens auszugeben:

- `state_machine_state`
- `state_confidence`
- `state_transition_reason`
- `setup_cycle_id`

Zusätzlich:
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`

Hilfreich für Debugging:
- `structural_invalidation`
- `timing_invalidation`
- `qualifies_early_ready`
- `qualifies_confirmed_ready`
- `qualifies_late`
- `qualifies_chased`

---

# 12. Kalibrierungshinweise für Abschnitt 4

## 12.1 Early- und Confirmed-Schwellen
Die Default-Schwellen sind Startwerte und müssen gegen reale Top-Kandidaten geprüft werden.

## 12.2 Late-/Chased-Schwellen
Wenn zu viele Coins zu früh in `late` oder `chased` kippen:
- State-Freshness-Schwellen anheben
- oder Early-/Confirmed-Idealzonen anpassen

## 12.3 Daily-only-Confirmed
Die Daily-only-Confirmed-Regel ist bewusst restriktiv.
Wenn sie in der Praxis zu viele brauchbare Mid-Cap-Setups verliert:
- `daily_only_min_phase_confidence` empirisch prüfen

---

# 13. Zusammenfassung Abschnitt 4

Mit Abschnitt 4 ist die State Machine formal definiert:

- Zustände:
  - `watch`
  - `early_ready`
  - `confirmed_ready`
  - `late`
  - `chased`
  - `rejected`

Zusätzlich festgelegt:
- state-basierte Frische
- explizite Definition der state-internen Distanzfelder
- state confidence
- harte Invarianten
- bewusste direkte Transition `watch -> confirmed_ready`
- direkte Sprünge nach `chased` bei starkem Aging
- strukturelle und timingbezogene Invalidation
- Setup-Cycle-Logik
- vollständige Transition-Tabelle
- No-change-Fälle
- deterministische Triggerdefinitionen

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 5 – Invalidation + Setup Cycle im Detail**:
- strukturelle Invalidation verfeinern
- timingbezogene Invalidation konsolidieren
- Zyklus-Reset-Logik explizit vertiefen
