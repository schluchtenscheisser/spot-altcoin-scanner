# Test‑Fixtures & Validierungsstrategie (v2) – Canonical

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Ziel
Codex‑sichere Entwicklung: deterministische Golden‑Fixtures + Unit‑Invarianten verhindern Fehlinterpretationen.

## Ordner (Repo‑konform)
- Tests: `tests/`
- Golden: `tests/golden/`
- Golden Fixtures: `tests/golden/fixtures/`

## Must‑have Unit Tests
### 1) EMA & ATR Definitionen
- EMA: SMA‑Seed bei Index `n-1`, Standard‑EMA Rekursion
- ATR: TR‑Definition + Wilder Seed + Wilder Smoothing

### 2) percent_rank Population
- Universe nach Hard Gates (N groß) vs Shortlist (N klein) → percent_rank muss Universe nutzen

### 3) Global Ranking Einmaligkeit & Weights
- Coin mit mehreren Setups → best_setup korrekt, Coin erscheint global nur einmal

### 4) Orderbook Budget (Top‑K)
- Sicherstellen, dass Orderbook‑Fetch <= K pro Run

### 5) Slippage Berechnung
- deterministisches Orderbook‑Fixture → erwartete `slippage_bps` innerhalb Toleranz

### 6) Backtest (E2‑K)
- Trigger innerhalb T_trigger_max
- hit_10/hit_20 korrekt
- no‑lookahead

### 7) Historie‑Gate
- Lege für jedes Setup mindestens zwei Fixtures an:
  1. **Insufficient history:** Die OHLCV‑Serie ist kürzer als die in der Konfiguration definierten `min_history_*`‑Schwellen. `is_valid_setup` muss `False` sein, und das Ergebnis soll den Grund „insufficient history“ enthalten.
  2. **Sufficient history:** Die OHLCV‑Serie erfüllt die Schwellenwerte. Das Setup darf an dieser Stelle nicht aufgrund der Historie invalide werden (andere Gate‑Regeln können natürlich greifen).

## Golden Fixtures (Minimum)
- Setup‑Validity: je Setup valide + invalide + fast‑valide (Watchlist)
- Liquidity Grade: A/B/C/D + “insufficient depth”
- Ranking: confluence + ties
- Backtest: trigger/hit / trigger/no hit / no trigger

## Property / Invarianten
- Closed‑candle only (keine Nutzung der aktuellen Candle in Baselines)
- No‑lookahead (t+1 darf nicht in Features/Score)
- Score Range bleibt 0–100

## Doc↔Code Drift Guard
- Konsistenztests für EMA/ATR und Re‑Rank Regel (Sort Keys) – wenn abweichend: Test fail.
