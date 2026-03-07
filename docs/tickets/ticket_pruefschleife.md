# Ticket-Prüfschleife für neue Tickets

> Zweck: Vor jeder Ticket-Erstellung sicherstellen, dass das Ticket **V4.2.1 / die aktuelle alleinige Referenz**, **Canonical im Repo** und **das Ticket-Template** widerspruchsfrei zusammenführt.  
> Ziel: Drift, Feldnamen-Konflikte, implizite Annahmen und unvollständige Codex-Tickets vorab abfangen.

---

## Grundsatz

Ein Ticket darf **nicht** nur gegen Roadmap/Epic formuliert werden.  
Es muss zusätzlich gegen folgende Ebenen geprüft werden:

1. **Aktuelle alleinige Referenz**  
   z. B. V4.2.1

2. **`docs/canonical/*`**  
   autoritative Begriffe, Feldnamen, Units, Statuspfade, Nullability, Determinismus

3. **Ticket-Template**  
   Vollständigkeit für Codex:
   - Defaults
   - Missing vs Invalid
   - Nullability
   - not-evaluated vs failed
   - Determinismus
   - Tests
   - Constraints / Invariants

4. **Repo-Realität**
   - bestehende Konfigurationspfade
   - vorhandene Canonical-Docs
   - ggf. reale Modul-/Feldnamen im Code, wenn das Ticket darauf aufsetzt

---

## Pflicht-Prüfschleife vor jedem Ticket

### 1) Referenz-Check
Vor Ticket-Start klären:

- Welche Roadmap / Version ist die **alleinige Referenz**?
- Welche PR / welches Epic soll dieses Ticket genau abbilden?
- Ist der Scope des Tickets auf **genau 1 PR** begrenzt?

**Abbruchregel:**  
Wenn Scope oder Referenz unklar sind, kein Ticket schreiben.

---

### 2) Canonical-Collision-Check
Prüfen, ob die im Ticket verwendeten Begriffe/Felder/Regeln bereits in `docs/canonical/*` definiert sind.

Zu prüfen sind insbesondere:

- Feldnamen
- Enum-Werte / Taxonomien
- Statuspfade
- Timestamp-Units
- Tie-Breaker
- Sortierregeln
- Nullability
- harte vs weiche Regeln
- Budget- und Gate-Definitionen

**Fragen:**
- Gibt es bereits einen kanonischen Feldnamen?
- Gibt es bereits eine kanonische Unit?
- Gibt es bereits eine kanonische Regel für denselben Sachverhalt?
- Würde das Ticket eine zweite konkurrierende Wahrheit erzeugen?

**Abbruchregel:**  
Wenn ein bestehender Canonical-Contract betroffen ist, muss das Ticket ihn explizit referenzieren und konsistent dazu formuliert werden.

---

### 3) Field-Name- und Normalisierungs-Check
Wenn im Ticket Felder genannt werden:

- Existiert der Feldname bereits kanonisch?
- Ist es ein **Raw-Feld** oder ein **normalisiertes kanonisches Feld**?
- Werden im Ticket versehentlich alternative Namen eingeführt?

**Pflicht:**
- Raw-Feld vs normalisiertes Feld explizit trennen
- einen bestehenden kanonischen Feldnamen nicht umbenennen
- keine freien Alias-Namen einführen

**Beispielhafte Prüffragen:**
- Nutzt das Ticket `closeTime`, `closeTime_ms` oder einen neuen Alias wie `close_time`?
- Ist klar, welches Feld im Contract verbindlich ist?
- Ist klar, wo Normalisierung beschrieben wird?

---

### 4) Status-/Taxonomie-Konsistenz-Check
Bei allen statusartigen Feldern prüfen:

- Sind Enum-Werte bereits kanonisch definiert?
- Ist die Bedeutung jedes Status eindeutig?
- Sind Statuspfade klar voneinander getrennt?

Besonders prüfen bei:
- `ENTER`
- `WAIT`
- `NO_TRADE`
- `UNKNOWN`
- `FAIL`
- `MARGINAL`
- `null`
- `false`

**Pflichtfragen:**
- Bedeutet `UNKNOWN` „nicht evaluiert“, „Fetch fehlgeschlagen“ oder „fachlich negativ bewertet“?
- Ist `MARGINAL` nur knapp handelbar oder bereits fast `FAIL`?
- Ist `WAIT` nur für voll evaluierte Kandidaten erlaubt?
- Wird `null` semantisch korrekt behandelt oder heimlich in `false` umgedeutet?

---

### 5) Defaults / Missing vs Invalid Check
Für jedes Ticket mit Config-, Schema- oder Output-Bezug prüfen:

- Was passiert, wenn ein Key fehlt?
- Was passiert, wenn ein Key vorhanden, aber ungültig ist?
- Was passiert, wenn ein Feld bewusst `null` ist?
- Was ist Default, was ist Fehler?

**Pflicht:**
- Missing ≠ Invalid
- keine stillen Fallbacks ohne explizite Regel
- kein implizites `bool(...)` auf semantisch nullable Feldern

---

### 6) Not-Evaluated vs Failed Check
Für jede neue Stage / jedes neue Feld prüfen:

- Kann etwas **nicht evaluiert** sein?
- Kann etwas **evaluiert, aber fehlgeschlagen** sein?
- Wird dieser Unterschied im Ticket explizit beschrieben?

