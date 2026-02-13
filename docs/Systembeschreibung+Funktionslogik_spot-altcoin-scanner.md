# SPOT ALTCOIN SCANNER

## Systembeschreibung & Funktionslogik (v1 – Vollständige Analyse)

---

# 1. Zweck des Systems

Der Spot Altcoin Scanner ist ein deterministisches Research-System zur Identifikation kurzfristiger Trading-Setups im MidCap-Altcoin-Segment auf MEXC Spot USDT-Märkten.

Er ist:

* kein Trading-Bot
* kein Prognosemodell
* kein ML-System
* kein Execution-System

Er ist ein strukturierter Setup-Scanner mit täglicher Ausführung.

Ziel:

> Systematisch asymmetrische Marktstrukturen erkennen, bevor Momentum einsetzt.

---

# 2. Strategischer Rahmen

Das Tool fokussiert sich ausschließlich auf:

* Exchange: MEXC
* Markt: Spot
* Quote Asset: USDT
* Segment: MidCaps (100M – 3B Market Cap)

Warum?

* Microcaps → zu illiquide / pumpanfällig
* Large Caps → zu träge
* Futures → anderes Risiko-Profil
* MidCaps → beste Kombination aus Volatilität + Liquidität

---

# 3. Gesamtarchitektur

## High-Level Pipeline

Täglicher deterministischer Ablauf:

1. Fetch MEXC Universe (alle USDT Spot Paare)
2. Fetch Market Cap Daten (CoinMarketCap)
3. Mapping: MEXC Symbol → Market Cap Asset
4. Hard Filters (Gates)
5. Cheap Pass (Ticker-basierte Vorauswahl)
6. Expensive Pass (OHLCV + Feature-Berechnung)
7. Setup-spezifisches Scoring (3 getrennte Systeme)
8. Report Generierung (Markdown + JSON)
9. Snapshot Speicherung
10. Optional: Backtest Auswertung auf historischen Snapshots

Wichtig:
Es gibt keinen globalen Score.
Jede Setup-Art wird unabhängig behandelt.

---

# 4. Datenquellen

## 4.1 MEXC API

Verwendet für:

* Universe Definition
* 24h Volumen
* OHLCV Daten (1D + 4H)

Design-Prinzip:
Bulk-Fetching + Caching → API-Limit-freundlich

---

## 4.2 CoinMarketCap API

Verwendet für:

* Market Cap
* Asset-Validierung
* Filterung nach Segment

Nur 1 Bulk-Call pro Tag (Free Tier kompatibel)

---

## 4.3 Snapshot-System

JSON-Snapshots speichern:

* Rohdaten
* Features
* Scores
* Mapping
* Metadaten

Warum?

→ Determinismus
→ Backtesting
→ Reproduzierbarkeit
→ Versionierbarkeit

---

# 5. Mapping Layer (kritischer Bestandteil)

MEXC verwendet Exchange-spezifische Ticker.

Beispiel:
HNTUSDT → muss korrekt dem HNT Asset zugeordnet werden.

Das Mapping-System:

* führt Symbol-basierte Zuordnung durch
* erkennt Kollisionen
* erlaubt Overrides
* speichert Confidence-Level
* blockiert Assets bei Mapping-Unsicherheit

Warum kritisch?

Falsches Mapping = falsche Market Cap = falsche Filter = falsches Scoring

Das Mapping wird durchgeführt bevor OHLCV geladen wird (Kostenreduktion).

---

# 6. Hard Filters (Gate-System)

Assets werden vor Scoring entfernt, wenn sie:

1. Kein MEXC Spot USDT Pair haben
2. Market Cap < 100M oder > 3B
3. 24h Quote Volume unter Schwellwert
4. Nicht genügend Historie besitzen
5. Stablecoins / Wrapped / Leveraged Tokens sind

Warum Gate-System?

* Performance (Cheap before Expensive)
* Vermeidung von Garbage-Daten
* Signalqualität erhöhen
* API-Kosten senken

Assets, die hier scheitern, werden nie gescored.

---

# 7. Cheap Pass vs Expensive Pass

## Cheap Pass

Verwendet nur:

* Ticker
* 24h Volume
* Market Cap

Ziel:

Top ~100 Kandidaten für Expensive Pass selektieren.

Warum?

OHLCV für 1800+ Assets wäre ineffizient.

---

## Expensive Pass

Lädt:

* 1D OHLCV
* 4H OHLCV

Berechnet Features:

* EMA
* Drawdown vom ATH
* ATR
* Relative Volume
* Range Highs
* Pullback Struktur
* Base Formation
* Trendstruktur

Erst danach beginnt Scoring.

---

# 8. Feature Engineering

Features sind deterministisch und rein technisch.

Typische Komponenten:

* EMA Distanz (Trend-Position)
* ATH Drawdown
* Volumen Expansion
* ATR Normalisierung
* Breakout Range Level
* Pullback Tiefe
* Base-Länge
* High/Low Struktur

Warum Feature-Entkopplung?

