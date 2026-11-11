<div align="center">

# harnesskit

### A lightweight, model-agnostic LLM agent harness — ReAct loop, tool registry, pluggable providers, session memory and policy guards.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status: experimental](https://img.shields.io/badge/status-experimental-orange.svg)
[![Tests](https://img.shields.io/badge/tests-9%20passing-success.svg)](#running-tests)

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
  `MockProvider` ships built in so demos and tests never need a network or an
  API key.
- **🧠 Sliding-window memory** — the system prompt is always preserved while
  recent turns stay within a bounded buffer.
- **🛡️ Policy guards** — every tool call passes a budget and optional
  allowlist check before execution; rejections are fed back to the model as
  observations.

> **Project status:** a study-grade orchestration kernel built to understand how
> production agent harnesses are put together. The core runs on the Python
> standard library; real model backends and multi-agent delegation are on the
> roadmap.

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│ Agent (ReAct loop)                                             │
│  provider.complete() → tool_calls? → guard → registry → memory │
└───────────────┬───────────────────────────────┬───────────────┘
                │                                 │
        ┌───────▼───────┐                 ┌───────▼───────┐
        │ LLMProvider    │                 │ ToolRegistry  │
        │ base / mock /  │                 │ Tool → result │
        │ openai-compat  │                 └───────────────┘
        └───────────────┘
                │
        ┌───────▼───────┐     ┌─────────────────┐
        │ Conversation   │     │ PolicyGuard      │
        │ Memory (window)│    │ budget / allowlist│
        └───────────────┘     └─────────────────┘
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
)

registry = ToolRegistry()
registry.register(CalculatorTool())
registry.register(ClockTool())
registry.register(EchoTool())

agent = Agent(
    name="assistant",
    provider=MockProvider(),
    registry=registry,
    memory=ConversationMemory(max_turns=20),
    guard=PolicyGuard(max_tool_calls=10),
    system_prompt="You are a concise assistant.",
)

reply = agent.run("calc: 6 * 7")
print(reply.content)
```

The `MockProvider` interprets a `calc: <expression>` hint as a calculator call;
swap in a real provider to talk to an actual model.

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

## Project layout

```
agent-harness-kit/
├── docs/                 # architecture, agent YAML spec
├── examples/             # declarative agent example
├── src/harnesskit/
│   ├── agent.py          # ReAct loop
│   ├── schema.py         # Message / ToolCall data structures
│   ├── memory.py         # sliding-window conversation memory
│   ├── tools/            # base registry + built-in tools
│   ├── providers/         # provider interface + offline mock
│   ├── policies/         # budget / allowlist guards
│   └── config.py         # agent configuration value object
└── tests/                # unit tests for memory, tools, agent loop
```

## Roadmap

- [ ] OpenAI-compatible provider backend (gateway / local model)
- [ ] Sub-agent delegation and supervisor routing
- [ ] Retrieval-augmented tool over a local document store
- [ ] Structured logging and a session trace exporter
- [ ] Dry-run policy mode that records actions without executing them

## Running tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Contributing

Contributions are welcome — see [CONTRIBUTING.md](CONTRIBUTING.md) for the
development setup, checklist and good first issues.

## License

[MIT](LICENSE)
