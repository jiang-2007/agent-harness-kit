import unittest

from harnesskit.memory import ConversationMemory
from harnesskit.schema import Message, ToolCall


class TestMemory(unittest.TestCase):
    def test_system_prompt_is_preserved(self):
        memory = ConversationMemory(max_turns=1)
        memory.set_system("be brief")
        memory.add(Message(role="user", content="hi"))
        memory.add(Message(role="assistant", content="hello"))
        memory.add(Message(role="user", content="again"))

        roles = [m.role for m in memory.all()]
        self.assertEqual(roles[0], "system")
        self.assertEqual(memory.all()[0].content, "be brief")

    def test_window_keeps_recent_turns(self):
        memory = ConversationMemory(max_turns=1)
        memory.add(Message(role="user", content="1"))
        memory.add(Message(role="assistant", content="a"))
        memory.add(Message(role="user", content="2"))
        memory.add(Message(role="assistant", content="b"))

        contents = [m.content for m in memory.all()]
        self.assertIn("2", contents)
        self.assertNotIn("1", contents)

    def test_snapshot_and_restore_roundtrip(self):
        memory = ConversationMemory(max_turns=4)
        memory.set_system("be brief")
        memory.add(Message(role="user", content="hi"))
        memory.add(
            Message(
                role="assistant",
                content="thinking",
                tool_calls=[ToolCall(name="calculator", arguments={"expression": "1+1"})],
            )
        )

        restored = ConversationMemory()
        restored.restore(memory.snapshot())
        self.assertEqual(restored.max_turns, 4)
        self.assertEqual([m.role for m in restored.all()], [m.role for m in memory.all()])
        self.assertEqual(
            restored.all()[2].tool_calls[0].arguments, {"expression": "1+1"}
        )

    def test_json_roundtrip(self):
        memory = ConversationMemory(max_turns=2)
        memory.add(Message(role="user", content="hello"))
        restored = ConversationMemory.from_json(memory.to_json())
        self.assertEqual(restored.all()[0].content, "hello")


if __name__ == "__main__":
    unittest.main()
