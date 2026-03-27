from __future__ import annotations

from tools.ai_sparring.errors import FatalProviderError, TransientProviderError
from tools.ai_sparring.providers.base import ProviderResult, SparringProvider
from tools.ai_sparring.retry import run_with_retry


class OpenAIProvider(SparringProvider):
    provider_name = "openai"

    def __init__(self, *, model: str, api_key: str, client=None) -> None:
        self.model = model
        if client is None:
            from openai import OpenAI

            client = OpenAI(api_key=api_key)
        self.client = client

    def generate(self, *, input_text: str) -> ProviderResult:
        def _call():
            try:
                response = self.client.responses.create(model=self.model, input=input_text)
            except Exception as exc:  # normalized below
                raise _normalize_provider_exception(exc) from exc
            text = getattr(response, "output_text", None) or ""
            if not text:
                raise FatalProviderError("OpenAI response did not include output_text")
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
