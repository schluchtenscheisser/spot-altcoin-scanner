# 🧩 SPOT-ALTCOIN-SCANNER — IMPLEMENTIERUNGS-ROADMAP v1.2
*(Fortsetzung nach erfolgreichem Breakout-Fix, Stand: 2026-01-22)*

## 🧭 Kontext

Dieses Projekt (`schluchtenscheisser/spot-altcoin-scanner`) dient der Früherkennung von Momentum-, Breakout- und Reversal-Strukturen bei MEXC-Spot-Altcoins (USDT-Paare).  
Der Scanner erzeugt täglich JSON- und Excel-Reports mit Feature-Scores, die inhaltlich valide Marktinformationen liefern sollen.  

Die aktuelle Version **v1.1** hat folgende Ausgangslage:  

| Komponente | Status | Bemerkung |
|-------------|---------|------------|
| `FeatureEngine` | ✅ stabil (v1.1, NaN-Handling aktiv) | liefert saubere technische Features |
| `scoring/breakout.py` | ✅ korrigiert (lineare Pre-Breakout-Skala) | validiert durch quant- & pro-Trader-Analyse |
| `scoring/reversal.py`, `scoring/pullback.py` | ⚠️ diskrete Schwellen, wenig Differenzierung | noch nicht marktkohärent |
| `pipeline/filters.py`, `pipeline/summary.py` | ⚠️ identische Listen, Zählfehler (48/48/48) | Filter nicht getrennt |
| `validate_features.py` | ⚙️ vorhanden, aber inaktiv | kein automatisches Reporting aktiver Verteilungen |

Ziel der **v1.2-Phase** ist die *inhaltliche Korrektur und Professionalisierung* der Scoring-, Filter- und Validierungsebenen.  
Alle Änderungen müssen **mit der `code_map.md` kompatibel bleiben** und werden **vor Implementierung durch ein professionelles Krypto-Trading-Modell validiert.**

---

## 🧩 Gesamtziele v1.2

1. **Filtertrennung & Summary-Fix:**  
   Jede Setup-Kategorie (Breakout / Reversal / Pullback) soll wieder unabhängig gezählt und gefiltert werden.  
2. **Scoring-Linearisation:**  
   Diskrete Werte (0 / 30 / 100) sollen durch kontinuierliche, marktkohärente Skalen ersetzt werden.  
3. **Base-Detection-Kalibrierung:**  
   Sensitivität der Seitwärts-Erkennung an volatile Marktphasen anpassen.  
4. **Validierungs- und Histogramm-Reports:**  
   Statistische Feature-Verteilung täglich visualisieren (Verteilungs-/Clusteranalyse).  

---

## 🧠 DETAIL-ROADMAP v1.2

### **PHASE 1 – Filter- & Summary-Trennung**

**Ziel:**  
Verhindern, dass `Reversal`, `Breakout` und `Pullback` dieselbe Symbol-Liste teilen.  
Jede Kategorie soll ihre eigene Filterlogik haben, basierend auf individuellen Scoring-Schwellen.

**Betroffene Dateien:**  
- `scanner/pipeline/filters.py`  
- `scanner/pipeline/summary.py`

**Vorgehen:**  
1. In `filters.py` prüfen, ob Funktionen wie  
   ```python
   get_breakout_setups()
   get_reversal_setups()
   get_pullback_setups()
   ```  
   auf denselben `filtered`- oder `shortlist`-Container zugreifen.  
2. Jede dieser Funktionen erhält eigene Schwellenparameter (`score_breakout > x`, `score_reversal > y`).  
3. `summary.py` soll statt einer globalen Liste (`all_setups`) drei getrennte Dictionaries erzeugen.  
4. Ergebnis:  
   - `Breakout Setups Found` ≠ `Reversal Setups Found` ≠ `Pullback Setups Found`  
   - Unterschiedliche Längen im Summary-Sheet  

**Validierung:**  
→ Die Änderung muss durch einen professionellen Krypto-Trader verifiziert werden, um sicherzustellen,  
dass die neue Trennung auch *markttechnisch sinnvoll* segmentiert (z. B. Breakout ≠ Trend-Reversal-Coins).  

---

### **PHASE 2 – Scoring-Linearisation**

**Ziel:**  
Reclaim-, Trend-, Momentum- und Volume-Scores kontinuierlich von 0–100 skalieren,  
statt diskrete Sprungwerte (0 / 30 / 100) zu verwenden.

