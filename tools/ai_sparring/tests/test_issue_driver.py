from pathlib import Path

import pytest

from tools.ai_sparring.issue_driver import IssueRuntimeEvent, handle_issue_event
from tools.ai_sparring.issue_state import encode_pointer, PointerState


class _ApiStub:
    def __init__(self, comments=None, artifacts=None):
        self._comments = comments or []
        self._artifacts = artifacts or []
        self.posted = []

    def list_issue_comments(self, issue_number: int):
        return self._comments

    def post_issue_comment(self, issue_number: int, body: str):
        self.posted.append(body)
        return {"id": len(self.posted)}

    def list_run_artifacts(self, run_id: int):
        return self._artifacts


def _event(comment: str) -> IssueRuntimeEvent:
    return IssueRuntimeEvent(
        issue_number=9,
        issue_body="""## Prompt\nImprove it\n\n## Mode\nticket_review\n\n## Rounds\n1\n\n## Drafter Provider\n\n## Drafter Model\n\n## Reviewer Provider\n\n## Reviewer Model\n\n## Extra Context Paths\n""",
        comment_body=comment,
        is_pull_request=False,
        repository="o/r",
        run_id=55,
    )


def test_invalid_command_for_state_posts_error_without_artifact(tmp_path: Path) -> None:
    api = _ApiStub(comments=[])
    result = handle_issue_event(event=_event("/continue"), repo_root=Path(__file__).resolve().parents[3], api=api, output_dir=tmp_path)
    assert result["action"] == "invalid_state"
    assert api.posted


def test_stop_sets_pointer_status_without_new_artifact(tmp_path: Path) -> None:
    pointer = PointerState(
        state_version=1,
        session_id="issue-9",
        issue_number=9,
        status="awaiting_continue",
        rounds_requested=2,
        rounds_completed=1,
        current_focus="x",
        latest_run_id=55,
        latest_artifact_name="ai-sparring-issue-9-r1",
    )
    api = _ApiStub(comments=[{"id": 1, "body": encode_pointer(pointer)}], artifacts=[{"name": "ai-sparring-issue-9-r1"}])
    result = handle_issue_event(event=_event("/stop"), repo_root=Path(__file__).resolve().parents[3], api=api, output_dir=tmp_path)
    assert result["action"] == "stopped"
    assert "Status: stopped" in api.posted[-1]


def test_issue_body_missing_required_heading_fails_start(tmp_path: Path) -> None:
    bad = IssueRuntimeEvent(
        issue_number=9,
        issue_body="## Prompt\nX",
        comment_body="/sparring start",
        is_pull_request=False,
        repository="o/r",
        run_id=55,
    )
    api = _ApiStub(comments=[])
    with pytest.raises(ValueError):
        handle_issue_event(event=bad, repo_root=Path(__file__).resolve().parents[3], api=api, output_dir=tmp_path)

def test_artifact_names_are_step_scoped_and_concurrency_group_is_issue_scoped() -> None:
    workflow = (Path(__file__).resolve().parents[3] / ".github/workflows/ai-sparring-issue.yml").read_text(encoding="utf-8")
    assert "group: ai-sparring-issue-${{ github.event.issue.number }}" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "actions: read" in workflow
