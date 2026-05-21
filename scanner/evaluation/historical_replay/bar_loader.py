from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class ClosedBarSlice:
    symbol: str
    timeframe: str
    bars: pd.DataFrame


class HistoricalBarLoader:
    def __init__(self, history_dataset_ref: str) -> None:
        self.root = Path(history_dataset_ref)

    def _path(self, timeframe: str, symbol: str) -> Path:
        return self.root / timeframe / f"{symbol}.parquet"

    def load_symbol_timeframe(self, symbol: str, timeframe: str) -> pd.DataFrame:
        p = self._path(timeframe, symbol)
        if not p.exists():
            return pd.DataFrame()
        df = pd.read_parquet(p)
        if "close_time_utc" not in df.columns:
            raise ValueError(f"Missing close_time_utc in {p}")
        df = df.copy()
        df["close_time_utc"] = pd.to_datetime(df["close_time_utc"], utc=True)
        if "open_time_utc" in df.columns:
            df["open_time_utc"] = pd.to_datetime(df["open_time_utc"], utc=True)
        return df.sort_values("close_time_utc").reset_index(drop=True)

    def closed_bars_as_of(self, symbol: str, timeframe: str, as_of_utc: datetime) -> ClosedBarSlice:
        if as_of_utc.tzinfo is None:
            as_of_utc = as_of_utc.replace(tzinfo=timezone.utc)
        df = self.load_symbol_timeframe(symbol, timeframe)
        if df.empty:
            return ClosedBarSlice(symbol=symbol, timeframe=timeframe, bars=df)
        sliced = df.loc[df["close_time_utc"] <= pd.Timestamp(as_of_utc)].copy().reset_index(drop=True)
        return ClosedBarSlice(symbol=symbol, timeframe=timeframe, bars=sliced)
