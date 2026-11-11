# Architecture

`harnesskit` is a small agent harness: the runtime that sits between a model
backend and a set of callable tools, owns the conversation trace, and applies
safety policies before any tool executes.

## Layers

```
┌──────────────────────────────────────────────────────────┐
│ Agent (ReAct loop)                                         │
│  provider.complete() → tool_calls? → guard → registry → memory
└───────────────┬───────────────────────────┬──────────────┘
                │                             │
        ┌───────▼───────┐             ┌──────▼───────┐
        │ LLMProvider    │             │ ToolRegistry  │
        │ base / mock /  │             │ Tool → result │
        │ openai-compat  │             └──────────────┘
        └───────────────┘
                │
        ┌───────▼───────┐     ┌────────────────┐
        │ Conversation   │     │ PolicyGuard     │
        │ Memory (window)│     │ budget/allowlist│
        └───────────────┘     └────────────────┘
```

### Agent loop

1. Append the user message to memory.
2. Ask the provider for a reply, passing the current tool specs.
3. If the reply has no tool calls, return it as the final answer.
4. For each tool call: run the policy guard; on rejection, record a blocked
   tool result; otherwise resolve the tool from the registry and execute it.
5. Append every tool result to memory and go back to step 2, until the model
   stops calling tools or the step budget is reached.

### Extension points

- **New provider**: subclass `providers.base.LLMProvider` and translate the
  `Message` trace to your upstream's wire format.
- **New tool**: subclass `tools.base.Tool`, declare `name`, `description` and
  `parameters`, then implement `run(**kwargs) -> ToolResult`.
- **New policy**: extend `policies.guard.PolicyGuard` with additional checks
  evaluated before execution.

## Design choices

- **Standard library core**: the offline mock provider and built-in tools run
  with no third-party dependency, so demos, tests and CI never need a network
  or an API key.
- **Bounded state**: memory is a sliding window; tool calls are capped; every
  external action passes through the guard before reaching the registry.
- **Provider-agnostic**: the harness speaks its own `Message` schema; upstream
  model specifics stay behind the provider interface.
