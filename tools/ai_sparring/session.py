from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from tools.ai_sparring.context_loader import DEFAULT_CONTEXT_SOURCES, load_default_context
from tools.ai_sparring.output_writer import write_session_artifacts
from tools.ai_sparring.providers import PROVIDERS

ALLOWED_MODES = {"ticket_review", "implementation_planning", "roadmap_review"}


@dataclass(frozen=True)
class SessionConfig:
    prompt: str
    provider: str
    mode: str
    rounds: int
    output_dir: Path


def validate_config(config: SessionConfig) -> None:
    if not config.prompt.strip():
        raise ValueError("Invalid prompt: must be non-empty")
    if config.provider not in PROVIDERS:
        available = ", ".join(sorted(PROVIDERS))
        raise ValueError(f"Invalid provider: {config.provider}. Allowed: {available}")
    if config.mode not in ALLOWED_MODES:
        allowed = ", ".join(sorted(ALLOWED_MODES))
        raise ValueError(f"Invalid mode: {config.mode}. Allowed: {allowed}")
    if not isinstance(config.rounds, int) or not 1 <= config.rounds <= 3:
        raise ValueError("Invalid rounds: must be an integer in range 1..3")


def run_session(config: SessionConfig, repo_root: Path) -> dict:
    validate_config(config)
    contexts = load_default_context(repo_root=repo_root)

    provider_cls = PROVIDERS[config.provider]
    provider = provider_cls()
    messages = provider.run(
        prompt=config.prompt,
        mode=config.mode,
        rounds=config.rounds,
        contexts=contexts,
    )

    payload = {
        "provider": config.provider,
        "mode": config.mode,
        "rounds": config.rounds,
        "prompt": config.prompt,
        "context_sources": list(DEFAULT_CONTEXT_SOURCES),
        "status": "success",
        "messages": messages,
    }
    write_session_artifacts(config.output_dir, payload)
    return payload
