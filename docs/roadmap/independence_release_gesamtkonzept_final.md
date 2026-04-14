# Independence-Release – finales Gesamtkonzept

## 1. Zielbild und Leitplanken

Die fachliche Grundlage des Independence-Release sind ausschließlich die 7 ausgearbeiteten Abschnittsdateien der bisherigen v2.1-Spezifikation. Diese 7 Dateien bleiben verbindliche Fachgrundlage für Phase, State, Invalidation, Update-Policy, Entry-Pattern und Decision Buckets. Legacy-Dokumentation ist für die Zielarchitektur nicht bindend. fileciteturn0file6 fileciteturn0file5 fileciteturn0file4 fileciteturn0file3 fileciteturn0file2 fileciteturn0file1 fileciteturn0file0

Das Independence-Release wird im **duplizierten Repo als neue Primärarchitektur** aufgebaut.  
Es gibt innerhalb dieses neuen Repos:

- keinen Shadow-Mode
- keine parallele Legacy-/Neu-Logik
- keine Dual-Outputs
- keinen Migrationspfad innerhalb desselben Codepfads

Der alte Scanner läuft separat im alten Repo weiter. Das neue Repo ist ein **Big-Bang-Neuaufbau** mit dauerhafter Zielarchitektur.

### Leitprinzipien

- keine Weiterführung der alten Score-/Ranking-/Decision-Architektur als Zielmodell
- klare Trennung zwischen:
  - Basishistorie
  - point-in-time Run-Artefakten
  - Reports
  - Evaluation
  - technischen Nebenartefakten
- alle Output-, Snapshot-, Report- und Diagnostikformate werden als **dauerhafte Zielarchitektur** definiert
- bewusst verschobene Themen werden explizit in `docs/canonical/feature_enhancements.md` gepflegt
- offene Fragen werden explizit in `docs/canonical/open_questions.md` gepflegt
- keine stillen Provisorien
- keine temporären Zwischenlösungen ohne explizite Nachverfolgung

---

## 2. Repo-Zielarchitektur

### 2.1 Empfohlene Struktur

```text
scanner/
  main.py
  config.py

  clients/
    mexc_client.py
    marketcap_client.py
    mapping.py

  universe/
    discovery.py
    eligibility.py
    market_data_budget.py

  data/
    bar_clock.py
    ohlcv_fetch.py
    cache_policy.py
    runtime_meta.py

  features/
    raw_1d.py
    raw_4h.py
    shared.py

  axes/
    normalization.py
    tier1.py
    tier2_simplified.py

  phase/
    interpreter.py

  state/
    invalidation.py
    cycle.py
    freshness.py
    machine.py
    models.py

  entry/
    patterns.py

  execution/
    adapter.py
    grading.py

  decision/
    buckets.py
    ranking.py
    reasons.py

  storage/
    sqlite.py
    repositories.py
    schema.py

  output/
    report_builder.py
    schema.py
    diagnostics.py

  runners/
    daily.py
    intraday.py

  evaluation/
    replay.py
    forward_returns.py
    dataset_export.py
    diagnostics.py

  utils/
    ...
```

### 2.2 Modulverantwortlichkeiten

#### `clients/`
Übernahmefähige Infrastruktur für:

- Exchange-Zugriff
- Market-Cap-Daten
- Symbol-Mapping

#### `universe/`
Neue explizite Schicht für das Discovery-Universum.

- `discovery.py`: baut das Rohuniversum auf
- `eligibility.py`: billige harte Vorfilter vor OHLCV
- `market_data_budget.py`: steuert gestuften Fetch für 1d, 4h und Execution

Diese Schicht ist zwingend, weil der bisherige frühe Universe-Cut fachlich nicht zur Zielarchitektur passt.

#### `data/`
- `bar_clock.py`: kanonische Zeitlogik für 1d/4h
- `ohlcv_fetch.py`: Datenbeschaffung
- `cache_policy.py`: Datenfrische und Nachladeentscheidungen
- `runtime_meta.py`: technische Laufmetadaten

#### `features/`
Reine Rohfeld-Berechnung aus 1d- und 4h-OHLCV.

- `raw_1d.py`
- `raw_4h.py`
- `shared.py`