→ Scoring bleibt modular
→ Feature-Wiederverwendung möglich
→ Backtesting transparenter

---

# 9. Setup Taxonomie

Der Scanner unterscheidet 3 unabhängige Setup-Typen:

---

## 9.1 Breakout

Definition:

Range Break + Volumen Expansion

Typische Kriterien:

* Mehrfach getestetes Widerstandslevel
* Frischer Range Break
* Volumen Spike
* Momentum-Aufbau

Ziel:

Früher Einstieg in neue Impulsbewegung.

---

## 9.2 Trend Pullback

Definition:

Etablierter Trend + Retracement + Rebound

Typische Kriterien:

* EMA Trend intakt
* Pullback 20–60 Tage
* Higher Low Struktur
* Re-Acceleration

Ziel:

Continuation statt Reversal handeln.

---

## 9.3 Reversal (Priorität)

Definition:

Downtrend → Base → Reclaim + Volumen

Typische Kriterien:

* 60–365 Tage Drawdown
* Seitwärts-Basenbildung
* EMA Reclaim
* Volumenanstieg

Ziel:

Frühe Trendwende erkennen.

Warum Priorität?

Reversals bieten höchste Asymmetrie.

---

# 10. Scoring Framework

Jeder Setup-Typ besitzt:

* Eigenes Modul
* Eigene Gewichtung
* Eigene Komponenten
* Eigenes Ranking

Scores:

* Normalisiert 0–100
* Komponenten-gewichtet
* Mit Penalties
* Mit erklärbaren Sub-Scores

Es gibt:

KEIN globales Combined Score.

Warum?

* Setup-Typen sollen sich nicht gegenseitig verzerren
* Verhindert Bias
* Erhöht Interpretierbarkeit

---

# 11. Output-System

## 11.1 Markdown Report

Enthält:

* Top Breakouts
* Top Pullbacks
* Top Reversals
* Komponenten-Scores
* Analyse-Text
* Begründungen

Human-readable.

---

## 11.2 JSON Report

Enthält:

* Rohdaten
* Features
* Scores
* Flags
* Mapping
* Meta-Info

Machine-readable.

---

## 11.3 Snapshot

Gespeichert unter:

snapshots/runtime/YYYY-MM-DD.json

Enthält vollständige Run-Daten.

Warum?

→ Backtest
→ Audit
→ Version-Vergleich

---

# 12. Backtesting System

Backtests werden nicht live gerechnet.

Sie nutzen gespeicherte Snapshots.

Berechnet:

* 7d Forward Return
* 14d Forward Return
* 30d Forward Return
* Hit Rate
* Median Return
* Tail Loss

Warum Snapshot-basiert?

* Keine Lookahead Bias
* Keine Live-API-Abhängigkeit
* Voll reproduzierbar

---

# 13. Determinismus

System ist deterministisch:

* Gleiche Inputs → gleiche Outputs
* Keine Randomness
* Versionierte Konfiguration
* Versionierte Scoring-Logik
* Snapshot-Versionierung

Warum wichtig?

* Forschung
* Vergleichbarkeit
* Iteratives Fine-Tuning

---

# 14. Performance-Charakteristik

Typischer Lauf:

* 1837 Assets initial
* ~400 nach Filtern
* ~100 im Expensive Pass
* ~40–50 je Setup scored
* Laufzeit: 4–5 Minuten

API Usage:

* MEXC: gecached
* CMC: 1 Call / Tag

---

# 15. Designprinzipien

1. Cheap before Expensive
2. Setup-Separation
3. Free-API-kompatibel
4. Deterministisch
5. Modular
6. Snapshot-first
7. Kein ML
8. Keine Execution

---

# 16. Nicht-Ziele

Das Tool ist nicht:

* Ein Portfolio-Allocator
* Ein Risk-Manager
* Ein ML-Predictor
* Ein Regime-Model
* Ein On-Chain Analyzer
* Ein News-Sentiment-Scanner

---

# 17. Kritische Schwachstellen (Analyse)

Aus Systemlogik ableitbar:

1. Mapping-Fehler = systemische Verzerrung
2. Fixe Market Cap Range (keine Regime-Anpassung)
3. Keine BTC/ETH Regime-Filter
4. Keine Volatilitäts-Regime-Erkennung
5. Kein Liquidity Depth Check (nur 24h Volume)
6. Keine Multi-Timeframe Alignment beyond 1D + 4H
7. Keine Portfolio-Korrelation Analyse
8. Keine adaptive Gewichtung
9. Keine Feature-Importance Analyse
10. Kein ML-Sanity-Check gegen historische Outperformance

---

# 18. Optimierungspotenziale

Potenzielle nächste Evolutionsstufen:

* Regime Detection (BTC Trend Filter)
* Volatility Clustering
* Dynamic Market Cap Bands
* Liquidity Quality Score
* Orderbook Depth Snapshot
* Feature Drift Monitoring
* Auto Weight Calibration via Backtests
* Regime-conditional Scoring
* False Positive Pattern Mining
* ML Meta-Ranker (nur als Overlay, nicht Kernsystem)

---
