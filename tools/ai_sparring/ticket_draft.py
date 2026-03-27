from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from tools.ai_sparring.providers.base import ProviderResult, SparringProvider

TICKET_DRAFTER_SYSTEM_PROMPT = (
    "You are generating a Codex-ready implementation ticket draft in English. "
    "Follow docs/tickets/_TEMPLATE.md section structure, be deterministic, explicit about defaults/validation/edge cases, "
    "include concrete tests, and output Markdown only (no JSON, no extra commentary)."
)


def derive_session_id(payload: dict) -> str:
    existing = payload.get("session_id")
    if isinstance(existing, str) and existing.strip():
        return existing
    canonical = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(canonical).hexdigest()[:12]
    return f"sess-{digest}"


def slugify_title(title: str, *, max_len: int = 60) -> str:
    normalized = title.lower().encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized)
    slug = re.sub(r"-+", "-", slug).strip("-")
    if not slug:
        slug = "ticket-draft"
    return slug[:max_len].strip("-") or "ticket-draft"


def _read_utf8_text(path: Path) -> str:
    if not path.exists() or not path.is_file():
        raise ValueError(f"required file missing: {path.as_posix()}")
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"required file is not UTF-8 readable: {path.as_posix()}") from exc


def _extract_title(markdown: str) -> str | None:
    first_line = markdown.splitlines()[0] if markdown.splitlines() else ""
    if first_line.strip() != "---":
        return None
    for line in markdown.splitlines()[1:80]:
        if line.strip() == "---":
            break
        if line.lower().startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def generate_ticket_draft(
    *,
    repo_root: Path,
    provider: SparringProvider,
    payload: dict,
    final_summary_text: str,
    mode: str,
) -> tuple[dict, str | None, str | None]:
    participants = payload["participants"]
    session_id = derive_session_id(payload)
    base = {
        "status": "failed",
        "provider": participants["drafter"]["provider"],
        "model": participants["drafter"]["model"],
        "session_id": session_id,
        "path": None,
        "title": None,
        "writeback": {
            "requested": False,
            "status": "not_requested",
            "branch": None,
            "target_path": None,
            "pull_request_number": None,
            "pull_request_url": None,
            "commit_sha": None,
            "error": None,
        },
    }

    if payload.get("status") != "completed":
        base["status"] = "skipped_not_completed"
        return base, None, "session status is not completed"

    template_path = repo_root / "docs/tickets/_TEMPLATE.md"
    checklist_path = repo_root / "docs/tickets/_TICKET_PREFLIGHT_CHECKLIST.md"
    try:
        template_text = _read_utf8_text(template_path)
        checklist_text = _read_utf8_text(checklist_path)
    except ValueError as exc:
        base["status"] = "failed"
        return base, None, str(exc)

    final_revision = payload["rounds"][-1]["revision"]["text"] if payload.get("rounds") else ""
    prompt_parts = [
        f"original_prompt:\n{payload['prompt']}",
        f"selected_mode:\n{mode}",
        f"participants:\n{json.dumps(participants, indent=2, ensure_ascii=False)}",
        f"context_sources:\n{json.dumps(payload.get('context_sources', []), indent=2, ensure_ascii=False)}",
        f"completed_session_json:\n{json.dumps(payload, indent=2, ensure_ascii=False)}",
        f"completed_final_summary:\n{final_summary_text}",
        f"final_round_revision:\n{final_revision}",
        f"ticket_template_markdown:\n{template_text}",
        f"ticket_preflight_checklist_markdown:\n{checklist_text}",
    ]
    protocol_input = "\n\n".join(prompt_parts)
    full_input = f"system_prompt:\n{TICKET_DRAFTER_SYSTEM_PROMPT}\n\n{protocol_input}"

    try:
        result: ProviderResult = provider.generate(input_text=full_input)
    except Exception as exc:  # provider errors are recorded as ticket draft failure
        base["status"] = "failed"
        return base, None, f"ticket draft generation failed: {exc}"
    markdown = result.text.strip()
    if not markdown.startswith("---"):
        base["status"] = "failed"
        return base, None, "generated ticket draft is missing required YAML frontmatter"

    title = _extract_title(markdown)
    if not title:
        base["status"] = "failed"
        return base, None, "generated ticket draft frontmatter missing title"

    base["status"] = "generated"
    base["path"] = "ticket_draft.md"
    base["title"] = title
    return base, markdown + ("\n" if not markdown.endswith("\n") else ""), None
