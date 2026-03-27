from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from tools.ai_sparring.github_api import GitHubApi
from tools.ai_sparring.ticket_draft import derive_session_id, slugify_title


@dataclass(frozen=True)
class WritebackPlan:
    session_id: str
    branch: str
    target_path: str


def compute_writeback_plan(*, payload: dict, utc_now: datetime | None = None) -> WritebackPlan:
    now = utc_now or datetime.now(timezone.utc)
    session_id = derive_session_id(payload)
    title = ((payload.get("ticket_draft") or {}).get("title") or "ticket-draft").strip()
    slug = slugify_title(title)
    date_part = now.strftime("%Y-%m-%d")
    branch = f"ai-sparring/drafts/{date_part}-{slug}-{session_id}"
    target_path = f"docs/tickets/drafts/{date_part}-{slug}-{session_id}.md"
    return WritebackPlan(session_id=session_id, branch=branch, target_path=target_path)


def _git(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def _is_clean_tree(repo_root: Path) -> bool:
    return _git(repo_root, "status", "--porcelain") == ""


def _remote_branch_exists(repo_root: Path, branch: str) -> bool:
    out = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch],
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    return out.returncode == 0 and bool(out.stdout.strip())


def _list_open_prs(api: GitHubApi, *, branch: str, base: str) -> list[dict]:
    owner = api.repo.split("/")[0]
    return api._request("GET", f"/repos/{api.repo}/pulls?state=open&head={owner}:{branch}&base={base}")


def perform_writeback(
    *,
    repo_root: Path,
    output_dir: Path,
    github_repo: str,
    github_token: str,
    writeback_enabled: bool,
    base_branch: str = "main",
    utc_now: datetime | None = None,
) -> dict:
    session_path = output_dir / "session.json"
    payload = json.loads(session_path.read_text(encoding="utf-8"))
    ticket = payload.setdefault("ticket_draft", {})
    wb = ticket.setdefault("writeback", {})
    wb.setdefault("requested", bool(writeback_enabled))

    def finalize(status: str, error: str | None = None) -> dict:
        wb["status"] = status
        wb.setdefault("branch", None)
        wb.setdefault("target_path", None)
        wb.setdefault("pull_request_number", None)
        wb.setdefault("pull_request_url", None)
        wb.setdefault("commit_sha", None)
        wb["error"] = error
        session_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return payload

    if not writeback_enabled:
        return finalize("not_requested")
    if ticket.get("status") != "generated" or ticket.get("path") != "ticket_draft.md":
        return finalize("skipped_no_draft", "ticket_draft.md not available")
    if payload.get("status") != "completed":
        return finalize("preflight_failed", "session status must be completed")
    if base_branch != "main":
        return finalize("preflight_failed", "base branch must be main")
    if not _is_clean_tree(repo_root):
        return finalize("preflight_failed", "working tree must be clean")

    plan = compute_writeback_plan(payload=payload, utc_now=utc_now)
    wb["branch"] = plan.branch
    wb["target_path"] = plan.target_path

    if not plan.target_path.startswith("docs/tickets/drafts/"):
        return finalize("preflight_failed", "target path outside docs/tickets/drafts/")

    api = GitHubApi(repo=github_repo, token=github_token)
    if _remote_branch_exists(repo_root, plan.branch):
        prs = _list_open_prs(api, branch=plan.branch, base=base_branch)
        if prs:
            pr = prs[0]
            wb["pull_request_number"] = pr.get("number")
            wb["pull_request_url"] = pr.get("html_url")
            return finalize("existing_pr")
        return finalize("branch_exists_without_pr", "remote branch exists without open PR")

    draft_text = (output_dir / "ticket_draft.md").read_text(encoding="utf-8")
    try:
        _git(repo_root, "checkout", base_branch)
        _git(repo_root, "checkout", "-b", plan.branch)
        target = repo_root / plan.target_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(draft_text, encoding="utf-8")
        _git(repo_root, "add", plan.target_path)
        filename = Path(plan.target_path).name
        _git(repo_root, "commit", "-m", f"Add AI sparring ticket draft: {filename}")
        commit_sha = _git(repo_root, "rev-parse", "HEAD")
        wb["commit_sha"] = commit_sha
        try:
            _git(repo_root, "push", "-u", "origin", plan.branch)
        except Exception as exc:
            return finalize("failed_before_push", str(exc))

        title = f"Add AI sparring ticket draft: {ticket.get('title') or 'Ticket Draft'}"
        pr_body = "\n".join(
            [
                "This PR was generated by ai-sparring.",
                "",
                f"- session_id: {plan.session_id}",
                "- source draft artifact: ticket_draft.md",
                f"- source mode: {payload.get('mode')}",
                "- source models:",
                f"  - {payload['participants']['drafter']['provider']}:{payload['participants']['drafter']['model']}",
                f"  - {payload['participants']['reviewer']['provider']}:{payload['participants']['reviewer']['model']}",
                "",
                "This PR contains a generated draft ticket for review.",
            ]
        )
        try:
            pr = api._request(
                "POST",
                f"/repos/{github_repo}/pulls",
                {"title": title, "head": plan.branch, "base": "main", "body": pr_body},
            )
        except Exception as exc:
            return finalize("failed_after_push", str(exc))

        wb["pull_request_number"] = pr.get("number")
        wb["pull_request_url"] = pr.get("html_url")
        return finalize("pr_opened")
    finally:
        _git(repo_root, "checkout", base_branch)
