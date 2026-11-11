import unittest

from harnesskit.agent import Agent
from harnesskit.providers import MockProvider
from harnesskit.supervisor import Supervisor
from harnesskit.tools import EchoTool, ToolRegistry


def _make_subagent(name: str = "sub") -> Agent:
    registry = ToolRegistry()
    registry.register(EchoTool())
    return Agent(name=name, provider=MockProvider(), registry=registry)


class _BoomProvider:
    """Provider that always fails, to exercise error isolation."""

    def complete(self, messages, tools=None):
        raise RuntimeError("boom")


class TestSupervisor(unittest.TestCase):
    def test_delegate_to_registered_agent(self):
        supervisor = Supervisor()
        supervisor.register("helper", _make_subagent())
        reply = supervisor.delegate("helper", "hello")
        self.assertEqual(reply.role, "assistant")
        self.assertIn("[mock]", reply.content)

    def test_lists_registered_names(self):
        supervisor = Supervisor()
        supervisor.register("a", _make_subagent())
        supervisor.register("b", _make_subagent())
        self.assertEqual(supervisor.names(), ["a", "b"])

    def test_unknown_agent_raises(self):
        supervisor = Supervisor()
        with self.assertRaises(KeyError):
            supervisor.delegate("missing", "task")

    def test_delegate_many_parallel_aggregates_replies(self):
        supervisor = Supervisor()
        supervisor.register("researcher", _make_subagent("researcher"))
        supervisor.register("coder", _make_subagent("coder"))

        result = supervisor.delegate_many(
            {"researcher": "summarize", "coder": "implement"},
            parallel=True,
        )

        self.assertEqual(sorted(result.replies), ["coder", "researcher"])
        self.assertEqual(result.errors, {})
        self.assertIn("researcher", result.summary)
        self.assertIn("coder", result.summary)

    def test_delegate_many_serial_matches_parallel(self):
        supervisor = Supervisor()
        supervisor.register("a", _make_subagent("a"))
        supervisor.register("b", _make_subagent("b"))

        result = supervisor.delegate_many({"a": "one", "b": "two"}, parallel=False)
        self.assertEqual(sorted(result.replies), ["a", "b"])
        self.assertEqual(result.errors, {})

    def test_broadcast_reaches_every_agent(self):
        supervisor = Supervisor()
        supervisor.register("x", _make_subagent("x"))
        supervisor.register("y", _make_subagent("y"))

        result = supervisor.broadcast("same task")
        self.assertEqual(sorted(result.replies), ["x", "y"])

    def test_failure_isolated_in_errors(self):
        supervisor = Supervisor()
        supervisor.register("ok", _make_subagent("ok"))
        boom = Agent(name="boom", provider=_BoomProvider(), registry=ToolRegistry())
        supervisor.register("boom", boom)

        result = supervisor.delegate_many({"ok": "hi", "boom": "fail"})

        self.assertIn("ok", result.replies)
        self.assertIn("boom", result.errors)
        self.assertIn("boom", result.errors["boom"])
        self.assertNotIn("boom", result.replies)


if __name__ == "__main__":
    unittest.main()
