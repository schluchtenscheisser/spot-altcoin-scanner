from __future__ import annotations

from pathlib import Path

DEFAULT_CONTEXT_SOURCES: tuple[str, ...] = (
    "docs/AGENTS.md",
    "docs/code_map.md",
    "docs/canonical/ROADMAP.md",
)


def load_default_context(repo_root: Path) -> list[dict[str, str | int]]:
    """Load the fixed default context sources in deterministic order."""
    contexts: list[dict[str, str | int]] = []
    for rel_path in DEFAULT_CONTEXT_SOURCES:
        abs_path = repo_root / rel_path
        if not abs_path.is_file():
            raise FileNotFoundError(f"Missing required context source: {rel_path}")
        content = abs_path.read_text(encoding="utf-8")
        contexts.append(
            {
                "path": rel_path,
                "chars": len(content),
                "content": content,
            }
        )
    return contexts