#### `axes/`
- `normalization.py`: Normierungsfunktionen und Missing-Data-Regeln
- `tier1.py`: Tier-1-Achsen aus Abschnitt 1 fileciteturn0file6
- `tier2_simplified.py`: Tier-2-Simplified-Achsen aus Abschnitt 2 fileciteturn0file5

#### `phase/`
`interpreter.py` bestimmt:

- `market_phase`
- `market_phase_confidence`
- `market_phase_runner_up`
- `market_phase_gap`
- `market_phase_blended`

gemäß Abschnitt 3. fileciteturn0file4

#### `state/`
- `invalidation.py`: autoritativ nach Abschnitt 5, nicht nach der verkürzten Darstellung in Abschnitt 4 fileciteturn0file2 fileciteturn0file3
- `cycle.py`: `setup_cycle_id`, `new_cycle_detected`, `cycle_end_*`
- `freshness.py`: state-interne Frische
- `machine.py`: Zustandsmaschine
- `models.py`: Typed Models / Dataclasses

#### `entry/`
`patterns.py` löst Entry-Pattern innerhalb der bereits bestimmten Marktphase auf. Abschnitt 7 ist dafür maßgeblich. fileciteturn0file0

#### `execution/`
Adapter auf bestehende technische Liquiditäts-/Execution-Komponenten, aber mit neuem Zielformat:

- `execution_status`
- `execution_grade`
- `execution_pass`
- `execution_reasons`

#### `decision/`
- `buckets.py`: Bucket-Zuordnung
- `ranking.py`: `priority_score`
- `reasons.py`: stabile Reason-Codes

#### `storage/`
SQLite-basierter Persistenzlayer für:

- State
- Cycle
- Cache-Meta
- Run-Meta
- diagnostische Snapshots

#### `output/`
- `report_builder.py`: kanonische Summary-Reports
- `schema.py`: Report-Schema
- `diagnostics.py`: vollständige Symboldiagnostik

#### `runners/`
- `daily.py`: Daily Discovery Scan
- `intraday.py`: Intraday Promotion Scan

#### `evaluation/`
Separate Independence-Release-Evaluationsschicht, nicht auf alte Evaluationslogik verbiegen.

---

## 3. Was aus dem alten Repo übernommen, refactored oder verworfen wird

### 3.1 Direkt übernehmbar

- `scanner/clients/*`
- große Teile aus `scanner/utils/*`
- Teile der Datenzugriffs- und technischen Infrastruktur
- Teile von `scanner/pipeline/liquidity.py` als technische Quelle
- bestehende GitHub-Actions-Ideen für Code Map, GPT Snapshot und Script-Runner

### 3.2 Nur als strukturelle Vorlage

- bisherige canonical-Doku-Struktur, insbesondere `SCOPE.md` und `GLOSSARY.md` fileciteturn4file27 fileciteturn4file41
- bestehende Doku-Schemata
- bisherige Snapshot-/Manifest-Ideen

### 3.3 Nicht als Zielarchitektur weiterführen

- alte Scoring-Module
- altes globales Ranking
- alte `decision.py`
- altes `output.py`-Denken
- alte Business-Golden-Logik
- `docs/legacy/**`

---

## 4. Dokumentationsarchitektur

### 4.1 Zielstruktur

```text
docs/
  canonical/
    CHANGELOG.md
    SCOPE.md
    GLOSSARY.md
    ARCHITECTURE.md
    DATA_MODEL.md
    RUNTIME_AND_OPERATIONS.md
    REPORTS.md
    SNAPSHOTS.md
    TEST_STRATEGY.md
    MIGRATION_NOTES.md
    open_questions.md
    feature_enhancements.md

  code_map.md
  GPT_SNAPSHOT.md
  AGENTS.md
```

### 4.2 Klassifizierung der bisherigen Doku

#### 1:1 übernehmen

- `docs/AGENTS.md`
- `docs/code_map.md` als auto-generiertes Artefakt
- `docs/GPT_SNAPSHOT.md` als auto-generiertes Artefakt, sofern wieder erzeugt

#### Nur strukturell als Vorlage

- bisherige canonical-Dateien mit neutralem Doku-Schema
- insbesondere `SCOPE.md`, `GLOSSARY.md`

#### Verwerfen

