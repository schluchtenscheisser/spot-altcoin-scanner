from pathlib import Path
import zipfile
from io import BytesIO

import pytest

from tools.ai_sparring.issue_driver import IssueRuntimeEvent, handle_issue_event
from tools.ai_sparring.issue_state import decode_pointer, encode_pointer, PointerState


class _ApiStub:
    def __init__(self, comments=None, artifacts=None, artifact_zip_by_id=None):
        self._comments = comments or []
        self._artifacts = artifacts or []
        self._artifact_zip_by_id = artifact_zip_by_id or {}
        self.posted = []

    def list_issue_comments(self, issue_number: int):
        return self._comments

    def post_issue_comment(self, issue_number: int, body: str):
        self.posted.append(body)
        return {"id": len(self.posted)}

    def list_run_artifacts(self, run_id: int):
        return self._artifacts

    def download_artifact_zip(self, artifact_id: int):
        return self._artifact_zip_by_id[artifact_id]


def _zip_with_file(path: str, content: str) -> bytes:
    buff = BytesIO()
    with zipfile.ZipFile(buff, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(path, content)
    return buff.getvalue()


def _event(comment: str) -> IssueRuntimeEvent:
    return IssueRuntimeEvent(
        issue_number=9,
        issue_body="""## Prompt\nImprove it\n\n## Mode\nticket_review\n\n## Rounds\n1\n\n## Drafter Provider\n\n## Drafter Model\n\n## Reviewer Provider\n\n## Reviewer Model\n\n## Extra Context Paths\n""",
        comment_body=comment,
        is_pull_request=False,
        repository="o/r",
        run_id=55,
    )


def _event_with_rounds(comment: str, rounds: int) -> IssueRuntimeEvent:
    return IssueRuntimeEvent(
        issue_number=9,
        issue_body=f"""## Prompt
Improve it

## Mode
ticket_review

## Rounds
{rounds}

## Drafter Provider

## Drafter Model

## Reviewer Provider

## Reviewer Model

## Extra Context Paths
""",
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
        latest_artifact_name="ai-sparring-issue-9-55",
    )
    api = _ApiStub(
        comments=[{"id": 1, "body": encode_pointer(pointer)}],
        artifacts=[{"id": 101, "name": "ai-sparring-issue-9-55"}],
        artifact_zip_by_id={101: _zip_with_file("final_summary.md", "done")},
    )
    result = handle_issue_event(event=_event("/stop"), repo_root=Path(__file__).resolve().parents[3], api=api, output_dir=tmp_path)
    assert result["action"] == "stopped"
    assert "Status: stopped" in api.posted[-1]
    assert "done" in api.posted[-1]


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

def test_artifact_names_match_pointer_resolution_and_concurrency_group_is_issue_scoped() -> None:
    workflow = (Path(__file__).resolve().parents[3] / ".github/workflows/ai-sparring-issue.yml").read_text(encoding="utf-8")
    assert "group: ai-sparring-issue-${{ github.event.issue.number }}" in workflow
    assert "cancel-in-progress: false" in workflow
    assert "actions: read" in workflow
    assert "name: ai-sparring-issue-${{ github.event.issue.number }}-${{ github.run_id }}" in workflow


def test_start_executes_only_one_round_even_when_issue_requests_multiple(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def _fake_run_session(*, config, repo_root):
        captured["rounds"] = config.rounds
        return {
            "status": "completed",
            "rounds_completed": 1,
            "rounds_requested": config.rounds,
            "rounds": [{"draft": {"text": "d"}, "review": {"text": "r"}, "revision": {"text": "v"}, "delta_summary": "ok"}],
        }

    monkeypatch.setattr("tools.ai_sparring.issue_driver.run_session", _fake_run_session)
    api = _ApiStub(comments=[])
    result = handle_issue_event(
        event=_event_with_rounds("/sparring start", rounds=3),
        repo_root=Path(__file__).resolve().parents[3],
        api=api,
        output_dir=tmp_path,
    )
    assert captured["rounds"] == 1
    assert result["status"] == "awaiting_continue"
    assert "Round: 1/3" in api.posted[-1]
    assert "Status: awaiting_continue" in api.posted[-1]


def test_continue_executes_exactly_one_additional_round(monkeypatch, tmp_path: Path) -> None:
    captured = {}

    def _fake_run_session(*, config, repo_root):
        captured["rounds"] = config.rounds
        return {
            "status": "completed",
            "rounds_completed": 1,
            "rounds_requested": config.rounds,
            "rounds": [{"draft": {"text": "d"}, "review": {"text": "r"}, "revision": {"text": "v"}, "delta_summary": "ok"}],
        }

    monkeypatch.setattr("tools.ai_sparring.issue_driver.run_session", _fake_run_session)
    pointer = PointerState(
        state_version=1,
        session_id="issue-9",
        issue_number=9,
        status="awaiting_continue",
        rounds_requested=3,
        rounds_completed=1,
        current_focus="x",
        latest_run_id=55,
        latest_artifact_name="ai-sparring-issue-9-55",
    )
    api = _ApiStub(comments=[{"id": 1, "body": encode_pointer(pointer)}], artifacts=[{"name": "ai-sparring-issue-9-55"}])
    result = handle_issue_event(
        event=_event_with_rounds("/continue", rounds=3),
        repo_root=Path(__file__).resolve().parents[3],
        api=api,
        output_dir=tmp_path,
    )
    assert captured["rounds"] == 1
    assert result["status"] == "awaiting_continue"
    assert "Round: 2/3" in api.posted[-1]


def test_start_pointer_uses_run_id_based_artifact_name(monkeypatch, tmp_path: Path) -> None:
    def _fake_run_session(*, config, repo_root):
        return {
            "status": "completed",
            "rounds_completed": 1,
            "rounds_requested": config.rounds,
            "rounds": [{"draft": {"text": "d"}, "review": {"text": "r"}, "revision": {"text": "v"}, "delta_summary": "ok"}],
        }

    monkeypatch.setattr("tools.ai_sparring.issue_driver.run_session", _fake_run_session)
    api = _ApiStub(comments=[])
    handle_issue_event(
        event=_event_with_rounds("/sparring start", rounds=2),
        repo_root=Path(__file__).resolve().parents[3],
        api=api,
        output_dir=tmp_path,
    )
    state = decode_pointer(api.posted[-1])
    assert state.latest_artifact_name == "ai-sparring-issue-9-55"
