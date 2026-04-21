from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Mapping, Sequence
from scanner.state.models import PersistedStateMachineContext, StatePersistencePatch


@dataclass(frozen=True)
class OhlcvBarRecord:
    symbol: str
    timeframe: str
    open_time_utc_ms: int
    close_time_utc_ms: int
    open: float
    high: float
    low: float
    close: float
    base_volume: float
    quote_volume: float


@dataclass(frozen=True)
class OhlcvCacheMetaRecord:
    symbol: str
    timeframe: str
    cached_close_time_utc_ms: int | None
    last_fetch_at_utc: str | None
    last_fetch_status: str
    last_error_code: str | None


def upsert_symbol_metadata(connection: sqlite3.Connection, symbol: str, mexc_first_tradable_date: str | None) -> None:
    with connection:
        connection.execute(
            """
            INSERT INTO symbol_metadata(symbol, mexc_first_tradable_date, updated_at_utc)
            VALUES (?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))
            ON CONFLICT(symbol) DO UPDATE SET
              mexc_first_tradable_date=excluded.mexc_first_tradable_date,
              updated_at_utc=excluded.updated_at_utc
            """,
            (symbol, mexc_first_tradable_date),
        )


def insert_symbol_run_decision(connection: sqlite3.Connection, row: Mapping[str, Any]) -> None:
    columns = [
        "run_id", "symbol", "eligible_pre_1d", "activity_gate_status", "pre_4h_filter_status",
        "pre_4h_filter_primary_reason", "monitoring_bypass_applied", "monitoring_bypass_reason",
        "was_capped_after_filter", "selected_for_4h_fetch", "quote_volume_24h", "active_days_last_14", "matched_filter_rules_json",
    ]
    values = [row.get(c) for c in columns]
    placeholders = ",".join("?" for _ in columns)
    with connection:
        connection.execute(
            f"INSERT INTO symbol_run_decisions ({','.join(columns)}) VALUES ({placeholders})",
            values,
        )


def get_ohlcv_cache_meta(connection: sqlite3.Connection, symbol: str, timeframe: str) -> OhlcvCacheMetaRecord | None:
    row = connection.execute(
        """
        SELECT symbol, timeframe, cached_close_time_utc_ms, last_fetch_at_utc, last_fetch_status, last_error_code
        FROM ohlcv_cache_meta
        WHERE symbol = ? AND timeframe = ?
        """,
        (symbol, timeframe),
    ).fetchone()
    if row is None:
        return None
    return OhlcvCacheMetaRecord(
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        cached_close_time_utc_ms=row["cached_close_time_utc_ms"],
        last_fetch_at_utc=row["last_fetch_at_utc"],
        last_fetch_status=row["last_fetch_status"],
        last_error_code=row["last_error_code"],
    )


def ohlcv_bar_exists(connection: sqlite3.Connection, symbol: str, timeframe: str, close_time_utc_ms: int) -> bool:
    row = connection.execute(
        """
        SELECT 1 FROM ohlcv_bars
        WHERE symbol = ? AND timeframe = ? AND close_time_utc_ms = ?
        LIMIT 1
        """,
        (symbol, timeframe, int(close_time_utc_ms)),
    ).fetchone()
    return row is not None


