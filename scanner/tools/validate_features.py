"""Validate scanner report feature/scoring plausibility."""

import json
import os
from typing import Any, Dict, List, Tuple


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_features(report_path: str) -> int:
    """
    Validate report scoring structure and numeric ranges.

    Checks:
    - score and raw_score in [0, 100]
    - each component in [0, 100]
    - penalty_multiplier in (0, 1]

    Returns process-style status code:
    - 0 if valid
    - 1 if report missing/invalid/anomalies found
    """

    if not os.path.exists(report_path):
        print(f"❌ Report-Datei nicht gefunden: {report_path}")
        return 1

    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "setups" in data:
        section_key = "setups"
    elif "data" in data:
        section_key = "data"
    elif "results" in data:
        section_key = "results"
    else:
        print("❌ Ungültiges Report-Format – keine 'setups', 'data' oder 'results'-Sektion gefunden.")
        return 1

    results = data[section_key]
    if not results:
        print("⚠️ Keine Ergebnisse im Report.")
        return 0

    anomalies: List[Tuple[str, str, str, Any]] = []

    for setup_type, setups in results.items():
        for s in setups:
            symbol = s.get("symbol", "UNKNOWN")

            for scalar_key in ("score", "raw_score"):
                if scalar_key in s:
                    val = s.get(scalar_key)
                    if not _is_number(val) or not (0 <= float(val) <= 100):
                        anomalies.append((setup_type, symbol, scalar_key, val))

            if "penalty_multiplier" in s:
                pm = s.get("penalty_multiplier")
                if not _is_number(pm) or not (0 < float(pm) <= 1):
                    anomalies.append((setup_type, symbol, "penalty_multiplier", pm))

            comps = s.get("components", {})
            if not isinstance(comps, dict):
                anomalies.append((setup_type, symbol, "components", comps))
                continue

            for key, value in comps.items():
                if not _is_number(value) or not (0 <= float(value) <= 100):
                    anomalies.append((setup_type, symbol, f"components.{key}", value))

    if anomalies:
        print("⚠️ Anomalien gefunden:")
        for setup_type, symbol, key, value in anomalies:
            print(f"  [{setup_type}] {symbol}: {key} = {value}")
        return 1

    print("✅ Scoring-Werte numerisch und plausibel (inkl. score/raw_score/components/penalty_multiplier).")
    return 0


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("⚠️  Bitte Report-Dateipfad angeben, z. B.:")
        print("    python -m scanner.tools.validate_features reports/2026-01-22.json")
        sys.exit(1)

    report_path = sys.argv[1]
    sys.exit(validate_features(report_path))
