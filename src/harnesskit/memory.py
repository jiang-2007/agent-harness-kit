"""Sliding-window conversation memory."""
from __future__ import annotations

from .schema import Message


class ConversationMemory:
    """Keep the system prompt plus the most recent turns.

    The window is expressed in turns; each turn contributes a user message and
    an assistant/tool reply, so the retained buffer stays bounded while the
    system instruction is always preserved at the front.
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
