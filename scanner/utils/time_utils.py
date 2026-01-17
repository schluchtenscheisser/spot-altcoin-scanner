"""
Time and date utilities.
All times are UTC-based for consistency.
"""

from datetime import datetime, timezone
from typing import Optional


def utc_now() -> datetime:
    """Get current UTC time (timezone-aware)."""
    return datetime.now(timezone.utc)


def utc_timestamp() -> str:
    """Get current UTC timestamp as ISO string (YYYY-MM-DDTHH:MM:SSZ)."""
    return utc_now().strftime("%Y-%m-%dT%H:%M:%SZ")


def utc_date() -> str:
    """Get current UTC date as string (YYYY-MM-DD)."""
    return utc_now().strftime("%Y-%m-%d")


def parse_timestamp(ts: str) -> datetime:
    """
    Parse ISO timestamp to datetime.
    
    Args:
        ts: ISO timestamp string (e.g., "2025-01-17T12:00:00Z")
        
    Returns:
        Timezone-aware datetime object
    """
    # Handle both with and without 'Z'
    if ts.endswith('Z'):
        ts = ts[:-1] + '+00:00'
    return datetime.fromisoformat(ts)


def timestamp_to_ms(dt: datetime) -> int:
    """Convert datetime to milliseconds since epoch (for APIs)."""
    return int(dt.timestamp() * 1000)


def ms_to_timestamp(ms: int) -> datetime:
    """Convert milliseconds since epoch to datetime."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc)
