"""Canonical UTC bar-clock helpers for the Independence-Release architecture."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
import re
from typing import Final

UTC = timezone.utc
FOUR_HOURS_SECONDS: Final[int] = 4 * 60 * 60
FOUR_HOURS_MS: Final[int] = FOUR_HOURS_SECONDS * 1000
ONE_DAY_MS: Final[int] = 86_400_000
DAILY_SCAN_DELTA_BARS: Final[int] = 6
_INTRADAY_BAR_ID_RE: Final[re.Pattern[str]] = re.compile(r"^(\d{4}-\d{2}-\d{2})T(00|04|08|12|16|20):00:00Z$")


def _coerce_utc_datetime(value: object, field_name: str = "timestamp") -> datetime:
    if value is None:
        raise TypeError(f"{field_name} must not be None")

    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise TypeError(f"{field_name} must be timezone-aware, got naive datetime")
        return value.astimezone(UTC)

    if isinstance(value, str):
        normalized = value.strip()
        if normalized.endswith("Z"):
            normalized = normalized[:-1] + "+00:00"
        try:
            dt = datetime.fromisoformat(normalized)
        except ValueError as exc:
            raise ValueError(f"{field_name} must be a valid ISO-8601 timestamp: {value!r}") from exc
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt.astimezone(UTC)

    if isinstance(value, bool):
        raise TypeError(f"{field_name} must be a datetime, ISO-8601 string, or Unix timestamp, got bool")

    if isinstance(value, (int, float)):
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"{field_name} must be finite, got {value!r}")
        return datetime.fromtimestamp(numeric / 1000.0, tz=UTC)

    raise TypeError(
        f"{field_name} must be a datetime, ISO-8601 string, or Unix timestamp, got {type(value).__name__}"
    )


def _floor_to_4h_boundary(dt: datetime) -> datetime:
    seconds_since_midnight = dt.hour * 3600 + dt.minute * 60 + dt.second
    floored_seconds = (seconds_since_midnight // FOUR_HOURS_SECONDS) * FOUR_HOURS_SECONDS
    return dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=floored_seconds)


def timeframe_to_duration_ms(timeframe: str) -> int:
    if timeframe == "1d":
        return ONE_DAY_MS
    if timeframe == "4h":
        return FOUR_HOURS_MS
    raise ValueError(f"timeframe invalid value {timeframe!r}: must be one of ('1d', '4h')")


def most_recent_closed_bar_close_time_utc_ms(timeframe: str, now: object) -> int:
    dt = _coerce_utc_datetime(now, "now")
    if timeframe == "4h":
        boundary = _floor_to_4h_boundary(dt)
        return int(boundary.timestamp() * 1000)
    if timeframe == "1d":
        boundary = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        return int(boundary.timestamp() * 1000)
    raise ValueError(f"timeframe invalid value {timeframe!r}: must be one of ('1d', '4h')")


def is_close_time_on_grid(timeframe: str, close_time_utc_ms: int) -> bool:
    duration = timeframe_to_duration_ms(timeframe)
    return close_time_utc_ms % duration == 0


def daily_bar_id(timestamp: object) -> str:
    """Return the YYYY-MM-DD identifier of the most recently closed daily bar."""
    dt = _coerce_utc_datetime(timestamp, "timestamp")
    boundary = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    if dt < boundary:
        boundary -= timedelta(days=1)
    closed_bar_date = boundary.date() - timedelta(days=1)
    return closed_bar_date.isoformat()


def intraday_bar_id(timestamp: object) -> int:
    """Return the close-time UTC epoch milliseconds of the most recently closed 4h bar."""
    dt = _coerce_utc_datetime(timestamp, "timestamp")
    boundary = _floor_to_4h_boundary(dt)
    return int(boundary.timestamp() * 1000)


def get_last_closed_intraday_bar_id(now_utc: datetime, timeframe: str = "4h") -> str:
    """Return canonical closed-bar id (`YYYY-MM-DDTHH:00:00Z`) for intraday scans."""
    dt = _coerce_utc_datetime(now_utc, "now_utc")
    if timeframe != "4h":
        raise ValueError("timeframe invalid value {!r}: must be '4h'".format(timeframe))

    boundary = _floor_to_4h_boundary(dt)
    return boundary.strftime("%Y-%m-%dT%H:00:00Z")


def has_new_intraday_bar(previous_bar_id: str | None, current_bar_id: str) -> bool:
    """Return whether `current_bar_id` is newer than `previous_bar_id`."""
    if previous_bar_id is None:
        _parse_intraday_bar_id(current_bar_id, field_name="current_bar_id")
        return True

    previous_dt = _parse_intraday_bar_id(previous_bar_id, field_name="previous_bar_id")
    current_dt = _parse_intraday_bar_id(current_bar_id, field_name="current_bar_id")
    return current_dt > previous_dt


def _parse_intraday_bar_id(value: str, *, field_name: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be str in YYYY-MM-DDTHH:00:00Z format")
    match = _INTRADAY_BAR_ID_RE.match(value)
    if match is None:
        raise ValueError(f"{field_name} must match YYYY-MM-DDTHH:00:00Z with HH in {{00,04,08,12,16,20}}")
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def delta_closed_4h_bars(previous_timestamp: object, current_timestamp: object) -> int:
    """Return the number of newly closed 4h bars in the half-open interval (previous, current]."""
    previous_dt = _coerce_utc_datetime(previous_timestamp, "previous_timestamp")
    current_dt = _coerce_utc_datetime(current_timestamp, "current_timestamp")

    if current_dt <= previous_dt:
        return 0

    previous_epoch = previous_dt.timestamp()
    current_epoch = current_dt.timestamp()
    previous_boundaries = math.floor(previous_epoch / FOUR_HOURS_SECONDS)
    current_boundaries = math.floor(current_epoch / FOUR_HOURS_SECONDS)
    return max(0, current_boundaries - previous_boundaries)
