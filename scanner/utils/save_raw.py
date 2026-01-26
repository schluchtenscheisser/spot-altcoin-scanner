import os
import pandas as pd
from datetime import datetime


def save_raw_snapshot(
    df: pd.DataFrame,
    source_name: str = "unknown",
    require_parquet: bool = False
):
    """
    Speichert die Rohdaten eines Runs im Ordner <BASEDIR>/<RUN_ID>/.

    - BASEDIR: per ENV `RAW_SNAPSHOT_BASEDIR` konfigurierbar (default: data/raw)
    - RUN_ID: wird einmal pro Run/Prozess erzeugt (ENV `RAW_SNAPSHOT_RUN_ID`)
             -> sorgt dafür, dass alle Snapshots eines Runs im selben Ordner landen.

    Exportiert immer zwei Formate:
      1. Parquet (für Analyse, effizient)
      2. CSV (für manuelle Kontrolle, optional gzip per `RAW_SNAPSHOT_CSV_GZIP=1`)
    """

    # 1) Ein Ordner pro Run: RUN_ID einmalig erzeugen und für den Prozess merken
    run_id = os.getenv("RAW_SNAPSHOT_RUN_ID")
    if not run_id:
        run_id = datetime.utcnow().strftime("%Y-%m-%d_%H-%M-%S")
        os.environ["RAW_SNAPSHOT_RUN_ID"] = run_id

    # 2) Basisordner konfigurierbar machen (z. B. snapshots/raw in GitHub Actions)
    base_root = os.getenv("RAW_SNAPSHOT_BASEDIR", os.path.join("data", "raw"))
    base_dir = os.path.join(base_root, run_id)
    os.makedirs(base_dir, exist_ok=True)

    parquet_path = os.path.join(base_dir, f"{source_name}.parquet")

    csv_gzip = os.getenv("RAW_SNAPSHOT_CSV_GZIP", "0").lower() in ("1", "true", "yes")
    csv_filename = f"{source_name}.csv.gz" if csv_gzip else f"{source_name}.csv"
    csv_path = os.path.join(base_dir, csv_filename)

    saved_paths = {"parquet": None, "csv": None}

    # --- 1️⃣ Parquet speichern ---
    try:
        df.to_parquet(parquet_path, index=False)
        print(f"[INFO] Raw data snapshot saved as Parquet: {parquet_path}")
        saved_paths["parquet"] = parquet_path
    except Exception as e:
        print(f"[WARN] Parquet export failed ({e}). You may need to install 'pyarrow' or 'fastparquet'.")

    # Wenn Parquet zwingend ist, zumindest klar & eindeutig loggen
    if require_parquet and not saved_paths["parquet"]:
        print("[ERROR] Parquet export is REQUIRED for this snapshot but failed.")

    # --- 2️⃣ CSV speichern ---
    try:
        if csv_gzip:
            df.to_csv(csv_path, index=False, compression="gzip")
        else:
            df.to_csv(csv_path, index=False)
        print(f"[INFO] Raw data snapshot saved as CSV: {csv_path}")
        saved_paths["csv"] = csv_path
    except Exception as e:
        print(f"[ERROR] CSV export failed: {e}")

    # --- Ergebnis ---
    if saved_paths["parquet"] or saved_paths["csv"]:
        print(f"[INFO] Raw data snapshot complete → {base_dir}")
    else:
        print("[ERROR] Could not save any raw data snapshot.")

    return saved_paths
