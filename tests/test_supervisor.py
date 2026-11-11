import unittest

from harnesskit.agent import Agent
from harnesskit.providers import MockProvider
from harnesskit.supervisor import Supervisor
from harnesskit.tools import EchoTool, ToolRegistry


def _make_subagent() -> Agent:
    registry = ToolRegistry()
    registry.register(EchoTool())
    return Agent(name="sub", provider=MockProvider(), registry=registry)


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


if __name__ == "__main__":
    unittest.main()
