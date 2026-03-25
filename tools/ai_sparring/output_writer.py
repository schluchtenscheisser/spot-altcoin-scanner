from __future__ import annotations

import json
from pathlib import Path


def write_session_artifacts(output_dir: Path, payload: dict) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    session_json = output_dir / "session.json"
    session_md = output_dir / "session.md"
    final_summary = output_dir / "final_summary.md"

    session_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    markdown_lines = [
        "# AI Sparring Session",
        "",
        f"- Provider: `{payload['provider']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Rounds: `{payload['rounds']}`",
        "",
        "## Prompt",
        payload["prompt"],
        "",
        "## Context Sources",
    ]
    markdown_lines.extend(f"- `{path}`" for path in payload["context_sources"])
    markdown_lines.extend(["", "## Messages"])
    for message in payload["messages"]:
        markdown_lines.append(f"- **{message['role']}**: {message['content']}")
    session_md.write_text("\n".join(markdown_lines) + "\n", encoding="utf-8")

    summary_lines = [
        "# Final Summary",
        "",
        f"Mode `{payload['mode']}` with provider `{payload['provider']}` completed successfully.",
        f"Processed {len(payload['context_sources'])} fixed context sources across {payload['rounds']} round(s).",
        f"Status: `{payload['status']}`.",
    ]
    final_summary.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
