# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

## [0.3.0] - 2026-11-11

### Added
- `Supervisor.delegate_many` and `Supervisor.broadcast`: fan out tasks to
  registered sub-agents on a thread pool (or serially), returning an
  `AggregateResult` with per-agent replies, isolated errors and a combined
  summary.
- Session serialization: `ConversationMemory` snapshot/restore and JSON
  round-trip; `Message` / `ToolCall` `to_dict` / `from_dict`.
- Trace persistence: `TraceLogger.restore` and `TraceLogger.from_json` to
  reload an exported event log for replay.
- Retrieval persistence: `RetrievalTool.documents`, `serialize`, `to_json` and
  `from_json` to save and reload the local document store.
- Parallel supervisor demo under `examples/`.
- Unit tests covering serialization, parallel aggregation, error isolation and
  retrieval persistence (34 tests total).

## [0.2.0] - 2026-11-11

### Added
- `Supervisor` for registering specialist agents and delegating tasks by name.
- `OpenAICompatibleProvider` backed by the stdlib `urllib` transport; the
  transport is injectable for offline testing.
- `RetrievalTool`: in-memory TF-IDF document store returning top-k passages.
- `TraceLogger`: structured user/assistant/tool/policy event log with JSON
  export.
- Dry-run mode on `PolicyGuard` and `Agent`: record intended tool calls without
  executing the real tools.
- Unit tests covering providers, retrieval, routing, trace and dry-run.

## [0.1.0] - 2026-11-11

### Added
- ReAct-style agent loop with bounded step budget.
- Tool registry with auto-generated specs for the model.
- Built-in `calculator`, `clock` and `echo` tools.
- Pluggable `LLMProvider` interface plus an offline `MockProvider` for demos
  and tests.
- Sliding-window conversation memory that preserves the system prompt.
- Policy guard: tool-call budget and optional allowlist.
- Unit tests covering memory, tools and the agent loop.
