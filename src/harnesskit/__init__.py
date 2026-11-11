"""harnesskit — a lightweight, model-agnostic LLM agent harness."""
from .agent import Agent
from .config import AgentConfig
from .memory import ConversationMemory
from .policies import PolicyGuard
from .providers import LLMProvider, MockProvider, OpenAICompatibleProvider
from .schema import Message, ToolCall
from .supervisor import Supervisor
from .tools import (
    CalculatorTool,
    ClockTool,
    EchoTool,
    RetrievalTool,
    ToolRegistry,
)
from .trace import TraceLogger

__version__ = "0.2.0"

__all__ = [
    "Agent",
    "AgentConfig",
    "ConversationMemory",
    "PolicyGuard",
    "LLMProvider",
    "MockProvider",
    "OpenAICompatibleProvider",
    "Message",
    "ToolCall",
    "ToolRegistry",
    "CalculatorTool",
    "ClockTool",
    "EchoTool",
    "RetrievalTool",
    "Supervisor",
    "TraceLogger",
]
