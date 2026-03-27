from __future__ import annotations

import json
from pathlib import Path


def _build_final_summary(payload: dict) -> str:
    summary_lines = [
        "# Final Summary",
        "",
        f"Session status: `{payload['status']}`.",
        f"Requested rounds: {payload['rounds_requested']}; completed rounds: {payload['rounds_completed']}.",
        f"Recorded round entries: {len(payload['rounds'])}.",
    ]
    return "\n".join(summary_lines) + "\n"


def write_session_artifacts(output_dir: Path, payload: dict, *, ticket_draft_text: str | None = None, ticket_draft_reason: str | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    session_json = output_dir / "session.json"
    session_md = output_dir / "session.md"
    final_summary = output_dir / "final_summary.md"

    session_json.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# AI Sparring Session",
        "",
        f"- Status: `{payload['status']}`",
        f"- Mode: `{payload['mode']}`",
        f"- Rounds requested: `{payload['rounds_requested']}`",
        f"- Rounds completed: `{payload['rounds_completed']}`",
        "",
        "## Participants",
        f"- Drafter: `{payload['participants']['drafter']['provider']}` / `{payload['participants']['drafter']['model']}`",
        f"- Reviewer: `{payload['participants']['reviewer']['provider']}` / `{payload['participants']['reviewer']['model']}`",
        "",
        "## Context Sources",
    ]
    for source in payload["context_sources"]:
        lines.append(f"- `{source['path']}` ({source['bytes']} bytes)")

    lines.extend(["", "## Rounds"])
    for round_item in payload["rounds"]:
        lines.append(f"### Round {round_item['index']}")
        for key in ("draft", "review", "revision"):
            if key in round_item:
                lines.append(f"- **{key}** ({round_item[key]['provider']}/{round_item[key]['model']}): {round_item[key]['text'][:120]}")
        lines.append(f"- Delta summary: {round_item.get('delta_summary', 'n/a')}")

    if payload.get("error"):
        lines.extend(["", "## Error", f"- `{payload['error']}`"])

    session_md.write_text("\n".join(lines) + "\n", encoding="utf-8")

    summary_text = _build_final_summary(payload)
    summary_lines = [summary_text.rstrip("\n"), "", "## Generated Ticket Draft", ""]
    if ticket_draft_text:
        summary_lines.append(ticket_draft_text.rstrip("\n"))
        (output_dir / "ticket_draft.md").write_text(ticket_draft_text, encoding="utf-8")
    else:
        summary_lines.append(f"Not generated: {ticket_draft_reason or 'unknown reason'}")

    final_summary.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
