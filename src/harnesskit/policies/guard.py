"""Lightweight policy guards evaluated before every tool call."""
from __future__ import annotations

from ..schema import ToolCall


class PolicyGuard:
    """Enforce a call budget and an optional tool allowlist.

    Policies run inside the agent loop: a blocked call is turned into a tool
    result so the model can observe the rejection and adapt, instead of the
    loop crashing.
    """

    def __init__(
        self,
        max_tool_calls: int = 10,
        allowlist: list[str] | None = None,
    ) -> None:
        self.max_tool_calls = max_tool_calls
        self.allowlist = allowlist
        self.calls = 0

    def check(self, call: ToolCall) -> tuple[bool, str]:
        self.calls += 1
        if self.calls > self.max_tool_calls:
            return False, f"tool call budget exceeded ({self.max_tool_calls})"
        if self.allowlist is not None and call.name not in self.allowlist:
            return False, f"tool '{call.name}' is not in the allowlist"
        return True, ""
