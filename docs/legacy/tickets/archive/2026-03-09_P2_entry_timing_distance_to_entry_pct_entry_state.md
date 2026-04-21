> ARCHIVED (ticket): Implemented in PR for this ticket. Canonical truth is under `docs/canonical/`.

# Ticket: Entry-Timing sichtbar machen (`distance_to_entry_pct` + `entry_state`)

## Kontext

Der letzte Fix hat die Darstellung von **geplantem Entry** und **aktuellem Spot** im Output getrennt.  
Damit ist die Datenbasis jetzt deutlich sauberer: Ein Report kann künftig unterscheiden zwischen

- **geplantem Einstieg** (`entry_price_usdt`)
- **aktuellem Marktpreis** (`current_price_usdt`)

Was weiterhin fehlt, ist eine **explizite Timing-Semantik**.  
Aktuell muss ein Leser selbst interpretieren, ob ein Setup:

- noch **vor dem Trigger** liegt,
- **am Trigger** ist,
- **im Entry-Bereich** liegt,
- oder bereits **zu weit gelaufen** ist.

Das führt weiterhin zu unnötiger Ambiguität in der Bewertung von Trade-Kandidaten.

## Ziel

Für jeden Trade-Kandidaten soll zusätzlich ausgewiesen werden:

1. **`distance_to_entry_pct`**  
   Prozentuale Distanz zwischen `current_price_usdt` und `entry_price_usdt`

2. **`entry_state`**  
   Ein kompakter, diskreter Status, der die aktuelle Marktlage relativ zum geplanten Entry beschreibt

Ziel ist **bessere Interpretierbarkeit**, **nicht** die Änderung der Decision-Logik.

---

## Scope

### Neu im kanonischen Output

#### 1) `distance_to_entry_pct`
Definition:

- Prozentuale Distanz von `current_price_usdt` zu `entry_price_usdt`
- Vorzeichenbehaftet
- deterministisch und dokumentiert

Empfohlene Formel:

```text
distance_to_entry_pct = ((current_price_usdt / entry_price_usdt) - 1.0) * 100
```

Beispiele:

- `0.00` → Spot exakt am Entry
- `-2.50` → Spot 2.5 % unter Entry
- `+4.20` → Spot 4.2 % über Entry

#### 2) `entry_state`
Diskreter Status aus der Lage von Spot vs. Entry.

Vorgeschlagene Werte:

- `early`
- `at_trigger`
- `inside_entry_zone`
- `late`
- `chased`

---

## Fachliche Semantik

### Grundprinzip

`entry_state` soll **nur** das Timing / die aktuelle Lage relativ zum geplanten Einstieg ausdrücken.

Es soll **nicht** ausdrücken:

- ob das Setup gut oder schlecht ist,
- ob der Trade erlaubt ist,
- ob RR attraktiv genug ist,
- ob die finale `decision` BUY / WATCH / PASS ist.

### Vorschlag für die Einordnung

Da wir noch keinen voll ausmodellierten Entry-Zonen-Begriff im gesamten Projekt standardisiert haben, soll die erste Version bewusst **einfach und stabil** sein.

#### Variante für V1

- `early`  
  Spot liegt sinnvoll **unterhalb** des Entry-Levels, Trigger noch nicht erreicht

- `at_trigger`  
  Spot liegt praktisch am Entry-Level  
  Empfohlene Toleranz: kleiner enger Bereich um 0 %, z. B. `abs(distance_to_entry_pct) <= 0.25`

- `inside_entry_zone`  
  Nur verwenden, falls im Datensatz bereits eine belastbare Entry-Range / Zone vorhanden ist  
  Wenn keine robuste Zone vorhanden ist, in V1 **nicht erzwingen**

- `late`  
  Spot liegt moderat **oberhalb** des Entry-Levels, Einstieg wäre potenziell verspätet

- `chased`  
  Spot liegt deutlich oberhalb des Entry-Levels, Kandidat wirkt „hinterhergelaufen“

### Empfohlene pragmatische Schwellen für V1

Falls noch keine bessere projektspezifische Semantik existiert:

- `early`: `distance_to_entry_pct < -0.25`
- `at_trigger`: `-0.25 <= distance_to_entry_pct <= +0.25`
- `late`: `+0.25 < distance_to_entry_pct <= +3.00`
- `chased`: `distance_to_entry_pct > +3.00`

`inside_entry_zone` nur dann setzen, wenn eine echte Zone aus bestehenden Feldern robust ableitbar ist.  
Sonst in V1 lieber **weglassen** oder intern auf `at_trigger` / `late` mappen, statt künstliche Logik zu erfinden.

---

## Nicht-Ziele

Dieses Ticket soll **nicht**:

- die Ranking-Logik ändern
- die `decision`-Logik ändern
- RR neu berechnen
- Stop / TP verschieben
- neue Filter aktivieren
- Kandidaten härter oder weicher selektieren

Es geht ausschließlich um **Output-Semantik und Interpretierbarkeit**.

---

## Anforderungen an die Implementierung

