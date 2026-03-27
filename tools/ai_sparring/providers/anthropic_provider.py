from __future__ import annotations

from tools.ai_sparring.errors import FatalProviderError, TransientProviderError
from tools.ai_sparring.providers.base import ProviderResult, SparringProvider
from tools.ai_sparring.retry import run_with_retry


class AnthropicProvider(SparringProvider):
    provider_name = "anthropic"

    def __init__(self, *, model: str, api_key: str, client=None) -> None:
        self.model = model
        if client is None:
            from anthropic import Anthropic

            client = Anthropic(api_key=api_key)
        self.client = client

    def generate(self, *, input_text: str) -> ProviderResult:
        def _call():
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=800,
                    messages=[{"role": "user", "content": input_text}],
                )
            except Exception as exc:
                raise _normalize_provider_exception(exc) from exc
            blocks = getattr(response, "content", []) or []
            text_parts = [getattr(block, "text", "") for block in blocks if getattr(block, "type", "") == "text"]
            text = "\n".join(part for part in text_parts if part).strip()
            if not text:
                raise FatalProviderError("Anthropic response did not include text content")
            return ProviderResult(
                provider=self.provider_name,
                model=self.model,
                text=text,
                attempts_used=1,
                request_id=(getattr(response, "id", None) or getattr(response, "request_id", None)),
            )

        result, attempts = run_with_retry(_call)
        return ProviderResult(
            provider=result.provider,
            model=result.model,
            text=result.text,
            attempts_used=attempts,
            request_id=result.request_id,
        )


def _normalize_provider_exception(exc: Exception) -> Exception:
    status = getattr(exc, "status_code", None)
    if status in {429, 500, 502, 503, 504}:
        return TransientProviderError(str(exc))
    if isinstance(exc, TimeoutError):
        return TransientProviderError(str(exc))
    name = exc.__class__.__name__.lower()
    if "connection" in name or "timeout" in name:
        return TransientProviderError(str(exc))
    return FatalProviderError(str(exc))
