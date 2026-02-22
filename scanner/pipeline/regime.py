"""BTC regime helpers for report-level risk context."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


def compute_btc_regime_from_1d_features(features_1d: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute canonical BTC regime payload from 1D BTC features."""
    features_1d = features_1d or {}
    close = _to_float(features_1d.get("close"))
    ema20 = _to_float(features_1d.get("ema_20"))
    ema50 = _to_float(features_1d.get("ema_50"))

    close_gt_ema50 = (close is not None and ema50 is not None and close > ema50)
    ema20_gt_ema50 = (ema20 is not None and ema50 is not None and ema20 > ema50)
    btc_risk_on = bool(close_gt_ema50 and ema20_gt_ema50)

    return {
        "state": "RISK_ON" if btc_risk_on else "RISK_OFF",
        "multiplier_risk_on": 1.0,
        "multiplier_risk_off": 0.85,
        "checks": {
            "close_gt_ema50": bool(close_gt_ema50),
            "ema20_gt_ema50": bool(ema20_gt_ema50),
        },
    }


def compute_btc_regime(mexc_client: Any, feature_engine: Any, lookback_1d: int, asof_ts_ms: int) -> Dict[str, Any]:
    """Fetch BTCUSDT 1D candles and compute report-level regime payload."""
    try:
        btc_klines_1d = mexc_client.get_klines("BTCUSDT", "1d", limit=int(lookback_1d))
        btc_features = feature_engine.compute_all({"BTCUSDT": {"1d": btc_klines_1d}}, asof_ts_ms=asof_ts_ms)
        return compute_btc_regime_from_1d_features(btc_features.get("BTCUSDT", {}).get("1d", {}))
    except Exception as exc:  # pragma: no cover - defensive runtime fallback
        logger.warning("BTC regime fallback to RISK_OFF due to recoverable error: %s", exc)
        return compute_btc_regime_from_1d_features({})


def _to_float(value: Any) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None

