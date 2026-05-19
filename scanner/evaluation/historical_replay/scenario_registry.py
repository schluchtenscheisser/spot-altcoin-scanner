from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def ensure_scenario_hash(*, registry_path: Path, scenario_id: str, scenario_hash: str, scenario_path: str) -> None:
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(registry_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS scenario_registry (
              scenario_id TEXT PRIMARY KEY,
              scenario_config_hash TEXT NOT NULL,
              first_seen_at_utc TEXT NOT NULL,
              first_scenario_path TEXT NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT scenario_config_hash FROM scenario_registry WHERE scenario_id = ?",
            (scenario_id,),
        ).fetchone()
        if row is None:
            conn.execute(
                "INSERT INTO scenario_registry (scenario_id, scenario_config_hash, first_seen_at_utc, first_scenario_path) VALUES (?, ?, ?, ?)",
                (scenario_id, scenario_hash, datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), scenario_path),
            )
            conn.commit()
            return
        if str(row[0]) != scenario_hash:
            raise ValueError(
                f"scenario_id '{scenario_id}' already exists with a different scenario_config_hash"
            )