### Output / Schema

- `distance_to_entry_pct` muss im kanonischen JSON enthalten sein
- `entry_state` muss im kanonischen JSON enthalten sein
- beide Felder müssen in die Schema-Dokumentation aufgenommen werden
- falls relevant: Excel-/Markdown-Export entsprechend ergänzen

### Datentypen

- `distance_to_entry_pct`: numerisch (`float`)
- `entry_state`: String / Enum

### Robustheit

Wenn `entry_price_usdt` oder `current_price_usdt` fehlt oder ungültig ist:

- `distance_to_entry_pct = null`
- `entry_state = null`

Keine stillen Fantasiewerte erzeugen.

### Determinismus

- gleiche Inputs → gleiche Klassifikation
- keine implizite Abhängigkeit von Rundung im UI
- Klassifikation zentral und testbar implementieren

---

## Akzeptanzkriterien

### AC1 — Neues Feld im Output
Ein Trade-Kandidat mit gültigem `entry_price_usdt` und `current_price_usdt` enthält ein numerisches Feld `distance_to_entry_pct`.

### AC2 — Neues Statusfeld im Output
Ein Trade-Kandidat mit gültigen Preisdaten enthält ein Feld `entry_state` mit einem erlaubten Statuswert.

### AC3 — Fehlende Daten sind sauber behandelt
Wenn einer der benötigten Preise fehlt oder ungültig ist, werden keine falschen Defaults erzeugt; die neuen Felder sind `null`.

### AC4 — Decision bleibt unverändert
Bei identischem Input darf dieses Ticket **keine** Änderung an Ranking, Score, RR oder `decision` verursachen.

### AC5 — Dokumentation aktualisiert
Die kanonische Output-Dokumentation beschreibt beide neuen Felder inklusive Semantik.

### AC6 — Exporte konsistent
Falls Excel-/Markdown-Exports Candidate-Felder spiegeln, sind die neuen Felder dort sichtbar oder bewusst dokumentiert ausgelassen.

---

## Testfälle

### Unit-Tests für Distanzberechnung

#### Fall 1: Exakt am Entry
- `entry_price_usdt = 100`
- `current_price_usdt = 100`
- Erwartung:
  - `distance_to_entry_pct = 0.0`
  - `entry_state = at_trigger`

#### Fall 2: Unter Entry
- `entry_price_usdt = 100`
- `current_price_usdt = 97`
- Erwartung:
  - `distance_to_entry_pct = -3.0`
  - `entry_state = early`

#### Fall 3: Leicht über Entry
- `entry_price_usdt = 100`
- `current_price_usdt = 101`
- Erwartung:
  - `distance_to_entry_pct = +1.0`
  - `entry_state = late`

#### Fall 4: Deutlich über Entry
- `entry_price_usdt = 100`
- `current_price_usdt = 106`
- Erwartung:
  - `distance_to_entry_pct = +6.0`
  - `entry_state = chased`

#### Fall 5: Fehlender Spot
- `entry_price_usdt = 100`
- `current_price_usdt = null`
- Erwartung:
  - `distance_to_entry_pct = null`
  - `entry_state = null`

#### Fall 6: Fehlender Entry
- `entry_price_usdt = null`
- `current_price_usdt = 100`
- Erwartung:
  - `distance_to_entry_pct = null`
  - `entry_state = null`

### Regression-Tests

- Bestehende `decision`-Werte bleiben für einen festen Snapshot unverändert
- Bestehende RR-Felder bleiben unverändert
- Bestehende Ranking-/Sorting-Felder bleiben unverändert

---

## Implementierungshinweise

### Empfehlung zur Architektur

Die Ableitung von

- `distance_to_entry_pct`
- `entry_state`

sollte an **einer zentralen Stelle** im Output-/Normalization-Layer erfolgen, nicht mehrfach in einzelnen Exportern.

Begründung:

- verhindert Drift zwischen JSON / Excel / Markdown
- macht die Logik testbar
- hält spätere Threshold-Anpassungen lokal

### Empfehlung zur Einführung

1. Berechnung im kanonischen Output ergänzen
2. Schema-Doku aktualisieren
3. Exporte erweitern
4. Regression-Tests laufen lassen
5. Erst danach reale Reports prüfen

---

## Rollout-Hinweis

Nach Merge dieses Tickets bitte die nächsten Reports gezielt darauf prüfen:

- sind `distance_to_entry_pct` und `entry_state` überall sinnvoll befüllt?
- wirken die Grenzen für `late` vs. `chased` praxistauglich?
- gibt es Kandidaten, die künftig eine echte `inside_entry_zone`-Semantik brauchen?

---

## Definition of Done

Das Ticket ist erledigt, wenn:

- die zwei neuen Felder im kanonischen Output vorhanden sind
- die Felder dokumentiert sind
- die Logik durch Unit-Tests abgedeckt ist
- Regression-Tests belegen, dass `decision` / RR / Ranking unverändert bleiben
- ein neuer Report manuell geprüft wurde und die neuen Felder plausibel aussehen
