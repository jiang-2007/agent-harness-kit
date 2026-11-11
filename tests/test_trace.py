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

    def test_restore_from_export(self):
        logger = TraceLogger()
        logger.record("user", "hi", topic="greeting")
        restored = TraceLogger()
        restored.restore(logger.export())
        self.assertEqual(restored.export()[0]["message"], "hi")
        self.assertEqual(restored.export()[0]["metadata"]["topic"], "greeting")

    def test_from_json_roundtrip(self):
        logger = TraceLogger()
        logger.record("tool", "42", tool="calculator")
        restored = TraceLogger.from_json(logger.to_json())
        self.assertEqual(restored.export()[0]["metadata"]["tool"], "calculator")


if __name__ == "__main__":
    unittest.main()
