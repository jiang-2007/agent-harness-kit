# Agent YAML spec

An agent can be declared declaratively. The example below describes the
fields the runtime understands; a YAML loader can map this file onto
`config.AgentConfig`.

```yaml
name: research_assistant
system_prompt: >
  You are a concise research assistant. Prefer calling tools over guessing,
  and cite the tool result you relied on.
provider:
  type: mock            # mock | openai-compatible | local
  model: gpt-4o-mini    # optional, provider-dependent
max_steps: 8
max_tool_calls: 10
tools:
  - calculator
  - clock
  - echo
allowlist:              # optional; omit to allow every registered tool
  - calculator
  - clock
```

## Fields

| Field | Type | Description |
| --- | --- | --- |
| `name` | string | Human-readable agent name. |
| `system_prompt` | string | System instruction injected at the front of memory. |
| `provider.type` | string | Backend kind. `mock` ships built in; other backends are pluggable. |
| `provider.model` | string | Optional model identifier passed to the backend. |
| `max_steps` | int | Maximum provider→tool iterations per run. |
| `max_tool_calls` | int | Hard cap on tool calls within one run. |
| `tools` | list[string] | Registered tool names exposed to the model. |
| `allowlist` | list[string] | Optional subset of tools permitted to execute. |
