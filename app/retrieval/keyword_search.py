"""Keyword search over stored chunks using PostgreSQL full-text search."""

import logging

from app.db import get_connection
from app.retrieval.vector_search import RetrievedChunk

logger = logging.getLogger(__name__)


def keyword_search(query: str, limit: int = 10) -> list[RetrievedChunk]:
    """Return chunks whose text best matches the query's keywords."""
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT id, content, metadata,
                   ts_rank(search_vector, websearch_to_tsquery('english', %(query)s)) AS rank
            FROM chunks
            WHERE search_vector @@ websearch_to_tsquery('english', %(query)s)
            ORDER BY rank DESC
            LIMIT %(limit)s
            """,
            {"query": query, "limit": limit},
        ).fetchall()

    results = [
        RetrievedChunk(chunk_id=row[0], content=row[1], metadata=row[2], score=row[3])
        for row in rows
    ]
    logger.info("keyword search complete", extra={"query_length": len(query), "hits": len(results)})
    return results
