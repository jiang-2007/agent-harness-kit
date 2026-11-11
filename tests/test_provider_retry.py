import unittest

from harnesskit.providers.base import LLMProvider
from harnesskit.providers.retry import RetryProvider
from harnesskit.schema import Message, StreamChunk


class FlakyProvider(LLMProvider):
    """Fails the first ``fail_times`` complete calls, then succeeds."""

    def __init__(self, fail_times: int = 0) -> None:
        self.fail_times = fail_times
        self.calls = 0

    def complete(self, messages, tools=None) -> Message:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise RuntimeError("transient upstream failure")
        return Message(role="assistant", content="ok")

    def stream(self, messages, tools=None):
        yield StreamChunk(content="ok", done=True)


class TestRetryProvider(unittest.TestCase):
    def test_recovers_after_transient_failures(self):
        inner = FlakyProvider(fail_times=2)
        sleeps: list[float] = []
        wrapper = RetryProvider(inner, max_retries=2, backoff=0.1, sleeper=sleeps.append)

        reply = wrapper.complete([])

        self.assertEqual(reply.content, "ok")
        self.assertEqual(inner.calls, 3)
        self.assertEqual(wrapper.attempts, 3)
        self.assertEqual(len(sleeps), 2)

    def test_raises_after_exhausting_retries(self):
        inner = FlakyProvider(fail_times=5)
        wrapper = RetryProvider(inner, max_retries=1, sleeper=lambda _: None)

        with self.assertRaises(RuntimeError):
            wrapper.complete([])
        self.assertEqual(inner.calls, 2)

    def test_zero_retries_passes_through(self):
        inner = FlakyProvider(fail_times=1)
        wrapper = RetryProvider(inner, max_retries=0)

        with self.assertRaises(RuntimeError):
            wrapper.complete([])
        self.assertEqual(inner.calls, 1)

    def test_stream_is_delegated_to_inner(self):
        wrapper = RetryProvider(FlakyProvider())
        chunks = list(wrapper.stream([]))
        self.assertEqual(len(chunks), 1)
        self.assertTrue(chunks[0].done)


if __name__ == "__main__":
    unittest.main()
