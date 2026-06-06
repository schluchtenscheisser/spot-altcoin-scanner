# Master-Checkliste für codex-feste Tickets

**Zweck:**  
Diese Checkliste ist die **eine verbindliche Master-Checkliste** für die Erstellung und Prüfung neuer Tickets, die von Codex umgesetzt werden sollen.

Sie ist **generisch** formuliert und bewusst **nicht** an eine bestimmte Roadmap-Version gebunden.  
Stattdessen arbeitet sie mit dem Prinzip der **aktuellen autoritativen Referenzmenge** plus **Repo-Realität**.

**Ziel:**  
Tickets so präzise formulieren, dass Codex **keine semantischen Annahmen treffen** muss und spätere Review-Kommentare auf ein Minimum reduziert werden.

**Anwendungsbereich:**  
Für **jedes** Ticket verpflichtend.  
Besonders strikt anwenden bei Tickets mit:

* Config-Logik
* numerischen Berechnungen
* Nullable-/Tri-State-Feldern
* Pipeline-Gates / Stop-Pfaden
* Budget-/Ranking-/Sorting-Logik
* Risk-/Tradeability-/Decision-Semantik
* Zeit-/Timestamp-/Bar-Clock-Logik
* Repo-Struktur-, Authority- oder Dokumentationsänderungen

\---

## Grundsatz

Ein Ticket darf **nicht nur** gegen Roadmap/Epic formuliert werden.  
Es muss zusätzlich gegen folgende Ebenen geprüft werden:

1. **Aktuelle autoritative Referenzmenge**  
z. B. die aktuell gültige Roadmap-, Struktur-, Zielbild- oder Fachspezifikationsmenge
2. **Bestehende Repo-Dokumente / Canonical / Authority-Dateien**  
nur insoweit autoritativ, wie sie der aktuellen autoritativen Referenzmenge **nicht widersprechen**
3. **Ticket-Template**  
Vollständigkeit für Codex:

   * Defaults
   * Missing vs Invalid
   * Nullability
   * not-evaluated vs failed
   * Determinismus
   * Tests
   * Constraints / Invariants
4. **Repo-Realität**

   * bestehende Konfigurationspfade
   * vorhandene Authority-/Canonical-/Readme-Dokumente
   * reale Modul-/Datei-/Funktionsnamen im Code
   * laufende Legacy- oder Current-Repo-Flows, die noch benutzbar bleiben müssen

\---

## 1\. Referenz- und Scope-Check

### Prüffragen

* \[ ] Welche Roadmap / Struktur / Version / Dokumentmenge ist die **aktuelle autoritative Referenzmenge**?
* \[ ] Welche PR / welches Epic / welcher Arbeitsschritt soll dieses Ticket genau abbilden?
* \[ ] Ist der Scope des Tickets auf **genau 1 PR** begrenzt?
* \[ ] Ist ausgeschlossen, dass das Ticket implizit spätere oder benachbarte PRs mitzieht?
* \[ ] Ist im Ticket klar benannt, welche älteren Repo-Dokumente nur noch nachrangig oder rein referenziell sind?
* \[ ] Falls im Abstimmungsprozess eine mögliche Konzeptverbesserung oder Optimierung erkennbar wird: ist diese **explizit markiert** statt stillschweigend ins Ticket übernommen?
* \[ ] Ist klar, dass eine solche potenzielle Abweichung / Optimierung nur nach expliziter Abstimmung mit Martin in die Ticketlogik übernommen werden darf?

### Abbruchregel

Wenn Referenz oder Scope unklar sind: **kein Ticket schreiben und User informieren**.

Wenn eine potenzielle Konzeptabweichung oder Konzeptoptimierung erkannt wird, darf sie **nicht stillschweigend** in das Ticket eingebaut werden. Sie ist explizit zu markieren und vor Übernahme mit dem User abzustimmen.

### Pflichtsatz im Ticket

> Wenn die aktuelle autoritative Referenzmenge, bestehende Repo-Authority/Canonical-Dokumente und bestehender Code kollidieren, gewinnt die aktuelle autoritative Referenzmenge. Repo-Dokumente gelten nur insoweit fort, wie sie dieser Referenzmenge nicht widersprechen.

\---

## 2\. Canonical-/Authority-Collision-Check

Prüfen, ob die im Ticket verwendeten Begriffe/Felder/Regeln bereits in bestehenden Authority-/Canonical-Dokumenten definiert sind und ob das Ticket diese bewusst übernimmt, überschreibt oder entwertet.

### Zu prüfen

