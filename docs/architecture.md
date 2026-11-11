# Architecture

`harnesskit` is a small agent harness: the runtime that sits between a model
backend and a set of callable tools, owns the conversation trace, and applies
safety policies before any tool executes. A supervisor layer routes tasks
between specialist agents.

## Layers

```
┌──────────────────────────────────────────────────────────┐
│ Supervisor ── delegates ──▶ Agent (ReAct loop)            │
│                             provider → tool_calls? → guard │
│                             → registry → memory → trace   │
└───────────────┬───────────────────────────┬──────────────┘
                │                             │
        ┌───────▼───────┐             ┌──────▼───────┐
        │ LLMProvider    │             │ ToolRegistry  │
        │ mock / openai- │             │ builtins /    │
        │ compatible     │             │ retrieval     │
        └───────────────┘             └──────────────┘
                │
        ┌───────▼───────┐     ┌────────────────┐
        │ Conversation   │     │ PolicyGuard     │
        │ Memory (window)│     │ budget/allowlist│
        └───────────────┘     │ / dry-run       │
                               └────────────────┘
```

### Agent loop

1. Append the user message to memory and record a `user` trace event.
2. Ask the provider for a reply, passing the current tool specs.
3. If the reply has no tool calls, return it as the final answer.
4. For each tool call: run the policy guard; on rejection, record a blocked
   tool result; otherwise execute the tool (or simulate it in dry-run mode) and
   append the result to memory.
5. Go back to step 2 until the model stops calling tools or the step budget is
   reached.

### Supervisor

The `Supervisor` holds named `Agent` instances. It does not call a model itself;
`delegate(name, task)` looks up the specialist and forwards the task to its
`run` method, returning that agent's reply. This keeps routing separate from any
single agent's loop.

### Trace

`TraceLogger` collects `user`, `assistant`, `tool` and `policy` events with
timestamps and metadata, and renders them as JSON. It is optional: an agent
runs normally without one.

### Extension points

- **New provider**: subclass `providers.base.LLMProvider` and translate the
  `Message` trace to your upstream's wire format.
- **New tool**: subclass `tools.base.Tool`, declare `name`, `description` and
  `parameters`, then implement `run(**kwargs) -> ToolResult`.
- **New policy**: extend `policies.guard.PolicyGuard` with additional checks
  evaluated before execution.
- **New specialist agent**: build an `Agent` and register it with a
  `Supervisor` for delegation.

## Design choices

- **Standard library core**: the offline mock provider, built-in tools and
  retrieval run with no third-party dependency, so demos, tests and CI never
  need a network or an API key.
- **Bounded state**: memory is a sliding window; tool calls are capped; every
  external action passes through the guard before reaching the registry.
- **Provider-agnostic**: the harness speaks its own `Message` schema; upstream
  model specifics stay behind the provider interface.
- **Observable by default**: optional structured trace lets a session be
  replayed or audited without a logging backend.
