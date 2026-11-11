"""Local vector store with a pluggable embedder — stdlib-only and offline.

This is the embedding half of a RAG pipeline: passages are mapped into a
fixed-dimensional vector space, stored in memory, and ranked by cosine
similarity at query time. The shipped :class:`HashEmbedder` is a deterministic
offline bag-of-words vectorizer; a real embedding-model-backed embedder can be
dropped in behind the same :class:`Embedder` protocol.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from dataclasses import dataclass, field
from typing import Any, Protocol

from .base import Tool, ToolResult

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase English/alnum words plus single CJK characters."""
    text = text.lower()
    tokens = _WORD_RE.findall(text)
    tokens.extend(ch for ch in text if "一" <= ch <= "鿿")
    return tokens


def _bucket(token: str, dim: int) -> int:
    """Stable hash bucket for a token (md5, not process-randomized)."""
    digest = hashlib.md5(token.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % dim


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class Embedder(Protocol):
    """Interface any text embedder must satisfy."""

    dim: int

    def embed(self, text: str) -> list[float]:
        ...


class HashEmbedder:
    """Deterministic offline embedder: hashed bag-of-words vectors.

    Tokens are mapped into a fixed-dimensional space via stable md5 hashing,
    weighted by term frequency, and L2-normalized. The same text always
    produces the same vector, so the store can be persisted and reloaded
    without re-embedding.
    """

    def __init__(self, dim: int = 256) -> None:
        if dim <= 0:
            raise ValueError("dim must be positive")
        self.dim = dim

    def embed(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        tokens = _tokenize(text)
        if not tokens:
            return vec
        for token in tokens:
            vec[_bucket(token, self.dim)] += 1.0
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0.0:
            vec = [x / norm for x in vec]
        return vec


@dataclass
class _Entry:
    text: str
    embedding: list[float]
    metadata: dict[str, Any] = field(default_factory=dict)


class VectorStore:
    """In-memory vector store ranked by cosine similarity, JSON-persistable."""

    def __init__(self, embedder: Embedder | None = None) -> None:
        self.embedder: Embedder = embedder or HashEmbedder()
        self._entries: list[_Entry] = []

    def add(self, text: str, metadata: dict[str, Any] | None = None) -> None:
        self._entries.append(
            _Entry(
                text=text,
                embedding=self.embedder.embed(text),
                metadata=dict(metadata or {}),
            )
        )

    def add_documents(self, documents: list[str]) -> None:
        for doc in documents:
            self.add(doc)

    def documents(self) -> list[str]:
        return [entry.text for entry in self._entries]

    def search(
        self,
        query: str,
        top_k: int = 3,
        min_score: float = 0.0,
    ) -> list[dict[str, Any]]:
        """Return the top-k passages by cosine similarity to the query."""
        if not self._entries:
            return []
        query_vec = self.embedder.embed(query)
        scored = [
            (_cosine(query_vec, entry.embedding), entry)
            for entry in self._entries
        ]
        scored = [(score, entry) for score, entry in scored if score >= min_score]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [
            {
                "text": entry.text,
                "score": round(score, 6),
                "metadata": dict(entry.metadata),
            }
            for score, entry in scored[:top_k]
        ]

    # ---- persistence -------------------------------------------------

    def serialize(self) -> dict[str, Any]:
        """Return a JSON-serialisable snapshot of the store."""
        return {
            "dim": self.embedder.dim,
            "entries": [
                {
                    "text": entry.text,
                    "embedding": entry.embedding,
                    "metadata": entry.metadata,
                }
                for entry in self._entries
            ],
        }

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.serialize(), ensure_ascii=False, indent=indent)

    @classmethod
    def from_json(cls, text: str) -> "VectorStore":
        snapshot = json.loads(text)
        store = cls(embedder=HashEmbedder(dim=int(snapshot.get("dim", 256)))))
        store._entries = [
            _Entry(
                text=e["text"],
                embedding=list(e["embedding"]),
                metadata=dict(e.get("metadata") or {}),
            )
            for e in snapshot.get("entries", [])
        ]
        return store


class VectorRetrievalTool(Tool):
    """Tool adapter that exposes a :class:`VectorStore` to the model."""

    name = "vector_retrieval"
    description = "Search the local vector store and return the most relevant passages."
    parameters = {
        "query": {"type": "string", "description": "Natural-language query."},
        "top_k": {"type": "integer", "description": "Maximum passages to return."},
    }

    def __init__(
        self,
        documents: list[str] | None = None,
        embedder: Embedder | None = None,
    ) -> None:
        self.store = VectorStore(embedder=embedder)
        if documents:
            self.store.add_documents(documents)

    def run(self, query: str = "", top_k: int = 3, **_: Any) -> ToolResult:
        hits = self.store.search(query, top_k=int(top_k))
        if not hits:
            return ToolResult(content="no relevant passage found")
        body = "\n---\n".join(f"{h['text']}  (score: {h['score']})" for h in hits)
        return ToolResult(content=body)
