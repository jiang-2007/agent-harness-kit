"""Core data structures shared across the harness."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Optional

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    """A request issued by the model to invoke a registered tool."""

    name: str
    arguments: dict
    id: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "arguments": self.arguments,
            "id": self.id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCall":
        return cls(
            name=data["name"],
            arguments=dict(data.get("arguments") or {}),
            id=data.get("id"),
        )


@dataclass
class StreamChunk:
    """One incremental piece of a streamed provider reply.

    ``content`` carries a text delta; ``tool_call`` delivers a complete tool
    request (typically on the final chunk); ``done`` marks the end of the reply.
    """

    content: str = ""
    tool_call: Optional[ToolCall] = None
    done: bool = False


@dataclass
class Message:
    """A single entry in the conversation trace.

    An assistant message may carry zero or more ``tool_calls``. A tool result
    message references the call it answers via ``tool_call_id``.
    """

    role: Role
    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "tool_calls": [call.to_dict() for call in self.tool_calls],
            "tool_call_id": self.tool_call_id,
            "name": self.name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        return cls(
            role=data["role"],
            content=data.get("content", ""),
            tool_calls=[ToolCall.from_dict(c) for c in data.get("tool_calls") or []],
            tool_call_id=data.get("tool_call_id"),
            name=data.get("name"),
        )
