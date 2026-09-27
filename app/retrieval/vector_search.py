"""Vector similarity search over stored chunks using pgvector."""

import logging
from dataclasses import dataclass

from app.db import get_connection
from app.embeddings import get_embeddings
from app.ingestion.store import vector_literal

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    """One chunk returned by a search, with enough info to cite and re-rank it."""

    chunk_id: int
    content: str
    metadata: dict
    score: float  # similarity, higher is better, in the range roughly [0, 1]


def vector_search(query: str, limit: int = 10) -> list[RetrievedChunk]:
    """Return the chunks whose embeddings are most similar to the query."""
    query_vector = vector_literal(get_embeddings().embed_query(query))

    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, content, metadata, 1 - (embedding <=> %(vector)s) AS similarity
            FROM chunks
            ORDER BY embedding <=> %(vector)s
            LIMIT %(limit)s
            """,
            {"vector": query_vector, "limit": limit},
        ).fetchall()

    results = [
        RetrievedChunk(chunk_id=row[0], content=row[1], metadata=row[2], score=row[3])
        for row in rows
    ]
    logger.info("vector search complete", extra={"query_length": len(query), "hits": len(results)})
    return results
