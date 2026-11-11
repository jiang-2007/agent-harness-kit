"""Retry wrapper around a provider for transient upstream failures."""
from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Callable

from ..schema import Message, StreamChunk
from .base import LLMProvider

Sleeper = Callable[[float], None]


class RetryProvider(LLMProvider):
    """Wrap a provider and retry transient ``complete`` failures.

    A real upstream can drop a connection or return a transient 5xx; this
    wrapper retries up to ``max_retries`` times, waiting ``backoff`` seconds
    between attempts. The sleeper is injectable so tests never actually sleep.
    ``stream`` is delegated to the inner provider unchanged.
    """

    def __init__(
        self,
        inner: LLMProvider,
        max_retries: int = 2,
        backoff: float = 0.0,
        sleeper: Sleeper | None = None,
    ) -> None:
        self.inner = inner
        self.max_retries = max_retries
        self.backoff = backoff
        self._sleep: Sleeper = sleeper or time.sleep
        self.attempts = 0

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            self.attempts += 1
            try:
                return self.inner.complete(messages, tools=tools)
            except Exception as exc:  # noqa: BLE001 - retry transient failure
                last_error = exc
                if attempt < self.max_retries:
                    self._sleep(self.backoff)
        assert last_error is not None
        raise last_error

    def stream(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Iterator[StreamChunk]:
        yield from self.inner.stream(messages, tools=tools)
