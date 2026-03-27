from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

ISSUE_HEADINGS = (
    "Prompt",
    "Mode",
    "Rounds",
    "Drafter Provider",
    "Drafter Model",
    "Reviewer Provider",
    "Reviewer Model",
    "Extra Context Paths",
)


class CommandType(str, Enum):
    START = "start"
    CONTINUE = "continue"
    FOCUS = "focus"
    STOP = "stop"


@dataclass(frozen=True)
class ParsedCommand:
    type: CommandType
    focus_text: str | None = None


def parse_issue_body(body: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    bucket: list[str] = []

    def _commit() -> None:
        nonlocal bucket
        if current is None:
            return
        sections[current] = "\n".join(bucket).strip()
        bucket = []

    for raw_line in body.splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("## "):
            heading = line[3:].strip()
            if heading in ISSUE_HEADINGS:
                _commit()
                current = heading
                continue
        if current is not None:
            bucket.append(line)
    _commit()

    required = ("Prompt", "Mode", "Rounds")
    missing = [name for name in required if not sections.get(name)]
    if missing:
        names = ", ".join(missing)
        raise ValueError(f"Missing required issue heading(s): {names}")
    return sections


def parse_comment_command(comment_body: str) -> ParsedCommand | None:
    stripped = comment_body.lstrip()
    if not stripped.startswith("/"):
        return None

    if stripped.startswith("/sparring"):
        parts = stripped.split()
        if parts == ["/sparring", "start"]:
            return ParsedCommand(type=CommandType.START)
        raise ValueError("Invalid /sparring command. Allowed: '/sparring start'")

    if stripped.startswith("/continue"):
        if stripped.split() == ["/continue"]:
            return ParsedCommand(type=CommandType.CONTINUE)
        raise ValueError("Invalid /continue command. Trailing tokens are not allowed")

    if stripped.startswith("/stop"):
        if stripped.split() == ["/stop"]:
            return ParsedCommand(type=CommandType.STOP)
        raise ValueError("Invalid /stop command. Trailing tokens are not allowed")

    if stripped.startswith("/focus"):
        if stripped == "/focus":
            raise ValueError("Invalid /focus command. Focus text is required")
        if not stripped.startswith("/focus "):
            raise ValueError("Invalid /focus command")
        focus = stripped[len("/focus ") :].strip()
        if not focus:
            raise ValueError("Invalid /focus command. Focus text is required")
        return ParsedCommand(type=CommandType.FOCUS, focus_text=focus)

    raise ValueError("Unsupported command")
