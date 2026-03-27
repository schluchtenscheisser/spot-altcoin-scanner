from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.ai_sparring.issue_parser import CommandType, parse_comment_command, parse_issue_body
from tools.ai_sparring.issue_state import (
    ACTIVE_STATUS,
    TERMINAL_STATUSES,
    PointerState,
    artifact_name,
    latest_valid_pointer_comment,
    render_focus_comment,
    render_round_comment,
    render_stop_comment,
)
from tools.ai_sparring.session import SessionConfig, run_session


@dataclass(frozen=True)
class IssueRuntimeEvent:
    issue_number: int
    issue_body: str
    comment_body: str
    is_pull_request: bool
    repository: str
    run_id: int


class IssueRuntimeError(RuntimeError):
    pass


def _session_id(issue_number: int) -> str:
    return f"issue-{issue_number}"


def _build_config_from_issue(sections: dict[str, str], output_dir: Path) -> SessionConfig:
    context_paths = tuple(x.strip() for x in sections.get("Extra Context Paths", "").splitlines() if x.strip())
    return SessionConfig(
        prompt=sections["Prompt"],
        mode=sections["Mode"],
        rounds=int(sections["Rounds"]),
        drafter_provider=sections.get("Drafter Provider") or "fake",
        drafter_model=sections.get("Drafter Model") or None,
        reviewer_provider=sections.get("Reviewer Provider") or "fake",
        reviewer_model=sections.get("Reviewer Model") or None,
        context_paths=context_paths,
        output_dir=output_dir,
    )


def _error_for_state(command: CommandType, state: PointerState | None) -> str | None:
    if state is None:
        return "No active session. Allowed command: `/sparring start`."
    if command == CommandType.START and state.status == ACTIVE_STATUS:
        return "Session already active. Allowed commands: `/continue`, `/focus <text>`, `/stop`."
    if state.status in TERMINAL_STATUSES:
        return f"Session is terminal (`{state.status}`). Start a new issue for a new session."
    if (
        command == CommandType.CONTINUE
        and state.status == ACTIVE_STATUS
        and state.rounds_completed >= state.rounds_requested
    ):
        return "Session already reached the requested rounds and is terminal (`completed`). Start a new issue for a new session."
    if command in {CommandType.CONTINUE, CommandType.FOCUS, CommandType.STOP} and state.status != ACTIVE_STATUS:
        return "No active session. Allowed command: `/sparring start`."
    return None


def handle_issue_event(*, event: IssueRuntimeEvent, repo_root: Path, api, output_dir: Path) -> dict:
    if event.is_pull_request:
        return {"action": "ignored_pull_request"}

    try:
        parsed_command = parse_comment_command(event.comment_body)
    except ValueError as exc:
        api.post_issue_comment(event.issue_number, f"AI Sparring command error: {exc}")
        return {"action": "invalid_command"}
    if parsed_command is None:
        return {"action": "ignored_non_command"}

    comments = api.list_issue_comments(event.issue_number)
    pointer = latest_valid_pointer_comment(comments)
    err = _error_for_state(parsed_command.type, pointer)
    if err and not (parsed_command.type == CommandType.START and pointer is None):
        api.post_issue_comment(event.issue_number, err)
        return {"action": "invalid_state", "reason": err}

    if parsed_command.type == CommandType.FOCUS:
        assert pointer is not None
        new_state = PointerState(**{**pointer.to_dict(), "current_focus": parsed_command.focus_text or ""})
        api.post_issue_comment(event.issue_number, render_focus_comment(state=new_state))
        return {"action": "focus_updated"}

    if parsed_command.type == CommandType.STOP:
        assert pointer is not None
        _resolve_prior_artifact_ref(api=api, pointer=pointer)
        stopped = PointerState(**{**pointer.to_dict(), "status": "stopped"})
        final_summary = "No final_summary.md available."
        if (output_dir / "final_summary.md").exists():
            final_summary = (output_dir / "final_summary.md").read_text(encoding="utf-8")
        api.post_issue_comment(event.issue_number, render_stop_comment(state=stopped, final_summary=final_summary))
        return {"action": "stopped"}

    # start or continue
    sections = parse_issue_body(event.issue_body)
    config = _build_config_from_issue(sections, output_dir)
    if parsed_command.type == CommandType.CONTINUE and pointer is not None:
        _resolve_prior_artifact_ref(api=api, pointer=pointer)
    requested_rounds = pointer.rounds_requested if pointer is not None else config.rounds
    config = SessionConfig(**{**config.__dict__, "rounds": 1})
    payload = run_session(config=config, repo_root=repo_root)

    status = payload["status"]
    rounds_completed_before = pointer.rounds_completed if pointer is not None else 0
    rounds_completed = rounds_completed_before + payload["rounds_completed"]
    rounds_requested = requested_rounds
    if status == "completed" and rounds_completed < rounds_requested:
        status = ACTIVE_STATUS

    state = PointerState(
        state_version=1,
        session_id=_session_id(event.issue_number),
        issue_number=event.issue_number,
        status=status,
        rounds_requested=rounds_requested,
        rounds_completed=rounds_completed,
        current_focus=(pointer.current_focus if pointer else ""),
        latest_run_id=event.run_id,
        latest_artifact_name=artifact_name(event.issue_number, rounds_completed),
    )

    round_data = payload["rounds"][-1] if payload["rounds"] else {}
    comment = render_round_comment(
        state=state,
        draft=round_data.get("draft", {}).get("text", ""),
        review=round_data.get("review", {}).get("text", ""),
        revision=round_data.get("revision", {}).get("text", ""),
        delta=round_data.get("delta_summary", "n/a"),
    )
    api.post_issue_comment(event.issue_number, comment)
    return {"action": "round_executed", "status": state.status}


def _resolve_prior_artifact_ref(*, api, pointer: PointerState) -> dict:
    artifacts = api.list_run_artifacts(pointer.latest_run_id)
    for item in artifacts:
        if item.get("name") == pointer.latest_artifact_name:
            return item
    raise IssueRuntimeError(
        f"Unable to resolve artifact '{pointer.latest_artifact_name}' for run {pointer.latest_run_id}"
    )
