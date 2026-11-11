import unittest

from harnesskit.memory import ConversationMemory
from harnesskit.schema import Message


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


if __name__ == "__main__":
    unittest.main()
