"""Structured session trace: event log and JSON export."""
from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

EventType = Literal["user", "assistant", "tool", "policy", "system"]


@dataclass
class TraceEvent:
    """One recorded step in a session."""

    type: EventType
    message: str
    timestamp: float = field(default_factory=time.time)
    metadata: dict[str, Any] = field(default_factory=dict)


class TraceLogger:
    """Collects events in memory and renders them as portable JSON.

    The trace is intentionally dependency-free so it can be shipped alongside a
    session for debugging, evaluation or audit, without a logging backend.
    """

    def __init__(self) -> None:
        self.events: list[TraceEvent] = []

    def record(self, event_type: EventType, message: str, **metadata: Any) -> None:
        self.events.append(
            TraceEvent(type=event_type, message=message, metadata=metadata)
        )

    def export(self) -> list[dict[str, Any]]:
        return [asdict(event) for event in self.events]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.export(), ensure_ascii=False, indent=indent)
