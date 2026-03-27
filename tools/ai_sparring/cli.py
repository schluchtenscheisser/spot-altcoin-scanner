from __future__ import annotations

import argparse
import sys
from pathlib import Path

from tools.ai_sparring.errors import PreflightValidationError
from tools.ai_sparring.session import SessionConfig, run_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI sparring runtime CLI")
    parser.add_argument("--prompt", required=True, help="Prompt text for the session")
    parser.add_argument("--mode", default="ticket_review", choices=["ticket_review", "implementation_planning", "roadmap_review"])
    parser.add_argument("--rounds", type=int, default=1, help="Round count in range 1..3 (default: 1)")
    parser.add_argument("--drafter-provider", default="fake", choices=["fake", "openai", "anthropic"])
    parser.add_argument("--drafter-model")
    parser.add_argument("--reviewer-provider", default="fake", choices=["fake", "openai", "anthropic"])
    parser.add_argument("--reviewer-model")
    parser.add_argument("--context-path", action="append", default=[])
    parser.add_argument("--output-dir", required=True, help="Directory for session artifacts")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[2]
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
    )
    try:
        payload = run_session(config=config, repo_root=repo_root)
    except PreflightValidationError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return 0 if payload["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
