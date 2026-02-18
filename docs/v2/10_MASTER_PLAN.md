# Master Plan – Spot Altcoin Scanner (Phase 1)

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Vision
Der Scanner identifiziert täglich **Midcap‑Altcoins** (100M–3B USD Market Cap), die kurzfristig (typisch wenige Tage) ein gutes Chance/Risiko‑Profil haben – mit **Potenzial** von **+10% bis +20%** (gelegentlich darüber), ohne FOMO/Pump‑Chasing.

- **Börse:** MEXC Spot (USDT‑Paare)
- **Tool‑Typ:** Research‑Tool (kein Trading‑Bot)

## Investment‑Kontext (wird berücksichtigt, aber nicht automatisiert)
- **Positionsgröße:** typ. 5k–20k USDT → Tradeability/Slippage wird standardmäßig auf **20k** bewertet
- **Haltedauer:** wenige Tage
- **Risk‑Fenster:** 14 Tage (Unlocks/Status/Delisting)

### Exit‑Idee (nur Kontext)
Der Scanner kennt als Interpretationshilfe:
- 30% bei +10%
- 30% bei +20%
- Rest laufen lassen, solange Chancen intakt sind

> Keine Orderausführung, keine “TP‑Bot‑Logik”. Trade‑Levels sind **Info‑Output**, nicht Ranking‑Input.

## Ziel-Outputs (pro Run)
1) **Global Ranking (Top‑20)** als zusätzlicher Tab  
2) **Setup‑Tabs**: Top‑10 je Setup (Breakout/Pullback/Reversal) bleiben bestehen  
3) **Watchlist**: fast‑valide Kandidaten mit Gründen/Triggern

## Prinzipien
- Gates vor Scores (Hard Gates + Risk Flags)
- Erklärbarkeit (Komponenten/Flags/Reason‑Codes im Report)
- Rate‑Limit‑Robustheit (teure Calls nur Top‑K)
- Paid Daten optional (Tokenomist nicht erforderlich in Phase 1)

## Milestones (High Level)
A) Risk Flags + Setup‑Validität + Anti‑Chase  
B) Liquidity‑Stage (Proxy → Orderbook Top‑K → Re‑Rank)  
C) Cross‑section Normalisierung (`percent_rank`‑Population fix)  
D) Global Ranking + Manifest + Watchlist  
E) Analytics‑Backtest (Potenzial‑Metrik, E2‑K)

## Definition of Done
- Feature‑Spec umgesetzt, Tickets erfüllt
- Golden/Unit Tests vorhanden, CI grün
- Schema‑Änderungen dokumentiert (`schema_version`, `SCHEMA_CHANGES.md`)
- Auto‑Docs (code_map) reflektieren neuen Stand
