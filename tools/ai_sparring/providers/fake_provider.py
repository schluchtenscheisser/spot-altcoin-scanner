from __future__ import annotations

from tools.ai_sparring.providers.base import SparringProvider


class FakeProvider(SparringProvider):
    """Deterministic synthetic provider for dry-runs."""

    def run(
        self,
        *,
        prompt: str,
        mode: str,
        rounds: int,
        contexts: list[dict[str, str | int]],
    ) -> list[dict[str, str]]:
        prompt_norm = " ".join(prompt.split())
        context_summary = ", ".join(
            f"{item['path']}({item['chars']})" for item in contexts
        )
        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": (
                    "FAKE_PROVIDER_SYNTHETIC_OUTPUT | "
                    f"mode={mode} | rounds={rounds} | contexts={context_summary}"
                ),
            }
        ]
        for round_idx in range(1, rounds + 1):
            messages.append(
                {
                    "role": "assistant",
                    "content": (
                        "FAKE_PROVIDER_SYNTHETIC_OUTPUT | "
                        f"round={round_idx} | prompt={prompt_norm}"
                    ),
                }
            )
        return messages
