"""Tool abstraction and registry."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    content: str
    ok: bool = True
    error: str | None = None


class Tool(ABC):
    """Base class for every callable tool exposed to the model."""

    name: str
    description: str
    parameters: dict

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        ...


class ToolRegistry:
    """Name -> Tool lookup used by the agent loop."""

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise KeyError(f"tool not found: {name}")
        return self._tools[name]

    def names(self) -> list[str]:
        return sorted(self._tools)

    def specs(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]
