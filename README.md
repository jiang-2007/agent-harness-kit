<div align="center">

# harnesskit

### A lightweight, model-agnostic LLM agent harness — ReAct loop, tool registry, pluggable providers, sub-agent routing, local retrieval and policy guards.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)
[![Tests](https://img.shields.io/badge/tests-24%20passing-success.svg)](#running-tests)

[Architecture](docs/architecture.md) · [Agent YAML spec](docs/agent-yaml-spec.md) · [Examples](examples/basic_agent.yaml) · [Contributing](CONTRIBUTING.md)

</div>

---

## Why harnesskit?

Most agent demos bind one model, one tool list and one prompt together.
`harnesskit` separates those concerns into small, swappable layers so you can
experiment with agent orchestration without rewriting the runtime each time.

- **🔁 ReAct-style loop** — the agent alternates between model replies and
  tool execution, bounded by a step budget.
- **🧰 Tool registry** — tools declare their own schema; the registry hands
  specs to the model and resolves calls by name.
- **🔌 Pluggable providers** — one `LLMProvider` interface; an offline
  `MockProvider` ships built in, plus an OpenAI-compatible backend for gateways,
  vLLM or local models.
- **🧠 Sliding-window memory** — the system prompt is always preserved while
  recent turns stay within a bounded buffer.
- **🛡️ Policy guards** — every tool call passes a budget, allowlist and
  optional dry-run check before execution; rejections are fed back to the model.
- **🤝 Sub-agent routing** — a `Supervisor` registers specialist agents and
  delegates a task to the right one, then returns its reply.
- **🔎 Local retrieval** — a stdlib TF-IDF retrieval tool grounds answers in a
  local document store, the retrieval half of a RAG pipeline.
- **🧾 Structured trace** — every user, assistant, tool and policy event is
  recorded and exportable as JSON for debugging and audit.

> **Project status:** a study-grade orchestration kernel built to understand how
> production agent harnesses are put together. The core runs on the Python
> standard library; richer model backends and longer-term memory are on the
> roadmap.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Supervisor ── delegates ──▶ Agent (ReAct loop)                │
│                             provider → tool_calls? → guard     │
│                             → registry → memory → trace       │
└───────────────┬───────────────────────────────┬───────────────┘
                │                                 │
        ┌───────▼───────┐                 ┌───────▼───────┐
        │ LLMProvider    │                 │ ToolRegistry  │
        │ mock / openai-  │                 │ builtins /     │
        │ compatible      │                 │ retrieval      │
        └───────────────┘                 └───────────────┘
                │
        ┌───────▼───────┐     ┌─────────────────┐
        │ Conversation   │     │ PolicyGuard      │
        │ Memory (window)│     │ budget/allowlist/│
        └───────────────┘     │ dry-run          │
                               └─────────────────┘
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

### Route tasks to sub-agents

```python
from harnesskit import Supervisor

supervisor = Supervisor()
supervisor.register("researcher", researcher_agent)
supervisor.register("coder", coder_agent)

reply = supervisor.delegate("researcher", "summarize the retrieval design")
```

### Add local RAG retrieval

```python
from harnesskit import RetrievalTool

retrieval = RetrievalTool([
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks documents by term weight and relevance.",
])
registry.register(retrieval)
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
├── examples/             # declarative agent example
├── src/harnesskit/
│   ├── agent.py          # ReAct loop
│   ├── supervisor.py     # sub-agent delegation
│   ├── trace.py          # structured event log + JSON export
│   ├── schema.py         # Message / ToolCall data structures
│   ├── memory.py         # sliding-window conversation memory
│   ├── tools/            # registry, builtins, local retrieval
│   ├── providers/        # interface, offline mock, OpenAI-compatible
│   ├── policies/         # budget / allowlist / dry-run guards
│   └── config.py         # agent configuration value object
└── tests/                # unit tests for memory, tools, providers, routing
```

## Roadmap

- [x] OpenAI-compatible provider backend (gateway / local model)
- [x] Sub-agent delegation and supervisor routing
- [x] Retrieval-augmented tool over a local document store
- [x] Structured logging and a session trace exporter
- [x] Dry-run policy mode that records actions without executing them
- [ ] Embedding-based retrieval and persistent vector store
- [ ] Parallel sub-agent execution and result aggregation
- [ ] Session serialization and resume from a saved trace

## Running tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup, checklist and good first issues.

## License

[MIT](LICENSE)
