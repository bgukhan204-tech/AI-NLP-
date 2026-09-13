"""Qdrant storage helpers with department-level retrieval isolation."""
from __future__ import annotations

import os
import uuid
from typing import Any

from qdrant_client import QdrantClient, models

COLLECTION = os.getenv("QDRANT_COLLECTION", "enterprise_documents")


def get_client() -> QdrantClient:
    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")
    if url:
        return QdrantClient(url=url, api_key=api_key or None)
    return QdrantClient(path=os.getenv("QDRANT_PATH", "./qdrant_data"))


def ensure_collection(client: QdrantClient, vector_size: int) -> None:
    if not client.collection_exists(COLLECTION):
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )


def upsert_chunks(client: QdrantClient, vectors: list[list[float]], chunks: list[dict[str, Any]]) -> None:
    points = [
        models.PointStruct(
            id=str(
                uuid.uuid5(
                    uuid.NAMESPACE_URL,
                    f"{chunk.get('source', 'unknown')}::{chunk.get('department', 'general')}::{i}",
                )
            ),
            vector=vector,
            payload=chunk,
        )
        for i, (vector, chunk) in enumerate(zip(vectors, chunks))
    ]
    client.upsert(collection_name=COLLECTION, points=points, wait=True)


def search(
    client: QdrantClient,
    vector: list[float],
    allowed_departments: list[str],
    limit: int = 5,
) -> list[dict[str, Any]]:
    if not allowed_departments:
        return []

    result = client.query_points(
        collection_name=COLLECTION,
        query=vector,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="department",
                    match=models.MatchAny(any=allowed_departments),
                )
            ]
        ),
        limit=limit,
        with_payload=True,
    )
    return [
        {"score": point.score, **(point.payload or {})}
        for point in result.points
    ]


def list_documents(client: QdrantClient, limit: int = 500) -> list[dict[str, Any]]:
    """Return unique indexed documents grouped by source and department."""
    records: dict[tuple[str, str], int] = {}
    offset = None
    remaining = max(1, min(int(limit), 2000))

    while remaining > 0:
        points, next_offset = client.scroll(
            collection_name=COLLECTION,
            limit=min(100, remaining),
            offset=offset,
            with_payload=True,
            with_vectors=False,
        )
        for point in points:
            payload = point.payload or {}
            key = (str(payload.get("source", "unknown")), str(payload.get("department", "general")))
            records[key] = records.get(key, 0) + 1
        remaining -= len(points)
        if next_offset is None or not points:
            break
        offset = next_offset

    return [
        {"source": source, "department": department, "chunks": chunks}
        for (source, department), chunks in sorted(records.items())
    ]


def delete_document(client: QdrantClient, source: str, department: str) -> None:
    """Delete all chunks belonging to one source/department pair."""
    client.delete(
        collection_name=COLLECTION,
        points_selector=models.FilterSelector(
            filter=models.Filter(
                must=[
                    models.FieldCondition(key="source", match=models.MatchValue(value=source)),
                    models.FieldCondition(key="department", match=models.MatchValue(value=department)),
                ]
            )
        ),
        wait=True,
    )
