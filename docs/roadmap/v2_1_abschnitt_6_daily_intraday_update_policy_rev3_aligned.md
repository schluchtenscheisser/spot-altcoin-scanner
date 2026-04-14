# v2.1 – Abschnitt 6: Daily vs Intraday Update Policy (überarbeitet)

Ziel dieses Abschnitts ist die **formal umsetzbare Definition** der Update- und Rechenpolitik für:

- Daily Discovery Scan
- Intraday Promotion Scan
- Cache-Verhalten
- Persistenzregeln
- Feldaktualisierung nach Frequenz

Dieser Abschnitt stellt sicher, dass die Architektur:
- **datensparsam**
- **zeitlich konsistent**
- **zyklusfrei**
- und **operativ früh genug**
arbeitet.

---

# 1. Grundprinzipien

## 1.1 Zwei Scan-Modi
Das System arbeitet in v2.1 mit genau zwei Scan-Modi:

### A) `daily_discovery_scan`
Zweck:
- breites Universum
- Eligibility
- Aufbau und Aktualisierung der strukturellen Sicht
- Watchlist-Erzeugung
- Marktphasen-Neubewertung

### B) `intraday_promotion_scan`
Zweck:
- nur reduzierte Kandidatenmenge
- frühere Erkennung von:
  - `watch -> early_ready`
  - `early_ready -> confirmed_ready`
  - `early/confirmed -> late/chased`
- deutlich geringere API- und Rechenlast als Daily

---

## 1.2 Trennung von Stabilität und Reaktionsgeschwindigkeit
Die Policy trennt bewusst:

- **langsamere, stabilere Daily-Komponenten**
- **schnellere, timing-sensitive Intraday-Komponenten**

Damit gilt:
- Marktphasen bauen primär auf Daily + 4h-Struktur
- Timing und Promotion reagieren intraday vor allem über 4h

---

## 1.3 Keine Vollneuberechnung für alles intraday
Intraday werden **nicht** alle Felder neu gerechnet.

Regel:
- 1d-nahe Felder werden gecacht
- 4h-sensitive Felder werden intraday aktualisiert
- state-interne Felder werden bei jedem Lauf aktualisiert
- teure Execution-Daten nur für reduzierte Subsets

---

# 2. Scan-Modi im Detail

# 2.1 `daily_discovery_scan`

## Zweck
Der Daily-Scan ist der **breite Hauptlauf**.

Er verarbeitet:
- das gefilterte Universum
- günstige und mittelteure Strukturfeatures
- Marktphasen
- erste State-Einschätzung
- Watch-/Early-/Confirmed-Buckets auf breiter Basis

## Mindestumfang
Der Daily-Scan soll mindestens 1x pro Kalendertag laufen.

## Typische Ausführung
- bevorzugt nach Abschluss des relevanten Daily-Bars
- Zeitzone konsistent mit Systemkonfiguration

## Operativer Fetch-Hinweis
Der Daily-Scan zieht 4h-Daten **nicht blind** für das gesamte breite Eligible-Universum.

Vor dem 4h-Fetch darf ein operativer Vorfilter eingesetzt werden:

- `pre_4h_candidate_filter`

Dieser Filter:
- ist **kein** kanonischer Phase- oder State-Entscheider
- arbeitet nur mit billigen Daten:
  - Eligibility-Meta
  - 1d-OHLCV
  - daraus ableitbaren 1d-only-Rohfeldern
- entscheidet nur:
  - welches Symbol im aktuellen Daily-Lauf zusätzlich 4h-Daten erhält

Wichtig:
- Coins, die den Filter nicht passieren, sind damit **nicht fachlich verworfen**
- sie erhalten in diesem Lauf lediglich keinen 4h-Refresh
- die konkrete Heuristik ist eine Budget-/Betriebsentscheidung und separat zu dokumentieren

---

# 2.2 `intraday_promotion_scan`

## Zweck
Der Intraday-Scan ist der **gezielte Folge-Scan**.

Er verarbeitet **nicht** das ganze Universum, sondern nur einen bereits reduzierten Pool.

## Empfohlene Frequenz
- alle 4h
oder
- alle 6h