* \[ ] Feldnamen
* \[ ] Enum-Werte / Taxonomien
* \[ ] Statuspfade
* \[ ] Timestamp-Units
* \[ ] Tie-Breaker
* \[ ] Sortierregeln
* \[ ] Nullability
* \[ ] harte vs weiche Regeln
* \[ ] Budget- und Gate-Definitionen
* \[ ] Dokumentstatus (`authoritative`, `canonical`, `legacy`, `reference-only`, o. ä.)

### Prüffragen

* \[ ] Gibt es bereits einen kanonischen/autoritativen Feldnamen?
* \[ ] Gibt es bereits eine kanonische/autoritative Unit?
* \[ ] Gibt es bereits eine kanonische/autoritative Regel für denselben Sachverhalt?
* \[ ] Würde das Ticket eine zweite konkurrierende Wahrheit erzeugen?
* \[ ] Lässt das Ticket ältere Authority-/Canonical-Dateien scheinbar aktiv, obwohl sie für diesen Bereich entwertet werden sollen?

### Abbruchregel

Wenn ein bestehender Authority-/Canonical-Contract betroffen ist, muss das Ticket ihn explizit referenzieren und konsistent dazu formuliert werden oder explizit beschreiben, wie dieser Contract entwertet/umpriorisiert wird.

\---

## 3\. Field-Name- und Normalisierungs-Check

Wenn im Ticket Felder genannt werden:

### Prüffragen

* \[ ] Existiert der Feldname bereits autoritativ?
* \[ ] Ist es ein **Raw-Feld** oder ein **normalisiertes kanonisches Feld**?
* \[ ] Werden versehentlich alternative Namen eingeführt?
* \[ ] Ist klar, wo Normalisierung beschrieben wird?

### Pflichtregeln

* \[ ] Raw-Feld vs normalisiertes Feld explizit trennen
* \[ ] einen bestehenden autoritativen Feldnamen nicht stillschweigend umbenennen
* \[ ] keine freien Alias-Namen einführen

### Typische Prüffrage

* \[ ] Nutzt das Ticket einen autoritativen Feldnamen oder führt es einen neuen Alias ein, obwohl bereits ein Contract existiert?

\---

## 4\. Begriffs- und Statusschärfe

Für jeden neuen oder geänderten Status, Enum-Wert oder Reason Key:

### Prüffragen

* \[ ] Ist die erlaubte Wertemenge **vollständig und explizit** ausgeschrieben?
* \[ ] Ist jeder Wert **positiv definiert**, nicht nur indirekt über Ausschluss?
* \[ ] Ist klar, welche Werte **weiterlaufen**, welche **stoppen** und welche nur **Kontext** sind?
* \[ ] Ist explizit beschrieben, was der jeweilige Wert **nicht** bedeutet?
* \[ ] Sind Reason Keys maschinenlesbar, stabil und eindeutig?

### Pflichtfragen für typische Status

* \[ ] Ist `UNKNOWN` klar von `FAIL` getrennt?
* \[ ] Ist `NOT\_EVALUATED` klar von `NEGATIVE\_EVALUATION` getrennt?
* \[ ] Ist `WAIT` klar von „nicht entscheidbar“ getrennt?
* \[ ] Ist `MARGINAL` klar von `UNKNOWN` und `FAIL` getrennt?
* \[ ] Ist `null` semantisch beschrieben?

### Pflichtsatz im Ticket

Für jeden kritischen Status mindestens ein Satz der Form:

* `UNKNOWN` bedeutet ...
* `FAIL` bedeutet ...
* `MARGINAL` bedeutet ...
* `WAIT` bedeutet ...
* `null` bedeutet ...

\---

## 5\. Defaults / Missing vs Invalid / Override-Semantik

Das ist eine der häufigsten Fehlerquellen.

Für **jeden** neuen oder genutzten Config-Block muss explizit beantwortet sein:

### Prüffragen

* \[ ] Welche Keys sind **optional**?
* \[ ] Welche Keys sind **required**?
* \[ ] Was passiert bei **fehlendem Key**?
* \[ ] Was passiert bei **ungültigem Wert**?
* \[ ] Was passiert bei **partiellem Nested-Override**?
* \[ ] Gibt es verbotene stille Fallbacks?

### Pflichtentscheidungen pro Config-Block

* \[ ] Missing key → **Default** oder **Fehler**?
* \[ ] Partielles Dict-Override → **Merge mit Defaults** oder **vollständiger Replace**?
* \[ ] Ungültiger Typ/Wert → klarer Fehler oder normalisierte Korrektur?
* \[ ] Werden zentrale Defaults benutzt oder ad-hoc Raw-Dict-Fallbacks?

### Pflichtsatz im Ticket

