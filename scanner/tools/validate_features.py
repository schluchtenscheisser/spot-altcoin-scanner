"""Validate scanner report feature/scoring plausibility."""

import json
import os
from typing import Any, Dict, List


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _error(
    path: str,
    code: str,
    msg: str,
    got: Any = None,
    expected: str | None = None,
) -> Dict[str, Any]:
    entry: Dict[str, Any] = {"path": path, "code": code, "msg": msg}
    if got is not None:
        entry["got"] = got
    if expected is not None:
        entry["expected"] = expected
    return entry


def _emit(ok: bool, errors: List[Dict[str, Any]]) -> int:
    print(json.dumps({"ok": ok, "errors": errors}, ensure_ascii=False))
    return 0 if ok else 1


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
        return _emit(
            False,
            [_error("report", "FILE_NOT_FOUND", "Report file not found.", got=report_path)],
        )

    try:
        with open(report_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        return _emit(
            False,
            [_error("report", "INVALID_JSON", "Report is not valid JSON.", got=str(exc))],
        )

    if "setups" in data:
        section_key = "setups"
    elif "data" in data:
        section_key = "data"
    elif "results" in data:
        section_key = "results"
    else:
        return _emit(
            False,
            [
                _error(
                    "report",
                    "MISSING_SECTION",
                    "Report must contain 'setups', 'data' or 'results' section.",
                )
            ],
        )

    results = data[section_key]
    if not results:
        return _emit(True, [])

    anomalies: List[Dict[str, Any]] = []

    for setup_type, setups in results.items():
        for idx, s in enumerate(setups):
            setup_path = f"{section_key}.{setup_type}[{idx}]"

            for required_key in ("score", "raw_score", "penalty_multiplier", "components"):
                if required_key not in s:
                    anomalies.append(
                        _error(
                            f"{setup_path}.{required_key}",
                            "MISSING_FIELD",
                            f"Required field '{required_key}' is missing.",
                            expected="present",
                        )
                    )

            for scalar_key in ("score", "raw_score"):
                if scalar_key in s:
                    val = s.get(scalar_key)
                    if not _is_number(val) or not (0 <= float(val) <= 100):
                        anomalies.append(
                            _error(
                                f"{setup_path}.{scalar_key}",
                                "RANGE",
                                f"{scalar_key} must be a number in [0,100].",
                                got=val,
                                expected="[0,100]",
                            )
                        )

            if "penalty_multiplier" in s:
                pm = s.get("penalty_multiplier")
                if not _is_number(pm) or not (0 < float(pm) <= 1):
                    anomalies.append(
                        _error(
                            f"{setup_path}.penalty_multiplier",
                            "RANGE",
                            "penalty_multiplier must be a number in (0,1].",
                            got=pm,
                            expected="(0,1]",
                        )
                    )

            comps = s.get("components", {})
            if not isinstance(comps, dict):
                anomalies.append(
                    _error(
                        f"{setup_path}.components",
                        "TYPE",
                        "components must be an object/dict.",
                        got=comps,
                        expected="dict",
                    )
                )
                continue

            for key, value in comps.items():
                if not _is_number(value) or not (0 <= float(value) <= 100):
                    anomalies.append(
                        _error(
                            f"{setup_path}.components.{key}",
                            "RANGE",
                            f"Component '{key}' must be a number in [0,100].",
                            got=value,
                            expected="[0,100]",
                        )
                    )

    if anomalies:
        return _emit(False, anomalies)

    return _emit(True, [])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "ok": False,
                    "errors": [
                        {
                            "path": "cli",
                            "code": "MISSING_ARGUMENT",
                            "msg": "Please provide report path, e.g. python -m scanner.tools.validate_features reports/2026-01-22.json",
                        }
                    ],
                },
                ensure_ascii=False,
            )
        )
        sys.exit(1)

    report_path = sys.argv[1]
    sys.exit(validate_features(report_path))