v2.1 bevorzugt:
- **4h**

weil:
- die Architektur 4h als primären Frühindikator nutzt

## Kernaufgabe
Der Intraday-Scan soll primär State-Transitions erkennen, nicht neue Universumsentdeckungen erzwingen.

---

# 3. Universe-Selektion je Scan-Modus

# 3.1 Universe für Daily
Input-Universum:
- alle Coins, die Eligibility potenziell erfüllen können
- nach harten Billigfiltern

Typische Quellen:
- lokaler Markt-Snapshot
- Metadaten-Snapshot
- OHLCV-Snapshot
- ggf. letzte Scanner-Persistenz

---

# 3.2 Universe für Intraday
Input-Universum für Intraday ist **nicht** das gesamte Daily-Universum.

Intraday verarbeitet nur Coins, die mindestens eines erfüllen:

- `state_machine_state in {watch, early_ready, confirmed_ready, late}`
- oder `decision_bucket in {watchlist, early_candidates, confirmed_candidates, late_monitor}`
- oder `market_phase_confidence >= cfg.intraday.min_phase_confidence_for_monitoring`

### Default-Startwert
- `min_phase_confidence_for_monitoring = 55`

## Ausschluss
Coins in:
- `rejected`
- `chased`

werden intraday **nicht weiterverfolgt**, außer:
- ein neuer Zyklus könnte erkannt werden
- oder ein separater Reset-Check ist aktiviert

---

# 4. Feldklassen nach Update-Frequenz

Zur Implementierung werden Felder in vier Gruppen geteilt:

## Gruppe A – langsam / daily-only
Nur im Daily-Scan neu berechnen

## Gruppe B – 4h-sensitiv / intraday-refresh
Im Daily-Scan und Intraday-Scan neu berechnen

## Gruppe C – state-intern / immer aktualisieren
Bei jedem Lauf aktualisieren, wenn Coin im Lauf enthalten ist

## Gruppe D – execution-/orderbook-sensitiv
Nur bei Bedarf und nur für reduzierte Subsets

---

# 5. Gruppe A – Daily-only-Felder

Diese Felder werden standardmäßig **nur im Daily-Scan** neu berechnet und intraday aus Cache übernommen.

## 5.1 Daily-only Roh- und Hilfsfelder
- `close_vs_ema20_1d_pct`
- `close_vs_ema50_1d_pct`
- `ema20_slope_1d_pct_per_bar`
- `ema20_vs_ema50_1d_pct`
- `atr_pct_rank_120_1d_pct`
- `pullback_depth_vs_last_impulse_pct_1d`
- `pullback_volume_ratio_1d`
- `close_vs_rolling_high_5_1d_pct`
- `volume_1d_current_vs_median10`
- `bars_since_last_new_low_1d`
- `range_width_10bars_1d_pct`
- `close_position_in_range_10bars_1d`
- `close_above_range_mid_ratio_10bars_1d`

## 5.2 Daily-only abgeleitete Felder
- Daily-Fallback-Komponenten der Tier-1- und Tier-2-Achsen
- `data_resolution_class`
- Eligibility-nahe Daily-Metriken
- Market-Cap-/Volumen-Meta, sofern nicht separat intraday aktualisiert

## 5.3 Cache-Regel
Im Intraday-Scan gelten diese Werte als:
- `cached_daily_value`
- letzter verfügbarer Daily-Stand

---

# 6. Gruppe B – 4h-sensitive Intraday-Felder

Diese Felder werden:
- im Daily-Scan
- und im Intraday-Scan
neu berechnet.

## 6.1 4h-nahe Rohfelder
- `close_vs_ema20_4h_pct`
- `close_vs_ema50_4h_pct`
- `ema20_slope_4h_pct_per_bar`
- `ema20_vs_ema50_4h_pct`
- `close_vs_high20_4h_pct`
- `bars_above_ema20_4h`
- `bars_above_ema50_4h`
- `bars_above_high20_4h`
- `bb_width_rank_120_4h_pct`
- `range_width_12bars_4h_vs_atr1d_pct`
- `std_return_rank_12bars_4h_pct`
- `move_from_last_structural_break_pct`
- `bars_since_last_structural_break_4h`
- `dist_to_ema20_4h_pct_abs`
- `volume_quote_spike_4h`
- `volume_spike_persistence_4h`
- `volume_4h_current_vs_median10`
- `distance_to_last_structural_anchor_pct_abs`
- `distance_to_range_high_pct_abs`
- `bars_since_last_volume_shift_event`
- `bars_since_last_structural_break_event`