Für jeden verschachtelten Config-Block muss mindestens einer dieser Sätze explizit enthalten sein:

**Variante A — Merge**

> Partielle Overrides in `<config\_block>` werden feldweise mit zentralen Defaults gemergt; fehlende Unterkeys gelten nicht als invalid.

**Variante B — Replace**

> Overrides in `<config\_block>` ersetzen den Block vollständig; fehlende Unterkeys sind nach dem Override invalid.

Ohne diese Festlegung ist das Ticket **nicht freigabefähig**.

\---

## 6\. Numerische Robustheit: `NaN`, `inf`, `-inf`, leere numerische Inputs

Diese Sektion ist Pflicht für Tickets mit:

* ATR / EMA / OHLCV / Risiko
* Slippage / Spread / Depth
* Prozenten / Scores / Thresholds
* pandas / numpy / float-Konvertierung
* sonstiger numerischer Transformationslogik
* Zeitdifferenzen / Epoch-Umrechnungen / Bar-Clock-Berechnungen

### Prüffragen

* \[ ] Was passiert bei `None`?
* \[ ] Was passiert bei `NaN`?
* \[ ] Was passiert bei `inf` / `-inf`?
* \[ ] Was passiert bei leerer Payload / leerer Serie / leerem Orderbook?
* \[ ] Was passiert bei Division durch 0 oder quasi-0?
* \[ ] Welche Eingaben gelten als „fehlend“?
* \[ ] Welche Eingaben gelten als „ungültig“?
* \[ ] Welche Eingaben gelten als „fachlich negativ“?

### Pflichtsatz im Ticket

> Nicht-finite numerische Werte (`NaN`, `inf`, `-inf`) gelten als ungültige bzw. nicht auswertbare Inputs und dürfen nicht in numerisch aussehende Outputs durchgereicht werden.

Wenn das **nicht** gelten soll, muss die Alternativregel explizit und testbar beschrieben sein.

\---

## 7\. Nullability / Tri-State / Bool-Fallen

Für jedes bool-artige Feld oder Entscheidungsergebnis:

### Prüffragen

* \[ ] Ist klar, ob das Feld wirklich **binär bool** ist?
* \[ ] Oder ist es fachlich **tri-state** (`true` / `false` / `null`)?
* \[ ] Ist `null` semantisch beschrieben?
* \[ ] Ist ausgeschlossen, dass `bool(x)` auf semantisch nullable Felder angewendet wird?
* \[ ] Bedeutet `false` wirklich „negativ bewertet“?
* \[ ] Bedeutet `null` „nicht evaluierbar“?
* \[ ] Darf ein nicht berechenbarer Wert zu `false` kollabieren?
* \[ ] Müssen abhängige Felder ebenfalls `null` bleiben, wenn Input fehlt?

### Pflichtsatz im Ticket

Für jedes potentiell tri-state Feld:

> `<feld>` ist nullable. `null` bedeutet „nicht belastbar evaluierbar“ und darf nicht implizit zu `false` koerziert werden.

\---

## 8\. Not-evaluated vs failed

Diese Trennung muss bei allen Gating-, Risk-, Tradeability- und Decision-Tickets explizit sein.

### Prüffragen

* \[ ] Kann etwas **nicht evaluiert** sein?
* \[ ] Kann etwas **evaluiert, aber fehlgeschlagen** sein?
* \[ ] Kann etwas **evaluiert, aber grenzwertig** sein?
* \[ ] Welcher Status / welches Feld repräsentiert diese Fälle?

### Pflichtsatz im Ticket

> Nicht evaluierbar / nicht bewertet und fachlich negativ bewertet sind getrennte Zustände und müssen im Code getrennt erhalten bleiben.

\---

## 9\. Determinismus / Reihenfolge / Tie-Breaker

Für jede Selektion, Sortierung, Budget-Grenze, Top-K-Logik oder Score-Reihenfolge:

### Prüffragen

* \[ ] Ist die Sortierlogik vollständig spezifiziert?
* \[ ] Ist ein Tie-Breaker explizit benannt?
* \[ ] Ist beschrieben, welche Eingaben zur Reihenfolge beitragen und welche nicht?
* \[ ] Ist ausgeschlossen, dass Dict-/Set-Iteration implizit die Reihenfolge bestimmt?
* \[ ] Ist bei identischem Input + identischer Config die Ausgabe identisch?
* \[ ] Ist closed-candle-only / no-lookahead, falls relevant, sauber eingehalten?

### Pflichtsatz im Ticket

> Bei identischem Input und identischer Config sind Auswahl, Reihenfolge, Status und Gründe identisch.

Wenn Sortierung relevant ist:

