from __future__ import annotations

import argparse
from pathlib import Path

from tools.ai_sparring.session import SessionConfig, run_session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI sparring dry-run foundation CLI")
    parser.add_argument("--prompt", required=True, help="Prompt text for the session")
    parser.add_argument("--provider", default="fake", help="Provider name (default: fake)")
    parser.add_argument(
        "--mode",
        default="ticket_review",
        help="Session mode (default: ticket_review)",
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=1,
        help="Round count in range 1..3 (default: 1)",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for session artifacts")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    repo_root = Path(__file__).resolve().parents[2]
    config = SessionConfig(
        prompt=args.prompt,
        provider=args.provider,
        mode=args.mode,
        rounds=args.rounds,
        output_dir=Path(args.output_dir),
    )
    run_session(config=config, repo_root=repo_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
