"""harnesskit — a lightweight, model-agnostic LLM agent harness."""
from .agent import Agent
from .config import AgentConfig
from .memory import ConversationMemory
from .policies import PolicyGuard
from .providers import LLMProvider, MockProvider
from .schema import Message, ToolCall
from .tools import CalculatorTool, ClockTool, EchoTool, ToolRegistry

__version__ = "0.1.0"

__all__ = [
    "Agent",
    "AgentConfig",
    "ConversationMemory",
    "PolicyGuard",
    "LLMProvider",
    "MockProvider",
    "Message",
    "ToolCall",
    "ToolRegistry",
    "CalculatorTool",
    "ClockTool",
    "EchoTool",
]