- `docs/legacy/**`
- alte Fachlogik-Dokumente zur bisherigen Scannerarchitektur
- alte Architektur- und Decision-Dokumente, soweit sie inhaltlich an Legacy gekoppelt sind

### 4.3 Zusätzliche verbindliche Dateien

- `docs/canonical/open_questions.md`
- `docs/canonical/feature_enhancements.md`

### 4.4 Doku-Regeln

- canonical-Doku beschreibt Zielarchitektur, keine lose Notizsammlung
- bewusst verschobene Themen gehen nach `feature_enhancements.md`
- ungelöste Fragen gehen nach `open_questions.md`
- `docs/code_map.md` und `docs/GPT_SNAPSHOT.md` bleiben unterstützende Standardartefakte

---

## 5. Verzeichnisrollen und Speicherklassen

### 5.1 Verzeichnisrollen

#### `reports/`
Scanner-Ergebnisse:

- Daily-Summaries
- Run-Reports
- Index-Dateien
- reportnahe Komfortformate

#### `snapshots/`
- historische Basisdaten
- point-in-time Run-Artefakte
- technische Reproduzierbarkeitsdateien

#### `evaluation/`
- Replay
- Forward-Return-Analysen
- Kalibrierung
- experimentelle Exporte

#### `artifacts/`
- technische Nebenprodukte
- CI-/Debug-/Profiling-/Research-Artefakte

#### `scripts/`
- nur ausführbare Hilfsskripte
- keine dauerhafte Artefaktablage

### 5.2 Commit-Regeln

#### Commitbar

- Code
- canonical-Doku
- kleine Fixtures
- kleine Goldens
- Schemas
- CI-Konfiguration
- `scripts/` selbst

#### Nicht regulär commitbar

- Daily-Reports
- reguläre Run-Diagnostik
- große Snapshot-Bestände
- Replay- und Evaluationsexporte
- Debug-/Profiling-Artefakte
- fortschreibbare OHLCV-Basishistorien

---

## 6. Snapshot-Strategie

### 6.1 Snapshot-Klassen

#### Klasse A – fortschreibbare historische Basisdaten
Beispiele:

- OHLCV 1d
- OHLCV 4h
- vergleichbare Basishistorien

#### Klasse B – point-in-time Run-Artefakte
Beispiele:

- State-Snapshots
- Run-Entscheidungen
- Run-Diagnostik
- Bucket-Zustände je Run

#### Klasse C – Evaluations-/Kalibrierungsdaten
Beispiele:

- Replay-Exporte
- Forward-Return-Sets
- Labeling-/Kalibrierungsdaten

#### Klasse D – technische Provenance-/Manifest-Daten
Beispiele:

- `run.manifest.json`
- Config-Hash
- Schema-Version
- Datenfrische
- Source-Meta

### 6.2 Festlegung 1 – Parquet-Partitionierung

Historische OHLCV unter `snapshots/history/ohlcv/` werden nach  
**`timeframe + symbol + year/month`** partitioniert.

```text
snapshots/history/ohlcv/timeframe=1d/symbol=TAOUSDT/year=2026/month=03/part-000.parquet
snapshots/history/ohlcv/timeframe=4h/symbol=TAOUSDT/year=2026/month=03/part-000.parquet
```

Zusatzregeln:

- Monat ist kleinste reguläre Zeitpartition
- offene Monats-Partitionen sind fortschreibbar
- abgeschlossene Monats-Partitionen sind immutable
- Repair-/Backfill-Jobs dürfen einzelne Monats-Partitionen gezielt neu bauen

### 6.3 Formate und Speicherorte

#### Klasse A – Basishistorie
- Speicherort: `snapshots/history/`
- Format: Parquet
- Komprimierung: ja
- keine tägliche Voll-Duplikation

#### Klasse B – Run-Artefakte
- Speicherort: `snapshots/runs/YYYY/MM/DD/<run_id>/`
- kleine Metadateien als JSON
- volle Diagnostik komprimiert zeilenbasiert

#### Klasse C – Evaluation
- Speicherort: `evaluation/exports/`, `evaluation/replay/`, `evaluation/calibration/`
- Formate je Anwendungsfall: Parquet, JSONL.gz, CSV nur wenn nötig