> Bei Score-Gleichstand greift der explizite Tie-Breaker `<x>`.

\---

## 10\. Pipeline-Grenzen / Stopp-Pfade

Für jedes Ticket, das eine Pipeline-Stufe verändert:

### Prüffragen

* \[ ] Ist die genaue Position in der Pipeline benannt?
* \[ ] Ist klar, was **weiterläuft** und was **stoppt**?
* \[ ] Ist klar, welche teuren Folgeschritte **nicht** mehr ausgelöst werden dürfen?
* \[ ] Sind interne Stop-Reasons klar benannt?
* \[ ] Erreichen gestoppte Kandidaten noch OHLCV / Features / Scoring / Risk / Decision?
* \[ ] Werden API-/Runtime-Kosten durch den Stop-Pfad wirklich vermieden?
* \[ ] Sind gestoppte Kandidaten still verworfen oder explizit begründet?

### Pflichtsatz im Ticket

> `<status/klasse>` stoppt vor `<nachfolgende\_stufe>` und darf keine weiteren Kosten in `<nachfolgende\_stufe>` auslösen.

\---

## 11\. Repo-Reality-Check

Bevor das Ticket finalisiert wird:

### Prüffragen

* \[ ] Gibt es bereits reale Dateien/Module/Funktionen, die denselben Contract berühren?
* \[ ] Werden im Ticket Dateipfade, Module oder Funktionsnamen genannt, die im Repo anders heißen?
* \[ ] Passt der Ticket-Scope zur tatsächlichen Struktur im Repo?
* \[ ] Werden vorhandene Helfer wiederverwendet, statt neue Parallel-Logik zu erzeugen?
* \[ ] Bricht das Ticket unbeabsichtigt noch laufende Legacy-/Current-Repo-Flows?
* \[ ] Muss der aktuelle README / Onboarding-Flow angepasst werden, damit das Repo weiterhin benutzbar bleibt?

### Pflichtsatz im Ticket

> Vorhandene Repo-Pfade/Helfer dürfen wiederverwendet werden, solange sie der aktuellen autoritativen Referenzmenge nicht widersprechen; keine zweite Wahrheit einführen.

\---

## 12\. Repository-Collision- und Authority-Consistency-Check

Diese Sektion ist **Pflicht** für Tickets, die Authority-/Canonical-Dokumente, Repo-Struktur, README, Zielbild, Legacy-Abgrenzung oder Dokumentstatus betreffen.

### Prüffragen

* \[ ] Gibt es im Repo bereits eine Datei, die denselben Bereich als „authoritative“, „canonical“ oder „single source of truth“ beansprucht?
* \[ ] Hebt das Ticket diese ältere Autoritätsbehauptung explizit auf oder priorisiert sie korrekt nach unten?
* \[ ] Ist klar benannt, welche Dokumente künftig **autoritative Wahrheit**, welche **legacy-track**, welche **reference-only** und welche **stale** sind?
* \[ ] Bleiben entwertete Dateien an einem Ort/Namen, der weiterhin fälschlich Autorität signalisiert?
* \[ ] Erzeugt das Ticket unbeabsichtigt zwei parallele Wahrheitssysteme?
* \[ ] Muss `AUTHORITY.md`, `README`, `code\_map`, `index`, `glossary` oder vergleichbare Einstiegsdokumentation mitgezogen werden, damit die neue Autoritätslage repo-weit konsistent ist?

### Pflichtsatz im Ticket

> Das Ticket darf keine zweite konkurrierende Dokumenten-Autorität erzeugen. Wenn bestehende Repo-Dokumente für den betroffenen Bereich entwertet oder nachrangig werden, muss dies explizit und repo-weit konsistent beschrieben werden.

### Mindesttests / Nachweise

* \[ ] konkreter Nachweis, dass kein entwertetes Dokument weiterhin als aktive SoT markiert bleibt
* \[ ] konkreter Nachweis, dass Einstiegsdokumente (`README`, `AUTHORITY`, Index/Guide) dieselbe Prioritätshierarchie widerspruchsfrei abbilden

\---

## 13\. Input-Semantik / Koerzierung / Rejection-Check

Diese Sektion ist **Pflicht** für jedes Ticket, das neue oder geänderte Funktionsparameter, Zeit-/Datums-Inputs, numerische Rohinputs, Parser oder Helper mit mehreren möglichen Input-Typen einführt.

### Prüffragen

