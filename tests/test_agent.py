import unittest

from harnesskit.agent import Agent
from harnesskit.policies import PolicyGuard
from harnesskit.providers import MockProvider
from harnesskit.tools import CalculatorTool, EchoTool, ToolRegistry


def build_agent(allowlist=None, max_calls=10, dry_run=False):
    registry = ToolRegistry()
    registry.register(CalculatorTool())
    registry.register(EchoTool())
    guard = PolicyGuard(max_tool_calls=max_calls, allowlist=allowlist, dry_run=dry_run)
    return Agent(
        name="tester",
        provider=MockProvider(),
        registry=registry,
        guard=guard,
        system_prompt="be brief",
    )


class TestAgentLoop(unittest.TestCase):
    def test_plain_reply(self):
        agent = build_agent()
        reply = agent.run("hello")
        self.assertEqual(reply.role, "assistant")
        self.assertIn("[mock]", reply.content)

    def test_tool_call_then_answer(self):
        agent = build_agent()
        reply = agent.run("calc: 6 * 7")
        # MockProvider emits one calculator call, then a canned reply on the
        # next pass; the tool result lands in memory.
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertEqual(tool_messages[0].content, "42")
        self.assertEqual(reply.role, "assistant")

    def test_allowlist_blocks_tool(self):
        agent = build_agent(allowlist=["echo"])
        agent.run("calc: 1 + 1")
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertIn("policy blocked", tool_messages[0].content)

    def test_dry_run_records_without_executing(self):
        agent = build_agent(dry_run=True)
        agent.run("calc: 6 * 7")
        tool_messages = [m for m in agent.memory.all() if m.role == "tool"]
        self.assertTrue(tool_messages)
        self.assertIn("[dry-run]", tool_messages[0].content)
        self.assertNotEqual(tool_messages[0].content, "42")


if __name__ == "__main__":
    unittest.main()
