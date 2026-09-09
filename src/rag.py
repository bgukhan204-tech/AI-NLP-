import os
from typing import Any

from sentence_transformers import SentenceTransformer

from .ingest import ingest
from .llm import answer
from .qdrant_store import (
    get_client,
    ensure_collection,
    upsert_chunks,
    search,
)

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "sentence-transformers/all-MiniLM-L6-v2",
)


class EnterpriseRAG:
    def __init__(self) -> None:
        self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        self.client = get_client()
        ensure_collection(self.client, self.embedder.get_sentence_embedding_dimension())

    def index_document(self, path: str, department: str) -> int:
        chunks = ingest(path, department)
        if not chunks:
            return 0
        vectors = self.embedder.encode(
            [chunk["text"] for chunk in chunks],
            normalize_embeddings=True,
        ).tolist()
        upsert_chunks(self.client, vectors, chunks)
        return len(chunks)

    def ask(
        self,
        question: str,
        allowed_departments: list[str],
        top_k: int = 5,
    ) -> dict[str, Any]:
        vector = self.embedder.encode(
            question,
            normalize_embeddings=True,
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
