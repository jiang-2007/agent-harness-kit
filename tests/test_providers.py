import unittest

from harnesskit.providers import MockProvider, OpenAICompatibleProvider
from harnesskit.schema import Message


class TestOpenAICompatibleProvider(unittest.TestCase):
    def test_plain_response_mapping(self):
        def fake_transport(payload):
            self.assertEqual(payload["model"], "gpt-4o-mini")
            self.assertEqual(payload["messages"][0]["role"], "user")
            return {"choices": [{"message": {"content": "hello back", "tool_calls": []}}]}

        provider = OpenAICompatibleProvider(
            base_url="http://localhost/v1",
            api_key="test-key",
            transport=fake_transport,
        )
        reply = provider.complete([Message(role="user", content="hi")])
        self.assertEqual(reply.content, "hello back")
        self.assertEqual(reply.tool_calls, [])

    def test_tool_call_parsing(self):
        def fake_transport(payload):
            return {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "tool_calls": [
                                {
                                    "id": "call-1",
                                    "function": {
                                        "name": "calculator",
                                        "arguments": '{"expression": "1 + 1"}',
                                    },
                                }
                            ],
                        }
                    }
                ]
            }

        provider = OpenAICompatibleProvider(
            base_url="http://localhost/v1",
            api_key="test-key",
            transport=fake_transport,
        )
        reply = provider.complete([Message(role="user", content="calc")])
        self.assertEqual(len(reply.tool_calls), 1)
        call = reply.tool_calls[0]
        self.assertEqual(call.name, "calculator")
        self.assertEqual(call.arguments, {"expression": "1 + 1"})

    def test_missing_api_key_raises(self):
        provider = OpenAICompatibleProvider(
            base_url="http://localhost/v1", api_key=""
        )
        with self.assertRaises(RuntimeError):
            provider.complete([Message(role="user", content="hi")])


class TestMockProvider(unittest.TestCase):
    def test_echo_reply(self):
        reply = MockProvider().complete([Message(role="user", content="yo")])
        self.assertIn("[mock]", reply.content)

    def test_calc_hint_emits_tool_call(self):
        reply = MockProvider().complete([Message(role="user", content="calc: 3*3")])
        self.assertEqual(reply.tool_calls[0].name, "calculator")


if __name__ == "__main__":
    unittest.main()
