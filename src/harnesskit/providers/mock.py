"""Deterministic offline provider for demos, tests and CI.

No API key, no network. It recognises a ``calc: <expression>`` hint and emits a
calculator tool call; otherwise it returns a canned echo reply. Swap this for
an OpenAI-compatible or local model provider in production.
"""
from __future__ import annotations

import re
from collections.abc import Iterator

from ..schema import Message, StreamChunk, ToolCall
from .base import LLMProvider

_CALC_RE = re.compile(r"calc:\s*(.+)")


class MockProvider(LLMProvider):
    def _reply(self, messages: list[Message]) -> Message:
        last = next((m for m in reversed(messages) if m.role == "user"), None)
        text = last.content if last else ""

        match = _CALC_RE.search(text)
        if match:
            return Message(
                role="assistant",
                tool_calls=[
                    ToolCall(
                        name="calculator",
                        arguments={"expression": match.group(1).strip()},
                    )
                ],
            )
        return Message(role="assistant", content=f"[mock] received: {text}")

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
        return self._reply(messages)

    def stream(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Iterator[StreamChunk]:
        """Yield the canned reply word by word for a deterministic stream demo."""
        reply = self._reply(messages)
        for call in reply.tool_calls:
            yield StreamChunk(tool_call=call)

        words = reply.content.split(" ") if reply.content else []
        if not words:
            yield StreamChunk(done=True)
            return
        for index, word in enumerate(words):
            trailing_space = " " if index < len(words) - 1 else ""
            yield StreamChunk(
                content=word + trailing_space,
                done=index == len(words) - 1,
            )
