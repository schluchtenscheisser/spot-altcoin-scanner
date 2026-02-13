# Verbesserungen mit zusätzlichen Daten (neue Endpoints/Quellen)

## Feature: `close` / `high` / `low` / `volume`
- Orderbook-Depth (Bid/Ask), Slippage-Schätzer, Spread
- Trades (Aggressor Volume) → Buy/Sell Pressure statt nur Candle-Volume
- Venue-Split (CEX vs DEX Volume)

---

## Feature: `r_1` / `r_3` / `r_7`
- Markt-Beta/Regime: BTC Dominance, Total Market, Sector Indizes
- News/Social Sentiment (Narratives) → Momentum-Qualität vs „Noise“

---

## Feature: `ema_20` / `ema_50`
- Derivatives-Regime: Funding Rate, Open Interest (OI), Liquidations → Trend „gesund“ vs „leveraged“

---

## Feature: `dist_ema20_pct` / `dist_ema50_pct`
- Options/Implied Volatility (IV) (wo verfügbar) → Overextension-Risiko
- Positioning-/Flow-Daten (z.B. Exchange Netflows)

---

## Feature: `atr_pct`
- Implied Volatility / Derivatives Vol (wo verfügbar) → ATR vs IV Divergenzen
- Volatility Surface / Skew (bei größeren Coins)

---

## Feature: `volume_sma_14`
- Real Volume (wash-trade bereinigt) / Exchange Quality Scores
- On-chain Volume / DEX Volume (zur Bestätigung echter Nachfrage)

---

## Feature: `volume_spike`
- CVD (Cumulative Volume Delta) / Aggressor Flow
- OI + Funding + Liquidations zur Unterscheidung:
  - Spot-Accumulation vs Short/Long Squeeze

---

## Feature: `hh_20`
- Orderbook + Trades: Breakout „echter Bid“ vs Wick-only
- Perp-Daten: Breakout getrieben durch Liquidations?

---

## Feature: `hl_20`
- On-chain Exchange Inflows/Outflows (Supply-Druck vs Accumulation)
- Holder/Whale Activity (Wallet Concentration/Flows)

---

## Feature: `breakout_dist_20` / `breakout_dist_30`
- Intraday Trigger-Qualität: Orderbook-Imbalance, Tape Speed
- Perp-Daten (Funding/OI/Liquidations) als Breakout-Quality Filter

---

## Feature: `drawdown_from_ath`
- Echtes ATH seit Listing (längere Historie / Datenprovider)
- Supply-Daten / Unlock-Schedules (Tokenomics) → Drawdown-Interpretation

---

## Feature: `base_score`
- On-chain Accumulation-Indikatoren (Exchange Netflows, Active Addresses)
- Social/News + Catalyst Kalender (Listings, Unlocks, Releases)
- Futures Positioning (OI/Funding) → Base „loaded“ vs „clean“