* \[ ] Welche Input-Typen sind **erlaubt**?
* \[ ] Welche Input-Typen sind **verboten**?
* \[ ] Welche Einheiten gelten je erlaubtem Typ?
* \[ ] Gibt es Inputs, die mehrdeutig sein können (z. B. Sekunden vs Millisekunden, naive vs timezone-aware Datetimes)?
* \[ ] Welche Inputs werden explizit **koerziert**?
* \[ ] Welche Inputs werden explizit **abgelehnt**?
* \[ ] Ist ausgeschlossen, dass die Implementierung einen fachlich gefährlichen Input still umdeutet?
* \[ ] Sind Fehlerklassen (`TypeError`, `ValueError`, o. ä.) für ungültige oder mehrdeutige Inputs festgelegt?
* \[ ] Sind Beispiel-Inputs und erwartete Outputs/Errors für jede erlaubte/verbotene Kategorie ausgeschrieben?

### Pflichtentscheidungen

* \[ ] Pro Input-Typ ist die Unit explizit genannt
* \[ ] Mehrdeutige Inputs sind entweder verboten oder deterministisch geregelt
* \[ ] Naive Datums-/Zeitobjekte sind entweder explizit erlaubt mit klarer Semantik oder explizit verboten
* \[ ] Rohe numerische Zeitwerte sind entweder explizit erlaubt mit klarer Unit oder explizit verboten
* \[ ] „Looks valid but semantically wrong“ wird als Fehler behandelt, nicht stillschweigend umgedeutet

### Pflichtsatz im Ticket

> Erlaubte Input-Typen, Units, Koerzionsregeln und harte Rejection-Regeln sind vollständig spezifiziert. Mehrdeutige Inputs dürfen nicht stillschweigend umgedeutet werden.

### Mindesttests / Nachweise

* \[ ] mindestens ein gültiger Test pro erlaubtem Input-Typ
* \[ ] mindestens ein Invalid-Type-Test
* \[ ] mindestens ein Mehrdeutigkeits-/Reject-Test
* \[ ] mindestens ein Test für „gefährlich, aber formal parsebar“ Input

\---

## 14\. Template-Vollständigkeits-Check

Vor finaler Ausgabe prüfen, ob das Ticket alle relevanten Template-Teile vollständig und codex-fest ausfüllt:

* \[ ] Title
* \[ ] Context / Source
* \[ ] Goal
* \[ ] Scope
* \[ ] Out of Scope
* \[ ] Canonical References
* \[ ] Proposed change
* \[ ] Codex Guardrails
* \[ ] Acceptance Criteria
* \[ ] Default-/Edgecase-Abdeckung
* \[ ] Tests
* \[ ] Constraints / Invariants
* \[ ] Definition of Done

### Pflichtregeln

* \[ ] keine leeren Pflichtabschnitte bei Code-Tickets
* \[ ] keine unklaren Formulierungen in Acceptance Criteria
* \[ ] keine versteckten Annahmen im Freitext statt in Guardrails / ACs

\---

## 15\. Drift-Check gegen bestehende Tickets

Vor Ausgabe eines neuen Tickets prüfen:

### Prüffragen

* \[ ] Widerspricht das neue Ticket einem bereits geschriebenen Ticket?
* \[ ] Ändert es stillschweigend einen früher festgelegten Begriff?
* \[ ] Muss ein Follow-up-Ticket statt einer stillen Änderung geschrieben werden?
* \[ ] Enthält das Ticket eine potenzielle Konzeptverbesserung oder Optimierung, die gegen die bisherige autoritative Referenzmenge laufen würde?
* \[ ] Ist diese potenzielle Optimierung explizit als Abstimmungspunkt markiert statt still im Ticket gelöst?

### Regel

* \[ ] Kein stilles Überschreiben früherer Tickets
* \[ ] Bei nachträglicher Korrektur: explizites Follow-up-Ticket schreiben
* \[ ] Keine stille konzeptionelle Optimierung gegen die aktuelle autoritative Referenzmenge
* \[ ] Erkennbare Verbesserungsmöglichkeiten oder Optimierungsideen explizit markieren und vor Übernahme mit dem User abstimmen

\---

## 16\. Test-Schärfe: Kategorien reichen nicht, konkrete Fälle sind Pflicht

Jede relevante Preflight-Kategorie muss im Ticket mindestens einen **konkreten Testfall** haben.

### Nicht ausreichend

* „Config Defaults testen“
* „Nullability testen“
* „Determinismus testen“
* „README prüfen“
* „Timestamp-Inputs prüfen“

### Erforderlich

* \[ ] konkreter Missing-Key-Test
* \[ ] konkreter Invalid-Value-Test
* \[ ] konkreter `NaN`-/`inf`-Test, falls numerisch relevant
* \[ ] konkreter `null`-bleibt-`null`-Test
* \[ ] konkreter not-evaluated-vs-failed-Test
* \[ ] konkreter deterministischer Reproduktions-Test
* \[ ] konkreter Stop-/Weiterlauf-Test bei Pipeline-Tickets
* \[ ] konkreter Authority-Konsistenz-Test/Nachweis bei Repo-/Doku-Tickets
* \[ ] konkreter Koerzierung-/Reject-Test bei Input-/Helper-Tickets

