import types

import pytest

from tools.ai_sparring.errors import FatalProviderError, TransientProviderError
from tools.ai_sparring.providers.anthropic_provider import _normalize_provider_exception as normalize_anthropic
from tools.ai_sparring.providers.base import ProviderResult
from tools.ai_sparring.providers.openai_provider import OpenAIProvider


class _TransientThenOkClient:
    def __init__(self) -> None:
        self.calls = 0
        self.responses = self

    def create(self, **kwargs):
        self.calls += 1
        if self.calls == 1:
            err = Exception("rate limited")
            err.status_code = 429
            raise err
        return types.SimpleNamespace(output_text="ok", id="req-1")


def test_retry_retries_only_transient_failures(monkeypatch) -> None:
    monkeypatch.setattr("tools.ai_sparring.retry.time.sleep", lambda *_: None)
    provider = OpenAIProvider(model="gpt-test", api_key="k", client=_TransientThenOkClient())
    result = provider.generate(input_text="hello")
    assert result.attempts_used == 2


def test_provider_contract_normalizes_request_id_and_attempts() -> None:
    client = types.SimpleNamespace(
        responses=types.SimpleNamespace(create=lambda **kwargs: types.SimpleNamespace(output_text="hello", id=None, request_id=None))
    )
    provider = OpenAIProvider(model="gpt-test", api_key="k", client=client)
    result = provider.generate(input_text="hello")
    assert isinstance(result, ProviderResult)
    assert result.request_id is None
    assert result.attempts_used == 1


def test_normalize_provider_errors() -> None:
    transient = Exception("temporary")
    transient.status_code = 500
    assert isinstance(normalize_anthropic(transient), TransientProviderError)
    assert isinstance(normalize_anthropic(Exception("bad auth")), FatalProviderError)
