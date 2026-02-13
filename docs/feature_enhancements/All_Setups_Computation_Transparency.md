# Spot Altcoin Scanner

# Computation Transparency -- All Setups

Generated: 2026-02-13T09:22:50.818314

------------------------------------------------------------------------

# 1. Data Layer

For each asset a and timeframe tf ∈ {1D, 4H}, OHLCV klines:

k_i = (open_i, high_i, low_i, close_i, volume_i, quoteVolume_i,
closeTime_i)

Only candles with:

closeTime_i \<= asof_ts_ms

If asof_ts_ms is None: last available candle is used.

Minimum required candles per timeframe: 50

------------------------------------------------------------------------

# 2. Feature Calculations (Common to All Setups)

## 2.1 Returns

r_n = ((C_t / C\_(t-n)) - 1) \* 100

Used: r_1, r_3, r_7

## 2.2 EMA

alpha = 2 / (n + 1)

EMA_0 = mean(first n closes)

EMA_t = alpha \* C_t + (1 - alpha) \* EMA\_(t-1)

Used: EMA_20, EMA_50

DistEMA_n = ((C_t / EMA_n) - 1) \* 100

## 2.3 ATR% (Wilder, n=14)

TR_i = max( H_i - L_i, abs(H_i - C\_(i-1)), abs(L_i - C\_(i-1)) )

ATR_0 = mean(TR_1 ... TR_14)

ATR_t = ((ATR\_(t-1) \* 13) + TR_t) / 14

ATR_pct = (ATR_t / C_t) \* 100

## 2.4 Volume

SMA_14 = mean(V\_(t-14) ... V\_(t-1))

VolumeSpike = V_t / SMA_14

## 2.5 Higher High / Higher Low

HH_20 = max(H\_(t-4:t)) \> max(H\_(t-20:t-5))

HL_20 = min(L\_(t-4:t)) \> min(L\_(t-20:t-5))

## 2.6 Drawdown

Lookback L = config.features.drawdown_lookback_days (default 365)

ATH_t = max(C_(t-L+1) ... C_t)

Drawdown = ((C_t / ATH_t) - 1) * 100

------------------------------------------------------------------------

# 3. Reversal Scoring

Weights:

drawdown = 0.30 base = 0.25 reclaim = 0.25 volume = 0.20

Raw:

S_raw = 0.30 * DrawdownScore + 0.25 * BaseScore + 0.25 * ReclaimScore + 0.20 * VolumeScore

BaseScore source:

BaseScore = clamp(feature_engine.base_score, 0, 100)

Penalties:

DistEMA50 > config.scoring.reversal.penalties.overextension_threshold_pct
→ *config.scoring.reversal.penalties.overextension_factor

quote_volume_24h < config.scoring.reversal.penalties.low_liquidity_threshold
→ *config.scoring.reversal.penalties.low_liquidity_factor

Final:

S_final = round(S_raw \* penalties, 2)

------------------------------------------------------------------------

# 4. Breakout Scoring

Weights:

range = 0.30 break_strength = 0.30 volume = 0.20 momentum = 0.20

Raw:

S_raw = 0.30 * RangeScore + 0.30 * BreakStrengthScore + 0.20 * VolumeScore + 0.20 * MomentumScore

MomentumScore = clamp((r_7 / 10) * 100, 0, 100)

Penalties (config-driven):

overextension -> *config.scoring.breakout.penalties.overextension_factor

low liquidity -> *config.scoring.breakout.penalties.low_liquidity_factor

Final:

S_final = round(S_raw \* penalties, 2)

------------------------------------------------------------------------

# 5. Pullback Scoring

Weights:

trend = 0.30 depth = 0.30 structure = 0.20 reacceleration = 0.20

Raw:

S_raw = 0.30 * TrendScore + 0.30 * DepthScore + 0.20 * StructureScore + 0.20 * ReaccelerationScore

Reacceleration momentum component uses continuous scaling:

MomentumScore = clamp((r_7 / 10) * 100, 0, 100)

Penalties (config-driven):

broken trend -> *config.scoring.pullback.penalties.broken_trend_factor

low liquidity -> *config.scoring.pullback.penalties.low_liquidity_factor

Final:

S_final = round(S_raw \* penalties, 2)

------------------------------------------------------------------------

# 6. Determinism

Identical OHLCV + identical config → identical outputs. No randomness.
No stochastic components.
