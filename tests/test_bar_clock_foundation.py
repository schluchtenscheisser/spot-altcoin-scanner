from datetime import datetime, timedelta, timezone

import pytest

from scanner.data.bar_clock import (
    DAILY_SCAN_DELTA_BARS,
    daily_bar_id,
    delta_closed_4h_bars,
    intraday_bar_id,
)


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2026-03-24T00:00:00.000Z", "2026-03-23"),
        ("2026-03-24T00:00:00.001Z", "2026-03-23"),
        ("2026-03-24T12:00:00.000Z", "2026-03-23"),
        ("2026-03-23T23:59:59.999Z", "2026-03-22"),
        ("2026-03-24T23:59:59.999Z", "2026-03-23"),
    ],
)
def test_daily_bar_id_examples(timestamp: str, expected: str) -> None:
    assert daily_bar_id(timestamp) == expected


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        ("2026-03-24T04:00:00.000Z", 1774324800000),
        ("2026-03-24T04:00:00.001Z", 1774324800000),
        ("2026-03-24T03:59:59.999Z", 1774310400000),
        ("2026-03-24T08:30:00.000Z", 1774339200000),
    ],
)
def test_intraday_bar_id_examples(timestamp: str, expected: int) -> None:
    assert intraday_bar_id(timestamp) == expected


def test_millisecond_numeric_inputs_are_accepted() -> None:
    assert daily_bar_id(1774324800000) == "2026-03-23"
    assert intraday_bar_id(1774324800000) == 1774324800000
    assert delta_closed_4h_bars(1774310400000, 1774324800000) == 1


def test_equivalent_aware_timezones_map_to_same_bar_ids() -> None:
    utc_value = datetime(2026, 3, 24, 4, 0, tzinfo=timezone.utc)
    plus_two_value = datetime(2026, 3, 24, 6, 0, tzinfo=timezone(timedelta(hours=2)))
    assert daily_bar_id(utc_value) == daily_bar_id(plus_two_value)
    assert intraday_bar_id(utc_value) == intraday_bar_id(plus_two_value)


@pytest.mark.parametrize(
    ("previous_timestamp", "current_timestamp", "expected"),
    [
        ("2026-03-24T00:00:00Z", "2026-03-24T04:00:00Z", 1),
        ("2026-03-24T00:00:00Z", "2026-03-24T08:00:00Z", 2),
        ("2026-03-24T00:00:01Z", "2026-03-24T04:00:00Z", 1),
        ("2026-03-24T04:00:00Z", "2026-03-24T04:00:00Z", 0),
        ("2026-03-24T00:00:00Z", "2026-03-25T00:00:00Z", 6),
    ],
)
def test_delta_closed_4h_bars_examples(previous_timestamp: str, current_timestamp: str, expected: int) -> None:
    assert delta_closed_4h_bars(previous_timestamp, current_timestamp) == expected


def test_bar_clock_is_deterministic() -> None:
    timestamp = datetime(2026, 3, 24, 8, 30, tzinfo=timezone.utc)
    assert daily_bar_id(timestamp) == daily_bar_id(timestamp)
    assert intraday_bar_id(timestamp) == intraday_bar_id(timestamp)


def test_daily_scan_delta_bars_constant() -> None:
    assert DAILY_SCAN_DELTA_BARS == 6


def test_bar_clock_invalid_inputs_raise_explicit_exceptions() -> None:
    with pytest.raises(TypeError, match="timestamp must not be None"):
        daily_bar_id(None)

    with pytest.raises(ValueError, match="timestamp must be finite"):
        daily_bar_id(float("nan"))

    with pytest.raises(ValueError, match="timestamp must be finite"):
        intraday_bar_id(float("inf"))

    with pytest.raises(ValueError, match="timestamp must be finite"):
        intraday_bar_id(float("-inf"))

    with pytest.raises(TypeError, match="previous_timestamp must not be None"):
        delta_closed_4h_bars(None, "2026-03-24T04:00:00Z")

    with pytest.raises(ValueError, match="current_timestamp must be finite"):
        delta_closed_4h_bars("2026-03-24T00:00:00Z", float("nan"))


def test_naive_datetime_inputs_are_rejected() -> None:
    naive = datetime(2026, 3, 24, 5, 0)
    with pytest.raises(TypeError, match="timezone-aware"):
        daily_bar_id(naive)

    with pytest.raises(TypeError, match="timezone-aware"):
        intraday_bar_id(naive)

    with pytest.raises(TypeError, match="timezone-aware"):
        delta_closed_4h_bars(naive, datetime(2026, 3, 24, 8, 0, tzinfo=timezone.utc))
