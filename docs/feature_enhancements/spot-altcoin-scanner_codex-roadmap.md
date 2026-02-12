# Spot Altcoin Scanner – Codex Roadmap & Arbeitsanweisung (PR‑basierte Feature‑Korrektheit)

Dieses Dokument ist als **Eingangspost für neue Chats** gedacht, in denen **ChatGPT Codex** direkt im Repository Code ändert, committet und Pull Requests erstellt.

**Oberstes Gebot:** Die berechneten Features müssen **fachlich korrekt** sein (nicht nur “lauffähig”).  
**Arbeitsmodus:** Pro Chat/Session bearbeiten wir **genau ein Thema**, das in sich **abgeschlossen** ist und in **einem PR** landet.

---

## 1) Was zu jedem Thema dazugehört:
1) **Dieses Dokument** (Roadmap/Anweisung)  
2) **`improvements_existing_data.md`** (verbindliche Ergänzungen/Änderungen) im Repo im Ordner docs/feature_enhancements 
3) **`SCHEMA_CHANGES.md`** (separates Dokument für Schema-/Output‑Änderungen) im Repo im Ordner docs/feature_enhancements 

---

## 2) Verbindliche Wissensquellen & Prioritätsregeln
Codex muss vor jeder Änderung **zuerst** die Projekt‑Doku lesen:

1) `README.md`  
2) `docs/GPT_SNAPSHOT.md` (wenn groß: die relevanten Abschnitte gezielt)  
3) `docs/code_map.md` (**verbindlich** für Modul-/Funktionsnamen, Architektur, Abhängigkeiten)  
4) `docs/spec.md`  
5) `docs/context.md`  
6) `docs/features.md` (Feature‑Definitionen)

### 2.1 Priorität bei widersprüchlichen Definitionen
1) **`improvements_existing_data.md`** hat Vorrang, **wo es explizit erweitert/ändert**.  
2) Ansonsten gelten `docs/features.md`, `docs/spec.md`, `docs/context.md` als Basis.  
3) `docs/code_map.md` ist die verbindliche Referenz für “wie das Repo aufgebaut ist” (Namen/Imports/Call‑Graph).

**Keine stillen Annahmen.** Wenn eine Definition fehlt oder unklar ist: im PR klar dokumentieren (oder im Chat nachfragen).

---

## 3) Codex‑Arbeitsweise (Repo‑Write, Commit, PR) – Standardprozess
Codex arbeitet direkt im Repo und erstellt pro Thema einen PR.

### 3.1 Branch‑Strategie (Standard)
**Pro Thema ein eigener Branch direkt von `main`** (empfohlen):
- Branch‑Name: `feat/<kurzer-slug>`  
  Beispiele: `feat/closed-candles`, `feat/wilder-atr`, `feat/raw-snapshot-v2`

**Warum:** klare Abgrenzung, weniger Konflikte, saubere Historie.

### 3.2 PR‑Inhalt (Mindestanforderungen)
Jeder PR muss enthalten:
- **Was ändert sich fachlich?** (Definitionen + Motivation)  
- **Welche Files/Funktionen sind betroffen?**  
- **Welche Tests/Checks beweisen die Korrektheit?**  
- **Wenn Schema/Output geändert:** `schema_version` + Eintrag in `SCHEMA_CHANGES.md`

### 3.3 “Definition of Done” pro PR
Ein Thema gilt als abgeschlossen, wenn:
1) Feature‑Definitionen sind korrekt umgesetzt (gemäß Prioritätsregeln).  
2) Validierung/Tests sind grün (siehe Qualitäts‑Gates).  
3) Doku ist aktualisiert, wenn sich Definitionen/Interpretationen geändert haben.  
4) Wenn Output/Snapshots betroffen: `schema_version` gepflegt + Eintrag in `SCHEMA_CHANGES.md`.

---

## 4) Qualitäts‑Gates (Korrektheit > Kompatibilität)
Codex muss pro Thema eine **Kombination** aus Prüfmethoden nutzen:

### Gate A — Golden Sample Tests (deterministische Fixtures)
- Ein kleiner, fester OHLCV‑Datensatz (Fixture)  
- Erwartete Feature‑Werte als Golden Output  
- Test vergleicht zentrale Werte und Key‑Presence

### Gate B — Invarianten / Property‑Checks
Beispiele (je nach Thema):
- **Closed‑candle only:** aktuelle Kerze muss geschlossen sein (via `closeTime <= asof`)  
- **Baseline excludes current candle:** SMA/High/Low‑Baselines ohne current candle  
- Keine NaNs/Inf in finalen Scores/Features (wo nicht erlaubt)  
- Monotonie‑Checks (z. B. EMA reagiert “glatt”, ATR nicht negativ)

### Gate C — Externe Referenz‑Validierung (wo sinnvoll)
Für Indikatoren (EMA/ATR) mindestens eine der Optionen:
- Vergleich gegen eine bekannte Referenz (z. B. TA‑Lib, TradingView‑Definitionen) anhand kleiner Beispiele  
- Alternativ: “handrechenbares” Mini‑Beispiel im Test (kleine Serie, erwartetes Ergebnis dokumentiert)

**Wichtig:** Wenn Werte bewusst von einer Standard‑Definition abweichen (weil `improvements_existing_data.md` es so will), muss das im PR erklärt und in Docs festgehalten werden.

---

