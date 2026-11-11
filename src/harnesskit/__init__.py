"""harnesskit — a lightweight, model-agnostic LLM agent harness."""
from .agent import Agent
from .config import AgentConfig
from .memory import ConversationMemory
from .policies import PolicyGuard
from .providers import LLMProvider, MockProvider, OpenAICompatibleProvider, RetryProvider
from .schema import Message, StreamChunk, ToolCall
from .supervisor import AggregateResult, Supervisor
from .tools import (
    CalculatorTool,
    ClockTool,
    EchoTool,
    Embedder,
    HashEmbedder,
    RetrievalTool,
    ToolRegistry,
    VectorRetrievalTool,
    VectorStore,
)
from .trace import TraceLogger

__version__ = "0.7.0"

__all__ = [
    "Agent",
    "AgentConfig",
    "ConversationMemory",
    "PolicyGuard",
    "LLMProvider",
    "MockProvider",
    "OpenAICompatibleProvider",
    "RetryProvider",
    "Message",
    "StreamChunk",
    "ToolCall",
    "ToolRegistry",
    "CalculatorTool",
    "ClockTool",
    "EchoTool",
    "RetrievalTool",
    "Embedder",
    "HashEmbedder",
    "VectorStore",
    "VectorRetrievalTool",
    "Supervisor",
    "AggregateResult",
    "TraceLogger",
]
