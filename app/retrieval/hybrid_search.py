"""Combine vector and keyword search results using Reciprocal Rank Fusion."""

import logging

from app.retrieval.keyword_search import keyword_search
from app.retrieval.vector_search import RetrievedChunk, vector_search

logger = logging.getLogger(__name__)

RRF_K = 60


def hybrid_search(query: str, limit: int = 5, candidates: int = 20) -> list[RetrievedChunk]:
    """Merge vector and keyword search rankings using Reciprocal Rank Fusion."""
    vector_results = vector_search(query, limit=candidates)
    keyword_results = keyword_search(query, limit=candidates)

    scores: dict[int, float] = {}
    chunks_by_id: dict[int, RetrievedChunk] = {}

    for result_list in (vector_results, keyword_results):
        for rank, chunk in enumerate(result_list, start=1):
            scores[chunk.chunk_id] = scores.get(chunk.chunk_id, 0.0) + 1 / (RRF_K + rank)
            chunks_by_id[chunk.chunk_id] = chunk

    ranked_ids = sorted(scores, key=lambda chunk_id: scores[chunk_id], reverse=True)

    results = [
        RetrievedChunk(
            chunk_id=chunk_id,
            content=chunks_by_id[chunk_id].content,
            metadata=chunks_by_id[chunk_id].metadata,
            score=scores[chunk_id],
        )
        for chunk_id in ranked_ids[:limit]
    ]
    logger.info(
        "hybrid search complete",
        extra={
            "query_length": len(query),
            "vector_hits": len(vector_results),
            "keyword_hits": len(keyword_results),
            "merged_hits": len(results),
        },
    )
    return results