### Pflichtsatz im Ticket

> Jede Preflight-Pflichtkategorie ist durch mindestens einen explizit ausgeschriebenen Testfall oder einen ebenso expliziten, prüfbaren Nachweis abgesichert.

\---

## 17\. Verbotsliste für stille Interpretationen

Ein Ticket ist **nicht ausreichend präzise**, wenn eine der folgenden Fragen offen bleibt:

* \[ ] Merge oder Replace bei verschachtelter Config?
* \[ ] `NaN` / `inf`-Verhalten?
* \[ ] `null` vs `false`?
* \[ ] not-evaluated vs failed?
* \[ ] expliziter Tie-Breaker?
* \[ ] gestoppt vs weitergereicht?
* \[ ] Default bei Missing Key?
* \[ ] klarer Fehler bei Invalid Value?
* \[ ] fehlend vs stale vs ungültig?
* \[ ] erlaubte Enum-Werte vollständig?
* \[ ] wer ist im betroffenen Bereich autoritative Wahrheit?
* \[ ] welche Repo-Dokumente werden entwertet oder nachrangig?
* \[ ] welche Input-Typen/Units sind erlaubt?
* \[ ] welche Inputs werden hart abgelehnt statt still umgedeutet?

Wenn eine dieser Fragen offen ist, muss das Ticket ergänzt werden.

\---

## 18\. Pflichtsektion für numerische / Config-lastige Tickets

Diese Sektion muss **wörtlich oder inhaltlich gleichwertig** in jedes Ticket aufgenommen werden, das Konfigurations- oder numerische Logik enthält:

### Pflichtblock

* \[ ] Partielle Nested-Overrides: **merge oder replace explizit festlegen**
* \[ ] Nicht-finite Werte (`NaN`, `inf`, `-inf`) explizit behandeln
* \[ ] Nullable Ergebnisse explizit als nullable markieren
* \[ ] Nicht auswertbar ≠ negativ bewertet
* \[ ] Fehlender Key ≠ ungültiger Key
* \[ ] Konkrete Tests für genau diese Fälle ausschreiben

\---

## 19\. Pflichtsektion für Repo-/Authority-/Onboarding-Tickets

Diese Sektion muss **wörtlich oder inhaltlich gleichwertig** in jedes Ticket aufgenommen werden, das README, Authority, Canonical, Zielstruktur, Legacy-Abgrenzung oder Einstiegsdokumentation verändert:

### Pflichtblock

* \[ ] aktuelle autoritative Referenzmenge explizit benennen
* \[ ] ältere Repo-Authority-Dateien nur insoweit fortgelten lassen, wie sie nicht widersprechen
* \[ ] keine entwertete Datei weiterhin als aktive SoT markieren lassen
* \[ ] README-/Onboarding-Funktion für den aktuellen Repo-Zustand benutzbar halten
* \[ ] konkrete Nachweise/Tests für die neue Autoritätshierarchie ausschreiben

\---

## 20\. Pflichtsektion für Input-/Parser-/Zeitlogik-Tickets

Diese Sektion muss **wörtlich oder inhaltlich gleichwertig** in jedes Ticket aufgenommen werden, das neue oder geänderte Input-Contracts einführt:

### Pflichtblock

* \[ ] erlaubte Input-Typen vollständig auflisten
* \[ ] Units pro Input-Typ vollständig auflisten
* \[ ] mehrdeutige Inputs explizit verbieten oder deterministisch regeln
* \[ ] naive DateTimes explizit erlauben oder explizit verbieten
* \[ ] rohe numerische Zeitwerte explizit erlauben oder explizit verbieten
* \[ ] konkrete Valid-/Invalid-/Reject-Tests für diese Fälle ausschreiben

\---

## 21. Documentation-Impact-Check

Der Documentation-Impact-Check ist für alle neu erstellten Codex-Zieltickets nach DOC-C verpflichtend. Er gilt außerdem für bestehende Tickets, die nach DOC-C materiell überarbeitet, neu ausgegeben oder reworked werden, sowie für bestehende Tickets, bei denen Codex ausdrücklich gebeten wird, das Ticket vor der Implementierung zu aktualisieren. Das Ticket muss eine konkrete Entscheidung enthalten, ob Dokumentation betroffen ist und wie damit umgegangen wird.

