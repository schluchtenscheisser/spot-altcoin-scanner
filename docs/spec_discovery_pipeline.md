
# SPEC: Discovery Pipeline Erweiterung – Spot Altcoin Scanner
**Datum:** 2026-01-19  
**Autor:** Spot-Altcoin-Scanner (GPT-5)  
**Status:** Draft  
**Version:** 0.1  

---

## 🧩 Zielsetzung

Erweiterung des bestehenden Spot Altcoin Scanners um eine zusätzliche, **parallele Discovery-Pipeline** zur frühzeitigen Identifikation von außergewöhnlichen Marktbewegungen (Outlier & Volumenbeschleunigungen).  
Diese Pipeline ergänzt die bestehenden drei Kategorien (Reversal, Breakout, Pullback) um eine **vierte Kategorie: Discovery**.  

---

## ⚙️ Architekturüberblick

### Aktueller Zustand

| Komponente | Beschreibung |
|-------------|---------------|
| `scoring/reversal.py` | Erkennung potenzieller Trendwechsel |
| `scoring/breakout.py` | Momentum- & Breakout-Detektion |
| `scoring/pullback.py` | Erkennung von Rücksetzern im Aufwärtstrend |
| `pipeline/features.py` | Berechnung technischer Metriken (EMA, ATR, RSI, etc.) |
| `pipeline/output.py` | Ausgabe der Reports mit den drei bisherigen Kategorien |

### Zielbild

Erweiterung um:
- neue Kategorie **Discovery**, die unabhängig, aber strukturell gleichwertig zu den drei bestehenden läuft.
- neue Metriken in `features_discovery.py`
- neue Scoring-Logik in `scoring/discovery.py`
- aktualisierte Reports mit 4 Kategorien (`Reversal`, `Breakout`, `Pullback`, `Discovery`).

---

## 🧠 Funktionsbeschreibung

### 1. Neue Kategorie: Discovery

**Ziel:** Früherkennung potenziell explosiver Moves durch abnormales Volumen-, Preis- oder Orderflow-Verhalten.

#### Eingangsdaten
- 1h / 4h / 1d OHLCV-Daten (aus `clients/mexc_client.py` / `clients/marketcap_client.py`)
- Optional: Social Buzz (siehe separaten Punkt unten)

#### Berechnete Features (neu in `pipeline/features_discovery.py`)

| Feature | Formel / Beschreibung | Schwelle | Bedeutung |
|----------|----------------------|-----------|------------|
| **VAI (Volume Acceleration Index)** | `VAI = Vol(1h) / SMA(24h Vol)` | > 3 | Relativer Volumenanstieg |
| **VWAP Bias** | `(Price - VWAP) / VWAP` | > 0.02 | institutionelle Akkumulation |
| **ZScore_Price** | `(Close - Mean(24h)) / Std(24h)` | > 1.5 | Preisabweichung über Normalmaß |
| **OB_Imbalance** | `(BidVol - AskVol) / (BidVol + AskVol)` | > 0.6 | starke Kaufdominanz |
| **AA_Score (Anomaly Activity)** | gewichteter Score aus o.g. | > 0.75 | kombiniertes Outlier-Signal |

#### Scoring-Modul (`scoring/discovery.py`)

**Eingabe:** Feature DataFrame  
**Ausgabe:** DiscoveryScore ∈ [0, 1]

**Formel:**
```
DiscoveryScore = w1*VAI + w2*ZScore_Price + w3*OB_Imbalance + w4*VWAP_Bias
```
mit Standardgewichten w1=0.4, w2=0.3, w3=0.2, w4=0.1  

Coins mit Score > 0.7 → Discovery-Kandidaten.

---

## 🧾 Reports & Output

### Anpassung in `pipeline/output.py`

Neues Ausgabeformat:  
```json
{
  "Reversal": [...],
  "Breakout": [...],
  "Pullback": [...],
  "Discovery": [...]
}
```
Alle vier Kategorien werden parallel behandelt und in den Reports (`reports/YYYY-MM-DD.json`, `.md`) dargestellt.

### Beispielausgabe (Markdown)

```markdown
## Top Discovery Coins
| Symbol | Score | Volume Spike | VWAP Bias | OB Imbalance |
|---------|--------|--------------|------------|---------------|
| DUSKUSDT | 0.81 | 4.2x | 0.03 | 0.68 |
| AKROUSDT | 0.74 | 3.1x | 0.01 | 0.72 |
```

---

## 📡 Erweiterung: Buzz-Abfrage (separat)

Die Social Buzz-Integration betrifft **alle Kategorien** und wird daher als **globale Feature-Schicht** implementiert.  
Sie läuft unabhängig von der neuen Discovery-Pipeline.

### Neues Modul
`features_buzz.py`

### Quellen
- LunarCrush API (Social Engagement, Mentions, Sentiment)
- Reddit/Telegram (via RSS)
- Google Trends API (optionale Ergänzung)

### Berechnete Metriken
| Feature | Beschreibung | Verwendung |
|----------|---------------|-------------|
| `buzz_mentions_delta` | Veränderung der Erwähnungen 24h vs 7d | Trendverstärker |
| `buzz_sentiment_score` | Positiv/Negativ-Ratio | Risikoanpassung |
| `buzz_engagement` | Likes + Retweets normalisiert | Hype-Intensität |

### Integration
Buzz-Daten werden als zusätzliche Spalte in das globale Feature-Set eingespeist (`merged_features.json`)  
und beeinflussen alle Scores über den Faktor `buzz_multiplier`.

---

## 🔄 Laufzeitintegration

| Pipeline | Neu | Beschreibung |
|-----------|-----|--------------|
| `main.py` | ✅ | Option `--mode discovery` |
| `__init__.py` | ✅ | Discovery-Import hinzufügen |
| `features_discovery.py` | 🆕 | neue Feature-Berechnung |
| `scoring/discovery.py` | 🆕 | neue Scoring-Logik |
| `output.py` | 🔄 | vierte Kategorie ergänzen |
| `features_buzz.py` | 🆕 | globale Buzz-Integration |

---

## 🧮 Scoring-Zusammenfassung

| Kategorie | Typ | Bewertungslogik | Hauptindikatoren |
|------------|------|------------------|------------------|
| Reversal | Trendwechsel | Baseline Reclaim + RSI | EMA, RSI |
| Breakout | Momentum | Preis/Volumen-Expl. | ATR, EMA |
| Pullback | Trend-Fortsetzung | Retest mit Momentum | Fib, EMA |
| **Discovery** | Outlier/Frühwarnung | Volumen + Preis-Anomalien | VAI, ZScore, VWAP |

---

## 🧱 Persistenz & Logging

- Neue Logdateien: `logs/scanner_discovery_YYYY-MM-DD.log`
- Features: `data/processed/discovery_features_YYYY-MM-DD.json`
- Ergebnisse: `reports/discovery_YYYY-MM-DD.json`

---

## 🚀 Deployment-Hinweis

- keine Konflikte mit bestehender Pipeline (läuft parallel)
- kann über `--mode discovery` oder `SCAN_MODE=discovery` aktiviert werden
- Buzz-Feature automatisch global verfügbar, unabhängig vom Modus

---

## ✅ Nächste Schritte

1. Modul `features_discovery.py` implementieren  
2. Scoring `scoring/discovery.py` entwickeln  
3. Anpassung `output.py` (neue Kategorie)  
4. Logging- und Persistenzrouten anlegen  
5. Tests (`tests/test_discovery_pipeline.py`) hinzufügen  
6. Dokumentation in `CODE_MAP.md` aktualisieren  
