import json
import subprocess
from pathlib import Path

from tools.ai_sparring.writeback import perform_writeback


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True)


def _init_repo(tmp_path: Path) -> tuple[Path, Path]:
    remote = tmp_path / "remote.git"
    work = tmp_path / "work"
    _git(tmp_path, "init", "--bare", str(remote))
    _git(tmp_path, "init", str(work))
    _git(work, "config", "user.email", "test@example.com")
    _git(work, "config", "user.name", "Test")
    (work / "README.md").write_text("x\n", encoding="utf-8")
    _git(work, "add", "README.md")
    _git(work, "commit", "-m", "init")
    _git(work, "branch", "-M", "main")
    _git(work, "remote", "add", "origin", str(remote))
    _git(work, "push", "-u", "origin", "main")
    return work, remote


def _write_artifacts(base: Path) -> Path:
    out = base / "artifacts"
    out.mkdir()
    payload = {
        "status": "completed",
        "mode": "ticket_review",
        "participants": {
            "drafter": {"provider": "openai", "model": "gpt-5"},
            "reviewer": {"provider": "anthropic", "model": "claude"},
        },
        "ticket_draft": {
            "status": "generated",
            "path": "ticket_draft.md",
            "title": "A New Draft",
            "writeback": {
                "requested": True,
                "status": "not_requested",
                "branch": None,
                "target_path": None,
                "pull_request_number": None,
                "pull_request_url": None,
                "commit_sha": None,
                "error": None,
            },
        },
    }
    (out / "session.json").write_text(json.dumps(payload), encoding="utf-8")
    (out / "ticket_draft.md").write_text("---\ntitle: \"A New Draft\"\n---\nBody\n", encoding="utf-8")
    return out


def test_existing_branch_without_pr_fails_cleanly(monkeypatch, tmp_path) -> None:
    work, _ = _init_repo(tmp_path)
    artifacts = _write_artifacts(tmp_path)

    class _Api:
        def __init__(self, *args, **kwargs):
            self.repo = "owner/repo"

        def _request(self, method, path, payload=None):
            return []

    monkeypatch.setattr("tools.ai_sparring.writeback.GitHubApi", _Api)
    monkeypatch.setattr("tools.ai_sparring.writeback._remote_branch_exists", lambda *a, **k: True)

    result = perform_writeback(
        repo_root=work,
        output_dir=artifacts,
        github_repo="owner/repo",
        github_token="x",
        writeback_enabled=True,
    )
    assert result["ticket_draft"]["writeback"]["status"] == "branch_exists_without_pr"


def test_existing_branch_with_open_pr_is_idempotent_success(monkeypatch, tmp_path) -> None:
    work, _ = _init_repo(tmp_path)
    artifacts = _write_artifacts(tmp_path)

    class _Api:
        def __init__(self, *args, **kwargs):
            self.repo = "owner/repo"

        def _request(self, method, path, payload=None):
            return [{"number": 7, "html_url": "https://example/pr/7"}]

    monkeypatch.setattr("tools.ai_sparring.writeback.GitHubApi", _Api)
    monkeypatch.setattr("tools.ai_sparring.writeback._remote_branch_exists", lambda *a, **k: True)

    result = perform_writeback(
        repo_root=work,
        output_dir=artifacts,
        github_repo="owner/repo",
        github_token="x",
        writeback_enabled=True,
    )
    wb = result["ticket_draft"]["writeback"]
    assert wb["status"] == "existing_pr"
    assert wb["pull_request_number"] == 7


def test_artifact_directory_inside_repo_is_excluded_from_clean_tree_check(monkeypatch, tmp_path) -> None:
    work, _ = _init_repo(tmp_path)
    artifacts = _write_artifacts(work)

    class _Api:
        def __init__(self, *args, **kwargs):
            self.repo = "owner/repo"

        def _request(self, method, path, payload=None):
            return [{"number": 11, "html_url": "https://example/pr/11"}]

    monkeypatch.setattr("tools.ai_sparring.writeback.GitHubApi", _Api)
    monkeypatch.setattr("tools.ai_sparring.writeback._remote_branch_exists", lambda *a, **k: True)

    result = perform_writeback(
        repo_root=work,
        output_dir=artifacts,
        github_repo="owner/repo",
        github_token="x",
        writeback_enabled=True,
    )

    wb = result["ticket_draft"]["writeback"]
    assert wb["status"] == "existing_pr"
    assert wb["pull_request_number"] == 11
