"""OpenAI-compatible chat completions provider (standard library only).

Talks to any endpoint that implements the Chat Completions schema
(OpenAI, Azure-compatible gateways, vLLM, Ollama's OpenAI shim, ...). The
network transport is injectable so the request/response mapping can be tested
offline without a real HTTP call.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from ..schema import Message, ToolCall
from .base import LLMProvider

Transport = Callable[[dict[str, Any]], dict[str, Any]]


def _default_transport(
    payload: dict[str, Any],
    *,
    base_url: str,
    api_key: str,
    timeout: float,
) -> dict[str, Any]:
    request = urllib.request.Request(
        url=f"{base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _to_wire(message: Message) -> dict[str, Any]:
    wire: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.name:
        wire["name"] = message.name
    if message.tool_call_id:
        wire["tool_call_id"] = message.tool_call_id
    if message.tool_calls:
        wire["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, ensure_ascii=False),
                },
            }
            for call in message.tool_calls
        ]
    return wire


def _parse_tool_calls(raw_calls: list[dict[str, Any]] | None) -> list[ToolCall]:
    calls: list[ToolCall] = []
    for raw in raw_calls or []:
        function = raw.get("function", {})
        arguments_raw = function.get("arguments", "{}")
        try:
            arguments = json.loads(arguments_raw) if isinstance(arguments_raw, str) else {}
        except json.JSONDecodeError:
            arguments = {}
        calls.append(
            ToolCall(
                name=function.get("name", ""),
                arguments=arguments,
                id=raw.get("id"),
            )
        )
    return calls


class OpenAICompatibleProvider(LLMProvider):
    """Provider backed by any OpenAI-compatible Chat Completions endpoint."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str = "gpt-4o-mini",
        transport: Transport | None = None,
        timeout: float = 30.0,
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self._transport = transport or self._default_transport

    def _default_transport(self, payload: dict[str, Any]) -> dict[str, Any]:
        return _default_transport(
            payload,
            base_url=self.base_url,
            api_key=self.api_key,
            timeout=self.timeout,
        )

    def complete(
        self,
        messages: list[Message],
        tools: list[dict] | None = None,
    ) -> Message:
        if not self.api_key:
            raise RuntimeError(
                "OpenAICompatibleProvider requires an api_key; use MockProvider "
                "for offline demos and tests."
            )

        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [_to_wire(message) for message in messages],
        }
        if tools:
            payload["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": spec["name"],
                        "description": spec["description"],
                        "parameters": spec["parameters"],
                    },
                }
                for spec in tools
            ]

        try:
            data = self._transport(payload)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"provider request failed: {exc}") from exc

        choice = (data.get("choices") or [{}])[0]
        raw_message = choice.get("message", {})
        return Message(
            role="assistant",
            content=raw_message.get("content") or "",
            tool_calls=_parse_tool_calls(raw_message.get("tool_calls")),
        )
