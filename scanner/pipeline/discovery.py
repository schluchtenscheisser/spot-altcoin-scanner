"""Discovery tag helpers (v2 T6.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _iso_to_ts_ms(value: str) -> Optional[int]:
    if not value:
        return None

    normalized = str(value).strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"

    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1000)


def compute_discovery_fields(
    *,
    asof_ts_ms: int,
    date_added: Optional[str],
    first_seen_ts: Optional[int],
    max_age_days: int = 180,
) -> Dict[str, Any]:
    """Compute deterministic discovery metadata for a symbol."""
    source_ts = _iso_to_ts_ms(date_added) if date_added else None
    source = "cmc_date_added" if source_ts is not None else None

    if source_ts is None and first_seen_ts is not None:
        try:
            source_ts = int(first_seen_ts)
            source = "first_seen_ts"
        except (TypeError, ValueError):
            source_ts = None
            source = None

    if source_ts is None:
        return {
            "discovery": False,
            "discovery_age_days": None,
            "discovery_source": None,
        }

    age_days = max(0, int((asof_ts_ms - source_ts) / 86_400_000))
    return {
        "discovery": age_days <= int(max_age_days),
        "discovery_age_days": age_days,
        "discovery_source": source,
    }