#### Klasse D – Manifest/Provenance
- kanonisch bei `snapshots/runs/...`
- JSON
- dauerhaft mit dem Run zusammen

---

## 7. Reports-Architektur

### 7.1 Zielstruktur

```text
reports/
  index/
    latest_run.txt
    latest_paths.json
    latest.json
    latest_daily.json
    latest_confirmed_candidates.json
    latest_watchlist.json
    recent_runs.json
    latest_manifest.json   # optional

  daily/
    YYYY/MM/DD/
      report.json
      report.md
      report.xlsx

  runs/
    YYYY/MM/DD/<run_id>/
      report.json
      symbol_diagnostics.jsonl.gz
      report.md
      report.xlsx

  aux/
  archive/   # optional
```

### 7.2 Verbindliche Dateitypen

#### `report.json`
Kompakte kanonische Summary-Datei:

- Run-ID
- As-of
- Bucket-Summary
- Counts
- kompakte Listen
- Verweise auf Manifest und Diagnostik

#### `symbol_diagnostics.jsonl.gz`
Verbindliches Format für die vollständige Symboldiagnostik:

- komprimiert
- zeilenbasiert
- pro Symbol ein Record

#### `report.md` und `report.xlsx`
Abgeleitete Komfortformate, nicht kanonisch.

### 7.3 Festlegung 3 – `reports/index/`

Pflichtdateien:

- `latest_run.txt`
- `latest_paths.json`
- `latest.json`
- `latest_daily.json`
- `latest_confirmed_candidates.json`
- `latest_watchlist.json`
- `recent_runs.json`

Optional:

- `latest_manifest.json`

Regel:

- `reports/index/` wird erst nach vollständig geschriebenem Run atomar aktualisiert

### 7.4 Festlegung 4 – Manifest-Duplikation

`run.manifest.json` liegt **kanonisch nur unter**  
`snapshots/runs/YYYY/MM/DD/<run_id>/run.manifest.json`

Regeln:

- `reports/runs/.../report.json` referenziert das Manifest
- `reports/index/latest_paths.json` referenziert das Manifest
- `reports/index/recent_runs.json` referenziert das Manifest
- keine zweite physische Manifest-Kopie unter `reports/runs/...`

---

## 8. Retention-Policy

### Festlegung 2 – klassenbasierte Zwei-Stufen-Retention

- `snapshots/history/` bleibt dauerhaft und wird nicht regulär gelöscht
- `reports/daily/` hält `report.json` dauerhaft online
- `report.md` und `report.xlsx` werden ab 180 Tagen archiviert
- `reports/runs/` bleibt 90 Tage online, danach Archivierung nach `reports/archive/`
- `snapshots/runs/` bleibt 90 Tage online, danach Archivierung nach `snapshots/archive/`
- `evaluation/`-Exporte werden selektiv nach Referenzwert aufbewahrt
- `artifacts/` sind kurzlebig

---

## 9. GitHub Actions und `scripts/`

### 9.1 GitHub Actions
Wieder aufsetzen:

- Code Map
- GPT Snapshot
- definierte Script-/Analyse-Runner

### 9.2 `scripts/`
`scripts/` bleibt zentrale Ablage für:

- Analyse
- Evaluation
- Kalibrierung
- Recherche
- technische Hilfsskripte

### 9.3 Verbindliche Output-Zielpfade
Script-Outputs gehen nicht ungeordnet nach `reports/`.

Erlaubte Zielpfade:

- `evaluation/exports/`
- `artifacts/`
- `reports/aux/`

### 9.4 CI vs lokale Laufartefakte

#### Festlegung 5

- lokale operative Scanner-Runs schreiben kanonisch in `reports/`, `snapshots/`, `evaluation/`, `artifacts/` je nach Artefaktklasse
- CI darf die echte Zielstruktur nur im isolierten Job-Workspace erzeugen
- CI-Artefakte sind nicht automatisch Teil der dauerhaften Repo-Artefakthaltung
- Standard-Uploads in CI bleiben klein und gezielt
- große Diagnostik-/Replay-/Exportdateien nur in spezialisierten Workflows
- fortgeschriebene OHLCV-Basishistorien sind keine regulären CI-Artefakte

---

## 10. Betriebsmodell

