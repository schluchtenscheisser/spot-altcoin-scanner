# v2.1 – Abschnitt 7: Entry-Pattern-Auflösung + Decision Buckets (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Definition** von:

- Entry-Pattern-Auflösung je Marktphase
- Decision Buckets
- Priorität und Ranking
- Zusammenspiel von:
  - Marktphase
  - State Machine
  - Execution
  - Entscheidungsausgabe

Dieser Abschnitt liegt **nach**:
- Phase-Interpreter
- State Machine
- optional Execution-Layer

Er bildet die Brücke zwischen:
- struktureller Klassifikation
und
- operativ nutzbarer Scanner-Ausgabe

---

# 1. Grundprinzipien

## 1.1 Rolle des Entry-Pattern-Layers
Der Entry-Pattern-Layer beantwortet **nicht**:

- ob ein Coin strukturell interessant ist
- ob er früh, bestätigt oder zu spät ist

Diese Fragen sind bereits beantwortet durch:
- Phase-Interpreter
- State Machine

Der Entry-Pattern-Layer beantwortet stattdessen:

- **welches konkrete Muster** innerhalb der aktuellen Marktphase am besten passt
- wie dieses Muster benannt und beschrieben wird
- wie es in die finale Decision-Ausgabe einfließt

---

## 1.2 Rolle der Decision Buckets
Decision Buckets gruppieren Coins in operative Ausgabeklassen, z. B.:

- `watchlist`
- `early_candidates`
- `confirmed_candidates`
- `late_monitor`
- `discarded`

Buckets sind:
- **keine Marktphasen**
- **keine States**
- **keine Entry-Pattern**

Sie sind das Endprodukt für:
- UI
- Reporting
- Ranking
- Follow-up-Scans
- Execution-Priorisierung

---

## 1.3 Trennung der Ebenen
Zur Klarstellung:

### Marktphase
- struktureller Zustand des Coins

### State
- Reifegrad / Timing-Zustand

### Entry Pattern
- konkreter Auslöser / Modus des potenziellen Einstiegs

### Execution
- Umsetzbarkeit auf MEXC für Zielvolumen

### Decision Bucket
- operative Endkategorie im Scanner-Output

---

# 2. Inputs für Abschnitt 7

## 2.1 Aus vorherigen Layern
- `market_phase`
- `market_phase_confidence`
- `market_phase_blended`
- `state_machine_state`
- `state_confidence`
- alle Tier-1-Achsen
- alle Tier-2-Simplified-Achsen
- `structural_invalidation`
- `timing_invalidation`

## 2.2 Optional aus Execution-Layer
- `execution_status`
- `execution_grade`
- `execution_pass`
- `execution_reason`

Wenn Execution im aktuellen Lauf noch nicht vorliegt:
- Abschnitt 7 darf trotzdem ein vorläufiges Bucket bilden
- aber mit reduziertem Finalitätsgrad

---

# 3. Entry-Pattern-Katalog v2.1

Für v2.1 sind die Entry-Pattern bewusst begrenzt und phasenspezifisch.

## 3.1 Pattern für `pressure_build`
- `range_reclaim`
- `breakout`
- `break_and_hold`

## 3.2 Pattern für `trend_resume`
- `shallow_pullback`
- `resume_reclaim`
- `continuation_breakout`

## 3.3 Pattern für `transition_reclaim`
- `ema_reclaim`
- `base_reclaim`
- `early_reversal_break`

## 3.4 Fallback
Wenn kein Pattern sauber auflösbar ist:
- `entry_pattern = none`

Das ist erlaubt, auch wenn:
- Marktphase gültig
- State aktiv
ist.

---

# 4. Entry-Pattern-Auflösung je Marktphase

Die Pattern-Auflösung erfolgt **deterministisch** und immer **innerhalb** der bereits bestimmten Marktphase.

Regel:
- zuerst Marktphase
- dann Pattern-Auflösung nur innerhalb dieser Phase

Keine kreuzweise Auflösung:
- ein `pressure_build`-Coin bekommt kein `shallow_pullback`

---

# 5. Entry-Pattern für `pressure_build`

## 5.1 Kandidaten-Inputs
- `reclaim_progress`
- `compression_strength`
- `volume_regime_shift`
- `expansion_progress_structural`
- `freshness_distance_structural`
- `base_integrity_simplified`

## 5.2 Pattern: `range_reclaim`
Ein `pressure_build`-Coin erhält `range_reclaim`, wenn:

