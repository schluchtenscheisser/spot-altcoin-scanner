from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from tools.ai_sparring.errors import PreflightValidationError
from tools.ai_sparring.github_api import GitHubApi
from tools.ai_sparring.issue_driver import IssueRuntimeEvent, handle_issue_event
from tools.ai_sparring.session import SessionConfig, run_session
from tools.ai_sparring.writeback import perform_writeback


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI sparring runtime CLI")
    parser.add_argument("command", nargs="?", choices=["issue-event", "writeback-artifact"])
    parser.add_argument("--prompt", help="Prompt text for the session")
    parser.add_argument(
        "--mode", default="ticket_review", choices=["ticket_review", "implementation_planning", "roadmap_review"]
    )
    parser.add_argument("--rounds", type=int, default=1, help="Round count in range 1..3 (default: 1)")
    parser.add_argument("--drafter-provider", default="fake", choices=["fake", "openai", "anthropic"])
    parser.add_argument("--drafter-model")
    parser.add_argument("--reviewer-provider", default="fake", choices=["fake", "openai", "anthropic"])
    parser.add_argument("--reviewer-model")
    parser.add_argument("--context-path", action="append", default=[])
    parser.add_argument("--output-dir", required=True, help="Directory for session artifacts")
    parser.add_argument("--event-path")
    parser.add_argument("--repo")
    parser.add_argument("--run-id", type=int)
    parser.add_argument("--writeback", action="store_true", default=False)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    if args.command is None:
        if not args.prompt:
            print("Missing required argument: --prompt", file=sys.stderr)
            return 2
        config = SessionConfig(
            prompt=args.prompt,
            mode=args.mode,
            rounds=args.rounds,
            drafter_provider=args.drafter_provider,
            drafter_model=args.drafter_model,
            reviewer_provider=args.reviewer_provider,
            reviewer_model=args.reviewer_model,
            context_paths=tuple(args.context_path),
            output_dir=Path(args.output_dir),
            writeback=bool(args.writeback),
        )
        try:
            payload = run_session(config=config, repo_root=repo_root)
        except PreflightValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        return 0 if payload["status"] == "completed" else 1

    if args.command == "issue-event":
        if not args.event_path or not args.repo or args.run_id is None:
            print("issue-event requires --event-path, --repo, and --run-id", file=sys.stderr)
            return 2
        event_payload = json.loads(Path(args.event_path).read_text(encoding="utf-8"))
        event = IssueRuntimeEvent(
            issue_number=event_payload["issue"]["number"],
            issue_body=event_payload["issue"]["body"] or "",
            comment_body=event_payload["comment"]["body"] or "",
            is_pull_request=bool(event_payload["issue"].get("pull_request")),
            repository=args.repo,
            run_id=args.run_id,
        )
        token = os.getenv("GITHUB_TOKEN", "")
        api = GitHubApi(repo=args.repo, token=token)
        handle_issue_event(event=event, repo_root=repo_root, api=api, output_dir=Path(args.output_dir))
        return 0

    if args.command == "writeback-artifact":
        if not args.repo:
            print("writeback-artifact requires --repo", file=sys.stderr)
            return 2
        token = os.getenv("GITHUB_TOKEN", "")
        if not token:
            print("writeback-artifact requires GITHUB_TOKEN", file=sys.stderr)
            return 2
        payload = perform_writeback(
            repo_root=repo_root,
            output_dir=Path(args.output_dir),
            github_repo=args.repo,
            github_token=token,
            writeback_enabled=bool(args.writeback),
            base_branch="main",
        )
        status = ((payload.get("ticket_draft") or {}).get("writeback") or {}).get("status")
        return 0 if status in {"pr_opened", "existing_pr", "not_requested", "skipped_no_draft"} else 1

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
