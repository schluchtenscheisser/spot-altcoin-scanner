# SPEC: Discovery Pipeline Erweiterung – Spot Altcoin Scanner
**Datum:** 2026-01-19  
**Autor:** Spot-Altcoin-Scanner (GPT-5)  
**Status:** ✅ Final Version 0.3 (Architekturangleichung)  

---

## 🧩 Zielsetzung

Erweiterung des bestehenden Spot Altcoin Scanners um eine zusätzliche,  
**vierte Pipeline-Kategorie: Discovery**, zur frühzeitigen Identifikation außergewöhnlicher Marktbewegungen  
(Outlier & Volumenbeschleunigungen).

Die Kategorie **Discovery** läuft **strukturell gleichwertig** zu den bestehenden Pipelines  
**Reversal**, **Breakout** und **Pullback**,  
nutzt aber angepasste Features und eine eigene Scoring-Logik.

---

## ⚙️ Architekturüberblick

### Aktueller Zustand

| Komponente | Beschreibung |
|-------------|---------------|
| `pipeline/features.py` | Berechnung gemeinsamer technischer Metriken (EMA, ATR, RSI etc.) |
| `pipeline/scoring/reversal_scoring.py` | Erkennung potenzieller Trendwechsel |
| `pipeline/scoring/breakout_scoring.py` | Momentum- & Breakout-Detektion |
| `pipeline/scoring/pullback_scoring.py` | Erkennung von Rücksetzern im Aufwärtstrend |
| `pipeline/output.py` | Ausgabe der Reports mit den bisherigen drei Kategorien |

---

### Zielbild (Version 0.3)

| Modul | Änderung | Beschreibung |
|--------|-----------|--------------|
| `pipeline/features.py` | 🔄 erweitert | enthält neue Discovery-Features |
| `pipeline/scoring/discovery_scoring.py` | 🆕 neu | berechnet den DiscoveryScore |
| `pipeline/output.py` | 🔄 erweitert | Reports zeigen vier Kategorien |
| `main.py` | 🔄 erweitert | neuer Modus `--mode discovery` |
| `config/pipeline.yaml` | 🔄 erweitert | Discovery-Kategorie konfigurierbar |

**Discovery wird also vollständig in die bestehende Pipeline-Struktur integriert**,  
nicht als separates Modul geführt.  

---

## 🧠 Funktionsbeschreibung

### 1️⃣ Neue Kategorie: Discovery

**Ziel:**  
Früherkennung potenziell explosiver Moves durch abnormales Volumen-, Preis- oder Orderflow-Verhalten.  

#### Eingangsdaten
- 1h / 4h / 1d OHLCV-Daten (aus `clients/mexc_client.py`, `clients/marketcap_client.py`)
- Optional: Social Buzz (via globale Feature-Schicht `features_buzz.py`)

---

### 2️⃣ Neue Feature-Berechnung (in `pipeline/features.py`)

| Feature | Formel / Beschreibung | Schwelle | Bedeutung |
|----------|----------------------|-----------|------------|
| **VAI (Volume Acceleration Index)** | `VAI = Vol(1h) / SMA(24h Vol)` | > 3 | Relativer Volumenanstieg |
| **VWAP Bias** | `(Price - VWAP) / VWAP` | > 0.02 | institutionelle Akkumulation |
| **ZScore_Price** | `(Close - Mean(24h)) / Std(24h)` | > 1.5 | Preisabweichung über Normalmaß |
| **OB_Imbalance** | `(BidVol - AskVol) / (BidVol + AskVol)` | > 0.6 | starke Kaufdominanz |
| **AA_Score (Anomaly Activity)** | gewichteter Score aus o.g. | > 0.75 | kombiniertes Outlier-Signal |

Diese neuen Funktionen werden als eigene Funktionsblöcke in `features.py` ergänzt,  
nicht in eine neue Datei ausgelagert.

---

## 🔢 Berechnungslogik – DiscoveryScore  
(Implementierung in `pipeline/scoring/discovery_scoring.py`)

### 1️⃣ Eingangsgrößen

