"""Retrieval-augmented generation pipeline with lazy model loading."""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from sentence_transformers import SentenceTransformer

from .ingest import ingest
from .llm import answer
from .qdrant_store import get_client, ensure_collection, upsert_chunks, search

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the embedding model once, only when the first RAG operation needs it."""
    return SentenceTransformer(EMBEDDING_MODEL)


class EnterpriseRAG:
    def __init__(self) -> None:
        # Keep startup lightweight. The transformer model can take time to download
        # on a fresh Render instance, so it is loaded on first index/query instead.
        self.client = get_client()

    @property
    def embedder(self) -> SentenceTransformer:
        return get_embedder()

    def _ensure_ready(self) -> None:
        ensure_collection(
            self.client,
            self.embedder.get_sentence_embedding_dimension(),
        )

    def index_document(self, path: str, department: str) -> int:
        chunks = ingest(path, department)
        if not chunks:
            return 0
        self._ensure_ready()
        vectors = self.embedder.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        upsert_chunks(self.client, vectors, chunks)
        return len(chunks)

    def ask(
        self,
        question: str,
        allowed_departments: list[str],
        top_k: int = 5,
    ) -> dict[str, Any]:
        self._ensure_ready()
        vector = self.embedder.encode(
            question,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).tolist()
        contexts = search(
            self.client,
            vector,
            allowed_departments,
            limit=top_k,
        )
        return {
            "answer": answer(question, contexts),
            "sources": [
                {
                    "source": item.get("source"),
                    "department": item.get("department"),
                    "score": item.get("score"),
                }
                for item in contexts
            ],
        }
