"""Deterministic offline provider for demos, tests and CI.

No API key, no network. It recognises a ``calc: <expression>`` hint and emits a
calculator tool call; otherwise it returns a canned echo reply. Swap this for
an OpenAI-compatible or local model provider in production.
"""
from __future__ import annotations

import re

from ..schema import Message, ToolCall
from .base import LLMProvider

_CALC_RE = re.compile(r"calc:\s*(.+)")


class MockProvider(LLMProvider):
    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
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
