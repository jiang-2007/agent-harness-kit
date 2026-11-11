"""Supervisor that routes tasks to registered sub-agents."""
from __future__ import annotations

from .agent import Agent
from .schema import Message


class Supervisor:
    """A lightweight orchestrator holding named sub-agents.

    The supervisor does not call a model itself; it looks up a registered
    sub-agent by name and delegates a task to it, returning that agent's reply.
    This mirrors the top-level routing pattern in multi-agent harnesses: one
    coordinator decides which specialist handles a request.
    """

    def __init__(self) -> None:
        self._agents: dict[str, Agent] = {}

    def register(self, name: str, agent: Agent) -> None:
        self._agents[name] = agent

    def names(self) -> list[str]:
        return sorted(self._agents)

    def delegate(self, agent_name: str, task: str) -> Message:
        if agent_name not in self._agents:
            raise KeyError(f"sub-agent not found: {agent_name}")
        return self._agents[agent_name].run(task)
