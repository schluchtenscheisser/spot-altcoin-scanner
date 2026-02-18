# Arbeitsanweisung an GPT‑Codex (Spot Altcoin Scanner)

> **Ziel dieses Dokuments:** Eindeutige Prozess‑ und Qualitätsanweisung für GPT‑Codex zur eigenständigen Arbeit im Repository.  
> **Fokus:** Arbeitsweise (Branch/PR/DoD, Qualitäts‑Gates, Versionierung, Dokumentationspflicht).  
> **Oberstes Gebot:** **Ergebnis muss immer korrekt berechnet werden** (wichtiger als lauffähiger Code).

---

## 0) Oberstes Gebot (nicht verhandelbar)

- **Korrekte Berechnung > lauffähiger Code.**  
  Wenn beides nicht gleichzeitig geht: **Korrektheit hat Vorrang**.
- Alles, was Scores/Features beeinflusst, muss **deterministisch, fachlich korrekt und reproduzierbar** sein.

---

## 1) Arbeitsmodus & Scope

- In einem Chat können **nacheinander mehrere Themen** bearbeitet werden.
- **Jedes Thema endet mit genau einem PR** (keine Vermischung mehrerer Themen in einem PR).
- **Keine Scope‑Creeps:** Pro Thema nur das umsetzen, was zu diesem Thema gehört.
- Sonderfall **„Critical Findings“:** **Nur Critical Findings** beheben, **keine Improvement‑Proposals** nebenbei umsetzen.

---

## 2) Pflichtlektüre vor jeder Änderung (Docs‑First)

Bevor Codex irgendetwas ändert, muss er die Projektdoku lesen (gezielt, aber vollständig genug):

1. `README.md`  
2. `docs/GPT_SNAPSHOT.md` (bei großem Umfang: relevante Abschnitte gezielt)  
3. `docs/code_map.md` (**verbindlich** für Modul‑/Funktionsnamen, Architektur, Call‑Graph)  
4. `docs/spec.md`  
5. `docs/context.md`  
6. `docs/features.md`  
7. `docs/config.md`  
8. `docs/scoring.md`  
9. `docs/All_Setups_Computation_Transparency.md`  
10. `docs/THEMA8_DOCUMENTATION.md`  
11. `docs/pipeline.md`  
12. `docs/data_model.md`

Zusätzlich (wenn vorhanden und relevant fürs Thema):

- `SCHEMA_CHANGES.md` (für Output‑/Schema‑Änderungen)
- `FEATURE_RULEBOOK.md` (als ergänzende Regeln)

---

## 3) Quellen‑Priorität bei widersprüchlichen Definitionen

Wenn Definitionen kollidieren, gilt diese Reihenfolge:

1. **Explizite Definitionen in den Docs unter `docs/`**  
   (insb. `features/spec/context/scoring/config/data_model/pipeline`)
2. `docs/code_map.md` ist die **verbindliche Referenz**, *wie* das Repo strukturiert ist (Namen/Imports/Call‑Graph)
3. Wenn trotz Docs unklar: **im Chat nachfragen** (siehe Punkt 4)

---

## 4) Keine stillen Annahmen (Unsicherheit → Chat)

- **Keine stillen Annahmen.**
- Wenn eine Definition fehlt/unklar ist:
  - **im Chat nachfragen**, bevor implementiert wird **oder**
  - wenn eine Klärung im PR erfolgen soll: dann **explizit im PR dokumentieren**, was entschieden wurde (inkl. Begründung).
- Wenn bewusst von Standard‑Definitionen abgewichen wird (weil Projektdoku das so fordert): **im PR erklären** und **in Docs festhalten**.

---

## 5) Repo‑Arbeitsweise (Branch → Commits → PR)

### 5.1 Branch‑Regeln

- Pro Thema ein eigener Branch **direkt von `main`**.
- Standard‑Branchname: `feat/<kurzer-slug>`  
  Beispiele: `feat/closed-candles`, `feat/wilder-atr`, …
- Sonderfall **Critical Findings:** Branchname `feat/fix-critical-findings`

### 5.2 PR‑Pflichtinhalt (Minimum)

Jeder PR muss klar beantworten:

- **Was ändert sich fachlich?** (Definition + Motivation)
- **Welche Dateien/Funktionen** sind betroffen?
- **Welche Tests/Checks** beweisen die Korrektheit?
- Wenn Output‑/Schema betroffen: **`schema_version`** und **Eintrag in `SCHEMA_CHANGES.md`**

### 5.3 Definition of Done (pro PR)

Ein Thema gilt erst als „done“, wenn:

1. Fachliche Definitionen sind korrekt umgesetzt (gemäß Priorität).  
2. Validierung/Tests sind grün (siehe Qualitäts‑Gates).  
3. Doku ist aktualisiert, wenn Semantik/Interpretation geändert wurde.  
4. Bei Output‑/Schema‑Änderungen: `schema_version` gepflegt + `SCHEMA_CHANGES.md` Eintrag.

---

## 6) Qualitäts‑Gates (Korrektheit beweisen, nicht nur hoffen)

Codex muss pro Thema eine **Kombination** aus folgenden Gates liefern:

### Gate A — Golden Sample Tests (deterministische Fixtures)

- Kleiner, fester OHLCV‑Datensatz (Fixture)
- Erwartete Feature‑Werte als „Golden Output“
- Test prüft zentrale Werte + Key‑Presence (nicht nur „läuft durch“)

### Gate B — Invarianten / Property‑Checks

Je nach Thema passende Invarianten, z. B.:

- **Closed‑candle only** (keine Intraday‑Wackler): aktuelle Kerze muss „geschlossen“ sein  
  (Konzept: `closeTime <= asof`)
- **Baselines ohne aktuelle Candle** (z. B. SMA/High/Low‑Baselines) wenn definitorisch gefordert
- **Keine NaN/Inf** in finalen Scores/Features (wo nicht ausdrücklich erlaubt)
- **Deterministisch** (gleiche Inputs → gleiche Outputs)
- **Kein Lookahead‑Bias**
- (falls relevant) **Score‑Range [0,100]**

### Gate C — Externe Referenz‑Validierung (wo sinnvoll)

Für Indikatoren (z. B. EMA/ATR) mindestens eine Option:

- Vergleich gegen bekannte Referenz (z. B. TA‑Lib / dokumentierte Definitionen) auf kleinen Beispielen **oder**
- „Handrechenbares“ Mini‑Beispiel im Test, erwartetes Ergebnis dokumentiert

**Wichtig:** Wenn ein Ergebnis absichtlich von einer Standard‑Bibliothek abweicht (weil die Projektdoku das so will): im PR klar begründen und in Docs festhalten.

---

## 7) Tests: „Fail before / Pass after“

- Neue/angepasste Tests sollen den Fehler/Gap **vor** der Implementierung nachweisbar machen  
  (würden vorher scheitern) und **nach** der Implementierung grün sein.

---

## 8) Konfiguration statt Hardcoding (besonders für Scoring/Thresholds)

- Scorer‑Schwellen/Thresholds müssen **config‑getrieben** sein.
- **Keine hardcodierten Konstanten**, wenn es um Thresholds/Scoring‑Parameter geht  
  (außer Doku sagt explizit etwas anderes und das ist im PR begründet).

---

## 9) Output‑/Snapshot‑Schema & Versionierung

### 9.1 Grundsatz

- Output/Docs dürfen angepasst werden.
- **Breaking Changes** sind erlaubt, aber **nur** mit sauberer **Schema‑Versionierung** und Doku.

### 9.2 Regeln bei Schema‑Änderung

Wenn sich Report‑/Snapshot‑Schema ändert (Keys/Struktur/Semantik):

1. `schema_version` erhöhen (z. B. `v1` → `v2`)  
2. PR beschreibt „was, warum, Migration“  
3. **Pflichteintrag in `SCHEMA_CHANGES.md`** mit:
   - Version vorher/nachher
   - Art der Änderung (additiv/breaking/semantisch)
   - Migration/Kompatibilität
   - kurzes Beispiel‑Payload

### 9.3 Reproduzierbarkeit („Replay“)

- Wenn „as‑of“ relevant ist (z. B. Closed‑Candle‑Logik): **As‑Of Timestamp** muss im Snapshot/Meta gespeichert werden (für Replay‑Fähigkeit).

---

## 10) Dokumentation aktualisieren (immer wenn Semantik sich ändert)

Wenn sich Bedeutung/Interpretation ändert (z. B. „close = last closed candle“, „ATR = Wilder“):

- relevante Doku unter `docs/` aktualisieren  
  (insb. `features/spec/context/scoring/config/pipeline/data_model`)
- plus kurzer Hinweis im PR‑Text

---

## 11) Was Codex im Chat liefern soll (Abschluss‑Output pro PR)

Nach Abschluss eines Themas im PR:

1. **PR‑Link** + kurze Zusammenfassung  
2. Liste der geänderten Bereiche (Dateien/Funktionen)  
3. Welche Qualitäts‑Gates erfüllt wurden (A/B/C)  
4. Hinweis zur `schema_version` (falls geändert) + Bestätigung, dass `SCHEMA_CHANGES.md` gepflegt ist

---

*Ende der Arbeitsanweisung.*
