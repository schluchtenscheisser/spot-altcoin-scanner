# Roadmap & Chat-Playbook: Feature-Berechnung verbessern (paketweise Sessions)

## 1) Ziel dieses Projekts
Wir verbessern die Feature-Berechnung des Repos `schluchtenscheisser/spot-altcoin-scanner` schrittweise, ohne die Architektur zu brechen und ohne „Big Bang“-Änderungen.

**Hauptziele:**
1) **Deterministische Features** (keine instabilen Werte durch offene Candles)  
2) **Bessere Indikator-Qualität** (ATR Wilder, EMA-Init etc.)  
3) **Bessere Reproduzierbarkeit** (Snapshots inkl. CloseTime/QuoteVolume)  
4) **Klarer, reviewbarer Prozess** über Feature-Branch und kleine PR-Pakete  

**Zusätzliche Referenzdatei pro Chat:** `improvements_existing_data.md` (wird immer mit hochgeladen)

---

## 2) Verbindliche Regeln für die Umsetzung (wichtig)
Diese Regeln sind **nicht verhandelbar**:

### 2.1 Single Source of Truth
Bevor du Code vorschlägst oder änderst, musst du zuerst lesen:
1) `README.md`  
2) `docs/GPT_SNAPSHOT.md` (falls zu groß: die relevanten Abschnitte per Suche/Teilausschnitt)  
3) `docs/code_map.md` (**verbindlich für Modul-/Funktionsnamen**)  
4) `docs/spec.md`  
5) `docs/context.md`  

Danach erst gezielt die betroffenen Code-Dateien laden.

### 2.2 Scope-Limit pro Paket/Session
- **max. 3 Dateien**
- **max. ~200 Diff-Zeilen**
- Änderungen **präzise & schrittweise**
- Keine Fantasie-Module/Funktionsnamen, die nicht in `docs/code_map.md` existieren
- Jede Änderung braucht: **Warum? / Was? / Wie prüfen?**

### 2.3 Output-Format pro Session (was du liefern musst)
Am Ende jedes Pakets will ich:
1) Liste der geänderten Dateien  
2) „Vorher/Nachher“-Blöcke (oder Diff)  
3) Wie ich lokal teste (konkrete Commands)  
4) Kurze Definition of Done (DoD) erfüllt? ja/nein  
5) Commit-Message Vorschlag  

---

## 3) Arbeitsweise pro Paket (Standard-Workflow)
1) **Feature-Branch erstellen** (nur einmal, Paket 1):  
   - `git checkout -b feature/feature-integrity-v2`
2) Du liest **erst die Doku-Dateien** (siehe 2.1) und prüfst `code_map.md` auf betroffene Stellen.
3) Du lokalisierst die relevanten Funktionen im Code.
4) Du machst einen **Mini-Plan** (3–6 Schritte).
5) Du schlägst eine Änderung vor (max 3 Dateien / 200 Zeilen).
6) Du gibst **Test/Validierungs-Schritte**.
7) Ich committe und (optional) öffne einen PR.
8) Nächstes Paket = neuer Chat.

---

# 4) Pakete (Themen) – jeweils in einer Session abschließbar

## Thema 1 — “Safety Net”: Mini-Regression & Golden Sample
**Ziel:** Wir schaffen eine minimale Prüfbasis, damit spätere Änderungen messbar sind.

**Scope:** nur Test/Fixture, keine Feature-Logik-Änderungen.

**Typisch betroffene Dateien (max 2–3):**
- `tests/...` (neu oder erweitern)
- ggf. kleine Test-Fixture Datei (z. B. `tests/fixtures/...json`)

**Schritte:**
1) In `code_map.md` prüfen, wie Tests aktuell strukturiert sind.
2) Minimalen OHLCV-Mini-Datensatz als Fixture definieren (z. B. 30 Kerzen).
3) `FeatureEngine` einmal laufen lassen → Output als Golden JSON speichern.
4) Test vergleicht: Keys vorhanden + einige zentrale Werte exakt/nahezu gleich.

**DoD:**
- `pytest` läuft durch
- Golden Output erzeugt/vergleichbar
- Keine Produktionslogik geändert

---

## Thema 2 — Closed Candle / “As-Of Time” (höchste Priorität)
**Ziel:** Features basieren **nur auf geschlossenen Candles**. Keine Intraday-Wackler.

**Warum:** Offene Daily/4h Candles verfälschen Returns/ATR/Breakout/Volume.

**Scope:** As-of Timestamp einführen + Candle-Filterung.

**Typisch betroffene Dateien (max 3):**
- `scanner/pipeline/ohlcv.py` **oder** Pipeline-Orchestrator (wo OHLCV→Features geht)
- `scanner/pipeline/features.py`
- ggf. `scanner/pipeline/snapshot.py` (nur Meta)

**Schritte:**
1) `asof_ts_ms` (UTC now) einmal pro Run erzeugen.
2) `asof_ts_ms` an Feature-Berechnung übergeben.
3) Aus MEXC-klines die `closeTime` nutzen, um die letzte geschlossene Kerze zu bestimmen.
4) Feature-Berechnung nutzt `last_closed_idx` (statt `[-1]`).
5) Snapshot-Meta speichert `asof_ts_ms` (für Replays).

