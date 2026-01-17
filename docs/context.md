# Persönlicher Kontext & Nutzungsabsicht  
Version: v1.0  
Language: Deutsch (motivational / contextual)  
Audience: Nutzer + GPT  

---

## 1. Zielsetzung & Motivation

Der Scanner wird gebaut, um **kurzfristige Trading-Chancen im Altcoin-Segment** zu identifizieren, die auf Basis von Chartstruktur, Volumen und Marktphase attraktiv erscheinen.

Er ist kein Trading-Bot und keine automatisierte Execution-Engine, sondern ein **Research-/Signal-Tool**, das tägliche Opportunities aufbereitet, die einer menschlichen Entscheidung unterliegen.

---

## 2. Handelsstil & Setup-Präferenzen

- gehandeltes Instrument: **Spot**, kein Leverage
- Börse: **MEXC**
- Quote-Asset: **USDT**
- keine Futures, keine Margin-Produkte
- Anlagehorizont: **wenige Tage bis maximal wenige Wochen**
- Fokus: **asymmetrische Moves**
- bevorzugte Setups:
  - Breakouts mit Volumen
  - Trend-Pullbacks mit Rebound
  - Reversals nach Drawdown + Base

---

## 3. Marktsegment & Asset Restrictions

- Fokus auf **MidCaps** (100M–3B Market Cap)
- keine Microcaps (illiquide, pump-/dump-anfällig)
- keine Mega-Caps (zäh, ineffizient für Kurzfrist-Setups)

Ausschlüsse (bewusst):
- Stablecoins
- Wrapped Tokens
- Leveraged Tokens
- synthetische Produkte
- Futures-only Assets

---

## 4. Warum MidCaps?

MidCaps haben oft die **beste Mischung aus Liquidität, Volatilität und „Entdeckungsphase“**, insbesondere im Altcoin-Markt.  
Sie bewegen sich schneller als Large Caps, aber sind weniger verzerrt als Microcaps.

---

## 5. Warum MEXC?

MEXC wird verwendet als:

- **Handlungsrealität**: dort sollen Signale tatsächlich handelbar sein
- **Datenrealität**: MEXC liefert Spot- und OHLC-Daten zuverlässig
- **Universe-Filter**: Tradeability ist ein zentrales Qualitätskriterium

---

## 6. Warum Spot (und nicht Futures)?

- saubere Risiko-Charakteristik
- keine Funding-Rates
- keine Leverage-Liquidationen
- keine Derivate-Arbitrage-Effekte
- Signalqualität eher „technisch“ als „mechanisch“
- kürzerer Setup-Horizont ohne Zwangsexit

---

## 7. Warum täglicher Scan?

Der Zeithorizont „Tage bis wenige Wochen“ profitiert stark von:

- **Daily Structure**
- **Daily Highs/Lows**
- **Daily Volume Context**
- **Daily Trend Breaks**

4h-Daten dienen dem Feinschliff, aber 1d ist die Leitstruktur.

---

## 8. Beispielhafte Ziel-Patterns

Der Scanner soll **Trades entdecken wie**:

> Humanity Protocol (H) im Dezember:  
> Drawdown → Base → Reclaim + Volume → 2–3× Move

Diese Klasse von Moves ist weder reiner Breakout noch klassischer Pullback, sondern eine **strukturierte Reversal-Transition**.

---

## 9. Rolle der 3 Setup-Kategorien

Die 3 Kategorien repräsentieren unterschiedliche Risiko/Timing-Profile:

| Setup | Charakter | Risiko | Chance | Timing |
|---|---|---|---|---|
| Breakout | sofortiges Momentum | hoch | hoch | früh |
| Pullback | Trend-Continuation | moderat | moderat | später |
| Reversal | Trendwechsel | hoch | sehr hoch | früh bis mittel |

Es gibt bewusst **keinen globalen Score**, da dieser Trading-Logiken verwässert.

---

## 10. Wofür das Tool _nicht_ gedacht ist

- kein Autotrading
- kein Portfolio Management
- keine News-Aggregation
- keine Onchain-Analyse
- keine Sentiment-Engine
- keine Fundamentalanalyse

Die Stärke ist **technische Signalidentifikation + Struktur + Kontext**.

---

## 11. Erwartete Entwicklung

Das Tool soll iterativ verfeinert werden durch:

1. Verbesserte Scoring-Logik
2. empirische Backtests (Forward Returns)
3. Performance-Monitoring
4. Erweiterung der Feature-Palette
5. Kontrolle von False Positives/Negatives
6. Feedback-Loops durch tägliche Review

---

## 12. Persönliche Erfolgsdefinition

Das Tool gilt als „gut“, wenn es:

- relevante Kandidaten surfaced
- Reversal-Opportunities früh erkennt
- Pullbacks in Trends zuverlässig zeigt
- Breakouts filtern kann, ohne Promos/Noise zu füttern
- stabil im Betrieb ist
- über Wochen/Monate **Value generiert**, nicht als einmalige Aktion

---

## 13. Zwischenfazit

Der Kontext rechtfertigt die Trennung von:

- USDT-Spot only
- MEXC only
- MidCaps only
- 3 Setup-Scores
- täglicher Run
- Backtestbarkeit

und begründet, warum diese Struktur optimal ist für einen Stil wie:

> „kurzfristig, opportunistisch, technisch, liquiditätsbewusst, asymmetrisch“  

---

## Ende von `context.md`