**Betroffene Dateien:**  
- `scanner/pipeline/scoring/reversal.py`  
- `scanner/pipeline/scoring/pullback.py`  
- `scanner/pipeline/scoring/trend.py`  
- `scanner/pipeline/scoring/volume.py`

**Vorgehen:**  
1. Diskrete Schwellen (z. B. RSI < 30 → 0, RSI > 70 → 100) durch lineare Interpolation ersetzen:  
   ```python
   def linear_scale(value, low, high):
       return np.clip(100 * (value - low) / (high - low), 0, 100)
   ```
2. Momentum → `return_rate` linear zu 0–100 skalieren  
3. Volume → Verhältnis `vol / vol_sma_14` log-transformieren (log2-Normierung)  
4. Trend → EMA-Ratio (EMA20 / EMA50) linear 0–100  
5. Reclaim → Preis-über-EMA-Delta linear statt binär  
6. Prüfen, dass keine NaN-Kaskaden entstehen  

**Validierung:**  
→ Jeder dieser Scores muss durch eine **Trading-Sichtprüfung** validiert werden:  
   - Trend-Score soll in Seitwärtsmärkten < 40 liegen  
   - Momentum > 70 nur bei realem Preis-Impuls  
   - Volume-Score log-verteilt, nicht binär  

---

### **PHASE 3 – Base-Detection-Kalibrierung**

**Ziel:**  
Erkennen von Seitwärtsphasen auch in volatilen Märkten ermöglichen.  
Aktuell zu restriktiv (Range < 5 % → kaum Treffer).

**Betroffene Datei:**  
- `scanner/pipeline/features.py` (`_detect_base()`)

**Vorgehen:**  
1. Toleranzbereich `max(close) / min(close) − 1` von **5 % auf 8 %** erhöhen  
2. Optional: Low-Volatility-Kriterium ergänzen  
   ```python
   if atr_14 / close < 0.03:
       base_score = ...
   ```
3. Score linear auf 0–100 normalisieren (z. B. Range-Ratio 0.02 → 100, 0.08 → 0)

**Validierung:**  
→ Trader-Feedback prüfen: Wird zu viel Seitwärtsrauschen erkannt?  
Falls ja, Rücknahme auf 6 – 7 % Range.  

---

### **PHASE 4 – Validierungsreports**

**Ziel:**  
Tägliche statistische Kontrolle der Feature-Verteilungen  
zur Qualitätsmessung und Early-Warning bei Pipeline-Fehlern.

**Betroffene Datei:**  
- `scanner/tools/validate_features.py` (neu oder erweitern)

**Vorgehen:**  
1. Nach jedem Run automatisch JSON importieren  
2. Für jede Feature-Kategorie (`breakout`, `volume`, `trend`, `momentum`, `base`, `drawdown`)  
   → Histogramme (0–100-Buckets, Count) erzeugen  
3. Ergebnisse in `/validation/YYYY-MM-DD.json` speichern  
4. Optional: Balkenplots mit Matplotlib  

**Validierung:**  
→ Professioneller Trader überprüft Verteilungsform:  
   - 10–20 % der Coins mit Scores > 70  
   - 60–70 % zwischen 30–70  
   - Rest < 30  
   → Nur so ergibt sich ein marktlogisch „atmen­der“ Score-Raum.  

---

### **PHASE 5 – Final Review (Trading-Validation)**

**Ziel:**  
Vor Merge in `main` müssen alle Änderungen fachlich validiert sein.

**Anforderung:**  
1. Quantitativ:  
   - Histogramme zeigen natürliche Streuung  
   - Kein Systemwert dauerhaft = 0 oder 100  
2. Qualitativ (Trader-Review):  
   - Pre-Breakout-Coins zeigen erhöhte Volumen- und Momentum-Scores  
   - Base-Setups in ruhigen Phasen sichtbar  
   - Filter-Trennung ergibt logisch unterschiedliche Coin-Cluster  

Erst nach bestandener Trading-Validierung darf in `main` gemergt werden.  

---

## 🔒 Hinweis zur Vorgehensweise

- **Jede Änderung muss mit `code_map.md` abgeglichen werden**, bevor Variablen oder Funktionsnamen angepasst werden.  
- Max. 3 Dateien / 200 Diff-Zeilen pro Commit.  
- Keine neuen Modulnamen ohne CodeMap-Ergänzung.  
- Kein Commit ohne vorangehende inhaltliche Validierung (fachlich > technisch).
