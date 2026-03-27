from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass

POINTER_PREFIX = "<!-- ai-sparring-state:v1:"
POINTER_RE = re.compile(r"<!-- ai-sparring-state:v1:([^>]+) -->")
TERMINAL_STATUSES = {"completed", "stopped", "failed_runtime", "failed_partial"}
ACTIVE_STATUS = "awaiting_continue"
MAX_SECTION_CHARS = 12000
TRUNCATION_SUFFIX = "[truncated for issue display; full content remains in workflow artifact]"


@dataclass(frozen=True)
class PointerState:
    state_version: int
    session_id: str
    issue_number: int
    status: str
    rounds_requested: int
    rounds_completed: int
    current_focus: str
    latest_run_id: int
    latest_artifact_name: str

    def to_dict(self) -> dict:
        return {
            "state_version": self.state_version,
            "session_id": self.session_id,
            "issue_number": self.issue_number,
            "status": self.status,
            "rounds_requested": self.rounds_requested,
            "rounds_completed": self.rounds_completed,
            "current_focus": self.current_focus,
            "latest_run_id": self.latest_run_id,
            "latest_artifact_name": self.latest_artifact_name,
        }


def encode_pointer(state: PointerState) -> str:
    raw = json.dumps(state.to_dict(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    encoded = base64.b64encode(raw).decode("ascii")
    return f"{POINTER_PREFIX}{encoded} -->"


def decode_pointer(pointer_comment: str) -> PointerState:
    match = POINTER_RE.search(pointer_comment)
    if not match:
        raise ValueError("Missing ai-sparring pointer payload")
    payload = json.loads(base64.b64decode(match.group(1)).decode("utf-8"))
    required = {
        "state_version",
        "session_id",
        "issue_number",
        "status",
        "rounds_requested",
        "rounds_completed",
        "current_focus",
        "latest_run_id",
        "latest_artifact_name",
    }
    missing = required - set(payload)
    if missing:
        raise ValueError(f"Pointer payload missing required keys: {sorted(missing)}")
    return PointerState(**payload)


def latest_valid_pointer_comment(comments: list[dict]) -> PointerState | None:
    selected: PointerState | None = None
    selected_id = -1
    for comment in comments:
        body = comment.get("body", "")
        try:
            state = decode_pointer(body)
        except Exception:
            continue
        comment_id = int(comment.get("id", 0))
        if comment_id > selected_id:
            selected = state
            selected_id = comment_id
    return selected


def artifact_name(issue_number: int, run_id: int) -> str:
    return f"ai-sparring-issue-{issue_number}-{run_id}"


def truncate_visible(text: str) -> str:
    if len(text) <= MAX_SECTION_CHARS:
        return text
    return text[:MAX_SECTION_CHARS] + "\n" + TRUNCATION_SUFFIX


def render_round_comment(*, state: PointerState, draft: str, review: str, revision: str, delta: str) -> str:
    commands = "`/continue`, `/focus <text>`, `/stop`" if state.status == ACTIVE_STATUS else "Session terminal"
    lines = [
        "## AI Sparring",
        f"Session: {state.session_id}",
        f"Status: {state.status}",
        f"Round: {state.rounds_completed}/{state.rounds_requested}",
        "### Draft",
        truncate_visible(draft),
        "### Review",
        truncate_visible(review),
        "### Revision",
        truncate_visible(revision),
        "### Delta",
        delta,
        "### Focus",
        state.current_focus or "(none)",
        "### Next commands",
        commands,
        encode_pointer(state),
    ]
    return "\n\n".join(lines)


def render_stop_comment(*, state: PointerState, final_summary: str) -> str:
    lines = [
        "## AI Sparring Final Summary",
        f"Session: {state.session_id}",
        "Status: stopped",
        f"Rounds completed: {state.rounds_completed}/{state.rounds_requested}",
        "### Final Summary",
        truncate_visible(final_summary),
        "### Focus",
        state.current_focus or "(none)",
        "### Closed session",
        "Session closed via `/stop`.",
        encode_pointer(state),
    ]
    return "\n\n".join(lines)


def render_focus_comment(*, state: PointerState) -> str:
    lines = [
        "## AI Sparring",
        f"Session: {state.session_id}",
        f"Status: {state.status}",
        "### Focus",
        state.current_focus or "(none)",
        "### Next commands",
        "`/continue`, `/focus <text>`, `/stop`",
        encode_pointer(state),
    ]
    return "\n\n".join(lines)
