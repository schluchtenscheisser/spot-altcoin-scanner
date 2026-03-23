"""Canonical UTC bar-clock helpers for the Independence-Release architecture."""

from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from typing import Final

UTC = timezone.utc
FOUR_HOURS_SECONDS: Final[int] = 4 * 60 * 60
FOUR_HOURS_MS: Final[int] = FOUR_HOURS_SECONDS * 1000
DAILY_SCAN_DELTA_BARS: Final[int] = 6


def _coerce_utc_datetime(value: object, field_name: str = "timestamp") -> datetime:
    if value is None:
        raise TypeError(f"{field_name} must not be None")

    if isinstance(value, datetime):
        dt = value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
        return dt

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
        return datetime.fromtimestamp(numeric, tz=UTC)

    raise TypeError(
        f"{field_name} must be a datetime, ISO-8601 string, or Unix timestamp, got {type(value).__name__}"
    )


def _floor_to_4h_boundary(dt: datetime) -> datetime:
    seconds_since_midnight = dt.hour * 3600 + dt.minute * 60 + dt.second
    floored_seconds = (seconds_since_midnight // FOUR_HOURS_SECONDS) * FOUR_HOURS_SECONDS
    return dt.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(seconds=floored_seconds)


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
