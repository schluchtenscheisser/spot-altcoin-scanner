from __future__ import annotations

from tools.ai_sparring.providers.base import ProviderResult, SparringProvider


class FakeProvider(SparringProvider):
    """Deterministic synthetic provider for dry-runs."""

    provider_name = "fake"

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def generate(self, *, input_text: str) -> ProviderResult:
        compact = " ".join(input_text.split())
        return ProviderResult(
            provider=self.provider_name,
            model=None,
            text=f"FAKE_PROVIDER_SYNTHETIC_OUTPUT | {compact[:160]}",
            attempts_used=1,
            request_id=None,
        )
