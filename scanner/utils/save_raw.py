import os
import pandas as pd
from datetime import datetime

def save_raw_snapshot(df: pd.DataFrame, source_name: str = "unknown"):
    """
    Speichert die Rohdaten eines Runs im Ordner data/raw/<timestamp>/
    """

    try:
        timestamp = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        base_dir = os.path.join("data", "raw", timestamp)
        os.makedirs(base_dir, exist_ok=True)

        filename = f"{source_name}.parquet"
        path = os.path.join(base_dir, filename)

        df.to_parquet(path, index=False)
        print(f"[INFO] Raw data snapshot saved: {path}")
        return path
    except Exception as e:
        print(f"[WARN] Could not save raw data snapshot: {e}")
        return None
