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
import numpy as np
from typing import List, Dict, Any
from scanner.utils.save_raw import save_raw_snapshot


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
                        print(
                            f"[WARN] Skipping malformed candle for {symbol} {tf}: {candle}"
                        )
                        continue

                    flat_records.append(
                        {
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
                        }
                    )
        df = pd.DataFrame(flat_records)
        return save_raw_snapshot(df, source_name="ohlcv_snapshot")
    except Exception as e:
        print(f"[WARN] Could not collect OHLCV snapshot: {e}")
        return None


# ===============================================================
# MarketCap Snapshots
# ===============================================================

_MAX_EXACT_IEEE754_INT = 2**53 - 1


def _is_oversized_int_like(value: Any) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return False
    if isinstance(value, (int, np.integer)):
        return abs(int(value)) > _MAX_EXACT_IEEE754_INT
    return False


def _stringify_for_raw_snapshot(value: Any) -> Any:
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value):
            return "NaN"
        if math.isinf(value):
            return "Infinity" if value > 0 else "-Infinity"

    if isinstance(value, (np.floating,)):
        numeric = float(value)
        if math.isnan(numeric):
            return "NaN"
        if math.isinf(numeric):
            return "Infinity" if numeric > 0 else "-Infinity"

    return str(value)


def _convert_oversized_ints_in_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _convert_oversized_ints_in_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_convert_oversized_ints_in_payload(v) for v in value]
    if _is_oversized_int_like(value):
        return str(int(value))
    return value


def _sanitize_object_columns_for_marketcap_parquet(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if df[col].dtype != "object":
            continue

        series = df[col]

        if series.map(lambda v: isinstance(v, (dict, list))).any():
            series = series.map(
                lambda v: (
                    json.dumps(v, ensure_ascii=False, sort_keys=True)
                    if isinstance(v, (dict, list))
                    else v
                )
            )

        non_null = series[series.notna()]
        has_oversized_int = (
            non_null.map(_is_oversized_int_like).any() if not non_null.empty else False
        )

        value_type_names = {
            type(v).__name__ for v in non_null if not isinstance(v, (bool, np.bool_))
        }
        has_mixed_scalar_types = len(value_type_names) > 1

        if has_oversized_int or has_mixed_scalar_types:
            series = series.map(_stringify_for_raw_snapshot)

        df[col] = series

    return df


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
        # Flach machen: quote.USD.* etc. -> quote__USD__*
        normalized_payload = _convert_oversized_ints_in_payload(data)
        df = pd.json_normalize(normalized_payload, sep="__")

        df = _sanitize_object_columns_for_marketcap_parquet(df)

        # Parquet ist hier zwingend (und sollte nach Normalisierung sauber durchlaufen)
        return save_raw_snapshot(
            df, source_name="marketcap_snapshot", require_parquet=True
        )
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