### 10.1 Daily Discovery Scan

Empfohlene Reihenfolge:

1. Universe Discovery
2. Eligibility Filter
3. 1d-OHLCV für alle Eligible
4. 1d-Rohfelder
5. `pre_4h_candidate_filter` auf Basis billiger 1d-/Meta-Signale
6. 4h-OHLCV nur für vorqualifizierte Symbole
7. volle Achsenberechnung
8. voller Phase-Interpreter
9. Invalidation / Cycle
10. State Machine
11. Entry Pattern
12. Bucket / Ranking
13. Execution nur für reduzierte Kandidatenmenge
14. Persistenz + Reports

### 10.2 Bedeutung des `pre_4h_candidate_filter`

Der `pre_4h_candidate_filter` ist ein **operativer Budget-Filter**, kein fachlich kanonischer Marktphasenentscheid.

Er:

- arbeitet nur mit billigen Daten:
  - Eligibility-Meta
  - 1d-OHLCV
  - daraus berechenbaren 1d-only-Rohfeldern
- entscheidet nur:
  - „bekommt dieses Symbol heute 4h-Daten oder nicht?“
- ist **nicht** mit dem eigentlichen `phase/interpreter.py` gleichzusetzen

Er gehört logisch in:

- `universe/market_data_budget.py`

Die konkrete Heuristik ist in der Dokumentation klar zu beschreiben und bis zur finalen Festlegung ggf. in `docs/canonical/open_questions.md` zu pflegen.

### 10.3 Intraday Promotion Scan

1. Daily-Basis prüfen
2. Monitoring-Universum laden
3. neue relevante 4h-Bars nachladen
4. 4h-Rohfelder aktualisieren
5. Freshness / Invalidation / State / Pattern / Bucket neu berechnen
6. optional Execution für reduzierte Menge
7. Persistenz + Reports

---

## 11. Zeitlogik und Bar-Clock

Die `bar_clock.py` ist Fundament, kein Hilfsmodul.

### Verbindliche Regeln

- Zeitzone: UTC
- `daily_bar_id = YYYY-MM-DD` des geschlossenen Daily-Bars
- `intraday_bar_id = close_time_utc_ms` des letzten geschlossenen 4h-Bars
- `bars_since_*` laufen in kanonischen 4h-Bar-Einheiten
- Daily-zu-4h-Umrechnung zentral an einer Stelle
- Daily-/Intraday-Skip-Entscheidungen hängen an dieser Schicht

Die Bar-Clock muss vor fast allem anderen implementiert und hart getestet werden.

---

## 12. Universe-, Fetch- und Budget-Strategie

### 12.1 Grundsatz
Die alte harte Vorselektion nach kurzfristigem MEXC-Volumen darf nicht als Independence-Release-Kernlogik übernommen werden.

### 12.2 Neue Logik

- billige Eligibility-Filter dürfen vor OHLCV bleiben
- der eigentliche 4h-Fetch wird gestuft organisiert
- 1d kommt deutlich breiter
- 4h kommt nach operativer Vorqualifikation
- Execution kommt am spätesten und nur für kleine Mengen

---

## 13. State-, Phase- und Entry-Logik

### 13.1 Phase-Interpreter
Deterministisch aus Abschnitt 3. `freshness_distance_structural` bleibt Achse; state-interne Frische liegt nicht im Phase-Interpreter. fileciteturn0file4

### 13.2 Invalidation
Abschnitt 5 ist autoritativ gegenüber der verkürzten Darstellung in Abschnitt 4. fileciteturn0file2 fileciteturn0file3

### 13.3 `market_phase = none`
Festlegung für die Implementierung:

- Coins mit `market_phase = none`, die nie aktiv waren, werden nicht in die State Machine aufgenommen
- `rejected` bleibt für ehemals aktive oder bewusst verfolgte Setups reserviert

### 13.4 Entry Pattern

- `early_ready` ohne Pattern fällt in die `watchlist`, nicht in `discarded`
- `confirmed_ready` ohne tragfähiges Pattern wird nicht als regulärer `confirmed_candidate` ausgewiesen, sondern konservativ als `late_monitor` mit Reason `CONFIRMED_PATTERN_UNRESOLVED` behandelt