**DoD:**
- Features ändern sich nicht mehr “innerhalb des Tages” bei erneuten Runs
- Tests (Thema 1) angepasst/erweitert und grün

---

## Thema 3 — Raw Snapshots erweitern (CloseTime + QuoteVolume speichern)
**Ziel:** Rohdaten sind replay-fähig und vollständig.

**Problem heute:** Snapshot OHLCV speichert oft nicht `closeTime`/`quoteVolume`, wodurch Replays nicht 1:1 sind.

**Typisch betroffene Dateien (max 2):**
- `scanner/utils/raw_collector.py`
- evtl. `scanner/pipeline/ohlcv.py` (falls Collector-Aufruf angepasst wird)

**Schritte:**
1) Prüfen, wie OHLCV aktuell gespeichert wird (Collector).
2) Collector erweitert: pro Candle auch `close_time` + `quote_volume` persistieren (wenn vorhanden).
3) Sicherstellen: Parquet/CSV können diese Felder speichern.
4) (Optional) Minimaler Test, dass Felder geschrieben werden.

**DoD:**
- Snapshot enthält die zusätzlichen Spalten
- Keine Downstream-Crashes beim Lesen/Schreiben

---

## Thema 4 — EMA-Initialisierung verbessern (SMA statt erster Wert)
**Ziel:** EMA weniger bias, stabiler Start.

**Typisch betroffene Datei (1):**
- `scanner/pipeline/features.py`

**Schritte:**
1) Aktuelle EMA-Implementierung lokalisieren.
2) EMA-Startwert = SMA der ersten `period` Werte.
3) Danach klassisch rekursiv fortsetzen.
4) Tests/Golden anpassen.

**DoD:**
- EMA-Werte plausibel, keine NaNs/Crash
- Tests grün

---

## Thema 5 — ATR auf Wilder ATR umstellen
**Ziel:** ATR als Standard-Definition (Wilder), weniger “sprunghaft”.

**Typisch betroffene Datei (1):**
- `scanner/pipeline/features.py`

**Schritte:**
1) True Range definieren/prüfen.
2) ATR Wilder rekursiv rechnen.
3) `atr_pct` sauber daraus ableiten.
4) Tests/Golden aktualisieren.

**DoD:**
- ATR-Werte konsistent und stabil
- Tests grün

---

## Thema 6 — “Lookback-Konvention”: Baselines ohne Current Candle
**Ziel:** Baselines (SMA/High/Low) werden aus **vorherigen** Kerzen gebildet, nicht inklusive “aktueller” Kerze.

**Typische Kandidaten laut `improvements_existing_data.md`:**
- Volume SMA/Spike baseline
- Breakout Range High/Low
- ggf. Drawdown-Berechnungen

**Typisch betroffene Datei (1):**
- `scanner/pipeline/features.py`

**Schritte:**
1) Festlegen: “current candle” = last_closed candle.
2) Baselines verwenden `series[:idx]` statt `series[:idx+1]`.
3) Dokumentieren: welche Features baseline-exklusive Fenster nutzen.
4) Tests/Golden aktualisieren.

**DoD:**
- Kein Feature nutzt baseline inklusive current candle (wo es nicht soll)
- Tests grün

---

## Thema 7 — QuoteVolume-basierte Liquidity/Volume Features (optional)
**Ziel:** Optional neue (oder alternative) Liquidity-Signale mit QuoteVolume.

**Typisch betroffene Dateien (max 2–3):**
- `scanner/pipeline/features.py`
- `docs/features.md` (Dokumentation)
- ggf. Output/Report falls neue Keys angezeigt werden

**Schritte:**
1) Prüfen, ob QuoteVolume überall vorhanden ist (Thema 3 Voraussetzung).
2) Feature(s) definieren: z. B. quoteVolume spike, quoteVolume SMA.
3) In docs aufnehmen.
4) Tests/Golden anpassen.

**DoD:**
- Neue Features dokumentiert
- Keine Downstream-Fehler

---

## Thema 8 — Dokumentation & “Definition of Done” für Gesamtprojekt
**Ziel:** Klarer Standard, wie Features definiert sind (closed candle, as-of, baseline-Fenster).

**Typisch betroffene Dateien (max 3):**
- `docs/features.md`
- `docs/spec.md`
- ggf. `README.md`

**DoD:**
- Dokumente erklären:  
  - “close = last closed candle”  
  - “asof_ts_ms = timestamp used for candle closure check”  
  - Lookback-Konventionen

---

# 5) Validierung nach jedem Paket (einfach, ohne Entwicklerwissen)
Nach jedem Thema wurde mir mindestens eins davon empfohlen:

1) **Zwei Runs hintereinander** am gleichen Tag → Werte sollten gleich bleiben (besonders nach Thema 2)
2) **Golden Sample Test** (`pytest`) → grün
3) Top-Rankings (Report) kurz vergleichen: große Sprünge erklären wir im Chat
