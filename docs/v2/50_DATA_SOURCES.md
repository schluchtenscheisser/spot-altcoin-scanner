# Datenquellen (v2) – Canonical

**Status:** Canonical v2 (für GPT‑Codex)  
**Datum:** 2026-02-18  

## Prinzip
Free‑First. Paid‑Quellen sind optional und dürfen Phase‑1‑Runs nicht blockieren.

## 1) MEXC (primär)
- Exchange Info (Symbole/Status)
- 24h Ticker (`quoteVolume`)
- OHLCV/Klines (1D, 4H)
- Orderbook/Depth (für Slippage) **nur Top‑K**

Rate‑Limit‑Strategie:
1) Proxy‑Pre‑Rank (cheap)
2) Orderbook nur Top‑K (expensive)
3) Slippage/Grade berechnen
4) Re‑Rank → Top‑20

## 2) CoinMarketCap (CMC)
- Zweck: Market Cap Universe (100M–3B) + Meta (u. a. `date_added`)
- **Entscheidung Option 1:** `run_mode=standard` erfordert CMC API Key

## 3) Symbol‑Mapping
- Exchange‑Symbol ≠ CMC‑Symbol (Ambiguität)
- Mapping muss Overrides/Logging haben (keine “magischen” Heuristiken ohne Report)

## 4) Manuelle Listen (Phase 1)
- `config/denylist.yaml` (Hard Exclude)
- `config/unlock_overrides.yaml` (major/minor, 14d Fenster)

## 5) Tokenomist (optional / später)
- Darf Phase 1 nicht blockieren
- Nur additive Flags/Confidence

## 6) Discovery Tag (ohne Paid‑Zwang)
- Primary: CMC `date_added` (wenn verfügbar)
- Fallback: `first_seen_ts` = älteste 1D Candle

## 7) Reproduzierbarkeit
- Reports enthalten Manifest (Commit‑Hash, Config‑Hash, Schema‑Version, AsOf)
- Caching wo möglich; keine Secrets in Artefakten