## 6.2 4h-nahe Tier-2-Simplified-Felder
- `bars_since_last_new_low_4h`
- `range_width_12bars_4h_pct`
- `close_position_in_range_12bars_4h`
- `close_above_range_mid_ratio_12bars_4h`
- `pullback_depth_vs_last_impulse_pct_4h`
- `pullback_volume_ratio_4h`
- `lowest_low_vs_ema20_4h_pct`
- `close_vs_rolling_high_5_4h_pct`

## 6.3 4h-nahe Break-/Anchor-Felder
- `fixed_structural_break_anchor_4h`
- `break_close_4h`
- `cycle_end_bar_index`-bezogene 4h-Counts

---

# 7. Gruppe C – State-interne Felder

Diese Felder werden **bei jedem Lauf** aktualisiert, wenn der Coin im Lauf enthalten ist.

## 7.1 Persistente State-Felder
- `state_machine_state`
- `state_confidence`
- `state_transition_reason`
- `setup_cycle_id`

## 7.2 State-Alter
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`

## 7.3 Entry-Referenzen
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`

## 7.4 State-basierte Frische
- `distance_from_ideal_entry_after_early`
- `distance_from_ideal_entry_after_confirmed`
- `freshness_distance_state_early`
- `freshness_distance_state_confirmed`

## 7.5 Invalidation-/Cycle-Felder
- `structural_invalidation`
- `structural_invalidation_reason`
- `timing_invalidation`
- `timing_invalidation_reason`
- `new_cycle_detected`
- `cycle_end_timestamp`
- `bars_since_cycle_end`

---

# 8. Gruppe D – Execution-/Orderbook-Felder

Diese Felder werden **nicht automatisch** in jedem Daily- oder Intraday-Lauf für alle Coins berechnet.

Sie werden nur für reduzierte Subsets gezogen.

## 8.1 Typische Felder
- Spread
- Orderbuch-Tiefe
- Slippage
- Execution Grade
- Depth-Imbalance
- trancheability / direct_ok / marginal etc.

## 8.2 Standardregel
Execution-Daten werden nur für Coins abgefragt, die mindestens eines erfüllen:

- `state_machine_state in {early_ready, confirmed_ready, late}`
- oder `market_phase_confidence >= cfg.execution.min_phase_confidence`
- oder `decision_bucket` liegt in aktiv beobachteten Buckets

### Default
- `min_phase_confidence = 60`

## 8.3 Cache-Regel für Execution
Execution-Daten werden **nicht scanübergreifend gecacht** für Decision-Zwecke.

Regel:
- Execution-Felder müssen in jedem Lauf, in dem sie für Ranking/Decision benötigt werden, **frisch abgefragt** werden
- stale Execution-Daten aus früheren Läufen dürfen **nicht** als gültige Entscheidungsbasis wiederverwendet werden

Kurzlebige In-Memory-Nutzung **innerhalb desselben Laufs** ist zulässig.

---

# 9. Cache-Regeln

# 9.1 Daily Cache
Alle Daily-only-Felder werden pro Symbol mit speichern:

- `daily_cache_timestamp`
- `daily_cache_bar_id`

Intraday darf diese Felder wiederverwenden, solange:
- kein neuer Daily-Bar abgeschlossen wurde

---

# 9.2 4h Cache
4h-sensitive Felder werden pro Symbol mit speichern:

- `intraday_cache_timestamp`
- `intraday_cache_bar_id`

Regel:
- wenn kein neuer 4h-Bar seit letztem Scan geschlossen hat:
  - 4h-Felder können aus Cache übernommen werden
- wenn neuer 4h-Bar vorhanden:
  - 4h-Felder neu berechnen

---

## 9.3 State Cache
State-Felder werden immer persisted und beim nächsten Lauf geladen.

