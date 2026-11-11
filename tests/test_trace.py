import json
import unittest

from harnesskit.trace import TraceLogger


class TestTraceLogger(unittest.TestCase):
    def test_record_and_export(self):
        logger = TraceLogger()
        logger.record("user", "hi", topic="greeting")
        logger.record("tool", "42", tool="calculator")

        export = logger.export()
        self.assertEqual(export[0]["message"], "hi")
        self.assertEqual(export[0]["metadata"]["topic"], "greeting")
        self.assertEqual(export[1]["metadata"]["tool"], "calculator")

    def test_to_json_is_valid(self):
        logger = TraceLogger()
        logger.record("assistant", "done")
        parsed = json.loads(logger.to_json())
        self.assertEqual(parsed[0]["message"], "done")


if __name__ == "__main__":
    unittest.main()
