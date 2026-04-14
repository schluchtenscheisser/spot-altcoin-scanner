# v2.1 / Independence-Release — Zusatzkontext für weitere Ticket-Arbeit ab Status „Tickets 1–3 umgesetzt“

## Zweck dieses Dokuments

Dieses Dokument ist ein **ergänzender Arbeitskontext** für die weitere Bearbeitung des Independence-Release (v2.1) im **duplizierten Repo**.

Es ist **ergänzend** zu den folgenden verbindlichen Grundlagen zu lesen:

- den 7 v2.1-Spezifikationsabschnitten
- `independence_release_gesamtkonzept_final.md`

Adressaten sind primär **ChatGPT** und **Claude** als Ticket-Autoren, Ticket-Reviewer und Architektur-Sparringspartner.

## Wichtige Einordnung

Dieses Dokument ist **keine neue fachliche Primärautorität**.  
Die fachlich verbindliche Wahrheit bleibt:

- die 7 v2.1-Abschnittsdateien
- `independence_release_gesamtkonzept_final.md`

Dieses Dokument dient stattdessen als:

- **Architektur-Präzisierungsdokument**
- **Arbeitskontext für neue Chats**
- **Leitplanken- und Priorisierungsdokument** für weitere Tickets
- **Orientierung für offene Präzisierungsblöcke**, die vor späteren Tickets sauber entschieden werden müssen

## Status quo

Für den weiteren Arbeitskontext gilt:

- **Tickets 1, 2 und 3 sind bereits umgesetzt**
- Neue Informationen aus nachgelagerten Architektur- und Organisationsklärungen sollen **nicht stillschweigend rückwirkend** in diese bereits umgesetzten Tickets hineininterpretiert werden
- Stattdessen gelten die hier festgehaltenen Punkte **ab jetzt** als:
  - Leitplanken für **weitere Tickets**
  - Hinweise für **Canonical-Doku**
  - Marker für **noch zu präzisierende Architekturblöcke**

---

## Teil A — Ab sofort verbindlich als Leitplanke für weitere Tickets verwenden

Die folgenden Punkte sollen ab jetzt in allen weiteren Chats und bei allen weiteren Tickets als **verbindliche Architekturleitplanken** behandelt werden, soweit sie den 7 Abschnittsdateien und dem Gesamtkonzept nicht widersprechen.

### 1. Independence-Release / v2.1 ist eine echte Neuarchitektur im duplizierten Repo

Das neue Repo ist ein **eigenständiges v2.1-Repo** und kein Legacy-kompatibler Hybrid.  
Es gibt **keine Pflicht**, im Zielsystem einen internen Shadow-Mode oder dauerhafte Legacy-Kompatibilität mitzuschleppen.

Alte Repo-Komponenten dürfen als Referenz, Codequelle oder Vergleich dienen, aber **nicht** als fachlicher Zielpfad.

### 2. Die v2.1 ist eine Schichtenarchitektur, keine Evolution des Legacy-Scorers

Die v2.1 ist fachlich in getrennten Schichten zu denken, nicht als kleine Weiterentwicklung des alten Score-/Decision-Kerns.

Insbesondere sollen folgende Alt-Repo-Komponenten **nicht** als Kernstruktur der Zielarchitektur behandelt werden:

- Legacy-Scorer
- globales Legacy-Ranking
- altes `decision.py`
- altes Output-Schema

### 3. `bar_clock.py` ist Fundamentmodul

Bar-Clock und Zeitlogik sind kein Neben-Utility, sondern Teil des fachlichen Kerns.

Davon hängen unmittelbar ab:

- `daily_bar_id`
- `intraday_bar_id`
- `bars_since_*`
- Timing-Invalidation
- Daily-/Intraday-Fortschreibung
- Persistenzkonsistenz

UTC bleibt die zentrale Zeitbasis.

### 4. 4h-Fetch bleibt gestuft

Die Zielarchitektur soll 4h-Daten **nicht blind** für das gesamte Eligible-Universum laden.

Das Grundprinzip bleibt:

1. Eligibility
2. 1d-Fetch für Eligible
3. 1d-basierte Vorqualifikation
4. 4h-Fetch nur für qualifizierte Symbole
5. Execution nur für kleinere Kandidatenmengen

Eine stillschweigende Rückkehr zum alten harten Shortlist-Cut darf nicht passieren.

### 5. Persistenz ist fachlicher Kern

Persistenz ist in der v2.1 **nicht optional** und nicht bloß technische Bequemlichkeit.

Persistierter Kontext ist fachlich relevant für:

- State-Fortschreibung
- Cycle-Kontext
- `bars_since_*`
- Reifung
- Verfall
- Reaktivierung
- Run-Kontext
- spätere Diagnostik und Evaluation

### 6. Historie liefert Kontext, aber keinen Override

Jeder Lauf bewertet den heutigen Zustand **frisch datengetrieben**.

Persistierte Historie liefert zusätzlichen Kontext für:

- Transition
- Reifung
- Bestätigung
- Verfall
- Reaktivierung
- Drop-Off
- Diagnose / Verlauf

