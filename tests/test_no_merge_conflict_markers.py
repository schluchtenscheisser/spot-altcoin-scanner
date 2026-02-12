import re
from pathlib import Path


START_RE = re.compile(r"^<<<<<<<\s")
MID_RE = re.compile(r"^=======$")
END_RE = re.compile(r"^>>>>>>>\s")
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}


def _iter_text_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".xlsx", ".zip", ".pyc"}:
            continue
        yield path


def _has_conflict_markers(text: str) -> bool:
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if START_RE.match(line):
            # Expect a matching middle and end marker later.
            has_mid = any(MID_RE.match(l) for l in lines[i + 1 :])
            has_end = any(END_RE.match(l) for l in lines[i + 1 :])
            if has_mid and has_end:
                return True
    return False


def test_repository_has_no_merge_conflict_markers() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    offending: list[str] = []

    for path in _iter_text_files(repo_root):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        if _has_conflict_markers(text):
            offending.append(str(path.relative_to(repo_root)))

    assert not offending, (
        "Merge conflict markers found in repository files: "
        + ", ".join(sorted(offending))
    )
