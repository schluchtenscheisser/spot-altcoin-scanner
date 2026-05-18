"""Configuration and date semantics for Historical Signal-Quality Replay Pre-1."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Iterable, Literal

SOURCE = "binance_spot"
SCHEMA_VERSION = "backtest_pre1_v1"
DEFAULT_FETCH_START_DATE = "2025-01-01"
DEFAULT_FETCH_END_DATE = "auto_last_closed_daily_bar"
DEFAULT_EVALUATION_START_DATE = "2025-05-01"
DEFAULT_EVALUATION_END_DATE = "fetch_end_date"
DEFAULT_TIMEFRAMES = ("1d", "4h")
VALID_TIMEFRAMES = {"1d", "4h"}
VALID_UNIVERSE_MODES = {"fixed_current_mexc_binance_intersection", "binance_spot_usdt_all"}
EXCLUSION_REASONS = (
    "mexc_only",
    "no_binance_history",
    "insufficient_history",
    "normalization_mismatch",
    "unsupported_symbol",
    "fetch_error",
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_utc_date(value: str | date, *, field_name: str) -> date:
    if isinstance(value, datetime):
        raise ValueError(f"{field_name} must be an ISO date (YYYY-MM-DD), not a datetime")
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be an ISO date string (YYYY-MM-DD)")
    candidate = value.strip()
    if "T" in candidate or ":" in candidate or candidate.endswith("Z") or len(candidate) != 10:
        raise ValueError(f"{field_name} must be an ISO date (YYYY-MM-DD), not a datetime")
    try:
        return date.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be a valid ISO date (YYYY-MM-DD): {value!r}") from exc


def last_closed_daily_bar_date(now: datetime | None = None) -> date:
    runtime = now or utc_now()
    if runtime.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    return runtime.astimezone(timezone.utc).date() - timedelta(days=1)


@dataclass(frozen=True)
class HistoryFetchConfig:
    fetch_start_date: date
    fetch_end_date_requested: str
    effective_fetch_end_date: date
    evaluation_start_date: date
    evaluation_end_date: date
    timeframes: tuple[str, ...] = DEFAULT_TIMEFRAMES
    source: str = SOURCE
    universe_mode: Literal["fixed_current_mexc_binance_intersection", "binance_spot_usdt_all"] = (
        "fixed_current_mexc_binance_intersection"
    )
    warm_up_1d_bars: int = 120
    warm_up_4h_bars: int = 120
    min_history_days: int = 150
    output_root: Path = Path("snapshots/history/ohlcv")
    manifest_root: Path = Path("snapshots/history/manifests")
    mexc_universe_path: Path | None = None
    force_repair: bool = False
    runtime_utc: datetime = field(default_factory=utc_now)

    @classmethod
    def resolve(
        cls,
        *,
        fetch_start_date: str | date = DEFAULT_FETCH_START_DATE,
        fetch_end_date: str | date = DEFAULT_FETCH_END_DATE,
        evaluation_start_date: str | date = DEFAULT_EVALUATION_START_DATE,
        evaluation_end_date: str | date = DEFAULT_EVALUATION_END_DATE,
        timeframes: Iterable[str] = DEFAULT_TIMEFRAMES,
        universe_mode: str = "fixed_current_mexc_binance_intersection",
        output_root: str | Path = Path("snapshots/history/ohlcv"),
        manifest_root: str | Path = Path("snapshots/history/manifests"),
        mexc_universe_path: str | Path | None = None,
        force_repair: bool = False,
        runtime_utc: datetime | None = None,
    ) -> "HistoryFetchConfig":
        runtime = runtime_utc or utc_now()
        if runtime.tzinfo is None:
            raise ValueError("runtime_utc must be timezone-aware")
        start = parse_utc_date(fetch_start_date, field_name="fetch_start_date")
        if fetch_end_date == DEFAULT_FETCH_END_DATE:
            effective_end = last_closed_daily_bar_date(runtime)
            requested = DEFAULT_FETCH_END_DATE
        else:
            effective_end = parse_utc_date(fetch_end_date, field_name="fetch_end_date")
            requested = effective_end.isoformat()
        eval_start = parse_utc_date(evaluation_start_date, field_name="evaluation_start_date")
        if evaluation_end_date == DEFAULT_EVALUATION_END_DATE:
            eval_end = effective_end
        else:
            eval_end = parse_utc_date(evaluation_end_date, field_name="evaluation_end_date")
        if start > effective_end:
            raise ValueError("fetch_start_date must be <= fetch_end_date")
        if eval_start > eval_end:
            raise ValueError("evaluation_start_date must be <= evaluation_end_date")
        tf_tuple = tuple(timeframes)
        invalid = [tf for tf in tf_tuple if tf not in VALID_TIMEFRAMES]
        if invalid:
            raise ValueError(f"unsupported timeframes: {invalid!r}; expected only '1d' and/or '4h'")
        ordered = tuple(tf for tf in DEFAULT_TIMEFRAMES if tf in set(tf_tuple))
        if not ordered:
            raise ValueError("at least one timeframe is required")
        if universe_mode not in VALID_UNIVERSE_MODES:
            raise ValueError(f"unsupported universe_mode: {universe_mode!r}")
        return cls(
            fetch_start_date=start,
            fetch_end_date_requested=requested,
            effective_fetch_end_date=effective_end,
            evaluation_start_date=eval_start,
            evaluation_end_date=eval_end,
            timeframes=ordered,
            universe_mode=universe_mode,  # type: ignore[arg-type]
            output_root=Path(output_root),
            manifest_root=Path(manifest_root),
            mexc_universe_path=Path(mexc_universe_path) if mexc_universe_path else None,
            force_repair=force_repair,
            runtime_utc=runtime.astimezone(timezone.utc),
        )

    @property
    def warm_up_coverage(self) -> dict[str, bool]:
        return {
            "evaluation_start_has_required_1d_warmup": (self.evaluation_start_date - self.fetch_start_date).days >= self.warm_up_1d_bars,
            "evaluation_start_has_required_4h_warmup": ((self.evaluation_start_date - self.fetch_start_date).days * 6) >= self.warm_up_4h_bars,
        }
