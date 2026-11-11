# Architecture

`harnesskit` is a small agent harness: the runtime that sits between a model
backend and a set of callable tools, owns the conversation trace, and applies
safety policies before any tool executes. A supervisor layer routes tasks
between specialist agents, with concurrent fan-out and result aggregation.

## Layers

```
                        ┌──────────────────────────────────────────┐
                        │ Supervisor                              │
                        │  delegate · delegate_many · broadcast    │
                        │  thread-pool fan-out → AggregateResult  │
                        └───────────────┬────────────────────────┘
                                        │ delegates
                ┌───────────────────────┼───────────────────────┐
                ▼                       ▼                       ▼
        ┌───────────────┐       ┌───────────────┐           ┌───────────────┐
        │ Agent  A      │       │ Agent  B      │           │ Agent  C      │
        │ ReAct loop    │       │ ReAct loop    │           │ ReAct loop    │
        └───────┬───────┘       └───────┬───────┘           └───────┬───────┘
                └───────────────────────┼───────────────────────────┘
                                        ▼
        ┌───────────────┐   ┌───────────────┐   ┌───────────────┐
        │ LLMProvider    │   │ ToolRegistry  │   │ Conversation  │
        │ mock / openai-│   │ builtins /    │   │ Memory        │
        │ compatible     │   │ tfidf/vector  │   │ snapshot/JSON │
        └───────────────┘   └───────────────┘   └───────────────┘
                                        │
                                ┌───────▼───────┐
                                │ PolicyGuard    │
                                │ budget / allow  │
                                │ list / dry-run  │
                                └───────────────┘
```

### Agent loop

1. Append the user message to memory and record a `user` trace event.
2. Ask the provider for a reply, passing the current tool specs.
3. If the reply has no tool calls, return it as the final answer.
4. For each tool call: run the policy guard; on rejection, record a blocked
   tool result. Otherwise validate the arguments against the tool's parameter
   schema; invalid arguments are recorded as an error result. In dry-run mode the
   call is simulated; otherwise the tool runs inside an exception boundary, so a
   raised error becomes a tool result fed back to the model instead of crashing
   the loop. The result is appended to memory.
5. Go back to step 2 until the model stops calling tools or the step budget is
   reached.

### Supervisor

The `Supervisor` holds named `Agent` instances. It does not call a model
itself.

- `delegate(name, task)` forwards one task to one specialist and returns its
  reply.
- `delegate_many({name: task}, parallel=True)` runs a distinct task per agent.
  By default agents run on a thread pool; each keeps its own memory, so
  concurrent delegation stays isolated. A failing agent lands in `errors`
  instead of aborting the batch.
- `broadcast(task)` sends the same task to every registered agent.

All three produce or wrap an `AggregateResult` with `replies`, `errors`,
`names` and a combined `summary`.

### Streaming

Providers may expose an optional `stream(messages, tools)` generator that
yields `StreamChunk` objects. Each chunk carries a text `content` delta, an
optional complete `tool_call`, and a `done` flag. The base implementation falls
back to `complete`, so a provider without native streaming still works with the
streaming loop.

`Agent.run_stream` drives the same ReAct loop as `run`: it accumulates chunk
deltas into an assistant message, forwards every chunk to an optional
`on_chunk` callback, executes tool calls through the guard, and yields the
completed message of each turn.

### Persistence

State is plain JSON-serialisable data so a session can be saved and resumed
without a database:

- `ConversationMemory` exposes `snapshot` / `restore` and `to_json` /
  `from_json`; messages use `Message.to_dict` / `Message.from_dict`.
- `TraceLogger` can `restore` an exported event list or load one from JSON.
- `RetrievalTool` serialises its document store to a JSON list and rebuilds the
  TF-IDF index on load.
- `VectorStore` persists its entries and embeddings to JSON; on reload the stored
  vectors are reused without re-embedding.

### Retrieval

Two complementary retrieval primitives ship in the stdlib core:

- `RetrievalTool` ranks passages with a simple TF-IDF dot product — lightweight
  and transparent, no vectors required.
- `VectorStore` ranks passages by cosine similarity over an `Embedder` space.
  The `Embedder` protocol lets a real embedding-model backend replace the offline
  deterministic `HashEmbedder` without touching the store or tool adapter.
  `VectorRetrievalTool` exposes the store to the model through the `Tool`
  interface.

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
- **Isolated failures**: in fan-out, one agent's exception is recorded and does
  not take down the rest of the batch; inside the loop, a tool exception or
  malformed call becomes a feedback result rather than a crash.
- **Observable and resumable**: optional structured trace and JSON snapshots
  let a session be replayed, audited or resumed without a logging backend.
