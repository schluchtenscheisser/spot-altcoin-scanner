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
import pandas as pd
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
                    flat_records.append({
                        "symbol": symbol,
                        "timeframe": tf,
                        "open_time": candle[0],
                        "open": candle[1],
                        "high": candle[2],
                        "low": candle[3],
                        "close": candle[4],
                        "volume": candle[5],
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
        # Flach machen: quote.USD.* etc. -> quote__USD__*
        df = pd.json_normalize(data, sep="__")

        # Restliche dict/list Werte Parquet-sicher machen (als JSON-String)
        for col in df.columns:
            if df[col].dtype == "object":
                if df[col].map(lambda v: isinstance(v, (dict, list))).any():
                    df[col] = df[col].map(
                        lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
                    )

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
