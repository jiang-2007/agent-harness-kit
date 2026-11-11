"""Supervisor that routes tasks to registered sub-agents."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field

from .agent import Agent
from .schema import Message


@dataclass
class AggregateResult:
    """Outcome of delegating one task to many sub-agents.

    ``replies`` maps agent name to its final reply; ``errors`` maps agent name
    to the exception message for any agent that failed. The two dicts partition
    the requested agents.
    """

    replies: dict[str, Message] = field(default_factory=dict)
    errors: dict[str, str] = field(default_factory=dict)

    @property
    def names(self) -> list[str]:
        return sorted(self.replies)

    @property
    def summary(self) -> str:
        """A plain-text digest that combines every successful reply."""
        if not self.replies:
            return ""
        return "\n\n".join(
            f"## {name}\n{reply.content}"
            for name, reply in sorted(self.replies.items())
        )


class Supervisor:
    """A lightweight orchestrator holding named sub-agents.

    The supervisor does not call a model itself; it looks up registered
    sub-agents and delegates tasks to them. It supports single delegation,
    fan-out to a custom mapping of agents to tasks, and broadcasting the same
    task to every registered agent. Fan-out runs on a thread pool by default;
    each sub-agent keeps its own memory, so parallel delegation stays isolated.
    """

    def __init__(self, max_workers: int = 4) -> None:
        self._agents: dict[str, Agent] = {}
        self._max_workers = max_workers

    def register(self, name: str, agent: Agent) -> None:
        self._agents[name] = agent

    def names(self) -> list[str]:
        return sorted(self._agents)

    def delegate(self, agent_name: str, task: str) -> Message:
        """Delegate a task to one registered sub-agent and return its reply."""
        if agent_name not in self._agents:
            raise KeyError(f"sub-agent not found: {agent_name}")
        return self._agents[agent_name].run(task)

    def delegate_many(
        self,
        mapping: dict[str, str],
        parallel: bool = True,
    ) -> AggregateResult:
        """Delegate a distinct task to each named sub-agent.

        Args:
            mapping: ``{agent_name: task}`` pairs to run.
            parallel: Run agents concurrently on a thread pool. When false,
                agents run in registration order on the calling thread.
        """
        missing = [name for name in mapping if name not in self._agents]
        if missing:
            raise KeyError(f"sub-agent not found: {missing[0]}")

        result = AggregateResult()

        def _run(name: str, task: str) -> tuple[str, Message]:
            return name, self._agents[name].run(task)

        if not parallel:
            for name, task in mapping.items():
                try:
                    _, reply = _run(name, task)
                    result.replies[name] = reply
                except Exception as exc:  # keep one failure from aborting the batch
                    result.errors[name] = str(exc)
            return result

        with ThreadPoolExecutor(max_workers=self._max_workers) as pool:
            futures = {
                pool.submit(_run, name, task): name
                for name, task in mapping.items()
            }
            for future in as_completed(futures):
                name = futures[future]
                try:
                    _, reply = future.result()
                    result.replies[name] = reply
                except Exception as exc:  # keep one failure from aborting the batch
                    result.errors[name] = str(exc)
        return result

    def broadcast(self, task: str, parallel: bool = True) -> AggregateResult:
        """Send the same task to every registered sub-agent."""
        return self.delegate_many(
            {name: task for name in self._agents},
            parallel=parallel,
        )
