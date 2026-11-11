# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/), and the project adheres to
[Semantic Versioning](https://semver.org/).

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
