from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


STATE_FIELDS = [
    "symbol","state_machine_state","state_confidence","state_transition_reason","setup_cycle_id",
    "bars_since_state_entered","bars_since_early_entered","bars_since_confirmed_entered",
    "close_at_early_entry_bar","close_at_confirmed_entry_bar","cycle_end_timestamp","bars_since_cycle_end",
    "last_aging_daily_bar_id","freshness_distance_state_early","freshness_distance_state_confirmed",
    "distance_from_ideal_entry_after_early","distance_from_ideal_entry_after_confirmed","last_evaluable_replay_date",
    "consecutive_missing_1d_bars","consecutive_missing_4h_bars",
]


class ReplayStateStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS replay_state (
                  symbol TEXT PRIMARY KEY,
                  state_machine_state TEXT,
                  state_confidence REAL,
                  state_transition_reason TEXT,
                  setup_cycle_id INTEGER,
                  bars_since_state_entered INTEGER,
                  bars_since_early_entered INTEGER,
                  bars_since_confirmed_entered INTEGER,
                  close_at_early_entry_bar REAL,
                  close_at_confirmed_entry_bar REAL,
                  cycle_end_timestamp INTEGER,
                  bars_since_cycle_end INTEGER,
                  last_aging_daily_bar_id TEXT,
                  freshness_distance_state_early REAL,
                  freshness_distance_state_confirmed REAL,
                  distance_from_ideal_entry_after_early REAL,
                  distance_from_ideal_entry_after_confirmed REAL,
                  last_evaluable_replay_date TEXT,
                  consecutive_missing_1d_bars INTEGER NOT NULL DEFAULT 0,
                  consecutive_missing_4h_bars INTEGER NOT NULL DEFAULT 0
                )
                """
            )

    def get(self, symbol: str) -> dict[str, Any]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM replay_state WHERE symbol=?", (symbol,)).fetchone()
        if row is None:
            return {"symbol": symbol, "consecutive_missing_1d_bars": 0, "consecutive_missing_4h_bars": 0}
        return dict(row)

    def upsert(self, record: dict[str, Any]) -> None:
        cols = [c for c in STATE_FIELDS if c in record]
        placeholders = ",".join("?" for _ in cols)
        updates = ",".join([f"{c}=excluded.{c}" for c in cols if c != "symbol"])
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"INSERT INTO replay_state ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT(symbol) DO UPDATE SET {updates}",
                tuple(record.get(c) for c in cols),
            )