Historie darf aber **nicht** die aktuelle objektive Bewertung übersteuern.

### 7. Output / Reports / Diagnostik als Dauerlösung entwerfen

Output- und Diagnostikstruktur sollen **nicht** als provisorische Zwischenlösung gedacht werden.

Die Zielrichtung ist:

- kompakter Summary-Report
- vollständige Symbol-Diagnostik
- technisches Manifest
- saubere Navigations- und Indexstruktur

### 8. Historische Basisdaten und Run-Artefakte trennen

Es soll klar getrennt werden zwischen:

**fortzuschreibenden historischen Basisdaten**, zum Beispiel:
- OHLCV-Historien
- laufende Marktdaten-Zeitreihen
- längerfristige Evaluationsgrundlagen

und

**Run-spezifischen Point-in-time-Artefakten**, zum Beispiel:
- Buckets
- Ranking
- State-/Cycle-Kontext zum Laufzeitpunkt
- Diagnostik
- Manifest

### 9. Evaluation ist Kernbestandteil, nicht Beiwerk

Evaluation gehört früh in die Zielarchitektur und soll **nicht** erst ganz am Ende „irgendwann noch“ ergänzt werden.

Insbesondere relevant sind später:

- Replay
- Forward Returns
- Transition-Auswertungen
- Bucket-/State-Auswertungen
- MFE / MAE
- Lead Time
- Reaktivierungs- und Drop-Off-Verhalten

### 10. Canonical-Doku inhaltlich neu, strukturell am bisherigen Schema orientieren

Die bestehende Canonical-Struktur kann als Informationsarchitektur dienen.  
Der alte fachliche Inhalt ist aber nicht automatisch weiter bindend.

Daraus folgt:

- Doku inhaltlich neu aufsetzen
- vorhandenes Schema als Navigationsrahmen nutzen
- alte Inhalte allenfalls als Referenz, nicht als neue Wahrheit

### 11. Code Map, GPT Snapshot und `scripts/`-Routine als Arbeitsinfrastruktur beibehalten

Diese Bestandteile sind fachlich nicht das Zielmodell, aber organisatorisch und analytisch weiterhin wertvoll.

Sie sollen im neuen Repo bewusst wiederverwendet bzw. neu aufgebaut werden.

---

## Teil B — Vor relevanten späteren Tickets noch explizit entscheiden

Die folgenden Punkte sind wichtig, aber **noch nicht präzise genug**, um sie ungeprüft in weitere Tickets zu schreiben.

Sie müssen vor den jeweils betroffenen Tickets oder Ticketgruppen bewusst geklärt werden.

### 1. Persisted Candidate Context / Watchlist-Kontinuität

Das ist derzeit der wichtigste offene Präzisierungsblock.

Noch festzulegen sind insbesondere:

- genaue Persistenzfelder
- Transition-Semantik
- Drop-Off-Regeln
- Reaktivierungsregeln
- Daily- vs. Intraday-Fortschreibung
- Output-Felder für Verlauf / Transition

Diese Klärung ist besonders wichtig vor späteren Tickets zu:

- State Machine
- Daily Runner
- Intraday Runner
- Output / Diagnostics
- Evaluation

### 2. Behandlung von `confirmed_ready` ohne tragfähiges Pattern

Dieser Fall soll vor dem betroffenen Ticket ausdrücklich geklärt werden.

Insbesondere muss entschieden werden, wie der Fall semantisch behandelt und diagnostisch ausgegeben wird.

### 3. Weitere Präzisierungen rund um Eligibility und 1d→4h-Stufung nur bewusst als Follow-up

Da Tickets 1–3 bereits umgesetzt sind, sollen neue Erkenntnisse zu dieser Schicht **nicht stillschweigend rückwirkend** hineingeschrieben werden.

Falls sich aus Betrieb, Review oder neuer Klärung zusätzlicher Änderungsbedarf ergibt, soll das als:

- offene Frage
- Nachschärfung
- Follow-up-Ticket
- oder explizite Ticket-Erweiterung

geführt werden.

### 4. Genaue Execution-Frequenz

Noch festzulegen:

- ob Daily immer oder nur für Top-N Execution-relevant wird
- ob Intraday immer oder nur bei bestimmten Promotions / Kandidatenmengen läuft
- welche Buckets / Ranks wirklich Execution-Kontext erhalten

### 5. Kanonische Output-Pflichtfelder

Vor den Output-/Report-Tickets ist festzulegen:

- Minimalfelder in `report.json`
- Pflichtfelder in der vollständigen Symbol-Diagnostik
- technische Pflichtfelder im Manifest

### 6. Evaluationshorizonte und Standardmetriken

Vor den Evaluation-Tickets ist festzulegen:

- welche Zeithorizonte kanonisch sind
- welche Standardmetriken Pflichtbestandteil werden
- welche Kennzahlen in Reports und Evaluationen dauerhaft erscheinen sollen

### 7. Reports-/Snapshots-Zielstruktur konkretisieren

Die Richtung ist geklärt, die konkrete Zielstruktur soll aber vor den betreffenden Tickets verbindlich festgelegt werden.

Das betrifft insbesondere:

