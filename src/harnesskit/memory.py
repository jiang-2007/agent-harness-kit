"""Sliding-window conversation memory."""
from __future__ import annotations

import json
from typing import Any

from .schema import Message


class ConversationMemory:
    """Keep the system prompt plus the most recent turns.

    The window is expressed in turns; each turn contributes a user message and
    an assistant/tool reply, so the retained buffer stays bounded while the
    system instruction is always preserved at the front.

    The full message buffer can be snapshotted to a plain dict (or JSON) and
    restored later, which lets a session be persisted and resumed.
    """

    def __init__(self, max_turns: int = 20) -> None:
        self.max_turns = max_turns
        self.messages: list[Message] = []

    def set_system(self, content: str) -> None:
        self.messages = [m for m in self.messages if m.role != "system"]
        self.messages.insert(0, Message(role="system", content=content))

    def add(self, message: Message) -> None:
        self.messages.append(message)
        system = [m for m in self.messages if m.role == "system"]
        rest = self.messages[len(system):]
        cap = self.max_turns * 2
        if len(rest) > cap:
            rest = rest[-cap:]
        self.messages = system + rest

    def all(self) -> list[Message]:
        return list(self.messages)

    # ---- persistence -------------------------------------------------

    def snapshot(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of this memory."""
        return {
            "max_turns": self.max_turns,
            "messages": [m.to_dict() for m in self.messages],
        }

    def restore(self, snapshot: dict[str, Any]) -> None:
        """Load messages from a snapshot produced by :meth:`snapshot`."""
        self.max_turns = int(snapshot.get("max_turns", self.max_turns))
        self.messages = [
            Message.from_dict(m) for m in snapshot.get("messages") or []
        ]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.snapshot(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "ConversationMemory":
        snapshot = json.loads(text)
        memory = cls(max_turns=int(snapshot.get("max_turns", 20)))
        memory.restore(snapshot)
        return memory