## 5) Output-/Snapshot‑Schema: Versionierung + separates Änderungslog (Option 2)
### 5.1 Grundsatz
Codex darf Output/Docs anpassen. Für Output/Snapshots gilt:
- **Breaking Changes** sind erlaubt, aber nur mit **Schema‑Versionierung** und Dokumentation.

### 5.2 Regeln
1) Wenn sich Report-/Snapshot‑Schema ändert (Keys, Struktur, Semantik):
   - `schema_version` erhöhen (z. B. `v1` → `v2`)
   - PR beschreibt “was, warum, Migration”
2) **Eintrag in `SCHEMA_CHANGES.md`** ist Pflicht:
   - Version vorher/nachher
   - Änderung (additiv/breaking/semantisch)
   - Migration/Kompatibilität
   - Beispiel‑Payload (kurz)

### 5.3 Dokumentation
Wenn Semantik sich ändert (z. B. “close = last closed candle”, “ATR = Wilder”), dann:
- `docs/features.md` / `docs/spec.md` aktualisieren  
- Kurzer Hinweis im PR‑Text

---

# 6) Themenpakete (jeweils ein PR, in sich abgeschlossen)
> Reihenfolge‑Empfehlung: **1 → 2 → 3 → 4 → 5 → 6 → (7 optional) → 8**

## Thema 1 — Test‑Basis: Golden Sample + minimale Invarianten
**Ziel:** Sicherheitsnetz für alle folgenden Änderungen.

**Akzeptanzkriterien:**
- `pytest` läuft grün
- Fixture + Golden Output vorhanden
- Mindestens 2–3 Invarianten‑Checks (Key‑Presence, keine NaNs, deterministisch)

---

## Thema 2 — Closed Candles + As‑Of Time (höchste Priorität)
**Ziel:** Features basieren ausschließlich auf **geschlossenen** Candles. Keine Intraday‑Wackler.

**Akzeptanzkriterien:**
- “current candle” = **last closed** candle (per `closeTime <= asof_ts_ms`)
- Alle Features nutzen Index der letzten geschlossenen Kerze (nicht `[-1]`)
- As‑Of Timestamp wird im Snapshot/Meta gespeichert (für Replay)

**Validierung:**
- Golden Sample angepasst + Invarianten: closed‑candle check
- Optional: 2 Runs hintereinander (gleiche Inputs) → gleiche Features

---

## Thema 3 — Raw Snapshots erweitern (closeTime + quoteVolume)
**Ziel:** Rohdaten sind replay‑fähig und vollständig.

**Akzeptanzkriterien:**
- OHLCV‑Raw Snapshot enthält zusätzlich `close_time` und `quote_volume` (wenn geliefert)
- Keine Downstream‑Crashes beim Speichern/Lesen
- Falls Snapshot‑Schema betroffen: `schema_version` + `SCHEMA_CHANGES.md`

---

## Thema 4 — EMA‑Initialisierung (SMA‑Start statt “erster Wert”)
**Ziel:** EMA fachlich sauber initialisieren, weniger Bias am Anfang.

**Akzeptanzkriterien:**
- EMA startet mit SMA(period) und setzt dann rekursiv fort
- Externe Referenz‑Check oder dokumentiertes Mini‑Beispiel im Test

---

## Thema 5 — ATR als Wilder ATR
**Ziel:** ATR nach Wilder‑Definition (rekursiv), stabilere Volatilitätsmessung.

**Akzeptanzkriterien:**
- Wilder ATR implementiert (inkl. sauberer True Range)
- Vergleich/Validierung gegen Referenz oder dokumentiertes Mini‑Beispiel
- `atr_pct` daraus abgeleitet, nie negativ

---

## Thema 6 — Lookback‑Konvention: Baselines ohne Current Candle
**Ziel:** SMA/High/Low‑Baselines sollen **nicht** die current candle enthalten (wo definitorisch gefordert).

**Akzeptanzkriterien:**
- Baselines nutzen Lookback bis `idx-1` (nicht `idx`)
- Explizite Doku im Code/Docs, welche Features baseline‑exklusiv sind
- Invarianten: baseline‑Fenster korrekt

---

## Thema 7 — QuoteVolume‑Features (optional)
**Ziel:** Liquidity/Volume‑Signale auf QuoteVolume stützen (wenn verfügbar).

**Akzeptanzkriterien:**
- Neue Features dokumentiert (`docs/features.md`)
- Tests/Golden erweitert
- Output‑Schema versioniert, wenn nötig

---

## Thema 8 — Dokumentation & Gesamt‑DoD
**Ziel:** Alles, was wir fachlich geändert haben, ist in Docs nachvollziehbar.

**Akzeptanzkriterien:**
- `docs/features.md` beschreibt closed‑candle, as‑of, baselines, ATR/EMA‑Definitionen
- `docs/spec.md`/`docs/context.md` konsistent
- `SCHEMA_CHANGES.md` vollständig für alle Schema‑Sprünge

---

## 7) Was du im Chat sagst (Startbefehl)
- „Heute arbeiten wir an Thema X.“
- Optional: „Bitte besonders auf Indikator‑Definitionen achten (EMA/ATR)“

---

## 8) Was Codex im Chat als Ergebnis liefern soll (kurz & überprüfbar)
Nach Abschluss des Themas im PR:
1) PR‑Link + kurze Zusammenfassung  
2) Liste der geänderten Bereiche (Files/Funktionen)  
3) Welche Gates erfüllt wurden (A/B/C)  
4) Hinweise zu Schema‑Version (falls geändert) + Eintrag in `SCHEMA_CHANGES.md`  