Bereits vor DOC-C existierende historische/backlog Tickets werden nicht allein dadurch automatisch ungültig, dass ihnen die exakte eigenständige Sektion `## Documentation impact` fehlt. Wenn ein solches älteres Ticket zur Implementierung aufgenommen wird und keine klare Documentation-Impact-Entscheidung enthält, muss Codex dies als Preflight-Gap sichtbar machen und vor der Implementierung eine kleine Ticket-Aktualisierung anfordern oder ergänzen, statt stillschweigend fortzufahren.

### Prüffragen

* [ ] Enthält das Ticket eine eigenständige Sektion `## Documentation impact`?
* [ ] Betrifft das Ticket Architektur, Pipeline-Flow oder Systemstruktur?
* [ ] Betrifft das Ticket Felder, Schemas, Diagnostics, Reports, Snapshots, persistierte Daten oder Output-Semantik?
* [ ] Betrifft das Ticket Runtime, Scheduling, Persistenz, Artefakte, CI oder operative Workflows?
* [ ] Betrifft das Ticket Evaluation, Replay, Backtesting oder Analyse-Outputs?
* [ ] Betrifft das Ticket Documentation Authority, Dokumentrollen, Onboarding, Workflow oder Prozessdokumentation?
* [ ] Falls Dokumentation betroffen ist: sind die betroffenen Dokumente im Ticket konkret genannt?
* [ ] Falls Dokumentation betroffen ist: werden die betroffenen Dokumente im selben PR aktualisiert oder ist ein explizites Follow-up / Out-of-Scope begründet?
* [ ] Falls keine Dokumentation betroffen ist: enthält das Ticket die Formulierung `No canonical documentation update required` mit spezifischer Begründung?

### Abbruchregel

Für neue oder nach DOC-C materiell überarbeitete, neu ausgegebene, reworked oder explizit zur Aktualisierung geöffnete Codex-Zieltickets gilt: Wenn die Sektion `## Documentation impact` im Ticket fehlt, ist das Ticket nicht freigabefähig.

Wenn Variante B (`No canonical documentation update required`) gewählt wird, aber die Begründung leer, generisch oder nicht auf den Ticket-Scope bezogen ist, ist das Ticket nicht freigabefähig.

Wenn das Ticket dokumentationsrelevante Änderungen enthält, aber weder eine Dokumentationsaktualisierung im selben PR noch ein explizit begründetes Follow-up / Out-of-Scope benennt, ist das Ticket nicht freigabefähig.

Für ältere Pre-DOC-C-Backlog-Tickets ohne exakte Sektion gilt: Nicht automatisch invalidieren, aber fehlende oder unklare Documentation-Impact-Entscheidungen als Preflight-Gap behandeln und vor Implementierungsbeginn klären.

\---

## 22\. Freigabe-Gate vor Ticket-Abgabe

Ein Ticket darf erst als **codex-fest** gelten, wenn alle folgenden Fragen mit **Ja** beantwortet sind:

* \[ ] Könnte Codex das Ticket umsetzen, ohne bei Missing-vs-Invalid raten zu müssen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne bei `null` vs `false` raten zu müssen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne bei `NaN`/`inf` raten zu müssen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne Merge-vs-Replace bei Config erraten zu müssen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne not-evaluated-vs-failed zu verwischen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne bei Dokumenten-Autorität oder Repo-Kollisionen zu raten?
* \[ ] Könnte Codex die PR umsetzen, ohne bei Documentation Impact oder betroffenen Current-State-Docs raten zu müssen?
* \[ ] Könnte Codex das Ticket umsetzen, ohne bei Input-Typen, Units, Koerzierung oder Rejection-Semantik raten zu müssen?
* \[ ] Könnte Codex die Tests schreiben, ohne zusätzliche Semantik zu erfinden?
* \[ ] Könnte Codex die PR umsetzen, ohne benachbarte Epics mitzuziehen?
* \[ ] Würde das Ticket keine stillschweigende Konzeptabweichung oder Optimierung einführen, ohne dass diese explizit markiert und mit dem User abgestimmt wurde?

Wenn eine Antwort **Nein** ist, ist das Ticket noch nicht scharf genug.

\---

## 23\. Wiederverwendbare Standardsätze für Tickets

Diese Sätze können fast wörtlich wiederverwendet werden:

### Config

> Partielle Overrides in `<block>` werden feldweise mit zentralen Defaults gemergt; fehlende Unterkeys gelten nicht als invalid. Ungültige Werte erzeugen einen klaren Fehler.

### Numerik

> Nicht-finite numerische Werte (`NaN`, `inf`, `-inf`) gelten als nicht auswertbar und dürfen nicht in numerisch aussehenden Outputs verbleiben.

