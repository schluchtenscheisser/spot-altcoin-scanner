> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-28 Kalibrierte Schwellenwerte als Shadow-Empfehlung einführen (ohne harte Live-Steuerung)

## Context / Source
- Die aktuelle alleinige Referenz sieht kalibrierte Schwellenwerte erst **nach** mindestens 6–8 Wochen stabiler Live-Datensammlung vor.
- PR-27 bereitet die Shadow-Calibration-Infrastruktur vor, ohne produktive Decision-Logik zu verändern.
- Dieses Ticket führt datenbasierte, empirisch validierte Schwellenwerte oder Shadow-Scores als **vorbereitende / optionale Empfehlungsebene** ein, ohne automatisch die produktive Live-Decision zu überschreiben.
- Die verbindlichen Ticket-Regeln gelten vollständig, insbesondere:
  - Canonical first
  - keine zweite fachliche Wahrheit
  - Missing vs Invalid trennen
  - `NaN` / `inf` explizit behandeln
  - `null`-Semantik explizit
  - Determinismus
  - keine stillen Feature-Fallbacks

## Goal
Kalibrierte Schwellenwerte bzw. Shadow-Scores technisch nutzbar machen, sodass:

- datenbasierte Empfehlungen für Thresholds aus ausreichend gelabelten Daten ableitbar sind
- optional Shadow-Scores wie `p_hit10_5d_est` / `p_hit20_5d_est` berechnet oder ausgegeben werden können
- diese Werte **noch nicht automatisch** produktive ENTER/WAIT/NO_TRADE-Entscheidungen steuern, sofern kein expliziter und gültiger Umschaltmechanismus vorgesehen ist
- produktive Heuristik-Schwellen bis zur bewusst aktivierten Umschaltung unverändert bleiben

## Scope
- Auswertung / Ableitung kalibrierter Schwellenwerte aus ausreichend gelabelten historischen Daten
- optionale Berechnung / Ausgabe von Shadow-Scores wie:
  - `p_hit10_5d_est`
  - `p_hit20_5d_est`
  oder gleichwertiger kalibrierter Shadow-Metriken
- klar getrennte Shadow-/Analyse-Ebene für:
  - empirisch empfohlene `min_score_for_enter`
  - empirisch empfohlene `min_rr_to_tp10`
  - ggf. weitere empirisch empfohlene Decision-Schwellen
- Tests für:
  - ausreichende vs unzureichende Datengrundlage
  - numerische Robustheit
  - deterministische Ergebnisse
  - keine stille Live-Umschaltung

## Out of Scope
- Keine automatische Aktivierung produktiver Live-Thresholds ohne expliziten, gültigen Umschaltmechanismus
- Kein stilles Überschreiben von `decision`-Config im Live-Scanner
- Keine Portfolio-/Exit-/Hold-Logik
- Keine In-sample-only-Optimierung ohne Walk-forward-/Out-of-sample-Absicherung
- Keine zweite fachliche SoT neben den kanonischen produktiven Outputs
- Keine erzwungene Einführung kalibrierter Wahrscheinlichkeiten in Phase 1, wenn die Datengrundlage unzureichend ist

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- relevante Canonical Docs zu Pipeline / Decision / Output / Eval
- aktuelle alleinige Referenz für EPIC 12 / PR-28
- vorbereitende Shadow-Calibration-Contracts aus PR-27

## Proposed change (high-level)
Before:
- Es gibt vorbereitende Shadow-Calibration-Infrastruktur, aber noch keine explizit abgeleiteten, datenbasierten Schwellenwerte oder Shadow-Probabilities.
- ENTER basiert weiterhin nur auf manuell gesetzten heuristischen Config-Schwellen.

After:
- Aus ausreichend gelabelten Daten können empirisch validierte Schwellenwerte oder Shadow-Scores abgeleitet werden.
- Diese Ergebnisse werden als Shadow-/Analyse-Ausgabe klar von produktiver Live-Decision getrennt.
- Wenn Canonical/Config später eine explizite Aktivierung erlaubt, muss diese explizit, zentral und testbar sein; ohne diese Aktivierung bleiben produktive Heuristik-Schwellen unverändert.
- Die Auswertung ist walk-forward-fähig und vermeidet reine in-sample-only Optimierung.