- `reclaim_progress >= cfg.pattern.pressure_build.range_reclaim.min_reclaim`
- `compression_strength >= cfg.pattern.pressure_build.range_reclaim.min_compression`
- `freshness_distance_structural <= cfg.pattern.pressure_build.range_reclaim.max_freshness`

Defaults:
- `min_reclaim = 45`
- `min_compression = 55`
- `max_freshness = 60`

### Score
- `0.45` `reclaim_progress`
- `0.30` `compression_strength`
- `0.25` `(100 - freshness_distance_structural)`

---

## 5.3 Pattern: `breakout`
Ein `pressure_build`-Coin erhält `breakout`, wenn:

- `expansion_progress_structural >= cfg.pattern.pressure_build.breakout.min_expansion`
- `volume_regime_shift >= cfg.pattern.pressure_build.breakout.min_volume_shift`
- `freshness_distance_structural <= cfg.pattern.pressure_build.breakout.max_freshness`

Defaults:
- `min_expansion = 35`
- `min_volume_shift = 55`
- `max_freshness = 65`

### Breakout-Expansions-Fit
Für `breakout` wird **nicht** monotones Mehr an Expansion belohnt.  
Stattdessen wird eine **moderate, frische Expansionszone** bevorzugt.

Definition:
- `breakout_expansion_fit = clamp(100 - abs(expansion_progress_structural - cfg.pattern.pressure_build.breakout.target_expansion), 0, 100)`

Default:
- `target_expansion = 40`

### Score
- `0.40` `breakout_expansion_fit`
- `0.35` `volume_regime_shift`
- `0.25` `(100 - freshness_distance_structural)`

Damit gilt:
- zu wenig Expansion = Break noch nicht sauber da
- moderate Expansion = optimal
- zu viel Expansion = bereits gelaufen

---

## 5.4 Pattern: `break_and_hold`
Ein `pressure_build`-Coin erhält `break_and_hold`, wenn:

- `reclaim_progress >= cfg.pattern.pressure_build.break_and_hold.min_reclaim`
- `expansion_progress_structural` liegt in einem moderaten Bereich
- `base_integrity_simplified >= cfg.pattern.pressure_build.break_and_hold.min_base_integrity`

Defaults:
- `min_reclaim = 55`
- `min_base_integrity = 45`
- moderater Expansionsbereich:
  - `30 <= expansion_progress_structural <= 65`

### Score
- `0.35` `reclaim_progress`
- `0.25` `base_integrity_simplified`
- `0.20` `volume_regime_shift`
- `0.20` `clamp(100 - abs(expansion_progress_structural - 45), 0, 100)`

---

# 6. Entry-Pattern für `trend_resume`