def write_ohlcv_bars_conflict_strict(
    connection: sqlite3.Connection,
    symbol: str,
    timeframe: str,
    bars: Sequence[OhlcvBarRecord],
) -> tuple[int, int]:
    inserted = 0
    noop_identical = 0
    for bar in bars:
        existing = connection.execute(
            """
            SELECT open_time_utc_ms, open, high, low, close, base_volume, quote_volume
            FROM ohlcv_bars
            WHERE symbol=? AND timeframe=? AND close_time_utc_ms=?
            """,
            (symbol, timeframe, int(bar.close_time_utc_ms)),
        ).fetchone()
        if existing is None:
            connection.execute(
                """
                INSERT INTO ohlcv_bars (
                    symbol, timeframe, open_time_utc_ms, close_time_utc_ms,
                    open, high, low, close, base_volume, quote_volume
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    symbol,
                    timeframe,
                    int(bar.open_time_utc_ms),
                    int(bar.close_time_utc_ms),
                    float(bar.open),
                    float(bar.high),
                    float(bar.low),
                    float(bar.close),
                    float(bar.base_volume),
                    float(bar.quote_volume),
                ),
            )
            inserted += 1
            continue

        same = (
            int(existing["open_time_utc_ms"]) == int(bar.open_time_utc_ms)
            and float(existing["open"]) == float(bar.open)
            and float(existing["high"]) == float(bar.high)
            and float(existing["low"]) == float(bar.low)
            and float(existing["close"]) == float(bar.close)
            and float(existing["base_volume"]) == float(bar.base_volume)
            and float(existing["quote_volume"]) == float(bar.quote_volume)
        )
        if same:
            noop_identical += 1
            continue
        raise ValueError(
            f"ohlcv bar conflict for {(symbol, timeframe, int(bar.close_time_utc_ms))}: existing row differs"
        )

    return inserted, noop_identical


def upsert_ohlcv_cache_meta(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    timeframe: str,
    cached_close_time_utc_ms: int | None,
    last_fetch_at_utc: str | None,
    last_fetch_status: str,
    last_error_code: str | None,
) -> None:
    connection.execute(
        """
        INSERT INTO ohlcv_cache_meta (
            symbol, timeframe, cached_close_time_utc_ms, last_fetch_at_utc, last_fetch_status, last_error_code
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(symbol, timeframe) DO UPDATE SET
            cached_close_time_utc_ms = excluded.cached_close_time_utc_ms,
            last_fetch_at_utc = excluded.last_fetch_at_utc,
            last_fetch_status = excluded.last_fetch_status,
            last_error_code = excluded.last_error_code
        """,
        (
            symbol,
            timeframe,
            cached_close_time_utc_ms,
            last_fetch_at_utc,
            last_fetch_status,
            last_error_code,
        ),
    )


def read_recent_ohlcv_bars(
    connection: sqlite3.Connection,
    symbol: str,
    timeframe: str,
    limit: int,
) -> list[OhlcvBarRecord]:
    rows = connection.execute(
        """
        SELECT symbol, timeframe, open_time_utc_ms, close_time_utc_ms, open, high, low, close, base_volume, quote_volume
        FROM ohlcv_bars
        WHERE symbol=? AND timeframe=?
        ORDER BY close_time_utc_ms DESC
        LIMIT ?
        """,
        (symbol, timeframe, int(limit)),
    ).fetchall()
    bars = [
        OhlcvBarRecord(
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            open_time_utc_ms=int(row["open_time_utc_ms"]),
            close_time_utc_ms=int(row["close_time_utc_ms"]),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            base_volume=float(row["base_volume"]),
            quote_volume=float(row["quote_volume"]),
        )
        for row in rows
    ]
    bars.reverse()
    return bars


def load_persisted_state_machine_context(connection: sqlite3.Connection, symbol: str) -> PersistedStateMachineContext:
    row = connection.execute(
        """
        SELECT
            symbol, setup_cycle_id, previous_setup_cycle_id, state_recorded_in_cycle_id, state_machine_state,
            freshness_distance_state_early, freshness_distance_state_confirmed, bars_since_state_entered,
            bars_since_early_entered, bars_since_confirmed_entered, bars_since_cycle_end,
            reclaim_below_reset_floor_seen_since_cycle_end, close_at_early_entry_bar, close_at_confirmed_entry_bar,
            distance_from_ideal_entry_after_early, distance_from_ideal_entry_after_confirmed,
            cycle_end_bar_index, cycle_end_timestamp
        FROM state_machine_context
        WHERE symbol = ?
        """,
        (symbol,),
    ).fetchone()
    if row is None:
        return PersistedStateMachineContext(
            symbol=symbol,
            current_setup_cycle_id=None,
            previous_setup_cycle_id=None,
            state_recorded_in_cycle_id=None,
            prev_state_machine_state=None,
            freshness_distance_state_early=None,
            freshness_distance_state_confirmed=None,
            bars_since_state_entered=None,
            bars_since_early_entered=None,
            bars_since_confirmed_entered=None,
            bars_since_cycle_end=None,
            reclaim_below_reset_floor_seen_since_cycle_end=None,
            close_at_early_entry_bar=None,
            close_at_confirmed_entry_bar=None,
            distance_from_ideal_entry_after_early=None,
            distance_from_ideal_entry_after_confirmed=None,
            cycle_end_bar_index=None,
            cycle_end_timestamp=None,
        )
    flag = row["reclaim_below_reset_floor_seen_since_cycle_end"]
    return PersistedStateMachineContext(
        symbol=row["symbol"],
        current_setup_cycle_id=row["setup_cycle_id"],
        previous_setup_cycle_id=row["previous_setup_cycle_id"],
        state_recorded_in_cycle_id=row["state_recorded_in_cycle_id"],
        prev_state_machine_state=row["state_machine_state"],
        freshness_distance_state_early=row["freshness_distance_state_early"],
        freshness_distance_state_confirmed=row["freshness_distance_state_confirmed"],
        bars_since_state_entered=row["bars_since_state_entered"],
        bars_since_early_entered=row["bars_since_early_entered"],
        bars_since_confirmed_entered=row["bars_since_confirmed_entered"],
        bars_since_cycle_end=row["bars_since_cycle_end"],
        reclaim_below_reset_floor_seen_since_cycle_end=(None if flag is None else bool(flag)),
        close_at_early_entry_bar=row["close_at_early_entry_bar"],
        close_at_confirmed_entry_bar=row["close_at_confirmed_entry_bar"],
        distance_from_ideal_entry_after_early=row["distance_from_ideal_entry_after_early"],
        distance_from_ideal_entry_after_confirmed=row["distance_from_ideal_entry_after_confirmed"],
        cycle_end_bar_index=row["cycle_end_bar_index"],
        cycle_end_timestamp=row["cycle_end_timestamp"],
    )


def apply_state_persistence_patch(connection: sqlite3.Connection, patch: StatePersistencePatch) -> None:
    with connection:
        connection.execute(
            """
            INSERT INTO state_machine_context (
                symbol, setup_cycle_id, previous_setup_cycle_id, state_recorded_in_cycle_id, state_machine_state,
                state_confidence, state_transition_reason, bars_since_state_entered, bars_since_early_entered,
                bars_since_confirmed_entered, bars_since_cycle_end, close_at_early_entry_bar,
                close_at_confirmed_entry_bar, distance_from_ideal_entry_after_early,
                distance_from_ideal_entry_after_confirmed, freshness_distance_state_early,
                freshness_distance_state_confirmed, cycle_end_bar_index, cycle_end_timestamp,
                reclaim_below_reset_floor_seen_since_cycle_end, data_resolution_class
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol) DO UPDATE SET
                setup_cycle_id=excluded.setup_cycle_id,
                previous_setup_cycle_id=excluded.previous_setup_cycle_id,
                state_recorded_in_cycle_id=excluded.state_recorded_in_cycle_id,
                state_machine_state=excluded.state_machine_state,
                state_confidence=excluded.state_confidence,
                state_transition_reason=excluded.state_transition_reason,
                bars_since_state_entered=excluded.bars_since_state_entered,
                bars_since_early_entered=excluded.bars_since_early_entered,
                bars_since_confirmed_entered=excluded.bars_since_confirmed_entered,
                bars_since_cycle_end=excluded.bars_since_cycle_end,
                close_at_early_entry_bar=excluded.close_at_early_entry_bar,
                close_at_confirmed_entry_bar=excluded.close_at_confirmed_entry_bar,
                distance_from_ideal_entry_after_early=excluded.distance_from_ideal_entry_after_early,
                distance_from_ideal_entry_after_confirmed=excluded.distance_from_ideal_entry_after_confirmed,
                freshness_distance_state_early=excluded.freshness_distance_state_early,
                freshness_distance_state_confirmed=excluded.freshness_distance_state_confirmed,
                cycle_end_bar_index=excluded.cycle_end_bar_index,
                cycle_end_timestamp=excluded.cycle_end_timestamp,
                reclaim_below_reset_floor_seen_since_cycle_end=excluded.reclaim_below_reset_floor_seen_since_cycle_end,
                data_resolution_class=excluded.data_resolution_class
            """,
            (
                patch.symbol,
                patch.setup_cycle_id,
                patch.previous_setup_cycle_id,
                patch.state_recorded_in_cycle_id,
                patch.state_machine_state,
                patch.state_confidence,
                patch.state_transition_reason,
                patch.bars_since_state_entered,
                patch.bars_since_early_entered,
                patch.bars_since_confirmed_entered,
                patch.bars_since_cycle_end,
                patch.close_at_early_entry_bar,
                patch.close_at_confirmed_entry_bar,
                patch.distance_from_ideal_entry_after_early,
                patch.distance_from_ideal_entry_after_confirmed,
                patch.freshness_distance_state_early,
                patch.freshness_distance_state_confirmed,
                patch.cycle_end_bar_index,
                patch.cycle_end_timestamp,
                None if patch.reclaim_below_reset_floor_seen_since_cycle_end is None else int(patch.reclaim_below_reset_floor_seen_since_cycle_end),
                patch.data_resolution_class,
            ),
        )
