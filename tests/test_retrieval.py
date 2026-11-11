import unittest

from harnesskit.tools import RetrievalTool

DOCUMENTS = [
    "The ReAct loop alternates between reasoning and acting.",
    "TF-IDF ranks documents by term weight and relevance.",
    "Python uses indentation to delimit code blocks.",
]


class TestRetrievalTool(unittest.TestCase):
    def setUp(self):
        self.tool = RetrievalTool(DOCUMENTS)

    def test_relevant_passage_ranked_first(self):
        result = self.tool.run(query="react reasoning acting", top_k=2)
        self.assertTrue(result.ok)
        self.assertIn("ReAct", result.content)

    def test_no_match_returns_message(self):
        result = self.tool.run(query="zzzqxv nonexistent", top_k=2)
        self.assertTrue(result.ok)
        self.assertEqual(result.content, "no relevant passage found")

    def test_empty_store_errors(self):
        tool = RetrievalTool([])
        result = tool.run(query="anything")
        self.assertFalse(result.ok)

    def test_add_document(self):
        self.tool.add("Retrieval augments the model with grounded passages.")
        result = self.tool.run(query="grounded passages retrieval", top_k=1)
        self.assertIn("grounded", result.content)

    def test_serialize_and_documents(self):
        self.assertEqual(self.tool.documents(), DOCUMENTS)
        self.assertEqual(self.tool.serialize(), DOCUMENTS)

    def test_json_roundtrip(self):
        restored = RetrievalTool.from_json(self.tool.to_json())
        result = restored.run(query="react reasoning acting", top_k=2)
        self.assertTrue(result.ok)
        self.assertIn("ReAct", result.content)
        self.assertEqual(restored.documents(), DOCUMENTS)


if __name__ == "__main__":
    unittest.main()
