"""
Raw Data Collector Utilities
============================

Diese Datei bündelt alle Funktionen, die Rohdaten aus der Pipeline
(OHLCV, MarketCap, Feature-Inputs etc.) zentral speichern.

Ziel:
- Einheitliche Logik für Speicherung & Logging
- Immer beide Formate (Parquet + CSV)
- Kein Code-Duplikat in den Clients oder Pipelines
"""

import json
import math
import pandas as pd
from typing import List, Dict, Any
from scanner.utils.save_raw import save_raw_snapshot


_IEEE754_SAFE_INT_MAX = (1 << 53) - 1


def _prepare_marketcap_payload_for_normalize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _prepare_marketcap_payload_for_normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_prepare_marketcap_payload_for_normalize(v) for v in value]
    if isinstance(value, int) and not isinstance(value, bool) and abs(value) > _IEEE754_SAFE_INT_MAX:
        return str(value)
    return value


def _is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except Exception:
        return False


def _stringify_scalar_for_raw_snapshot(value: Any) -> Any:
    if _is_missing_value(value):
        return None
    if isinstance(value, float):
        if math.isnan(value):
            return "nan"
        if math.isinf(value):
            return "inf" if value > 0 else "-inf"
    return str(value)


def _sanitize_marketcap_df_for_parquet(df: pd.DataFrame) -> pd.DataFrame:
    sanitized = df.copy()
    for col in sanitized.columns:
        if sanitized[col].dtype != "object":
            continue

        series = sanitized[col]

        if series.map(lambda v: isinstance(v, (dict, list))).any():
            series = series.map(
                lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            )

        has_oversized_int = series.map(
            lambda v: isinstance(v, int) and not isinstance(v, bool) and abs(v) > _IEEE754_SAFE_INT_MAX
        ).any()
        has_non_finite_float = series.map(
            lambda v: isinstance(v, float) and (math.isnan(v) or math.isinf(v))
        ).any()

        if has_oversized_int or has_non_finite_float:
            series = series.map(_stringify_scalar_for_raw_snapshot)

        sanitized[col] = series

    return sanitized


# ===============================================================
# OHLCV Snapshots
# ===============================================================

def collect_raw_ohlcv(results: Dict[str, Dict[str, Any]]):
    """
    Speichert alle OHLCV-Daten als Rohdaten-Snapshot.
    Erwartet das Dictionary, das aus OHLCVFetcher.fetch_all() zurückkommt.
    """
    if not results:
        print("[WARN] No OHLCV data to snapshot.")
        return None

    try:
        flat_records = []
        for symbol, tf_data in results.items():
            for tf, candles in tf_data.items():
                for candle in candles:
                    if not isinstance(candle, (list, tuple)) or len(candle) < 6:
                        print(f"[WARN] Skipping malformed candle for {symbol} {tf}: {candle}")
                        continue

                    flat_records.append({
                        "symbol": symbol,
                        "timeframe": tf,
                        "open_time": candle[0],
                        "close_time": candle[6] if len(candle) > 6 else None,
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
                        "quote_volume": candle[7] if len(candle) > 7 else None,
                    })
        df = pd.DataFrame(flat_records)
        return save_raw_snapshot(df, source_name="ohlcv_snapshot")
    except Exception as e:
        print(f"[WARN] Could not collect OHLCV snapshot: {e}")
        return None


# ===============================================================
# MarketCap Snapshots
# ===============================================================

def collect_raw_marketcap(data: List[Dict[str, Any]]):
    """
    Speichert alle MarketCap-Daten (Listings) als Rohdaten-Snapshot.
    Erwartet die Ausgabe aus MarketCapClient.get_listings() oder get_all_listings().

    Wichtig: CMC liefert verschachtelte Strukturen (z.B. quote -> USD -> ...).
    Für Parquet müssen wir das in eine flache Tabelle umwandeln.
    """
    if not data:
        print("[WARN] No MarketCap data to snapshot.")
        return None

    try:
        prepared_data = [_prepare_marketcap_payload_for_normalize(item) for item in data]

        # Flach machen: quote.USD.* etc. -> quote__USD__*
        df = pd.json_normalize(prepared_data, sep="__")

        # Objektspalten parquet-sicher und präzisionsfest bereinigen
        df = _sanitize_marketcap_df_for_parquet(df)

        # Parquet ist hier zwingend (und sollte nach Normalisierung sauber durchlaufen)
        return save_raw_snapshot(df, source_name="marketcap_snapshot", require_parquet=True)
    except Exception as e:
        print(f"[WARN] Could not collect MarketCap snapshot: {e}")
        return None


# ===============================================================
# Feature Snapshots (optional für spätere Erweiterung)
# ===============================================================

def collect_raw_features(df: pd.DataFrame, stage_name: str = "features"):
    """
    Speichert Feature-Inputs oder Zwischenstufen.
    Ideal für Debugging oder Backtests.
    """
    if df is None or df.empty:
        print("[WARN] No feature data to snapshot.")
        return None

    try:
        return save_raw_snapshot(df, source_name=f"{stage_name}_snapshot")
    except Exception as e:
        print(f"[WARN] Could not collect feature snapshot: {e}")
        return None
