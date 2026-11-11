"""LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterator

from ..schema import Message, StreamChunk


class LLMProvider(ABC):
    """Pluggable model backend.

    Implementations translate the harness ``Message`` trace into whatever wire
    format their upstream model expects, and return an assistant ``Message``
    that either carries plain content or a list of ``ToolCall`` requests.

    ``stream`` is optional: the default implementation replays the finished
    ``complete`` reply as a single chunk, so every provider works with the
    streaming agent loop. Backends with native streaming can override it to
    yield incremental deltas.
    """

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
        ...

    def stream(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Iterator[StreamChunk]:
        """Yield the reply incrementally; defaults to a single-chunk fallback."""
        reply = self.complete(messages, tools=tools)
        for call in reply.tool_calls:
            yield StreamChunk(tool_call=call)
        yield StreamChunk(content=reply.content, done=True)