**Pflichtfragen:**
- Liegt kein Orderbook vor, weil Budget nicht gereicht hat?
- Oder wurde gefetcht, aber die Daten waren kaputt/stale?
- Ist das ein `UNKNOWN`-Pfad oder ein `FAIL`-Pfad?

---

### 7) Determinismus-Check
Für jedes Ticket mit Sortierung, Ranking, Output oder Gates prüfen:

- Ist die Sortierung stabil?
- Gibt es definierte Tie-Breaker?
- Sind NaN/null-Fälle geregelt?
- Gibt es datums-/zeitbasierte Regeln mit klarer Unit?
- Ist Closed-Candle-only / No-lookahead sauber eingehalten?

**Pflicht:**
- keine fuzzy Formulierungen wie „normalerweise“, „üblicherweise“, „ungefähr“
- deterministische Acceptance Criteria
- deterministische Testfälle

---

### 8) Repo-Reality-Check
Bevor das Ticket finalisiert wird:

- Gibt es bereits reale Dateien/Module/Funktionen, die denselben Contract berühren?
- Werden im Ticket Dateipfade, Module oder Funktionsnamen genannt, die im Repo anders heißen?
- Passt der Ticket-Scope zur tatsächlichen Struktur im Repo?

**Pflicht:**
- Ticket nicht nur aus Roadmap herleiten
- Ticket gegen bestehende Repo-Struktur plausibilisieren

---

### 9) Template-Vollständigkeits-Check
Vor finaler Ausgabe prüfen, ob das Ticket alle relevanten Template-Teile vollständig und codex-fest ausfüllt:

- Title
- Context / Source
- Goal
- Scope
- Out of Scope
- Canonical References
- Proposed change
- Codex Guardrails
- Acceptance Criteria
- Default-/Edgecase-Abdeckung
- Tests
- Constraints / Invariants
- Definition of Done

**Pflicht:**
- keine leeren Pflichtabschnitte bei Code-Tickets
- keine unklaren Formulierungen in Acceptance Criteria
- keine versteckten Annahmen im Freitext statt in Guardrails / ACs

---

### 10) Drift-Check gegen bestehende Tickets
Vor Ausgabe eines neuen Tickets prüfen:

- Widerspricht das neue Ticket einem bereits geschriebenen Ticket?
- Ändert es stillschweigend einen früher festgelegten Begriff?
- Muss ein Follow-up-Ticket statt einer stillen Änderung geschrieben werden?

**Regel:**
- Kein stilles Überschreiben früherer Tickets
- Bei nachträglicher Korrektur: explizites Follow-up-Ticket schreiben

---

## Minimaler Preflight-Workflow

Vor jedem Ticket diese Reihenfolge einhalten:

1. Referenz festziehen  
2. Relevante Canonical-Dokumente identifizieren  
3. Feldnamen / Taxonomien / Units abgleichen  
4. Repo-Realität plausibilisieren  
5. Ticket schreiben  
6. Template-Check durchführen  
7. Drift- / Collision-Check gegen bestehende Tickets  
8. Erst dann Ticket final ausgeben

---

## Abbruchsignale — Ticket noch nicht ausgeben

Ein Ticket ist **nicht freigabefähig**, wenn mindestens einer dieser Punkte zutrifft:

- alleinige Referenz unklar
- betroffene Canonical-Docs nicht geprüft
- Feldname/Unit/Status bereits anders kanonisch definiert
- Missing vs Invalid nicht explizit geregelt
- not-evaluated vs failed nicht getrennt
- Nullability semantisch unklar
- Acceptance Criteria nicht deterministisch
- Scope greift faktisch mehr als 1 PR an
- Ticket widerspricht einem bestehenden Ticket
- Repo-Dateipfade / Contracts sind nur geraten

---

## Empfehlung für die praktische Anwendung

Für jede neue Ticket-Erstellung vorab kurz dokumentieren:

- Welche Canonical-Dokumente wurden geprüft?
- Welche kritischen Feldnamen / Status / Units wurden abgeglichen?
- Gibt es offene Kollisionen?
- Falls nein: Ticket freigeben
- Falls ja: Ticket anpassen oder Follow-up-Ticket anlegen

---

## Kurzcheckliste für den operativen Einsatz

- [ ] Alleinige Referenz identifiziert
- [ ] Relevante `docs/canonical/*` geprüft
- [ ] Feldnamen/Units mit Canonical abgeglichen
- [ ] Raw vs normalisiert sauber getrennt
- [ ] Statuspfade / Enum-Werte konsistent
- [ ] Missing vs Invalid geregelt
- [ ] not-evaluated vs failed getrennt
- [ ] Nullability explizit
- [ ] Determinismus / Tie-Breaker geklärt
- [ ] Repo-Pfade / echte Modulnamen plausibilisiert
- [ ] Template vollständig ausgefüllt
- [ ] Kein Widerspruch zu bestehenden Tickets
- [ ] Bei Korrekturen: explizites Follow-up statt stiller Änderung

---

## Zielzustand

Ein Ticket ist erst dann „codex-fest“, wenn es:

- fachlich zur Referenz passt,
- repo-konsistent mit Canonical ist,
- keine zweite Wahrheit erzeugt,
- keine stillen Annahmen enthält,
- deterministisch testbar ist,
- und frühere Tickets nicht unbemerkt überschreibt.