### 13.5 `execution_pending`
Nur intern, nicht als eigener User-Bucket.

---

## 14. Persistenz

### 14.1 Technologie
SQLite für:

- symbolbezogenen State
- Cycle
- Cache-Meta
- Run-Meta
- technische Repositories

### 14.2 Warum SQLite

- atomare Updates
- symbolweiser Zugriff
- alltagstauglich für Daily + Intraday
- besser kontrollierbar als lose JSON-Stores

### 14.3 Grenzen
Bulk-Zeitreihen-Historie gehört nicht primär in SQLite, sondern in die Parquet-Historie unter `snapshots/history/`.

---

## 15. Output-Schema

### 15.1 Kanonische Summary
`report.json` ist die kompakte Summary, keine Voll-Diagnostik.

### 15.2 Voll-Diagnostik
`symbol_diagnostics.jsonl.gz` enthält je Symbol die komplette Diagnostik, mindestens:

- Roh-Layer-Schlüssel
- Achsen
- Phase
- Invalidation
- Cycle
- State
- Pattern
- Execution
- Bucket
- Priority Score
- zentrale Reason-Codes
- relevante Pfade/IDs/Bar-Kontexte

### 15.3 Komfortformate
Markdown- und Excel-Reports bleiben derived.

---

## 16. Tests und Goldens

### 16.1 Weiterverwendbare Alt-Tests

- Infrastrukturtests
- Client-Tests
- Parsing-Tests
- Utility-Tests
- fachlogisch neutrale Daten-/Schema-Tests

### 16.2 Nicht primäre Independence-Release-Akzeptanztests

- alte Business-Logiktests
- alte Scoring-/Decision-/Ranking-Goldens

### 16.3 Neue Golden-Strategie

#### Typ 1 – deterministische Fixture-Goldens
Kleine Handfälle für:

- Achsen
- Phase
- State
- Pattern
- Buckets

#### Typ 2 – historische Replay-Goldens
Gezielte echte historische Zeitfenster.

#### Typ 3 – Schema-/Manifest-Goldens
Für Reports, Manifeste, Diagnostikformate.

#### Typ 4 – optionale Datenintegritäts-Goldens
Alte Samples nur für Parser-/Datenintegrität, nicht als Business-Golden.

---

## 17. Validierungsstrategie

### 17.1 Primäre Validierung
Nicht „Ähnlichkeit zum alten Scanner“, sondern:

- erkennt Independence-Release früher?
- erkennt Independence-Release besser?
- sind Zustandsübergänge statistisch sinnvoll?

### 17.2 Metriken

- `first_watch_bar`
- `first_early_ready_bar`
- `first_confirmed_ready_bar`
- 1d-/3d-/5d-/10d-Forward-Returns
- MFE (Maximum Favorable Excursion)
- MAE (Maximum Adverse Excursion)
- Conversion-Raten:
  - `watch -> early_ready`
  - `early_ready -> confirmed_ready`
  - `early/confirmed -> late/chased`
- Execution-Pass-Raten
- Laufzeiten
- Request-Zahlen
- Cache-Hit-Raten

### 17.3 Erfolgskriterien

- `early_ready` erscheint im Median vor dem Hauptmove
- `confirmed_ready` hat bessere Forward-Return-Profile als `watch`
- `late/chased` sind klar spätere und schlechtere Zustände
- Watchlist bläht sich nicht unkontrolliert auf
- Daily- und Intraday-Betrieb bleiben API-seitig tragfähig

---

## 18. Risiken und Gegenmaßnahmen

### 18.1 4h-Budget
**Risiko:** zu teure 4h-Vollversorgung  
**Gegenmaßnahme:** gestufter Fetch über `market_data_budget.py` und `pre_4h_candidate_filter`

### 18.2 Bar-Clock-Fehler
**Risiko:** falsche `bars_since_*`, falsche State-Transitions  
**Gegenmaßnahme:** `bar_clock.py` als frühes Fundament + Edge-Case-Tests

### 18.3 Persistenzdrift
**Risiko:** verlorene Cycles, inkonsistente State-Historie  
**Gegenmaßnahme:** SQLite + transaktionale Updates + klare Keys

