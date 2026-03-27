from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from tools.ai_sparring.context_loader import load_context
from tools.ai_sparring.errors import FatalProviderError, PreflightValidationError, TransientProviderError
from tools.ai_sparring.output_writer import write_session_artifacts
from tools.ai_sparring.providers import PROVIDER_NAMES, build_provider

ALLOWED_MODES = {"ticket_review", "implementation_planning", "roadmap_review"}


@dataclass(frozen=True)
class SessionConfig:
    prompt: str
    mode: str
    rounds: int
    drafter_provider: str
    drafter_model: str | None
    reviewer_provider: str
    reviewer_model: str | None
    context_paths: tuple[str, ...]
    output_dir: Path


def _validate_preflight(config: SessionConfig, repo_root: Path) -> list[dict[str, str | int]]:
    if not config.prompt.strip():
        raise PreflightValidationError("Invalid prompt: must be non-empty")
    if config.mode not in ALLOWED_MODES:
        raise PreflightValidationError(f"Invalid mode: {config.mode}")
    if not isinstance(config.rounds, int) or not 1 <= config.rounds <= 3:
        raise PreflightValidationError("Invalid rounds: must be an integer in range 1..3")

    for role, provider, model in (
        ("drafter", config.drafter_provider, config.drafter_model),
        ("reviewer", config.reviewer_provider, config.reviewer_model),
    ):
        if provider not in PROVIDER_NAMES:
            raise PreflightValidationError(f"Invalid provider for {role}: {provider}")
        if provider in {"openai", "anthropic"} and not (model and model.strip()):
            raise PreflightValidationError(f"Missing required model id for provider '{provider}' ({role})")

    needs_openai = config.drafter_provider == "openai" or config.reviewer_provider == "openai"
    needs_anthropic = config.drafter_provider == "anthropic" or config.reviewer_provider == "anthropic"
    if needs_openai and not os.getenv("OPENAI_API_KEY"):
        raise PreflightValidationError("Missing required API key: OPENAI_API_KEY")
    if needs_anthropic and not os.getenv("ANTHROPIC_API_KEY"):
        raise PreflightValidationError("Missing required API key: ANTHROPIC_API_KEY")

    return load_context(repo_root=repo_root, extra_paths=list(config.context_paths))


def _build_input(
    *,
    prompt: str,
    mode: str,
    contexts: list[dict[str, str | int]],
    round_idx: int,
    stage: str,
    draft_text: str | None = None,
    review_text: str | None = None,
    previous_revision_text: str | None = None,
) -> str:
    lines = [
        f"mode={mode}",
        f"round={round_idx}",
        f"stage={stage}",
        "prompt:",
        prompt,
        "context:",
    ]
    lines.extend(f"- {item['path']} ({item['bytes']} bytes)" for item in contexts)
    if previous_revision_text:
        lines.extend(["previous_revision:", previous_revision_text])
    if draft_text:
        lines.extend(["draft:", draft_text])
    if review_text:
        lines.extend(["review:", review_text])
    return "\n".join(lines)


def run_session(config: SessionConfig, repo_root: Path) -> dict:
    contexts = _validate_preflight(config=config, repo_root=repo_root)

    drafter = build_provider(
        config.drafter_provider,
        model=config.drafter_model,
        api_key=os.getenv("OPENAI_API_KEY") if config.drafter_provider == "openai" else os.getenv("ANTHROPIC_API_KEY"),
    )
    reviewer = build_provider(
        config.reviewer_provider,
        model=config.reviewer_model,
        api_key=os.getenv("OPENAI_API_KEY") if config.reviewer_provider == "openai" else os.getenv("ANTHROPIC_API_KEY"),
    )

    payload = {
        "session_version": 2,
        "status": "completed",
        "mode": config.mode,
        "prompt": config.prompt,
        "rounds_requested": config.rounds,
        "rounds_completed": 0,
        "participants": {
            "drafter": {"provider": config.drafter_provider, "model": config.drafter_model if config.drafter_provider != "fake" else None},
            "reviewer": {"provider": config.reviewer_provider, "model": config.reviewer_model if config.reviewer_provider != "fake" else None},
        },
        "context_sources": [{"path": item["path"], "bytes": item["bytes"]} for item in contexts],
        "rounds": [],
        "error": None,
    }

    previous_revision = None
    try:
        for round_idx in range(1, config.rounds + 1):
            round_data = {"index": round_idx}

            draft_input = _build_input(
                prompt=config.prompt,
                mode=config.mode,
                contexts=contexts,
                round_idx=round_idx,
                stage="draft",
                previous_revision_text=previous_revision,
            )
            draft = drafter.generate(input_text=draft_input)
            round_data["draft"] = draft.__dict__

            review_input = _build_input(
                prompt=config.prompt,
                mode=config.mode,
                contexts=contexts,
                round_idx=round_idx,
                stage="review",
                draft_text=draft.text,
            )
            review = reviewer.generate(input_text=review_input)
            round_data["review"] = review.__dict__

            revision_input = _build_input(
                prompt=config.prompt,
                mode=config.mode,
                contexts=contexts,
                round_idx=round_idx,
                stage="revision",
                draft_text=draft.text,
                review_text=review.text,
            )
            revision = drafter.generate(input_text=revision_input)
            round_data["revision"] = revision.__dict__

            round_data["delta_summary"] = (
                f"round={round_idx};review_present=yes;revision_present=yes;"
                f"drafter={draft.provider}/{draft.model};reviewer={review.provider}/{review.model}"
            )
            payload["rounds"].append(round_data)
            payload["rounds_completed"] = round_idx
            previous_revision = revision.text

    except (FatalProviderError, TransientProviderError) as exc:
        payload["error"] = str(exc)
        payload["status"] = "failed_partial" if payload["rounds"] else "failed_runtime"

    write_session_artifacts(config.output_dir, payload)
    return payload
