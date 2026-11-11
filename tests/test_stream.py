import unittest

from harnesskit.agent import Agent
from harnesskit.policies import PolicyGuard
from harnesskit.providers import LLMProvider, MockProvider
from harnesskit.schema import Message, StreamChunk
from harnesskit.tools import CalculatorTool, EchoTool, ToolRegistry


class TestMockStream(unittest.TestCase):
    def test_text_stream_concatenates_to_complete_reply(self):
        provider = MockProvider()
        source = [Message(role="user", content="yo")]
        chunks = list(provider.stream(source))
        content = "".join(chunk.content for chunk in chunks)
        self.assertEqual(content, provider.complete(source).content)
        self.assertTrue(chunks[-1].done)
        self.assertGreater(len(chunks), 1)

    def test_calc_stream_carries_tool_call(self):
        provider = MockProvider()
        chunks = list(provider.stream([Message(role="user", content="calc: 3*3")]))
        calls = [chunk.tool_call for chunk in chunks if chunk.tool_call]
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].name, "calculator")
        self.assertTrue(chunks[-1].done)


class _PlainProvider(LLMProvider):
    """Only implements ``complete``; exercises the base stream fallback."""

    def complete(self, messages, tools=None):
        return Message(role="assistant", content="fallback reply")


class TestBaseStreamFallback(unittest.TestCase):
    def test_default_stream_yields_single_done_chunk(self):
        chunks = list(_PlainProvider().stream([Message(role="user", content="hi")]))
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].done)
        self.assertEqual(chunks[0].content, "fallback reply")


def build_agent() -> Agent:
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(EchoTool())
    return Agent(
        name="tester",
        provider=MockProvider(),
        registry=registry,
        guard=PolicyGuard(),
    )


class TestAgentRunStream(unittest.TestCase):
    def test_plain_reply_emits_chunks(self):
        agent = build_agent()
        seen: list[StreamChunk] = []
        replies = list(agent.run_stream("hello", on_chunk=seen.append))
        self.assertTrue(seen)
        self.assertEqual(replies[-1].role, "assistant")
        self.assertIn("[mock]", replies[-1].content)

    def test_stream_tool_call_is_executed(self):
        agent = build_agent()
        list(agent.run_stream("calc: 6 * 7"))
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertEqual(tool_messages[0].content, "42")


if __name__ == "__main__":
    unittest.main()
