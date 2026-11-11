import unittest

from harnesskit.tools import CalculatorTool, ClockTool, EchoTool, ToolRegistry


class TestTools(unittest.TestCase):
    def test_calculator_arithmetic(self):
        result = CalculatorTool().run(expression="2 * (3 + 4)")
        self.assertTrue(result.ok)
        self.assertEqual(result.content, "14")

    def test_calculator_rejects_garbage(self):
        result = CalculatorTool().run(expression="__import__('os')")
        self.assertFalse(result.ok)

    def test_echo(self):
        self.assertEqual(EchoTool().run(text="ok").content, "ok")

    def test_registry_lookup(self):
        registry = ToolRegistry()
        registry.register(ClockTool())
        self.assertIn("clock", registry.names())
        self.assertEqual(registry.get("clock").name, "clock")
        with self.assertRaises(KeyError):
            registry.get("missing")


if __name__ == "__main__":
    unittest.main()