| Variable | Beschreibung | Datentyp | Bereich |
|-----------|---------------|-----------|----------|
| `VAI` | Volume Acceleration Index | Float | 0 – ∞ |
| `ZScore_Price` | Preisabweichung vom 24h-Mittel | Float | -∞ – ∞ |
| `OB_Imbalance` | Orderbook-Imbalance | Float | -1 – +1 |
| `VWAP_Bias` | relative Abweichung vom VWAP | Float | -1 – +1 |

---

### 2️⃣ Normalisierung

```python
VAI_norm = min(VAI / 5, 1)
ZScore_norm = min(max((ZScore_Price + 3) / 6, 0), 1)
OB_Imbalance_norm = (OB_Imbalance + 1) / 2
VWAP_Bias_norm = min(max((VWAP_Bias + 0.05) / 0.1, 0), 1)
```

---

### 3️⃣ Gewichtete Aggregation

```python
DiscoveryScore = (
    0.4 * VAI_norm +
    0.3 * ZScore_norm +
    0.2 * OB_Imbalance_norm +
    0.1 * VWAP_Bias_norm
)
```

---

### 4️⃣ Schwellenwerte & Kategorisierung

| Score-Bereich | Bedeutung | Interpretation |
|----------------|------------|----------------|
| 0.00 – 0.39 | Neutral | kein Outlier-Verhalten |
| 0.40 – 0.69 | Beobachtung | mögliche Frühphase |
| 0.70 – 0.84 | **Discovery** | wahrscheinliche Anomalie |
| ≥ 0.85 | **High-Confidence Discovery** | starkes Signal |

---

## 🧾 Reports & Output

`pipeline/output.py` wird so erweitert,  
dass die vier Kategorien **gleichberechtigt** behandelt werden:

```json
{
  "Reversal": [...],
  "Breakout": [...],
  "Pullback": [...],
  "Discovery": [...]
}
```

Markdown-Beispiel:
```markdown
## Top Discovery Coins
| Symbol | Score | Volume Spike | VWAP Bias | OB Imbalance |
|---------|--------|--------------|------------|---------------|
| DUSKUSDT | 0.81 | 4.2x | 0.03 | 0.68 |
| AKROUSDT | 0.74 | 3.1x | 0.01 | 0.72 |
```

---

## 📡 Globale Erweiterung: Buzz-Features

Die Buzz-Daten werden weiterhin **global** integriert (nicht spezifisch für Discovery).

| Feature | Beschreibung |
|----------|---------------|
| `buzz_mentions_delta` | Veränderung der Erwähnungen (24h vs 7d) |
| `buzz_sentiment_score` | Positiv/Negativ-Ratio |
| `buzz_engagement` | Hype-Intensität |

Neues Modul: `pipeline/features_buzz.py`  
→ beeinflusst alle Scoring-Kategorien über den Multiplikator `buzz_multiplier`.

---

## 🔄 Laufzeitintegration

| Komponente | Änderung | Beschreibung |
|-------------|-----------|--------------|
| `main.py` | 🔄 erweitert | `--mode discovery` |
| `pipeline/features.py` | 🔄 erweitert | Discovery-Feature-Funktionen integriert |
| `pipeline/scoring/discovery_scoring.py` | 🆕 neu | Discovery-Score-Berechnung |
| `pipeline/output.py` | 🔄 erweitert | Ausgabe um Discovery ergänzt |
| `pipeline/features_buzz.py` | 🆕 neu | globale Buzz-Schicht |
| `config/pipeline.yaml` | 🔄 erweitert | Discovery aktivierbar |

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

- Logdateien: `logs/scanner_discovery_YYYY-MM-DD.log`
- Features: `data/processed/discovery_features_YYYY-MM-DD.json`
- Reports: `reports/discovery_YYYY-MM-DD.json`

---

## 🚀 Deployment-Hinweis

- Discovery läuft parallel zu den bestehenden Pipelines  
- Aktivierung über `--mode discovery` oder ENV `SCAN_MODE=discovery`
- Buzz-Feature automatisch global verfügbar  

---

## ✅ Nächste Schritte

1. Erweiterung `features.py` um Discovery-Funktionen  
2. Neues Modul `scoring/discovery_scoring.py` erstellen  
3. `output.py` und `pipeline.yaml` erweitern  
4. Logging- und Persistenzpfade hinzufügen  
5. Tests (`tests/test_discovery_pipeline.py`) erstellen  
6. `CODE_MAP.md` aktualisieren  