### 18.4 Architekturverwässerung
**Risiko:** Altlogik aus Bequemlichkeit wieder hereinziehen  
**Gegenmaßnahme:** klare Modulgrenzen und neue Zielstruktur

### 18.5 Unklare offene Punkte
**Gegenmaßnahme:** alles entweder in `open_questions.md` oder `feature_enhancements.md`

---

## 19. Umsetzungsreihenfolge als Workstream

### Ticket 1
**`bar_clock + sqlite + config foundation`**  
`depends_on: []`

### Ticket 2
**`canonical docs bootstrap + path conventions`**  
`depends_on: []`

### Ticket 3
**`eligibility + market data budget + pre_4h_candidate_filter`**  
`depends_on: [1, 2]`

### Ticket 4
**`ohlcv fetch + cache policy`**  
`depends_on: [1, 3]`

### Ticket 5
**`raw features + normalization`**  
`depends_on: [1, 4]`

### Ticket 6
**`tier1 axes`**  
`depends_on: [5]`

### Ticket 7
**`tier2 simplified axes`**  
`depends_on: [5]`

### Ticket 8
**`phase interpreter`**  
`depends_on: [6, 7]`

### Ticket 9
**`invalidation + cycle`**  
`depends_on: [8]`

### Ticket 10
**`freshness + state machine`**  
`depends_on: [8, 9]`

### Ticket 11
**`entry patterns`**  
`depends_on: [8, 10]`

### Ticket 12
**`decision buckets + ranking + reasons`**  
`depends_on: [10, 11]`

### Ticket 13
**`output schema + reports architecture + diagnostics format`**  
`depends_on: [1, 2]`

Kann weitgehend parallel zur Fachlogik entwickelt werden.

### Ticket 14
**`history storage + snapshot lifecycle policy`**  
`depends_on: [1, 2]`

Kann ebenfalls parallel laufen.

### Ticket 15
**`daily runner`**  
`depends_on: [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]`

### Ticket 16
**`execution adapter + grading`**  
`depends_on: [12]`

### Ticket 17
**`intraday runner`**  
`depends_on: [1, 4, 9, 10, 11, 12, 13, 14, 16]`

### Ticket 18
**`evaluation + replay + forward returns`**  
`depends_on: [13, 14, 15, 17]`

### Ticket 19
**`github actions + scripts output conventions`**  
`depends_on: [2, 13, 14]`

---

## 20. Verbindliche Entscheidungen

### Festlegung 1
OHLCV-Parquet nach `timeframe + symbol + year/month`, offene Monate fortschreibbar, abgeschlossene Monate immutable.

### Festlegung 2
Klassenbasierte Zwei-Stufen-Retention:

- `snapshots/history/` dauerhaft
- `reports/daily/report.json` dauerhaft
- Komfortformate ab 180 Tagen Archiv
- `reports/runs/` 90 Tage online
- `snapshots/runs/` 90 Tage online
- `evaluation/` selektiv
- `artifacts/` kurzlebig

### Festlegung 3
`reports/index/` mit:

- `latest_run.txt`
- `latest_paths.json`
- `latest.json`
- `latest_daily.json`
- `latest_confirmed_candidates.json`
- `latest_watchlist.json`
- `recent_runs.json`
- optional `latest_manifest.json`

### Festlegung 4
`run.manifest.json` kanonisch nur unter `snapshots/runs/...`, Referenzen aus Report und Index.

### Festlegung 5
CI-Artefakte klar getrennt von lokalen/operativen Laufartefakten; echte Zielstruktur in CI nur im isolierten Workspace.

### Festlegung 6
`confirmed_ready` ohne tragfähiges Pattern wird dem Bucket `late_monitor` zugeordnet mit Reason Code `CONFIRMED_PATTERN_UNRESOLVED`.

---

## 21. Offene Fragen für `docs/canonical/open_questions.md`

### Vor Ticket 3 zu klären
1. genaue Eligibility-Schwellen vor 1d-Fetch
2. konkrete Regeln für den `pre_4h_candidate_filter`

### Vor Ticket 16/17 zu klären
3. Execution-Frequenz und Top-N-Regeln

### Kann später geklärt werden
4. exakte JSON-Struktur von `recent_runs.json`
5. Compaction-Regeln offener Monats-Partitionen
6. Archiv-/Cold-Storage-Automation
