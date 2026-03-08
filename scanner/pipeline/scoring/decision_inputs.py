"""Helpers for standardized setup-scorer decision inputs."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List


def standardize_entry_readiness(entry_ready: bool, reason_keys: Iterable[str], setup_subtype: str) -> Dict[str, Any]:
    """Build standardized readiness fields for setup scorers.

    Contract:
    - non-entry-ready rows must include at least one standardized reason key
    - entry-ready rows must not include negative readiness reasons
    """

    reasons: List[str] = []
    seen = set()
    for reason in reason_keys:
        if not isinstance(reason, str) or not reason.strip():
            continue
        if reason in seen:
            continue
        seen.add(reason)
        reasons.append(reason)

    is_ready = bool(entry_ready)
    if is_ready:
        reasons = []
    elif not reasons:
        raise ValueError("entry_ready=false requires at least one entry_readiness_reasons key")

    return {
        "entry_ready": is_ready,
        "entry_readiness_reasons": reasons,
        "setup_subtype": setup_subtype,
    }


def standardize_invalidation_anchor(anchor_price: Any, anchor_type: Any, derivable: bool) -> Dict[str, Any]:
    """Build normalized invalidation anchor fields.

    Non-finite or semantically missing anchors are always returned as not-derivable.
    """

    if not derivable:
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    try:
        numeric_anchor = float(anchor_price)
    except (TypeError, ValueError):
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    if not math.isfinite(numeric_anchor) or numeric_anchor <= 0 or not isinstance(anchor_type, str) or not anchor_type:
        return {
            "invalidation_anchor_price": None,
            "invalidation_anchor_type": None,
            "invalidation_derivable": False,
        }

    return {
        "invalidation_anchor_price": numeric_anchor,
        "invalidation_anchor_type": anchor_type,
        "invalidation_derivable": True,
    }

