import io
import unittest
from contextlib import redirect_stdout

from harnesskit import demo


class TestDemo(unittest.TestCase):
    def test_main_runs_offline_without_raising(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            demo.main()
        output = buffer.getvalue()

        self.assertIn("ReAct", output)
        self.assertIn("Streamed", output)
        self.assertIn("Retrieval", output)
        self.assertIn("Parallel", output)


if __name__ == "__main__":
    unittest.main()