Edge cases:
- unzureichende Datengrundlage
- stark unausgewogene Zielverteilungen
- fehlende Label-Felder
- `NaN`, `inf`, `-inf` in Features / Labels / Shadow-Scores
- nicht monotone / instabile Threshold-Empfehlungen
- widersprüchliche Shadow-Empfehlungen vs heuristische Live-Schwellen
- explizite Aktivierung verlangt, aber keine belastbare Kalibrierungsbasis vorhanden

Backward compatibility impact:
- Ohne explizite gültige Umschaltung bleibt produktive Live-Decision unverändert.
- Shadow-Empfehlungen erweitern Analyse- und Migrationsfähigkeit, ohne still die bestehende Fachlogik zu überschreiben.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Dieses Ticket darf produktive Live-Decision nur dann beeinflussen, wenn die alleinige Referenz und Canonical dafür einen expliziten, gültigen Mechanismus vorsehen. Andernfalls bleibt es Shadow-/Analyse-Ebene.
- **Keine stille Umschaltung:** Kalibrierte Schwellen dürfen produktive Heuristik-Schwellen nicht heimlich ersetzen.
- **Keine zweite Wahrheit:** Shadow-Scores / empfohlene Schwellen sind Analyse-/Empfehlungsebene, nicht automatisch die neue produktive Fachwahrheit.
- **Walk-forward statt in-sample-only:** Wenn Schwellen aus Daten abgeleitet werden, muss das Verfahren gegen reine In-sample-Optimierung abgesichert sein.
- **Missing vs invalid trennen:** unzureichende Datengrundlage, fehlende Labels und formal ungültige Datenzustände sind getrennt zu behandeln.
- **`NaN` / `inf` explizit:** Nicht-finite Werte in Features, Labels oder Ausgabemetriken dürfen nicht still in scheinbar gültige Empfehlungen diffundieren.
- **Nullability explizit:** Wenn Shadow-Scores oder empfohlene Schwellen mangels belastbarer Daten nicht ableitbar sind, bleiben sie `null`/nicht auswertbar und kollabieren nicht zu `0`, `false` oder Default-Schwellen.
- **Determinismus:** Gleiche Eingabedaten + gleiche Kalibrierungsregeln => gleiche Shadow-Ergebnisse.
- **Keine stillen Defaults für Datenmenge:** Mindestanforderungen an Datengrundlage müssen explizit konfiguriert oder kanonisch definiert sein.
- **Partielle Nested-Overrides explizit:** Wenn es verschachtelte Calibration-/Shadow-Config-Blöcke gibt, muss das Ticket bzw. die Implementierung klar festlegen, ob Overrides **merge**n oder **vollständig ersetzen**.
- **Keine Live-Threshold-Änderung ohne Tests:** Wenn optional eine explizite Aktivierung erlaubt ist, muss sie separat und vollständig abgesichert sein.

## Implementation Notes (optional but useful)
- Wahrscheinlich betroffen:
  - vorbereitende Shadow-Calibration-/Analyse-Module aus PR-27
  - Eval-/Label-Export-Daten als Input
  - ggf. Analyse-Outputs / Tooling
- Empfohlene Schwellen können z. B. auf Basis von:
  - hit-rate nach Score-Buckets
  - MAE-/MFE-Verteilungen
  - RR-Verteilungen
  - Walk-forward-Slices
  abgeleitet werden.
- Wenn `p_hit10_5d_est` / `p_hit20_5d_est` erzeugt werden, müssen deren Semantik, Datenbasis und Nullable-Verhalten explizit sein.
- Falls noch keine produktive Aktivierung erfolgen soll, Output klar als `shadow_*`, `recommended_*` oder gleichwertig gekennzeichnet halten.

## Acceptance Criteria (deterministic)
1) Es existiert eine technische Möglichkeit, datenbasierte empfohlene Schwellenwerte oder Shadow-Scores aus ausreichend gelabelten Daten abzuleiten.

2) Die abgeleiteten Werte bleiben klar von produktiven Live-Schwellen getrennt, sofern keine explizite und gültige Aktivierung vorgesehen ist.

3) Unzureichende Datengrundlage wird explizit und testbar behandelt; es gibt keinen stillen Fallback auf scheinbar valide kalibrierte Werte.

