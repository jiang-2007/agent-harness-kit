"""End-to-end offline demo.

Drives a single ReAct agent, a streamed reply, local retrieval and a parallel
supervisor through deterministic offline providers. No network or API key is
required.

Run with::

    PYTHONPATH=src python3 -m harnesskit.demo
    # or, after installation:  harnesskit-demo
"""
from __future__ import annotations

from .agent import Agent
from .policies import PolicyGuard
from .providers import MockProvider
from .providers.base import LLMProvider
from .schema import Message, StreamChunk, ToolCall
from .supervisor import Supervisor
from .tools import (
    CalculatorTool,
    ClockTool,
    EchoTool,
    RetrievalTool,
    ToolRegistry,
)
from .trace import TraceLogger

_DEMO_DOCS = [
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks passages by term weight and relevance.",
    "Cosine similarity ranks vectors by their angle and overlap.",
]


class _OnceToolProvider(LLMProvider):
    """First turn issues one calculator call; the next turn answers directly.

    Mirrors how a real model stops calling tools after observing the tool result.
    """

    def __init__(self) -> None:
        self._calls = 0

    def complete(self, messages, tools=None) -> Message:
        self._calls += 1
        if self._calls == 1:
            return Message(
                role="assistant",
                tool_calls=[
                    ToolCall(name="calculator", arguments={"expression": "6 * 7"})
                ],
            )
        return Message(role="assistant", content="6 times 7 is 42.")

    def stream(self, messages, tools=None):
        reply = self.complete(messages, tools)
        for call in reply.tool_calls:
            yield StreamChunk(tool_call=call)
        yield StreamChunk(content=reply.content, done=True)


def _single_agent() -> Agent:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(ClockTool())
    registry.register(EchoTool())
    return Agent(
        name="assistant",
        provider=_OnceToolProvider(),
        registry=registry,
        guard=PolicyGuard(max_tool_calls=10),
        system_prompt="You are a concise offline demo assistant.",
        trace=TraceLogger(),
    )


def main() -> None:
    print("=" * 60)
    print("harnesskit — offline end-to-end demo")
    print("=" * 60)

    # 1. Single ReAct turn with a calculator tool call.
    agent = _single_agent()
    reply = agent.run("what is 6 times 7?")
    print("\n[1] ReAct turn")
    print("reply:", reply.content)

    # 2. Streamed reply, chunk by chunk.
    print("\n[2] Streamed reply")
    stream_registry = ToolRegistry()
    stream_agent = Agent(
        name="streamer",
        provider=MockProvider(),
        registry=stream_registry,
    )
    streamed: list[str] = []
    for _turn in stream_agent.run_stream(
        "hello from the streaming loop", on_chunk=lambda c: streamed.append(c.content)
    ):
        pass
    print("streamed:", "".join(streamed))

    # 3. Local TF-IDF retrieval over the demo document store.
    retrieval = RetrievalTool(_DEMO_DOCS)
    hits = retrieval.run(query="how does the loop decide to act", top_k=2)
    print("\n[3] Retrieval hits")
    print(hits.content or hits.error)

    # 4. Parallel supervisor fan-out with per-agent isolation.
    def specialist(name: str) -> Agent:
        registry = ToolRegistry()
        registry.register(EchoTool())
        return Agent(name=name, provider=MockProvider(), registry=registry)

    supervisor = Supervisor(max_workers=2)
    supervisor.register("researcher", specialist("researcher"))
    supervisor.register("coder", specialist("coder"))
    result = supervisor.delegate_many(
        {"researcher": "summarize the retrieval design", "coder": "sketch the registry"},
        parallel=True,
    )
    print("\n[4] Parallel delegation")
    print("replies:", sorted(result.replies))
    print("errors:", result.errors)
    print("summary:", result.summary)

    print("\nDone. Inspect `agent.trace.to_json()` for the full event log.")


if __name__ == "__main__":
    main()
