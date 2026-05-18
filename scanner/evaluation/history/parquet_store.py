"""Partitioned Parquet storage helpers for Pre-1 OHLCV history."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

import pandas as pd

REQUIRED_COLUMNS = [
    "source",
    "symbol",
    "timeframe",
    "open_time_utc",
    "close_time_utc",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "is_closed",
    "fetch_run_id",
    "fetched_at_utc",
]
KEY_COLUMNS = ["source", "symbol", "timeframe", "open_time_utc"]
NUMERIC_COLUMNS = ["open", "high", "low", "close", "volume", "quote_volume"]


@dataclass
class WriteResult:
    written: list[str] = field(default_factory=list)
    skipped_existing: list[str] = field(default_factory=list)
    repaired: list[str] = field(default_factory=list)
    existing_partitions_detected: int = 0
    new_partitions_written: int = 0
    existing_closed_partitions_rewritten: int = 0


def partition_path(root: Path, *, timeframe: str, symbol: str, year: int, month: int) -> Path:
    return root / f"timeframe={timeframe}" / f"symbol={symbol}" / f"year={year:04d}" / f"month={month:02d}" / "part-000.parquet"


def _relative(path: Path) -> str:
    return path.as_posix()


def _month_is_closed(year: int, month: int, effective_fetch_end_date: date) -> bool:
    return (year, month) < (effective_fetch_end_date.year, effective_fetch_end_date.month)


def _validate_rows(df: pd.DataFrame) -> None:
    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"missing required OHLCV columns: {missing!r}")
    if not df["is_closed"].eq(True).all():
        raise ValueError("all persisted OHLCV rows must have is_closed=true")
    for column in NUMERIC_COLUMNS:
        values = pd.to_numeric(df[column], errors="coerce")
        finite_or_null = values.map(lambda value: pd.isna(value) or math.isfinite(float(value)))
        if not finite_or_null.all():
            raise ValueError(f"non-finite numeric values detected in {column}")


def normalize_rows(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    _validate_rows(df)
    output = df[REQUIRED_COLUMNS].copy()
    output["open_time_utc"] = pd.to_datetime(output["open_time_utc"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    output["close_time_utc"] = pd.to_datetime(output["close_time_utc"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    output = output.drop_duplicates(subset=KEY_COLUMNS, keep="last")
    return output.sort_values(["symbol", "timeframe", "open_time_utc"]).reset_index(drop=True)


def read_partition(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return pd.read_parquet(path)


def write_partitioned_ohlcv(
    rows: pd.DataFrame,
    *,
    output_root: Path,
    effective_fetch_end_date: date,
    force_repair: bool = False,
) -> WriteResult:
    result = WriteResult()
    if rows.empty:
        return result
    normalized = normalize_rows(rows)
    normalized["_open_ts"] = pd.to_datetime(normalized["open_time_utc"], utc=True)
    grouped = normalized.groupby(["timeframe", "symbol", normalized["_open_ts"].dt.year, normalized["_open_ts"].dt.month], sort=True)
    for (timeframe, symbol, year, month), group in grouped:
        path = partition_path(output_root, timeframe=str(timeframe), symbol=str(symbol), year=int(year), month=int(month))
        rel = _relative(path)
        exists = path.exists()
        closed_month = _month_is_closed(int(year), int(month), effective_fetch_end_date)
        if exists:
            result.existing_partitions_detected += 1
        if exists and closed_month and not force_repair:
            result.skipped_existing.append(rel)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        out_group = group.drop(columns=["_open_ts"]).copy()
        if exists and not force_repair:
            existing = read_partition(path)
            out_group = normalize_rows(pd.concat([existing, out_group], ignore_index=True))
            before = len(normalize_rows(existing)) if not existing.empty else 0
            if len(out_group) == before:
                result.skipped_existing.append(rel)
                continue
        else:
            out_group = normalize_rows(out_group)
        out_group.to_parquet(path, index=False)
        if exists and closed_month and force_repair:
            result.repaired.append(rel)
            result.existing_closed_partitions_rewritten += 1
        else:
            result.written.append(rel)
            if not exists:
                result.new_partitions_written += 1
    result.written.sort()
    result.skipped_existing.sort()
    result.repaired.sort()
    return result


def discover_partitions(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(root.glob("timeframe=*/symbol=*/year=*/month=*/part-000.parquet"))


def load_symbol_timeframe(root: Path, symbol: str, timeframe: str) -> pd.DataFrame:
    paths = sorted((root / f"timeframe={timeframe}" / f"symbol={symbol}").glob("year=*/month=*/part-000.parquet"))
    frames = [pd.read_parquet(path) for path in paths]
    if not frames:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return normalize_rows(pd.concat(frames, ignore_index=True))
