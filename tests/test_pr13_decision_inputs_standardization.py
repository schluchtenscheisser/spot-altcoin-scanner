import pytest

from scanner.pipeline.scoring.decision_inputs import standardize_entry_readiness, standardize_invalidation_anchor


def test_entry_readiness_requires_reason_when_not_ready() -> None:
    with pytest.raises(ValueError):
        standardize_entry_readiness(entry_ready=False, reason_keys=[], setup_subtype="fresh_breakout")


def test_entry_readiness_ready_rows_drop_negative_reasons() -> None:
    result = standardize_entry_readiness(
        entry_ready=True,
        reason_keys=["breakout_not_confirmed"],
        setup_subtype="confirmed_breakout",
    )
    assert result["entry_ready"] is True
    assert result["entry_readiness_reasons"] == []


def test_invalidation_nonfinite_anchor_is_not_derivable() -> None:
    result = standardize_invalidation_anchor(anchor_price=float("inf"), anchor_type="breakout_level", derivable=True)
    assert result["invalidation_derivable"] is False
    assert result["invalidation_anchor_price"] is None
    assert result["invalidation_anchor_type"] is None
