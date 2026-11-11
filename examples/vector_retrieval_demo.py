"""Demo: local vector retrieval with persistence, fully offline.

Run from the repository root:

    PYTHONPATH=src python3 examples/vector_retrieval_demo.py

No network or API key is required; the offline ``HashEmbedder`` produces
deterministic vectors, so ranking and JSON round-trip can be exercised locally.
"""
from harnesskit import VectorRetrievalTool, VectorStore

DOCUMENTS = [
    "The ReAct loop alternates between reasoning and acting.",
    "Cosine similarity ranks vectors by angle and overlap.",
    "Python uses indentation to delimit code blocks.",
]

QUERY = "reasoning and acting in the agent loop"


def main() -> None:
    tool = VectorRetrievalTool(DOCUMENTS)

    print(f"Query: {QUERY!r}\n")
    hits = tool.store.search(QUERY, top_k=2)
    for hit in hits:
        print(f"  [{hit['score']:.3f}] {hit['text']}")

    # Persist the store to JSON, then reload it in a fresh store.
    snapshot = tool.store.to_json()
    reloaded = VectorStore.from_json(snapshot)

    reloaded_hits = reloaded.search(QUERY, top_k=2)
    print("\n--- After JSON reload ---")
    for hit in reloaded_hits:
        print(f"  [{hit['score']:.3f}] {hit['text']}")

    same = [h["text"] for h in hits] == [h["text"] for h in reloaded_hits]
    print(f"\nRanking preserved after reload: {same}")


if __name__ == "__main__":
    main()
