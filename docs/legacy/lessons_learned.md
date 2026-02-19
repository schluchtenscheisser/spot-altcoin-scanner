# Lessons Learned (Prototyp → Neuaufbau)
Version: v1.0
Language: Deutsch
Audience: Nutzer + GPT

---

## 1. Zweck

Dieses Dokument fasst die Erkenntnisse aus dem bisherigen Prototyp und dem Neuaufbau zusammen.  
Es dient als Referenz dafür:

- was in der alten Logik funktionierte
- was problematisch war
- warum der Neuaufbau strukturell anders ist
- welche Prinzipien sich daraus ergeben

---

## 2. Positive Aspekte des Prototyps

Der alte Prototyp hatte mehrere sinnvolle Designentscheidungen:

1. **MidCap-Fokus**  
   → sinnvoll für Volatilität, Liquidität und asymmetrische Moves

2. **MEXC als reale Börse**  
   → verhindert „nicht handelbare Signale“

3. **Spot-only**  
   → saubere Risiko-Dynamik, kein Derivate-Noise

4. **Volumenbasierte Vorfilterung**  
   → gute Cheap-Filter-Logik für Shortlist

5. **Backtest-Vision**  
   → Grundidee bereits vorhanden (wenn auch nicht stabil)

6. **Iterativer Entwicklungsansatz**  
   → UI/Output war nicht zentral, sondern Analyse

Diese Punkte wurden im Neuaufbau übernommen.

---

## 3. Problematische Aspekte des Prototyps

Mehrere Probleme führten zu Inkonsistenzen oder unbrauchbaren Signalen:

1. **Ein einziger globaler Score**  
   → vermischte völlig unterschiedliche Setup-Typen

2. **Keine Setup-Taxonomie**  
   → Reversals, Breakouts und Pullbacks wurden als „gleich“ behandelt

3. **Überlastung des Scoring-Systems**  
   → Score war zu breit, zu unspezifisch, zu schwer zu kalibrieren

4. **Unklare Feature-Schicht**  
   → Features, Filter und Score wurden vermischt

5. **Instabile Mapping-Logik**  
   → Mapping war zu schwach spezifiziert, führte zu Rate-Limit-Bypass-Logiken und unvollständigen Asset-Sets

6. **Nachträgliche API-Verklebung**  
   → Datenquellen wurden nachträglich kombiniert, statt modular geplant

7. **Keine Snapshot/Backtest-Trennung**  
   → Backtests basierten auf Live-Zuständen → unbrauchbar

8. **Entwicklung ohne Versionierung**  
   → Spezifikation / Config / Score / Code drifteten auseinander

---

## 4. Ursachenanalyse (Warum es scheiterte)

Die Kernursachen lagen nicht im Trading-Ansatz, sondern in der **Architektur**:

- fehlende Setup-Isolation
- fehlende Pipeline-Trennung
- fehlende deterministische Datenmodelle
- fehlende Snapshot-Strategie
- fehlende Feature-Engine
- fehlende Mapping-Schicht

Diese Lücken verhinderten Skalierung und iterative Korrekturen.

---

## 5. Verbesserungen im Neuaufbau

Der Neuaufbau adressiert diese Punkte:

| Problem (alt) | Lösung (neu) |
|---|---|
| Global-Score | 3 unabhängige Setup-Scores |
| Mischlogik | Setup-Taxonomie: Breakout / Pullback / Reversal |
| Featurefehler | getrennte Feature-Engine |
| Instabiles Mapping | deterministische Mapping-Schicht |
| Live-Backtests | Snapshot-basierte Backtests |
| Daten-Bindung | Cheap → Expensive Pipeline |
| Kein Versionsmodell | Spezifikation + Config-Versionierung |
| GPT-Kontextverlust | Snapshot + Code-Map Integration |

---

## 6. Erkenntnisse aus Trading-Perspektive

Trocken extrahiert aus dem Prototyp:

1. **Reversals als Hidden-Alpha**  
   → Setup-Typ mit klarster Asymmetrie

2. **MidCaps hitten besser als Microcaps**  
   → Microcaps verursachten Noise + API-Overhead

3. **Daily-Structure schlägt 1h-Noise**  
   → Setup-Horizont bestätigt

4. **Volume-Spikes sind universell**  
   → Volume ist Setup-agnostischer Bestätigungspunkt

5. **Backtests ohne Snapshot wertlos**  
   → Lesson war teuer, aber entscheidend

---

## 7. Lessons für GPT-Assisted Development

Aus der Prototyp-Phase:

1. GPT darf nie „freien Strukturmodus“ fahren
2. Spezifikation muss vor Coding stehen
3. Code-Map verhindert Refactoring-Chaos
4. Snapshot erlaubt echte Iteration
5. Versionen müssen dokumentiert sein

---

## 8. Lessons für zukünftige Iterationen

Bewährt haben sich:

- Setup-Trennung
- MidCap-Fokus
- USDT-Spot
- MEXC-Handlungsrealität
- Backtests via Snapshots
- Cheap→Expensive Pipeline

Verbesserungen für später:

- Kategorie- und Sektor-Insights
- Regime-Filtration (BTC, ETH)
- Onchain-/TVL-Daten
- Event-erweiterte Breakouts
- Execution-Modul für Research

---

## 9. Fazit

Der Prototyp war **konzeptionell richtig**, aber **architektonisch unzureichend**.  
Der Neuaufbau ist **strukturgetrieben**, **versionierbar**, **GPT-kompatibel** und **backtestfähig**.

Diese Lessons sichern langfristige Iteration ohne Rewrites.

---

## Ende von `lessons_learned.md`
