from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import PurePosixPath

_ALLOWED_OHLCV_HISTORY_TIMEFRAMES = frozenset({"1d", "4h"})


@dataclass(frozen=True)
class MonthMutabilityPolicy:
    is_open: bool
    mutable_in_normal_operation: bool
    targeted_repair_allowed: bool


def _validate_relative_root(root: str, key_name: str) -> str:
    if not isinstance(root, str) or not root.strip():
        raise ValueError(f"{key_name} ({root!r}) must be a non-empty string")
    normalized = root.strip().replace("\\", "/").strip("/")
    if not normalized:
        raise ValueError(f"{key_name} ({root!r}) must be a non-empty relative path")
    if normalized.startswith(".") or "/../" in f"/{normalized}/":
        raise ValueError(f"{key_name} ({root!r}) must be repository-root-relative")
    return normalized


def _validate_symbol(symbol: str) -> str:
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError(f"symbol ({symbol!r}) must be a non-empty string")
    normalized = symbol.strip()
    if "/" in normalized or "\\" in normalized or ".." in normalized:
        raise ValueError(f"symbol ({symbol!r}) must not contain path separators or traversal")
    return normalized


def _validate_timeframe(timeframe: str) -> str:
    if timeframe not in _ALLOWED_OHLCV_HISTORY_TIMEFRAMES:
        allowed = ", ".join(sorted(_ALLOWED_OHLCV_HISTORY_TIMEFRAMES))
        raise ValueError(f"timeframe ({timeframe!r}) must be one of {{{allowed}}}")
    return timeframe


def _validate_partition_year_month(year: int, month: int) -> tuple[int, int]:
    if isinstance(year, bool) or not isinstance(year, int) or year < 0 or year > 9999:
        raise ValueError(f"year ({year!r}) must be an integer in [0, 9999]")
    if isinstance(month, bool) or not isinstance(month, int) or month < 1 or month > 12:
        raise ValueError(f"month ({month!r}) must be an integer in [1, 12]")
    return year, month


def build_ohlcv_history_partition_dir(
    *,
    timeframe: str,
    symbol: str,
    year: int,
    month: int,
    history_root: str = "snapshots/history",
) -> str:
    tf = _validate_timeframe(timeframe)
    sym = _validate_symbol(symbol)
    yyyy, mm = _validate_partition_year_month(year, month)
    base_root = _validate_relative_root(history_root, "history_root")

    path = PurePosixPath(base_root) / "ohlcv" / f"timeframe={tf}" / f"symbol={sym}" / f"year={yyyy:04d}" / f"month={mm:02d}"
    return f"{path.as_posix()}/"


def is_month_open(*, year: int, month: int, reference_date: date) -> bool:
    yyyy, mm = _validate_partition_year_month(year, month)
    if not isinstance(reference_date, date):
        raise ValueError(f"reference_date ({reference_date!r}) must be a date")
    return reference_date.year == yyyy and reference_date.month == mm


def month_mutability_policy(*, year: int, month: int, reference_date: date) -> MonthMutabilityPolicy:
    open_month = is_month_open(year=year, month=month, reference_date=reference_date)
    return MonthMutabilityPolicy(
        is_open=open_month,
        mutable_in_normal_operation=open_month,
        targeted_repair_allowed=True,
    )


def _parse_daily_bar_id(value: str) -> date:
    if not isinstance(value, str):
        raise ValueError(f"daily_bar_id ({value!r}) must match YYYY-MM-DD")
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError(f"daily_bar_id ({value!r}) must match YYYY-MM-DD") from exc


def _validate_run_id(run_id: str) -> str:
    if not isinstance(run_id, str) or not run_id.strip():
        raise ValueError(f"run_id ({run_id!r}) must be a non-empty string")
    normalized = run_id.strip()
    if "/" in normalized or "\\" in normalized or ".." in normalized:
        raise ValueError(f"run_id ({run_id!r}) must not contain path separators or traversal")
    return normalized


def build_run_snapshot_dir(*, daily_bar_id: str, run_id: str, runs_root: str = "snapshots/runs") -> str:
    run_date = _parse_daily_bar_id(daily_bar_id)
    safe_run_id = _validate_run_id(run_id)
    base_root = _validate_relative_root(runs_root, "runs_root")
    path = PurePosixPath(base_root) / f"{run_date.year:04d}" / f"{run_date.month:02d}" / f"{run_date.day:02d}" / safe_run_id
    return f"{path.as_posix()}/"


def build_run_manifest_path(*, daily_bar_id: str, run_id: str, runs_root: str = "snapshots/runs") -> str:
    return f"{build_run_snapshot_dir(daily_bar_id=daily_bar_id, run_id=run_id, runs_root=runs_root)}run.manifest.json"
