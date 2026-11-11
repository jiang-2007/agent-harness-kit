"""Local retrieval tool — a minimal stdlib TF-IDF RAG primitive."""
from __future__ import annotations

import json
import math
import re
from typing import Any

from .base import Tool, ToolResult

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase English/alnum words plus single CJK characters."""
    text = text.lower()
    tokens = _WORD_RE.findall(text)
    tokens.extend(ch for ch in text if "一" <= ch <= "鿿")
    return tokens


class RetrievalTool(Tool):
    """In-memory document store ranked by a simple TF-IDF dot product.

    This is the retrieval half of a RAG pipeline: load passages, query with
    natural language, get back the top-k most relevant snippets to ground the
    model's answer. No vector database or third-party dependency required.
    """

    name = "retrieval"
    description = "Search the local document store and return the most relevant passages."
    parameters = {
        "query": {"type": "string", "description": "Natural-language query."},
        "top_k": {"type": "integer", "description": "Maximum passages to return."},
    }

    def __init__(self, documents: list[str] | None = None) -> None:
        self._docs: list[str] = list(documents or [])
        self._doc_tokens: list[list[str]] = [_tokenize(doc) for doc in self._docs]
        self._idf: dict[str, float] = {}
        self._recompute_idf()

    def _recompute_idf(self) -> None:
        n = len(self._docs)
        df: dict[str, int] = {}
        for tokens in self._doc_tokens:
            for token in set(tokens):
                df[token] = df.get(token, 0) + 1
        self._idf = {
            token: math.log((n + 1) / (count + 1)) + 1 for token, count in df.items()
        }

    def add(self, text: str) -> None:
        self._docs.append(text)
        self._doc_tokens.append(_tokenize(text))
        self._recompute_idf()

    def documents(self) -> list[str]:
        """Return a copy of the stored passages."""
        return list(self._docs)

    def serialize(self) -> list[str]:
        """Return the document store as a JSON-serialisable list."""
        return list(self._docs)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.serialize(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "RetrievalTool":
        return cls(documents=json.loads(text))

    def _score(self, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not doc_tokens:
            return 0.0
        doc_tf: dict[str, int] = {}
        for token in doc_tokens:
            doc_tf[token] = doc_tf.get(token, 0) + 1
        score = 0.0
        for token in set(query_tokens):
            if token in doc_tf:
                score += (doc_tf[token] / len(doc_tokens)) * self._idf.get(token, 1.0)
        return score

    def run(self, query: str = "", top_k: int = 3, **_: Any) -> ToolResult:
        if not self._docs:
            return ToolResult(content="", ok=False, error="document store is empty")

        query_tokens = _tokenize(query)
        ranked = sorted(
            range(len(self._docs)),
            key=lambda i: self._score(query_tokens, self._doc_tokens[i]),
            reverse=True,
        )
        k = min(int(top_k), len(self._docs))
        hits = [
            self._docs[i]
            for i in ranked[:k]
            if self._score(query_tokens, self._doc_tokens[i]) > 0
        ]
        if not hits:
            return ToolResult(content="no relevant passage found")
        return ToolResult(content="\n---\n".join(hits))
