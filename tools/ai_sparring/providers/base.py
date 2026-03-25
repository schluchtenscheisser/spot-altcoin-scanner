from __future__ import annotations

from abc import ABC, abstractmethod


class SparringProvider(ABC):
    @abstractmethod
    def run(
        self,
        *,
        prompt: str,
        mode: str,
        rounds: int,
        contexts: list[dict[str, str | int]],
    ) -> list[dict[str, str]]:
        """Produce deterministic session messages."""
