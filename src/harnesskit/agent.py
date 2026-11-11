"""The agent runtime: a ReAct-style loop over provider, tools and memory."""
from __future__ import annotations

from collections.abc import Iterator
from typing import Callable

from .memory import ConversationMemory
from .policies.guard import PolicyGuard
from .providers.base import LLMProvider
from .schema import Message, StreamChunk
from .tools.base import ToolRegistry
from .trace import TraceLogger

ChunkCallback = Callable[[StreamChunk], None]


class Agent:
    """One conversational agent bound to a provider, a tool registry and a guard.

    The loop alternates: ask the provider for a reply -> execute any tool calls
    through the registry (after the policy guard) -> feed results back into
    memory -> repeat until the model answers without tool calls or the step
    budget is reached.

    Args:
        trace: Optional logger that records every user, assistant, tool and
            policy event for debugging or audit.
        dry_run: Record tool calls without executing the real tools. Inherits
            the guard's ``dry_run`` when set there.
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
        trace: TraceLogger | None = None,
        dry_run: bool = False,
    ) -> None:
        self.name = name
        self.provider = provider
        self.registry = registry
        self.memory = memory or ConversationMemory()
        self.guard = guard or PolicyGuard()
        self.max_steps = max_steps
        self.trace = trace
        self.dry_run = dry_run or self.guard.dry_run
        if system_prompt:
            self.memory.set_system(system_prompt)

    def _log(self, event_type: str, message: str, **metadata: object) -> None:
        if self.trace is not None:
            self.trace.record(event_type, message, **metadata)

    def _execute_tool_calls(self, reply: Message) -> None:
        """Run every tool call in an assistant reply through the guard."""
        for call in reply.tool_calls:
            allowed, reason = self.guard.check(call)
            if not allowed:
                self._log("policy", reason, tool=call.name)
                self.memory.add(
                    Message(
                        role="tool",
                        content=f"policy blocked: {reason}",
                        name=call.name,
                        tool_call_id=call.id,
                    )
                )
                continue

            if self.dry_run:
                simulated = f"[dry-run] would call {call.name}({call.arguments})"
                self._log("tool", simulated, tool=call.name, dry_run=True)
                self.memory.add(
                    Message(
                        role="tool",
                        content=simulated,
                        name=call.name,
                        tool_call_id=call.id,
                    )
                )
                continue

            tool = self.registry.get(call.name)

            validation_errors = tool.validate(call.arguments)
            if validation_errors:
                detail = "; ".join(validation_errors)
                self._log("tool", detail, tool=call.name, ok=False, validation=True)
                self.memory.add(
                    Message(
                        role="tool",
                        content=f"invalid arguments: {detail}",
                        name=call.name,
                        tool_call_id=call.id,
                    )
                )
                continue

            try:
                result = tool.run(**call.arguments)
            except Exception as exc:  # noqa: BLE001 - isolate tool failure from the loop
                self._log("tool", str(exc), tool=call.name, ok=False)
                self.memory.add(
                    Message(
                        role="tool",
                        content=f"error: {exc}",
                        name=call.name,
                        tool_call_id=call.id,
                    )
                )
                continue

            self._log(
                "tool",
                result.content or (result.error or ""),
                tool=call.name,
                ok=result.ok,
            )
            self.memory.add(
                Message(
                    role="tool",
                    content=result.content if result.ok else f"error: {result.error}",
                    name=call.name,
                    tool_call_id=call.id,
                )
            )

    def run(self, user_input: str) -> Message:
        self.memory.add(Message(role="user", content=user_input))
        self._log("user", user_input)

        for _ in range(self.max_steps):
            reply = self.provider.complete(
                self.memory.all(),
                tools=self.registry.specs(),
            )
            self.memory.add(reply)
            self._log(
                "assistant",
                reply.content,
                tool_calls=[call.name for call in reply.tool_calls],
            )

            if not reply.tool_calls:
                return reply

            self._execute_tool_calls(reply)

        return Message(role="assistant", content="max steps reached.")

    def run_stream(
        self,
        user_input: str,
        on_chunk: ChunkCallback | None = None,
    ) -> Iterator[Message]:
        """Stream the agent loop, yielding one assistant message per turn.

        Every provider chunk is handed to ``on_chunk`` as it arrives; completed
        turns are yielded back to the caller. Tool calls are executed through
        the guard exactly as in :meth:`run`.
        """
        self.memory.add(Message(role="user", content=user_input))
        self._log("user", user_input)

        for _ in range(self.max_steps):
            content_parts: list[str] = []
            tool_calls: list = []

            for chunk in self.provider.stream(
                self.memory.all(),
                tools=self.registry.specs(),
            ):
                if on_chunk is not None:
                    on_chunk(chunk)
                if chunk.content:
                    content_parts.append(chunk.content)
                if chunk.tool_call:
                    tool_calls.append(chunk.tool_call)

            reply = Message(
                role="assistant",
                content="".join(content_parts),
                tool_calls=tool_calls,
            )
            self.memory.add(reply)
            self._log(
                "assistant",
                reply.content,
                tool_calls=[call.name for call in reply.tool_calls],
            )

            if not reply.tool_calls:
                yield reply
                return

            self._execute_tool_calls(reply)
            yield reply

        yield Message(role="assistant", content="max steps reached.")
