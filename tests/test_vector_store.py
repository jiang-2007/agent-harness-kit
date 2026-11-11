import math
import unittest

from harnesskit.tools import (
    HashEmbedder,
    VectorRetrievalTool,
    VectorStore,
)

DOCUMENTS = [
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks documents by term weight and relevance.",
    "Python uses indentation to delimit code blocks.",
]


class TestHashEmbedder(unittest.TestCase):
    def test_is_deterministic(self):
        embedder = HashEmbedder(dim=64)
        self.assertEqual(embedder.embed("reasoning acting"), embedder.embed("reasoning acting"))

    def test_vector_is_l2_normalized(self):
        embedder = HashEmbedder(dim=64)
        vec = embedder.embed("reasoning acting")
        norm = math.sqrt(sum(x * x for x in vec))
        self.assertAlmostEqual(norm, 1.0, places=6)

    def test_empty_text_is_zero_vector(self):
        embedder = HashEmbedder(dim=32)
        self.assertEqual(embedder.embed(""), [0.0] * 32)


class TestVectorStore(unittest.TestCase):
    def setUp(self):
        self.store = VectorStore()
        self.store.add_documents(DOCUMENTS)

    def test_relevant_passage_ranked_first(self):
        hits = self.store.search("react reasoning acting", top_k=2)
        self.assertTrue(hits)
        self.assertIn("ReAct", hits[0]["text"])
        self.assertGreaterEqual(hits[0]["score"], hits[1]["score"])

    def test_related_document_outscores_unrelated_in_one_query(self):
        hits = self.store.search("reasoning acting loop", top_k=3)
        by_text = {h["text"]: h["score"] for h in hits}
        react = by_text["The ReAct loop alternates between reasoning and acting."]
        python = by_text["Python uses indentation to delimit code blocks."]
        self.assertGreater(react, 0.0)
        self.assertGreater(react, python)

    def test_min_score_filters_hits(self):
        hits = self.store.search("zzzqxv nonexistent", top_k=3, min_score=0.05)
        self.assertEqual(hits, [])

    def test_json_roundtrip_keeps_results(self):
        restored = VectorStore.from_json(self.store.to_json())
        self.assertEqual(restored.documents(), DOCUMENTS)
        original = self.store.search("react reasoning acting", top_k=1)
        reloaded = restored.search("react reasoning acting", top_k=1)
        self.assertEqual(original[0]["text"], reloaded[0]["text"])
        self.assertAlmostEqual(original[0]["score"], reloaded[0]["score"], places=6)


class TestVectorRetrievalTool(unittest.TestCase):
    def test_run_returns_ranked_passages(self):
        tool = VectorRetrievalTool(DOCUMENTS)
        result = tool.run(query="react reasoning acting", top_k=2)
        self.assertTrue(result.ok)
        self.assertIn("ReAct", result.content)

    def test_empty_store_message(self):
        tool = VectorRetrievalTool([])
        result = tool.run(query="anything")
        self.assertEqual(result.content, "no relevant passage found")


if __name__ == "__main__":
    unittest.main()
