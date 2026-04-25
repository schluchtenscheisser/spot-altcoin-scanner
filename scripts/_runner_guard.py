"""Guard utilities for GitHub Actions analysis script execution."""

from __future__ import annotations

import sys
from pathlib import Path


def validate_script_path(script_path: str, *, repo_root: Path | None = None) -> str:
    """Validate and normalize a repo-relative analysis script path.

    Returns a normalized repo-relative POSIX path on success.
    Raises ValueError on invalid inputs.
    """
    if script_path is None:
        raise ValueError("script_path is required")

    raw = script_path.strip()
    if not raw:
        raise ValueError("script_path must not be empty")

    candidate = Path(raw)
    if candidate.is_absolute():
        raise ValueError("script_path must be a relative path under scripts/")

    root = (repo_root or Path.cwd()).resolve()
    scripts_root = (root / "scripts").resolve()
    normalized = (root / candidate).resolve(strict=False)

    try:
        normalized.relative_to(scripts_root)
    except ValueError as exc:
        raise ValueError("script_path must point to a file under scripts/") from exc

    if normalized.suffix != ".py":
        raise ValueError("script_path must reference a .py file")

    if not normalized.exists():
        raise ValueError("script_path does not exist")

    if not normalized.is_file():
        raise ValueError("script_path must reference a file, not a directory")

    return normalized.relative_to(root).as_posix()


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)

    if len(args) != 1:
        print("Usage: python scripts/_runner_guard.py <script_path>", file=sys.stderr)
        return 1

    try:
        normalized = validate_script_path(args[0])
    except ValueError as exc:
        print(f"Invalid script_path: {exc}", file=sys.stderr)
        return 1

    sys.stdout.write(f"script_path={normalized}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
