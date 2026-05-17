Es ist wichtig, zwischen drei Kategorien zu unterscheiden: was **naheliegend und realistisch** ist, was **mehr Aufwand** erfordert, und was echte **professionelle Tiefe** bringt, aber auch entsprechend komplex wird.

---

## 1) Was als nächstes ohnehin kommt — und direkt zur Signalqualität beiträgt

**Forward-Return-Validierung (T30)**
Das ist der wichtigste nächste Schritt überhaupt. Das System identifiziert Kandidaten — aber ob diese Kandidaten tatsächlich besser performen als der Zufall, ist bisher empirisch nicht belegt. T30 schließt genau diese Lücke: für jeden ausgegebenen Kandidaten wird nachträglich gemessen, was der Kurs in den nächsten 1, 3, 7 Tagen gemacht hat. Erst damit lässt sich beurteilen, welche Bucket-Kategorien, Setups und Execution-Klassen wirklich etwas taugen — und welche rausgeworfen werden sollten.

Ohne diese Validierung ist jede weitere Optimierung am System im Grunde Raten. Mit ihr wird das System lernfähig.

**Überdehnungs-Filterung**
Schon teilweise implementiert (Entry-Location-Check gegen die 4h-EMA). Was noch fehlt: ein einfacher Short-Return-Filter — also die Frage, ob ein Coin in den letzten 3–7 Tagen bereits stark gelaufen ist. Viele Fehlsignale entstehen nicht weil die Logik falsch ist, sondern weil der Entry schlicht zu spät kommt. Das ist kein komplexes Feature, hat aber direkten Einfluss auf die Trefferquote.

---

## 2) Realistisch ergänzbar mit überschaubarem Aufwand

**BTC-Regime als Kontext-Filter**
Der Markt verhält sich in Risk-On-Phasen (BTC stabil oder steigend) fundamental anders als in Risk-Off-Phasen. Ein einfacher Regime-Indikator auf BTC — nicht als Scoring-Faktor, sondern als binärer Kontext-Filter — würde viele Situationen herausfiltern, in denen technisch gute Setups trotzdem nicht funktionieren, weil der Gesamtmarkt dagegen läuft. Professionelle Systeme machen das standardmäßig. Es ist kein großer Baustein, aber ein wirkungsvoller.

**Korrelations-Filterung**
Wenn das System täglich 10 Kandidaten ausgibt und 7 davon Layer-1-Coins mit ähnlicher Marktstruktur sind, ist das Portfolio de facto nicht diversifiziert — man hat dasselbe Risiko mehrfach. Ein einfacher Post-Processing-Schritt, der stark korrelierte Kandidaten innerhalb desselben Buckets erkennt und nur den stärksten behält, verbessert die praktische Nutzbarkeit erheblich.

**Token-Qualitäts-Filter**
Listing-Alter, Handelsvolumen-Konsistenz, ob es Unlock-Events gibt — das sind Informationen, die öffentlich verfügbar sind und helfen, strukturell riskante Kandidaten früh auszusortieren. Ein junger Coin mit fraglichem Volumen sieht technisch manchmal gut aus, ist aber ein anderes Risikoprofil als ein etablierter MidCap.

---

## 3) Was echte professionelle Tiefe bringt — aber auch den Aufwand deutlich steigert

**Definierte Exit-Logik**
Das ist der größte strukturelle Unterschied zu professionellen Systemen: die haben nicht nur Entry-Signale, sondern vollständige Trade-Pläne — wann wird Gewinn mitgenommen, wann wird der Trade gecancelt, wie entwickelt sich der Stop mit dem Kurs. Ohne Exit-Logik hängt die tatsächliche Performance zu sehr von manuellen Entscheidungen ab. Eine regelbasierte Exit-Systematik — auch wenn sie simpel beginnt — würde die Auswertbarkeit und die Reproduzierbarkeit der Ergebnisse dramatisch verbessern.

**Orderflow- und Volumen-Profil-Analyse**
Statt nur Orderbook-Tiefe zu prüfen, schauen professionelle Systeme auf Orderflow — also wer kauft und wer verkauft, auf welchem Preisniveau sich Volumen angesammelt hat, und ob eine Bewegung von echtem Kaufdruck getragen wird oder nur von dünnem Markt. Das ist technisch komplexer, aber ein echter Qualitätsfilter für Breakout- und Reversal-Setups.

**Systematisches Regime-Backtesting**
Nicht nur validieren, ob Signale funktioniert haben — sondern in welchem Marktregime sie funktioniert haben. Ein Signal, das in Bull-Phasen eine 70% Trefferquote hat und in Bear-Phasen eine 30%, ist ein gutes Signal mit falschem Einsatzzeitpunkt — kein schlechtes Signal. Dieses Wissen erlaubt es, das System selektiv einzusetzen, statt es blind zu laufen.

---

## Die ehrliche Priorisierung

Wenn es um Ergebnisqualität geht, ist die Reihenfolge klar:

Erst **Forward-Return-Validierung** — ohne Daten über tatsächliche Outcomes ist jede weitere Optimierung blind. Dann **Überdehnungs-Filterung** und **BTC-Regime-Kontext** — beide haben hohes Impact-to-Effort-Verhältnis. Dann **Exit-Logik** — weil das der Punkt ist, an dem aus einem guten Signal ein reproduzierbarer, auswertbarer Trade wird.

Der Rest ist wertvoll, aber setzt voraus, dass die Grundlage sitzt.
