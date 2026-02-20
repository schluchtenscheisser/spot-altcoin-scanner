from pathlib import Path

from scanner.pipeline.filters import UniverseFilters


def test_unlock_overrides_ignore_invalid_days_and_keep_valid_entries(caplog):
    overrides_data = {
        "overrides": [
            {"symbol": "VALID_STRUSDT", "severity": "major", "days_to_unlock": "7"},
            {"symbol": "VALID_ZEROUSDT", "severity": "minor", "days_to_unlock": 0},
            {"symbol": "VALID_INTUSDT", "severity": "major", "days_to_unlock": 14},
            {"symbol": "BAD_NONEUSDT", "severity": "major", "days_to_unlock": None},
            {"symbol": "BAD_EMPTYUSDT", "severity": "minor", "days_to_unlock": ""},
            {"symbol": "BAD_SUFFIXUSDT", "severity": "major", "days_to_unlock": "7d"},
            {"symbol": "BAD_NEGUSDT", "severity": "minor", "days_to_unlock": -3},
            {"symbol": "TOO_FARUSDT", "severity": "major", "days_to_unlock": 15},
        ]
    }

    filters = UniverseFilters.__new__(UniverseFilters)
    filters._safe_load_yaml = lambda _: overrides_data

    with caplog.at_level("WARNING"):
        major_symbols, _, minor_symbols, _ = filters._load_unlock_overrides(Path("ignored.yaml"))

    assert major_symbols == {"VALID_STRUSDT", "VALID_INTUSDT"}
    assert minor_symbols == {"VALID_ZEROUSDT"}

    warning_text = "\n".join(caplog.messages)
    assert "BAD_NONEUSDT" in warning_text
    assert "BAD_EMPTYUSDT" in warning_text
    assert "BAD_SUFFIXUSDT" in warning_text
    assert "BAD_NEGUSDT" in warning_text
