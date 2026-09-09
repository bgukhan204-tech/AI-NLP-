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
            id=str(uuid.uuid5(uuid.NAMESPACE_URL, f"{chunk.get("source","unknown")}::{chunk.get("department","general")}::{i}")),
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