- Pfade
- Artefakttypen
- Indizes / Navigationsstruktur
- Trennung von Basisdaten und Run-Artefakten
- technische Provenance / Manifeste

### 8. Test-/Golden-Strategie neu schneiden

Vor späteren Test-/Evaluation-/Output-Tickets ist bewusst zu entscheiden:

- welche technischen Tests aus dem alten Repo weiter nutzbar sind
- welche fachlichen Goldens neu aufgebaut werden
- welche Replay-/Schema-/Manifest-Goldens entstehen sollen
- welche Betriebs-/Budget-Tests Pflicht sind

---

## Teil C — Arbeitsregel für neue Chats und weitere Ticket-Bearbeitung

### Arbeitsregel 1 — Umgang mit diesem Dokument

Dieses Dokument ist ein **ergänzender Architekturkontext**, aber **keine neue Primärautorität**.

In neuen Chats und bei der weiteren Bearbeitung gilt deshalb:

1. **Primärautorität bleibt**:
   - die 7 Abschnittsdateien
   - `independence_release_gesamtkonzept_final.md`

2. Dieses Dokument liefert:
   - Architekturleitplanken
   - Klärungsbedarf für spätere Tickets
   - Priorisierungshinweise
   - Prozesskontext für Ticket-Schärfung

3. Bei Widerspruch gilt:
   - Spezifikationsabschnitte und Gesamtkonzept gehen vor
   - dieses Dokument darf keine konkurrierende Wahrheit erzeugen

### Arbeitsregel 2 — Umgang mit weiteren Tickets ab dem Status „Tickets 1–3 umgesetzt“

Für jedes weitere Ticket soll vor der Ausarbeitung oder dem Review geprüft werden:

#### Schritt 1 — Leitplanken-Check
Welche Punkte aus **Teil A** müssen für dieses Ticket zwingend mitgedacht werden?

#### Schritt 2 — Präzisierungs-Check
Welche Punkte aus **Teil B** berührt dieses Ticket direkt?

- Falls keiner: Ticket normal weiter ausarbeiten
- Falls einzelne: diese Punkte **vor Ticketfinalisierung bewusst entscheiden**
- Falls die Punkte noch nicht sauber entscheidbar sind: als offene Vorbedingung markieren und nicht raten

### Praktische Anwendung

Bei der Bearbeitung der nächsten Tickets soll also nicht einfach nur geprüft werden:
- „Passt das zum Template?“
- „Passt das zum Gesamtkonzept?“

sondern zusätzlich:
- „Verletzt das Ticket eine der neuen Leitplanken?“
- „Berührt das Ticket einen noch offenen Präzisierungsblock?“
- „Müssen vor dem Ticket noch Architekturdetails explizit entschieden werden?“

---

## Teil D — Empfohlene Nutzung in neuen Chats mit ChatGPT oder Claude

Beim Start neuer Chats soll dieses Dokument idealerweise zusammen mit dem Gesamtkonzept und den Abschnittsdateien bereitgestellt werden.

Empfohlene Einordnung für neue Chats:

> Dieses Dokument ist ein ergänzender Architektur- und Arbeitskontext für die weitere Ticket-Bearbeitung im Independence-Release / v2.1.  
> Es ergänzt die verbindlichen Spezifikationsdateien und das Gesamtkonzept, ersetzt sie aber nicht.  
> Tickets 1–3 gelten als bereits umgesetzt.  
> Für weitere Tickets sollen die enthaltenen Leitplanken berücksichtigt und die offenen Präzisierungsblöcke vor betroffenen Tickets ausdrücklich geklärt werden.

---

## Teil E — Empfohlene kurzfristige Folgearbeit

Die folgenden Schritte sind aus diesem Dokument abgeleitet und sollen in der weiteren Bearbeitung bewusst berücksichtigt werden:

### Kurzfristig sinnvoll
- Teil A als feste Prüf-Liste für weitere Tickets verwenden
- Teil B als offene Architektur-Präzisierungsliste führen
- offene Punkte nicht versteckt in Tickets raten, sondern vorher klären

### Besonders früh vorbereiten
- Persisted Candidate Context / Watchlist-Kontinuität
- Output-/Report-/Snapshot-Zielarchitektur
- Evaluation-Grundstruktur
- spätere Ticket-Schärfung für State / Runner / Output / Evaluation

---

## Kurzfassung

Für die weitere Bearbeitung ab dem Status „Tickets 1–3 umgesetzt“ gilt:

- v2.1 / Independence-Release ist eine **Neuarchitektur**
- Bar-Clock, Persistenz und gestufter Fetch sind **Grundpfeiler**
- Historie liefert **Kontext, aber keinen Override**
- Output / Diagnostik / Manifest sollen **als Dauerlösung** gedacht werden
- historische Basisdaten und Run-Artefakte sind **zu trennen**
- Evaluation ist **früher Kernbestandteil**
- einige wichtige Blöcke sind architektonisch angelegt, aber **vor späteren Tickets noch präzise zu entscheiden**
- dieses Dokument ergänzt die Spezifikation und das Gesamtkonzept, **ersetzt sie aber nicht**
