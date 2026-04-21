> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

## Title
[P0] PR-18 `trade_candidates` als kanonisches Output-Objekt (JSON) einführen

## Context / Source
- Die aktuelle alleinige Referenz verlangt in Epic 9 eine einheitliche Output-SoT für Trading-Kandidaten.
- Nach Decision Layer und BTC-Regime müssen die Kandidaten in einer einzigen kanonischen JSON-Struktur ausgegeben werden.
- Diese Struktur ist die fachliche Wahrheit für spätere Renderer (Markdown / Excel) und darf keine format-spezifischen Abweichungen zulassen.
- Das Ticket ist nach Canonical, Template und Master-Checkliste formuliert; insbesondere sind Missing-vs-Invalid, Nullability, Determinismus und Score-Rollentrennung explizit.

## Goal
`scanner/pipeline/output.py` erzeugt ein kanonisches JSON-Output-Objekt `trade_candidates`, das:
- alle Phase-1-entscheidungsrelevanten Felder pro Kandidat enthält,
- maschinenlesbar und stabil ist,
- sortiert und deterministisch ist,
- `trade_candidates` klar von technischem Run-Manifest trennt,
- spätere Renderer ohne zweite Wahrheit bedienen kann.

## Scope
- `scanner/pipeline/output.py`
- ggf. enge, direkte Anpassungen an output-nahe Hilfsfunktionen/TypedDicts/Dataclasses
- ggf. kleine Anpassungen in `scanner/pipeline/__init__.py`, soweit nötig, um die neue SoT sauber zu übergeben
- output-nahe Tests unter `tests/`

## Out of Scope
- Kein Run Manifest (kommt in PR-19)
- Kein Markdown-Renderer (kommt in PR-20)
- Kein Excel-Renderer (kommt in PR-21)
- Keine Output-Consistency-Tests über mehrere Formate (kommt in PR-22)
- Keine neue Decision-/Risk-/Tradeability-Logik
- Keine Migration-/Feature-Flag-Logik
- Keine Änderung der fachlichen Sortiersemantik jenseits der kanonischen Output-Reihenfolge

## Canonical References (important)
- `docs/canonical/AUTHORITY.md`
- `docs/canonical/OUTPUT_SCHEMA.md`
- `docs/canonical/DECISION_LAYER.md`
- `docs/canonical/RISK_MODEL.md`
- `docs/canonical/LIQUIDITY/TRADEABILITY_GATE.md`
- `docs/canonical/PIPELINE.md`
- `docs/canonical/CHANGELOG.md`

## Proposed change (high-level)
Before:
- Candidate-Output ist noch nicht als eine einzige kanonische JSON-SoT festgezogen.
- Nachgelagerte Formate/Artefakte riskieren Drift oder implizite Parallelwahrheiten.

After:
- `output.py` erzeugt `trade_candidates` als kanonisches JSON-Objekt.
- Jeder Kandidat enthält die in der Referenz geforderten Pflichtfelder.
- Sortierung ist deterministisch:
  - primär: `ENTER` vor `WAIT` vor `NO_TRADE`
  - sekundär innerhalb `ENTER`: `global_score` absteigend
  - sekundär innerhalb `WAIT`: `global_score` absteigend
  - Tie-Breaker explizit und stabil
- `trade_candidates` enthält ausschließlich Trading-SoT; technisches Run-Metadaten gehören **nicht** in dieses Objekt.
- `tp10_price` und `tp20_price` werden als Orientierungsziele ausgegeben, ohne Exit-Logik zu implizieren.

Edge cases:
- nullable Risk-/Tradeability-Felder bleiben `null`, wenn fachlich nicht belastbar berechenbar
- `risk_acceptable` ist als bool vorgesehen; wenn Canonical/Implementierung hier nullable erfordern, Ticket stoppen statt implizit bool-casten
- Kandidat ohne optionales Kontextfeld bleibt gültig, solange Pflichtfelder korrekt gesetzt sind
- fehlende `decision_reasons` sind nicht erlaubt
- keine UNKNOWN-Kandidaten in `trade_candidates`, wenn Canonical/Pipeline sie vorher ausschließt

