"""
Feature Engine
==============

Computes technical features from OHLCV data for both 1d and 4h timeframes.

Features computed:
- Price: Returns (1d/3d/7d), HH/HL detection
- Trend: EMA20/50, Price relative to EMAs
- Volatility: ATR%
- Volume: Spike detection, Volume SMA
- Structure: Breakout distance, Drawdown, Base detection
"""

import logging
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class FeatureEngine:
    """Computes technical features from OHLCV data (v1.3 – critical findings remediation)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        logger.info("Feature Engine v1.3 initialized")

    def _config_get(self, path: List[str], default: Any) -> Any:
        """Read config path from either dict or ScannerConfig.raw."""
        root = self.config.raw if hasattr(self.config, "raw") else self.config
        current: Any = root
        for key in path:
            if not isinstance(current, dict):
                return default
            current = current.get(key)
            if current is None:
                return default
        return current

    def _get_volume_period_for_timeframe(self, timeframe: str) -> int:
        periods_cfg = self._config_get(["features", "volume_sma_periods"], None)
        if isinstance(periods_cfg, dict):
            tf_period = periods_cfg.get(timeframe)
            if tf_period is not None:
                return int(tf_period)

        legacy_period = self._config_get(["features", "volume_sma_period"], None)
        if legacy_period is not None:
            return int(legacy_period)

        logger.warning("Using legacy default volume_sma_period=14; please define config.features.volume_sma_periods")
        return 14

    # -------------------------------------------------------------------------
    # Main entry point
    # -------------------------------------------------------------------------
    def compute_all(
        self,
        ohlcv_data: Dict[str, Dict[str, List[List]]],
        asof_ts_ms: Optional[int] = None
    ) -> Dict[str, Dict[str, Any]]:
        results = {}
        total = len(ohlcv_data)
        logger.info(f"Computing features for {total} symbols")

        for i, (symbol, tf_data) in enumerate(ohlcv_data.items(), 1):
            try:
                logger.debug(f"[{i}/{total}] Computing features for {symbol}")
                symbol_features = {}

                last_closed_idx_map: Dict[str, Optional[int]] = {}

                if "1d" in tf_data:
                    idx_1d = self._get_last_closed_idx(tf_data["1d"], asof_ts_ms)
                    last_closed_idx_map["1d"] = idx_1d
                    symbol_features["1d"] = self._compute_timeframe_features(
                        tf_data["1d"], "1d", symbol, last_closed_idx=idx_1d
                    )

                if "4h" in tf_data:
                    idx_4h = self._get_last_closed_idx(tf_data["4h"], asof_ts_ms)
                    last_closed_idx_map["4h"] = idx_4h
                    symbol_features["4h"] = self._compute_timeframe_features(
                        tf_data["4h"], "4h", symbol, last_closed_idx=idx_4h
                    )

                last_update = None
                if "1d" in tf_data:
                    idx = last_closed_idx_map.get("1d")
                    if isinstance(idx, int) and idx >= 0:
                        last_update = int(tf_data["1d"][idx][0])

                symbol_features["meta"] = {
                    "symbol": symbol,
                    "asof_ts_ms": asof_ts_ms,
                    "last_closed_idx": last_closed_idx_map,
                    "last_update": last_update,
                }
                results[symbol] = symbol_features
            except Exception as e:
                logger.error(f"Failed to compute features for {symbol}: {e}")
        logger.info(f"Features computed for {len(results)}/{total} symbols")
        return results

    # -------------------------------------------------------------------------
    # Helper Funktion
    # -------------------------------------------------------------------------
    def _get_last_closed_idx(self, klines: List[List], asof_ts_ms: Optional[int]) -> int:
        """
        Returns index of the last candle with closeTime <= asof_ts_ms.
        Expected kline format includes closeTime at index 6.
        """
        if not klines:
            return -1
        if asof_ts_ms is None:
            return len(klines) - 1

        for i in range(len(klines) - 1, -1, -1):
            k = klines[i]
            if len(k) < 7:
                continue
            try:
                close_time = int(float(k[6]))
            except (TypeError, ValueError):
                continue
            if close_time <= asof_ts_ms:
                return i

        return -1

    # -------------------------------------------------------------------------
    # Timeframe feature computation
    # -------------------------------------------------------------------------
    def _compute_timeframe_features(
        self,
        klines: List[List],
        timeframe: str,
        symbol: str,
        last_closed_idx: Optional[int] = None
    ) -> Dict[str, Any]:
        if not klines:
            return {}

        if last_closed_idx is None:
            last_closed_idx = len(klines) - 1

        if last_closed_idx < 0:
            logger.warning(f"[{symbol}] no closed candles found for timeframe={timeframe}")
            return {}

        klines = klines[: last_closed_idx + 1]
        closes = np.array([k[4] for k in klines], dtype=float)
        highs = np.array([k[2] for k in klines], dtype=float)
        lows = np.array([k[3] for k in klines], dtype=float)
        volumes = np.array([k[5] for k in klines], dtype=float)
        quote_volumes = np.array([k[7] if len(k) > 7 else np.nan for k in klines], dtype=float)

        if len(closes) < 50:
            logger.warning(f"[{symbol}] insufficient candles ({len(closes)}) for timeframe {timeframe}")
            return {}

        f = {}
        f["close"], f["high"], f["low"], f["volume"] = map(float, (closes[-1], highs[-1], lows[-1], volumes[-1]))

        # Returns & EMAs
        f["r_1"] = self._calc_return(symbol, closes, 1)
        f["r_3"] = self._calc_return(symbol, closes, 3)
        f["r_7"] = self._calc_return(symbol, closes, 7)
        f["ema_20"] = self._calc_ema(symbol, closes, 20)
        f["ema_50"] = self._calc_ema(symbol, closes, 50)

        f["dist_ema20_pct"] = ((closes[-1] / f["ema_20"]) - 1) * 100 if f.get("ema_20") else np.nan
        f["dist_ema50_pct"] = ((closes[-1] / f["ema_50"]) - 1) * 100 if f.get("ema_50") else np.nan

        f["atr_pct"] = self._calc_atr_pct(symbol, highs, lows, closes, 14)

        # Phase 1: timeframe-specific volume baseline period (include_current=False baseline)
        volume_period = self._get_volume_period_for_timeframe(timeframe)
        f["volume_sma"] = self._calc_sma(volumes, volume_period, include_current=False)
        f["volume_sma_period"] = int(volume_period)
        f["volume_spike"] = self._calc_volume_spike(symbol, volumes, f["volume_sma"])

        # Backward compatibility keys
        f["volume_sma_14"] = self._calc_sma(volumes, 14, include_current=False)

        # Quote volume features (with same period by timeframe + legacy key)
        f.update(self._calc_quote_volume_features(symbol, quote_volumes, volume_period))

        # Trend structure
        f["hh_20"] = bool(self._detect_higher_high(highs, 20))
        f["hl_20"] = bool(self._detect_higher_low(lows, 20))

        # Structural metrics
        f["breakout_dist_20"] = self._calc_breakout_distance(symbol, closes, highs, 20)
        f["breakout_dist_30"] = self._calc_breakout_distance(symbol, closes, highs, 30)
        drawdown_lookback = int(self._config_get(["features", "drawdown_lookback_days"], 365))
        f["drawdown_from_ath"] = self._calc_drawdown(closes, drawdown_lookback)

        # Base detection
        f["base_score"] = self._detect_base(symbol, closes, lows, 30) if timeframe == "1d" else np.nan

        return self._convert_to_native_types(f)

    # -------------------------------------------------------------------------
    # Calculation methods
    # -------------------------------------------------------------------------
    def _calc_return(self, symbol: str, closes: np.ndarray, periods: int) -> Optional[float]:
        if len(closes) <= periods:
            logger.warning(f"[{symbol}] insufficient candles for return({periods})")
            return np.nan
        try:
            return float(((closes[-1] / closes[-periods-1]) - 1) * 100)
        except Exception as e:
            logger.error(f"[{symbol}] return({periods}) error: {e}")
            return np.nan

    def _calc_ema(self, symbol: str, data: np.ndarray, period: int) -> Optional[float]:
        if len(data) < period:
            logger.warning(f"[{symbol}] insufficient data for EMA{period}")
            return np.nan

        alpha = 2 / (period + 1)
        ema = float(np.nanmean(data[:period]))
        for val in data[period:]:
            ema = alpha * val + (1 - alpha) * ema
        return float(ema)

    def _calc_sma(self, data: np.ndarray, period: int, include_current: bool = True) -> Optional[float]:
        if include_current:
            return float(np.nanmean(data[-period:])) if len(data) >= period else np.nan
        return float(np.nanmean(data[-period-1:-1])) if len(data) >= (period + 1) else np.nan

    def _calc_volume_spike(self, symbol: str, volumes: np.ndarray, sma: Optional[float]) -> float:
        if sma is None or np.isnan(sma) or sma == 0:
            logger.warning(f"[{symbol}] volume_spike fallback=1.0 (SMA invalid)")
            return 1.0
        return float(volumes[-1] / sma)

    def _calc_quote_volume_features(
        self,
        symbol: str,
        quote_volumes: np.ndarray,
        period: int,
    ) -> Dict[str, Optional[float]]:
        if len(quote_volumes) == 0 or np.all(np.isnan(quote_volumes)):
            return {
                "volume_quote": None,
                "volume_quote_sma": None,
                "volume_quote_spike": None,
                "volume_quote_sma_14": None,
            }

        volume_quote = float(quote_volumes[-1]) if not np.isnan(quote_volumes[-1]) else np.nan
        volume_quote_sma = self._calc_sma(quote_volumes, period, include_current=False)
        volume_quote_spike = self._calc_volume_spike(symbol, quote_volumes, volume_quote_sma)
        volume_quote_sma_14 = self._calc_sma(quote_volumes, 14, include_current=False)

        return {
            "volume_quote": volume_quote,
            "volume_quote_sma": volume_quote_sma,
            "volume_quote_spike": volume_quote_spike,
            "volume_quote_sma_14": volume_quote_sma_14,
        }

    def _calc_atr_pct(self, symbol: str, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, period: int) -> Optional[float]:
        if len(highs) < period + 1:
            logger.warning(f"[{symbol}] insufficient candles for ATR{period}")
            return np.nan

        tr = [
            max(
                highs[i] - lows[i],
                abs(highs[i] - closes[i - 1]),
                abs(lows[i] - closes[i - 1]),
            )
            for i in range(1, len(highs))
        ]

        atr = float(np.nanmean(tr[:period]))
        for tr_val in tr[period:]:
            atr = ((atr * (period - 1)) + tr_val) / period

        if atr < 0:
            logger.warning(f"[{symbol}] ATR computed negative ({atr}); returning NaN")
            return np.nan

        return float((atr / closes[-1]) * 100) if closes[-1] > 0 else np.nan

    def _calc_breakout_distance(self, symbol: str, closes: np.ndarray, highs: np.ndarray, lookback: int) -> Optional[float]:
        if len(highs) < lookback + 1:
            logger.warning(f"[{symbol}] insufficient candles for breakout_dist_{lookback}")
            return np.nan
        try:
            prior_high = np.nanmax(highs[-lookback-1:-1])
            return float(((closes[-1] / prior_high) - 1) * 100)
        except Exception as e:
            logger.error(f"[{symbol}] breakout_dist_{lookback} error: {e}")
            return np.nan

    def _calc_drawdown(self, closes: np.ndarray, lookback_days: int = 365) -> Optional[float]:
        if len(closes) == 0:
            return np.nan
        lookback = max(1, int(lookback_days))
        window = closes[-lookback:]
        ath = np.nanmax(window)
        return float(((closes[-1] / ath) - 1) * 100)

    # -------------------------------------------------------------------------
    # Structure detection
    # -------------------------------------------------------------------------
    def _detect_higher_high(self, highs: np.ndarray, lookback: int = 20) -> bool:
        if len(highs) < lookback:
            return False
        return bool(np.nanmax(highs[-5:]) > np.nanmax(highs[-lookback:-5]))

    def _detect_higher_low(self, lows: np.ndarray, lookback: int = 20) -> bool:
        if len(lows) < lookback:
            return False
        return bool(np.nanmin(lows[-5:]) > np.nanmin(lows[-lookback:-5]))

    def _detect_base(self, symbol: str, closes: np.ndarray, lows: np.ndarray, lookback: int = 30) -> Optional[float]:
        if len(closes) < lookback:
            logger.warning(f"[{symbol}] insufficient candles for base detection")
            return np.nan
        recent_low = np.nanmin(lows[-lookback//3:])
        prior_low = np.nanmin(lows[-lookback:-lookback//3])
        no_new_lows = recent_low >= prior_low
        price_range = (np.nanmax(closes[-lookback:]) - np.nanmin(closes[-lookback:])) / np.nanmean(closes[-lookback:]) * 100
        stability_score = max(0.0, 100.0 - price_range)
        base_score = stability_score if no_new_lows else stability_score / 2
        return float(base_score)

    # -------------------------------------------------------------------------
    # Utility
    # -------------------------------------------------------------------------
    def _convert_to_native_types(self, features: Dict[str, Any]) -> Dict[str, Any]:
        converted = {}
        for k, v in features.items():
            if v is None or (isinstance(v, float) and np.isnan(v)):
                converted[k] = None
            elif isinstance(v, (np.floating, np.float64, np.float32)):
                converted[k] = float(v)
            elif isinstance(v, (np.integer, np.int64, np.int32)):
                converted[k] = int(v)
            elif isinstance(v, (np.bool_, bool)):
                converted[k] = bool(v)
            else:
                converted[k] = v
        return converted
