"""LLM provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from ..schema import Message


class LLMProvider(ABC):
    """Pluggable model backend.

    Implementations translate the harness ``Message`` trace into whatever wire
    format their upstream model expects, and return an assistant ``Message``
    that either carries plain content or a list of ``ToolCall`` requests.
    """

    @abstractmethod
    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
        ...
