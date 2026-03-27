from tools.ai_sparring.providers.anthropic_provider import AnthropicProvider
from tools.ai_sparring.providers.base import ProviderResult, SparringProvider
from tools.ai_sparring.providers.fake_provider import FakeProvider
from tools.ai_sparring.providers.openai_provider import OpenAIProvider

PROVIDER_NAMES = ("fake", "openai", "anthropic")


def build_provider(name: str, *, model: str | None, api_key: str | None) -> SparringProvider:
    if name == "fake":
        return FakeProvider(model=model)
    if name == "openai":
        return OpenAIProvider(model=model or "", api_key=api_key or "")
    if name == "anthropic":
        return AnthropicProvider(model=model or "", api_key=api_key or "")
    raise ValueError(f"Unsupported provider: {name}")


__all__ = [
    "ProviderResult",
    "SparringProvider",
    "FakeProvider",
    "OpenAIProvider",
    "AnthropicProvider",
    "PROVIDER_NAMES",
    "build_provider",
]