Ohne State-Persistenz sind insbesondere nicht korrekt berechenbar:
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `distance_from_ideal_entry_after_*`
- T4 in Abschnitt 5 (`trend_resume` Reaccel Failure nach frühem State)

---

## 9.4 No-Backfill-Regel
Wenn einzelne Felder im Persistenzspeicher fehlen:
- keine künstliche Rückrechnung aus zukünftigen Informationen
- stattdessen:
  - Feld = `null`
  - Regel mit Persistenzabhängigkeit gilt als nicht erfüllbar

---

# 10. Welche Layer laufen in welchem Modus?

# 10.1 Daily Discovery Scan
Läuft vollständig:

1. Eligibility
2. Tier-1-Achsen
3. Tier-2-Simplified-Achsen
4. Phase-Interpreter
5. State Machine
6. optional Entry-Pattern
7. optional Execution für Shortlist
8. Decision

---

# 10.2 Intraday Promotion Scan
Läuft reduziert:

1. Load Cached Daily Values
2. Recompute 4h-sensitive Fields
3. Recompute Tier-1-/Tier-2-Komponenten mit 4h-Anteil
4. Recompute Phase-Interpreter
5. Recompute State Machine
6. optional Entry-Pattern für aktive Kandidaten
7. optional Execution für reduzierte aktive Kandidaten
8. Decision refresh

### Hinweis zur Hybrid-Bewertung
Im Intraday-Scan basiert der Phase-Interpreter bewusst auf einem **Hybrid** aus:
- gecachten 1d-Werten
- frischen 4h-Werten

Das ist beabsichtigt:
- 1d-Kontext bleibt stabil
- 4h-Änderungen treiben Promotions und Degradierungen

Konsequenz:
- Zwischen letztem Intraday-Scan und nächstem Daily-Scan kann es bei starken Tagesbewegungen zu sichtbaren Re-Ratings kommen
- der nächste Daily-Scan korrigiert dann mit vollständiger Daily-Information

Das ist **kein Fehler**, sondern Teil des Designs.

---

# 11. Aktualisierung der Achsen pro Modus

# 11.1 Tier-1-Achsen

## Daily
alle Tier-1-Achsen vollständig berechnen:
- `trend_strength`
- `reclaim_progress`
- `compression_strength`
- `expansion_progress_structural`
- `volume_regime_shift`
- `freshness_distance_structural`

## Intraday
recompute nur dort, wo 4h-sensitive Inputs enthalten sind.

Praktisch:
- `trend_strength` wird intraday teilweise neu berechnet
- `reclaim_progress` wird intraday neu berechnet
- `compression_strength` wird intraday neu berechnet
- `expansion_progress_structural` wird intraday neu berechnet
- `volume_regime_shift` wird intraday neu berechnet
- `freshness_distance_structural` wird intraday neu berechnet

Dabei:
- 1d-Komponenten kommen aus Daily-Cache
- 4h-Komponenten sind frisch

---

# 11.2 Tier-2-Simplified-Achsen

## Daily
voll berechnen, inkl. möglicher Daily-Fallbacks

## Intraday
neu berechnen, sofern 4h-Inputs vorhanden sind:
- `base_integrity_simplified`
- `pullback_quality_simplified`
- `reacceleration_strength_simplified`

Wenn 4h fehlt:
- Daily-Fallback bleibt gecacht
- Flag `reduced_resolution = true`

---

# 12. State Machine Update Policy

# 12.1 Immer neu für Intraday-Kandidaten
Wenn ein Coin im Intraday-Universum ist:
- State Machine wird immer neu ausgewertet

## 12.2 Kanonische Bar-Einheit für `bars_since_*`
Alle state-internen `bars_since_*`-Zähler werden in v2.1 **einheitlich in 4h-Bar-Einheiten** geführt.

Das gilt für:
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `bars_since_cycle_end`

### Daily-Scan
Ein neu abgeschlossener Daily-Bar entspricht:
- `delta_closed_bars_relevant = 6`

### Intraday-Scan
- `delta_closed_bars_relevant = Anzahl neu geschlossener 4h-Bars seit letztem Lauf`