Backward compatibility impact:
- Output-Schema ändert sich bewusst in Richtung kanonischer SoT.
- Bestehende JSON-Konsumenten können Anpassungen benötigen.
- Alte Parallel-Outputs bleiben bis zu späteren Migrationstickets unberührt, soweit nicht direkt betroffen.

## Codex Implementation Guardrails (No-Guesswork, Pflicht bei Code-Tickets)
- **Canonical first:** Feldnamen, Feldrollen und Sortierregeln exakt nach Canonical/aktueller Referenz verwenden.
- **Eine Wahrheit:** `trade_candidates` ist die kanonische Trading-SoT; kein format-spezifischer Zusatz darf eine abweichende Trading-Wahrheit erzeugen.
- **Score-Rollen trennen:** `setup_score` = Decision-Schwelleninput; `global_score` = Priorisierung/Kontext. Nicht vermischen.
- **TP-Felder nicht überdehnen:** `tp10_price` / `tp20_price` sind Orientierungsziele, keine automatische Exit-Semantik.
- **Nullability explizit:** Nullable Felder müssen `null` bleiben können; keine implizite `bool(...)`- oder `0.0`-Koerzierung.
- **Missing vs invalid trennen:** Fehlende optionale Felder ≠ ungültige Pflichtfelder. Pflichtfelder müssen explizit validiert werden.
- **Determinismus ist Pflicht:** Identischer Input + identische Config => identische Kandidatenliste, identische Reihenfolge, identische Reasons.
- **Tie-Breaker explizit:** Wenn `global_score` gleich ist, muss ein stabiler Tie-Breaker greifen (z. B. `symbol` oder anderer kanonisch stabiler Schlüssel).
- **Kein Manifest im Kandidatenobjekt:** Technische Run-Metadaten gehören nicht in `trade_candidates`.
- **Keine zweite Wahrheit durch Legacy-Kontext:** Falls alte `global_top20` o. Ä. parallel existieren, dürfen sie nicht von `trade_candidates` als Trading-SoT abweichen.

## Implementation Notes (optional but useful)
- Prüfe bestehende Output-Pfade in `scanner/pipeline/output.py`.
- Wenn das Modul bereits JSON-nahe Strukturen baut, diese auf das kanonische Schema umbauen statt parallele neue Strukturen einzuführen.
- Nutze, wenn vorhanden, zentrale Serialisierungshilfen für Dataclasses/TypedDicts.
- Falls `canonical_schema_version` auf Kandidatenebene nicht vorgesehen ist, nicht hineinschreiben; das gehört ins spätere Manifest.
- Candidate-Rank sollte aus der final sortierten Liste abgeleitet werden und stabil sein.

## Acceptance Criteria (deterministic)
1) `scanner/pipeline/output.py` erzeugt `trade_candidates` als kanonisches JSON-Output-Objekt.

2) Jeder Kandidat in `trade_candidates` enthält mindestens die Pflichtfelder:
   - `rank`
   - `symbol`
   - `coin_name`
   - `decision`
   - `decision_reasons`
   - `entry_price_usdt`
   - `stop_price_initial`
   - `risk_pct_to_stop`
   - `tp10_price`
   - `tp20_price`
   - `rr_to_tp10`
   - `rr_to_tp20`
   - `best_setup_type`
   - `setup_subtype`
   - `setup_score`
   - `global_score`
   - `entry_ready`
   - `entry_readiness_reasons`
   - `tradeability_class`
   - `execution_mode`
   - `spread_pct`
   - `depth_bid_1pct_usd`
   - `depth_ask_1pct_usd`
   - `slippage_bps_5k`
   - `slippage_bps_20k`
   - `risk_acceptable`
   - `market_cap_usd`
   - `btc_regime`
   - `flags`

3) `trade_candidates` ist deterministisch sortiert:
   - `ENTER` vor `WAIT` vor `NO_TRADE`
   - innerhalb `ENTER`: `global_score` absteigend
   - innerhalb `WAIT`: `global_score` absteigend
   - stabiler Tie-Breaker bei Gleichstand explizit implementiert

