from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class ProviderResult:
    provider: str
    model: str | None
    text: str
    attempts_used: int
    request_id: str | None


class SparringProvider(ABC):
    provider_name: str

    @abstractmethod
    def generate(self, *, input_text: str) -> ProviderResult:
        """Generate one response for one protocol step."""
