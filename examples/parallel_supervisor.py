"""Demo: parallel supervisor delegation with an offline mock provider.

Run from the repository root:

    PYTHONPATH=src python3 examples/parallel_supervisor.py

No network or API key is required; the ``MockProvider`` produces deterministic
replies so the fan-out, aggregation and error-isolation paths can be exercised
locally.
"""
from harnesskit import (
    Agent,
    EchoTool,
    MockProvider,
    RetrievalTool,
    Supervisor,
    ToolRegistry,
    TraceLogger,
)

RESEARCHER_DOCS = [
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks passages by term weight and relevance.",
]


def build_agent(name: str, documents: list[str] | None = None) -> Agent:
    registry = ToolRegistry()
    registry.register(EchoTool())
    if documents:
        registry.register(RetrievalTool(documents))
    return Agent(
        name=name,
        provider=MockProvider(),
        registry=registry,
        trace=TraceLogger(),
    )


def main() -> None:
    supervisor = Supervisor(max_workers=4)
    supervisor.register("researcher", build_agent("researcher", RESEARCHER_DOCS))
    supervisor.register("coder", build_agent("coder"))

    # Fan out a distinct task per agent, run concurrently.
    result = supervisor.delegate_many(
        {
            "researcher": "summarize the retrieval design",
            "coder": "sketch the tool registry interface",
        },
        parallel=True,
    )

    print("Replies:", sorted(result.replies))
    print("Errors:", result.errors)
    print("\n--- Aggregate summary ---")
    print(result.summary)

    # Broadcast the same task to every registered agent.
    broadcast = supervisor.broadcast("same task to everyone")
    print("\nBroadcast agents:", broadcast.names)


if __name__ == "__main__":
    main()