4) `decision_reasons` und `entry_readiness_reasons` sind maschinenlesbare Listen und bei Kandidaten mit erklärungsbedürftigem Status nicht leer.

5) `tp10_price` und `tp20_price` werden als Orientierungsziele ausgegeben, ohne dass dieses PR automatische Exit-Logik einführt.

6) Nullable Felder bleiben `null`, wenn sie fachlich nicht belastbar berechnet werden können; keine stille Koerzierung zu `false`, `0`, `0.0` oder leerem String.

7) `trade_candidates` enthält kein technisches Run-Manifest und keine manifest-spezifischen Felder.

8) Identischer Input + identische Config erzeugen identische Kandidaten, identische Reihenfolge und identische Ranks.

## Default-/Edgecase-Abdeckung (Pflicht bei Code-Tickets)
- **Config Defaults (Missing key → Default):** ✅ (soweit output-relevante Flags/Sortierung/Schema-Version zentral definiert sind; fehlende optionale Kontextfelder führen nicht zu impliziten Fallback-Hacks)
- **Config Invalid Value Handling:** ✅ (ungültige output-relevante Config/Struktur erzeugt klaren Fehler statt stiller Schema-Degradation)
- **Nullability / kein bool()-Coercion:** ✅ (nullable Felder bleiben `null`; `decision` / `risk_acceptable` werden nicht aus truthiness abgeleitet)
- **Not-evaluated vs failed getrennt:** ✅ (nullable Felder und Statuspfade im Output verwischen nicht „nicht berechenbar“ mit „negativ bewertet“)
- **Strict/Preflight Atomizität (0 Partial Writes):** ✅ (wenn Output geschrieben wird: keine halbgaren JSON-Strukturen; bei Fehlern sauber abbrechen)
- **ID/Dateiname Namespace-Kollisionen (falls relevant):** ✅ (N/A für diese Stufe, solange kein manifest/dateibasierter Writer eingeführt wird)
- **Deterministische Sortierung / Tie-breaker:** ✅ (AC #3, #8)

## Tests (required if logic changes)
- Unit:
  - Kandidat wird mit vollständigem Pflichtfeldsatz serialisiert
  - nullable Felder bleiben `null` statt implizit zu `false`/`0`
  - `decision_reasons` ist Liste, nicht String
  - `entry_readiness_reasons` ist Liste, nicht String
  - Sortierung `ENTER > WAIT > NO_TRADE`
  - `global_score` sortiert absteigend innerhalb `ENTER`
  - stabiler Tie-Breaker bei Score-Gleichstand
  - `rank` entspricht finaler Sortierreihenfolge

- Integration:
  - finaler Pipeline-Output enthält `trade_candidates` mit kanonischer Struktur
  - identischer Input + identische Config => identisches JSON
  - kein Manifest-Feld in `trade_candidates`
  - keine UNKNOWN-Kandidaten in `trade_candidates`, sofern Pipeline-Contract sie vorher stoppt

- Golden fixture / verification:
  - vorhandene JSON-/Snapshot-Fixtures nur dort bewusst aktualisieren, wo die neue SoT das Schema oder die Reihenfolge kanonisch ändert
  - keine Autodocs manuell editieren

## Constraints / Invariants (must not change)
- [ ] `trade_candidates` bleibt die kanonische Trading-SoT
- [ ] `global_score` bleibt Priorisierung, nicht primäre Decision-Wahrheit
- [ ] `setup_score` bleibt Decision-Schwelleninput
- [ ] `tp10_price` / `tp20_price` bleiben Orientierungsziele
- [ ] kein Run-Manifest in `trade_candidates`
- [ ] deterministische Sortierung und Ranking
- [ ] keine Scope-Ausweitung auf Markdown/Excel/Migration

## Definition of Done (Codex must satisfy)
- [ ] `trade_candidates` gemäß Acceptance Criteria implementiert
- [ ] Tests gemäß Ticket ergänzt/aktualisiert
- [ ] Nullability / Determinismus / Score-Rollentrennung explizit abgesichert
- [ ] Keine Scope-Überschreitung in Manifest/Markdown/Excel/Migration
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
