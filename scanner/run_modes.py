"""Runtime-mode normalization helpers.

The scanner has three deliberately separate mode contexts:

* CLI/config input modes, where legacy compatibility aliases are accepted.
* SQLite run metadata scan modes, which use T1-canonical values.
* Report/diagnostics scan modes, which use T13-canonical values.
"""

from __future__ import annotations

from typing import Final, Literal

CliRunMode = Literal[
    "daily_discovery",
    "intraday_promotion",
    "standard",
    "fast",
    "offline",
    "backtest",
]
RunnerTarget = Literal["daily", "intraday"]
RunMetadataScanMode = Literal["daily_discovery", "intraday_promotion"]
ReportScanMode = Literal["daily", "intraday"]

CANONICAL_CLI_RUN_MODES: Final[tuple[str, ...]] = ("daily_discovery", "intraday_promotion")
COMPATIBILITY_CLI_RUN_MODES: Final[tuple[str, ...]] = ("standard", "fast", "offline", "backtest")
ACCEPTED_CLI_RUN_MODES: Final[tuple[str, ...]] = CANONICAL_CLI_RUN_MODES + COMPATIBILITY_CLI_RUN_MODES

_CLI_TO_RUNNER_TARGET: Final[dict[str, RunnerTarget]] = {
    "daily_discovery": "daily",
    "intraday_promotion": "intraday",
    "standard": "daily",
    "fast": "daily",
    "offline": "daily",
    "backtest": "daily",
}

_CLI_TO_RUN_METADATA_SCAN_MODE: Final[dict[str, RunMetadataScanMode]] = {
    "daily_discovery": "daily_discovery",
    "intraday_promotion": "intraday_promotion",
    "standard": "daily_discovery",
    "fast": "daily_discovery",
    "offline": "daily_discovery",
    "backtest": "daily_discovery",
}

_RUN_METADATA_TO_REPORT_SCAN_MODE: Final[dict[str, ReportScanMode]] = {
    "daily_discovery": "daily",
    "intraday_promotion": "intraday",
}

# Historical storage values are accepted only for migration/read-normalization.
_LEGACY_STORAGE_TO_RUN_METADATA_SCAN_MODE: Final[dict[str, RunMetadataScanMode]] = {
    "daily": "daily_discovery",
    "intraday": "intraday_promotion",
}


def _invalid_mode_error(mode: str, *, context: str, expected: tuple[str, ...]) -> ValueError:
    return ValueError(f"invalid {context} {mode!r}: expected one of {sorted(expected)}")


def resolve_cli_mode_to_runner(mode: str) -> RunnerTarget:
    """Resolve a CLI/config input mode to the runner target."""
    try:
        return _CLI_TO_RUNNER_TARGET[str(mode)]
    except KeyError as exc:
        raise _invalid_mode_error(str(mode), context="run_mode", expected=ACCEPTED_CLI_RUN_MODES) from exc


def resolve_cli_mode_to_run_metadata_scan_mode(mode: str) -> RunMetadataScanMode:
    """Resolve a CLI/config input mode to T1-canonical SQLite run metadata."""
    try:
        return _CLI_TO_RUN_METADATA_SCAN_MODE[str(mode)]
    except KeyError as exc:
        raise _invalid_mode_error(str(mode), context="run_mode", expected=ACCEPTED_CLI_RUN_MODES) from exc


def resolve_run_metadata_scan_mode_to_report_scan_mode(mode: str) -> ReportScanMode:
    """Resolve T1-canonical run metadata mode to T13 report/diagnostics mode."""
    try:
        return _RUN_METADATA_TO_REPORT_SCAN_MODE[str(mode)]
    except KeyError as exc:
        raise _invalid_mode_error(
            str(mode),
            context="run_metadata.scan_mode",
            expected=tuple(_RUN_METADATA_TO_REPORT_SCAN_MODE),
        ) from exc


def normalize_storage_scan_mode_for_migration(mode: str) -> RunMetadataScanMode:
    """Normalize legacy stored values while migrating to T1-canonical metadata."""
    value = str(mode)
    if value in _CLI_TO_RUN_METADATA_SCAN_MODE:
        return _CLI_TO_RUN_METADATA_SCAN_MODE[value]
    if value in _LEGACY_STORAGE_TO_RUN_METADATA_SCAN_MODE:
        return _LEGACY_STORAGE_TO_RUN_METADATA_SCAN_MODE[value]
    raise _invalid_mode_error(
        value,
        context="stored run_metadata.scan_mode",
        expected=tuple(_CLI_TO_RUN_METADATA_SCAN_MODE) + tuple(_LEGACY_STORAGE_TO_RUN_METADATA_SCAN_MODE),
    )