### Invariante
Alle Freshness-Normalisierungen aus Abschnitt 4 und 5, die auf `bars_since_*` operieren, sind in **4h-Bar-Einheiten** kalibriert.

Damit gelten die gleichen Schwellen:
- unabhängig davon, ob ein Coin nur Daily gesehen wurde
- oder auch intraday verfolgt wird

## 12.3 Keine Promotion ohne neue Information
Wenn im Intraday-Lauf:
- kein neuer 4h-Bar
- keine neue State-relevante Information
vorliegt, dann:

- State bleibt unverändert
- nur `no_change`-Pfad

---

# 13. Decision- und Bucket-Update-Policy

## 13.1 Daily
Daily erzeugt die primäre:
- Watchlist
- Early Candidates
- Confirmed Candidates
- Late Monitor

## 13.2 Intraday
Intraday darf:
- Kandidaten zwischen Buckets verschieben
- Confirmed promoten
- Late/Chased degradieren
- Execution-Prioritäten aktualisieren

---

# 14. Default Scheduling v2.1

## 14.1 Daily
- 1x pro Tag nach Daily Close

## 14.2 Intraday
- alle 4h

## 14.3 Ressourcenarme Alternative
Falls API-/Compute-Limits eng sind:
- Intraday alle 6h
- aber dann Freshness-Schwellen in Abschnitt 4/5 prüfen und ggf. lockern

---

# 15. Persistenz-Minimum für korrekten Betrieb

Ohne diese Felder ist v2.1 nicht korrekt lauffähig:

- `state_machine_state`
- `setup_cycle_id`
- `bars_since_state_entered`
- `bars_since_early_entered`
- `bars_since_confirmed_entered`
- `close_at_early_entry_bar`
- `close_at_confirmed_entry_bar`
- `cycle_end_bar_index`
- `cycle_end_timestamp`
- `daily_cache_bar_id`
- `intraday_cache_bar_id`

Diese Felder sind **pflichtpersistente Minimalbasis**.

---

# 16. Failure-Handling

## 16.1 Fehlender Daily Cache
Wenn Daily-Cache fehlt:
- Intraday-Lauf für den Coin nicht zulässig
- Coin zurückstellen bis nächster Daily-Scan
- Flag:
  - `intraday_skipped_missing_daily_cache = true`

## 16.2 Fehlender State Cache
Wenn State-Cache fehlt:
- Coin darf weiterhin Daily neu bewertet werden
- state-history-abhängige Regeln gelten als nicht erfüllbar
- neuer Coin startet in:
  - `watch`
  - sofern positive Phase vorliegt

## 16.3 Fehlender 4h-Refresh
Wenn 4h-Daten im Intraday-Lauf nicht aktualisiert werden können:
- letzter 4h-Cache darf nur verwendet werden, wenn kein neuer 4h-Bar geschlossen wurde
- sonst:
  - Intraday-State-Update für diesen Coin aussetzen
  - Flag:
    - `intraday_skipped_stale_4h = true`

---

# 17. Zusammenfassung Abschnitt 6

Mit Abschnitt 6 ist formal definiert:

- Daily vs Intraday Scan
- Universe-Selektion je Scan
- Feldklassen nach Update-Frequenz
- Cache-Regeln
- Persistenz-Minimum
- Layer-Ausführung je Modus
- State-Update-Policy
- Failure-Handling

Zusätzlich festgelegt:
- Daily berechnet breit und stabil
- Intraday promotet gezielt und reaktiv
- 1d wird gecacht, 4h wird intraday frisch gezogen
- State-Felder müssen persistent geführt werden
- alle `bars_since_*` laufen in kanonischen 4h-Bar-Einheiten
- Execution-Daten werden für Entscheidungen nicht scanübergreifend gecacht
- Intraday-Phase-Bewertung nutzt bewusst Hybrid aus Daily-Cache und frischem 4h

## Nächster Schritt in v2.1
Als Nächstes folgt **Abschnitt 7 – Entry-Pattern-Auflösung + Decision Buckets**:
- Entry-Pattern je Marktphase
- Entscheidung nach State + Execution
- Ausgabe-Buckets
- Priorität und Ranking
