"""Core data structures shared across the harness."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Optional

Role = Literal["system", "user", "assistant", "tool"]


@dataclass
class ToolCall:
    """A request issued by the model to invoke a registered tool."""

    name: str
    arguments: dict
    id: Optional[str] = None


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
