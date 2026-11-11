"""Agent configuration value object."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentConfig:
    name: str
    system_prompt: str = "You are a helpful, concise agent."
    provider: str = "mock"
    max_steps: int = 8
    max_tool_calls: int = 10
    dry_run: bool = False
    tools: list[str] = field(default_factory=list)
    allowlist: list[str] | None = None
