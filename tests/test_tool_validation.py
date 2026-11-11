import unittest

from harnesskit.agent import Agent
from harnesskit.policies import PolicyGuard
from harnesskit.providers.base import LLMProvider
from harnesskit.schema import Message, ToolCall
from harnesskit.tools import CalculatorTool, Tool, ToolRegistry


class FixedProvider(LLMProvider):
    """Returns a prebuilt assistant reply regardless of the trace."""

    def __init__(self, reply: Message) -> None:
        self._reply = reply

    def complete(self, messages, tools=None) -> Message:
        return self._reply


class BoomTool(Tool):
    name = "boom"
    description = "Always raises."
    parameters = {"message": {"type": "string", "description": "ignored."}}

    def run(self, message: str = "", **_):
        raise RuntimeError("boom")


class TestToolValidate(unittest.TestCase):
    def test_valid_string_argument_passes(self):
        tool = CalculatorTool()
        self.assertEqual(tool.validate({"expression": "1 + 1"}), [])

    def test_wrong_type_reports_error(self):
        tool = CalculatorTool()
        errors = tool.validate({"expression": 123})
        self.assertTrue(errors)
        self.assertIn("expression", errors[0])

    def test_missing_argument_is_left_to_default(self):
        tool = CalculatorTool()
        self.assertEqual(tool.validate({}), [])

    def test_bool_is_not_an_integer(self):
        from harnesskit.tools import RetrievalTool

        tool = RetrievalTool(["a passage"])
        errors = tool.validate({"top_k": True})
        self.assertTrue(errors)


def build_agent(provider: LLMProvider, tool: Tool) -> Agent:
    registry = ToolRegistry()
    registry.register(tool)
    return Agent(
        name="tester",
        provider=provider,
        registry=registry,
        guard=PolicyGuard(),
    )


class TestAgentValidationAndIsolation(unittest.TestCase):
    def test_invalid_argument_type_is_feedback_not_crash(self):
        reply = Message(
            role="assistant",
            tool_calls=[ToolCall(name="calculator", arguments={"expression": 123})],
        )
        agent = build_agent(FixedProvider(reply), CalculatorTool())
        agent.run("go")
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertIn("invalid arguments", tool_messages[0].content)

    def test_tool_exception_is_isolated(self):
        reply = Message(
            role="assistant",
            tool_calls=[ToolCall(name="boom", arguments={"message": "x"})],
        )
        agent = build_agent(FixedProvider(reply), BoomTool())
        agent.run("go")  # must not raise
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertIn("error: boom", tool_messages[0].content)


if __name__ == "__main__":
    unittest.main()