## 6.1 Kandidaten-Inputs
- `trend_strength`
- `reclaim_progress`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`
- `freshness_distance_structural`
- `expansion_progress_structural`

## 6.2 Pattern: `shallow_pullback`
Ein `trend_resume`-Coin erhält `shallow_pullback`, wenn:

- `pullback_quality_simplified >= cfg.pattern.trend_resume.shallow_pullback.min_pullback_quality`
- `trend_strength >= cfg.pattern.trend_resume.shallow_pullback.min_trend`
- `freshness_distance_structural <= cfg.pattern.trend_resume.shallow_pullback.max_freshness`

Defaults:
- `min_pullback_quality = 55`
- `min_trend = 55`
- `max_freshness = 65`

### Score
- `0.40` `pullback_quality_simplified`
- `0.30` `trend_strength`
- `0.30` `(100 - freshness_distance_structural)`

---

## 6.3 Pattern: `resume_reclaim`
Ein `trend_resume`-Coin erhält `resume_reclaim`, wenn:

- `reclaim_progress >= cfg.pattern.trend_resume.resume_reclaim.min_reclaim`
- `reacceleration_strength_simplified >= cfg.pattern.trend_resume.resume_reclaim.min_reaccel`
- `freshness_distance_structural <= cfg.pattern.trend_resume.resume_reclaim.max_freshness`

Defaults:
- `min_reclaim = 50`
- `min_reaccel = 50`
- `max_freshness = 60`

### Score
- `0.35` `reclaim_progress`
- `0.35` `reacceleration_strength_simplified`
- `0.30` `(100 - freshness_distance_structural)`

---

## 6.4 Pattern: `continuation_breakout`
Ein `trend_resume`-Coin erhält `continuation_breakout`, wenn:

- `trend_strength >= cfg.pattern.trend_resume.continuation_breakout.min_trend`
- `reacceleration_strength_simplified >= cfg.pattern.trend_resume.continuation_breakout.min_reaccel`
- `expansion_progress_structural` noch nicht zu hoch

Defaults:
- `min_trend = 60`
- `min_reaccel = 55`
- `max_expansion = 70`

### Score
- `0.35` `trend_strength`
- `0.35` `reacceleration_strength_simplified`
- `0.30` `(100 - expansion_progress_structural)`

---

# 7. Entry-Pattern für `transition_reclaim`

## 7.1 Kandidaten-Inputs
- `reclaim_progress`
- `trend_strength`
- `base_integrity_simplified`
- `volume_regime_shift`
- `freshness_distance_structural`

## 7.2 Pattern: `ema_reclaim`
Ein `transition_reclaim`-Coin erhält `ema_reclaim`, wenn:

- `reclaim_progress >= cfg.pattern.transition_reclaim.ema_reclaim.min_reclaim`
- `trend_strength >= cfg.pattern.transition_reclaim.ema_reclaim.min_trend`
- `freshness_distance_structural <= cfg.pattern.transition_reclaim.ema_reclaim.max_freshness`

Defaults:
- `min_reclaim = 45`
- `min_trend = 40`
- `max_freshness = 65`

### Score
- `0.45` `reclaim_progress`
- `0.25` `trend_strength`
- `0.30` `(100 - freshness_distance_structural)`

---

## 7.3 Pattern: `base_reclaim`
Ein `transition_reclaim`-Coin erhält `base_reclaim`, wenn:

- `base_integrity_simplified >= cfg.pattern.transition_reclaim.base_reclaim.min_base_integrity`
- `reclaim_progress >= cfg.pattern.transition_reclaim.base_reclaim.min_reclaim`

Defaults:
- `min_base_integrity = 45`
- `min_reclaim = 45`

### Score
- `0.40` `base_integrity_simplified`
- `0.35` `reclaim_progress`
- `0.25` `volume_regime_shift`

---

## 7.4 Pattern: `early_reversal_break`
Ein `transition_reclaim`-Coin erhält `early_reversal_break`, wenn:

- `reclaim_progress >= cfg.pattern.transition_reclaim.early_reversal_break.min_reclaim`
- `volume_regime_shift >= cfg.pattern.transition_reclaim.early_reversal_break.min_volume_shift`
- `freshness_distance_structural <= cfg.pattern.transition_reclaim.early_reversal_break.max_freshness`

Defaults:
- `min_reclaim = 50`
- `min_volume_shift = 50`
- `max_freshness = 60`

### Score
- `0.40` `reclaim_progress`
- `0.30` `volume_regime_shift`
- `0.30` `(100 - freshness_distance_structural)`

---

# 8. Pattern-Auswahlregel

## 8.1 Pattern-Scores
Für die aktuelle Marktphase werden alle zulässigen Pattern-Scores berechnet.

## 8.2 Auswahl
- `entry_pattern = argmax(pattern_scores_within_phase)`
- `entry_pattern_score = max(pattern_scores_within_phase)`

## 8.3 Kein zulässiges Pattern
Wenn kein Pattern seine Mindestbedingungen erfüllt:
- `entry_pattern = none`
- `entry_pattern_score = 0`

## 8.4 Tie-Break
Bei exakt gleichem Score mehrerer Pattern innerhalb derselben Phase gilt:

### `pressure_build`
1. `range_reclaim`
2. `break_and_hold`
3. `breakout`

### `trend_resume`
1. `resume_reclaim`
2. `shallow_pullback`
3. `continuation_breakout`

### `transition_reclaim`
1. `base_reclaim`
2. `ema_reclaim`
3. `early_reversal_break`

Begründung:
- zuerst stabilere / besser definierte Pattern
- dann aggressivere / frühere Varianten

---

# 9. Decision Buckets

Für v2.1 gibt es genau diese Buckets:

- `watchlist`
- `early_candidates`
- `confirmed_candidates`
- `late_monitor`
- `discarded`

Optional intern zusätzlich:
- `execution_pending`

Wenn Execution noch nicht vorliegt, aber strukturell bereits klar ist.

---

# 10. Bucket-Zuordnung

## 10.1 `watchlist`
Ein Coin kommt in `watchlist`, wenn mindestens eine der folgenden Bedingungen gilt:

### Watch-Zustand
- `state_machine_state = watch`
- `market_phase != none`
- `state_confidence >= cfg.bucket.watchlist.min_state_confidence`

oder

### Early ohne Pattern
- `state_machine_state = early_ready`
- `entry_pattern = none`

Begründung:
- Der Coin ist strukturell früh interessant
- aber noch nicht pattern-scharf genug für `early_candidates`

Default:
- `min_state_confidence = 50`

---

## 10.2 `early_candidates`
Ein Coin kommt in `early_candidates`, wenn:

- `state_machine_state = early_ready`
- `entry_pattern != none`
- `state_confidence >= cfg.bucket.early.min_state_confidence`

Default:
- `min_state_confidence = 60`

Wenn Execution vorliegt:
- `execution_status` darf nicht `fail` sein

---

## 10.3 `confirmed_candidates`
Ein Coin kommt in `confirmed_candidates`, wenn:

- `state_machine_state = confirmed_ready`
- `entry_pattern != none`
- `state_confidence >= cfg.bucket.confirmed.min_state_confidence`

Default:
- `min_state_confidence = 65`

Wenn Execution vorliegt:
- `execution_status` darf nicht `fail` sein

---

## 10.4 `late_monitor`
Ein Coin kommt in `late_monitor`, wenn:

- `state_machine_state in {late, chased}`
- `market_phase != none`

oder

- `state_machine_state = confirmed_ready`
- aber `execution_status = fail`

oder

- `state_machine_state = confirmed_ready`
- `entry_pattern = none`
- Reason Code:
  - `CONFIRMED_PATTERN_UNRESOLVED`

Diese Regel ist bewusst konservativ:
- `confirmed_ready` ohne tragfähiges Pattern wird **nicht** als regulärer `confirmed_candidate` ausgewiesen
- der Coin bleibt aber als beobachtbares Setup sichtbar
- deshalb `late_monitor` statt `discarded`

---

## 10.5 `discarded`
Ein Coin kommt in `discarded`, wenn mindestens eines gilt:

- `state_machine_state = rejected`
- `market_phase = none`
- `execution_status = fail` und kein Monitoring-Bucket greift
- `state_confidence < cfg.bucket.discarded.min_state_confidence`

### Default
- `min_state_confidence = 35`

### Wichtige Ausnahme
Ein Coin mit:
- `state_machine_state = early_ready`
- `entry_pattern = none`

ist **nicht** `discarded`, sondern bleibt in:
- `watchlist`

---

# 11. Optionales Bucket `execution_pending`

## Zweck
Wenn:
- Struktur, Phase, State und Pattern gut sind
- aber Execution noch nicht abgefragt wurde

dann darf intern gesetzt werden:
- `decision_bucket = execution_pending`

## Regel
Dieses Bucket ist optional und primär für:
- Pipeline-Steuerung
- API-Budget-Priorisierung
gedacht

Wichtig:
- `execution_pending` ist **kein kanonischer User-Bucket**
- für Nutzer-Output soll dieses Bucket nicht als eigene Hauptkategorie erscheinen

Für Nutzer-Output kann `execution_pending` alternativ in:
- `early_candidates`
oder
- `confirmed_candidates`
mit Flag
umgewandelt werden

---

# 12. Priority Score

Der `priority_score` ist der finale Rangwert für Sortierung innerhalb und teilweise über Buckets.

## 12.1 Inputs
- `market_phase_confidence`
- `state_confidence`
- `entry_pattern_score`
- optional `execution_grade`

## 12.2 Grundformel ohne Execution
Wenn Execution noch nicht vorliegt:

- `priority_score = 0.35 * market_phase_confidence + 0.40 * state_confidence + 0.25 * entry_pattern_score`

## 12.3 Formel mit Execution
Wenn Execution vorliegt:

- `priority_score = 0.30 * market_phase_confidence + 0.35 * state_confidence + 0.20 * entry_pattern_score + 0.15 * execution_grade`

Alle Scores in `0..100`

## 12.4 Penalty für Early ohne Pattern
Wenn:
- `state_machine_state = early_ready`
- `entry_pattern = none`
- Bucket = `watchlist`

dann optional:
- `priority_score = priority_score - cfg.priority.early_without_pattern_penalty`

Default:
- `early_without_pattern_penalty = 15`

Clamp:
- nicht unter 0

---

# 13. Definition `execution_grade`

Für v2.1 wird `execution_grade` als numerisches Mapping des `execution_status` definiert, sofern kein feinerer Execution-Score vorliegt.

## 13.1 Default-Mapping
- `direct_ok -> 100`
- `tranche_ok -> 75`
- `marginal -> 40`
- `fail -> 0`

## 13.2 Vorrang feinerer Scores
Wenn der Execution-Layer später einen feineren numerischen Score liefert:
- dieser darf das Default-Mapping ersetzen

Für v2.1 ist das obige Mapping ausreichend und verbindlich.

---

# 14. Ranking-Regeln

## 14.1 Primäre Bucket-Reihenfolge
Für die Darstellung gilt diese Prioritätsreihenfolge:

1. `confirmed_candidates`
2. `early_candidates`
3. `watchlist`
4. `late_monitor`
5. `discarded`

## 14.2 Ranking innerhalb eines Buckets
Innerhalb jedes Buckets wird sortiert nach:

1. `priority_score` absteigend
2. `state_confidence` absteigend
3. `market_phase_confidence` absteigend
4. `entry_pattern_score` absteigend
5. Symbol alphabetisch als finaler Tie-Break

---

# 15. Execution-Einfluss auf Buckets

## 15.1 Execution als Filter, nicht als Phase
Execution verändert nicht:
- Marktphase
- State
- Entry-Pattern

Execution beeinflusst nur:
- Bucket-Zuordnung
- Priority Score
- Darstellungspriorität

## 15.2 Regeln
- `execution_status = fail`
  - verhindert `early_candidates` und `confirmed_candidates`
  - verschiebt in `late_monitor` oder `discarded`

- `execution_status in {marginal, tranche_ok, direct_ok}`
  - erlaubt Kandidaten-Buckets
  - beeinflusst Priority Score

---

# 16. Pflicht-Output-Felder für Abschnitt 7

Mindestens auszugeben:

- `entry_pattern`
- `entry_pattern_score`
- `decision_bucket`
- `priority_score`

Zusätzlich sinnvoll:
- `bucket_reason_primary`
- `bucket_reason_secondary`
- `execution_required`
- `execution_pending`

---

# 17. Standard-Reason-Codes für Buckets

## 17.1 Watchlist
- `WATCH_PHASE_VALID`
- `WATCH_STATE_VALID`
- `WATCH_WAITING_FOR_PROMOTION`
- `WATCH_EARLY_NO_PATTERN`

## 17.2 Early
- `EARLY_STATE_VALID`
- `EARLY_PATTERN_VALID`
- `EARLY_EXECUTION_OK`
- `EARLY_EXECUTION_PENDING`

## 17.3 Confirmed
- `CONFIRMED_STATE_VALID`
- `CONFIRMED_PATTERN_VALID`
- `CONFIRMED_EXECUTION_OK`
- `CONFIRMED_EXECUTION_PENDING`

## 17.4 Late Monitor
- `LATE_STATE`
- `CHASED_STATE`
- `EXECUTION_FAILED_MONITOR`
- `FORMER_CANDIDATE_STALE`

## 17.5 Discarded
- `STATE_REJECTED`
- `PHASE_NONE`
- `PATTERN_NONE_CONFIRMED`
- `EXECUTION_FAILED`
- `INSUFFICIENT_CONFIDENCE`

---

# 18. Kalibrierungshinweise

## 18.1 Pattern-Schwellen
Pattern-Schwellen sollen anfangs konservativ bleiben.

Wenn zu viele Coins `entry_pattern = none` bekommen:
- Mindestschwellen leicht lockern
- aber nicht unter die Phasen-/State-Logik ziehen

## 18.2 Priority Score
Wenn Execution im Ranking zu stark oder zu schwach wirkt:
- Gewicht von `execution_grade` anpassen
- Standard bleibt bewusst moderat

## 18.3 Buckets klar halten
Buckets sollen operativ brauchbar bleiben:
- nicht zu viele Coins in `confirmed_candidates`
- `watchlist` nicht beliebig aufblasen
- `late_monitor` bewusst nachgelagert halten

---

# 19. Zusammenfassung Abschnitt 7

Mit Abschnitt 7 sind formal definiert:

- Entry-Pattern je Marktphase
- Pattern-Scores
- Pattern-Tie-Breaks
- Decision Buckets
- Bucket-Zuordnung
- Priority Score
- numerische Definition von `execution_grade`
- Ranking-Reihenfolge
- Execution-Einfluss auf finale Ausgabe

Zusätzlich festgelegt:
- `pressure_build -> breakout` bevorzugt moderate, frische Expansion statt monotones „mehr ist besser“
- `early_ready` ohne Pattern wird nicht verworfen, sondern bleibt auf der `watchlist`

Damit ist die operative Ausgabe des Scanners vollständig spezifiziert.

## Nächster Schritt in v2.1
Als Nächstes kann die Gesamtspezifikation konsolidiert werden oder — falls gewünscht — in eine technische Implementierungsplanung für das Repo überführt werden.
