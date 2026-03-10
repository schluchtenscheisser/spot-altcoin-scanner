import json
import math
from pathlib import Path

import pytest


REPORT_PATH = Path("reports/2026-03-10.json")


def _finite_positive(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric) or numeric <= 0:
        return None
    return numeric


def test_report_2026_03_10_tp_rr_fields_follow_canonical_formula() -> None:
    report = json.loads(REPORT_PATH.read_text())
    candidates = report.get("trade_candidates")
    assert isinstance(candidates, list) and candidates

    for row in candidates:
        entry = _finite_positive(row.get("entry_price_usdt"))
        stop = _finite_positive(row.get("stop_price_initial"))
        tp10 = row.get("tp10_price")
        tp20 = row.get("tp20_price")
        rr10 = row.get("rr_to_tp10")
        rr20 = row.get("rr_to_tp20")

        if entry is None:
            assert tp10 is None
            assert tp20 is None
            assert rr10 is None
            assert rr20 is None
            continue

        assert tp10 == pytest.approx(entry * 1.10)
        assert tp20 == pytest.approx(entry * 1.20)

        if stop is None or stop >= entry:
            assert rr10 is None
            assert rr20 is None
            continue

        risk_abs = entry - stop
        assert rr10 == pytest.approx((entry * 1.10 - entry) / risk_abs)
        assert rr20 == pytest.approx((entry * 1.20 - entry) / risk_abs)
