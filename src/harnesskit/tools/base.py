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


# Schema type name -> accepted Python types. ``boolean`` is checked separately
# because ``bool`` subclasses ``int`` and must not pass an integer check.
_TYPE_CHECKS: dict[str, tuple[type, ...]] = {
    "string": (str,),
    "integer": (int,),
    "number": (int, float),
    "boolean": (bool,),
    "array": (list,),
    "object": (dict,),
}


class Tool(ABC):
    """Base class for every callable tool exposed to the model."""

    name: str
    description: str
    parameters: dict

    @abstractmethod
    def run(self, **kwargs: Any) -> ToolResult:
        ...

    def validate(self, arguments: dict[str, Any]) -> list[str]:
        """Check provided arguments against the declared parameter schema.

        Returns a list of human-readable errors; an empty list means the
        arguments are acceptable. Missing arguments are left to the tool's
        own defaults; only supplied arguments are type-checked here.
        """
        errors: list[str] = []
        for arg_name, spec in self.parameters.items():
            if arg_name not in arguments:
                continue
            expected = spec.get("type")
            accepted = _TYPE_CHECKS.get(expected)
            if accepted is None:
                continue
            value = arguments[arg_name]
            if expected == "integer" and isinstance(value, bool):
                errors.append(f"argument '{arg_name}' must be an integer, got boolean")
            elif not isinstance(value, accepted):
                errors.append(
                    f"argument '{arg_name}' must be {expected}, "
                    f"got {type(value).__name__}"
                )
        return errors


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
