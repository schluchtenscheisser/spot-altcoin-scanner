from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

from tools.ai_sparring.errors import TransientProviderError

T = TypeVar("T")


RETRY_DELAYS_SECONDS: tuple[int, ...] = (5, 15)
MAX_ATTEMPTS = 3


def run_with_retry(call: Callable[[], T]) -> tuple[T, int]:
    """Run provider calls with exactly 3 total attempts (5s then 15s delay)."""
    attempt = 1
    while True:
        try:
            return call(), attempt
        except TransientProviderError:
            if attempt >= MAX_ATTEMPTS:
                raise
            time.sleep(RETRY_DELAYS_SECONDS[attempt - 1])
            attempt += 1
