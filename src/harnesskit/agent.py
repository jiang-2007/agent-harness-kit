"""The agent runtime: a ReAct-style loop over provider, tools and memory."""
from __future__ import annotations

from .memory import ConversationMemory
from .policies.guard import PolicyGuard
from .providers.base import LLMProvider
from .schema import Message
from .tools.base import ToolRegistry


class Agent:
    """One conversational agent bound to a provider, a tool registry and a guard.

    The loop alternates: ask the provider for a reply -> execute any tool calls
    through the registry (after the policy guard) -> feed results back into
    memory -> repeat until the model answers without tool calls or the step
    budget is reached.
    """

    def __init__(
        self,
        name: str,
        provider: LLMProvider,
        registry: ToolRegistry,
        memory: ConversationMemory | None = None,
        guard: PolicyGuard | None = None,
        max_steps: int = 8,
        system_prompt: str = "",
    ) -> None:
        self.name = name
        self.provider = provider
        self.registry = registry
        self.memory = memory or ConversationMemory()
        self.guard = guard or PolicyGuard()
        self.max_steps = max_steps
        if system_prompt:
            self.memory.set_system(system_prompt)

    def run(self, user_input: str) -> Message:
        self.memory.add(Message(role="user", content=user_input))

        for _ in range(self.max_steps):
            reply = self.provider.complete(
                self.memory.all(),
                tools=self.registry.specs(),
            )
            self.memory.add(reply)

            if not reply.tool_calls:
                return reply

            for call in reply.tool_calls:
                allowed, reason = self.guard.check(call)
                if not allowed:
                    self.memory.add(
                        Message(
                            role="tool",
                            content=f"policy blocked: {reason}",
                            name=call.name,
                            tool_call_id=call.id,
                        )
                    )
                    continue

                tool = self.registry.get(call.name)
                result = tool.run(**call.arguments)
                self.memory.add(
                    Message(
                        role="tool",
                        content=result.content if result.ok else f"error: {result.error}",
                        name=call.name,
                        tool_call_id=call.id,
                    )
                )

        return Message(role="assistant", content="max steps reached.")