### Nullability

> `<feld>` ist nullable. `null` bedeutet „nicht belastbar evaluierbar“ und darf nicht implizit zu `false` koerziert werden.

### Status-Trennung

> Nicht evaluierbar / nicht bewertet und fachlich negativ bewertet sind getrennte Zustände und bleiben im Code getrennt erhalten.

### Determinismus

> Bei identischem Input und identischer Config sind Auswahl, Reihenfolge, Status und Gründe identisch.

### Pipeline-Stop

> `<status/klasse>` stoppt vor `<stufe>` und darf keine weiteren Kosten in `<stufe>` auslösen.

### Authority

> Das Ticket darf keine zweite konkurrierende Dokumenten-Autorität erzeugen. Bestehende Repo-Dokumente gelten im betroffenen Bereich nur insoweit fort, wie sie der aktuellen autoritativen Referenzmenge nicht widersprechen.

### Input-Contract

> Erlaubte Input-Typen, Units, Koerzionsregeln und harte Rejection-Regeln sind vollständig spezifiziert. Mehrdeutige Inputs dürfen nicht stillschweigend umgedeutet werden.

\---

## 24\. Schnellprüfung vor Freigabe

Diese Kurzprüfung muss vor Ticket-Abgabe einmal bewusst beantwortet werden:

### Config

* \[ ] Missing key → Default oder Fehler?
* \[ ] Invalid value → klarer Fehler?
* \[ ] Nested override → merge oder replace?

### Numerik

* \[ ] `None` behandelt?
* \[ ] `NaN` behandelt?
* \[ ] `inf` / `-inf` behandelt?
* \[ ] Division durch 0 / quasi-0 behandelt?

### Nullable Felder

* \[ ] Ist das Feld wirklich bool oder tri-state?
* \[ ] Ist `null` semantisch beschrieben?
* \[ ] Bleibt `null` erhalten oder kollabiert fälschlich zu `false`?

### Statuslogik

* \[ ] not evaluated ≠ failed?
* \[ ] unknown ≠ fail?
* \[ ] missing data ≠ negative evaluation?

### Authority / Repo

* \[ ] Ist im betroffenen Bereich eindeutig, welches Dokument/Welche Dokumentmenge autoritativ ist?
* \[ ] Bleibt keine entwertete Datei fälschlich als aktive SoT markiert?
* \[ ] Bleibt das aktuelle Repo-Onboarding benutzbar?

### Inputs / Semantik

* \[ ] erlaubte Input-Typen vollständig genannt?
* \[ ] Units pro Input-Typ vollständig genannt?
* \[ ] mehrdeutige Inputs verboten oder explizit geregelt?
* \[ ] harte Reject-Fälle ausgeschrieben?

### Documentation Impact

* \[ ] `## Documentation impact` vorhanden?
* \[ ] Falls keine Doku betroffen: spezifische Begründung enthalten?
* \[ ] Falls Doku betroffen: betroffene Dateien / Follow-up klar benannt?

### Tests

* \[ ] ein Missing-Key-Test
* \[ ] ein Invalid-Value-Test
* \[ ] ein `NaN`-/`inf`-Test
* \[ ] ein `null`-bleibt-`null`-Test
* \[ ] ein deterministischer Reproduktions-Test
* \[ ] ein Authority-Konsistenz-Nachweis, falls relevant
* \[ ] ein Koerzierung-/Reject-Test, falls relevant

\---

## 25\. Zielzustand

Ein Ticket ist erst dann „codex-fest“, wenn es:

* zur aktuellen autoritativen Referenzmenge passt,
* repo-konsistent mit bestehenden Authority-/Canonical-Dokumenten ist oder deren Entwertung explizit regelt,
* keine zweite Wahrheit erzeugt,
* keine stillen Annahmen enthält,
* deterministisch testbar ist,
* frühere Tickets nicht unbemerkt überschreibt,
* Missing vs Invalid / null vs false / unknown vs fail explizit trennt,
* und Input-Typen / Units / Koerzierung / Rejection-Semantik vollständig festlegt.

## 26\. Ausgabe

Je Ticket eine Datei im Markdown-Format erzeugen und dem User als downloadbare Datei zur Verfügung stellen.

### Pflichtregel

* [ ] Ticket-Entwürfe immer als **Markdown-Datei zum Download** ausgeben
* [ ] Ticket-Entwürfe **nie nur als reinen Text im Chat** ausgeben

Diese Regel gilt für Erstentwürfe, überarbeitete Fassungen, nach Review-Kommentaren korrigierte Fassungen und finale abgestimmte Ticketversionen.

