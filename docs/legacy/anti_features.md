# Anti-Features & Hard Exclusions
Version: v1.0
Language: Deutsch + English (hybrid)
Audience: Developer + GPT

---

## 1. Zweck

Dieses Dokument listet bewusst **nicht implementierte Funktionen**, **konzeptionelle Verbote** und **vermeidungspflichtige Mechaniken**, die während der Prototyp-Phase Probleme verursacht haben oder im Neuaufbau für v1/v2 bewusst ausgeschlossen werden.

Anti-Features sind genauso wichtig wie Features, da sie **Scope creep**, **technischen Overhead**, **Trugsignale** und **Unkalibrierbarkeit** verhindern.

---

## 2. Warum Anti-Features?

Anti-Features dienen dazu:

- Architektur zu schützen
- Scoring konsistent zu halten
- Backtests valide zu halten
- Free-API-Restriktionen einzuhalten
- Iteration nicht zu blockieren
- Fehlentwicklung früh zu unterbinden

---

## 3. Hard Exclusions (v1/v2)

Diese Features werden **hart ausgeschlossen**, bis später ausreichend Architektur vorhanden ist:

### 3.1 Kein „Global Score“
- Setups bleiben strikt getrennt
- keine Fusion, kein Meta-Score, kein Ranking über alle Setups

Reason:
> Mixing → destroys signal integrity, breaks backtests, prevents tuning.

### 3.2 Kein Leverage / Futures
- Spot only
- keine funding-abhängigen Effekte
- keine liquidation-basierten Signals

### 3.3 Keine News/Sentiment Integration (v1)
- CryptoPanic/Twitter/Telegram sind noisy
- erfordern NLP und Filterlogiken
- nicht backtestbar ohne massive Historical-Corpus

### 3.4 Keine AI/ML / Predictive Models (v1)
- keine Klassifikatoren
- keine Regessionsmodelle
- keine RL-Strategien
- keine Feature-Auto-Selection

ML kommt frühestens nach stabilen Backtests.

### 3.5 Keine On-Chain / TVL / DEX Analytics (v1)
- DeFi/Macro Signals optional für v3+

### 3.6 Keine Execution Engine (v1)
- kein Auto-Trade
- kein Order-Routing
- kein Portfolio Management

### 3.7 Keine Portfolio-Optimierung (v1)
- keine Risk/Reward-Allocator
- keine Kelly-Sizing
- keine Markowitz-Runner

---

## 4. Soft Exclusions (Optional Future)

Soft Exclusions sind Features, die technisch sinnvoll wären, aber aktuell **Kosten-/API-/Komplexitätsgründe** haben:

| Feature | Status | Grund |
|---|---|---|
| BTC/ETH Regime Filter | Soft | braucht Market Regime Spec |
| Sector/Category Signals | Soft | braucht Metadata Source |
| Exchange Listing Events | Soft | Kafka-ähnlicher Feed |
| Social Velocity | Soft | braucht Caching + NLP |
| Launchpad/IDO Signals | Soft | nicht stable + nicht bulk |
| Multi-Venue Pricing | Soft | komplexe Arbitrage-Effekte |

---

## 5. Anti-Scoring-Regeln

Der Scanner darf **nicht**:

- Scoring mit „Fear/Greed“ mischen
- Scoring mit Market Cap mischen
- Scoring mit Sentiment mischen
- Scoring mit Orderbook mischen
- Scoring mit Funding mischen

Scoring bleibt **structure-only**.

---

## 6. Anti-Pipeline-Regeln

Pipeline darf **nicht**:

- Futures-Universe mischen
- 1h/5m Noise-Timeframes mischen
- Backtest auf Live-Daten rechnen
- Mapping dynamic rewrites machen

---

## 7. Anti-Backtest-Regeln

Backtests dürfen **nicht**:

- future leakage verwenden
- sentiment rückwärts simulieren
- social feeds retrospektiv modellieren
- stop-loss simulieren ohne Execution-Modul
- portfolios simulieren ohne Allocator

---

## 8. Anti-GPT-Regeln (wichtig)

GPT darf während Entwicklung **nicht**:

- Spec überschreiben ohne Nachfrage
- Code-Map mutieren ohne Nachfrage
- global Score einführen
- Setups fusionieren
- Feature-Schicht mit Scoring fusionieren
- Datenquellen mischen
- API-Clients in Scoring einbauen

Diese Anti-Regeln haben sich im Prototyp als entscheidend erwiesen.

---

## 9. Finanz-Anti-Features

Scanner darf kein:

- Trading-Bot
- Signal-Abo-Service
- Newsletter
- Portfolio-Allocator
- Rendite-Versprechen
- Preis-Prognose
- Investment-Produkt

Der Scanner ist ein **Research-Tool**.

---

## 10. Zusammenfassung

Anti-Features bewahren:

- Klarheit
- Architektur
- Signal-Integrität
- Iterationsfähigkeit
- Backtest-Validität
- GPT-Konsistenz

Sie verhindern Fehler aus der Vergangenheit + Scope-Explosion.

---

## Ende von `anti_features.md`
