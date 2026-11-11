<div align="center">

# harnesskit

### A model-agnostic LLM agent harness — ReAct loop, tool registry, pluggable providers, streaming replies, parallel sub-agent routing, local vector and TF-IDF retrieval, structured trace and policy guards.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)
[![Tests](https://img.shields.io/badge/tests-58%20passing-success.svg)](#running-tests)
![Stdlib core](https://img.shields.io/badge/core-stdlib%20only-2c3e50.svg)
![Multi-agent](https://img.shields.io/badge/multi-agent-orchestration-8e44ad.svg)

[Architecture](docs/architecture.md) · [Agent YAML spec](docs/agent-yaml-spec.md) · [Examples](examples/) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why harnesskit?

Most agent demos bind one model, one tool list and one prompt together.
`harnesskit` separates those concerns into small, swappable layers so you can
experiment with agent orchestration without rewriting the runtime each time. The
core runs on the Python standard library — no network, no API key, no third-party
dependency to run the demos and tests.

| Layer | What it does |
| --- | --- |
| 🔁 **ReAct loop** | The agent alternates between model replies and tool execution, bounded by a step budget. |
| 🧰 **Tool registry** | Tools declare their own schema; the registry hands specs to the model, resolves calls by name, and validates arguments against the schema before execution. |
| 🔌 **Pluggable providers** | One `LLMProvider` interface; an offline `MockProvider`, an OpenAI-compatible backend for gateways/vLLM/local models, and a `RetryProvider` wrapper for transient failures. |
| 🌊 **Streaming replies** | An optional `stream` interface yields `StreamChunk` deltas; `Agent.run_stream` forwards chunks to a callback while the ReAct loop and guards keep running. |
| 🧠 **Bounded memory** | Sliding-window buffer that always preserves the system prompt, with snapshot / restore for resumable sessions. |
| 🤝 **Supervisor routing** | Register specialist agents; delegate a single task, fan out a task map, or broadcast to every agent — concurrently or serially. |
| 🔎 **TF-IDF retrieval** | A stdlib TF-IDF retrieval tool grounds answers in a local document store; the store serialises to JSON for persistence. |
| 🧬 **Vector store** | A cosine-similarity `VectorStore` with a pluggable `Embedder`; an offline deterministic `HashEmbedder` ships built in, and the store persists to JSON. |
| 🧾 **Structured trace** | Every user, assistant, tool and policy event is recorded, exportable as JSON and restorable for replay. |
| 🛡️ **Policy guards** | Every tool call passes a budget, allowlist and optional dry-run check before execution; rejections and tool exceptions feed back to the model instead of crashing the loop. |

> **Project status:** a study-grade orchestration kernel built to understand how
> production agent harnesses are put together. Real SSE deltas and richer model
> backends are on the roadmap.

## Architecture

```
                        ┌──────────────────────────────────────────┐
                        │ Supervisor                                │
                        │  delegate · delegate_many · broadcast    │
                        │  thread-pool fan-out → AggregateResult    │
                        └───────────────┬──────────────────────────┘
                                        │ delegates
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                           ▼
        ┌───────────────┐       ┌───────────────┐           ┌───────────────┐
        │ Agent  A      │       │ Agent  B      │           │ Agent  C      │
        │ ReAct loop    │       │ ReAct loop    │           │ ReAct loop    │
        └───────┬───────┘       └───────┬───────┘           └───────┬───────┘
                └───────────────────────┼───────────────────────────┘
                                        ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │ LLMProvider    │   │ ToolRegistry  │   │ Conversation  │
        │ mock / openai- │   │ builtins /    │   │ Memory        │
        │ compatible     │   │ retrieval     │   │ snapshot/JSON │
        └───────────────┘   └───────────────┘   └───────────────┘
                                        │
                                ┌───────▼───────┐
                                │ PolicyGuard    │
                                │ budget / allow │
                                │ list / dry-run │
                                └───────────────┘
```

See [docs/architecture.md](docs/architecture.md) for the layer breakdown and
extension points.

## Quick start

### Install

```bash
git clone https://github.com/jiang-2007/agent-harness-kit.git
cd agent-harness-kit
pip install -e .
```

### Run a minimal agent (offline, no API key)

```python
from harnesskit import (
    Agent,
    CalculatorTool,
    ClockTool,
    ConversationMemory,
    EchoTool,
    MockProvider,
    PolicyGuard,
    ToolRegistry,
    TraceLogger,
)

registry = ToolRegistry()
registry.register(CalculatorTool())
registry.register(ClockTool())
registry.register(EchoTool())

trace = TraceLogger()
agent = Agent(
    name="assistant",
    provider=MockProvider(),
    registry=registry,
    memory=ConversationMemory(max_turns=20),
    guard=PolicyGuard(max_tool_calls=10),
    system_prompt="You are a concise assistant.",
    trace=trace,
)

reply = agent.run("calc: 6 * 7")
print(reply.content)
print(trace.to_json())
```

The `MockProvider` interprets a `calc: <expression>` hint as a calculator call;
swap in `OpenAICompatibleProvider` to talk to a real model endpoint.

### Wrap a provider with retry

```python
from harnesskit import MockProvider, RetryProvider

provider = RetryProvider(MockProvider(), max_retries=3, backoff=0.5)
```

### Stream a reply incrementally

```python
def on_chunk(chunk):
    if chunk.content:
        print(chunk.content, end="", flush=True)

for turn in agent.run_stream("explain the ReAct loop", on_chunk=on_chunk):
    pass  # `turn` is the completed assistant message of each model turn
```

`run_stream` yields one `Message` per turn; tool calls still pass the policy
guard. A provider without native streaming falls back to `complete` and sends a
single chunk.

### Parallel sub-agent delegation

```python
from harnesskit import Supervisor

supervisor = Supervisor(max_workers=4)
supervisor.register("researcher", researcher_agent)
supervisor.register("coder", coder_agent)

# One task per agent, run concurrently; failures are isolated into `errors`.
result = supervisor.delegate_many(
    {"researcher": "summarize the retrieval design",
     "coder": "sketch the registry interface"},
    parallel=True,
)

print(result.summary)   # combined digest of every successful reply
print(result.errors)    # agent name -> exception message, if any
```

`broadcast(task)` sends the same task to every registered agent.

### Add local RAG retrieval

```python
from harnesskit import RetrievalTool

retrieval = RetrievalTool([
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks documents by term weight and relevance.",
])
registry.register(retrieval)

# Persist and restore the document store
text = retrieval.to_json()
restored = RetrievalTool.from_json(text)
```

### Vector retrieval over a local store

```python
from harnesskit import VectorRetrievalTool, VectorStore

# Plug in any Embedder; the offline HashEmbedder needs no network.
vector = VectorRetrievalTool([
    "The ReAct loop alternates between reasoning and acting.",
    "Cosine similarity ranks vectors by angle and overlap.",
])
registry.register(vector)

# Persist and reload the vector store
store_json = vector.store.to_json()
reloaded = VectorStore.from_json(store_json)
```

### Persist and resume a session

```python
# Snapshot memory and trace to JSON, then reload in a later run.
memory_json = agent.memory.to_json()
trace_json = trace.to_json()

memory = ConversationMemory.from_json(memory_json)
restored_trace = TraceLogger.from_json(trace_json)
```

### Declarative config

Agents can be described in YAML; see
[`examples/basic_agent.yaml`](examples/basic_agent.yaml) and the
[agent YAML spec](docs/agent-yaml-spec.md).

## Extending the harness

| Extension | How |
| --- | --- |
| New model backend | Subclass `providers.base.LLMProvider`, translate the `Message` trace to your upstream wire format. |
| New tool | Subclass `tools.base.Tool`, declare `name` / `description` / `parameters`, implement `run(**kwargs) -> ToolResult`. |
| New policy | Extend `policies.guard.PolicyGuard` with checks evaluated before execution. |
| New specialist agent | Build an `Agent` and register it with a `Supervisor` for delegation. |

## Project layout

```
agent-harness-kit/
├── docs/                 # architecture, agent YAML spec
├── examples/             # declarative agent, parallel supervisor, vector retrieval demos
├── src/harnesskit/
│   ├── agent.py          # ReAct loop
│   ├── supervisor.py     # sub-agent delegation, fan-out, aggregation
│   ├── trace.py          # structured event log + JSON export/restore
│   ├── schema.py         # Message / ToolCall data structures + serialization
│   ├── memory.py         # sliding-window memory + snapshot/restore
│   ├── tools/            # registry, builtins, TF-IDF + vector retrieval
│   ├── providers/        # interface, mock, OpenAI-compatible, retry
│   ├── policies/         # budget / allowlist / dry-run guards
│   └── config.py         # agent configuration value object
└── tests/                # unit tests across memory, tools, providers, routing
```

## Roadmap

- [x] OpenAI-compatible provider backend (gateway / local model)
- [x] Sub-agent delegation and supervisor routing
- [x] Retrieval-augmented tool over a local document store
- [x] Structured logging and a session trace exporter
- [x] Dry-run policy mode that records actions without executing them
- [x] Parallel sub-agent execution and result aggregation
- [x] Session serialization and resume from a saved trace
- [x] Embedding-style retrieval and persistent vector store
- [x] Streaming provider responses via an optional chunked provider interface
- [x] Tool argument schema validation and tool-exception isolation
- [x] Retry wrapper for transient provider failures
- [ ] Real SSE deltas and incremental tool-call arguments in the OpenAI-compatible provider
- [ ] Production embedding-model backend behind the Embedder interface

## Running tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup, checklist and good first issues.

## License

[MIT](LICENSE)
