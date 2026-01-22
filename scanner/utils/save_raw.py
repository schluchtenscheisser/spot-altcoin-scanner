import os
import pandas as pd
from datetime import datetime


def save_raw_snapshot(df: pd.DataFrame, source_name: str = "unknown"):
    """
    Speichert die Rohdaten eines Runs im Ordner data/raw/<timestamp>/.
    Exportiert immer zwei Formate:
      1. Parquet (für Analyse, effizient)
      2. CSV (für manuelle Kontrolle)
    """

    timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
    base_dir = os.path.join("data", "raw", timestamp)
    os.makedirs(base_dir, exist_ok=True)

    parquet_path = os.path.join(base_dir, f"{source_name}.parquet")
    csv_path = os.path.join(base_dir, f"{source_name}.csv")

    saved_paths = {"parquet": None, "csv": None}

    # --- 1️⃣ Parquet speichern ---
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"[INFO] Raw data snapshot saved as Parquet: {parquet_path}")
        saved_paths["parquet"] = parquet_path
    except Exception as e:
        print(f"[WARN] Parquet export failed ({e}). You may need to install 'pyarrow' or 'fastparquet'.")

    # --- 2️⃣ CSV speichern ---
    try:
        df.to_csv(csv_path, index=False)
        print(f"[INFO] Raw data snapshot saved as CSV: {csv_path}")
        saved_paths["csv"] = csv_path
    except Exception as e:
        print(f"[ERROR] CSV export failed: {e}")

    # --- Ergebnis ---
    if saved_paths["parquet"] or saved_paths["csv"]:
        print(f"[INFO] Raw data snapshot complete → {base_dir}")
    else:
        print(f"[ERROR] Could not save any raw data snapshot.")

    return saved_paths
