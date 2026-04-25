from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import re
from typing import Any, Dict, Mapping, Literal

SCHEMA_VERSION = "ir1.0"

ScanMode = Literal["daily", "intraday"]

COUNTS_BUCKET_KEYS = (
    "watchlist",
    "early_candidates",
    "confirmed_candidates",
    "late_monitor",
    "discarded",
)

SYMBOL_LIST_BUCKET_KEYS = (
    "confirmed_candidates",
    "early_candidates",
    "watchlist",
    "late_monitor",
)

REQUIRED_DIAGNOSTIC_BLOCKS = (
    "axes",
    "phase",
    "invalidation",
    "cycle",
    "state",
    "pattern",
    "decision",
    "reasons",
)

_AS_OF_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DAILY_BAR_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INTRADAY_BAR_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T(00|04|08|12|16|20):00:00Z$")
_RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_scan_mode(value: Any) -> ScanMode:
    if value not in {"daily", "intraday"}:
        raise ValueError(f"scan_mode must be 'daily' or 'intraday', got {value!r}")
    return value


def validate_run_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"run_id must be a non-empty string, got {value!r}")
    if not _RUN_ID_RE.match(value):
        raise ValueError(
            "run_id must match ^[A-Za-z0-9][A-Za-z0-9._-]*$ "
            "(safe characters only; no path separators)"
        )
    if ".." in value:
        raise ValueError("run_id must not contain '..'")
    return value


def validate_as_of_utc(value: Any) -> str:
    if not isinstance(value, str) or not _AS_OF_UTC_RE.match(value):
        raise ValueError(
            f"as_of_utc must match YYYY-MM-DDTHH:MM:SSZ, got {value!r}"
        )
    datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    return value


def validate_daily_bar_id(value: Any) -> str:
    if not isinstance(value, str) or not _DAILY_BAR_ID_RE.match(value):
        raise ValueError(f"daily_bar_id must match YYYY-MM-DD, got {value!r}")
    date.fromisoformat(value)
    return value


def validate_intraday_bar_id(scan_mode: ScanMode, value: Any) -> str | None:
    if scan_mode == "daily":
        if value is not None:
            raise ValueError("intraday_bar_id must be null for daily scan_mode")
        return None

    if isinstance(value, str) and _INTRADAY_BAR_ID_RE.match(value):
        return value
    raise ValueError(
        f"intraday_bar_id must match YYYY-MM-DDTHH:00:00Z for intraday scan_mode, got {value!r}"
    )


def _require_symbol_list(key: str, value: Any) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"symbol_lists.{key} must be a list[str], got {value!r}")
    out: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item:
            raise ValueError(f"symbol_lists.{key}[{idx}] must be non-empty str, got {item!r}")
        out.append(item)
    return out


def normalize_symbol_lists(value: Mapping[str, Any] | None) -> Dict[str, list[str]]:
    source: Mapping[str, Any] = value or {}
    unknown = set(source.keys()) - set(SYMBOL_LIST_BUCKET_KEYS)
    if unknown:
        raise ValueError(f"symbol_lists contains unsupported keys: {sorted(unknown)}")

    return {k: _require_symbol_list(k, source.get(k, [])) for k in SYMBOL_LIST_BUCKET_KEYS}


def normalize_counts_by_bucket(value: Mapping[str, Any] | None) -> Dict[str, int]:
    source: Mapping[str, Any] = value or {}
    unknown = set(source.keys()) - set(COUNTS_BUCKET_KEYS)
    if unknown:
        raise ValueError(f"counts_by_bucket contains unsupported keys: {sorted(unknown)}")

    counts: Dict[str, int] = {}
    for key in COUNTS_BUCKET_KEYS:
        raw = source.get(key, 0)
        if isinstance(raw, bool) or not isinstance(raw, int) or raw < 0:
            raise ValueError(f"counts_by_bucket.{key} must be int >= 0, got {raw!r}")
        counts[key] = raw
    return counts


@dataclass(frozen=True)
class RunReport:
    run_id: str
    scan_mode: ScanMode
    as_of_utc: str
    daily_bar_id: str
    intraday_bar_id: str | None
    counts_by_bucket: Dict[str, int]
    symbol_lists: Dict[str, list[str]]
    manifest_path: str
    diagnostics_path: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "run_id": validate_run_id(self.run_id),
            "scan_mode": validate_scan_mode(self.scan_mode),
            "as_of_utc": validate_as_of_utc(self.as_of_utc),
            "daily_bar_id": validate_daily_bar_id(self.daily_bar_id),
            "intraday_bar_id": validate_intraday_bar_id(self.scan_mode, self.intraday_bar_id),
            "counts_by_bucket": normalize_counts_by_bucket(self.counts_by_bucket),
            "symbol_lists": normalize_symbol_lists(self.symbol_lists),
            "manifest_path": _validate_relative_path("manifest_path", self.manifest_path),
            "diagnostics_path": _validate_relative_path("diagnostics_path", self.diagnostics_path),
        }


def _validate_relative_path(key: str, value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{key} must be non-empty str")
    if value.startswith("/"):
        raise ValueError(f"{key} must be repository-root-relative, got absolute path")
    return value


def validate_diagnostics_record(record: Mapping[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, Mapping):
        raise ValueError(f"diagnostics record must be mapping, got {record!r}")

    scan_mode = validate_scan_mode(record.get("scan_mode"))

    out: Dict[str, Any] = {
        "schema_version": record.get("schema_version") or SCHEMA_VERSION,
        "run_id": validate_run_id(record.get("run_id")),
        "scan_mode": scan_mode,
        "symbol": _require_symbol(record.get("symbol")),
        "as_of_utc": validate_as_of_utc(record.get("as_of_utc")),
        "daily_bar_id": validate_daily_bar_id(record.get("daily_bar_id")),
        "intraday_bar_id": validate_intraday_bar_id(scan_mode, record.get("intraday_bar_id")),
        "data_4h_available": _require_bool("data_4h_available", record.get("data_4h_available")),
    }

    if out["schema_version"] != SCHEMA_VERSION:
        raise ValueError(
            f"diagnostics.schema_version must be {SCHEMA_VERSION!r}, got {out['schema_version']!r}"
        )

    for block_key in REQUIRED_DIAGNOSTIC_BLOCKS:
        block = record.get(block_key)
        if not isinstance(block, Mapping):
            raise ValueError(f"diagnostics.{block_key} must be object")
        out[block_key] = dict(block)

    out["execution_attempted"] = _require_bool("execution_attempted", record.get("execution_attempted", False))
    out["execution_status_raw"] = _require_nullable_str("execution_status_raw", record.get("execution_status_raw"))
    out["execution_reason_raw"] = _require_nullable_str("execution_reason_raw", record.get("execution_reason_raw"))
    out["execution_pass"] = _require_nullable_bool("execution_pass", record.get("execution_pass"))
    grade = record.get("execution_grade_t16")
    if grade is not None:
        raise ValueError("execution_grade_t16 must be null")
    out["execution_grade_t16"] = None
    duration = record.get("execution_fetch_duration_ms")
    if duration is not None and (isinstance(duration, bool) or not isinstance(duration, int) or duration < 0):
        raise ValueError("execution_fetch_duration_ms must be int >= 0 or null")
    out["execution_fetch_duration_ms"] = duration

    return out


def _require_symbol(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"symbol must be non-empty str, got {value!r}")
    return value


def _require_bool(key: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be bool, got {value!r}")
    return value


def _require_nullable_str(key: str, value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{key} must be str or null, got {value!r}")
    return value


def _require_nullable_bool(key: str, value: Any) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be bool or null, got {value!r}")
    return value
