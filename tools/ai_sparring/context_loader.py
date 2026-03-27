from __future__ import annotations

from pathlib import Path, PurePosixPath

from tools.ai_sparring.errors import PreflightValidationError

DEFAULT_CONTEXT_SOURCES: tuple[str, ...] = (
    "docs/AGENTS.md",
    "docs/code_map.md",
    "docs/canonical/ROADMAP.md",
)
MAX_CONTEXT_BYTES = 153600


def _normalize_repo_rel_path(path: str) -> str:
    normalized = PurePosixPath(path.replace("\\", "/")).as_posix()
    if normalized.startswith("/") or normalized.startswith("../") or "/../" in normalized:
        raise PreflightValidationError(f"Invalid context path (outside repo): {path}")
    return normalized


def _read_context_file(repo_root: Path, rel_path: str) -> dict[str, str | int]:
    abs_path = (repo_root / rel_path).resolve()
    if not abs_path.is_file():
        raise PreflightValidationError(f"Invalid context path (not a file): {rel_path}")

    try:
        abs_path.relative_to(repo_root.resolve())
    except ValueError as exc:
        raise PreflightValidationError(f"Invalid context path (outside repo): {rel_path}") from exc

    raw = abs_path.read_bytes()
    if len(raw) > MAX_CONTEXT_BYTES:
        raise PreflightValidationError(
            f"Invalid context path (file too large > {MAX_CONTEXT_BYTES} bytes): {rel_path}"
        )
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PreflightValidationError(f"Invalid context path (not UTF-8 text): {rel_path}") from exc

    return {"path": rel_path, "bytes": len(raw), "content": content}


def load_context(repo_root: Path, extra_paths: list[str]) -> list[dict[str, str | int]]:
    normalized_extras = sorted({_normalize_repo_rel_path(path) for path in extra_paths})
    ordered_paths = list(DEFAULT_CONTEXT_SOURCES) + normalized_extras

    contexts: list[dict[str, str | int]] = []
    seen: set[str] = set()
    for rel_path in ordered_paths:
        if rel_path in seen:
            continue
        seen.add(rel_path)
        contexts.append(_read_context_file(repo_root=repo_root, rel_path=rel_path))
    return contexts