4) Nicht-finite numerische Werte (`NaN`, `inf`, `-inf`) in Features, Labels oder Zwischenwerten werden explizit behandelt und diffundieren nicht still in Shadow-Ergebnisse.

5) Wenn Shadow-Scores wie `p_hit10_5d_est` / `p_hit20_5d_est` erzeugt werden, ist ihre Semantik klar, ihre Ausgabe deterministisch und ihre Nullability explizit behandelt.

6) Die Kalibrierungslogik ist walk-forward-fähig oder anderweitig explizit gegen reine in-sample-only Optimierung abgesichert.

7) Gleiche Eingabedaten + gleiche Regeln => identische kalibrierte Empfehlungen / Shadow-Ergebnisse.

8) Tests belegen explizit, dass produktive Live-Thresholds ohne gültige explizite Aktivierung unverändert bleiben.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (fehlende Kalibrierungs-/Shadow-Keys nutzen zentrale Defaults oder brechen klar, wenn sie required sind)
- **Config Invalid Value Handling:** ✅ (ungültige Kalibrierungsparameter oder widersprüchliche Shadow-/Live-Umschaltzustände => klarer Fehler)
- **Nullability / kein bool()-Coercion:** ✅ (nicht ableitbare Shadow-Scores / empfohlene Schwellen bleiben `null`, nicht `0`/`false`)
- **Not-evaluated vs failed getrennt:** ✅ (unzureichende Kalibrierungsbasis ≠ negative Kalibrierungsempfehlung)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (bei invalidem Kalibrierungszustand kein halb-konsistenter Empfehlungssatz)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (Shadow-/Analyse-Artefakte konfliktfrei und deterministisch)
- **Deterministische Sortierung / Tie-breaker:** ✅ (falls Empfehlungen / Buckets / Outputs sortiert werden, explizite stabile Reihenfolge)

## Tests (required if logic changes)
- Unit:
  - ausreichende Datengrundlage erzeugt deterministische empfohlene Schwellen / Shadow-Scores
  - unzureichende Datengrundlage wird explizit behandelt
  - `NaN`/`inf` in Kalibrierungsdaten werden explizit behandelt
  - `null`-bleibt-`null` für nicht ableitbare Shadow-Werte
  - ungültige Kalibrierungs-Config erzeugt klaren Fehler
  - produktive Live-Schwellen bleiben ohne explizite Aktivierung unverändert

- Integration:
  - Walk-forward-/Out-of-sample-fähige Shadow-Auswertung auf kleinem Fixture-Datensatz
  - gleicher Input + gleiche Regeln => identische Shadow-Ergebnisse
  - keine stille Änderung produktiver Decision-Thresholds
  - falls optionale Aktivierung existiert: nur mit explizit gültigem Schalter und vollständiger Testabdeckung

- Golden fixture / verification:
  - nur dort Golden-/Fixture-Updates, wo neue Shadow-/Empfehlungsartefakte bewusst eingeführt werden
  - keine kosmetischen Änderungen an produktiven Artefakten

## Constraints / Invariants (must not change)
- [ ] keine stille Live-Umschaltung auf kalibrierte Schwellen
- [ ] keine zweite fachliche SoT
- [ ] Shadow-/Empfehlungsebene bleibt klar getrennt von produktiver Decision
- [ ] unzureichende Daten führen nicht zu scheinbar validen Empfehlungen
- [ ] Walk-forward-/Anti-in-sample-only-Schutz bleibt gewahrt
- [ ] Determinismus bleibt erhalten
- [ ] keine Scope-Ausweitung in Portfolio / Exit / Hold

## Definition of Done (Codex must satisfy)
- [ ] kalibrierte Empfehlungen / Shadow-Scores gemäß Acceptance Criteria implementiert
- [ ] Tests für ausreichende/unzureichende Daten, `NaN`/`inf`, Nullability und Live-Unverändertheit vorhanden
- [ ] keine stille produktive Schwellenänderung eingeführt
- [ ] Walk-forward-/Anti-in-sample-only-Anforderung sichtbar berücksichtigt
- [ ] PR erstellt: genau 1 Ticket → 1 PR
- [ ] Ticket nach PR-Erstellung gemäß Workflow verschoben

## Metadata (optional)
```yaml
created_utc: "2026-03-08T00:00:00Z"
priority: P0
type: feature
owner: codex
related_issues: []
```
